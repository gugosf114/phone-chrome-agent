from __future__ import annotations

import unittest

from agent_bridge_task.adapters import PhoneMcpAdapter
from agent_bridge_task.engine import Engine
from agent_bridge_task.models import Authority, Step, TaskPlan


class FakeClient:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def call(self, tool_name, arguments):
        self.calls.append((tool_name, arguments))
        return self.result


class PhoneAdapterTests(unittest.TestCase):
    def test_empty_command_payload_cannot_verify_a_phone_mutation(self) -> None:
        adapter = PhoneMcpAdapter(client=FakeClient({}))
        plan = TaskPlan.from_dict(
            {
                "task": {
                    "goal": "reject command-only proof",
                    "permission": {
                        "authority": "full",
                        "scope": {"kind": "task"},
                        "targets": ["phone:george"],
                    },
                },
                "steps": [
                    {
                        "adapter": "phone",
                        "verb": "android_tap",
                        "target": "phone:george",
                        "args": {"arguments": {"x": 1, "y": 1}},
                        "expect": {"equals": {"payload": {}}},
                    }
                ],
            },
            "phone-fake-proof",
        )
        check = Engine(None, {"phone": adapter}).preflight(plan)
        self.assertFalse(check["allowed"])
        self.assertIn("intrinsic post-action proof", check["checks"][0]["reason"])

    def test_whole_phone_is_one_exclusive_resource(self) -> None:
        adapter = PhoneMcpAdapter(client=FakeClient({}))
        self.assertEqual(
            adapter.exclusive_resources(
                Step("phone", "android_get_screen_state", "phone:george")
            ),
            ("phone:george",),
        )

    def test_phone_actions_have_stable_levels(self) -> None:
        adapter = PhoneMcpAdapter(client=FakeClient({}))
        cases = {
            "android_get_screen_state": Authority.READ,
            "android_download_from_url": Authority.COLLECT,
            "android_tap": Authority.EXTERNAL,
            "android_notification_reply": Authority.EXTERNAL,
            "android_delete_file": Authority.FULL,
        }
        for verb, expected in cases.items():
            with self.subTest(verb=verb):
                self.assertEqual(
                    adapter.required_authority(Step("phone", verb, "phone:george")),
                    expected,
                )

    def test_phone_target_is_the_whole_named_device(self) -> None:
        adapter = PhoneMcpAdapter(client=FakeClient({}))
        bound = adapter.bind(Step("phone", "android_tap", "phone:claimed"))
        self.assertEqual(bound.target, "phone:george")

    def test_phone_effect_can_raise_but_never_lower(self) -> None:
        adapter = PhoneMcpAdapter(client=FakeClient({}))
        read = Step(
            "phone",
            "android_get_screen_state",
            "phone:george",
            args={"effect": "external"},
        )
        tap = Step(
            "phone",
            "android_tap",
            "phone:george",
            args={"effect": "read"},
        )
        self.assertEqual(adapter.required_authority(read), Authority.EXTERNAL)
        self.assertEqual(adapter.required_authority(tap), Authority.EXTERNAL)

    def test_internal_effect_label_is_not_sent_to_the_phone_tool(self) -> None:
        client = FakeClient({"structuredContent": {"changed": True}})
        adapter = PhoneMcpAdapter(client=client)
        step = Step(
            "phone",
            "android_tap",
            "phone:george",
            args={"x": 10, "y": 20, "effect": "external"},
            expect={"equals": {"payload.changed": True}},
        )
        adapter.execute(step)
        self.assertEqual(client.calls[0][1], {"x": 10, "y": 20})

    def test_phone_result_is_verified(self) -> None:
        client = FakeClient(
            {
                "content": [
                    {"type": "text", "text": '{"package":"com.example","ready":true}'}
                ]
            }
        )
        adapter = PhoneMcpAdapter(client=client)
        step = Step(
            "phone",
            "android_get_screen_state",
            "phone:george",
            args={"arguments": {"include_screenshot": False}},
            expect={"equals": {"payload.ready": True}},
        )
        result = adapter.execute(step)
        self.assertTrue(result.ok)
        self.assertTrue(result.verified)
        self.assertEqual(client.calls[0][0], "android_get_screen_state")


if __name__ == "__main__":
    unittest.main()
