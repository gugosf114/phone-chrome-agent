"""One focused smoke for early hints, persistence and changed approaches."""
import copy
from datetime import datetime, timezone
from email.utils import format_datetime
import json
import tempfile
import unittest
from pathlib import Path

from agent_bridge_task.browser_tasks import BrowserTasks
from agent_bridge_task.site_judgment import SiteJudgment, retry_deadline
from agent_bridge_task.store import Store


class Page:
    def __init__(self):
        self.calls = 0
        self.page = {'revision': 'one', 'stable': True, 'url': 'https://hotel.example/search', 'title': 'Search',
                     'text': 'Choose a date', 'controls': [
                         {'id': 'calendar', 'tag': 'button', 'text': 'Calendar', 'label': '', 'type': 'button'},
                         {'id': 'date', 'tag': 'input', 'type': 'text', 'label': 'Date', 'value': ''}],
                     'site_signals': {'alerts': [], 'challenge': False, 'invalid_fields': []}, 'network': []}

    def observe(self, screenshot=False): return copy.deepcopy(self.page)

    def act(self, action, revision):
        self.calls += 1
        if action['kind'] == 'fill':
            self.page['controls'][1]['value'] = action['value']
            self.page['revision'] = 'date-entered'
        return {'ok': True, 'dispatched': True, 'observation': self.observe()}


class SiteJudgmentSmoke(unittest.TestCase):
    def test_early_warning_survives_restart_and_recovery_and_strategies_have_to_change(self):
        now = [1700000000.0]
        date = format_datetime(datetime.fromtimestamp(now[0] + 600, timezone.utc), usegmt=True)
        self.assertEqual(retry_deadline('30', now[0]), now[0] + 30)
        self.assertEqual(retry_deadline(date, now[0]), now[0] + 600)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'state.db'
            page = Page()
            store = Store(path)
            tasks = BrowserTasks(store, lambda config: page)
            tasks.judgment = SiteJudgment(store, lambda: now[0])
            task_id = tasks.start('Find a room', page.page['url'], [{'contains': {'text': 'Results'}}])['task_id']
            # A successful HTTP response can warn us BEFORE rate-limit rejection.
            page.page['network'] = [{'id': 'early-1', 'at': now[0], 'site': 'hotel.example', 'relevant': True,
                                     'status': 200, 'top_level': False,
                                     'headers': {'x-ratelimit-remaining': '1', 'x-ratelimit-reset': str(int(now[0] + 120))}}]
            view = tasks.observe(task_id)
            self.assertTrue(view['paused'])
            self.assertEqual(view['site_advice']['retry_after_seconds'], 120)
            blocked = tasks.act(task_id, 'not-sent', view['observation_id'], {'kind': 'click', 'control_id': 'calendar'})
            self.assertTrue(blocked['paused'])
            self.assertEqual(page.calls, 0)
            store.close()
            store = Store(path)
            try:
                tasks = BrowserTasks(store, lambda config: page)
                tasks.judgment = SiteJudgment(store, lambda: now[0])
                recovered = tasks.recover(task_id, page.page['url'])
                self.assertTrue(recovered['paused'])
                self.assertEqual(page.calls, 0)
                with self.assertRaisesRegex(ValueError, 'cooldown'):
                    tasks.release_site(task_id, [{'contains': {'text': 'Choose a date'}}])
                tasks.cancel(task_id)
                task_id = tasks.start('Another task on the same site', page.page['url'], [{'contains': {'text': 'Results'}}])['task_id']
                self.assertTrue(tasks.observe(task_id)['paused'])
                now[0] += 121
                # Re-reading the same response does not keep renewing the timer.
                self.assertEqual(tasks.observe(task_id)['site_advice']['decision'], 'continue')
                page.page['network'] = [{'id': 'ad-403', 'at': now[0], 'site': 'ads.example', 'relevant': False,
                                         'status': 403, 'headers': {}}]
                for number in range(2):
                    view = tasks.observe(task_id)
                    result = tasks.act(task_id, f'calendar-{number}', view['observation_id'],
                                       {'kind': 'click', 'control_id': 'calendar'}, strategy='calendar')
                    self.assertEqual(result['diagnosis']['category'], 'no_progress')
                calls = page.calls
                view = tasks.recover(task_id)
                refused = tasks.act(task_id, 'renamed', view['observation_id'],
                                    {'kind': 'click', 'control_id': 'calendar'}, strategy='clever new label')
                self.assertEqual(refused['status'], 'needs_new_strategy')
                self.assertEqual(page.calls, calls)
                self.assertIn('date', json.dumps(refused['diagnosis']['alternatives']).lower())
                result = tasks.act(task_id, 'direct-entry', view['observation_id'],
                                   {'kind': 'fill', 'control_id': 'date', 'value': '2026-10-01'}, strategy='type into the observed date field')
                self.assertEqual(result['diagnosis']['category'], 'progress')
                # Visible account trouble pauses before another credential attempt.
                page.page['site_signals']['alerts'] = ['Incorrect password. 1 attempt remaining.']
                self.assertTrue(tasks.observe(task_id)['paused'])
                self.assertEqual(tasks.judgment.assess('https://unrelated.example')['decision'], 'continue')
            finally: store.close()


if __name__ == '__main__': unittest.main()
