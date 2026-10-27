"""Focused smoke: changing pages, process restart, lost reply, real outcome checks."""
import copy
import tempfile
import unittest
from pathlib import Path

from agent_bridge_task.browser_tasks import BrowserTasks
from agent_bridge_task.store import Store


class Browser:
    def __init__(self):
        self.page = {"revision": "initial", "stable": True, "url": "https://hotel.example/search",
                     "title": "Hotel", "text": "Choose dates", "controls": []}
        self.bookings = 0
        self.lose_reply = False

    def observe(self, screenshot=False): return copy.deepcopy(self.page)

    def act(self, action, revision):
        if revision != self.page["revision"]:
            return {"ok": False, "dispatched": False, "observation": self.observe()}
        if action["kind"] == "fill":
            self.page.update(revision="dates", text="Denver October 1–3, 2 adults")
        if action["kind"] == "click":
            self.bookings += 1
            self.page.update(revision="receipt", url="https://hotel.example/reservations/AB1234",
                             text="Confirmed AB1234 Denver October 1–3, 2 adults")
            if self.lose_reply: raise ConnectionError("reply lost after booking")
        if action["kind"] == "navigate": self.page["url"] = action["url"]
        return {"ok": True, "dispatched": True, "observation": self.observe()}


class BrowserTaskSmoke(unittest.TestCase):
    def test_restart_and_uncertain_booking_do_not_repeat_and_require_persistent_proof(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Path(folder) / "state.db"
            browser = Browser()
            store = Store(db)
            tasks = BrowserTasks(store, lambda config: browser)
            task = tasks.start("Book Denver for October 1–3 for 2 adults", "https://hotel.example/search",
                               [{"contains": {"text": "Denver"}}, {"contains": {"text": "October 1–3"}},
                                {"contains": {"text": "2 adults"}}, {"contains": {"text": "Confirmed"}}], transactional=True)
            task_id = task["task_id"]
            view = tasks.observe(task_id)
            tasks.act(task_id, "dates", view["observation_id"], {"kind": "fill", "control_id": "dates", "value": "October 1–3"})
            store.close()
            # A different controller instance reads saved goal and progress.
            store = Store(db)
            try:
                tasks = BrowserTasks(store, lambda config: browser)
                recovered = tasks.recover(task_id)
                self.assertEqual(recovered["steps"], 1)
                self.assertEqual(recovered["goal"], "Book Denver for October 1–3 for 2 adults")
                incomplete = tasks.complete(task_id, "https://hotel.example/reservations/AB1234", "October")
                self.assertEqual(incomplete["status"], "incomplete")
                view = tasks.observe(task_id)
                browser.lose_reply = True
                action = {"kind": "click", "control_id": "reserve"}
                result = tasks.act(task_id, "reserve-once", view["observation_id"], action)
                self.assertEqual(result["status"], "uncertain")
                tasks.act(task_id, "reserve-once", view["observation_id"], action)
                self.assertEqual(browser.bookings, 1)
                with self.assertRaises(ValueError): tasks.complete(task_id)
                tasks.recover(task_id, "https://hotel.example/reservations/AB1234")
                tasks.resolve(task_id, "reserve-once", "applied", [{"contains": {"text": "Confirmed AB1234"}}])
                complete = tasks.complete(task_id, "https://hotel.example/reservations/AB1234", "AB1234")
                self.assertEqual(complete["status"], "completed")
                self.assertTrue(complete["result"]["read_back"])
                self.assertEqual(browser.bookings, 1)
            finally: store.close()


if __name__ == "__main__": unittest.main()
