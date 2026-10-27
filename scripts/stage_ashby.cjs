// stage_ashby.cjs — fill one Ashby application (jobs.ashbyhq.com) to the Submit button with human hands. NEVER submits.
// Built 2026-10-26 from Agent Bridge's ashby_application.py (selectors, field kinds, "needs-input"), plain CDP, no Python.
//
//   CDP_PORT=19222 node scripts/stage_ashby.cjs <job-url> [--overrides file.json] [--resume file.pdf]
//
// <job-url>: https://jobs.ashbyhq.com/<org>/<posting-id> or .../application. Opens a new tab in the laptop Chrome,
// skims the page, opens the Application tab, fills every field the answer book covers, uploads the resume, wheels the
// "Submit Application" button into view and stops. Output: logs/stage/ashby-<stamp>.json + .png, 6-line receipt.
// --overrides: { "<posting-id>": { "skip": "why" } | { "rules": [["regex", "answer"], ...] } }, written by the picker.
// Ashby saves each answer to its server as a draft while you fill (ApiSetFormValue); that is not a submission.

const { stage, openTab, press, BOOK, human } = require('./stage_lib.cjs');

const FORM = '.ashby-application-form-container';
const READY = `!!document.querySelector('${FORM} .ashby-application-form-question-title') && !document.body.innerText.includes('Fetching application form')`;

// The page, read in one gulp (runs inside the page). One entry per question box, kinds in the adapter's order.
function readAshby() {
  const t = e => (e ? (e.innerText || e.textContent || '') : '').replace(/\s+/g, ' ').trim();
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  document.querySelectorAll('[data-stage]').forEach(e => e.removeAttribute('data-stage'));
  let n = 0; const mark = e => { const k = 's' + (n++); e.setAttribute('data-stage', k); return `[data-stage="${k}"]`; };
  const lab = c => (c.labels && c.labels[0]) ? t(c.labels[0]) : '';
  const fields = [], seen = new Set();
  const boxes = [...document.querySelectorAll('.ashby-application-form-field-entry, fieldset')].filter(b => b.querySelector('.ashby-application-form-question-title') && vis(b));
  for (const b of boxes) {
    const q = b.querySelector('.ashby-application-form-question-title');
    const label = t(q).replace(/\s*\*$/, '');
    const owner = b.closest('[data-field-path]') || b.querySelector('[data-field-path]');
    const key = (owner && owner.getAttribute('data-field-path')) || label;
    if (!label || seen.has(key)) continue; seen.add(key);
    const required = /required/i.test(q.className) || !!b.querySelector('input[required],textarea[required],select[required],[aria-required=true]');
    const file = b.querySelector('input[type=file]'), radios = [...b.querySelectorAll('input[type=radio]')], checks = [...b.querySelectorAll('input[type=checkbox]')];
    const btns = [...b.querySelectorAll('button')].filter(vis), ta = b.querySelector('textarea'), sel = b.querySelector('select');
    const inp = b.querySelector('input:not([type=hidden]):not([type=radio]):not([type=checkbox]):not([type=file])');
    const f = { key, label, required };
    if (file) {
      const shown = (t(b).match(/[\w .()-]+\.(pdf|docx?|odt|rtf|txt)\b/i) || [''])[0].trim();
      Object.assign(f, { type: 'file', sel: mark(file), filled: !!(file.files && file.files.length) || !!shown, value: (file.files && file.files[0] && file.files[0].name) || shown });
    } else if (radios.length) {
      const on = radios.find(r => r.checked);
      Object.assign(f, { type: 'radio', options: radios.map(r => lab(r) || t(r.parentElement)), optsel: radios.map(r => mark((r.labels && r.labels[0]) || r)), filled: !!on, value: on ? lab(on) : '' });
    } else if (checks.length && btns.length && ['yes', 'no'].every(w => btns.some(x => t(x).toLowerCase() === w))) {
      const yn = btns.filter(x => /^(yes|no)$/i.test(t(x)));
      const on = yn.find(x => x.getAttribute('aria-pressed') === 'true' || /_active_|selected/i.test(x.className));
      Object.assign(f, { type: 'yesno', options: yn.map(t), optsel: yn.map(mark), filled: !!on, value: on ? t(on) : '' });
    } else if (ta) {
      Object.assign(f, { type: 'textarea', sel: mark(ta), filled: !!ta.value.trim(), value: ta.value });
    } else if (sel) {
      const o = sel.options[sel.selectedIndex];
      Object.assign(f, { type: 'select', sel: mark(sel), options: [...sel.options].map(x => t(x)), filled: !!sel.value, value: sel.value && o ? t(o) : '' });
    } else if (inp) {
      const kind = /react-datepicker/i.test(inp.className) || /pick date/i.test(inp.placeholder || '') ? 'date'
        : (key === '_systemfield_location' || inp.getAttribute('role') === 'combobox') ? 'combobox' : (inp.type || 'text');
      Object.assign(f, { type: kind, sel: mark(inp), filled: !!inp.value.trim(), value: inp.value });
    } else if (checks.length) {
      const on = checks.map((c, i) => c.checked ? i : -1).filter(i => i > -1);
      Object.assign(f, checks.length === 1
        ? { type: 'checkbox', options: [lab(checks[0]) || label], optsel: [mark((checks[0].labels && checks[0].labels[0]) || checks[0])], checked: checks[0].checked, filled: checks[0].checked, value: checks[0].checked ? 'checked' : '' }
        : { type: 'checkboxes', options: checks.map(lab), optsel: checks.map(c => mark((c.labels && c.labels[0]) || c)), checkedIdx: on, filled: on.length > 0, value: on.map(i => lab(checks[i])) });
    } else continue;
    fields.push(f);
  }
  const submit = [...document.querySelectorAll('button')].find(x => /^submit application$/i.test(t(x)) && vis(x));
  return { title: document.title, fields, submitSel: submit ? mark(submit) : '', submitText: submit ? t(submit) : '', valid: undefined };
}

// Ashby's own system fields, straight from the book's facts.
const F = BOOK.facts;
const facts = f => {
  if (f.key === '_systemfield_name') return /legal/i.test(f.label) ? { value: F.full_legal_name, source: 'fact:full_legal_name' } : { value: `${F.first_name} ${F.last_name}`, source: 'fact:first_name+last_name' };
  if (f.key === '_systemfield_email') return { value: F.email, source: 'fact:email' };
  if (f.key === '_systemfield_phone') return { value: F.phone, source: 'fact:phone' };
  if (f.key === '_systemfield_location') return { value: F.location, query: F.city, source: 'fact:location' };
  return null;
};

stage({
  site: 'ashby',
  jobId: url => (url.match(/jobs\.ashbyhq\.com\/[^/]+\/([0-9a-f-]{36})/i) || [])[1] || url,
  facts,
  READ: `(${readAshby.toString()})()`,
  formReady: READY,
  readPasses: 3,
  open: async url => {
    const h = await openTab(url.replace(/\/application\/?$/, ''), `document.readyState === 'complete' && !!document.querySelector('${FORM}, a[href$="/application"], [role=tab]')`);
    if (!(await h.evaluate(READY))) { // the posting opens on Overview; the form is behind the Application tab
      const found = await h.evaluate(`(()=>{const e=[...document.querySelectorAll('a, button, [role=tab]')].find(x=>/^(application|apply for this job)$/i.test((x.innerText||'').trim())&&x.getBoundingClientRect().height>0);if(!e)return false;e.setAttribute('data-stage-open','1');return true})()`);
      if (found) { await h.pause(2000, 5000); await press(h, '[data-stage-open="1"]'); } // a beat to read the overview first
      else await h.send('Page.navigate', { url: url.replace(/\/?$/, '/application').replace(/\/application\/application$/, '/application') });
      const t0 = Date.now(); while (Date.now() - t0 < 20000 && !(await h.evaluate(READY))) await human.sleep(400);
    }
    return h;
  },
}).catch(e => { console.log('ERROR', e && e.message); process.exit(1); });
