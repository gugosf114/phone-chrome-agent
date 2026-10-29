// map_easy_apply.cjs — walk LinkedIn Easy Apply on N jobs, fill from the answer book, STOP one click before Submit,
// and log every screen, field, fork, and the time each run took. Never submits without --submit. Dismisses + discards each form.
// Clocks (10/27): every Chrome command 20 s (human.cjs), every job --clock 90 s → TIMED_OUT and on to the next. After a
// --submit run the receipt is LinkedIn's own Applied list (scripts/applied_check.cjs), never the pop-up after the click.
//
//   CDP_PORT=19222 node scripts/map_easy_apply.cjs --jobs 10 --keywords "legal operations"
//   CDP_PORT=19222 node scripts/map_easy_apply.cjs --ids 111,222 --jobs 2 [--overrides picks/picks-<stamp>.json]
//
// Hands: scripts/human.cjs (10/27). Every press is a pointer path + press/release, every box is filled key by key,
// drop-downs are opened with a real click and walked with ArrowDown/ArrowUp + Enter, scrolling is the wheel.
// No element.click(), no .value setters, no Runtime.enable. Proven 10/27 on the laptop Chrome: the native drop-down
// opens over CDP and takes the keys. If a drop-down ever refuses the keys, the setter is the last resort and the
// log says "setter: <label>".
// Stops the whole run (exit 4) on a captcha, a /checkpoint/ or login wall, or HTTP 999. Touches nothing after that.
// Output: logs/easy_apply_map/map-<stamp>.jsonl (one line per job) + logs/easy_apply_map/seen-forks.json (grows across runs).
// A "fork" = screen heading + field type + field label. A run's "new forks" = ones no earlier run has seen.
// A "miss" = a field the book did not answer: no rule hit, or only a test default (number 5, text/yes-no "Yes").
// Job files (10/27): resume + cover letter per job from picks ("resume_file", "letter_file": laptop paths; "letter_text": the
// letter's text; "letter" is the human angle and is never typed) or the apply/<jobId>/ folder (meta.json names, pushed to the laptop by scripts/push_apply_files.sh).
// A form that offers a cover letter with neither in hand stops that job: NEEDS_LETTER.
// No silent skips (10/27): every field the form offers, required or optional, is filled from the book / picks, or the job
// stops with NEEDS_INPUT naming the field. Nothing is left empty and walked past.

const fs = require('fs'); const path = require('path');
const human = require('./human.cjs');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const rnd = (a, b) => a + Math.random() * (b - a);
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : d; };
const JOBS = parseInt(arg('--jobs', '10'), 10);
const JOB_CLOCK = parseInt(arg('--clock', '90'), 10); // seconds per job before TIMED_OUT (10/27)
const KW = arg('--keywords', 'legal operations');
const PORT = process.env.CDP_PORT || '19222';
const ROOT = path.resolve(__dirname, '..');
const BOOK = JSON.parse(fs.readFileSync(path.join(ROOT, 'scripts/answers.json'), 'utf8'));
const LOGDIR = path.join(ROOT, 'logs/easy_apply_map');
// --overrides <file.json>: { "<jobId>": { "skip": "reason" | "rules": [[regex, answer], ...] } } — per-job answers written by the thinker before the run
const OVR = arg('--overrides', '') ? JSON.parse(fs.readFileSync(arg('--overrides', ''), 'utf8')) : {};
let CUR_RULES = []; fs.mkdirSync(LOGDIR, { recursive: true });
const stamp = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19);
const OUT = path.join(LOGDIR, `map-${stamp}.jsonl`);
const SEENF = path.join(LOGDIR, 'seen-forks.json');
const seen = new Set(fs.existsSync(SEENF) ? JSON.parse(fs.readFileSync(SEENF, 'utf8')) : []);
setTimeout(() => { console.log('TIMEOUT 25 min'); process.exit(3); }, 25 * 60 * 1000);

// ---------- answer book ----------
const NEVER_YES = new RegExp(BOOK.never_yes, 'i');
const RULES = BOOK.rules.map(([re, v]) => [new RegExp(re, 'i'), v]);
function answerFor(label, type, options) {
  const l = (label || '').trim();
  if (!l) return null;
  if (/authoriz\w* to work|legally authorized|permanently authorized|eligible to work/i.test(l)) return { value: 'Yes', source: 'rule:authorized-to-work (beats never_yes)' };
  if (NEVER_YES.test(l)) return { value: 'No', source: 'never_yes' };
  const fits = v => v !== 'ALL' || type === 'checkboxgroup'; // "ALL" = tick every box; it means nothing to other fields
  for (const [re, v] of CUR_RULES) if (re.test(l) && fits(v)) return { value: v, source: 'job-rule:' + re.source.slice(0, 30) };
  const hk = l.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').replace(/[\s*:]+$/, '').toLowerCase(); const hh = (BOOK.history || {})[hk]; // George's own past answer to this exact question (LinkedIn export 10/29); beats the regex rules
  if (hh && fits(hh.answer)) return { value: hh.answer, source: 'history:' + hh.n + 'x' };
  for (const [re, v] of RULES) if (re.test(l) && fits(v)) return { value: v, source: 'rule:' + re.source.slice(0, 30) };
  if (type === 'number') return BOOK.defaults.number ? { value: BOOK.defaults.number, source: 'default:number' } : null; // 10/27 George: no guessing; null = NEEDS_INPUT
  if (type === 'radio' && (options || []).some(o => /\.(pdf|docx?)$/i.test(o))) return { value: BOOK.facts.resume_file || options[0], source: 'fact:resume_file' };
  if (type === 'radio' || type === 'select') {
    const opts = (options || []).map(o => o.toLowerCase());
    const dec = opts.findIndex(o => /do not want to answer|prefer not|don.?t wish|decline to/.test(o)); if (dec > -1) return { value: options[dec], source: 'default:decline-option' };
    if (BOOK.defaults.yesNo && opts.some(o => /^yes$/.test(o))) return { value: BOOK.defaults.yesNo, source: 'default:yesNo' };
    return null;
  }
  if (type === 'text' || type === 'textarea') return BOOK.defaults.text ? { value: BOOK.defaults.text, source: 'default:text' } : null;
  if (type === 'checkbox' && /agree|consent|acknowledge|terms|certify/i.test(l)) return { value: 'Yes', source: 'consent box' };
  return null;
}
const isMiss = src => !src || /^(NO_ANSWER|FAILED|default:(number|text|yesNo))/.test(src);
// Is a value LinkedIn saved from an old application the same answer as the book's? Loose on purpose:
// "4156328008" = "415-632-8008", "Daly City, California, United States" = "Daly City, CA", "Juris Doctor (J.D.)" = "Juris Doctor".
const norm = s => String(s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
function same(had, want, type) {
  const a = norm(had), b = norm(want);
  if (a === b) return true;
  const da = String(had).replace(/\D/g, ''), db = String(want).replace(/\D/g, '');
  if (da.length >= 7 && da === db) return true;
  if (/^\s*\d+(\.\d+)?\s*$/.test(had) && /^\s*\d+(\.\d+)?\s*$/.test(want)) return +had === +want;
  if ((type === 'select' || type === 'radio') && b && a.includes(b)) return true;
  if (String(want).includes(',') && b) return a.startsWith(norm(String(want).split(',')[0]));
  return false;
}
const CHECKED_TYPES = new Set(['select', 'radio', 'text', 'number', 'textarea', 'typeahead']); // saved values of these get the book check
const isResumeCard = f => f.type === 'radio' && /\.(pdf|docx?)$/i.test(f.label);
// Which radio option the book's value means; -1 when it is not one of them.
function radioIndex(f, value) {
  const o = (f.options || []).map(x => x.toLowerCase()), w = String(value).toLowerCase();
  let j = o.indexOf(w); if (j < 0) j = o.findIndex(x => x.startsWith(w));
  if (j < 0 && /don.?t wish|prefer not|decline/.test(w)) j = o.findIndex(x => /prefer not|don.?t wish|decline|not to (answer|specify|say|disclose)/.test(x));
  return j;
}
// This job's resume and cover letter: picks keys first, then apply/<jobId>/ (files on the laptop under meta.json's names).
// No job resume = the book's resume_file, selected from LinkedIn's saved list (never uploaded).
function jobFiles(jid, o) {
  const dir = path.join(ROOT, 'apply', jid), metaF = path.join(dir, 'meta.json');
  const meta = fs.existsSync(metaF) ? JSON.parse(fs.readFileSync(metaF, 'utf8')) : null;
  const win = name => `C:\\Users\\georg\\job-applications\\${jid}\\${name}`;
  const base = p => String(p).split(/[\\/]/).pop();
  const resumePath = o.resume_file || (meta ? win(meta.resume_name) : null);
  const letterPath = o.letter_file || (meta ? win(meta.letter_name) : null);
  const txtF = path.join(dir, 'cover-letter.txt');
  const letterText = fs.existsSync(txtF) ? fs.readFileSync(txtF, 'utf8').trim() : (o.letter_text || null); // 'letter' in picks is the human angle, never typed
  return { resumePath, resumeName: resumePath ? base(resumePath) : BOOK.facts.resume_file, letterPath, letterName: letterPath ? base(letterPath) : null, letterText, from: o.resume_file || o.letter_file || o.letter_text ? 'picks' : meta ? 'apply/' + jid : 'none' };
}

// Stop signs: the run ends on any of these and touches nothing more.
const BLOCKED = `(()=>{const nav=performance.getEntriesByType("navigation")[0]||{};if(nav.responseStatus===999)return "HTTP 999";
  if(/\\/(checkpoint|authwall|uas\\/login|login)\\b/.test(location.pathname))return "wall page: "+location.pathname;
  if(document.querySelector('iframe[src*="captcha" i], iframe[title*="captcha" i], iframe[title*="challenge" i], #captcha-internal'))return "captcha";
  if(/quick security check|security verification|verify you.?re (a )?human/i.test((document.body&&document.body.innerText||"").slice(0,4000)))return "captcha text";return ""})()`;

(async () => {
  // ---------- connect ----------
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  const tab = list.find(o => o.type === 'page' && o.url.includes('linkedin.com')) || list.find(o => o.type === 'page');
  if (!tab) { console.log('no tab on port', PORT); process.exit(2); }
  // 10/28: a tab behind another tab reads as hidden and every mouse event takes 5 s; make ours the front tab first
  try { await fetch(`http://127.0.0.1:${PORT}/json/activate/${tab.id}`); await new Promise(r => setTimeout(r, 600)); } catch {}
  const h = await human.attach(tab, { log: m => process.stderr.write('  [human] ' + m + '\n') });
  // Uploads: Chrome's file chooser is answered in code (no dialog on the laptop screen); the press on the button stays human.
  let chooserWaiter = null;
  await h.send('Page.enable'); await h.send('Page.setInterceptFileChooserDialog', { enabled: true });
  h.on('Page.fileChooserOpened', p => { if (chooserWaiter) chooserWaiter(p); });
  const ev = async x => { try { return await h.evaluate(x); } catch (e) { console.log('PAGE EXC:', e.message.slice(0, 200), 'in:', x.slice(0, 90).replace(/\s+/g, ' ')); return undefined; } };
  // 10/27: hidden window = 5 s per mouse event = a frozen-looking run. Before each job: if the tab is hidden, show the
  // laptop window (ShowAgentChrome task over ssh, laptop pipe only), re-check, and stop the run if it stays hidden.
  const showWindow = async () => {
    await h.send('Page.bringToFront').catch(() => {});
    if (!await ev('document.hidden')) return true;
    if (PORT === '19222') { try { require('child_process').execFileSync('ssh', ['-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes', 'wimlaptop', 'schtasks /run /tn ShowAgentChrome'], { stdio: 'ignore', timeout: 20000 }); } catch {} await sleep(3000); }
    if (!await ev('document.hidden')) { console.log('  window was hidden; shown again'); return true; }
    console.log('STOP: the Chrome tab is hidden and will not show. Every mouse event would take 5 s. Show the window, then rerun.'); process.exit(5);
  };
  const stopIfBlocked = async (rec) => {
    const why = await ev(BLOCKED); if (!why) return;
    console.log(`STOP: ${why} (job ${rec ? rec.jobId : '-'}). Nothing touched after this.`);
    if (rec) { rec.status = 'STOPPED_BLOCKED'; rec.error = why; fs.appendFileSync(OUT, JSON.stringify(rec) + '\n'); }
    h.close(); process.exit(4);
  };

  // ---------- hands (human.cjs) ----------
  // Never a press on Submit (unless --submit), Save, Follow, or Message, whatever the caller asked for.
  const FORBID = /^(submit|save|follow|message)\b/i;
  const SUBMIT = process.argv.includes('--submit');
  async function click(sel) {
    const t = await ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});const b=e&&e.closest("button,a,[role=button]");return b?((b.innerText||"")+" "+(b.getAttribute("aria-label")||"")).replace(/\\s+/g," ").trim():""})()`) || '';
    if (FORBID.test(t) && !(SUBMIT && /^submit/i.test(t))) { console.log(`  REFUSED a press on "${t.slice(0, 40)}"`); return false; }
    try { await h.click(sel); return true; } catch (e) { console.log('  hands:', e.message.slice(0, 120)); return false; }
  }
  async function typeInto(sel, text) { try { await h.type(sel, text); return true; } catch (e) { console.log('  hands:', e.message.slice(0, 120)); return false; } }
  // A drop-down: real click opens the list, arrows walk from the current option to the wanted one, Enter takes it.
  // If the list ignored the keys, the arrows go to the closed (focused) box. Last resort: the setter, logged.
  async function pickSelect(f, wanted) {
    const t = await ev(`(()=>{const s=document.querySelector(${JSON.stringify(f.sel)});if(!s)return null;const w=${JSON.stringify(String(wanted).toLowerCase())};
      const all=[...s.options];const opts=all.filter(o=>!/select an option|^select$|^--/i.test(o.text.trim()));
      let o=opts.find(o=>o.text.trim().toLowerCase()===w)||opts.find(o=>o.text.toLowerCase().includes(w))||opts.find(o=>o.value.toLowerCase()===w);
      if(!o&&/^yes$/i.test(w))o=opts.find(o=>/^yes\\b/i.test(o.text));if(!o&&/^no$/i.test(w))o=opts.find(o=>/^no\\b/i.test(o.text));
      if(!o)return {miss:true};const tx=all.map(x=>x.text.trim().toLowerCase()),wi=all.indexOf(o),w0=tx[wi];let pre=o.text.trim();
      for(let n=2;n<=w0.length;n++){if(tx.filter(x=>x.startsWith(w0.slice(0,n))).length===1){pre=o.text.trim().slice(0,n);break}}
      return {want:wi,text:o.text.trim(),prefix:pre}})()`);
    if (!t) return 'no el'; if (t.miss) return 'no option for ' + wanted;
    const at = () => ev(`document.querySelector(${JSON.stringify(f.sel)}).selectedIndex`);
    const isOpen = () => ev(`(()=>{try{return document.querySelector(${JSON.stringify(f.sel)}).matches(":open")}catch(e){return false}})()`);
    // near: arrows. Far down a long list (LinkedIn's School list has 2,467 schools): type the start of the name instead.
    const walk = async () => { const n = t.want - Math.max(0, await at()); if (Math.abs(n) > 15) return h.keys(t.prefix); for (let i = 0; i < Math.abs(n); i++) await h.key(n > 0 ? 'ArrowDown' : 'ArrowUp'); };
    if (await click(f.sel)) {
      await h.pause(250, 600); await walk();
      if (await isOpen()) await h.key('Enter');
      await h.pause(200, 500); if (await at() === t.want) return 'ok:' + t.text;
      if (await isOpen()) await click(f.sel); // the list is still up and deaf: a second press on the box closes it
      await h.pause(200, 400); await walk(); await h.pause(200, 400);
      if (await at() === t.want) return 'ok:' + t.text + ' (closed-box arrows)';
    }
    const r = await ev(`(()=>{const s=document.querySelector(${JSON.stringify(f.sel)});const set=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,"value").set;set.call(s,s.options[${t.want}].value);
      s.dispatchEvent(new Event("input",{bubbles:true}));s.dispatchEvent(new Event("change",{bubbles:true}));return s.selectedIndex})()`);
    console.log(`  setter: ${f.label}`);
    return r === t.want ? 'ok:' + t.text + ' (setter)' : 'setter failed';
  }
  // The wheel, never a JS scroll. dy > 0 = down.
  async function wheel(dy, at) {
    const p = at || await ev('({x:innerWidth*(0.35+Math.random()*0.3),y:innerHeight*(0.35+Math.random()*0.3)})');
    await h.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: p.x, y: p.y, deltaX: 0, deltaY: dy, pointerType: 'mouse' });
    await h.pause(300, 800);
  }

  // Put the book's answer into one field with the hands; true when the field now holds it.
  // allowDefault: an EMPTY yes/no radio whose rule value is not an option gets the test yes/no default (old behaviour).
  // A saved answer is never overwritten with a test default.
  async function fillField(f, a, entry, allowDefault = true) {
    if (f.type === 'select') { const r = String(await pickSelect(f, a.value)); if (!/^ok/.test(r) || /setter/.test(r)) entry.note = /setter/.test(r) ? 'setter: ' + f.label : r; return /^ok/.test(r); }
    if (f.type === 'radio') {
      let j = radioIndex(f, a.value);
      const yn = (f.options || []).some(o => /^yes$/i.test(o)) && (f.options || []).some(o => /^no$/i.test(o));
      if (j < 0 && allowDefault && BOOK.defaults.yesNo && yn && !/\.(pdf|docx?)$/i.test(a.value)) { a.source = 'default:yesNo (rule value "' + a.value + '" not an option)'; a.value = BOOK.defaults.yesNo; j = radioIndex(f, a.value); }
      if (j < 0 && allowDefault && (f.options || []).some(o => /\.(pdf|docx?)$/i.test(o))) j = Math.max(0, (f.options || []).findIndex(o => o.includes(BOOK.facts.resume_file || '\u0000')));
      if (j < 0) { entry.note = 'not an option: ' + a.value; return false; }
      const verify = async () => { const s2 = await snap(); const g = (s2.fields || []).find(x => x.type === 'radio' && x.label === f.label); return !!(g && g.value === f.options[j]); };
      await click(f.optsel[j]); await h.pause(300, 600);
      let chk = await verify();
      if (!chk) { await click(f.radiosel[j]); await h.pause(300, 500); chk = await verify(); entry.note = 'second press, on the radio itself'; }
      return chk;
    }
    if (f.type === 'checkboxgroup') { // book value "ALL" ticks every box (George 10/27: contract types); else "A; B" ticks those
      const want = String(a.value).toUpperCase() === 'ALL' ? f.options.map((_, i) => i)
        : String(a.value).split(/\s*;\s*/).map(v => f.options.findIndex(o => o.toLowerCase().startsWith(v.toLowerCase()))).filter(i => i > -1);
      if (!want.length) { entry.note = 'no box matches: ' + a.value; return false; }
      const ticked = [];
      for (const i of want) { if (f.checked[i]) continue; if (await click(f.optsel[i])) ticked.push(f.options[i]); await h.pause(200, 600); }
      const g = ((await snap()).fields || []).find(x => x.type === 'checkboxgroup' && x.label === f.label);
      entry.ticked = ticked;
      console.log(`  ticked ${ticked.length} of ${f.options.length} in "${f.label.slice(0, 60)}": ${ticked.join(', ')}`);
      return !!g && want.every(i => g.checked[i]);
    }
    if (f.type === 'checkbox') { // one box: the book's No is an answer (left unticked, logged); anything else ticks it
      if (/^no$/i.test(String(a.value))) { entry.note = 'book says No: left unticked'; return true; }
      await click(f.sel); await h.pause(300, 600);
      const g = ((await snap()).fields || []).find(x => x.type === 'checkbox' && x.label === f.label);
      return !!(g && g.value);
    }
    if (f.type === 'text' || f.type === 'number' || f.type === 'textarea' || f.type === 'typeahead') { const ok = await typeInto(f.sel, a.value); if (ok && f.type === 'typeahead') { await h.pause(900, 1500); await h.key('ArrowDown'); await h.key('Enter'); } return ok; }
    return false;
  }

  // ---------- screen reader ----------
  // Marks are stable across reads (window.__mfN only grows), so a later read never points an old selector at a new element.
  const SNAP = `(()=>{const d=document.querySelector("dialog[open], [role=dialog], .jobs-easy-apply-modal");if(!d)return JSON.stringify({modal:false});
    const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0};
    const txt=e=>(e?(e.innerText||e.textContent||""):"").replace(/\\s+/g," ").trim();
    const dtxt=txt(d);const prog=(dtxt.match(/(\\d+)\\/(\\d+) pages?/i)||[])[0]||"";const h3s=[...d.querySelectorAll("h3")].map(txt).filter(Boolean);const own=e=>[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(" ").replace(/\\s+/g," ").trim();const els=[...d.querySelectorAll("*")];const pi=els.findIndex(e=>prog&&own(e)===prog);let title="";if(pi>-1){for(let i=pi+1;i<els.length;i++){const t=own(els[i]);if(t&&t.length>=3&&t.length<=40&&!/^Apply to/i.test(t)){title=t;break}}}const heading=(title||h3s[0]||(prog?txt(d.querySelector("h2")):"Single page")||"").slice(0,60);
    const labelOf=el=>{let l="";if(el.id){const f=d.querySelector('label[for="'+CSS.escape(el.id)+'"]');if(f)l=txt(f)}
      if(!l)l=el.getAttribute("aria-label")||"";if(!l){const fs=el.closest("fieldset");if(fs)l=txt(fs.querySelector("legend"))}
      if(!l){const g=el.closest("[data-test-form-element], .fb-dash-form-element, .jobs-easy-apply-form-element, .artdeco-text-input--container");if(g){const lab=g.querySelector("label, legend, span[aria-hidden]");l=txt(lab)}}
      if(!l)l=el.placeholder||el.name||"";return l.replace(/[*\\u00a0\\s]+$/,"").slice(0,120)};
    const req=el=>el.required||el.getAttribute("aria-required")==="true";
    const fields=[];const mark=el=>{let k=el.getAttribute("data-map-idx");if(!k||!/^mf/.test(k)){k="mf"+(window.__mfN=(window.__mfN||0)+1);el.setAttribute("data-map-idx",k)}return "[data-map-idx="+k+"]"};
    d.querySelectorAll("select").forEach(s=>{if(!vis(s))return;const cur=s.options[s.selectedIndex]?.text.trim()||"";const empty=!s.value||/select an option|^select$|^--/i.test(cur);
      fields.push({type:"select",label:labelOf(s),required:req(s),options:[...s.options].map(o=>o.text.trim()).filter(t=>!/select an option/i.test(t)).slice(0,12),value:empty?"":cur,sel:mark(s)})});
    const groups={};d.querySelectorAll("input[type=radio]").forEach(r=>{(groups[r.name]=groups[r.name]||[]).push(r)});Object.entries(groups).forEach(([name,rs])=>{const fs=rs[0].closest("fieldset")||rs[0].closest("[role=radiogroup]");if(!(rs.some(vis)||(fs&&vis(fs))))return;const label=txt(fs?.querySelector("legend"))||(rs[0].getAttribute("aria-label")||"").replace(/[*\\u00a0\\s]+$/,"")||labelOf(rs[0])||name;const opts=rs.map(r=>{const lab=r.id?d.querySelector('label[for="'+CSS.escape(r.id)+'"]'):null;const row=r.parentElement&&r.parentElement.parentElement;const t=txt(lab)||(row?txt(row):"")||r.value;const target=(lab&&vis(lab))?lab:((row&&vis(row))?row:r);return {text:t.slice(0,80),sel:mark(target)}});const chosen=rs.find(r=>r.checked);fields.push({type:"radio",label:label.slice(0,160),required:true,options:opts.map(o=>o.text),optsel:opts.map(o=>o.sel),radiosel:rs.map(mark),value:chosen?((opts[rs.indexOf(chosen)]||{}).text||"chosen"):""})});
    // checkboxes: a box's words are its label, or (2026 LinkedIn: empty label) the paragraph beside it. Boxes that share a
    // parent are one question ("Please specify the contracts ..."); its words are the line just above the first box.
    const rowOf=c=>{let r=c.parentElement;for(let k=0;k<5&&r&&r!==d;k++){if(txt(r))return r;r=r.parentElement}return null};
    const boxText=c=>{const lab=c.id?d.querySelector('label[for="'+CSS.escape(c.id)+'"]'):null;return (txt(lab)||c.getAttribute("aria-label")||txt(rowOf(c))||"").slice(0,120)};
    const groupOf=c=>{let g=c.parentElement;for(let k=0;k<8&&g&&g!==d;k++){if(g.querySelectorAll("input[type=checkbox]").length>1)return g;g=g.parentElement}return null};
    const questionOf=(g,first)=>{const fs=g.closest("fieldset");if(fs&&txt(fs.querySelector("legend")))return txt(fs.querySelector("legend"));let a=g;for(let k=0;k<4&&a&&a!==d;k++){const it=a.innerText||"";const i=first?it.indexOf(first):-1;if(i>0){const raw=it.slice(0,i),ls=raw.split("\\n").map(x=>x.trim()).filter(x=>x&&!/^[*\\s]+$/.test(x));if(ls.length)return ls[ls.length-1]+(/\\*\\s*$/.test(raw)?"*":"")}a=a.parentElement}return ""};
    const cbs=new Map();
    d.querySelectorAll("input[type=checkbox]").forEach(c=>{const lab=c.id?d.querySelector('label[for="'+CSS.escape(c.id)+'"]'):null;if(!vis(c)&&!(lab&&vis(lab)))return;const g=groupOf(c)||c;if(!cbs.has(g))cbs.set(g,[]);cbs.get(g).push({c,lab})});
    cbs.forEach((boxes,g)=>{const tgt=b=>mark((b.lab&&vis(b.lab))?b.lab:b.c);
      if(boxes.length===1){const b=boxes[0];fields.push({type:"checkbox",label:boxText(b.c),required:req(b.c),value:b.c.checked?"checked":"",sel:tgt(b)});return}
      const opts=boxes.map(b=>boxText(b.c)),q=questionOf(g,opts[0]);
      fields.push({type:"checkboxgroup",label:q.replace(/[*\\u00a0\\s]+$/,"").slice(0,160),required:/\\*\\s*$/.test(q)||boxes.some(b=>req(b.c)),options:opts,optsel:boxes.map(tgt),checked:boxes.map(b=>b.c.checked),value:boxes.filter(b=>b.c.checked).map(b=>boxText(b.c)).join("; ")})});
    d.querySelectorAll("input:not([type]),input[type=text],input[type=number],input[type=email],input[type=tel],input[type=url],textarea").forEach(i=>{if(!vis(i)||i.readOnly||i.disabled)return;
      const type=i.tagName==="TEXTAREA"?"textarea":(i.type==="number"?"number":(i.getAttribute("role")==="combobox"||i.getAttribute("aria-autocomplete")?"typeahead":"text"));
      fields.push({type,label:labelOf(i),required:req(i),value:(i.value||"").trim(),sel:mark(i)})});
    d.querySelectorAll("input[type=file]").forEach(f=>{fields.push({type:"file",label:labelOf(f)||"file upload",required:req(f),value:"",sel:mark(f)})});
    const btns=[...d.querySelectorAll("button")].filter(vis).map(b=>({t:((b.innerText||"")+" "+(b.getAttribute("aria-label")||"")).replace(/\\s+/g," ").trim(),sel:mark(b)}));
    const pick=re=>btns.find(b=>re.test(b.t));
    const uploads=btns.filter(b=>/^Upload\\b/i.test(b.t)).map(b=>({kind:/resume|\\bcv\\b/i.test(b.t)?"resume":/cover/i.test(b.t)?"cover":"other",sel:b.sel,text:b.t.slice(0,60)}));
    const resumeCards=[...d.querySelectorAll("input[type=radio]")].filter(r=>/\\.(pdf|docx?)$/i.test(r.getAttribute("aria-label")||"")).map(r=>{const lab=r.id?d.querySelector('label[for="'+CSS.escape(r.id)+'"]'):null;let row=r.parentElement;for(let k=0;k<3&&row&&!vis(row);k++)row=row.parentElement;return {name:r.getAttribute("aria-label"),checked:r.checked,sel:mark((lab&&vis(lab))?lab:(row&&vis(row)?row:r))}});
    const next=pick(/^Submit application/i)||pick(/^Review/i)||pick(/^Next|Continue to next step/i)||pick(/^Continue/i)||null;
    const errors=[...d.querySelectorAll(".artdeco-inline-feedback--error, [role=alert], [id^=error-message]")].filter(vis).map(txt).filter(Boolean).slice(0,5);
    return JSON.stringify({modal:true,heading,prog,h3s:h3s.slice(0,4),fields,uploads,resumeCards,next:next?{t:next.t.slice(0,30),sel:next.sel,isSubmit:/^Submit/i.test(next.t)}:null,buttons:btns.map(b=>b.t).slice(0,10),errors,text:dtxt.slice(0,400)})})()`;
  const snap = async () => { const v = await ev(SNAP); if (typeof v !== 'string') { console.log('snap failed'); return { modal: false, failed: true }; } return JSON.parse(v); };
  const DLG = 'dialog[open], [role=dialog], [role=alertdialog], .jobs-easy-apply-modal';
  const IN_DLG = DLG.split(',').map(s => s.trim() + ' button').join(', ');
  let mk = 0;
  // Mark the first visible element in `scope` whose text matches `re` (a regex source string), then press it with the hands.
  async function clickByText(re, scope = 'button') {
    const k = 'clk' + (++mk);
    const ok = await ev(`(()=>{const vis=e=>e.getBoundingClientRect().height>0;const b=[...document.querySelectorAll(${JSON.stringify(scope)})].filter(vis).find(b=>${re}.test(((b.innerText||"")+" "+(b.getAttribute("aria-label")||"")).replace(/\\s+/g," ").trim()));if(!b)return false;b.setAttribute("data-map-idx","${k}");return true})()`);
    return ok ? click(`[data-map-idx=${k}]`) : false;
  }
  // Close the form without sending it: the X ("Dismiss"), then "Discard" on the "Save this application?" box. Never "Save".
  async function dismiss() {
    const open = () => ev(`!!document.querySelector(${JSON.stringify(DLG)})`);
    await clickByText('/^Dismiss|^Close|Dismiss$/i', IN_DLG); await h.pause(900, 1600);
    await clickByText('/^Discard/i', IN_DLG); await h.pause(900, 1600);
    if (await open()) { // the Review page's X is an icon button: Escape opens "Save this application?", then Discard
      await h.key('Escape'); await h.pause(1200, 1800);
      await clickByText('/^Discard/i', IN_DLG); await h.pause(800, 1400);
    }
    if (await open()) { console.log('  WARNING: form still open after dismiss'); return false; }
    return true;
  }
  // Press an Upload button with the hands, answer Chrome's file chooser with the laptop path, wait for the name to show.
  async function upload(sel, winPath, name) {
    const got = new Promise(r => { chooserWaiter = r; });
    if (!await click(sel)) { chooserWaiter = null; return false; }
    const p = await Promise.race([got, sleep(6000).then(() => null)]); chooserWaiter = null;
    if (!p) { console.log('  upload: no file chooser opened'); return false; }
    await h.send('DOM.setFileInputFiles', { files: [winPath], backendNodeId: p.backendNodeId });
    return waitFor(`(document.querySelector(${JSON.stringify(DLG)})||{innerText:""}).innerText.includes(${JSON.stringify(name)})`, 15000);
  }
  // Resume: the job's file already in LinkedIn's saved list -> select it; else upload it. Cover letter offered as an upload:
  // the job's PDF, required or optional. Returns a stop ({status, field}) or null.
  async function handleDocs(st, rec, F) {
    const up = kind => (st.uploads || []).find(u => u.kind === kind);
    if (!rec.resume && ((st.resumeCards || []).length || up('resume'))) {
      const card = (st.resumeCards || []).find(c => c.name === F.resumeName);
      if (card) { if (!card.checked) { await click(card.sel); await h.pause(400, 800); } rec.resume = `selected saved: ${F.resumeName}${F.resumePath ? '' : ' (book default: no job resume)'}`; }
      else if (F.resumePath && up('resume')) { if (!await upload(up('resume').sel, F.resumePath, F.resumeName)) return { status: 'NEEDS_INPUT', field: 'resume upload failed: ' + F.resumeName }; rec.resume = `uploaded: ${F.resumeName}`; }
      else return { status: 'NEEDS_INPUT', field: `resume: ${F.resumeName} is not in the saved list and there is no job file to upload` };
      const now = ((await snap()).resumeCards || []).find(c => c.name === F.resumeName);
      if (now && !now.checked) { await click(now.sel); await h.pause(400, 800); }
      if (!now || !((await snap()).resumeCards || []).find(c => c.name === F.resumeName && c.checked)) return { status: 'NEEDS_INPUT', field: 'resume not selected after ' + rec.resume };
      console.log(`  resume: ${rec.resume}`);
    }
    const other = (st.uploads || []).filter(u => u.kind === 'other');
    if (other.length) return { status: 'NEEDS_INPUT', field: 'upload: ' + other.map(u => u.text).join(', ') };
    if (!rec.letter && up('cover')) {
      if (!F.letterPath) return { status: 'NEEDS_LETTER', field: 'cover letter upload (no letter_file in picks, no apply/' + rec.jobId + '/ folder)' };
      if (!await upload(up('cover').sel, F.letterPath, F.letterName)) return { status: 'NEEDS_INPUT', field: 'cover letter upload failed: ' + F.letterName };
      rec.letter = `uploaded: ${F.letterName}`; console.log(`  cover letter: ${rec.letter}`);
    }
    return null;
  }
  // The Review page ticks "Follow <company>" by default. Untick it with a real press, every time, and log it.
  async function untickFollow(rec) {
    const k = 'flw' + (++mk);
    const f = await ev(`(()=>{const d=document.querySelector(${JSON.stringify(DLG)});if(!d)return null;const t=e=>(e?(e.innerText||e.textContent||""):"").replace(/\\s+/g," ").trim();
      for(const c of d.querySelectorAll("input[type=checkbox]")){const lab=c.id?d.querySelector('label[for="'+CSS.escape(c.id)+'"]'):null;let row=c.parentElement;for(let i=0;i<4&&row&&!t(row);i++)row=row.parentElement;const text=t(lab)||t(row);
        if(c.id==="follow-company-checkbox"||/^Follow\\b/i.test(text)){const tgt=(lab&&lab.getBoundingClientRect().width>0)?lab:c;tgt.setAttribute("data-map-idx","${k}");return {text:text.slice(0,90),checked:c.checked}}}return null})()`);
    if (!f) rec.follow = 'no Follow box on Review';
    else if (!f.checked) rec.follow = `already unticked: ${f.text}`;
    else {
      const ticked = () => ev(`(()=>{const e=document.querySelector("[data-map-idx=${k}]");const c=e&&(e.tagName==="INPUT"?e:(e.control||document.getElementById(e.htmlFor)));return !!(c&&c.checked)})()`);
      let presses = 0, still = true;
      while (still && presses < 2) { presses++; await click(`[data-map-idx=${k}]`); await h.pause(500, 900); still = await ticked(); } // the box is 24 px; a second press if the first missed
      rec.follow = (still ? 'FAILED to untick: ' : 'unticked: ') + f.text + (presses > 1 ? ` (${presses} presses)` : '');
    }
    console.log(`  Follow: ${rec.follow}`);
  }
  const waitFor = async (expr, ms = 8000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await ev(expr)) return true; await sleep(250); } return false; };
  // LinkedIn's 2026 job page has no <h1>; the title line and the description box are the stable handles (same as gather.cjs).
  const JOB_READY = '/ \\| LinkedIn$/.test(document.title) && !!document.querySelector("[id^=JobDetails_AboutTheJob]")';

  // ---------- job list ----------
  const IDS = arg('--ids', '');
  let ids = [];
  if (!IDS) {
  const listWheel = async () => { // wheel the results pane so more cards load
    const b = await ev(`(()=>{const e=document.querySelector('.scaffold-layout__list, .jobs-search-results-list');if(!e)return null;const r=e.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
    if (b) for (let s = 0; s < 3; s++) await wheel(rnd(600, 900), { x: b.x + rnd(-40, 40), y: b.y + rnd(-60, 60) });
  };
  const grab = async () => JSON.parse(await ev('JSON.stringify([...document.querySelectorAll("a[href*=\\"/jobs/view/\\"]")].map(a=>(a.href.match(/jobs\\/view\\/(\\d+)/)||[])[1]).filter(Boolean))'));
  for (let pg = 0; pg <= 3 && (pg === 0 || ids.length < JOBS * 3); pg++) {
    await h.send('Page.navigate', { url: `https://www.linkedin.com/jobs/search/?f_AL=true&keywords=${encodeURIComponent(KW)}&location=United%20States${pg ? '&start=' + pg * 25 : ''}` });
    await waitFor('document.querySelectorAll("a[href*=\\"/jobs/view/\\"]").length>3', 15000); await stopIfBlocked(); await h.pause(1500, 3000);
    await listWheel();
    ids = ids.concat(await grab());
  }
  // skip jobs already walked in earlier logs (unless --repeat)
  const done = new Set();
  if (!process.argv.includes('--repeat')) for (const f of fs.readdirSync(LOGDIR).filter(f => /^map-.*\.jsonl$/.test(f))) for (const line of fs.readFileSync(path.join(LOGDIR, f), 'utf8').split('\n')) { try { done.add(JSON.parse(line).jobId); } catch {} }
  ids = ids.filter((v, i, a) => a.indexOf(v) === i).filter(v => !done.has(v)).slice(0, JOBS * 4);
  }
  if (IDS) ids = IDS.split(',').map(x => x.trim()).filter(Boolean);
  console.log(`keywords="${KW}" jobs found: ${ids.length} · target runs: ${JOBS} · log: ${path.relative(ROOT, OUT)}`);

  let runs = 0; const t00 = Date.now();
  for (const jid of ids) {
    if (runs >= JOBS) break;
    const o = OVR[jid] || {};
    if (o.skip) { console.log(`  skip ${jid} by thinker: ${o.skip}`); fs.appendFileSync(OUT, JSON.stringify({ run: null, jobId: jid, status: 'SKIPPED_BY_THINKER', reason: o.skip, startedAt: new Date().toISOString() }) + '\n'); continue; }
    CUR_RULES = (o.rules || []).map(([re, v]) => [new RegExp(re, 'i'), v]);
    const F = jobFiles(jid, o);
    const rec = { run: runs + 1, jobId: jid, startedAt: new Date().toISOString(), screens: [], status: '', review: false, stuck: [], newForks: [], filled: 0, unanswered: 0, misses: [], overwrote: [], resume: null, letter: null, files: F.from, needs: null, error: null };
    const t0 = Date.now();
    let opened = false;
    // Per-job clock (10/27): JOB_CLOCK seconds for the whole walk, then the job is written as TIMED_OUT and the run moves on.
    let clockHit = false; const clock = new Promise(r => setTimeout(() => { clockHit = true; r('CLOCK'); }, JOB_CLOCK * 1000));
    const raced = async (pr) => { const v = await Promise.race([pr, clock]); if (v === 'CLOCK') throw new Error('job clock: ' + JOB_CLOCK + ' s ran out'); return v; };
    try { await raced((async () => {
      await showWindow();
      await h.send('Page.navigate', { url: `https://www.linkedin.com/jobs/view/${jid}/` });
      await waitFor(JOB_READY, 12000); await stopIfBlocked(rec); await h.pause(1200, 2600);
      const tp = String(await ev('document.title') || '').split(' | ');
      rec.title = (tp.length >= 3 ? tp.slice(0, -2).join(' | ') : tp[0] || '').trim().slice(0, 80); rec.company = (tp.length >= 3 ? tp[tp.length - 2] : '').trim().slice(0, 60);
      // read a little like a person: wheel down, then back up
      const down = rnd(250, 600); await wheel(down); await h.pause(800, 2000); await wheel(-down - 200); await h.pause(400, 900);
      const ea = await clickByText('/^Easy Apply/i', 'button, a, [role=button]');
      if (!ea) { rec.status = 'NO_EASY_APPLY_BUTTON'; rec.ms = Date.now() - t0; console.log(`  skip ${jid} (no Easy Apply button) ${rec.title}`); return; }
      if (!await waitFor(`!!document.querySelector(${JSON.stringify(DLG)})`, 8000)) { await stopIfBlocked(rec); rec.status = 'NO_DIALOG'; rec.ms = Date.now() - t0; console.log(`  skip ${jid} (no dialog) ${rec.title}`); return; }
      opened = true; runs++; await h.pause(900, 1800);
      let lastSig = '';
      for (let step = 0; step < 12; step++) {
        const ts = Date.now();
        await stopIfBlocked(rec);
        let st = await snap();
        if (!st.modal) { rec.status = 'MODAL_GONE'; break; }
        const sig = st.prog + '|' + st.heading + '|' + st.fields.map(f => f.type + ':' + f.label).join(';');
        if (sig === lastSig && step > 0) { rec.status = 'STUCK_SAME_SCREEN'; rec.stuck.push({ heading: st.heading, prog: st.prog, errors: st.errors, buttons: st.buttons, text: st.text, fields: st.fields.filter(f => !f.value).map(f => f.type + ':' + f.label) }); break; }
        lastSig = sig;
        const screen = { heading: st.heading, prog: st.prog, h3s: st.h3s, fields: [], ms: 0, next: st.next ? st.next.t : null, buttons: st.buttons, errors: st.errors, text: st.fields.length ? undefined : st.text };
        const stop = await handleDocs(st, rec, F);
        if (stop) { rec.status = stop.status; rec.needs = stop.field; console.log(`  ${stop.status}: ${stop.field}`); screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
        if (rec.resume || rec.letter) st = await snap();
        const needs = []; // fields the book and picks cannot fill: the job stops here, naming them
        for (const f of st.fields) {
          const fork = `${st.heading}|${f.type}|${f.label.toLowerCase()}`;
          const isNew = !seen.has(fork); if (isNew) { seen.add(fork); rec.newForks.push(fork); }
          const entry = { type: f.type, label: f.label, group: f.group || undefined, required: !!f.required, options: f.options, had: f.value || '', filledWith: null, source: null, new: isNew };
          if (f.type === 'checkbox' && /^Follow\b/i.test(f.label)) { entry.source = 'Follow box: unticked on Review'; screen.fields.push(entry); continue; }
          if (f.type === 'file') { entry.source = 'NEEDS_INPUT'; needs.push('file: ' + f.label); screen.fields.push(entry); continue; }
          if (isResumeCard(f)) { entry.source = 'resume card: ' + (rec.resume || 'not handled'); screen.fields.push(entry); continue; }
          if (/cover letter/i.test(f.label) && (f.type === 'textarea' || f.type === 'text')) { // the letter as a text box: typed key by key
            if (!F.letterText) { rec.status = 'NEEDS_LETTER'; rec.needs = 'cover letter text box: ' + f.label; break; }
            if (!same(f.value, F.letterText, 'text')) { const ok = await typeInto(f.sel, F.letterText); entry.filledWith = ok ? `cover letter (${F.letterText.length} chars)` : null; entry.source = ok ? 'job letter text' : 'FAILED:job letter text'; if (ok) { rec.filled++; rec.letter = `typed: ${F.letterText.length} chars`; console.log(`  cover letter: ${rec.letter}`); } }
            screen.fields.push(entry); continue;
          }
          if (!f.value && f.type !== 'file') {
            const a = answerFor(f.label, f.type, f.options);
            if (a && a.value === 'BLANK') { entry.filledWith = '(left blank on purpose)'; entry.source = a.source; rec.filled++; } // 10/27: a book rule can say BLANK (middle name)
            else if (a) {
              const ok = await fillField(f, a, entry);
              if (ok) { entry.filledWith = a.value; entry.source = a.source; rec.filled++; }
              else { entry.source = 'FAILED:' + a.source; rec.unanswered++; needs.push(`${f.label || f.type} ("${a.value}" could not be set${entry.note ? ': ' + entry.note : ''})`); }
            } else { entry.source = 'NO_ANSWER'; rec.unanswered++; needs.push(`${f.label || '(no label)'} [${f.type}${f.required ? ', required' : ', optional'}${f.options && f.options.length ? ': ' + f.options.slice(0, 6).join('/') : ''}]`); }
            await h.pause(300, 900);
          } else if (f.value && CHECKED_TYPES.has(f.type) && !isResumeCard(f)) {
            // LinkedIn pre-fills answers from old applications. Each one gets the same book check as an empty box;
            // when a book rule says something else, the hands overwrite it. A test default never overwrites.
            const a = answerFor(f.label, f.type, f.options);
            if (!a || /^default:/.test(a.source)) entry.source = 'kept saved (' + (a ? 'book has only a test default' : 'no book rule') + ')';
            else if (same(f.value, a.value, f.type)) entry.source = 'saved = book (' + a.source + ')';
            else if (await fillField(f, a, entry, false)) {
              entry.filledWith = a.value; entry.source = a.source; entry.overwrote = { old: f.value, new: a.value }; rec.filled++;
              rec.overwrote.push({ label: f.label, old: f.value, new: a.value, source: a.source });
              console.log(`  overwrote saved: ${f.label} ${f.value} → ${a.value}`);
              await h.pause(300, 900);
            } else entry.source = `kept saved (book says "${a.value}", could not set it: ${entry.note || 'unknown'})`;
          }
          screen.fields.push(entry);
        }
        if (needs.length && rec.status !== 'NEEDS_LETTER') { rec.status = 'NEEDS_INPUT'; rec.needs = needs.join(' | '); console.log(`  NEEDS_INPUT: ${rec.needs}`); screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
        if (rec.status === 'NEEDS_LETTER') { console.log(`  NEEDS_LETTER: ${rec.needs}`); screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
        st = await snap();
        const stillEmpty = st.fields.filter(f => f.required && !f.value && f.type !== 'file' && f.type !== 'checkbox');
        if (stillEmpty.length) { rec.status = 'STUCK_REQUIRED'; rec.stuck.push({ heading: st.heading, fields: stillEmpty.map(f => f.type + ':' + f.label + (f.options ? ' [' + f.options.join('/') + ']' : '')) }); screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
        if (!st.next) { rec.status = 'NO_NEXT_BUTTON'; rec.stuck.push({ heading: st.heading, buttons: st.buttons, text: st.text }); screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
        if (st.next.isSubmit) {
          await untickFollow(rec);
          if (!SUBMIT) { rec.status = 'READY_TO_SUBMIT'; rec.review = true; screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
          // Press Submit and move on. No watcher (George 10/27): LinkedIn's Applied list and its email are the receipt.
          await h.pause(700, 1500); await click(st.next.sel); await h.pause(2000, 3000);
          rec.status = 'SUBMITTED'; rec.submittedAt = new Date().toISOString();
          screen.ms = Date.now() - ts; rec.screens.push(screen); break;
        }
        await h.pause(700, 2200);
        await click(st.next.sel);
        await h.pause(1200, 2600);
        screen.ms = Date.now() - ts; rec.screens.push(screen);
      }
      if (!rec.status) rec.status = 'MAX_STEPS';
    })()); } catch (e) { rec.error = e.message.slice(0, 300); if (clockHit) rec.status = 'TIMED_OUT'; else if (!rec.status) rec.status = 'ERROR'; }
    rec.ms = Date.now() - t0;
    if (opened) { const closed = await Promise.race([dismiss().catch(() => false), sleep(15000).then(() => false)]); if (!closed) rec.error = (rec.error ? rec.error + ' · ' : '') + 'form still open after dismiss'; }
    rec.msTotal = Date.now() - t0;
    if (/^NO_(EASY_APPLY_BUTTON|DIALOG)$/.test(rec.status)) { fs.appendFileSync(OUT, JSON.stringify(rec) + '\n'); continue; }
    for (const s of rec.screens) for (const f of s.fields) if (!f.had && f.type !== 'file' && isMiss(f.source)) rec.misses.push({ screen: s.heading, label: f.label, group: f.group, type: f.type, options: f.options, required: f.required, source: f.source, filledWith: f.filledWith });
    fs.appendFileSync(OUT, JSON.stringify(rec) + '\n');
    fs.writeFileSync(SEENF, JSON.stringify([...seen], null, 0));
    console.log(`run ${rec.run}/${JOBS} · ${(rec.ms / 1000).toFixed(1)} s · ${rec.status}${rec.review ? ' (Review)' : ''} · screens ${rec.screens.length} · filled ${rec.filled} · misses ${rec.misses.length} · overwrote ${rec.overwrote.length}${rec.needs ? ' · needs: ' + rec.needs.slice(0, 70) : ''} · new forks ${rec.newForks.length}${rec.error ? ' · ERROR ' + rec.error.slice(0, 80) : ''} · ${rec.title} @ ${rec.company}`);
    if (runs < JOBS && jid !== ids[ids.length - 1]) { const gap = rnd(15000, 45000); console.log(`  waiting ${(gap / 1000).toFixed(0)} s`); await sleep(gap); }
  }
  console.log(`done: ${runs} runs in ${((Date.now() - t00) / 60000).toFixed(1)} min · forks known: ${seen.size} · log: ${path.relative(ROOT, OUT)}`);
  if (SUBMIT) { // the receipt is LinkedIn's own Applied list, not a 3-second peek at the pop-up (George 10/27)
    try { const r = await require('./applied_check.cjs').check(h, ids.filter(j => !(OVR[j] || {}).skip)); fs.appendFileSync(OUT, JSON.stringify({ run: null, appliedCheck: r, at: new Date().toISOString() }) + '\n'); }
    catch (e) { console.log('applied check failed:', e.message); }
  }
  h.close(); process.exit(0);
})().catch(e => { console.log('ERROR', e && e.message); process.exit(1); });
