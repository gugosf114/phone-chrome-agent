"""Observed site warnings and failed approaches. No hidden-risk-score claims."""
from __future__ import annotations

from datetime import timezone
from email.utils import parsedate_to_datetime
import json
import math
import re
import time
from urllib.parse import urlparse

from .adapters import verify_expectation
from .engine import redact
from .skill_schema import canonical, digest

SCHEMA = """
CREATE TABLE IF NOT EXISTS browser_site_policy (
 site TEXT PRIMARY KEY, until REAL NOT NULL DEFAULT 0, hold TEXT NOT NULL DEFAULT '',
 reason TEXT NOT NULL DEFAULT '', caution_until REAL NOT NULL DEFAULT 0,
 last_ui TEXT NOT NULL DEFAULT '[]', updated REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS browser_site_signals (
 id TEXT PRIMARY KEY, site TEXT NOT NULL, kind TEXT NOT NULL, observed REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS browser_strategy_attempts (
 request_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, site TEXT NOT NULL,
 fingerprint TEXT NOT NULL, strategy TEXT NOT NULL, outcome TEXT NOT NULL,
 diagnosis_json TEXT NOT NULL, observed REAL NOT NULL
);
"""


def site_key(url):
    host = (urlparse(url).hostname or '').lower().rstrip('.')
    return host[4:] if host.startswith('www.') else host


def retry_deadline(value, now):
    """Retry-After can be delay seconds or an HTTP date; never shorten a valid wait."""
    if value is None: return None
    text = str(value).strip()
    try:
        if text.isdigit():
            seconds = int(text)
            return now + seconds
        date = parsedate_to_datetime(text)
        if date.tzinfo is None: date = date.replace(tzinfo=timezone.utc)
        return max(now, date.timestamp())
    except (ValueError, TypeError, OverflowError): return None


def ui_signals(page):
    ui = page.get('site_signals') or {}
    alerts = ui.get('alerts') or []
    # Long articles mentioning "captcha" or "banned" are not account warnings.
    text = ' '.join(str(x) for x in alerts)
    if not text and len(page.get('text', '')) < 900:
        text = page.get('text', '')
    text = (page.get('title', '') + ' ' + text).lower()
    found = []
    if ui.get('challenge'):
        found.append(('challenge', 'A live human-verification challenge is visible.'))
    if re.search(r'(your account.{0,35}(suspended|locked|restricted)|account has been (locked|suspended)|unusual (traffic|activity)|suspicious (activity|sign.in)|[12] (attempts?|tries) (left|remaining))', text):
        found.append(('account_warning', 'The page reports an account/activity warning.'))
    if re.search(r'(incorrect password|invalid (password|credentials)|sign.in failed|login failed|password is incorrect)', text):
        found.append(('authentication_failure', 'The site rejected authentication; do not keep guessing credentials.'))
    if re.search(r'(too many requests|too many attempts|rate limit.{0,25}(exceeded|reached))', text):
        found.append(('rate_limit', 'The page says requests or attempts are limited.'))
    return found


class SiteJudgment:
    def __init__(self, store, clock=time.time):
        self.store, self.clock = store, clock
        store.db.executescript(SCHEMA)

    def _row(self, site):
        with self.store.db:
            self.store.db.execute('INSERT OR IGNORE INTO browser_site_policy(site) VALUES (?)', (site,))
        return dict(self.store.db.execute('SELECT * FROM browser_site_policy WHERE site=?', (site,)).fetchone())

    def assess(self, url):
        site, now = site_key(url), self.clock()
        row = self._row(site)
        seconds = max(0, math.ceil(row['until'] - now))
        decision = 'pause' if seconds or row['hold'] else 'caution' if row['caution_until'] > now else 'continue'
        return {'site': site, 'decision': decision,
                'retry_after_seconds': seconds, 'hold': row['hold'], 'reason': row['reason'] if decision != 'continue' else '',
                'last_warning': row['reason'], 'last_warning_at': row['updated'],
                'basis': 'observed signals and conservative heuristics; not the site\'s private bot score'}

    def ingest(self, page):
        site, now = site_key(page.get('url', '')), self.clock()
        row = self._row(site)
        active_ui = ui_signals(page)
        active_kinds = {kind for kind, _ in active_ui}
        old_ui = set(json.loads(row['last_ui']))
        pending_events = []
        pending_ids = set()
        for event in page.get('network', []):
            if not event.get('relevant') or not event.get('id'): continue
            if event.get('site', site) != site: continue
            # A delayed/replayed observation must not repeatedly extend the wait.
            stamp = float(event.get('at', now))
            if stamp < now - 600 or stamp > now + 60: continue
            headers = event.get('headers') or {}
            status = int(event.get('status', 0))
            kind = ''
            remaining = headers.get('x-ratelimit-remaining', headers.get('ratelimit-remaining'))
            remaining = int(remaining) if str(remaining).isdigit() else None
            if str(headers.get('cf-mitigated', '')).lower() == 'challenge': kind = 'challenge'
            elif status == 429: kind = 'rate_limit'
            elif remaining is not None and remaining <= 2: kind = 'near_limit'
            elif status == 401: kind = 'authentication_failure' if event.get('auth_request') else 'authentication_required'
            elif status == 403: kind = 'access_denied'
            elif status in {500, 502, 503, 504}: kind = 'service_error'
            elif event.get('top_level') and 200 <= status < 300: kind = 'healthy_document'
            if not kind: continue
            if event['id'] in pending_ids or self.store.db.execute('SELECT 1 FROM browser_site_signals WHERE id=?', (event['id'],)).fetchone(): continue
            pending_ids.add(event['id'])
            pending_events.append((event['id'], site, kind, stamp))
            count = self.store.db.execute('SELECT COUNT(*) FROM browser_site_signals WHERE site=? AND kind=? AND observed>?', (site, kind, now - 600)).fetchone()[0] + sum(e[2] == kind for e in pending_events)
            if kind in {'rate_limit', 'near_limit'} or (kind == 'service_error' and (status == 503 or count >= 2)):
                deadline = retry_deadline(headers.get('retry-after'), stamp)
                reset = headers.get('x-ratelimit-reset', headers.get('ratelimit-reset'))
                # Implement common epoch/delta formats explicitly; unknown formats use a conservative default.
                if deadline is None and str(reset).isdigit():
                    number = int(reset)
                    deadline = float(number) if number >= 1000000000 else stamp + number
                if deadline is None or deadline < stamp: deadline = stamp + min(60 * 2 ** min(count - 1, 5), 1800)
                row['until'] = max(row['until'], deadline)
                row['reason'] = f'{kind}: HTTP {status}' + (f', {remaining} requests remaining' if remaining is not None else '')
            elif kind in {'challenge', 'access_denied'}:
                row['hold'], row['reason'] = kind, f'{kind}: observed HTTP {status}; this does not by itself prove a bot ban'
            elif kind == 'authentication_failure':
                row['hold'], row['reason'] = kind, 'Authentication attempt rejected; inspect the account before another credential attempt.'
            elif kind == 'healthy_document' and stamp > row['updated'] and not active_ui and row['hold'] in {'challenge', 'access_denied'}:
                row['hold'] = ''
                row['reason'] = 'A later successful page response cleared the visible access restriction; any server wait still applies.'
            else:
                row['caution_until'] = max(row['caution_until'], now + 300)
                row['reason'] = f'{kind}: investigate before repeating the action'
            if kind != 'healthy_document': row['updated'] = max(row['updated'], stamp)
        for kind, reason in active_ui:
            if kind == 'rate_limit':
                if kind not in old_ui: row['until'] = max(row['until'], now + 60)
            else: row['hold'] = kind
            row['reason'], row['updated'] = reason, now
        if (page.get('site_signals') or {}).get('verification_widget') and not active_ui:
            row['caution_until'] = max(row['caution_until'], now + 300)
            if not row['hold']: row['reason'] = 'A verification widget is present; watch for a challenge, do not repeatedly submit.'
        with self.store.db:
            # A crash cannot mark a warning consumed without also saving its backoff.
            self.store.db.executemany('INSERT OR IGNORE INTO browser_site_signals VALUES (?,?,?,?)', pending_events)
            self.store.db.execute('UPDATE browser_site_policy SET until=MAX(until,?),hold=?,reason=?,caution_until=MAX(caution_until,?),last_ui=?,updated=? WHERE site=?',
                                  (row['until'], row['hold'], row['reason'], row['caution_until'], canonical(sorted(active_kinds)), row['updated'], site))
        return self.assess(page.get('url', ''))

    def release(self, page, evidence_checks):
        """Reconsider a resolved visible restriction, never override a timed server wait."""
        advice = self.ingest(page)
        if advice['retry_after_seconds']: raise ValueError('server cooldown has not expired')
        if ui_signals(page): raise ValueError('the page still shows a restriction')
        if not evidence_checks or not all(verify_expectation(page, check)[0] for check in evidence_checks):
            raise ValueError('fresh positive evidence is required to release a restriction')
        with self.store.db:
            self.store.db.execute("UPDATE browser_site_policy SET hold='',reason='restriction reconsidered against fresh evidence',caution_until=? WHERE site=?", (self.clock() + 60, advice['site']))
        return self.assess(page['url'])

    @staticmethod
    def signature(page, action):
        node = next((n for n in page.get('controls', []) if n.get('id') == action.get('control_id')), {})
        target = {k: node.get(k) for k in ('label', 'text', 'tag', 'type', 'role')}
        fields = [{k: n.get(k) for k in ('label', 'type', 'value', 'checked', 'selected')} for n in page.get('controls', []) if n.get('tag') in {'input', 'textarea', 'select'}]
        return digest({'kind': action.get('kind'), 'target': target,
                       'page': page.get('url'), 'fields': fields,
                       'value': action.get('value'), 'url': action.get('url'), 'key': action.get('key'),
                       'x': action.get('x'), 'y': action.get('y'), 'pixels': action.get('pixels')})

    def before_action(self, task_id, page, action):
        current = self.assess(page['url'])
        if current['decision'] == 'pause': return {'allowed': False, 'paused': True, 'site_advice': current}
        target_url = action.get('url') if action.get('kind') == 'navigate' else page['url']
        advice = self.assess(target_url)
        if advice['decision'] == 'pause': return {'allowed': False, 'paused': True, 'site_advice': advice}
        now = self.clock()
        rows = self.store.db.execute('SELECT * FROM browser_strategy_attempts WHERE site=? AND observed>? ORDER BY observed DESC', (advice['site'], now - 600)).fetchall()
        # Pace is a precaution, not a claim that detection occurred.
        if sum(r['observed'] > now - 20 for r in rows) >= 8:
            return {'allowed': False, 'paused': True, 'site_advice': {**advice, 'decision': 'pause', 'reason': 'rapid action burst; take a short pause before generating more traffic', 'retry_after_seconds': 10}}
        signature = self.signature(page, action)
        failures = []
        for previous in rows:
            if previous['fingerprint'] != signature: continue
            if previous['outcome'] == 'progress': break
            if previous['outcome'] != 'stale_observation': failures.append(previous)
        if len(failures) >= 2:
            return {'allowed': False, 'paused': False, 'diagnosis': {'category': 'repeated_failed_approach',
                    'reason': 'This actual approach already failed twice; changing a request ID or strategy label does not make it new.',
                    'alternatives': self.alternatives(page, action)}}
        return {'allowed': True, 'site_advice': advice}

    @staticmethod
    def alternatives(page, action):
        choices = [{'method': 'inspect_current_state', 'reason': 'Read enabled states, field errors and the current page before choosing a different method.'}]
        for node in page.get('controls', []):
            if node.get('disabled'): continue
            if node.get('tag') in {'input', 'textarea', 'select'} and any(w in (node.get('label', '') + ' ' + node.get('type', '')).lower() for w in ('date', 'search', 'destination', 'month')):
                choices.append({'method': 'use_observed_field_or_options', 'control_id': node['id'], 'label': node.get('label', '')})
            if node.get('tag') == 'a' and any(w in node.get('text', '').lower() for w in ('help', 'support', 'search')):
                choices.append({'method': 'inspect_observed_link', 'control_id': node['id'], 'href': node.get('href', '')})
        if action.get('kind') == 'click': choices.append({'method': 'inspect_visual_layout', 'reason': 'Request a screenshot or inspect an editable field instead of repeating this click.'})
        return choices[:6]

    def record(self, task_id, request_id, before, action, reply, strategy=''):
        after = reply.get('observation') or before
        error = str(reply.get('error', '')).lower()
        invalid = (after.get('site_signals') or {}).get('invalid_fields', [])
        def meaningful(page):
            ui = page.get('site_signals') or {}
            # Compare on the same privacy boundary: log redaction alone is not progress.
            return redact({**{k: page.get(k) for k in ('url', 'text', 'controls')}, 'scroll': ui.get('scroll'), 'focused': ui.get('focused')})
        changed = digest(meaningful(before)) != digest(meaningful(after))
        if not reply.get('ok') and reply.get('dispatched') is not False: category = 'uncertain_effect'
        elif 'page changed' in error: category = 'stale_observation'
        elif 'disabled' in error or 'missing' in error or 'uniquely' in error: category = 'unavailable_control'
        elif reply.get('ok'): category = 'progress'
        else: category = 'action_error'
        if category == 'progress' and not changed:
            category = 'form_validation' if invalid and action.get('kind') in {'click', 'press'} else 'no_progress'
        diagnosis = {'category': category, 'error': reply.get('error'), 'invalid_fields': invalid,
                     'alternatives': [] if category in {'progress', 'uncertain_effect'} else self.alternatives(after, action)}
        if category == 'uncertain_effect': diagnosis['next'] = 'Inspect the live result and reconcile before any alternative action.'
        with self.store.db:
            self.store.db.execute('INSERT OR IGNORE INTO browser_strategy_attempts VALUES (?,?,?,?,?,?,?,?)',
                                  (request_id, task_id, site_key(before['url']), self.signature(before, action), strategy,
                                   category, canonical(diagnosis), self.clock()))
        return diagnosis
