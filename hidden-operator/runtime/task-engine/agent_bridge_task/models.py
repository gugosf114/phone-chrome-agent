from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any
from urllib.parse import parse_qsl, urlparse


DEFAULT_SECRET_FIELD_NAMES = frozenset(
    {
        "password",
        "passcode",
        "token",
        "api_key",
        "apikey",
        "secret",
        "authorization",
        "cookie",
        "private_key",
        "bearer",
    }
)
SECRET_REFERENCE_KEYS = frozenset({"$secret_env", "$secret_file"})
BROWSER_BACKENDS = frozenset(
    {"phone-headless", "android-chrome", "laptop-chrome", "cdp"}
)


def _is_secret_reference(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and len(value) == 1
        and next(iter(value)) in SECRET_REFERENCE_KEYS
        and isinstance(next(iter(value.values())), str)
        and bool(next(iter(value.values())).strip())
    )


def is_secret_field_name(name: str, extra_fields: tuple[str, ...] = ()) -> bool:
    normalized = name.strip().lower().replace("-", "_")
    extra = {item.strip().lower().replace("-", "_") for item in extra_fields}
    if normalized in extra:
        return True
    return any(
        normalized == secret
        or normalized.endswith(f"_{secret}")
        or normalized.endswith(secret)
        for secret in DEFAULT_SECRET_FIELD_NAMES
    )


def validate_secret_storage(value: Any, extra_fields: tuple[str, ...]) -> None:
    def validate_url(item: str, path: str) -> None:
        try:
            parsed = urlparse(item)
        except ValueError:
            return
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return
        query_names = [
            name for name, _ in parse_qsl(parsed.query, keep_blank_values=True)
        ]
        fragment_names = [
            name for name, _ in parse_qsl(parsed.fragment, keep_blank_values=True)
        ]
        sensitive_names = {"code", "sig", "signature", "session", "session_id"}
        if (
            parsed.username
            or parsed.password
            or any(
                is_secret_field_name(name) or name.lower() in sensitive_names
                for name in (*query_names, *fragment_names)
            )
        ):
            raise ValueError(
                f"Sensitive URL {path!r} cannot be stored inline; remove its credential."
            )

    def walk(item: Any, path: str = "args") -> None:
        if _is_secret_reference(item):
            return
        if isinstance(item, dict):
            for key, child in item.items():
                child_path = f"{path}.{key}"
                if is_secret_field_name(key, extra_fields) and not _is_secret_reference(
                    child
                ):
                    raise ValueError(
                        f"Secret field {child_path!r} must use $secret_env or $secret_file."
                    )
                walk(child, child_path)
        elif isinstance(item, list):
            for index, child in enumerate(item):
                walk(child, f"{path}.{index}")
        elif isinstance(item, str):
            validate_url(item, path)

    walk(value)


def validate_target_storage(target: str, path: str) -> None:
    candidate = (
        target
        if target.startswith(("http://", "https://"))
        else target.split(":", 1)[1]
        if ":" in target
        else target
    )
    validate_secret_storage(candidate, ())
    if not target.startswith(("browser:http://", "browser:https://")):
        return
    parsed = urlparse(candidate)
    if (
        not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            f"Browser target {path!r} must be an origin without credentials or path data."
        )


def validate_secret_fields(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) and bool(item.strip()) for item in value
    ):
        raise ValueError("secret_fields must be a list of non-empty strings")
    return tuple(item.strip() for item in value)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Authority(IntEnum):
    TALK = 0
    READ = 1
    COLLECT = 2
    LOCAL = 3
    EXTERNAL = 4
    FULL = 5


AUTHORITY_NAMES = {
    "talk": Authority.TALK,
    "talk-only": Authority.TALK,
    "read": Authority.READ,
    "read-only": Authority.READ,
    "collect": Authority.COLLECT,
    "read-download": Authority.COLLECT,
    "local": Authority.LOCAL,
    "local-changes": Authority.LOCAL,
    "external": Authority.EXTERNAL,
    "named-external": Authority.EXTERNAL,
    "full": Authority.FULL,
    "full-authority": Authority.FULL,
    "total-control": Authority.FULL,
}


def parse_authority(value: Authority | int | str) -> Authority:
    if isinstance(value, Authority):
        return value
    if isinstance(value, int):
        return Authority(value)
    normalized = value.strip().lower().replace("_", "-")
    if normalized.isdigit():
        return Authority(int(normalized))
    try:
        return AUTHORITY_NAMES[normalized]
    except KeyError as error:
        choices = ", ".join(sorted(AUTHORITY_NAMES))
        raise ValueError(
            f"Unknown authority {value!r}. Use one of: {choices}"
        ) from error


@dataclass(frozen=True)
class Scope:
    kind: str
    value: str | None = None
    remaining_uses: int | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | str) -> "Scope":
        if isinstance(raw, str):
            raw = {"kind": raw}
        kind = str(raw.get("kind", "task")).strip().lower()
        allowed = {"answer", "test", "turns", "session", "task", "standing"}
        if kind not in allowed:
            raise ValueError(f"Unknown permission scope {kind!r}.")
        if kind == "session" and not raw.get("value"):
            raise ValueError("Session permission needs a concrete session ID.")
        remaining = raw.get("remaining_uses")
        if kind == "answer":
            remaining = 1
        if kind == "turns" and remaining is None:
            remaining = int(raw.get("turns", 0))
        if remaining is not None and int(remaining) < 1:
            raise ValueError("Permission remaining_uses must be at least 1.")
        return cls(
            kind=kind,
            value=str(raw["value"]) if raw.get("value") is not None else None,
            remaining_uses=int(remaining) if remaining is not None else None,
        )


@dataclass(frozen=True)
class PermissionGrant:
    id: str
    authority: Authority
    scope: Scope
    targets: tuple[str, ...]
    denied_actions: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)
    expires_at: str | None = None
    revoked_at: str | None = None

    @classmethod
    def from_dict(cls, grant_id: str, raw: dict[str, Any]) -> "PermissionGrant":
        raw_targets = raw.get("targets", [])
        raw_denied = raw.get("denied_actions", [])
        if not isinstance(raw_targets, list) or not all(
            isinstance(item, str) and bool(item.strip()) for item in raw_targets
        ):
            raise ValueError("permission targets must be a list of non-empty strings")
        if not isinstance(raw_denied, list) or not all(
            isinstance(item, str) and bool(item.strip()) for item in raw_denied
        ):
            raise ValueError(
                "permission denied_actions must be a list of non-empty strings"
            )
        targets = tuple(item.strip() for item in raw_targets)
        authority = parse_authority(raw.get("authority", "talk"))
        if authority > Authority.TALK and not targets:
            raise ValueError("A working permission needs at least one named target.")
        grant = cls(
            id=grant_id,
            authority=authority,
            scope=Scope.from_dict(raw.get("scope", "task")),
            targets=targets,
            denied_actions=tuple(item.strip() for item in raw_denied),
            expires_at=raw.get("expires_at"),
        )
        grant.validate_for_storage()
        return grant

    def validate_for_storage(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("permission ID must be a non-empty string")
        if not isinstance(self.authority, Authority):
            raise ValueError("permission authority must be an Authority value")
        if not isinstance(self.scope, Scope):
            raise ValueError("permission scope must be a Scope")
        allowed_scopes = {"answer", "test", "turns", "session", "task", "standing"}
        if self.scope.kind not in allowed_scopes:
            raise ValueError(f"Unknown permission scope {self.scope.kind!r}.")
        if self.scope.value is not None and (
            not isinstance(self.scope.value, str) or not self.scope.value.strip()
        ):
            raise ValueError("permission scope value must be a non-empty string")
        remaining = self.scope.remaining_uses
        if remaining is not None and (
            isinstance(remaining, bool)
            or not isinstance(remaining, int)
            or remaining < 0
        ):
            raise ValueError("permission remaining_uses must be a non-negative integer")
        if self.scope.kind in {"answer", "turns"} and remaining is None:
            raise ValueError(f"{self.scope.kind} permission needs remaining_uses")
        if not isinstance(self.targets, (list, tuple)) or not all(
            isinstance(item, str) and bool(item.strip()) for item in self.targets
        ):
            raise ValueError("permission targets must be a list of non-empty strings")
        if self.authority > Authority.TALK and not self.targets:
            raise ValueError("A working permission needs at least one named target.")
        if not isinstance(self.denied_actions, (list, tuple)) or not all(
            isinstance(item, str) and bool(item.strip()) for item in self.denied_actions
        ):
            raise ValueError(
                "permission denied_actions must be a list of non-empty strings"
            )
        for index, target in enumerate(self.targets):
            validate_target_storage(target, f"permission.targets.{index}")


@dataclass(frozen=True)
class Step:
    adapter: str
    verb: str
    target: str
    args: dict[str, Any] = field(default_factory=dict)
    expect: dict[str, Any] = field(default_factory=dict)
    secret_fields: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Step":
        adapter = str(raw.get("adapter", "")).strip()
        verb = str(raw.get("verb", "")).strip()
        target = str(raw.get("target", "")).strip()
        if not adapter or not verb or not target:
            raise ValueError("Every step needs adapter, verb, and target.")
        args = raw.get("args", {})
        expect = raw.get("expect", {})
        if not isinstance(args, dict) or not isinstance(expect, dict):
            raise ValueError("Step args and expect must be objects.")
        secret_fields = validate_secret_fields(raw.get("secret_fields", []))
        validate_target_storage(target, "step.target")
        validate_secret_storage(args, secret_fields)
        validate_secret_storage(expect, secret_fields)
        return cls(
            adapter=adapter,
            verb=verb,
            target=target,
            args=args,
            expect=expect,
            secret_fields=secret_fields,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "verb": self.verb,
            "target": self.target,
            "args": self.args,
            "expect": self.expect,
            "secret_fields": list(self.secret_fields),
        }

    def validate_for_storage(self) -> None:
        secret_fields = validate_secret_fields(self.secret_fields)
        validate_target_storage(self.target, "step.target")
        validate_secret_storage(self.args, secret_fields)
        validate_secret_storage(self.expect, secret_fields)


@dataclass(frozen=True)
class TaskPlan:
    id: str
    goal: str
    steps: tuple[Step, ...]
    permission: PermissionGrant | None = None
    permission_ref: str | None = None
    browser_backend: str | None = None
    recipe_key: str | None = None
    race_ref: str | None = None
    baseline_ms: int | None = None
    speed_ratio: float = 1.0

    @classmethod
    def from_dict(cls, raw: dict[str, Any], generated_id: str) -> "TaskPlan":
        task = raw.get("task", raw)
        task_id = str(task.get("id") or generated_id)
        goal = str(task.get("goal", "")).strip()
        if not goal:
            raise ValueError("The task needs a goal.")
        permission_ref = task.get("permission_ref")
        permission_raw = task.get("permission")
        if permission_ref and permission_raw is not None:
            raise ValueError("Use permission or permission_ref, not both.")
        if permission_ref:
            permission = None
            permission_ref = str(permission_ref)
        else:
            permission_raw = permission_raw or {}
            permission = PermissionGrant.from_dict(
                str(permission_raw.get("id") or f"grant-{task_id}"),
                permission_raw,
            )
            if permission.scope.kind in {"task", "test"}:
                if permission.scope.value not in {None, task_id}:
                    raise ValueError(
                        "inline task/test permission belongs to another task"
                    )
                permission = replace(
                    permission,
                    scope=replace(permission.scope, value=task_id),
                )
        steps = tuple(Step.from_dict(item) for item in raw.get("steps", []))
        if not steps:
            raise ValueError("The plan needs at least one step.")
        browser_backend = task.get("browser_backend")
        if browser_backend is not None:
            browser_backend = str(browser_backend).strip()
            if browser_backend not in BROWSER_BACKENDS:
                choices = ", ".join(sorted(BROWSER_BACKENDS))
                raise ValueError(f"browser_backend must be one of: {choices}")
        if any(step.adapter == "browser" for step in steps) and not browser_backend:
            raise ValueError(
                "A browser task must name task.browser_backend: phone-headless, "
                "android-chrome, laptop-chrome, or cdp."
            )
        baseline = task.get("baseline_ms")
        ratio = float(task.get("speed_ratio", 1.0))
        if baseline is not None and int(baseline) < 1:
            raise ValueError("baseline_ms must be positive.")
        if ratio <= 0:
            raise ValueError("speed_ratio must be positive.")
        return cls(
            id=task_id,
            goal=goal,
            steps=steps,
            permission=permission,
            permission_ref=permission_ref,
            browser_backend=browser_backend,
            recipe_key=task.get("recipe_key"),
            race_ref=task.get("race_ref"),
            baseline_ms=int(baseline) if baseline is not None else None,
            speed_ratio=ratio,
        )

    def to_dict(self) -> dict[str, Any]:
        task: dict[str, Any] = {
            "id": self.id,
            "goal": self.goal,
            "browser_backend": self.browser_backend,
            "recipe_key": self.recipe_key,
            "race_ref": self.race_ref,
            "baseline_ms": self.baseline_ms,
            "speed_ratio": self.speed_ratio,
        }
        if self.permission_ref:
            task["permission_ref"] = self.permission_ref
        elif self.permission:
            task["permission"] = {
                "id": self.permission.id,
                "authority": int(self.permission.authority),
                "scope": {
                    "kind": self.permission.scope.kind,
                    "value": self.permission.scope.value,
                    "remaining_uses": self.permission.scope.remaining_uses,
                },
                "targets": list(self.permission.targets),
                "denied_actions": list(self.permission.denied_actions),
                "expires_at": self.permission.expires_at,
            }
        return {
            "task": task,
            "steps": [step.to_dict() for step in self.steps],
        }

    def validate_for_storage(self) -> None:
        if (
            self.browser_backend is not None
            and self.browser_backend not in BROWSER_BACKENDS
        ):
            choices = ", ".join(sorted(BROWSER_BACKENDS))
            raise ValueError(f"browser_backend must be one of: {choices}")
        if (
            any(step.adapter == "browser" for step in self.steps)
            and not self.browser_backend
        ):
            raise ValueError(
                "A browser task must name task.browser_backend: phone-headless, "
                "android-chrome, laptop-chrome, or cdp."
            )
        for step in self.steps:
            step.validate_for_storage()
