// map_easy_apply.cjs — walk LinkedIn Easy Apply on N jobs, fill from the answer book, STOP one click before Submit,
// and log every screen, field, fork, and the time each run took. Never submits. Dismisses + discards each form.
//
//   CDP_PORT=19222 node scripts/map_easy_apply.cjs --jobs 10 --keywords "legal operations"
//
// Human rhythm lives HERE, below the model: real mouse moves + clicks, key-by-key typing with jitter, random pauses.
// Output: logs/easy_apply_map/map-<stamp>.jsonl (one line per job) + logs/easy_apply_map/seen-forks.json (grows across runs).
// A "fork" = screen heading + field type + field label. A run's "new forks" = ones no earlier run has seen.

const fs = require('fs'); const path = require('path');
const WebSocket = globalThis.WebSocket || require('ws');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const rnd = (a, b) => a + Math.random() * (b - a);
const pause = (a = 800, b = 3000) => sleep(rnd(a, b));
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
const stamp = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 16);
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

(async () => {
  // ---------- connect ----------
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  const tab = list.find(o => o.type === 'page' && o.url.includes('linkedin.com')) || list.find(o => o.type === 'page');
  if (!tab) { console.log('no tab on port', PORT); process.exit(2); }
  const ws = new WebSocket(tab.webSocketDebuggerUrl); await new Promise(r => ws.onopen = r);
  let id = 0; const pend = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m); delete pend[m.id]; } };
  const send = (m, p = {}) => new Promise(res => { const i = ++id; pend[i] = res; ws.send(JSON.stringify({ id: i, method: m, params: p })); });
  const ev = async x => { const r = await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true, userGesture: true }); if (r.result && r.result.exceptionDetails) { const ex = r.result.exceptionDetails; console.log('PAGE EXC:', (ex.exception && ex.exception.description || ex.text || '').slice(0, 200), '@line', ex.lineNumber, 'col', ex.columnNumber, 'in:', x.slice(0, 90).replace(/\s+/g, ' ')); return undefined; } return r.result && r.result.result ? r.result.result.value : undefined; };
  await send('Page.enable'); await send('Runtime.enable');

  // ---------- human hands (below the model) ----------
  async function mouseTo(x, y) {
    const steps = 3 + Math.floor(Math.random() * 3);
    const cur = await ev('JSON.stringify(window.__mapMouse||[200,200])'); let [cx, cy] = JSON.parse(cur);
    for (let i = 1; i <= steps; i++) {
      const nx = cx + (x - cx) * i / steps + rnd(-2, 2), ny = cy + (y - cy) * i / steps + rnd(-2, 2);
      await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: nx, y: ny }); await sleep(rnd(15, 45));
    }
    await ev(`window.__mapMouse=[${x},${y}]`);
  }
  async function humanClick(sel) {
    const rect = await ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return null;e.scrollIntoView({block:"center"});const r=e.getBoundingClientRect();return JSON.stringify({x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height})})()`);
    if (!rect) return false;
    const r = JSON.parse(rect); if (r.w === 0 || r.h === 0) return false;
    await sleep(rnd(150, 400));
    const x = r.x + rnd(-r.w * 0.2, r.w * 0.2), y = r.y + rnd(-r.h * 0.2, r.h * 0.2);
    await mouseTo(x, y); await sleep(rnd(60, 160));
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
    await sleep(rnd(50, 120));
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
    return true;
  }
  async function humanType(sel, text) {
    await humanClick(sel);
    await ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(e){e.focus();if(e.select)e.select();}})()`);
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'a', code: 'KeyA', modifiers: 2 }); // ctrl+a
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'a', code: 'KeyA', modifiers: 2 });
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Backspace', code: 'Backspace' });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Backspace', code: 'Backspace' });
    for (const ch of String(text)) { await send('Input.insertText', { text: ch }); await sleep(rnd(40, 130)); }
    await sleep(rnd(200, 500));
    await ev(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(e){e.dispatchEvent(new Event("change",{bubbles:true}));e.blur();}})()`);
  }
  async function setSelect(sel, wanted) {
    return await ev(`(()=>{const s=document.querySelector(${JSON.stringify(sel)});if(!s)return "no el";const w=${JSON.stringify(String(wanted).toLowerCase())};
      const opts=[...s.options].filter(o=>!/select an option|^select$|^--/i.test(o.text.trim()));
      let o=opts.find(o=>o.text.trim().toLowerCase()===w)||opts.find(o=>o.text.toLowerCase().includes(w))||opts.find(o=>o.value.toLowerCase()===w);
      if(!o&&/^yes$/i.test(w))o=opts.find(o=>/^yes\\b/i.test(o.text));if(!o&&/^no$/i.test(w))o=opts.find(o=>/^no\\b/i.test(o.text));
      if(!o)return "no option for "+w;const set=Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,"value").set;set.call(s,o.value);
      s.dispatchEvent(new Event("input",{bubbles:true}));s.dispatchEvent(new Event("change",{bubbles:true}));return "ok:"+o.text.trim()})()`);
  }

  // ---------- screen reader ----------
  const SNAP = `(()=>{const d=document.querySelector("dialog[open], [role=dialog], .jobs-easy-apply-modal");if(!d)return JSON.stringify({modal:false});
    const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0};
    const txt=e=>(e?(e.innerText||e.textContent||""):"").replace(/\\s+/g," ").trim();
    const dtxt=txt(d);const prog=(dtxt.match(/(\\d+)\\/(\\d+) pages?/i)||[])[0]||"";const h3s=[...d.querySelectorAll("h3")].map(txt).filter(Boolean);const own=e=>[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join(" ").replace(/\\s+/g," ").trim();const els=[...d.querySelectorAll("*")];const pi=els.findIndex(e=>prog&&own(e)===prog);let title="";if(pi>-1){for(let i=pi+1;i<els.length;i++){const t=own(els[i]);if(t&&t.length>=3&&t.length<=40&&!/^Apply to/i.test(t)){title=t;break}}}const heading=(title||h3s[0]||(prog?txt(d.querySelector("h2")):"Single page")||"").slice(0,60);
    const labelOf=el=>{let l="";if(el.id){const f=d.querySelector('label[for="'+CSS.escape(el.id)+'"]');if(f)l=txt(f)}
      if(!l)l=el.getAttribute("aria-label")||"";if(!l){const fs=el.closest("fieldset");if(fs)l=txt(fs.querySelector("legend"))}
      if(!l){const g=el.closest("[data-test-form-element], .fb-dash-form-element, .jobs-easy-apply-form-element, .artdeco-text-input--container");if(g){const lab=g.querySelector("label, legend, span[aria-hidden]");l=txt(lab)}}
      if(!l)l=el.placeholder||el.name||"";return l.replace(/[*\\u00a0\\s]+$/,"").slice(0,120)};
    const req=el=>el.required||el.getAttribute("aria-required")==="true"||/required/i.test((el.closest("fieldset,div")||{}).textContent||"")&&false;
    const fields=[];let n=0;const mark=el=>{const k="mf"+(n++);el.setAttribute("data-map-idx",k);return "[data-map-idx="+k+"]"};
    d.querySelectorAll("select").forEach(s=>{if(!vis(s))return;const cur=s.options[s.selectedIndex]?.text.trim()||"";const empty=!s.value||/select an option|^select$|^--/i.test(cur);
      fields.push({type:"select",label:labelOf(s),required:req(s),options:[...s.options].map(o=>o.text.trim()).filter(t=>!/select an option/i.test(t)).slice(0,12),value:empty?"":cur,sel:mark(s)})});
    const groups={};d.querySelectorAll("input[type=radio]").forEach(r=>{(groups[r.name]=groups[r.name]||[]).push(r)});Object.entries(groups).forEach(([name,rs])=>{const fs=rs[0].closest("fieldset")||rs[0].closest("[role=radiogroup]");if(!(rs.some(vis)||(fs&&vis(fs))))return;const label=txt(fs?.querySelector("legend"))||(rs[0].getAttribute("aria-label")||"").replace(/[*\\u00a0\\s]+$/,"")||labelOf(rs[0])||name;const opts=rs.map(r=>{const lab=r.id?d.querySelector('label[for="'+CSS.escape(r.id)+'"]'):null;const row=r.parentElement&&r.parentElement.parentElement;const t=txt(lab)||(row?txt(row):"")||r.value;const target=(lab&&vis(lab))?lab:((row&&vis(row))?row:r);return {text:t.slice(0,80),sel:mark(target)}});const chosen=rs.find(r=>r.checked);fields.push({type:"radio",label:label.slice(0,160),required:true,options:opts.map(o=>o.text),optsel:opts.map(o=>o.sel),radiosel:rs.map(mark),value:chosen?((opts[rs.indexOf(chosen)]||{}).text||"chosen"):""})});
    d.querySelectorAll("input[type=checkbox]").forEach(c=>{if(!vis(c))return;const lab=c.id?d.querySelector('label[for="'+CSS.escape(c.id)+'"]'):null;
      fields.push({type:"checkbox",label:txt(lab)||labelOf(c),required:req(c),value:c.checked?"checked":"",sel:mark(lab||c)})});
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
  const clickText = re => ev(`(()=>{const vis=e=>e.getBoundingClientRect().height>0;const b=[...document.querySelectorAll("button")].filter(vis).find(b=>${re}.test(((b.innerText||"")+" "+(b.getAttribute("aria-label")||"")).trim()));if(!b)return false;b.setAttribute("data-map-idx","clk");return true})()`);
  async function clickByText(re) { if (await clickText(re)) return await humanClick('[data-map-idx=clk]'); return false; }
  async function dismiss() {
    await clickByText('/^Dismiss|^Close|Dismiss$/i'); await pause(900, 1600);
    await clickByText('/^Discard/i'); await pause(900, 1600);
    await ev('(()=>{const d=document.querySelector("dialog[open], [role=dialog], .jobs-easy-apply-modal");if(d){const b=[...d.querySelectorAll("button")].find(b=>/Dismiss|Discard|Close/i.test(b.innerText+(b.getAttribute("aria-label")||"")));if(b)b.click();}})()');
    await ev('(()=>{const d=document.querySelector("dialog[open], [role=dialog], .jobs-easy-apply-modal");if(d){const b=[...d.querySelectorAll("button")].find(b=>/^Discard/i.test(b.innerText+(b.getAttribute("aria-label")||"")));if(b)b.click();}})()');
    await pause(500, 1000);
  }
  const waitFor = async (expr, ms = 8000) => { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (await ev(expr)) return true; await sleep(250); } return false; };

  // ---------- job list ----------
  const IDS = arg('--ids', ''); const SUBMIT = process.argv.includes('--submit');
  let ids = [];
  if (!IDS) {
  await send('Page.navigate', { url: `https://www.linkedin.com/jobs/search/?f_AL=true&keywords=${encodeURIComponent(KW)}&location=United%20States` });
  await waitFor('document.querySelectorAll("a[href*=\\"/jobs/view/\\"]").length>3', 15000); await pause(1500, 3000);
  for (let s = 0; s < 3; s++) { await ev('document.querySelector(".jobs-search-results-list, .scaffold-layout__list")?.scrollBy(0,900)'); await pause(600, 1200); }
  const grab = async () => JSON.parse(await ev('JSON.stringify([...document.querySelectorAll("a[href*=\\"/jobs/view/\\"]")].map(a=>(a.href.match(/jobs\\/view\\/(\\d+)/)||[])[1]).filter(Boolean))'));
  ids = await grab();
  for (let pg = 1; pg <= 3 && ids.length < JOBS * 3; pg++) {
    await send('Page.navigate', { url: `https://www.linkedin.com/jobs/search/?f_AL=true&keywords=${encodeURIComponent(KW)}&location=United%20States&start=${pg * 25}` });
    await waitFor('document.querySelectorAll("a[href*=\\"/jobs/view/\\"]").length>3', 15000); await pause(1500, 3000);
    for (let s = 0; s < 3; s++) { await ev('document.querySelector(".jobs-search-results-list, .scaffold-layout__list")?.scrollBy(0,900)'); await pause(600, 1200); }
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
    const rec = { run: runs + 1, jobId: jid, startedAt: new Date().toISOString(), screens: [], status: '', stuck: [], newForks: [], filled: 0, unanswered: 0 };
    const t0 = Date.now();
    await send('Page.navigate', { url: `https://www.linkedin.com/jobs/view/${jid}/` });
    await waitFor('!!document.querySelector("h1")', 10000); await pause(1200, 2600);
    rec.title = await ev('(document.querySelector("h1")||{}).innerText||document.title');
    rec.company = await ev('(document.querySelector(".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name, a[href*=\\"/company/\\"]")||{}).innerText||""');
    rec.title = (rec.title || '').trim().slice(0, 80); rec.company = (rec.company || '').trim().slice(0, 60);
    // scroll a little like a reader
    await ev('window.scrollBy(0,' + Math.floor(rnd(200, 600)) + ')'); await pause(800, 2000); await ev('window.scrollTo(0,0)'); await pause(400, 900);
    const ea = await clickByText('/^Easy Apply/i');
    if (!ea) { console.log(`  skip ${jid} (no Easy Apply button) ${rec.title}`); continue; }
    if (!await waitFor('!!document.querySelector("dialog[open], [role=dialog], .jobs-easy-apply-modal")', 8000)) { console.log(`  skip ${jid} (no dialog) ${rec.title}`); continue; }
    runs++; await pause(900, 1800);
    let lastSig = '';
    for (let step = 0; step < 12; step++) {
      const ts = Date.now();
      let st = await snap();
      if (!st.modal) { rec.status = 'MODAL_GONE'; break; }
      const sig = st.prog + '|' + st.heading + '|' + st.fields.map(f => f.type + ':' + f.label).join(';');
      if (sig === lastSig && step > 0) { rec.status = 'STUCK_SAME_SCREEN'; rec.stuck.push({ heading: st.heading, prog: st.prog, errors: st.errors, buttons: st.buttons, text: st.text, fields: st.fields.filter(f => !f.value).map(f => f.type + ':' + f.label) }); break; }
      lastSig = sig;
      const screen = { heading: st.heading, prog: st.prog, h3s: st.h3s, fields: [], ms: 0, next: st.next ? st.next.t : null, buttons: st.buttons, errors: st.errors, text: st.fields.length ? undefined : st.text };
      for (const f of st.fields) {
        const fork = `${st.heading}|${f.type}|${f.label.toLowerCase()}`;
        const isNew = !seen.has(fork); if (isNew) { seen.add(fork); rec.newForks.push(fork); }
        const entry = { type: f.type, label: f.label, required: !!f.required, options: f.options, had: f.value || '', filledWith: null, source: null, new: isNew };
        if (!f.value && f.type !== 'file') {
          const a = answerFor(f.label, f.type, f.options);
          if (a) {
            let ok = false;
            if (f.type === 'select') ok = /^ok/.test(String(await setSelect(f.sel, a.value)));
            else if (f.type === 'radio') { let want = String(a.value).toLowerCase(); let j = (f.options || []).findIndex(o => o.toLowerCase() === want); if (j < 0) j = (f.options || []).findIndex(o => o.toLowerCase().startsWith(want)); if (j < 0 && /don.?t wish|prefer not|decline/i.test(want)) j = (f.options || []).findIndex(o => /prefer not|don.?t wish|decline|not to (answer|specify|say|disclose)/i.test(o));
              if (j < 0 && (f.options || []).some(o => /^yes$/i.test(o)) && (f.options || []).some(o => /^no$/i.test(o)) && !/\.(pdf|docx?)$/i.test(want)) { want = String(BOOK.defaults.yesNo).toLowerCase(); j = (f.options || []).findIndex(o => o.toLowerCase() === want); a.source = 'default:yesNo (rule value "' + a.value + '" not an option)'; a.value = BOOK.defaults.yesNo; } if (j < 0 && (f.options || []).some(o => /\.(pdf|docx?)$/i.test(o))) j = Math.max(0, (f.options || []).findIndex(o => o.includes(BOOK.facts.resume_file || '\u0000'))); if (j > -1) { await humanClick(f.optsel[j]); await pause(300, 600); const verify = async () => { const s2 = await snap(); const g = (s2.fields || []).find(x => x.type === 'radio' && x.label === f.label); return !!(g && g.value); }; let chk = await verify(); if (!chk) { await ev(`(()=>{const r=document.querySelector(${JSON.stringify(f.radiosel[j])});if(r){r.click();r.dispatchEvent(new Event('change',{bubbles:true}))}})()`); await pause(300, 500); chk = await verify(); entry.note = 'js-click fallback'; } ok = chk; } }
            else if (f.type === 'checkbox') { if (f.required || /agree|consent|acknowledge|terms/i.test(f.label)) ok = await humanClick(f.sel); else ok = true; }
            else if (f.type === 'text' || f.type === 'number' || f.type === 'textarea' || f.type === 'typeahead') { await humanType(f.sel, a.value); ok = true; if (f.type === 'typeahead') { await pause(900, 1500); await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'ArrowDown', code: 'ArrowDown' }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'ArrowDown', code: 'ArrowDown' }); await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter' }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter' }); } }
            if (ok) { entry.filledWith = a.value; entry.source = a.source; rec.filled++; }
            else { entry.source = 'FAILED:' + a.source; rec.unanswered++; }
          } else { entry.source = 'NO_ANSWER'; rec.unanswered++; }
          await pause(300, 900);
        }
        screen.fields.push(entry);
      }
      st = await snap();
      const stillEmpty = st.fields.filter(f => f.required && !f.value && f.type !== 'file' && f.type !== 'checkbox');
      if (stillEmpty.length) { rec.status = 'STUCK_REQUIRED'; rec.stuck.push({ heading: st.heading, fields: stillEmpty.map(f => f.type + ':' + f.label + (f.options ? ' [' + f.options.join('/') + ']' : '')) }); screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
      if (!st.next) { rec.status = 'NO_NEXT_BUTTON'; rec.stuck.push({ heading: st.heading, buttons: st.buttons, text: st.text }); screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
      if (st.next.isSubmit) {
        if (!SUBMIT) { rec.status = 'READY_TO_SUBMIT'; screen.ms = Date.now() - ts; rec.screens.push(screen); break; }
        await pause(700, 1500); await humanClick(st.next.sel); await pause(2500, 4000);
        const after = await ev('(()=>{const d=document.querySelector("dialog[open], [role=dialog]");return (d?d.innerText:document.body.innerText).replace(/\\s+/g," ").slice(0,200)})()');
        rec.receipt = after; rec.status = /application (was )?sent|applied|submitted/i.test(after) ? 'SUBMITTED' : 'SUBMIT_CLICKED_NO_RECEIPT';
        screen.ms = Date.now() - ts; rec.screens.push(screen); break;
      }
      await pause(700, 2200);
      await humanClick(st.next.sel);
      await pause(1200, 2600);
      screen.ms = Date.now() - ts; rec.screens.push(screen);
    }
    if (!rec.status) rec.status = 'MAX_STEPS';
    rec.ms = Date.now() - t0;
    await dismiss();
    fs.appendFileSync(OUT, JSON.stringify(rec) + '\n');
    fs.writeFileSync(SEENF, JSON.stringify([...seen], null, 0));
    console.log(`run ${rec.run}/${JOBS} · ${(rec.ms / 1000).toFixed(1)} s · ${rec.status} · screens ${rec.screens.length} · filled ${rec.filled} · unanswered ${rec.unanswered} · new forks ${rec.newForks.length} · ${rec.title} @ ${rec.company}`);
    if (runs < JOBS) { const gap = rnd(15000, 45000); console.log(`  waiting ${(gap / 1000).toFixed(0)} s`); await sleep(gap); }
  }
  console.log(`done: ${runs} runs in ${((Date.now() - t00) / 60000).toFixed(1)} min · forks known: ${seen.size} · log: ${path.relative(ROOT, OUT)}`);
  ws.close(); process.exit(0);
})().catch(e => { console.log('ERROR', e && e.message); process.exit(1); });
