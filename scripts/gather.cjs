// gather.cjs — the dumb job-search script. Searches LinkedIn with set filters, opens each posting, copies everything
// a picker needs, marks the hard walls, and writes one file. READ ONLY: it never presses Apply, never fills a form.
// Built 2026-10-26. The picking is NOT here. George's rule (10/17): never let the script pick jobs. The thinker reads
// the gathered file against me/george-dossier.md + me/writings.md, writes overrides, then map_easy_apply.cjs walks.
//
//   CDP_PORT=19222 node scripts/gather.cjs --keywords "legal operations" [--max 20] [--hours 24] [--remote] [--easy]
//                                          [--location "United States"] [--pages 2]
//
// Output: logs/gather/<stamp>.json (every posting, full description) + logs/gather/<stamp>.md (the table) + prints the table.
// Walls come from scripts/walls.json: a rule hit is a WALL with the exact sentence it matched. No rule = no wall. The
// script never decides "fit"; it only says "this sentence matched this rule".
// Hands: human.cjs (real pointer, wheel scroll) for the one click it makes (the "… more" fold) and the list scroll. Pages load by URL.

const fs = require('fs'); const path = require('path');
const human = require('./human.cjs');
const arg = (k, d) => { const i = process.argv.indexOf(k); return i > -1 ? process.argv[i + 1] : d; };
const has = k => process.argv.includes(k);
const KW = arg('--keywords', 'legal operations');
const MAX = parseInt(arg('--max', '20'), 10);
const HOURS = parseInt(arg('--hours', '24'), 10);
const PAGES = parseInt(arg('--pages', '2'), 10);
const LOC = arg('--location', 'United States');
const PORT = process.env.CDP_PORT || '19222';
const ROOT = path.resolve(__dirname, '..');
const WALLS = JSON.parse(fs.readFileSync(path.join(ROOT, 'scripts/walls.json'), 'utf8')).map(w => ({ ...w, rx: new RegExp(w.re, 'i') }));
const LOGDIR = path.join(ROOT, 'logs/gather'); fs.mkdirSync(LOGDIR, { recursive: true });
const stamp = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19); // to the second: two runs in one minute must not share a file
const OUTJ = path.join(LOGDIR, `gather-${stamp}.json`), OUTM = path.join(LOGDIR, `gather-${stamp}.md`);
setTimeout(() => { console.log('TIMEOUT 20 min'); process.exit(3); }, 20 * 60 * 1000);
const rnd = (a, b) => a + Math.random() * (b - a);

const searchUrl = (start) => {
  const p = new URLSearchParams({ keywords: KW, location: LOC, sortBy: 'DD', f_TPR: `r${HOURS * 3600}` });
  if (has('--easy')) p.set('f_AL', 'true');
  if (has('--remote')) p.set('f_WT', '2');
  if (start) p.set('start', String(start));
  return `https://www.linkedin.com/jobs/search/?${p}`;
};

// What one posting page says, read from the DOM in one gulp. Runs inside the page (sent as text), never in Node.
// LinkedIn's 2026 job page: obfuscated classes, no h1. Stable handles: document.title ("<title> | <company> | LinkedIn"),
// the JobDetails_AboutTheJob_<id> box, and the top text "<company> <title> <location> · <age> · ... Remote Full-time Apply Save".
function readPage() {
  const t = e => (e ? (e.innerText || e.textContent || '') : '').replace(/\s+/g, ' ').trim();
  const lines = e => (e ? (e.innerText || e.textContent || '') : '').replace(/[ \t ]+/g, ' ').replace(/ *\n */g, '\n').replace(/\n{3,}/g, '\n\n').trim();
  const jid = (location.pathname.match(/\/jobs\/view\/(\d+)/) || [])[1] || '';
  const tparts = document.title.split(' | ');
  const title = (tparts[0] || '').trim(), company = (tparts.length >= 3 ? tparts[1] : '').trim();
  const main = t(document.querySelector('main') || document.body);
  const about = document.getElementById('JobDetails_AboutTheJob_' + jid) || document.querySelector('[id^=JobDetails_AboutTheJob]');
  const desc = lines(about).replace(/^About the job\s*/i, '').replace(/\s*(… ?more|show more|show less)\s*$/i, '');
  const cut = main.match(/\b(Easy Apply|Apply)\b( Save)?/);
  const top = cut ? main.slice(0, cut.index + cut[0].length) : main.slice(0, 400);
  // "<company> <title> <location> · <age> · ...": peel off company and title, the location is what is left before the first " · "
  let rest = top;
  if (company && rest.startsWith(company)) rest = rest.slice(company.length).trim();
  if (title && rest.startsWith(title)) rest = rest.slice(title.length).trim();
  const bits = rest.split(' · ');
  const loc = bits.length > 1 ? bits[0].trim() : '';
  const age = bits.length > 1 ? (bits[1].match(/^(Reposted )?\d+ \w+ ago/) || [''])[0] : '';
  const workplace = (bits.slice(1).join(' · ').match(/\b(Remote|Hybrid|On-site)\b/) || [''])[0]; // after the title, so "Fully Remote ..." in a title does not count
  const ctl = [...document.querySelectorAll('button, [role=button], a')].map(t).find(x => /^(Easy Apply|Apply)\b/i.test(x)) || '';
  const applied = /\bApplied\b/.test(top) || /Application (submitted|viewed)/i.test(main.slice(0, 600));
  // Pay: the top line first (LinkedIn's own "$180K/yr - $300K/yr"), then the description. "$5 billion" is not pay; a lone
  // amount with no range, no "K", no "/yr" counts only with a pay word just before it ("More than $6,000,000 donated" does not).
  const money = String.raw`\$\s?\d(?:[\d,]*\d)?(?:\.\d+)?\s?[Kk]?`, unit = String.raw`(?:\s?(?:\/|per|an?)\s?(?:hr|hour|yr|year|annum|month|mo)\b)?`;
  const payRx = new RegExp(`${money}${unit}(?:\\s?(?:-|–|—|to)\\s?${money}${unit})?`, 'g');
  const payIn = s => [...s.matchAll(payRx)].map(m => ({ m: m[0].trim(), before: s.slice(Math.max(0, m.index - 50), m.index), after: s.slice(m.index + m[0].length, m.index + m[0].length + 12) }))
    .filter(({ m, before, after }) => !/^\s*(billion|million|bn|[MB]\b)/i.test(after) && (/[-–—]|\bto\b|[Kk]\b|\/|per|an? /.test(m) || (/salary|pay|compensation|base|wage|range|earn|rate|\bOTE\b/i.test(before) && parseFloat(m.replace(/[^\d.]/g, '')) >= 10000)))
    .map(x => x.m)[0] || '';
  return { title, company, location: loc, workplace, age, top, applyButton: ctl, applied, pay: payIn(top) || payIn(desc), desc };
}
const READ = `(${readPage.toString()})()`;

(async () => {
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  const tab = list.find(o => o.type === 'page' && o.url.includes('linkedin.com')) || list.find(o => o.type === 'page');
  if (!tab) { console.log('no tab on port', PORT); process.exit(2); }
  const h = await human.attach(tab, { settle: false, log: m => process.stderr.write('  [human] ' + m + '\n') });
  const nav = async (url, readyExpr, ms = 15000) => { await h.send('Page.navigate', { url }); const t0 = Date.now(); while (Date.now() - t0 < ms) { try { if (await h.evaluate(readyExpr)) break; } catch { } await human.sleep(300); } await h.pause(1200, 2600); };
  const wheelList = async () => { // scroll the results pane with the wheel so more cards load
    const b = await h.evaluate(`(()=>{const e=document.querySelector('.scaffold-layout__list, .jobs-search-results-list');if(!e)return null;const r=e.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2}})()`);
    if (!b) return;
    for (let i = 0; i < 4; i++) { await h.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: b.x + rnd(-40, 40), y: b.y + rnd(-60, 60), deltaX: 0, deltaY: rnd(500, 900), pointerType: 'mouse' }); await h.pause(500, 1100); }
  };
  const grab = async () => JSON.parse(await h.evaluate('JSON.stringify([...document.querySelectorAll("a[href*=\\"/jobs/view/\\"]")].map(a=>(a.href.match(/jobs\\/view\\/(\\d+)/)||[])[1]).filter(Boolean))'));

  // ---------- 1. search ----------
  let ids = [];
  for (let pg = 0; pg < PAGES && ids.length < MAX * 2; pg++) {
    await nav(searchUrl(pg * 25), 'document.querySelectorAll("a[href*=\\"/jobs/view/\\"]").length>3');
    await wheelList();
    ids = ids.concat(await grab());
  }
  ids = ids.filter((v, i, a) => a.indexOf(v) === i).slice(0, MAX);
  console.log(`search "${KW}" · last ${HOURS} h · ${LOC}${has('--remote') ? ' · remote' : ''}${has('--easy') ? ' · Easy Apply' : ''} → ${ids.length} postings`);

  // ---------- 2. gather ----------
  const out = [];
  for (const [i, jid] of ids.entries()) {
    const url = `https://www.linkedin.com/jobs/view/${jid}/`;
    try {
      await nav(url, '!!document.querySelector("[id^=JobDetails_AboutTheJob]") && / \\| LinkedIn$/.test(document.title)', 12000);
      // the fold on the description ("… more"); the text is in the page either way, the click is what a reader does
      try { await h.click({ text: /^(…\s*)?(see |show )?more$/i, tag: `#JobDetails_AboutTheJob_${jid} button` }); } catch { }
      await h.pause(600, 1400);
      const r = await h.evaluate(READ);
      const rec = { jobId: jid, url, ...r, gatheredAt: new Date().toISOString() };
      rec.desc = (rec.desc || '').slice(0, 12000);
      rec.walls = [];
      // a wall with "field": "title" looks at the title only; "field": "where" looks at "<Remote|Hybrid|On-site> · <location>" (10/26, George: on-site outside the Bay Area must flag even when the description never names the city); the rest look at title + description, one sentence or line at a time
      const sentences = { title: [rec.title], where: [[rec.workplace, rec.location].filter(Boolean).join(' · ')], all: [rec.title, ...rec.desc.split(/(?<=[.!?•])(?<!\b[A-Za-z]\.)\s+|\n+/)] }; // "U.S.", "J.D." do not end a sentence
      const around = (s, rx) => { if (s.length <= 200) return s; const i = Math.max(0, s.search(rx) - 60); return (i ? '…' : '') + s.slice(i, i + 200) + '…'; };
      for (const w of WALLS) { const s = sentences[w.field === 'title' ? 'title' : w.field === 'where' ? 'where' : 'all'].find(x => w.rx.test(x)); if (s) rec.walls.push({ wall: w.name, sentence: around(s.trim(), w.rx) }); }
      rec.easy = /^Easy Apply/i.test(rec.applyButton);
      out.push(rec);
      console.log(`[${i + 1}/${ids.length}] ${rec.title.slice(0, 50)} @ ${rec.company.slice(0, 30)} · ${rec.pay || 'pay ?'} · ${rec.easy ? 'Easy' : (rec.applyButton || 'no button')}${rec.applied ? ' · APPLIED' : ''}${rec.walls.length ? ' · WALL: ' + rec.walls.map(w => w.wall).join(', ') : ''}`);
    } catch (e) { console.log(`[${i + 1}/${ids.length}] ${jid} ERR ${e.message.slice(0, 80)}`); out.push({ jobId: jid, url, error: e.message }); }
    await h.pause(2500, 5000); // LinkedIn throttles fast readers
  }

  // ---------- 3. write ----------
  fs.writeFileSync(OUTJ, JSON.stringify({ keywords: KW, hours: HOURS, location: LOC, remote: has('--remote'), easy: has('--easy'), gatheredAt: new Date().toISOString(), postings: out }, null, 1));
  const rows = out.filter(r => !r.error).map(r => `| ${r.jobId} | ${r.title.slice(0, 45)} | ${r.company.slice(0, 25)} | ${[r.workplace, r.location].filter(Boolean).join(' · ')} | ${r.pay || ''} | ${r.easy ? 'Easy' : 'external'}${r.applied ? ' (applied)' : ''} | ${r.walls.map(w => w.wall).join(', ')} |`);
  const md = `# Gather ${stamp} — "${KW}", last ${HOURS} h, ${LOC}${has('--remote') ? ', remote' : ''}${has('--easy') ? ', Easy Apply only' : ''}\n\n${out.length} postings. Walls are rule hits with the matched sentence in the JSON; they are not a verdict. The picker reads me/george-dossier.md and me/writings.md, then every description in the JSON.\n\n| id | title | company | where | pay | apply | walls |\n|---|---|---|---|---|---|---|\n${rows.join('\n')}\n`;
  fs.writeFileSync(OUTM, md);
  console.log(`\nwrote ${path.relative(ROOT, OUTJ)} and ${path.relative(ROOT, OUTM)}`);
  console.log(md);
  h.close(); process.exit(0); // the 20-min alarm above would otherwise hold node open after the work is done
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
