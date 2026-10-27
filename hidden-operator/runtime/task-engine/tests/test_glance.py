"""The fast look: old button still there, press it. Gone, stop."""
import copy
import tempfile
import unittest
from pathlib import Path

from agent_bridge_task.browser_tasks import BrowserTasks
from agent_bridge_task.glance import critic_packet, follow_step, name_break, press_or_stop, revise_step, run_plan
from agent_bridge_task.store import Store


PAGE = [
    {"id": "insurance", "text": "Trip insurance"},
    {"id": "reserve", "text": "Reserve"},
]


class GlanceTests(unittest.TestCase):
    def test_extra_option_does_not_steal_the_old_button(self):
        decision = press_or_stop("Reserve", PAGE)
        self.assertEqual(decision["action"], "press")
        self.assertEqual(decision["control"]["id"], "reserve")
        self.assertEqual(decision["extra"], 1)

    def test_missing_button_stops_and_keeps_the_page(self):
        decision = press_or_stop("Reserve", [{"id": "insurance", "text": "Trip insurance"}])
        self.assertEqual(decision["action"], "stop")
        self.assertEqual(decision["reason"], "the old button is gone")
        self.assertEqual(decision["page"][0]["id"], "insurance")

    def test_two_buttons_with_the_same_name_stop(self):
        doubled = [{"id": "a", "text": "Reserve"}, {"id": "b", "text": "Reserve"}]
        decision = press_or_stop("Reserve", doubled)
        self.assertEqual(decision["reason"], "the old button appears more than once")

    def test_backup_name_is_used_only_after_the_learned_name_is_gone(self):
        page = [{"id": "go", "text": "Continue"}]
        decision = press_or_stop("Reserve", page, backups=["Continue"])
        self.assertEqual(decision["control"]["id"], "go")
        self.assertEqual(decision["matched"], "Continue")

    def test_critic_packet_keeps_the_saved_plan_out(self):
        packet = critic_packet("book a table", [{"text": "Reserve"}], [{"step": 1, "status": "missed"}])
        self.assertEqual(set(packet), {"instruction", "observations", "actions"})

    def test_break_names_the_first_miss(self):
        found = name_break([
            {"step": 0, "status": "pressed"},
            {"step": 1, "status": "missed", "cause": "Reserve is gone"},
        ])
        self.assertEqual(found, {"step": 1, "cause": "Reserve is gone"})

    def test_revise_changes_one_step(self):
        spec = {"plan": {"steps": [
            {"args": {"selector": {"text": "Date"}}},
            {"args": {"selector": {"text": "Reserve"}}},
        ]}}
        fresh = revise_step(spec, 1, "Continue")
        self.assertEqual(fresh["plan"]["steps"][1]["args"]["selector"]["text"], "Continue")
        self.assertEqual(fresh["plan"]["steps"][0]["args"]["selector"]["text"], "Date")
        self.assertEqual(spec["plan"]["steps"][1]["args"]["selector"]["text"], "Reserve")


class RepairTests(unittest.TestCase):
    def test_saved_button_does_not_wake_the_model(self):
        def model(packet):
            raise AssertionError(packet)
        decision = follow_step("book a table", {"text": "Reserve"}, PAGE, model=model)
        self.assertEqual(decision["via"], "saved")
        self.assertEqual(decision["control"]["id"], "reserve")

    def test_miss_hides_the_old_plan_and_presses_the_model_line(self):
        seen = []

        def model(packet):
            seen.append(packet)
            return "Continue"

        page = [{"id": "go", "text": "Continue"}, {"id": "extra", "text": "Seating"}]
        decision = follow_step("book a table", {"text": "Confirm"}, page, model=model, step_index=1)
        self.assertEqual(decision["control"]["id"], "go")
        self.assertEqual(decision["via"], "model")
        self.assertNotIn("Confirm", str(seen[0]))
        self.assertNotIn("plan", seen[0])
        self.assertEqual(seen[0]["actions"][0]["step"], 1)

    def test_a_name_off_the_page_is_not_clicked(self):
        decision = follow_step("book a table", {"text": "Confirm"}, PAGE, model=lambda packet: "Nope")
        self.assertEqual(decision["action"], "stop")
        self.assertEqual(decision["rejected"], "Nope")

    def test_a_button_that_already_failed_is_not_pressed_again(self):
        page = [{"id": "go", "text": "Continue"}]
        decision = follow_step(
            "book a table",
            {"text": "Confirm"},
            page,
            model=lambda packet: "Continue",
            failures=[{"page": "continue", "button": "Continue"}],
        )
        self.assertEqual(decision["reason"], "that button already failed on this page")

    def test_a_page_with_no_names_needs_a_picture(self):
        calls = []
        page = [{"id": "x", "text": ""}]
        decision = follow_step("book a table", {"text": "Confirm"}, page, model=lambda packet: calls.append(packet) or "x")
        self.assertEqual(decision["reason"], "need a picture")
        self.assertEqual(calls, [])
        with_picture = follow_step("book a table", {"text": "Confirm"}, page, model=lambda packet: "Go", picture="pic")
        self.assertEqual(with_picture["action"], "stop")

    def test_two_different_pages_admit_one_step_and_leave_the_others(self):
        steps = [{"text": "Date", "check": "Date set"}, {"text": "Confirm", "check": "Held"}]
        pages_one = [
            {"controls": [{"id": "date", "text": "Date"}], "after": "Date set"},
            {"controls": [{"id": "go", "text": "Continue"}, {"id": "a", "text": "Seating"}], "after": "Held for 7"},
        ]
        pages_two = [
            {"controls": [{"id": "date", "text": "Date"}], "after": "Date set"},
            {"controls": [{"id": "go", "text": "Continue"}, {"id": "b", "text": "Insurance"}], "after": "Held for 8"},
        ]
        model = lambda packet: "Continue"
        first = run_plan("book a table", steps, pages_one, model=model)
        self.assertEqual(first["presses"], ["date", "go"])
        self.assertEqual(first["asked"], 1)
        self.assertEqual(first["steps"][1]["text"], "Confirm")
        second = run_plan("book a table", steps, pages_two, model=model, book=first["book"])
        self.assertEqual(second["steps"][0]["text"], "Date")
        self.assertEqual(second["steps"][1]["text"], "Continue")
        self.assertEqual(second["asked"], 1)

    def test_a_press_in_the_wrong_room_does_not_count(self):
        steps = [{"text": "Next", "check": "Tuesday"}, {"text": "Pay"}]
        pages = [{"controls": [{"id": "n", "text": "Next"}], "after": "Wednesday"}]
        result = run_plan("book a table", steps, pages)
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(result["reason"], "the job did not happen")
        self.assertEqual(result["presses"], ["n"])
        self.assertEqual(len(result["actions"]), 1)

    def test_two_presses_without_a_result_do_not_save_the_new_step(self):
        steps = [{"text": "Confirm"}]
        one = [{"controls": [{"id": "go", "text": "Continue"}, {"id": "a", "text": "Seating"}]}]
        two = [{"controls": [{"id": "go", "text": "Continue"}, {"id": "b", "text": "Insurance"}]}]
        model = lambda packet: "Continue"
        first = run_plan("book a table", steps, one, model=model)
        second = run_plan("book a table", steps, two, model=model, book=first["book"])
        self.assertEqual(second["steps"][0]["text"], "Confirm")

    def test_the_same_page_twice_does_not_admit(self):
        steps = [{"text": "Confirm"}]
        page = [[{"id": "go", "text": "Continue"}]]
        model = lambda packet: "Continue"
        first = run_plan("book a table", steps, page, model=model)
        second = run_plan("book a table", steps, page, model=model, book=first["book"])
        self.assertEqual(second["steps"][0]["text"], "Confirm")


class Page:
    def __init__(self, controls):
        self.controls = controls
        self.calls = []

    def observe(self, screenshot=False):
        return {
            "revision": "one",
            "stable": True,
            "url": "https://book.example/table",
            "title": "Book",
            "text": " ".join(item["text"] for item in self.controls),
            "controls": copy.deepcopy(self.controls),
        }

    def act(self, action, revision):
        self.calls.append(action)
        return {"ok": True, "dispatched": True, "observation": self.observe()}


class SavedClickTests(unittest.TestCase):
    def run_click(self, controls, action, model=None):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder) / "state.db")
            page = Page(controls)
            tasks = BrowserTasks(store, lambda config: page, model=model)
            try:
                task_id = tasks.start(
                    "Book a table",
                    "https://book.example/table",
                    [{"contains": {"text": "Booked"}}],
                )["task_id"]
                view = tasks.observe(task_id)
                result = tasks.act(task_id, "click-1", view["observation_id"], action)
                return result, page.calls, tasks.status(task_id)["steps"]
            finally:
                store.close()

    def test_live_run_presses_the_old_button_when_an_extra_option_appears(self):
        result, calls, steps = self.run_click(PAGE, {"kind": "click", "saved": "Reserve", "control_id": "insurance"})
        self.assertEqual(calls[0]["control_id"], "reserve")
        self.assertEqual(steps, 1)
        self.assertNotEqual(result["status"], "stopped")

    def test_live_run_presses_the_model_line_when_the_old_button_is_gone(self):
        result, calls, steps = self.run_click(
            [{"id": "go", "text": "Continue"}],
            {"kind": "click", "saved": "Reserve"},
            model=lambda packet: "Continue",
        )
        self.assertEqual(calls[0]["control_id"], "go")
        self.assertEqual(steps, 1)
        self.assertNotIn("Reserve", str(result.get("packet", "")))

    def test_live_run_does_not_click_when_the_old_button_is_gone(self):
        result, calls, steps = self.run_click(
            [{"id": "insurance", "text": "Trip insurance"}],
            {"kind": "click", "saved": "Reserve"},
        )
        self.assertEqual(result["status"], "stopped")
        self.assertEqual(calls, [])
        self.assertEqual(steps, 0)


if __name__ == "__main__":
    unittest.main()
