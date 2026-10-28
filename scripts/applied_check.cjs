#!/usr/bin/env node
// applied_check.cjs — the receipt. Open LinkedIn's own Applied list (My Jobs → Applied), read every job on it, and say
// which of the given job ids are there. "If it was an Easy Apply, checking what we applied to is also easy." (George 10/27)
//
//   CDP_PORT=19222 node scripts/applied_check.cjs --ids 111,222         # these ids
//   CDP_PORT=19222 node scripts/applied_check.cjs                       # ids from the newest map-*.jsonl
//   CDP_PORT=19222 node scripts/applied_check.cjs --list                # just print the Applied list
// Also used by map_easy_apply.cjs at the end of every --submit run. Read-only: scroll and read, no presses.
const fs = require('fs'); const path = require('path');
const human = require('./human.cjs');
const ROOT = path.resolve(__dirname, '..');
const LOGDIR = path.join(ROOT, 'logs/easy_apply_map');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const URL = 'https://www.linkedin.com/jobs-tracker/?stage=applied'; // 10/27: /my-items/saved-jobs/?cardType=APPLIED now redirects to the tracker's Saved tab

const READ = `(()=>{const out=[];for(const a of document.querySelectorAll('a[href*="/jobs/view/"]')){const m=a.href.match(/jobs\\/view\\/(\\d+)/);if(!m)continue;
  const card=a.closest('li')||a.closest('[data-chameleon-result-urn]')||(a.parentElement&&a.parentElement.parentElement)||a.parentElement;const t=(card?card.innerText:a.innerText).replace(/\\s+/g,' ').trim();
  const when=(t.match(/Applied\\s+([^·]*?ago)/i)||[])[1]||(t.match(/Applied on ([A-Za-z]+ \\d+(, \\d{4})?)/i)||[])[1]||'';
  if(!out.some(o=>o.jobId===m[1]))out.push({jobId:m[1],title:(a.innerText||'').replace(/\\s+/g,' ').trim().slice(0,80),when,text:t.slice(0,160)});}
  return {count:out.length,items:out,title:document.title,url:location.href}})()`;

async function check(h, ids = []) {
  await h.send('Page.navigate', { url: URL });
  const t0 = Date.now(); while (Date.now() - t0 < 15000) { if (await h.evaluate('/jobs-tracker/.test(location.pathname) && document.readyState==="complete" && !!document.querySelector(\'a[href*="/jobs/view/"]\')')) break; await sleep(300); }
  await h.pause(1500, 2500);
  // make sure the Applied tab is the one showing (it is a checkbox-styled label); press it if not
  await h.evaluate('(()=>{if(/stage=applied/.test(location.search))return "on";const l=[...document.querySelectorAll("label")].find(e=>/^Applied\\s*·/.test((e.innerText||"").trim()));if(!l)return "no label";const c=l.control||document.getElementById(l.htmlFor);l.click();if(c&&!c.checked)c.click();return "pressed"})()');
  await h.pause(2500, 3500);
  console.log('tracker:', await h.evaluate('location.href'));
  let seen = new Map(); let same = 0;
  for (let i = 0; i < 8; i++) { // the list loads as you scroll; stop when a scroll adds nothing
    const r = await h.evaluate(READ); for (const it of r.items) seen.set(it.jobId, it);
    if (ids.length && ids.every(j => seen.has(j))) break;
    const before = seen.size; await h.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: 400, y: 500, deltaX: 0, deltaY: 1200, pointerType: 'mouse' }).catch(() => {});
    await h.pause(1200, 2000);
    if (seen.size === before && ++same >= 2) break; else if (seen.size !== before) same = 0;
  }
  const list = [...seen.values()];
  const res = { checkedAt: new Date().toISOString(), listCount: list.length, applied: [], notOnList: [] };
  for (const j of ids) { const it = seen.get(j); if (it) res.applied.push({ jobId: j, title: it.title, when: it.when }); else res.notOnList.push(j); }
  if (!ids.length) res.list = list;
  console.log(`Applied list: ${list.length} jobs read` + (ids.length ? ` · on list ${res.applied.length} of ${ids.length}` + (res.notOnList.length ? ` · NOT on list: ${res.notOnList.join(', ')}` : '') : ''));
  for (const a of res.applied) console.log(`  SENT  ${a.jobId}  ${a.title}  ${a.when}`);
  for (const j of res.notOnList) console.log(`  not sent  ${j}`);
  return res;
}

if (require.main === module) (async () => {
  const PORT = process.env.CDP_PORT || '19222';
  const arg = (k, d) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : d; };
  let ids = (arg('--ids', '') || '').split(',').map(s => s.trim()).filter(Boolean);
  if (!ids.length && !process.argv.includes('--list')) {
    const logs = fs.readdirSync(LOGDIR).filter(f => /^map-.*\.jsonl$/.test(f)).sort(); const last = logs[logs.length - 1];
    if (last) for (const line of fs.readFileSync(path.join(LOGDIR, last), 'utf8').split('\n')) { try { const o = JSON.parse(line); if (o.jobId && o.run) ids.push(o.jobId); } catch {} }
    console.log(`ids from ${last}: ${ids.join(', ')}`);
  }
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  const tab = list.find(o => o.type === 'page' && o.url.includes('linkedin.com')) || list.find(o => o.type === 'page');
  if (!tab) { console.log('no tab on port', PORT); process.exit(2); }
  // 10/28: a tab behind another tab reads as hidden and every mouse event takes 5 s; make ours the front tab first
  try { await fetch(`http://127.0.0.1:${PORT}/json/activate/${tab.id}`); await new Promise(r => setTimeout(r, 600)); } catch {}
  const h = await human.attach(tab, {});
  const r = await check(h, ids);
  const out = path.join(LOGDIR, `applied-${new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19)}.json`);
  fs.writeFileSync(out, JSON.stringify(r, null, 1)); console.log('saved', path.relative(ROOT, out));
  h.close(); process.exit(r.notOnList.length ? 1 : 0);
})().catch(e => { console.log('ERROR', e.message); process.exit(1); });

module.exports = { check };
