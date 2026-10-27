from __future__ import annotations

import unittest

from agent_bridge_task.adapters import GoogleConsoleAdapter
from agent_bridge_task.engine import Engine
from agent_bridge_task.models import Authority, Step, TaskPlan


class GoogleConsoleAdapterTests(unittest.TestCase):
    def test_empty_command_payload_cannot_verify_a_console_mutation(self) -> None:
        adapter = GoogleConsoleAdapter(binary="unused")
        plan = TaskPlan.from_dict(
            {
                "task": {
                    "goal": "reject command-only proof",
                    "permission": {
                        "authority": "full",
                        "scope": {"kind": "task"},
                        "targets": ["google-console:george"],
                    },
                },
                "steps": [
                    {
                        "adapter": "google-console",
                        "verb": "click",
                        "target": "google-console:george",
                        "expect": {"equals": {"payload": {}}},
                    }
                ],
            },
            "google-fake-proof",
        )
        check = Engine(None, {"google-console": adapter}).preflight(plan)
        self.assertFalse(check["allowed"])
        self.assertIn("intrinsic post-action proof", check["checks"][0]["reason"])

    def test_whole_console_is_one_exclusive_resource(self) -> None:
        adapter = GoogleConsoleAdapter(binary="unused")
        self.assertEqual(
            adapter.exclusive_resources(
                Step("google-console", "read", "google-console:george")
            ),
            ("google-console:george",),
        )

    def test_target_is_bound_to_georges_authenticated_console(self) -> None:
        adapter = GoogleConsoleAdapter(binary="unused")
        bound = adapter.bind(
            Step(
                "google-console",
                "open",
                "google-console:claimed",
                args={"arguments": ["https://example.com/"]},
            )
        )
        self.assertEqual(bound.target, "google-console:george")

    def test_form_actions_default_to_external(self) -> None:
        adapter = GoogleConsoleAdapter(binary="unused")
        for verb in ("click", "fill", "upload", "frame-click", "frame-fill"):
            with self.subTest(verb=verb):
                self.assertEqual(
                    adapter.required_authority(
                        Step("google-console", verb, "google-console:george")
                    ),
                    Authority.EXTERNAL,
                )

    def test_screenshot_is_a_new_download(self) -> None:
        adapter = GoogleConsoleAdapter(binary="unused")
        self.assertEqual(
            adapter.required_authority(
                Step("google-console", "screenshot", "google-console:george")
            ),
            Authority.COLLECT,
        )


if __name__ == "__main__":
    unittest.main()
