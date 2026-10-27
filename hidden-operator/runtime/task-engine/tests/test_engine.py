from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import time
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from agent_bridge_task.adapters import AdapterResult, NoopAdapter, ProcessAdapter
from agent_bridge_task.engine import Engine, redact
from agent_bridge_task.models import Authority, PermissionGrant, Scope, Step, TaskPlan
from agent_bridge_task.store import Store


class FlakyAdapter:
    def __init__(self) -> None:
        self.calls = 0

    def required_authority(self, step: Step) -> Authority:
        return Authority.READ

    def execute(self, step: Step) -> AdapterResult:
        self.calls += 1
        if self.calls == 1:
            return AdapterResult(False, False, {"error": "first call fails"})
        return AdapterResult(True, True, {"ok": True})


class DowngradeAdapter:
    def __init__(self, store: Store, task_id: str) -> None:
        self.store = store
        self.task_id = task_id
        self.calls = 0

    def required_authority(self, step: Step) -> Authority:
        return Authority.LOCAL

    def execute(self, step: Step) -> AdapterResult:
        self.calls += 1
        if self.calls == 1:
            current = self.store.grant_for_task(self.task_id)
            self.store.replace_permission(
                self.task_id,
                PermissionGrant(
                    id=current.id,
                    authority=Authority.READ,
                    scope=Scope("task"),
                    targets=("test:*",),
                ),
            )
        return AdapterResult(True, True, {"ok": True})


class DriftBindingAdapter:
    def __init__(self) -> None:
        self.bind_calls = 0
        self.execute_calls = 0

    def bind(self, step: Step) -> Step:
        self.bind_calls += 1
        target = "browser:allowed" if self.bind_calls == 1 else "browser:outside"
        return replace(step, target=target)

    def required_authority(self, step: Step) -> Authority:
        return Authority.READ

    def execute(self, step: Step) -> AdapterResult:
        self.execute_calls += 1
        return AdapterResult(True, True, {"ok": True})


class BlockingReadAdapter:
    def __init__(
        self,
        started: threading.Event | None = None,
        release: threading.Event | None = None,
    ) -> None:
        self.started = started
        self.release = release
        self.execute_calls = 0

    def required_authority(self, step: Step) -> Authority:
        return Authority.READ

    def execute(self, step: Step) -> AdapterResult:
        self.execute_calls += 1
        if self.started:
            self.started.set()
        if self.release:
            self.release.wait(timeout=5)
        return AdapterResult(True, True, {"value": "done"})


class ResourceBlockingAdapter(BlockingReadAdapter):
    @staticmethod
    def exclusive_resources(step: Step) -> tuple[str, ...]:
        return ("job-browser:job-applications",)


class ReplaceThenFailAdapter:
    def __init__(self, store: Store, task_id: str) -> None:
        self.store = store
        self.task_id = task_id
        self.external_attempts = 0

    def required_authority(self, step: Step) -> Authority:
        return Authority.READ

    def execute(self, step: Step) -> AdapterResult:
        if step.verb == "replace":
            self.store.replace_permission(
                self.task_id,
                PermissionGrant(
                    id="replacement-answer",
                    authority=Authority.READ,
                    scope=Scope("answer", remaining_uses=1),
                    targets=("test:*",),
                ),
            )
            return AdapterResult(True, True, {"replaced": True})
        self.external_attempts += 1
        return AdapterResult(False, False, {"attempted": True})


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "state.sqlite3")

    def tearDown(self) -> None:
        self.store.close()
        self.temp.cleanup()

    def plan(self, task_id: str, **changes) -> TaskPlan:
        browser_backend = changes.pop("browser_backend", None)
        raw = {
            "task": {
                "id": task_id,
                "goal": "finish the test",
                "permission": {
                    "authority": changes.pop("authority", "full"),
                    "scope": changes.pop("scope", {"kind": "task"}),
                    "targets": changes.pop("targets", ["test:*"]),
                },
                "recipe_key": changes.pop("recipe_key", None),
                "race_ref": changes.pop("race_ref", None),
                "baseline_ms": changes.pop("baseline_ms", None),
                "speed_ratio": changes.pop("speed_ratio", 1.0),
            },
            "steps": changes.pop(
                "steps",
                [
                    {"adapter": "noop", "verb": "read", "target": "test:item"},
                    {
                        "adapter": "noop",
                        "verb": "local",
                        "target": "test:item",
                        "expect": {"equals": {"verb": "local"}},
                    },
                    {
                        "adapter": "noop",
                        "verb": "external",
                        "target": "test:item",
                        "expect": {"equals": {"verb": "external"}},
                    },
                ],
            ),
        }
        if browser_backend is not None:
            raw["task"]["browser_backend"] = browser_backend
        self.assertFalse(changes, f"unused test inputs: {changes}")
        return TaskPlan.from_dict(raw, task_id)

    def test_full_run_finishes_and_saves_recipe(self) -> None:
        engine = Engine(self.store, {"noop": NoopAdapter()})
        result = engine.create_and_run(self.plan("task-ok", recipe_key="fast-test"))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["steps_completed"], 3)
        self.assertEqual(len(self.store.events("task-ok")), 3)
        recipe = self.store.recipe("fast-test")
        self.assertIsNotNone(recipe)
        self.assertEqual(recipe["successes"], 1)

    def test_permission_failure_blocks_before_first_action(self) -> None:
        engine = Engine(self.store, {"noop": NoopAdapter()})
        plan = self.plan("task-block", authority="read")
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.store.events("task-block"), [])

    def test_exit_code_alone_is_not_a_mutation_postcondition(self) -> None:
        engine = Engine(self.store, {"noop": NoopAdapter()})
        plan = self.plan(
            "task-fake-verification",
            steps=[
                {
                    "adapter": "noop",
                    "verb": "external",
                    "target": "test:item",
                    "expect": {"equals": {"exit_code": 0}},
                }
            ],
        )
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("postcondition", result["preflight"]["checks"][0]["reason"])
        self.assertEqual(self.store.events("task-fake-verification"), [])

    def test_empty_contains_is_not_a_mutation_postcondition(self) -> None:
        engine = Engine(self.store, {"noop": NoopAdapter()})
        plan = self.plan(
            "task-empty-verification",
            steps=[
                {
                    "adapter": "noop",
                    "verb": "external",
                    "target": "test:item",
                    "expect": {"contains": {"target": ""}},
                }
            ],
        )
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(self.store.events("task-empty-verification"), [])

    def test_target_failure_blocks_before_first_action(self) -> None:
        engine = Engine(self.store, {"noop": NoopAdapter()})
        plan = self.plan("task-target", targets=["phone:*"])
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("outside", result["preflight"]["checks"][0]["reason"])

    def test_effective_target_is_rebound_immediately_before_execution(self) -> None:
        adapter = DriftBindingAdapter()
        engine = Engine(self.store, {"drift": adapter})
        plan = self.plan(
            "task-target-drift",
            targets=["browser:allowed"],
            steps=[{"adapter": "drift", "verb": "read", "target": "browser:allowed"}],
        )
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(
            result["failure"]["reason"],
            "target 'browser:outside' is outside the permission box",
        )
        self.assertEqual(adapter.execute_calls, 0)
        self.assertEqual(self.store.events("task-target-drift"), [])

    def test_failed_step_is_exact_resume_checkpoint(self) -> None:
        flaky = FlakyAdapter()
        engine = Engine(self.store, {"flaky": flaky})
        plan = self.plan(
            "task-resume",
            steps=[{"adapter": "flaky", "verb": "read", "target": "test:item"}],
        )
        first = engine.create_and_run(plan)
        self.assertEqual(first["status"], "failed")
        self.assertEqual(self.store.task_status("task-resume")["next_step"], 0)
        second = engine.run("task-resume")
        self.assertEqual(second["status"], "completed")
        self.assertEqual(self.store.task_status("task-resume")["next_step"], 1)

    def test_slow_completed_work_is_named_slow(self) -> None:
        engine = Engine(self.store, {"noop": NoopAdapter()})
        plan = self.plan(
            "task-slow",
            baseline_ms=1,
            steps=[
                {
                    "adapter": "noop",
                    "verb": "read",
                    "target": "test:item",
                    "args": {"delay_ms": 15},
                }
            ],
        )
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "completed_slow")
        self.assertFalse(result["speed_pass"])

    def test_request_clock_includes_planning_and_wait_time(self) -> None:
        race = self.store.create_race("race-whole-task", "whole task")
        time.sleep(0.02)
        engine = Engine(self.store, {"noop": NoopAdapter()})
        plan = self.plan(
            "task-whole-race",
            race_ref=race["id"],
            baseline_ms=5,
            steps=[{"adapter": "noop", "verb": "read", "target": "test:item"}],
        )
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "completed_slow")
        self.assertEqual(result["timing_scope"], "request_to_result")
        self.assertGreaterEqual(result["elapsed_ms"], 15)
        self.assertGreaterEqual(result["planning_and_wait_ms"], 10)
        self.assertLessEqual(result["execution_ms"], result["elapsed_ms"])
        saved = self.store.race(race["id"])
        self.assertEqual(saved["claimed_by"], "task-whole-race")
        self.assertIsNotNone(saved["finished_at"])

    def test_answer_permission_is_consumed_once_per_run(self) -> None:
        engine = Engine(self.store, {"noop": NoopAdapter()})
        plan = self.plan(
            "task-answer",
            scope={"kind": "answer"},
            steps=[{"adapter": "noop", "verb": "read", "target": "test:item"}],
        )
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(
            self.store.grant_for_task("task-answer").scope.remaining_uses, 0
        )

    def test_secret_values_are_never_persisted_and_recipe_replay_resolves_reference(
        self,
    ) -> None:
        engine = Engine(self.store, {"noop": NoopAdapter()})
        with patch.dict(os.environ, {"AGENT_BRIDGE_TASK_TEST_SECRET": "secret-value"}):
            plan = self.plan(
                "task-secret",
                recipe_key="secret-recipe",
                steps=[
                    {
                        "adapter": "noop",
                        "verb": "read",
                        "target": "test:item",
                        "args": {
                            "token": {"$secret_env": "AGENT_BRIDGE_TASK_TEST_SECRET"},
                            "safe": "visible",
                        },
                    }
                ],
            )
            result = engine.create_and_run(plan)
            self.assertEqual(result["status"], "completed")
            replay = engine.replay(
                "secret-recipe",
                {
                    "authority": "read",
                    "scope": {"kind": "task"},
                    "targets": ["test:*"],
                },
            )
            self.assertEqual(replay["status"], "completed")
        raw = self.store.events("task-secret")[0]["args_json"]
        self.assertNotIn("secret-value", raw)
        self.assertEqual(json.loads(raw)["token"], "[REDACTED]")
        task_json = self.store.task_row("task-secret")["plan_json"]
        recipe_json = self.store.db.execute(
            "SELECT steps_json FROM recipes WHERE key = ?", ("secret-recipe",)
        ).fetchone()["steps_json"]
        self.assertNotIn("secret-value", task_json)
        self.assertNotIn("secret-value", recipe_json)
        self.assertNotIn(b"secret-value", Path(self.store.path).read_bytes())

    def test_result_urls_are_reduced_to_origin_before_persistence(self) -> None:
        safe = redact(
            {
                "url": (
                    "https://user:password@example.com/magic/path-token"
                    "?access_token=hidden#fragment"
                )
            }
        )
        self.assertEqual(safe["url"], "https://example.com")
        encoded = json.dumps(safe)
        for secret in ("user", "password", "path-token", "hidden", "fragment"):
            self.assertNotIn(secret, encoded)

    def test_result_url_redaction_does_not_depend_on_the_key_name(self) -> None:
        for key in ("link", "redirect", "location", "website"):
            with self.subTest(key=key):
                self.assertEqual(
                    redact(
                        {key: "https://example.com/private?access_token=secret#code=x"}
                    )[key],
                    "https://example.com",
                )

    def test_embedded_result_urls_are_reduced_to_origin_before_persistence(
        self,
    ) -> None:
        safe = redact(
            {
                "text": (
                    "Open HTTPS://user:password@example.com/private,"
                    "access_token=secret#fragment now"
                )
            }
        )
        self.assertEqual(safe["text"], "Open https://example.com now")

    def test_inline_secret_is_rejected_before_storage(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "must use \\$secret_env or \\$secret_file"
        ):
            self.plan(
                "task-inline-secret",
                steps=[
                    {
                        "adapter": "noop",
                        "verb": "read",
                        "target": "test:item",
                        "args": {"credential": "secret-value"},
                        "secret_fields": ["credential"],
                    }
                ],
            )

    def test_secret_fields_string_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "secret_fields must be a list"):
            self.plan(
                "task-bad-secret-fields",
                steps=[
                    {
                        "adapter": "noop",
                        "verb": "read",
                        "target": "test:item",
                        "args": {"credential": "inline-secret"},
                        "secret_fields": "credential",
                    }
                ],
            )

    def test_nested_provider_api_key_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
            self.plan(
                "task-provider-secret",
                steps=[
                    {
                        "adapter": "noop",
                        "verb": "read",
                        "target": "test:item",
                        "args": {"env": {"OPENAI_API_KEY": "sk-inline-leak"}},
                    }
                ],
            )

    def test_credential_bearing_url_is_rejected_before_plan_storage(self) -> None:
        with self.assertRaisesRegex(ValueError, "Sensitive URL"):
            self.plan(
                "task-sensitive-url",
                steps=[
                    {
                        "adapter": "browser",
                        "verb": "open",
                        "target": "browser:https://example.com",
                        "args": {
                            "arguments": [
                                "https://example.com/callback?access_token=inline-secret"
                            ]
                        },
                        "expect": {"contains": {"payload.url": "example.com"}},
                    }
                ],
            )

    def test_credential_bearing_step_target_is_rejected_before_storage(self) -> None:
        with self.assertRaisesRegex(ValueError, "Sensitive URL"):
            self.plan(
                "task-sensitive-target",
                steps=[
                    {
                        "adapter": "browser",
                        "verb": "read",
                        "target": "browser:https://example.com/path?access_token=inline-secret",
                    }
                ],
            )

        with self.assertRaisesRegex(ValueError, "Sensitive URL"):
            Step.from_dict(
                {
                    "adapter": "browser",
                    "verb": "read",
                    "target": "https://example.com/path?access_token=inline-secret",
                }
            )

    def test_browser_permission_target_must_be_an_origin(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be an origin"):
            PermissionGrant.from_dict(
                "path-target",
                {
                    "authority": "read",
                    "scope": {"kind": "task"},
                    "targets": ["browser:https://example.com/private/path"],
                },
            )

    def test_direct_permission_target_string_cannot_become_character_globs(
        self,
    ) -> None:
        grant = PermissionGrant(
            id="direct-string-target",
            authority=Authority.FULL,
            scope=Scope("standing"),
            targets="browser:*",  # type: ignore[arg-type]
        )
        with self.assertRaisesRegex(ValueError, "list of non-empty strings"):
            self.store.create_grant(grant)

    def test_direct_dataclass_secret_is_rejected_by_store(self) -> None:
        grant = PermissionGrant(
            id="direct-secret-grant",
            authority=Authority.READ,
            scope=Scope("task"),
            targets=("test:*",),
        )
        plan = TaskPlan(
            id="direct-secret-task",
            goal="reject direct secret",
            permission=grant,
            steps=(
                Step(
                    "noop",
                    "read",
                    "test:item",
                    args={"token": "direct-inline-secret"},
                ),
            ),
        )
        with self.assertRaisesRegex(ValueError, "must use"):
            self.store.save_plan(plan)
        with self.assertRaises(KeyError):
            self.store.task_row("direct-secret-task")
        with self.assertRaisesRegex(ValueError, "must use"):
            self.store.save_recipe(
                "direct-secret-recipe",
                "reject direct recipe secret",
                [
                    {
                        "adapter": "noop",
                        "verb": "read",
                        "target": "test:item",
                        "args": {"token": "direct-inline-secret"},
                    }
                ],
                1,
            )
        self.assertIsNone(self.store.recipe("direct-secret-recipe"))

    def test_process_adapter_runs_exact_argv_without_shell(self) -> None:
        engine = Engine(self.store, {"process": ProcessAdapter()})
        plan = self.plan(
            "task-process",
            authority="full",
            targets=["process:*"],
            steps=[
                {
                    "adapter": "process",
                    "verb": "read",
                    "target": "test:python",
                    "args": {"argv": ["python3", "-c", "print('apple')"]},
                    "expect": {"contains": {"stdout": "apple"}},
                }
            ],
        )
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "completed")

    def test_process_permission_is_bound_to_the_resolved_executable(self) -> None:
        echo = Path(shutil.which("echo") or "/bin/echo").absolute()
        engine = Engine(self.store, {"process": ProcessAdapter()})
        plan = self.plan(
            "task-process-target",
            authority="full",
            targets=[f"process:{echo}"],
            steps=[
                {
                    "adapter": "process",
                    "verb": "read",
                    "target": f"process:{echo}",
                    "args": {"argv": ["true"]},
                    "expect": {"contains": {"stdout": "never-run"}},
                }
            ],
        )
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("outside", result["preflight"]["checks"][0]["reason"])
        self.assertEqual(self.store.events("task-process-target"), [])

    def test_newer_permission_takes_effect_between_steps(self) -> None:
        task_id = "task-downgrade"
        adapter = DowngradeAdapter(self.store, task_id)
        engine = Engine(self.store, {"change": adapter})
        plan = self.plan(
            task_id,
            steps=[
                {
                    "adapter": "change",
                    "verb": "one",
                    "target": "test:item",
                    "expect": {"equals": {"ok": True}},
                },
                {
                    "adapter": "change",
                    "verb": "two",
                    "target": "test:item",
                    "expect": {"equals": {"ok": True}},
                },
            ],
        )
        result = engine.create_and_run(plan)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["steps_completed"], 1)
        self.assertEqual(len(self.store.events(task_id)), 1)
        self.assertIn("needs level 3", result["failure"]["reason"])

    def test_replacement_limited_grant_is_reserved_before_its_first_step(self) -> None:
        task_id = "task-mid-run-answer"
        adapter = ReplaceThenFailAdapter(self.store, task_id)
        plan = self.plan(
            task_id,
            steps=[
                {"adapter": "change", "verb": "replace", "target": "test:item"},
                {"adapter": "change", "verb": "attempt", "target": "test:item"},
            ],
        )
        engine = Engine(self.store, {"change": adapter})
        first = engine.create_and_run(plan)
        self.assertEqual(first["status"], "failed")
        self.assertEqual(adapter.external_attempts, 1)
        self.assertEqual(
            self.store.grant_for_task(task_id).scope.remaining_uses,
            0,
        )
        resumed = engine.run(task_id)
        self.assertEqual(resumed["status"], "blocked")
        self.assertEqual(adapter.external_attempts, 1)

    def test_shared_five_answer_style_permission_counts_across_tasks(self) -> None:
        shared = PermissionGrant(
            id="shared-two-runs",
            authority=Authority.READ,
            scope=Scope("turns", remaining_uses=2),
            targets=("test:*",),
        )
        self.store.create_grant(shared)
        engine = Engine(self.store, {"noop": NoopAdapter()})
        statuses = []
        for index in range(3):
            task_id = f"shared-task-{index}"
            plan = TaskPlan.from_dict(
                {
                    "task": {
                        "id": task_id,
                        "goal": "use one shared answer permission",
                        "permission_ref": shared.id,
                    },
                    "steps": [
                        {"adapter": "noop", "verb": "read", "target": "test:item"}
                    ],
                },
                task_id,
            )
            statuses.append(engine.create_and_run(plan)["status"])
        self.assertEqual(statuses, ["completed", "completed", "blocked"])
        self.assertEqual(self.store.grant(shared.id).scope.remaining_uses, 0)

    def test_inline_task_permission_is_bound_to_its_plan_id(self) -> None:
        plan = self.plan("task-inline-bound")
        self.store.save_plan(plan)
        self.assertEqual(
            self.store.grant_for_task("task-inline-bound").scope.value,
            "task-inline-bound",
        )

    def test_replacement_task_permission_is_bound_to_its_task_id(self) -> None:
        plan = self.plan("task-replacement-bound")
        self.store.save_plan(plan)
        replacement = PermissionGrant(
            id="ignored-replacement-id",
            authority=Authority.READ,
            scope=Scope("task"),
            targets=("test:*",),
        )
        self.store.replace_permission("task-replacement-bound", replacement)
        self.assertEqual(
            self.store.grant_for_task("task-replacement-bound").scope.value,
            "task-replacement-bound",
        )

    def test_unbound_shared_task_permission_is_rejected(self) -> None:
        shared = PermissionGrant(
            id="shared-unbound-task",
            authority=Authority.READ,
            scope=Scope("task"),
            targets=("test:*",),
        )
        with self.assertRaisesRegex(ValueError, "concrete task ID"):
            self.store.create_grant(shared)

    def test_bound_shared_task_permission_cannot_attach_to_another_task(self) -> None:
        shared = PermissionGrant(
            id="shared-bound-task",
            authority=Authority.READ,
            scope=Scope("task", "task-owner"),
            targets=("test:*",),
        )
        self.store.create_grant(shared)
        plan = TaskPlan.from_dict(
            {
                "task": {
                    "id": "task-intruder",
                    "goal": "reuse another task permission",
                    "permission_ref": shared.id,
                },
                "steps": [{"adapter": "noop", "verb": "read", "target": "test:item"}],
            },
            "task-intruder",
        )
        with self.assertRaisesRegex(ValueError, "another task"):
            self.store.save_plan(plan)

    def save_two_tasks_with_shared_grant(self, grant_id: str) -> None:
        shared = PermissionGrant(
            id=grant_id,
            authority=Authority.READ,
            scope=Scope("standing"),
            targets=("test:*",),
        )
        self.store.create_grant(shared)
        for suffix in ("one", "two"):
            task_id = f"{grant_id}-{suffix}"
            plan = TaskPlan.from_dict(
                {
                    "task": {
                        "id": task_id,
                        "goal": "shared permission isolation",
                        "permission_ref": shared.id,
                    },
                    "steps": [
                        {"adapter": "noop", "verb": "read", "target": "test:item"}
                    ],
                },
                task_id,
            )
            self.store.save_plan(plan)

    def test_permit_detaches_one_task_from_a_shared_grant(self) -> None:
        self.save_two_tasks_with_shared_grant("shared-permit")
        self.store.replace_permission(
            "shared-permit-one",
            PermissionGrant(
                id="ignored",
                authority=Authority.TALK,
                scope=Scope("task"),
                targets=("test:*",),
            ),
        )
        self.assertEqual(
            self.store.grant_for_task("shared-permit-one").authority, Authority.TALK
        )
        self.assertEqual(
            self.store.grant_for_task("shared-permit-two").authority, Authority.READ
        )
        self.assertNotEqual(
            self.store.task_row("shared-permit-one")["grant_id"],
            self.store.task_row("shared-permit-two")["grant_id"],
        )

    def test_revoke_detaches_one_task_from_a_shared_grant(self) -> None:
        self.save_two_tasks_with_shared_grant("shared-revoke")
        self.store.revoke_permission("shared-revoke-one")
        self.assertIsNotNone(self.store.grant_for_task("shared-revoke-one").revoked_at)
        self.assertIsNone(self.store.grant_for_task("shared-revoke-two").revoked_at)

    def test_one_remaining_permission_run_is_reserved_atomically(self) -> None:
        shared = PermissionGrant(
            id="shared-one-run",
            authority=Authority.READ,
            scope=Scope("turns", remaining_uses=1),
            targets=("test:*",),
        )
        self.store.create_grant(shared)
        barrier = threading.Barrier(3)
        results: list[bool] = []
        lock = threading.Lock()

        def reserve() -> None:
            store = Store(self.store.path)
            try:
                barrier.wait()
                reserved = store.reserve_permission_run(shared.id)
                with lock:
                    results.append(reserved)
            finally:
                store.close()

        threads = [threading.Thread(target=reserve) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())

        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(self.store.grant(shared.id).scope.remaining_uses, 0)

    def test_same_task_cannot_run_twice_concurrently(self) -> None:
        plan = self.plan(
            "task-single-runner",
            steps=[{"adapter": "blocking", "verb": "read", "target": "test:item"}],
        )
        self.store.save_plan(plan)
        started = threading.Event()
        release = threading.Event()
        first_adapter = BlockingReadAdapter(started, release)
        first_result: list[dict] = []

        def run_first() -> None:
            store = Store(self.store.path)
            try:
                first_result.append(
                    Engine(store, {"blocking": first_adapter}).run("task-single-runner")
                )
            finally:
                store.close()

        thread = threading.Thread(target=run_first)
        thread.start()
        self.assertTrue(started.wait(timeout=5))
        second_adapter = BlockingReadAdapter()
        second = Engine(self.store, {"blocking": second_adapter}).run(
            "task-single-runner"
        )
        self.assertEqual(second["status"], "blocked")
        self.assertIn("already running", second["preflight"]["reason"])
        self.assertEqual(second_adapter.execute_calls, 0)
        release.set()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(first_result[0]["status"], "completed")

    def test_different_tasks_cannot_interleave_one_browser_profile(self) -> None:
        first_plan = self.plan(
            "task-browser-one",
            browser_backend="laptop-chrome",
            steps=[{"adapter": "browser", "verb": "read", "target": "test:item"}],
        )
        second_plan = self.plan(
            "task-browser-two",
            browser_backend="laptop-chrome",
            steps=[{"adapter": "browser", "verb": "read", "target": "test:item"}],
        )
        self.store.save_plan(first_plan)
        self.store.save_plan(second_plan)
        started = threading.Event()
        release = threading.Event()
        first_adapter = ResourceBlockingAdapter(started, release)
        first_result: list[dict] = []

        def run_first() -> None:
            store = Store(self.store.path)
            try:
                first_result.append(
                    Engine(store, {"browser": first_adapter}).run("task-browser-one")
                )
            finally:
                store.close()

        thread = threading.Thread(target=run_first)
        thread.start()
        self.assertTrue(started.wait(timeout=5))
        second_adapter = ResourceBlockingAdapter()
        second = Engine(self.store, {"browser": second_adapter}).run("task-browser-two")
        self.assertEqual(second["status"], "blocked")
        self.assertIn("job-browser:job-applications", second["preflight"]["reason"])
        self.assertEqual(second_adapter.execute_calls, 0)
        release.set()
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(first_result[0]["status"], "completed")

    def test_orphaned_running_task_can_be_recovered_after_lock_release(self) -> None:
        plan = self.plan(
            "task-stale-runner",
            steps=[{"adapter": "noop", "verb": "read", "target": "test:item"}],
        )
        self.store.save_plan(plan)
        old_lock = self.store.acquire_task_lock("task-stale-runner")
        self.assertIsNotNone(old_lock)
        self.assertTrue(
            self.store.start_run("run-stale-old", "task-stale-runner", "old receipt", 0)
        )
        competing_store = Store(self.store.path)
        try:
            self.assertIsNone(competing_store.acquire_task_lock("task-stale-runner"))
        finally:
            competing_store.close()
        self.store.release_task_lock(old_lock)

        replacement_lock = self.store.acquire_task_lock("task-stale-runner")
        self.assertIsNotNone(replacement_lock)
        self.assertTrue(
            self.store.start_run("run-stale-new", "task-stale-runner", "new receipt", 0)
        )
        self.store.release_task_lock(replacement_lock)
        old = self.store.db.execute(
            "SELECT status FROM runs WHERE id = ?", ("run-stale-old",)
        ).fetchone()
        self.assertEqual(old["status"], "abandoned")


if __name__ == "__main__":
    unittest.main()
