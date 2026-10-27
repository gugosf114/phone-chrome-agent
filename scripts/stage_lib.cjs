// stage_lib.cjs — what stage_ashby.cjs and stage_greenhouse.cjs share. Built 2026-10-26, ported from Agent Bridge's
// Python adapters (tools/session-toolkit/browser-control/ashby_application.py, greenhouse_application.py), no Python.
// The answer book, the hands for each kind of form control, the resume upload, the screenshot, the log, the receipt.
//
// Every click and every key goes through human.cjs. Never element.click(), never .value=.
// NOTHING here presses Submit: press() refuses any target whose text says "submit", and no key is ever Enter.
// The run ends with the Submit button wheeled into view and left alone.
//
// "needs-input" (from the adapters): a question with no answer in the book is never guessed. It is listed as
// unanswered, and the picker (a model) adds a per-job override or George adds a rule to scripts/answers.json.
// The book's test defaults ("any number = 5, any yes/no = Yes") are NOT used here; README: real answers and test
// answers stay apart. The one fallback is the EEO block: no rule = the decline option.

const fs = require('fs'); const path = require('path'); const { execFileSync } = require('child_process');
const human = require('./human.cjs');
const ROOT = path.resolve(__dirname, '..');
const PORT = process.env.CDP_PORT || '19222';
const BOOK = JSON.parse(fs.readFileSync(path.join(ROOT, 'scripts/answers.json'), 'utf8'));
const RULES = BOOK.rules.map(([re, v]) => [new RegExp(re, 'i'), v]);
const NEVER_YES = new RegExp(BOOK.never_yes, 'i');
const DECLINE = /don.?t wish|do not wish|prefer not|decline|not to (answer|say|disclose|specify|self)|do not want to answer|choose not/i;
const EEO = /gender|\bsex\b|race|ethnic|hispanic|latino|veteran|disab|sexual orientation|transgender|pronoun/i;
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : d; };
const norm = s => String(s || '').replace(/\s+/g, ' ').trim().toLowerCase();
const digits = s => String(s || '').replace(/\D/g, '');
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
// Some boxes list states by code (Scale AI's "state of residence": AL, AK, ... CA); the book says "California".
const STATES = { alabama: 'AL', alaska: 'AK', arizona: 'AZ', arkansas: 'AR', california: 'CA', colorado: 'CO', connecticut: 'CT', delaware: 'DE', florida: 'FL', georgia: 'GA', hawaii: 'HI', idaho: 'ID', illinois: 'IL', indiana: 'IN', iowa: 'IA', kansas: 'KS', kentucky: 'KY', louisiana: 'LA', maine: 'ME', maryland: 'MD', massachusetts: 'MA', michigan: 'MI', minnesota: 'MN', mississippi: 'MS', missouri: 'MO', montana: 'MT', nebraska: 'NE', nevada: 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ', 'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', ohio: 'OH', oklahoma: 'OK', oregon: 'OR', pennsylvania: 'PA', 'rhode island': 'RI', 'south carolina': 'SC', 'south dakota': 'SD', tennessee: 'TN', texas: 'TX', utah: 'UT', vermont: 'VT', virginia: 'VA', washington: 'WA', 'west virginia': 'WV', wisconsin: 'WI', wyoming: 'WY', 'district of columbia': 'DC' };

// ---------- answer book ----------
// Order: per-job override > a site's system field (facts) > authorized-to-work > never_yes > rules > EEO decline.
function answerFor(f, jobRules, facts) {
  const l = f.label || '';
  for (const [re, v] of jobRules) if (re.test(l) || re.test(f.key || '')) return { value: v, source: 'override:' + re.source.slice(0, 40) };
  const fact = facts(f); if (fact) return fact;
  if (/authoriz\w* to work|legally authorized|permanently authorized|eligible to work/i.test(l)) return { value: 'Yes', source: 'rule:authorized-to-work (beats never_yes)' };
  if (NEVER_YES.test(l)) return { value: 'No', source: 'never_yes' };
  for (const [re, v] of RULES) if (re.test(l)) return { value: v, source: 'rule:' + re.source.slice(0, 40) };
  // EEO with no rule: the decline row (a type-and-pick box shows its rows only once open, so the book's own phrasing)
  if (EEO.test(l) || EEO.test(f.key || '')) { const d = (f.options || []).find(o => DECLINE.test(o)); if (d || f.type === 'combobox') return { value: d || "I don't wish to answer", source: 'eeo:decline (no rule)' }; }
  return null;
}

// Which option a book answer means. Exact, then the decline family, then "Yes" -> "Yes, I ...", then the JD for
// "Doctorate" (facts.juris_doctor), then a whole-word hit, then a number inside a range ("8" -> "5-10 years").
function pickOption(options, value) {
  const v = norm(value), os = options.map(norm);
  let i = os.indexOf(v); if (i > -1) return i;
  if (STATES[v]) { i = os.indexOf(STATES[v].toLowerCase()); if (i > -1) return i; }
  if (DECLINE.test(value)) { i = options.findIndex(o => DECLINE.test(o)); if (i > -1) return i; }
  i = os.findIndex(o => new RegExp('^' + esc(v) + '\\b').test(o)); if (i > -1) return i;
  if (/^doctorate$/i.test(value) && /^yes$/i.test(BOOK.facts.juris_doctor || '')) { i = options.findIndex(o => /juris doctor|\bj\.?d\.?\b/i.test(o)); if (i > -1) return i; }
  if (v.length >= 4) { i = os.findIndex(o => new RegExp('\\b' + esc(v) + '\\b').test(o)); if (i > -1) return i; }
  if (/^\d+(\.\d+)?$/.test(String(value).trim())) {
    const n = +value;
    i = options.findIndex(o => { const r = o.match(/(\d+)\s*(?:-|–|to)\s*(\d+)/); if (r) return n >= +r[1] && n <= +r[2]; const p = o.match(/(\d+)\s*\+/); return p ? n >= +p[1] : false; });
    if (i > -1) return i;
  }
  return -1;
}

const sameValue = (f, value) => {
  if (!f.filled) return false;
  if (f.type === 'tel') return digits(f.value).endsWith(digits(value));
  if (Array.isArray(f.options) && f.options.length && f.type !== 'combobox') { const i = pickOption(f.options, value); return i > -1 && norm(f.options[i]) === norm(f.value); }
  return norm(f.value) === norm(value) || (f.type === 'combobox' && norm(f.value).startsWith(norm(value)));
};

// ---------- hands for form controls (all through human.cjs) ----------
async function press(h, sel) {
  const t = await h.evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});return e?String(e.innerText||e.value||e.getAttribute('aria-label')||'').trim().slice(0,80):null})()`);
  if (t === null) throw new Error('no element ' + sel);
  if (/submit/i.test(t)) throw new Error('refused: the target says submit (' + t + ')');
  return h.click(sel);
}
const typeInto = (h, sel, text, multiline) => h.type(sel, multiline ? String(text) : String(text).replace(/\s*\n\s*/g, ' ')); // a newline in a one-line box is Enter = submit

// Visible [role=option] rows of whatever list is open, each marked so human.cjs can find it.
const OPTIONS = `(()=>{document.querySelectorAll('[data-stage-opt]').forEach(e=>e.removeAttribute('data-stage-opt'));
  return [...document.querySelectorAll('[role=option]')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0}).slice(0,80).map((e,k)=>{
    e.setAttribute('data-stage-opt',String(k));const r=e.getBoundingClientRect();const t=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);
    return {text:(e.innerText||'').replace(/\\s+/g,' ').trim(),sel:'[data-stage-opt="'+k+'"]',hit:!!t&&(t===e||e.contains(t))}})})()`;
const readOptions = h => h.evaluate(OPTIONS);

// Long menus scroll inside themselves; wheel over the menu (not the page) until the row is in the open.
async function wheelMenu(h, o) {
  for (let k = 0; k < 12; k++) {
    const b = await h.evaluate(`(()=>{const e=document.querySelector(${JSON.stringify(o.sel)});if(!e)return null;const m=e.closest('[role=listbox]')||e.parentElement;const r=e.getBoundingClientRect(),q=m.getBoundingClientRect();const t=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return {hit:!!t&&(t===e||e.contains(t)),dy:(r.top+r.height/2)-(q.top+q.height/2),x:q.left+q.width/2,y:q.top+q.height/2}})()`);
    if (!b || b.hit) return;
    await h.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: b.x, y: b.y, deltaX: 0, deltaY: Math.sign(b.dy) * Math.min(Math.abs(b.dy), 240), pointerType: 'mouse' });
    await h.pause(120, 260);
  }
}

// A type-and-pick box (Greenhouse's react-select, Ashby's location search): open it, look at the rows, type to narrow
// them (or to search), press the row. Never Enter.
async function pickFromBox(h, sel, value, { query } = {}) {
  await press(h, sel); await h.pause(400, 900);
  let options = await readOptions(h); const before = options;
  let i = options.length ? pickOption(options.map(o => o.text), value) : -1;
  if (query || i < 0 || !options[i].hit) {
    const q = query || (i > -1 ? options[i].text : String(value));
    await typeInto(h, sel, q.slice(0, 40));
    let last = '';
    for (let k = 0; k < 20; k++) { // search results arrive late; wait until the list stops changing
      await h.pause(250, 350); options = await readOptions(h);
      const sig = options.map(o => o.text).join('|'); if (options.length && sig === last) break; last = sig;
    }
    i = pickOption(options.map(o => o.text), value);
    if (i < 0 && query) i = pickOption(options.map(o => o.text), query);
  }
  if (i < 0) { await h.key('Escape'); return { ok: false, note: `no row for "${value}"; saw: ${(options.length ? options : before).slice(0, 6).map(o => o.text).join(' / ') || 'none'}` }; }
  if (!options[i].hit) await wheelMenu(h, options[i]);
  const chose = options[i].text;
  await press(h, options[i].sel);
  await h.pause(300, 700);
  if ((await readOptions(h)).length) await h.key('Escape'); // a multi-select stays open after a pick
  return { ok: true, chose };
}

// A native <select>: one press to focus (the list pops open), Escape folds it, arrow keys walk to the row.
async function nativeSelect(h, f, value) {
  const want = pickOption(f.options, value);
  if (want < 0) return { ok: false, note: `no option "${value}"` };
  await press(h, f.sel); await h.pause(300, 700); await h.key('Escape');
  const cur = await h.evaluate(`document.querySelector(${JSON.stringify(f.sel)}).selectedIndex`);
  for (let k = 0; k < Math.abs(want - cur); k++) await h.key(want > cur ? 'ArrowDown' : 'ArrowUp');
  return { ok: true, chose: f.options[want] };
}

async function fill(h, f, a) {
  const v = String(a.value);
  switch (f.type) {
    case 'text': case 'email': case 'tel': case 'url': case 'number': case 'search':
      await typeInto(h, f.sel, v); return { ok: true };
    case 'date': { // a date picker cannot take "Immediately": that answer means today
      const d = /immediately|asap|right away|now/i.test(v) ? new Date() : new Date(v);
      if (isNaN(d)) return { ok: false, note: `"${v}" is not a date` };
      const md = `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}/${d.getFullYear()}`;
      await typeInto(h, f.sel, md); await h.key('Escape'); return { ok: true, chose: md + (md === v ? '' : ` (book: "${v}")`) };
    }
    case 'textarea': await typeInto(h, f.sel, v, true); return { ok: true };
    case 'combobox': return pickFromBox(h, f.sel, v, { query: a.query });
    case 'select': return nativeSelect(h, f, v);
    case 'radio': case 'yesno': {
      const i = pickOption(f.options, v); if (i < 0) return { ok: false, note: `no option "${v}" in ${f.options.join(' / ')}` };
      await press(h, f.optsel[i]); return { ok: true, chose: f.options[i] };
    }
    case 'checkbox': {
      const yes = /^(yes|true|1|checked|agree|i agree)$/i.test(v);
      if (yes !== !!f.checked) await press(h, f.optsel[0]);
      return { ok: true, chose: yes ? 'checked' : 'unchecked' };
    }
    case 'checkboxes': {
      const want = (Array.isArray(a.value) ? a.value : [v]).map(x => pickOption(f.options, x));
      if (want.some(i => i < 0)) return { ok: false, note: `no option "${v}" in ${f.options.join(' / ')}` };
      for (const i of want) if (!(f.checkedIdx || []).includes(i)) await press(h, f.optsel[i]);
      return { ok: true, chose: want.map(i => f.options[i]).join(', ') };
    }
  }
  return { ok: false, note: 'field type not handled: ' + f.type };
}

// ---------- resume ----------
// DOM.setFileInputFiles takes a path on the machine Chrome runs on. The laptop Chrome is Windows, so the file is
// copied to C:\Users\<you>\job-applications-resumes\ first (scp over the same ssh host laptop_chrome.sh uses).
async function uploadResume(h, sel) {
  const name = BOOK.facts.resume_file;
  const local = [arg('--resume'), path.join('/root/job-vault/vault/resumes/current', name), path.join('/root/.cache/resumes', name)].filter(Boolean).find(p => fs.existsSync(p));
  if (!local) return { ok: false, status: 'resume upload skipped: file missing', name };
  let target = local;
  const ver = await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();
  if (/windows/i.test(ver['File-Path-Style'] || '')) {
    const host = process.env.LAPTOP_SSH || 'wimlaptop', ssh = ['-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10'];
    const home = execFileSync('ssh', [...ssh, host, 'powershell -NoProfile -Command "New-Item -ItemType Directory -Force $env:USERPROFILE\\job-applications-resumes | Out-Null; $env:USERPROFILE"'], { encoding: 'utf8', timeout: 40000 }).trim();
    execFileSync('scp', ['-q', ...ssh, local, `${host}:job-applications-resumes/${path.basename(local)}`], { timeout: 90000 });
    target = `${home}\\job-applications-resumes\\${path.basename(local)}`;
  }
  const { result } = await h.send('Runtime.evaluate', { expression: `document.querySelector(${JSON.stringify(sel)})` });
  if (!result || !result.objectId) return { ok: false, status: 'resume upload failed: no file input', name };
  await h.send('DOM.setFileInputFiles', { files: [target], objectId: result.objectId });
  await h.pause(1500, 2500);
  return { ok: true, status: 'uploaded', name, local, target };
}

// ---------- eyes ----------
const CAPTCHA = `(()=>{const vis=e=>{const r=e.getBoundingClientRect();return r.width>60&&r.height>60&&getComputedStyle(e).visibility!=='hidden'};
  return /verify you are human|are you a robot|human verification|press and hold|unusual traffic/i.test((document.body.innerText||'').slice(0,6000))
    ||[...document.querySelectorAll('iframe')].some(f=>/recaptcha\\/(api2|enterprise)\\/bframe|hcaptcha\\.com.*challenge|challenges\\.cloudflare\\.com/.test(f.src)&&vis(f))})()`;

async function reader(h, n) { // wheel down the page with reading pauses, like a person skimming before they fill
  const v = await h.evaluate('({w:innerWidth,h:innerHeight})');
  for (let k = 0; k < n; k++) {
    await h.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: v.w * (0.4 + Math.random() * 0.2), y: v.h * (0.4 + Math.random() * 0.2), deltaX: 0, deltaY: 280 + Math.random() * 380, pointerType: 'mouse' });
    await h.pause(900, 2200);
  }
}

async function screenshot(h, file) { // the whole page, top to bottom
  const m = await h.send('Page.getLayoutMetrics'); const c = m.cssContentSize || m.contentSize;
  const { data } = await h.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { x: 0, y: 0, width: Math.ceil(c.width), height: Math.min(Math.ceil(c.height), 16000), scale: 1 } });
  fs.writeFileSync(file, Buffer.from(data, 'base64'));
}

// New tab in the laptop Chrome (never a new Chrome), wait for the page, then attach the hands with their settle.
async function openTab(url, readyExpr, ms = 30000) {
  const tab = await (await fetch(`http://127.0.0.1:${PORT}/json/new?${url}`, { method: 'PUT' })).json();
  const probe = await human.attach(tab, { settle: false });
  const t0 = Date.now(); while (Date.now() - t0 < ms) { try { if (await probe.evaluate(readyExpr)) break; } catch { } await human.sleep(400); }
  probe.close();
  return human.attach(tab, { log: m => process.stderr.write('  [human] ' + m + '\n') });
}

// ---------- the walk ----------
// cfg: { site, jobId(url), facts(field), READ (page expression -> {fields, title, submitSel, submitText, valid}),
//        loaded (expr), openForm(h, url), formReady (expr), readPasses }
async function stage(cfg) {
  const url = process.argv[2];
  if (!url || url.startsWith('--')) { console.log(`usage: CDP_PORT=19222 node scripts/stage_${cfg.site}.cjs <job-url> [--overrides file.json] [--resume file.pdf]`); process.exit(2); }
  if (['9335', '9336'].includes(String(PORT))) { console.log('refused: 9335 and 9336 are the phone Chromes; use the laptop on 19222'); process.exit(2); }
  setTimeout(() => { console.log('TIMEOUT 15 min'); process.exit(3); }, 15 * 60 * 1000);
  const t0 = Date.now(), stamp = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19);
  const LOGDIR = path.join(ROOT, 'logs/stage'); fs.mkdirSync(LOGDIR, { recursive: true });
  const OUT = path.join(LOGDIR, `${cfg.site}-${stamp}.json`), PNG = path.join(LOGDIR, `${cfg.site}-${stamp}.png`);
  const jobId = cfg.jobId(url);
  const OVR = arg('--overrides') ? JSON.parse(fs.readFileSync(arg('--overrides'), 'utf8')) : {};
  const o = OVR[jobId] || OVR['*'] || {};
  const log = { site: cfg.site, url, jobId, startedAt: new Date().toISOString(), status: '', title: '', fields: [], unanswered: [], resume: null, submit: null, screenshot: null };
  const finish = (status) => {
    log.status = status; log.ms = Date.now() - t0; log.endedAt = new Date().toISOString();
    fs.writeFileSync(OUT, JSON.stringify(log, null, 1));
    const filled = log.fields.filter(f => f.ok).length, optional = log.fields.filter(f => /^skipped/.test(f.source || '')).length;
    console.log([
      `${status} · ${cfg.site} · ${log.title || jobId} · ${(log.ms / 1000).toFixed(0)} s`,
      url,
      `filled ${filled} · unanswered required ${log.unanswered.length}${log.unanswered.length ? ' (' + log.unanswered.map(u => u.label.slice(0, 40)).join('; ') + ')' : ''} · optional left empty ${optional}`,
      `resume: ${log.resume ? (log.resume.ok ? 'uploaded ' + log.resume.name : log.resume.status) : 'no resume field'}`,
      `stopped at: ${log.submit && log.submit.found ? '"' + log.submit.text + '" (NOT pressed)' : 'no Submit button seen'}${log.formValid === undefined ? '' : ' · form valid: ' + (log.formValid ? 'yes' : 'no')}`,
      `log ${path.relative(ROOT, OUT)} · screenshot ${log.screenshot ? path.relative(ROOT, log.screenshot) : 'none'}`,
    ].join('\n'));
  };
  if (o.skip) { log.skipped = o.skip; finish('SKIPPED_BY_PICKER'); process.exit(0); }
  const jobRules = (o.rules || []).map(([re, v]) => [new RegExp(re, 'i'), v]);

  const h = await cfg.open(url);
  const stopIfCaptcha = async (where) => {
    if (!(await h.evaluate(CAPTCHA))) return;
    log.captchaAt = where; await screenshot(h, PNG).then(() => { log.screenshot = PNG; }).catch(() => { });
    finish('CAPTCHA_STOP'); h.close(); process.exit(4);
  };
  await stopIfCaptcha('open');
  await reader(h, cfg.readPasses || 3);
  const ready = await (async () => { const t = Date.now(); while (Date.now() - t < 20000) { if (await h.evaluate(cfg.formReady)) return true; await human.sleep(400); } return false; })();
  if (!ready) { log.title = await h.evaluate('document.title'); finish('NO_FORM'); h.close(); process.exit(5); }
  await stopIfCaptcha('form');

  // One field at a time, re-reading the page each time: answers can open follow-up questions, React can re-draw.
  const done = new Map();
  for (let pass = 0; pass < 80; pass++) {
    const page = await h.evaluate(cfg.READ); log.title = page.title;
    const f = page.fields.find(x => !done.has(x.key));
    if (!f) break;
    const rec = { label: f.label, key: f.key, type: f.type, required: !!f.required, options: (f.options || []).slice(0, 12), had: f.value || '', filledWith: null, source: null, ok: false };
    done.set(f.key, rec); log.fields.push(rec);
    if (f.type === 'file') {
      if (!/resume|\bcv\b/i.test(f.label)) { rec.source = 'skipped (optional, only the resume is uploaded)'; if (f.required) rec.source = 'NO_ANSWER (only the resume is uploaded)'; continue; }
      if (f.filled) { rec.ok = true; rec.source = 'already attached'; log.resume = { ok: true, name: f.value || 'already attached' }; continue; }
      try { log.resume = await uploadResume(h, f.sel); } catch (e) { log.resume = { ok: false, status: 'resume upload failed: ' + e.message.slice(0, 120) }; }
      rec.ok = !!log.resume.ok; rec.filledWith = log.resume.name; rec.source = 'fact:resume_file' + (log.resume.ok ? '' : ' · ' + log.resume.status);
      continue;
    }
    const a = answerFor(f, jobRules, cfg.facts);
    if (!a) { rec.source = f.required ? 'NO_ANSWER' : 'skipped (optional, no answer in the book)'; continue; }
    rec.source = a.source;
    if (sameValue(f, a.value)) { rec.filledWith = f.value; rec.ok = true; rec.note = 'already there'; continue; }
    try { const r = await fill(h, f, a); rec.filledWith = r.chose || a.value; rec.ok = r.ok; if (r.note) rec.note = r.note; }
    catch (e) { rec.ok = false; rec.note = e.message.slice(0, 160); }
    await h.pause(300, 900);
  }

  // Read the page once more: what the form now holds is the truth, not what we meant to type.
  await h.pause(1200, 2000);
  const fin = await h.evaluate(cfg.READ);
  for (const f of fin.fields) {
    const rec = done.get(f.key); if (!rec) continue;
    rec.final = Array.isArray(f.value) ? f.value.join(', ') : f.value;
    if (rec.ok && !f.filled && rec.type !== 'checkbox') { rec.ok = false; rec.note = (rec.note ? rec.note + '; ' : '') + 'empty on re-read'; }
  }
  for (const rec of log.fields) { // Greenhouse swaps the file box for the file's name once it is attached
    if (rec.type !== 'file' || !rec.ok || rec.final !== undefined) continue;
    const shown = await h.evaluate(`document.body.innerText.includes(${JSON.stringify(rec.filledWith || '')})`);
    if (shown) rec.final = rec.filledWith + ' (shown on the page)'; else { rec.ok = false; rec.note = 'file name not on the page after upload'; log.resume.ok = false; }
  }
  log.unanswered = fin.fields.filter(f => f.required && !f.filled).map(f => ({ label: f.label, type: f.type, options: (f.options || []).slice(0, 12), why: (done.get(f.key) || {}).note || (done.get(f.key) || {}).source || 'appeared late' }));
  log.formValid = fin.valid;
  log.submit = { found: !!fin.submitSel, text: fin.submitText || '', pressed: false };
  if (fin.submitSel) await h.scrollTo(fin.submitSel).catch(() => { }); // one click away; this script never makes it
  await stopIfCaptcha('end');
  await h.pause(600, 1200);
  try { await screenshot(h, PNG); log.screenshot = PNG; } catch (e) { log.screenshotError = e.message; }
  finish(log.unanswered.length ? 'NEEDS_INPUT' : 'READY_TO_SUBMIT');
  h.close(); process.exit(0);
}

module.exports = { stage, openTab, press, pickOption, answerFor, BOOK, PORT, human };
