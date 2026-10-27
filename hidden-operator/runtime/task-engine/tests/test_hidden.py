from __future__ import annotations

import copy
import unittest

from agent_bridge_task.models import Step

try:
    from agent_bridge_task.hidden import HiddenAdapter
except ImportError:
    HiddenAdapter = None


def screen(revision=1, text="Search"):
    return {"display_id": 7, "generation": "reader-7", "revision": revision,
            "observed_at_ms": 10000, "valid": True,
            "nodes": [{"token": "0", "package": "com.example", "text": text,
                       "description": "", "resource_id": "com.example:id/search",
                       "enabled": True, "visible": True, "clickable": True,
                       "editable": True, "bounds": [10, 20, 90, 80]}]}


class Device:
    def __init__(self):
        self.current = screen()
        self.now = 10000
        self.dispatched = []
        self.reject = False

    def observe(self, name):
        return {"now_ms": self.now, "snapshot": copy.deepcopy(self.current)}

    def action(self, name, request):
        if self.reject:
            return {"ok": False, "dispatched": False, "error": "snapshot changed"}
        self.dispatched.append(request)
        self.current = screen(2, request.get("text", "Results"))
        self.current["observed_at_ms"] += 1
        self.now += 1
        return {"ok": True, "dispatched": True}


class HiddenTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(HiddenAdapter, "fresh hidden-display adapter is missing")
        self.device = Device()
        self.adapter = HiddenAdapter(device=self.device)

    def tap(self, **overrides):
        args = {"package": "com.example", "selector": {"text": "Search"}, "wait_ms": 0}
        args.update(overrides)
        return Step("hidden", "click", "hidden:main", args,
                    {"contains": {"screen.text": "Results"}})

    def test_only_a_current_unique_enabled_node_can_be_clicked(self):
        result = self.adapter.execute(self.tap())
        self.assertTrue(result.verified)
        self.assertEqual(result.data["screen"]["display_id"], 7)
        self.assertEqual(self.device.dispatched[0]["token"], "0")
        self.assertEqual(self.device.dispatched[0]["generation"], "reader-7")

    def test_stale_or_invalid_screen_never_dispatches(self):
        for change in ({"observed_at_ms": 1}, {"valid": False}):
            self.device.current = {**screen(), **change}
            result = self.adapter.execute(self.tap())
            self.assertFalse(result.ok)
        self.assertEqual(self.device.dispatched, [])

    def test_disabled_and_ambiguous_nodes_do_not_fall_back_to_coordinates(self):
        self.device.current["nodes"][0]["enabled"] = False
        self.assertFalse(self.adapter.execute(self.tap()).ok)
        self.device.current = screen()
        self.device.current["nodes"].append({**self.device.current["nodes"][0], "token": "1"})
        self.assertFalse(self.adapter.execute(self.tap()).ok)
        self.assertEqual(self.device.dispatched, [])

    def test_cross_package_match_is_not_a_valid_target(self):
        self.assertFalse(self.adapter.execute(self.tap(package="com.other")).ok)
        self.assertEqual(self.device.dispatched, [])

    def test_rejected_action_is_not_retried(self):
        self.device.reject = True
        result = self.adapter.execute(self.tap())
        self.assertFalse(result.ok)
        self.assertFalse(result.data["dispatched"])
        self.assertEqual(self.device.dispatched, [])

    def test_changed_display_cannot_prove_an_action(self):
        original = self.device.action
        def moved(name, request):
            result = original(name, request)
            self.device.current["display_id"] = 9
            return result
        self.device.action = moved
        result = self.adapter.execute(self.tap())
        self.assertFalse(result.verified)
        self.assertEqual(len(self.device.dispatched), 1)

    def test_unicode_text_is_passed_as_data_and_read_back(self):
        text = "George's café — Բարև\nsecond line $(literal)"
        step = Step("hidden", "set_text", "hidden:main",
                    {"package": "com.example", "selector": {"text": "Search"}, "text": text, "wait_ms": 0},
                    {"equals": {"screen.nodes.0.text": text}})
        result = self.adapter.execute(step)
        self.assertTrue(result.verified)
        self.assertEqual(self.device.dispatched[0]["text"], text)

    def test_mutation_requires_a_screen_postcondition_before_dispatch(self):
        for expect in ({}, {"equals": {"dispatched": True}}):
            step = self.tap()
            step = Step(step.adapter, step.verb, step.target, step.args, expect)
            self.assertFalse(self.adapter.execute(step).ok)
        self.assertEqual(self.device.dispatched, [])

    def test_invalid_display_name_is_rejected(self):
        with self.assertRaises(ValueError):
            self.adapter.bind(Step("hidden", "observe", "hidden:../main"))


if __name__ == "__main__":
    unittest.main()
