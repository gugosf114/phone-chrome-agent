// map_easy_apply.cjs — walk LinkedIn Easy Apply on N jobs, fill from the answer book, STOP one click before Submit,
// and log every screen, field, fork, and the time each run took. Never submits. Dismisses + discards each form.
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

const fs = require('fs'); const path = require('path');
const human = require('./human.cjs');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const rnd = (a, b) => a + Math.random() * (b - a);
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : d; };
const JOBS = parseInt(arg('--jobs', '10'), 10);
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
  for (const [re, v] of CUR_RULES) if (re.test(l)) return { value: v, source: 'job-rule:' + re.source.slice(0, 30) };
  for (const [re, v] of RULES) if (re.test(l)) return { value: v, source: 'rule:' + re.source.slice(0, 30) };
  if (type === 'number') return { value: BOOK.defaults.number, source: 'default:number' };
  if (type === 'radio' && (options || []).some(o => /\.(pdf|docx?)$/i.test(o))) return { value: BOOK.facts.resume_file || options[0], source: 'fact:resume_file' };
  if (type === 'radio' || type === 'select') {
    const opts = (options || []).map(o => o.toLowerCase());
    const dec = opts.findIndex(o => /do not want to answer|prefer not|don.?t wish|decline to/.test(o)); if (dec > -1) return { value: options[dec], source: 'default:decline-option' };
    if (opts.some(o => /^yes$/.test(o))) return { value: BOOK.defaults.yesNo, source: 'default:yesNo' };
    return null;
  }
  if (type === 'text' || type === 'textarea') return { value: BOOK.defaults.text, source: 'default:text' };
  return null;
}
const isMiss = src => !src || /^(NO_ANSWER|FAILED|default:(number|text|yesNo))/.test(src);

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
  const h = await human.attach(tab, { log: m => process.stderr.write('  [human] ' + m + '\n') });
  const ev = async x => { try { return await h.evaluate(x); } catch (e) { console.log('PAGE EXC:', e.message.slice(0, 200), 'in:', x.slice(0, 90).replace(/\s+/g, ' ')); return undefined; } };
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
      return o?{want:all.indexOf(o),text:o.text.trim()}:{miss:true}})()`);
    if (!t) return 'no el'; if (t.miss) return 'no option for ' + wanted;
    const at = () => ev(`document.querySelector(${JSON.stringify(f.sel)}).selectedIndex`);
    const isOpen = () => ev(`(()=>{try{return document.querySelector(${JSON.stringify(f.sel)}).matches(":open")}catch(e){return false}})()`);
    const walk = async () => { const n = t.want - Math.max(0, await at()); for (let i = 0; i < Math.abs(n); i++) await h.key(n > 0 ? 'ArrowDown' : 'ArrowUp'); };
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
    d.querySelectorAll("input[type=checkbox]").forEach(c=>{const lab=c.id?d.querySelector('label[for="'+CSS.escape(c.id)+'"]'):null;if(!vis(c)&&!(lab&&vis(lab)))return;const fs=c.closest("fieldset");
      fields.push({type:"checkbox",label:txt(lab)||labelOf(c),group:fs?txt(fs.querySelector("legend")).slice(0,160):"",required:req(c),value:c.checked?"checked":"",sel:mark(lab||c)})});
    d.querySelectorAll("input:not([type]),input[type=text],input[type=number],input[type=email],input[type=tel],input[type=url],textarea").forEach(i=>{if(!vis(i)||i.readOnly||i.disabled)return;
      const type=i.tagName==="TEXTAREA"?"textarea":(i.type==="number"?"number":(i.getAttribute("role")==="combobox"||i.getAttribute("aria-autocomplete")?"typeahead":"text"));
      fields.push({type,label:labelOf(i),required:req(i),value:(i.value||"").trim(),sel:mark(i)})});
    d.querySelectorAll("input[type=file]").forEach(f=>{fields.push({type:"file",label:labelOf(f)||"file upload",required:req(f),value:"",sel:mark(f)})});
    const btns=[...d.querySelectorAll("button")].filter(vis).map(b=>({t:((b.innerText||"")+" "+(b.getAttribute("aria-label")||"")).replace(/\\s+/g," ").trim(),sel:mark(b)}));
    const pick=re=>btns.find(b=>re.test(b.t));
    const next=pick(/^Submit application/i)||pick(/^Review/i)||pick(/^Next|Continue to next step/i)||pick(/^Continue/i)||null;
    const errors=[...d.querySelectorAll(".artdeco-inline-feedback--error, [role=alert], [id^=error-message]")].filter(vis).map(txt).filter(Boolean).slice(0,5);
    return JSON.stringify({modal:true,heading,prog,h3s:h3s.slice(0,4),fields,next:next?{t:next.t.slice(0,30),sel:next.sel,isSubmit:/^Submit/i.test(next.t)}:null,buttons:btns.map(b=>b.t).slice(0,10),errors,text:dtxt.slice(0,400)})})()`;
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
    const rec = { run: runs + 1, jobId: jid, startedAt: new Date().toISOString(), screens: [], status: '', review: false, stuck: [], newForks: [], filled: 0, unanswered: 0, misses: [], error: null };
    const t0 = Date.now();
    let opened = false;
    try {
      await h.send('Page.navigate', { url: `https://www.linkedin.com/jobs/view/${jid}/` });
      await waitFor(JOB_READY, 12000); await stopIfBlocked(rec); await h.pause(1200, 2600);
      const tp = String(await ev('document.title') || '').split(' | ');
      rec.title = (tp.length >= 3 ? tp.slice(0, -2).join(' | ') : tp[0] || '').trim().slice(0, 80); rec.company = (tp.length >= 3 ? tp[tp.length - 2] : '').trim().slice(0, 60);
      // read a little like a person: wheel down, then back up
      const down = rnd(250, 600); await wheel(down); await h.pause(800, 2000); await wheel(-down - 200); await h.pause(400, 900);
      const ea = await clickByText('/^Easy Apply/i', 'button, a, [role=button]');
      if (!ea) { rec.status = 'NO_EASY_APPLY_BUTTON'; rec.ms = Date.now() - t0; console.log(`  skip ${jid} (no Easy Apply button) ${rec.title}`); fs.appendFileSync(OUT, JSON.stringify(rec) + '\n'); continue; }
      if (!await waitFor(`!!document.querySelector(${JSON.stringify(DLG)})`, 8000)) { await stopIfBlocked(rec); rec.status = 'NO_DIALOG'; rec.ms = Date.now() - t0; console.log(`  skip ${jid} (no dialog) ${rec.title}`); fs.appendFileSync(OUT, JSON.stringify(rec) + '\n'); continue; }
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
        for (const f of st.fields) {
          const fork = `${st.heading}|${f.type}|${f.label.toLowerCase()}`;
          const isNew = !seen.has(fork); if (isNew) { seen.add(fork); rec.newForks.push(fork); }
          const entry = { type: f.type, label: f.label, group: f.group || undefined, required: !!f.required, options: f.options, had: f.value || '', filledWith: null, source: null, new: isNew };
          if (!f.value && f.type !== 'file') {
            const a = answerFor(f.label, f.type, f.options);
            if (a) {
              let ok = false;
              if (f.type === 'select') { const r = String(await pickSelect(f, a.value)); ok = /^ok/.test(r); if (/setter/.test(r)) entry.note = 'setter: ' + f.label; }
              else if (f.type === 'radio') { let want = String(a.value).toLowerCase(); let j = (f.options || []).findIndex(o => o.toLowerCase() === want); if (j < 0) j = (f.options || []).findIndex(o => o.toLowerCase().startsWith(want)); if (j < 0 && /don.?t wish|prefer not|decline/i.test(want)) j = (f.options || []).findIndex(o => /prefer not|don.?t wish|decline|not to (answer|specify|say|disclose)/i.test(o));
                if (j < 0 && (f.options || []).some(o => /^yes$/i.test(o)) && (f.options || []).some(o => /^no$/i.test(o)) && !/\.(pdf|docx?)$/i.test(want)) { want = String(BOOK.defaults.yesNo).toLowerCase(); j = (f.options || []).findIndex(o => o.toLowerCase() === want); a.source = 'default:yesNo (rule value "' + a.value + '" not an option)'; a.value = BOOK.defaults.yesNo; } if (j < 0 && (f.options || []).some(o => /\.(pdf|docx?)$/i.test(o))) j = Math.max(0, (f.options || []).findIndex(o => o.includes(BOOK.facts.resume_file || '\u0000')));
                if (j > -1) {
                  const verify = async () => { const s2 = await snap(); const g = (s2.fields || []).find(x => x.type === 'radio' && x.label === f.label); return !!(g && g.value); };
                  await click(f.optsel[j]); await h.pause(300, 600);
                  let chk = await verify();
                  if (!chk) { await click(f.radiosel[j]); await h.pause(300, 500); chk = await verify(); entry.note = 'second press, on the radio itself'; }
                  ok = chk;
                } }
              else if (f.type === 'checkbox') { if (f.required || /agree|consent|acknowledge|terms/i.test(f.label)) ok = await click(f.sel); else { entry.note = 'optional checkbox left alone'; a.source = 'left:' + a.source; } }
              else if (f.type === 'text' || f.type === 'number' || f.type === 'textarea' || f.type === 'typeahead') { ok = await typeInto(f.sel, a.value); if (ok && f.type === 'typeahead') { await h.pause(900, 1500); await h.key('ArrowDown'); await h.key('Enter'); } }
              if (ok) { entry.filledWith = a.value; entry.source = a.source; rec.filled++; }
              else if (/^left:/.test(a.source)) entry.source = a.source;
              else { entry.source = 'FAILED:' + a.source; rec.unanswered++; }
            } else { entry.source = 'NO_ANSWER'; rec.unanswered++; }
            await h.pause(300, 900);
          }
          screen.fields.push(entry);
        }
        st = await snap();
        const stillEmpty = st.fields.filter(f => f.required && !f.value && f.type !== 'file' && f.type !== 'checkbox');
        if (stillEmpty.length) { rec.status = 'STUCK_REQUIRED'; rec.stuck.push({ heading: st.heading, fields: stillEmpty.map(f => f.type + ':' + f.label + (f.options ? ' [' + f.options.join('/') + ']' : '')) }); screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
        if (!st.next) { rec.status = 'NO_NEXT_BUTTON'; rec.stuck.push({ heading: st.heading, buttons: st.buttons, text: st.text }); screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
        if (st.next.isSubmit) {
          if (!SUBMIT) { rec.status = 'READY_TO_SUBMIT'; rec.review = true; screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
          await h.pause(700, 1500); await click(st.next.sel); await h.pause(2500, 4000);
          const after = await ev('(()=>{const d=document.querySelector("dialog[open], [role=dialog]");return (d?d.innerText:document.body.innerText).replace(/\\s+/g," ").slice(0,200)})()');
          rec.receipt = after; rec.status = /application (was )?sent|applied|submitted/i.test(after) ? 'SUBMITTED' : 'SUBMIT_CLICKED_NO_RECEIPT';
          screen.ms = Date.now() - ts; rec.screens.push(screen); break;
        }
        await h.pause(700, 2200);
        await click(st.next.sel);
        await h.pause(1200, 2600);
        screen.ms = Date.now() - ts; rec.screens.push(screen);
      }
      if (!rec.status) rec.status = 'MAX_STEPS';
    } catch (e) { rec.error = e.message.slice(0, 300); if (!rec.status) rec.status = 'ERROR'; }
    rec.ms = Date.now() - t0;
    if (opened && !await dismiss()) rec.error = (rec.error ? rec.error + ' · ' : '') + 'form still open after dismiss';
    rec.msTotal = Date.now() - t0;
    for (const s of rec.screens) for (const f of s.fields) if (!f.had && f.type !== 'file' && isMiss(f.source)) rec.misses.push({ screen: s.heading, label: f.label, group: f.group, type: f.type, options: f.options, required: f.required, source: f.source, filledWith: f.filledWith });
    fs.appendFileSync(OUT, JSON.stringify(rec) + '\n');
    fs.writeFileSync(SEENF, JSON.stringify([...seen], null, 0));
    console.log(`run ${rec.run}/${JOBS} · ${(rec.ms / 1000).toFixed(1)} s · ${rec.status}${rec.review ? ' (Review)' : ''} · screens ${rec.screens.length} · filled ${rec.filled} · misses ${rec.misses.length} · new forks ${rec.newForks.length}${rec.error ? ' · ERROR ' + rec.error.slice(0, 80) : ''} · ${rec.title} @ ${rec.company}`);
    if (runs < JOBS && jid !== ids[ids.length - 1]) { const gap = rnd(15000, 45000); console.log(`  waiting ${(gap / 1000).toFixed(0)} s`); await sleep(gap); }
  }
  console.log(`done: ${runs} runs in ${((Date.now() - t00) / 60000).toFixed(1)} min · forks known: ${seen.size} · log: ${path.relative(ROOT, OUT)}`);
  h.close(); process.exit(0);
})().catch(e => { console.log('ERROR', e && e.message); process.exit(1); });
