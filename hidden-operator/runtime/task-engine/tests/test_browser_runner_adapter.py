from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from unittest.mock import Mock, call, patch

from agent_bridge_task.adapters import (
    BrowserRunnerAdapter,
    BrowserRunnerClient,
    canonical_browser_target,
    canonical_file_target,
    default_adapters,
)
from agent_bridge_task.engine import Engine
from agent_bridge_task.models import Authority, TaskPlan, Step


class FakeRunnerClient:
    def __init__(self, url: str = "https://example.com/current?token=hidden#part"):
        self.backend = "laptop-chrome"
        self.url = url
        self.ready_error: Exception | None = None
        self.ready_calls = 0
        self.page_token = "a" * 64
        self.commands: list[tuple[list[str], str | None, str | None, str | None]] = []
        self.result = {
            "code": 0,
            "stdout": "",
            "stderr": "",
            "result": {
                "action": "read",
                "url": url,
                "text": "apple",
                "effect": {
                    "kind": "semantic-change",
                    "verified": True,
                    "changed": True,
                },
            },
        }

    def ensure_ready(self):
        self.ready_calls += 1
        if self.ready_error:
            raise self.ready_error
        return {
            "code": 0,
            "status": "ready",
            "profile": "job-applications",
            "backend": "laptop-chrome",
            "protocol": BrowserRunnerClient.EXPECTED_PROTOCOL,
        }

    def current_page(self):
        self.ensure_ready()
        return {
            "url": canonical_browser_target(self.url).removeprefix("browser:"),
            "pageToken": self.page_token,
            "status": "ready",
        }

    def command(
        self,
        arguments,
        *,
        expected_url=None,
        expected_page_token=None,
        allowed_origin=None,
    ):
        self.commands.append(
            (arguments, expected_url, expected_page_token, allowed_origin)
        )
        return self.result


class BrowserRunnerAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = FakeRunnerClient()
        self.adapter = BrowserRunnerAdapter(self.client)

    def step(self, verb: str, arguments=None, **args) -> Step:
        return Step(
            "browser",
            verb,
            "browser:claimed.example",
            args={"arguments": arguments or [], **args},
        )

    def test_canonical_target_uses_real_url_without_query_or_fragment(self) -> None:
        self.assertEqual(
            canonical_browser_target("HTTPS://Example.COM:443/path?q=1#part"),
            "browser:https://example.com",
        )

    def test_default_browser_adapter_is_the_authenticated_job_runner(self) -> None:
        adapters = default_adapters()
        self.assertIsInstance(adapters["browser"], BrowserRunnerAdapter)
        self.assertNotIn("process", adapters)
        self.assertNotIn("noop", adapters)

    def test_authority_classes_and_neutral_continue(self) -> None:
        self.assertEqual(
            self.adapter.required_authority(self.step("read")), Authority.READ
        )
        self.assertEqual(
            self.adapter.required_authority(self.step("download", ["Resume"])),
            Authority.COLLECT,
        )
        self.assertEqual(
            self.adapter.required_authority(self.step("screenshot")),
            Authority.COLLECT,
        )
        self.assertEqual(
            self.adapter.required_authority(self.step("fill", ["Name", "George"])),
            Authority.EXTERNAL,
        )
        self.assertEqual(
            self.adapter.required_authority(self.step("click", ["Continue"])),
            Authority.EXTERNAL,
        )
        self.assertEqual(
            self.adapter.required_authority(self.step("eval", ["document.title"])),
            Authority.FULL,
        )

    def test_effect_can_raise_but_never_lower(self) -> None:
        self.assertEqual(
            self.adapter.required_authority(
                self.step("fill", ["Name", "x"], effect="external")
            ),
            Authority.EXTERNAL,
        )
        self.assertEqual(
            self.adapter.required_authority(
                self.step("click", ["Continue"], effect="read")
            ),
            Authority.EXTERNAL,
        )

    def test_secret_reference_can_occupy_a_browser_argument(self) -> None:
        step = Step(
            "browser",
            "fill",
            "browser:claimed",
            args={
                "arguments": [
                    "Password",
                    {"$secret_env": "AGENT_BRIDGE_TASK_BROWSER_PASSWORD"},
                ]
            },
        )
        self.assertEqual(self.adapter.required_authority(step), Authority.EXTERNAL)

    def test_open_binds_permission_to_actual_url(self) -> None:
        bound = self.adapter.bind(
            self.step("open", ["https://outside.example/job?source=x"])
        )
        self.assertEqual(bound.target, "browser:https://outside.example")
        self.assertNotIn("_expected_url", bound.args)
        self.assertNotIn("_expected_page_token", bound.args)

    def test_current_page_observation_is_atomically_guarded(self) -> None:
        bound = self.adapter.bind(
            Step(
                "browser",
                "read",
                "browser:claimed.example",
                args={"arguments": []},
                expect={"contains": {"payload.text": "apple"}},
            )
        )
        self.assertEqual(bound.target, "browser:https://example.com")
        result = self.adapter.execute(bound)
        self.assertTrue(result.verified)
        self.assertEqual(
            self.client.commands,
            [
                (
                    ["read"],
                    None,
                    "a" * 64,
                    "https://example.com",
                )
            ],
        )

    def test_claimed_target_cannot_authorize_another_open_url(self) -> None:
        plan = TaskPlan.from_dict(
            {
                "task": {
                    "goal": "target test",
                    "browser_backend": "laptop-chrome",
                    "permission": {
                        "authority": "full",
                        "scope": {"kind": "test"},
                        "targets": ["browser:https://allowed.example"],
                    },
                },
                "steps": [
                    {
                        "adapter": "browser",
                        "verb": "open",
                        "target": "browser:https://allowed.example",
                        "args": {"arguments": ["https://outside.example/"]},
                        "expect": {
                            "equals": {"payload.effect.verified": True},
                            "contains": {"payload.url": "outside.example"},
                        },
                    }
                ],
            },
            "target-test",
        )
        check = Engine(None, {"browser": self.adapter}).preflight(plan)
        self.assertFalse(check["allowed"])
        self.assertEqual(
            check["checks"][0]["target"], "browser:https://outside.example"
        )
        self.assertEqual(self.client.commands, [])

    def test_batch_accepts_only_observations_plus_optional_first_open(self) -> None:
        step = Step(
            "browser",
            "batch",
            "browser:claimed",
            args={
                "steps": [
                    {"verb": "open", "arguments": ["https://example.com/"]},
                    {"verb": "read", "arguments": []},
                ]
            },
        )
        self.assertEqual(self.adapter.required_authority(step), Authority.LOCAL)
        for verb in ("click", "fill", "upload", "eval", "ashby-submit"):
            forbidden = Step(
                "browser",
                "batch",
                "browser:claimed",
                args={"steps": [{"verb": verb, "arguments": []}]},
            )
            with (
                self.subTest(verb=verb),
                self.assertRaisesRegex(ValueError, "unsafe action"),
            ):
                self.adapter.required_authority(forbidden)

    def test_denied_nested_open_cannot_hide_behind_batch(self) -> None:
        plan = TaskPlan.from_dict(
            {
                "task": {
                    "goal": "respect nested denial",
                    "browser_backend": "laptop-chrome",
                    "permission": {
                        "authority": "full",
                        "scope": {"kind": "test"},
                        "targets": ["browser:https://example.com"],
                        "denied_actions": ["browser:open"],
                    },
                },
                "steps": [
                    {
                        "adapter": "browser",
                        "verb": "batch",
                        "target": "browser:https://example.com",
                        "args": {
                            "steps": [
                                {
                                    "verb": "open",
                                    "arguments": ["https://example.com/"],
                                },
                                {"verb": "read", "arguments": []},
                            ]
                        },
                        "expect": {
                            "equals": {
                                "payload.results.0.result.effect.verified": True
                            },
                            "contains": {
                                "payload.results.1.result.text": "Example",
                                "payload.results.0.result.url": "example.com",
                            },
                        },
                    }
                ],
            },
            "nested-denial",
        )
        check = Engine(None, {"browser": self.adapter}).preflight(plan)
        self.assertFalse(check["allowed"])
        self.assertIn("explicitly denied", check["checks"][0]["reason"])
        self.assertEqual(self.client.commands, [])

    def test_batch_translates_saved_numeric_read_limit(self) -> None:
        step = Step(
            "browser",
            "batch",
            "browser:https://example.com",
            args={
                "steps": [
                    {"verb": "open", "arguments": ["https://example.com/"]},
                    {"verb": "read", "arguments": ["2000"]},
                ]
            },
            expect={"contains": {"payload.text": "apple"}},
        )
        self.adapter.execute(step)
        arguments, _, _, _ = self.client.commands[0]
        self.assertEqual(arguments[0], "batch")
        payload = json.loads(arguments[1])
        self.assertEqual(payload[1]["arguments"], ["--limit", "2000"])

    def test_ashby_spec_binds_to_apply_url(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            spec = Path(directory) / "application.json"
            spec.write_text(
                json.dumps(
                    {"apply_url": "https://jobs.ashbyhq.com/company/job/application"}
                ),
                encoding="utf-8",
            )
            bound = self.adapter.bind(self.step("ashby-stage", [str(spec)]))
        self.assertEqual(
            bound.target,
            "browser:https://jobs.ashbyhq.com",
        )

    def test_greenhouse_spec_binds_to_apply_url_and_exact_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            answer_bank = root / "answers.json"
            resume = root / "resume.pdf"
            cover = root / "cover.pdf"
            answer_bank.write_text("{}", encoding="utf-8")
            resume.write_bytes(b"resume")
            cover.write_bytes(b"cover")
            spec = root / "application.json"
            spec.write_text(
                json.dumps(
                    {
                        "apply_url": "https://job-boards.greenhouse.io/eve/jobs/4257562009",
                        "answer_bank": answer_bank.name,
                        "documents": {
                            "resume": {"path": resume.name},
                            "cover_letter": {"path": cover.name},
                        },
                    }
                ),
                encoding="utf-8",
            )
            bound = self.adapter.bind(self.step("greenhouse-stage", [str(spec)]))
            targets = self.adapter.permission_steps(bound)
            self.assertEqual(
                bound.target, "browser:https://job-boards.greenhouse.io"
            )
            self.assertEqual(
                {step.target for step in targets},
                {
                    canonical_file_target(str(spec)),
                    canonical_file_target(str(answer_bank)),
                    canonical_file_target(str(resume)),
                    canonical_file_target(str(cover)),
                },
            )

    def test_upload_requires_permission_for_the_exact_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            resume = Path(directory) / "resume.pdf"
            resume.write_bytes(b"resume")
            raw = {
                "task": {
                    "goal": "upload one permitted resume",
                    "browser_backend": "laptop-chrome",
                    "permission": {
                        "authority": "full",
                        "scope": {"kind": "test"},
                        "targets": ["browser:https://example.com"],
                    },
                },
                "steps": [
                    {
                        "adapter": "browser",
                        "verb": "upload",
                        "target": "browser:https://example.com",
                        "args": {"arguments": ["Resume", str(resume)]},
                        "expect": {"equals": {"payload.effect.verified": True}},
                    }
                ],
            }
            denied = TaskPlan.from_dict(raw, "upload-source-denied")
            check = Engine(None, {"browser": self.adapter}).preflight(denied)
            self.assertFalse(check["allowed"])
            self.assertIn("outside the permission box", check["checks"][0]["reason"])

            raw["task"]["permission"]["targets"].append(
                canonical_file_target(str(resume))
            )
            allowed = TaskPlan.from_dict(raw, "upload-source-allowed")
            check = Engine(None, {"browser": self.adapter}).preflight(allowed)
            self.assertFalse(check["allowed"])
            self.assertIn("safely replay", check["checks"][0]["reason"])

    def test_artifact_read_binds_to_the_exact_file_not_the_current_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "state.json"
            artifact.write_text("{}", encoding="utf-8")
            bound = self.adapter.bind(self.step("artifact-read", [str(artifact)]))
            self.assertEqual(bound.target, canonical_file_target(str(artifact)))
            self.assertEqual(self.client.ready_calls, 0)

    def test_ashby_requires_permission_for_spec_answer_bank_and_documents(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            answer_bank = root / "answers.json"
            resume = root / "resume.pdf"
            cover = root / "cover.pdf"
            answer_bank.write_text("{}", encoding="utf-8")
            resume.write_bytes(b"resume")
            cover.write_bytes(b"cover")
            spec = root / "application.json"
            spec.write_text(
                json.dumps(
                    {
                        "apply_url": "https://jobs.ashbyhq.com/company/job/application",
                        "answer_bank": answer_bank.name,
                        "documents": {
                            "resume": {"path": resume.name},
                            "cover_letter": {"path": cover.name},
                        },
                    }
                ),
                encoding="utf-8",
            )
            raw = {
                "task": {
                    "goal": "stage only named local documents",
                    "browser_backend": "laptop-chrome",
                    "permission": {
                        "authority": "full",
                        "scope": {"kind": "test"},
                        "targets": ["browser:https://jobs.ashbyhq.com"],
                    },
                },
                "steps": [
                    {
                        "adapter": "browser",
                        "verb": "ashby-stage",
                        "target": "browser:https://jobs.ashbyhq.com",
                        "args": {"arguments": [str(spec)]},
                        "expect": {"equals": {"payload.status": "ready"}},
                    }
                ],
            }
            denied = TaskPlan.from_dict(raw, "ashby-files-denied")
            check = Engine(None, {"browser": self.adapter}).preflight(denied)
            self.assertFalse(check["allowed"])
            self.assertIn("outside the permission box", check["checks"][0]["reason"])

            raw["task"]["permission"]["targets"].extend(
                canonical_file_target(str(path))
                for path in (spec, answer_bank, resume, cover)
            )
            allowed = TaskPlan.from_dict(raw, "ashby-files-allowed")
            check = Engine(None, {"browser": self.adapter}).preflight(allowed)
            self.assertTrue(check["allowed"])

    def test_mutation_without_postcondition_is_not_verified(self) -> None:
        result = self.adapter.execute(self.step("fill", ["Name", "George"]))
        self.assertTrue(result.ok)
        self.assertFalse(result.verified)
        self.assertIn("no semantic postcondition", result.data["verification"])

    def test_generic_click_is_blocked_before_the_runner_can_act(self) -> None:
        plan = TaskPlan.from_dict(
            {
                "task": {
                    "goal": "do not replay an ambiguous click",
                    "browser_backend": "laptop-chrome",
                    "permission": {
                        "authority": "full",
                        "scope": {"kind": "test"},
                        "targets": ["browser:https://example.com"],
                    },
                },
                "steps": [
                    {
                        "adapter": "browser",
                        "verb": "click",
                        "target": "browser:https://example.com",
                        "args": {"arguments": ["Submit"]},
                        "expect": {
                            "equals": {"payload.effect.verified": True},
                            "contains": {"payload.text": "Thank you"},
                        },
                    }
                ],
            },
            "ambiguous-click-blocked",
        )
        check = Engine(None, {"browser": self.adapter}).preflight(plan)
        self.assertFalse(check["allowed"])
        self.assertIn("safely replay", check["checks"][0]["reason"])
        self.assertEqual(self.client.commands, [])

    def test_eval_is_blocked_even_when_the_dom_effect_claims_success(self) -> None:
        plan = TaskPlan.from_dict(
            {
                "task": {
                    "goal": "reject unverifiable JavaScript effects",
                    "browser_backend": "laptop-chrome",
                    "permission": {
                        "authority": "full",
                        "scope": {"kind": "test"},
                        "targets": ["browser:https://example.com"],
                    },
                },
                "steps": [
                    {
                        "adapter": "browser",
                        "verb": "eval",
                        "target": "browser:https://example.com",
                        "args": {"arguments": ["fetch('/delete')"]},
                        "expect": {
                            "equals": {"payload.effect.verified": True},
                            "contains": {"payload.value": "done"},
                        },
                    }
                ],
            },
            "eval-proof-rejected",
        )
        check = Engine(None, {"browser": self.adapter}).preflight(plan)
        self.assertFalse(check["allowed"])
        self.assertIn("safely replay", check["checks"][0]["reason"])

    def test_degraded_runtime_fails_before_action(self) -> None:
        self.client.ready_error = RuntimeError(
            "job browser is not ready: tunnel exited"
        )
        result = self.adapter.execute(self.step("read"))
        self.assertFalse(result.ok)
        self.assertIn("tunnel exited", result.data["error"])
        self.assertEqual(self.client.commands, [])


class BrowserRunnerClientTests(unittest.TestCase):
    def test_missing_phone_daemon_is_started_once(self) -> None:
        client = BrowserRunnerClient(
            socket_path="/tmp/not-used", backend="phone-headless"
        )
        ready = {
            "code": 0,
            "status": "ready",
            "profile": "job-applications",
            "backend": "phone-headless",
            "protocol": BrowserRunnerClient.EXPECTED_PROTOCOL,
        }
        with patch.object(
            client,
            "_request",
            side_effect=[ConnectionRefusedError(111, "refused"), ready],
        ), patch.object(client, "_start_daemon") as start, patch(
            "agent_bridge_task.adapters.time.sleep"
        ):
            self.assertEqual(client.ensure_ready(), ready)
        start.assert_called_once_with()

    def test_accepted_command_waits_for_daemon_terminal_result(self) -> None:
        connection = Mock()
        connection.recv.side_effect = [b'{"code":0}\n']
        client = BrowserRunnerClient(
            socket_path="/tmp/browser.sock", backend="laptop-chrome"
        )
        with patch("agent_bridge_task.adapters.socket.socket", return_value=connection):
            response = client._request({"argv": ["status"]})

        self.assertEqual(response["code"], 0)
        self.assertEqual(connection.settimeout.call_args_list, [call(3.0), call(None)])

    def test_fixed_profile_and_backend_are_sent_to_daemon(self) -> None:
        client = BrowserRunnerClient(
            socket_path="/tmp/not-used", backend="phone-headless"
        )
        with patch.object(
            client,
            "_request",
            return_value={"code": 0, "stdout": '{"url":"https://example.com/"}'},
        ) as request:
            response = client.command(
                ["read", "--limit", "1000"],
                expected_page_token="a" * 64,
                allowed_origin="https://example.com",
            )

        self.assertEqual(response["result"]["url"], "https://example.com/")
        request.assert_called_once_with(
            {
                "profile": "job-applications",
                "argv": [
                    "--profile",
                    "job-applications",
                    "--backend",
                    "phone-headless",
                    "read",
                    "--limit",
                    "1000",
                ],
                "expectedPageToken": "a" * 64,
                "allowedOrigin": "https://example.com",
            }
        )

    def test_control_status_requires_the_exact_runtime(self) -> None:
        client = BrowserRunnerClient(
            socket_path="/tmp/not-used", backend="laptop-chrome"
        )
        with patch.object(
            client,
            "_request",
            return_value={
                "code": 0,
                "status": "ready",
                "profile": "other",
                "backend": "laptop-chrome",
                "protocol": BrowserRunnerClient.EXPECTED_PROTOCOL,
            },
        ):
            with self.assertRaisesRegex(RuntimeError, "job browser is not ready"):
                client.ensure_ready()

    def test_control_status_rejects_a_stale_runner_protocol(self) -> None:
        client = BrowserRunnerClient(
            socket_path="/tmp/not-used", backend="laptop-chrome"
        )
        with patch.object(
            client,
            "_request",
            return_value={
                "code": 0,
                "status": "ready",
                "profile": "job-applications",
                "backend": "laptop-chrome",
            },
        ):
            with self.assertRaisesRegex(RuntimeError, "protocol is incompatible"):
                client.ensure_ready()


if __name__ == "__main__":
    unittest.main()
