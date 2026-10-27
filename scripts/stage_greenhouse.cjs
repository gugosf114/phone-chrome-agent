// stage_greenhouse.cjs — fill one Greenhouse application to the Submit button with human hands. NEVER submits.
// Built 2026-10-26 from Agent Bridge's greenhouse_application.py (field ids, react-select boxes, form validity),
// plain CDP, no Python.
//
//   CDP_PORT=19222 node scripts/stage_greenhouse.cjs <job-url> [--overrides file.json] [--resume file.pdf]
//
// <job-url>: https://job-boards.greenhouse.io/<org>/jobs/<id> (or boards.greenhouse.io). The form sits under the job
// text on the same page. Opens a new tab in the laptop Chrome, reads down the job text, fills every field the answer
// book covers, uploads the resume, wheels "Submit application" into view and stops.
// Output: logs/stage/greenhouse-<stamp>.json + .png, 6-line receipt.
// --overrides: { "<job id>": { "skip": "why" } | { "rules": [["regex", "answer"], ...] } }, written by the picker.

const { stage, openTab, BOOK } = require('./stage_lib.cjs');

const READY = `!!document.getElementById('first_name')`;

// The form, read in one gulp (runs inside the page). Controls with an id; the id-less inputs are react-select's
// hidden "required" twins and the phone flag search, skipped. Radios and checkboxes are grouped by their fieldset.
function readGreenhouse() {
  const t = e => (e ? (e.innerText || e.textContent || '') : '').replace(/\s+/g, ' ').trim();
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  document.querySelectorAll('[data-stage]').forEach(e => e.removeAttribute('data-stage'));
  let n = 0; const mark = e => { const k = 's' + (n++); e.setAttribute('data-stage', k); return `[data-stage="${k}"]`; };
  const form = document.querySelector('form#application-form') || (document.getElementById('first_name') || { closest: () => null }).closest('form');
  if (!form) return { title: document.title, fields: [], submitSel: '', valid: false };
  const labelOf = c => {
    if (c.type === 'file') { const g = c.closest('[role=group][aria-labelledby]'); const gl = g && document.getElementById(g.getAttribute('aria-labelledby')); if (gl) return t(gl); } // "Resume/CV", not its "Attach" button
    let l = c.id ? form.querySelector(`label[for="${CSS.escape(c.id)}"]`) : null;
    if (!l) { const g = c.closest('[role=group][aria-labelledby]'); if (g) l = document.getElementById(g.getAttribute('aria-labelledby')); }
    if (!l && c.getAttribute('aria-labelledby')) l = document.getElementById(c.getAttribute('aria-labelledby').split(' ')[0]);
    if (!l) { const fs = c.closest('fieldset'); if (fs) l = fs.querySelector('legend'); }
    return t(l);
  };
  const boxValue = c => { // what a react-select box shows as chosen
    let p = c; for (let i = 0; i < 6 && p; i++, p = p.parentElement) {
      const single = p.querySelector('[class*=single-value]'); if (single) return t(single);
      const multi = [...p.querySelectorAll('[class*=multi-value__label]')]; if (multi.length) return multi.map(t).join(', ');
      if (/select__control|select-shell/.test(p.className)) break;
    }
    return '';
  };
  const fields = [], groups = new Set();
  for (const c of form.querySelectorAll('input, textarea, select')) {
    if (c.type === 'hidden' || !c.id || /^iti-/.test(c.id)) continue;
    if ((c.type === 'radio' || c.type === 'checkbox')) {
      const fs = c.closest('fieldset') || c.parentElement.parentElement; if (groups.has(fs)) continue; groups.add(fs);
      const items = [...fs.querySelectorAll(`input[type=${c.type}]`)];
      const leg = t(fs.querySelector('legend')) || labelOf(c);
      const lab = x => t(form.querySelector(`label[for="${CSS.escape(x.id)}"]`)) || t(x.parentElement);
      const on = items.map((x, i) => x.checked ? i : -1).filter(i => i > -1);
      const required = items.some(x => x.required || x.getAttribute('aria-required') === 'true') || /\*\s*$/.test(leg);
      const label = leg.replace(/\s*\*\s*$/, '');
      if (c.type === 'radio') fields.push({ key: fs.id || c.name || c.id, label, required, type: 'radio', options: items.map(lab), optsel: items.map(x => mark(form.querySelector(`label[for="${CSS.escape(x.id)}"]`) || x)), filled: on.length > 0, value: on.length ? lab(items[on[0]]) : '' });
      else if (items.length === 1) fields.push({ key: c.id, label: label || lab(c), required, type: 'checkbox', options: [lab(c)], optsel: [mark(form.querySelector(`label[for="${CSS.escape(c.id)}"]`) || c)], checked: c.checked, filled: c.checked, value: c.checked ? 'checked' : '' });
      else fields.push({ key: fs.id || c.name || c.id, label, required, type: 'checkboxes', options: items.map(lab), optsel: items.map(x => mark(form.querySelector(`label[for="${CSS.escape(x.id)}"]`) || x)), checkedIdx: on, filled: on.length > 0, value: on.map(i => lab(items[i])) });
      continue;
    }
    if (c.type !== 'file' && !vis(c)) continue;
    const raw = labelOf(c), required = c.required || c.getAttribute('aria-required') === 'true' || /\*\s*$/.test(raw);
    const f = { key: c.id, label: raw.replace(/\s*\*\s*$/, ''), required };
    if (c.type === 'file') {
      const box = c.closest('[role=group]') || c.parentElement.parentElement;
      const shown = (t(box).match(/[\w .()-]+\.(pdf|docx?|odt|rtf|txt)\b/i) || [''])[0].trim();
      Object.assign(f, { type: 'file', sel: mark(c), filled: !!(c.files && c.files.length) || !!shown, value: (c.files && c.files[0] && c.files[0].name) || shown });
    } else if (c.getAttribute('role') === 'combobox') {
      const v = boxValue(c); Object.assign(f, { type: 'combobox', sel: mark(c), filled: !!v, value: v });
    } else if (c.tagName === 'SELECT') {
      const o = c.options[c.selectedIndex]; Object.assign(f, { type: 'select', sel: mark(c), options: [...c.options].map(x => t(x)), filled: !!c.value, value: c.value && o ? t(o) : '' });
    } else {
      Object.assign(f, { type: c.tagName === 'TEXTAREA' ? 'textarea' : (c.type || 'text'), sel: mark(c), filled: !!c.value.trim(), value: c.value });
    }
    fields.push(f);
  }
  const submit = [...form.querySelectorAll('button, input[type=submit]')].find(x => /^submit application$/i.test(t(x) || x.value || '') && vis(x));
  return { title: document.title, fields, submitSel: submit ? mark(submit) : '', submitText: submit ? (t(submit) || submit.value) : '', valid: form.checkValidity() };
}

const F = BOOK.facts;
const facts = f => {
  const k = { first_name: 'first_name', last_name: 'last_name', preferred_name: 'preferred_name', email: 'email', phone: 'phone', country: 'country' }[f.key];
  if (k) return { value: F[k], source: 'fact:' + k };
  if (f.key === 'candidate-location') return { value: F.location, query: F.city, source: 'fact:location' };
  return null;
};

stage({
  site: 'greenhouse',
  jobId: url => (url.match(/\/jobs\/(\d+)/) || url.match(/gh_jid=(\d+)/) || [])[1] || url,
  facts,
  READ: `(${readGreenhouse.toString()})()`,
  formReady: READY,
  readPasses: 5, // the job text sits above the form; read down through it first
  open: url => openTab(url, `document.readyState === 'complete' && ${READY}`),
}).catch(e => { console.log('ERROR', e && e.message); process.exit(1); });
