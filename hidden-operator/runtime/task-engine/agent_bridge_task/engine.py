from __future__ import annotations

import os
import re
import time
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .adapters import Adapter, AdapterResult
from .models import (
    SECRET_REFERENCE_KEYS,
    Authority,
    Step,
    TaskPlan,
    is_secret_field_name,
    utc_now,
)
from .permissions import PermissionContext, evaluate_permission, permission_receipt
from .store import Store


PUBLIC_URL_PATTERN = re.compile(r"https?://[^\s<>'\"]+", re.IGNORECASE)


def redact(
    value: Any,
    extra_fields: tuple[str, ...] = (),
    secret_values: tuple[str, ...] = (),
) -> Any:
    if isinstance(value, dict):
        if len(value) == 1 and next(iter(value)) in SECRET_REFERENCE_KEYS:
            return "[SECRET_REFERENCE]"
        return {
            key: (
                "[REDACTED]"
                if is_secret_field_name(key, extra_fields)
                else redact(item, extra_fields, secret_values)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item, extra_fields, secret_values) for item in value]
    if isinstance(value, str):
        safe = value
        for secret in secret_values:
            if secret:
                safe = safe.replace(secret, "[REDACTED]")
        return safe_url_for_log(safe)
    return value


def safe_url_for_log(value: str) -> str:
    def origin(match: re.Match[str]) -> str:
        try:
            parsed = urlparse(match.group(0))
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                return "[INVALID_URL]"
            host = parsed.hostname.lower()
            if ":" in host:
                host = f"[{host}]"
            default_port = 443 if parsed.scheme == "https" else 80
            netloc = (
                host if parsed.port in {None, default_port} else f"{host}:{parsed.port}"
            )
            return f"{parsed.scheme.lower()}://{netloc}"
        except ValueError:
            return "[INVALID_URL]"

    return PUBLIC_URL_PATTERN.sub(origin, value)


def resolve_secret_references(value: Any) -> tuple[Any, tuple[str, ...]]:
    secrets: list[str] = []

    def walk(item: Any) -> Any:
        if isinstance(item, dict):
            if len(item) == 1 and "$secret_env" in item:
                name = str(item["$secret_env"])
                try:
                    secret = os.environ[name]
                except KeyError as error:
                    raise ValueError(
                        f"Secret environment variable {name!r} is unavailable."
                    ) from error
                secrets.append(secret)
                return secret
            if len(item) == 1 and "$secret_file" in item:
                path = Path(str(item["$secret_file"])).expanduser()
                try:
                    secret = path.read_text(encoding="utf-8").rstrip("\r\n")
                except OSError as error:
                    raise ValueError(
                        f"Secret file {str(path)!r} is unavailable: {error}"
                    ) from error
                secrets.append(secret)
                return secret
            return {key: walk(child) for key, child in item.items()}
        if isinstance(item, list):
            return [walk(child) for child in item]
        return item

    return walk(value), tuple(secrets)


def has_semantic_postcondition(expect: dict[str, Any]) -> bool:
    structural_roots = {
        "exit_code",
        "verification",
        "transport",
        "server_elapsed_ms",
    }
    for operation in ("equals", "contains"):
        checks = expect.get(operation)
        if isinstance(checks, dict):
            for dotted, wanted in checks.items():
                if dotted.split(".", 1)[0] in structural_roots:
                    continue
                if operation == "contains" and (wanted == "" or wanted is None):
                    continue
                return True
    return False


def validate_mutation_postcondition(
    adapter: Adapter, step: Step, required: Authority
) -> None:
    if required < Authority.LOCAL:
        return
    validator = getattr(adapter, "validate_postcondition", None)
    if validator is not None:
        validator(step)
        return
    if not has_semantic_postcondition(step.expect):
        raise ValueError(
            "a mutation needs a non-empty equals or contains postcondition"
        )


class Engine:
    def __init__(self, store: Store, adapters: dict[str, Adapter]):
        self.store = store
        self.adapters = adapters

    @staticmethod
    def _bind(adapter: Adapter, step: Step) -> Step:
        binder = getattr(adapter, "bind", None)
        return binder(step) if binder is not None else step

    @staticmethod
    def _configure_browser(adapter: Adapter, step: Step, plan: TaskPlan) -> None:
        if step.adapter != "browser":
            return
        if not plan.browser_backend:
            raise ValueError(
                "A browser task must name task.browser_backend: phone-headless, "
                "android-chrome, laptop-chrome, or cdp."
            )
        configure = getattr(adapter, "configure_backend", None)
        if configure is not None:
            configure(plan.browser_backend)

    @staticmethod
    def _permission_check(
        adapter: Adapter,
        step: Step,
        grant: Any,
        context: PermissionContext,
    ) -> tuple[Authority, Any]:
        required = adapter.required_authority(step)
        decision = evaluate_permission(grant, step, required, context)
        if not decision.allowed:
            return required, decision
        expander = getattr(adapter, "permission_steps", None)
        if expander is not None:
            for nested in expander(step):
                nested_required = adapter.required_authority(nested)
                nested_decision = evaluate_permission(
                    grant, nested, nested_required, context
                )
                if not nested_decision.allowed:
                    return required, nested_decision
        return required, decision

    def preflight(
        self,
        plan: TaskPlan,
        session_id: str | None = None,
        start_index: int = 0,
    ) -> dict[str, Any]:
        if plan.permission is None:
            raise ValueError("Preflight needs the resolved permission.")
        checks = []
        allowed = True
        context = PermissionContext(plan.id, session_id)
        for index, step in enumerate(plan.steps[start_index:], start=start_index):
            adapter = self.adapters.get(step.adapter)
            if adapter is None:
                checks.append(
                    {"step": index, "allowed": False, "reason": "unknown adapter"}
                )
                allowed = False
                continue
            try:
                self._configure_browser(adapter, step, plan)
                bound_step = self._bind(adapter, step)
                required = adapter.required_authority(bound_step)
                required, decision = self._permission_check(
                    adapter, bound_step, plan.permission, context
                )
                if decision.allowed:
                    validate_mutation_postcondition(adapter, bound_step, required)
            except (OSError, RuntimeError, ValueError) as error:
                checks.append({"step": index, "allowed": False, "reason": str(error)})
                allowed = False
                continue
            checks.append(
                {
                    "step": index,
                    "adapter": step.adapter,
                    "verb": step.verb,
                    "target": bound_step.target,
                    "declared_target": step.target,
                    "required_level": int(required),
                    "required_name": required.name.lower(),
                    "allowed": decision.allowed,
                    "reason": decision.reason,
                }
            )
            allowed = allowed and decision.allowed
        return {
            "allowed": allowed,
            "browser_backend": plan.browser_backend,
            "permission": permission_receipt(plan.permission),
            "checks": checks,
        }

    def create_and_run(
        self, plan: TaskPlan, session_id: str | None = None
    ) -> dict[str, Any]:
        self.store.save_plan(plan)
        return self.run(plan.id, session_id=session_id)

    def run(self, task_id: str, session_id: str | None = None) -> dict[str, Any]:
        task_lock = self.store.acquire_task_lock(task_id)
        if task_lock is None:
            row = self.store.task_row(task_id)
            return {
                "task_id": task_id,
                "status": "blocked",
                "next_step": int(row["next_step"]),
                "preflight": {
                    "allowed": False,
                    "reason": "task is already running",
                },
            }
        resource_locks = []
        try:
            plan = self.store.plan_for_task(task_id)
            resources: set[str] = set()
            for step in plan.steps[int(self.store.task_row(task_id)["next_step"]) :]:
                adapter = self.adapters.get(step.adapter)
                if adapter is None:
                    continue
                exclusive_resources = getattr(adapter, "exclusive_resources", None)
                if exclusive_resources is not None:
                    resources.update(exclusive_resources(step))
            for resource in sorted(resources):
                resource_lock = self.store.acquire_resource_lock(resource)
                if resource_lock is None:
                    return {
                        "task_id": task_id,
                        "status": "blocked",
                        "next_step": int(self.store.task_row(task_id)["next_step"]),
                        "preflight": {
                            "allowed": False,
                            "reason": f"resource {resource!r} is already in use",
                        },
                    }
                resource_locks.append(resource_lock)
            return self._run_locked(task_id, session_id=session_id)
        finally:
            for resource_lock in reversed(resource_locks):
                self.store.release_resource_lock(resource_lock)
            self.store.release_task_lock(task_lock)

    def _run_locked(
        self, task_id: str, session_id: str | None = None
    ) -> dict[str, Any]:
        row = self.store.task_row(task_id)
        plan = self.store.plan_for_task(task_id)
        grant = self.store.grant_for_task(task_id)
        plan = replace(plan, permission=grant)
        start_index = int(row["next_step"])
        preflight = self.preflight(plan, session_id=session_id, start_index=start_index)
        if not preflight["allowed"]:
            self.store.block_task_if_idle(task_id, start_index)
            return {
                "task_id": task_id,
                "status": "blocked",
                "next_step": start_index,
                "preflight": preflight,
            }

        run_id = f"run-{uuid.uuid4().hex[:16]}"
        receipt = preflight["permission"]
        if not self.store.start_run(run_id, task_id, receipt, start_index):
            return {
                "task_id": task_id,
                "status": "blocked",
                "next_step": start_index,
                "preflight": {
                    **preflight,
                    "allowed": False,
                    "reason": "task is already running or already finished",
                },
            }
        reserved_grants: set[str] = set()

        def reserve_current_grant() -> tuple[Any | None, str | None]:
            for _ in range(32):
                current = self.store.grant_for_task(task_id)
                if current.id not in reserved_grants:
                    if not self.store.reserve_permission_run(current.id):
                        return None, "permission has no remaining runs"
                    reserved_grants.add(current.id)
                latest = self.store.grant_for_task(task_id)
                if latest.id == current.id:
                    return latest, None
            return None, "permission changed too many times at one step boundary"

        current_grant, reserve_error = reserve_current_grant()
        if current_grant is None:
            blocked_summary = {
                "run_id": run_id,
                "steps_total": len(plan.steps),
                "steps_completed": start_index,
                "failure": {"reason": reserve_error},
            }
            self.store.finish_run(
                run_id,
                task_id,
                "blocked",
                0,
                blocked_summary,
                start_index,
            )
            return {
                "task_id": task_id,
                "status": "blocked",
                "next_step": start_index,
                "preflight": {
                    **preflight,
                    "allowed": False,
                    "reason": reserve_error,
                },
            }
        run_started = time.monotonic()
        next_step = start_index
        final_status = "completed"
        failure: dict[str, Any] | None = None

        for index, step in enumerate(plan.steps[start_index:], start=start_index):
            adapter = self.adapters[step.adapter]
            current_grant, reserve_error = reserve_current_grant()
            if current_grant is None:
                final_status = "blocked"
                failure = {"step": index, "reason": reserve_error}
                break
            try:
                self._configure_browser(adapter, step, plan)
                bound_step = self._bind(adapter, step)
                required = adapter.required_authority(bound_step)
            except (OSError, RuntimeError, ValueError) as error:
                final_status = "blocked"
                failure = {"step": index, "reason": str(error)}
                break
            required, current_decision = self._permission_check(
                adapter,
                bound_step,
                current_grant,
                PermissionContext(task_id, session_id, reserved_run=True),
            )
            if not current_decision.allowed:
                final_status = "blocked"
                failure = {"step": index, "reason": current_decision.reason}
                break
            try:
                validate_mutation_postcondition(adapter, bound_step, required)
            except ValueError as error:
                final_status = "blocked"
                failure = {"step": index, "reason": str(error)}
                break
            started_at = utc_now()
            action_started = time.monotonic()
            resolved_args: dict[str, Any] = {}
            secret_values: tuple[str, ...] = ()
            try:
                resolved_args, secret_values = resolve_secret_references(
                    bound_step.args
                )
                resolved_expect, expect_secrets = resolve_secret_references(
                    bound_step.expect
                )
                secret_values = (*secret_values, *expect_secrets)
                execution_step = replace(
                    bound_step,
                    args=resolved_args,
                    expect=resolved_expect,
                )
                result = adapter.execute(execution_step)
            except Exception as error:  # adapter boundary: record the failure, never lose the checkpoint
                result = AdapterResult(
                    False, False, {"error": f"{type(error).__name__}: {error}"}
                )
            action_ms = max(0, round((time.monotonic() - action_started) * 1000))
            ended_at = utc_now()
            action_status = "success" if result.ok and result.verified else "failed"
            public_args = {
                key: value
                for key, value in bound_step.args.items()
                if not key.startswith("_")
            }
            safe_args = redact(public_args, bound_step.secret_fields, secret_values)
            safe_result = redact(result.data, bound_step.secret_fields, secret_values)
            self.store.record_event(
                {
                    "run_id": run_id,
                    "task_id": task_id,
                    "step_index": index,
                    "adapter": bound_step.adapter,
                    "verb": bound_step.verb,
                    "target": bound_step.target,
                    "args": safe_args,
                    "started_at": started_at,
                    "ended_at": ended_at,
                    "elapsed_ms": action_ms,
                    "status": action_status,
                    "verified": result.verified,
                    "result": safe_result,
                }
            )
            if action_status != "success":
                final_status = "failed"
                failure = {"step": index, "result": safe_result}
                if plan.recipe_key:
                    self.store.mark_recipe_failure(plan.recipe_key)
                break
            next_step = index + 1
            self.store.checkpoint(task_id, next_step)

        execution_ms = max(0, round((time.monotonic() - run_started) * 1000))
        elapsed_ms = execution_ms
        timing_scope = "execution_only"
        planning_and_wait_ms = None
        timer_started_at = None
        if plan.race_ref:
            race = self.store.race(plan.race_ref)
            elapsed_ms = max(
                execution_ms,
                round((time.time_ns() - int(race["started_unix_ns"])) / 1_000_000),
            )
            timing_scope = "request_to_result"
            planning_and_wait_ms = max(0, elapsed_ms - execution_ms)
            timer_started_at = race["started_at"]
        speed_pass = True
        speed_limit_ms = None
        if plan.baseline_ms is not None:
            speed_limit_ms = round(plan.baseline_ms * plan.speed_ratio)
            speed_pass = elapsed_ms <= speed_limit_ms
            if final_status == "completed" and not speed_pass:
                final_status = "completed_slow"

        result_summary = {
            "run_id": run_id,
            "browser_backend": plan.browser_backend,
            "steps_total": len(plan.steps),
            "steps_completed": next_step,
            "elapsed_ms": elapsed_ms,
            "execution_ms": execution_ms,
            "planning_and_wait_ms": planning_and_wait_ms,
            "timing_scope": timing_scope,
            "timer_started_at": timer_started_at,
            "baseline_ms": plan.baseline_ms,
            "speed_limit_ms": speed_limit_ms,
            "speed_pass": speed_pass,
            "failure": failure,
            "final_permission": permission_receipt(self.store.grant_for_task(task_id)),
        }
        self.store.finish_run(
            run_id,
            task_id,
            final_status,
            elapsed_ms,
            result_summary,
            next_step,
        )
        if plan.race_ref:
            self.store.finish_race(plan.race_ref)
        if final_status in {"completed", "completed_slow"} and plan.recipe_key:
            self.store.save_recipe(
                plan.recipe_key,
                plan.goal,
                [step.to_dict() for step in plan.steps],
                execution_ms,
            )
        return {
            "task_id": task_id,
            "status": final_status,
            "permission": receipt,
            **result_summary,
        }

    def replay(
        self,
        recipe_key: str,
        permission: dict[str, Any],
        goal: str | None = None,
        baseline_ms: int | None = None,
        race_ref: str | None = None,
        browser_backend: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        recipe = self.store.recipe(recipe_key)
        if recipe is None:
            raise KeyError(f"Unknown recipe {recipe_key!r}.")
        task_id = f"task-{uuid.uuid4().hex[:16]}"
        raw = {
            "task": {
                "id": task_id,
                "goal": goal or recipe["goal"],
                "permission": permission,
                "recipe_key": recipe_key,
                "baseline_ms": baseline_ms,
                "race_ref": race_ref,
                "browser_backend": browser_backend,
            },
            "steps": recipe["steps"],
        }
        plan = TaskPlan.from_dict(raw, task_id)
        return self.create_and_run(plan, session_id=session_id)
