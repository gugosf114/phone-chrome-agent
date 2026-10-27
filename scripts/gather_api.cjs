#!/usr/bin/env node
// Read LinkedIn through GETs observed in this tab. No fixed query/decor IDs, no Apply clicks.
// CDP_PORT=19222 node scripts/gather_api.cjs --keywords "legal operations" --hours 48 --max 30 --questions
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const ROOT = path.resolve(__dirname, '..');
const LOGDIR = path.join(ROOT, 'logs/gather');
const NOTES = path.join(ROOT, 'docs/linkedin-api-notes.md');
const sleep = ms => new Promise(r => setTimeout(r, ms)); // Deliberately ignores HUMAN_SPEED.
const random = (a, b) => a + Math.random() * (b - a);
const text = v => typeof v === 'string' ? v : v?.text || '';
const badURL = url => /\/(checkpoint|authwall)(?:[/?#]|$)/i.test(url);
const redact = headers => Object.fromEntries(Object.entries(headers || {}).map(([k, v]) =>
  [k, /cookie|authorization|csrf|token/i.test(k) ? '<redacted>' : v]));

function options(argv) {
  const o = { keywords: 'legal operations', hours: 24, max: 100, location: 'United States', easy: true, all: false, remote: false, questions: false };
  let mode;
  for (let i = 0; i < argv.length; i++) {
    const k = argv[i];
    if (['--easy', '--any'].includes(k)) {
      if (mode && mode !== k) throw new Error('Choose --easy or --any.');
      mode = k; o.easy = k === '--easy';
    } else if (['--all', '--remote', '--questions'].includes(k)) o[k.slice(2)] = true;
    else if (['--keywords', '--hours', '--max', '--location'].includes(k)) {
      const value = argv[++i];
      if (!value || value.startsWith('--')) throw new Error('Missing value for ' + k);
      o[k.slice(2)] = ['--hours', '--max'].includes(k) ? Number(value) : value;
    } else throw new Error('Unknown option: ' + k);
  }
  for (const k of ['hours', 'max']) if (!Number.isSafeInteger(o[k]) || o[k] < 1) throw new Error('--' + k + ' must be a positive integer');
  if ((process.env.CDP_PORT || '19222') !== '19222') throw new Error('Only CDP_PORT=19222 is allowed.');
  return o;
}

function searchURL(o) {
  const p = new URLSearchParams({ keywords: o.keywords, location: o.location, sortBy: 'DD', f_TPR: `r${o.hours * 3600}` });
  if (o.easy) p.set('f_AL', 'true');
  if (o.remote) p.set('f_WT', '2');
  return 'https://www.linkedin.com/jobs/search/?' + p;
}

function payIn(s) { // Same pay rules as gather.cjs.
  const money = String.raw`\$\s?\d(?:[\d,]*\d)?(?:\.\d+)?\s?[Kk]?`;
  const unit = String.raw`(?:\s?(?:\/|per|an?)\s?(?:hr|hour|yr|year|annum|month|mo)\b)?`;
  const rx = new RegExp(`${money}${unit}(?:\\s?(?:-|–|—|to)\\s?${money}${unit})?`, 'g');
  return [...s.matchAll(rx)].map(m => ({ m: m[0].trim(), before: s.slice(Math.max(0, m.index - 50), m.index), after: s.slice(m.index + m[0].length, m.index + m[0].length + 12) }))
    .filter(({ m, before, after }) => !/^\s*(billion|million|bn|[MB]\b)/i.test(after) && (/[-–—]|\bto\b|[Kk]\b|\/|per|an? /.test(m) || (/salary|pay|compensation|base|wage|range|earn|rate|\bOTE\b/i.test(before) && parseFloat(m.replace(/[^\d.]/g, '')) >= 10000)))
    .map(x => x.m)[0] || '';
}

function richText(v) {
  const s = text(v), breaks = new Set([0, s.length]);
  for (const a of v?.attributesV2 || []) if (['PARAGRAPH', 'LIST_ITEM'].includes(a.detailData?.style)) {
    breaks.add(a.start); breaks.add(a.start + a.length);
  }
  const points = [...breaks].filter(n => Number.isInteger(n) && n >= 0 && n <= s.length).sort((a, b) => a - b);
  return points.slice(1).map((n, i) => s.slice(points[i], n)).join('\n').replace(/\n{3,}/g, '\n\n').trim();
}

function graph(...payloads) {
  const index = new Map();
  for (const p of payloads) for (const x of p?.included || []) if (x.entityUrn) index.set(x.entityUrn, { ...index.get(x.entityUrn), ...x });
  return index;
}

function searchCards(payload) {
  const idx = graph(payload), elements = payload.data?.elements;
  if (!Array.isArray(elements)) throw new Error('Search response has no data.elements array');
  return elements.map(e => idx.get(e.jobCardUnion?.['*jobPostingCard'])).filter(Boolean);
}

function wallsFor(rec, rules) {
  const sentences = { title: [rec.title], where: [[rec.workplace, rec.location].filter(Boolean).join(' · ')], all: [rec.title, ...rec.desc.split(/(?<=[.!?•])(?<!\b[A-Za-z]\.)\s+|\n+/)] };
  const around = (s, rx) => { if (s.length <= 200) return s; const i = Math.max(0, s.search(rx) - 60); return (i ? '…' : '') + s.slice(i, i + 200) + '…'; };
  return rules.flatMap(w => {
    const rx = new RegExp(w.re, 'i');
    const hit = sentences[w.field === 'title' ? 'title' : w.field === 'where' ? 'where' : 'all'].find(s => rx.test(s));
    return hit ? [{ wall: w.name, sentence: around(hit.trim(), rx) }] : [];
  });
}

function decode(card, search, detail, rules, wantQuestions) {
  const idx = graph(search, detail);
  const jobId = (card.jobPostingUrn || card['*jobPosting'] || card.entityUrn).match(/(?:jobPosting:|jobPostingCard:\()(\d+)/)?.[1];
  if (!jobId) throw new Error('Search card has no job ID');
  const job = idx.get('urn:li:fsd_jobPosting:' + jobId) || {};
  const topCard = idx.get(`urn:li:fsd_jobPostingCard:(${jobId},JOB_DETAILS)`) || {};
  const application = idx.get(topCard.primaryActionV2?.applyJobAction?.['*applyJobActionResolutionResult']);
  const insights = (topCard.jobInsightsV2ResolutionResults || []).flatMap(i => (i.jobInsightViewModel?.description || []).map(d => text(d.text).trim())).filter(Boolean);
  const tertiary = text(topCard.tertiaryDescription);
  const workUrn = (job['*jobWorkplaceTypes'] || job['*workplaceTypesResolutionResults'] || [])[0];
  const workplace = idx.get(workUrn)?.localizedName || text(card.secondaryDescription).match(/\((Remote|Hybrid|On-site)\)$/)?.[1] || '';
  const location = tertiary.includes(' · ') ? tertiary.split(' · ')[0].trim() : text(card.secondaryDescription).replace(/\s*\((Remote|Hybrid|On-site)\)$/, '').trim();
  const listedAt = (card.footerItems || []).find(f => f.type === 'LISTED_DATE')?.timeAt || null;
  const age = tertiary.match(/(?:Reposted )?\d+ \w+ ago/)?.[0] || '';
  const applicants = tertiary.match(/(Over\s+)?([\d,]+)\s+(applicants?|people clicked apply)/i);
  const companyUrn = job.companyDetails?.jobCompany?.['*company'] || null;
  const easyApply = application ? application.onsiteApply === true : (card.footerItems || []).some(f => f.type === 'EASY_APPLY_TEXT');
  const applyButton = text(application?.applyCtaText) || (easyApply ? 'Easy Apply' : 'Apply');
  const title = job.title || card.jobPostingTitle || text(card.title);
  const company = text(topCard.primaryDescription) || text(card.primaryDescription) || idx.get(companyUrn)?.name || '';
  const desc = richText(job.description);
  if (!title || !company || !desc) throw new Error(`Incomplete detail JSON for ${jobId}: title/company/description required`);
  const salaryText = insights.find(s => payIn(s)) || (payIn(text(card.tertiaryDescription)) ? text(card.tertiaryDescription) : null);
  const top = [company, title, tertiary, ...insights, applyButton].filter(Boolean).join(' ');
  const rec = { jobId, url: `https://www.linkedin.com/jobs/view/${jobId}/`, title, company, location, workplace, age, top, applyButton, applied: application?.applied === true, pay: payIn(top) || payIn(text(card.tertiaryDescription)) || payIn(desc), desc, gatheredAt: new Date().toISOString(), easy: easyApply,
    workplaceType: workplace || null, applicantCount: applicants ? Number(applicants[2].replace(/,/g, '')) : null,
    applicantCountIsLowerBound: !!applicants?.[1], applicantCountKind: applicants ? (applicants[3] === 'people clicked apply' ? 'apply clicks' : 'applicants') : null,
    salaryInsight: salaryText ? { text: salaryText, source: 'LinkedIn job card' } : null,
    easyApply, postingAge: age || null, postingAgeHours: listedAt ? Math.round((Date.now() - listedAt) / 36000) / 100 : null, listedAt, companyUrn };
  rec.walls = wallsFor(rec, rules);
  if (wantQuestions) {
    rec.questions = null;
    rec.questionsStatus = easyApply ? 'unavailable: no form-schema GET observed without opening Apply' : 'not applicable: external application';
  }
  return rec;
}

class Browser {
  constructor(ws, logPath) {
    this.ws = ws; this.logPath = logPath; this.id = 0; this.pending = new Map(); this.requests = new Map();
    this.observed = new Map(); this.permits = new Set(); this.paused = new Set(); this.tasks = new Set();
    this.queue = Promise.resolve(); this.count = 0; this.lastSent = 0; this.stopped = null; this.closing = false;
  }
  log(data) { fs.appendFileSync(this.logPath, JSON.stringify({ at: new Date().toISOString(), ...data }) + '\n', { mode: 0o600 }); }
  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.id;
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error('CDP timeout: ' + method)); }, 20000);
      this.pending.set(id, { resolve, reject, timer });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async evaluate(expression) {
    const r = await this.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  }
  async stop(reason, ban = true) {
    if (this.stopped) return;
    this.stopped = { reason, ban, at: new Date().toISOString() };
    this.log({ event: 'STOP', ...this.stopped });
    if (ban) {
      fs.mkdirSync(path.dirname(NOTES), { recursive: true });
      fs.appendFileSync(NOTES, `\n### Run stopped ${this.stopped.at}\n\n${reason}. No retry. See \`${path.relative(ROOT, this.logPath)}\`.\n`);
    }
    await this.send('Page.stopLoading').catch(() => {});
    await Promise.all([...this.paused].map(id => this.fail(id)));
  }
  check() { if (this.stopped) throw new Error(this.stopped.reason); }
  async fail(requestId) { this.paused.delete(requestId); await this.send('Fetch.failRequest', { requestId, errorReason: 'Aborted' }).catch(() => {}); }
  async allow(p, data) {
    if (this.stopped || this.closing) return this.fail(p.requestId);
    if (data) {
      if (this.count >= 60) { await this.stop('60-request budget reached', false); return this.fail(p.requestId); }
      await sleep(Math.max(0, this.lastSent + random(2500, 4000) - Date.now()));
      if (this.stopped || this.closing) return this.fail(p.requestId);
      this.lastSent = Date.now(); this.count++;
      this.log({ event: 'ALLOWED', number: this.count, method: p.request.method, url: p.request.url });
    }
    this.paused.delete(p.requestId);
    await this.send('Fetch.continueRequest', { requestId: p.requestId }).catch(e => {
      // A page can cancel a queued request while navigation replaces its document.
      if (!/Invalid InterceptionId/i.test(e.message)) throw e;
      this.log({ event: 'CANCELED', url: p.request.url });
    });
  }
  async intercept(p) {
    this.paused.add(p.requestId);
    const r = p.request, u = new URL(r.url);
    const data = ['XHR', 'Fetch', 'Document', 'Ping', 'EventSource'].includes(p.resourceType) || u.pathname.startsWith('/voyager/api/');
    if (badURL(r.url)) { await this.stop('redirect to checkpoint/authwall'); return this.fail(p.requestId); }
    if (this.stopped || this.closing) return this.fail(p.requestId);
    const safeDocument = p.resourceType === 'Document' && u.origin === 'https://www.linkedin.com' && /^\/jobs\/(search\/|view\/\d+\/)/.test(u.pathname);
    const permitted = this.permits.delete(r.url);
    if (r.method !== 'GET' || (data && !safeDocument && !permitted)) {
      this.log({ event: 'BLOCKED', method: r.method, url: r.url, status: 'blocked locally', reason: r.method !== 'GET' ? 'GET only' : 'not an explicit job read' });
      return this.fail(p.requestId);
    }
    if (data) { this.queue = this.queue.then(() => this.allow(p, true)); return this.queue; }
    return this.allow(p, false);
  }
  async event(method, p) {
    if (method === 'Fetch.requestPaused') return this.intercept(p);
    if (method === 'Network.requestWillBeSent') {
      if (badURL(p.request.url) || (p.redirectResponse && [403, 429, 999].includes(p.redirectResponse.status))) await this.stop('blocked redirect: ' + p.request.url);
      const r = { method: p.request.method, url: p.request.url, headers: p.request.headers, type: p.type };
      this.requests.set(p.requestId, r);
      if (r.url.includes('/voyager/api/')) {
        this.observed.set(r.url, r);
        this.log({ event: 'REQUEST', requestId: p.requestId, ...r, headers: redact(r.headers) });
      }
    }
    if (method === 'Network.responseReceived') {
      const rec = this.requests.get(p.requestId);
      if (rec) { rec.status = p.response.status; rec.mimeType = p.response.mimeType; }
      if ([403, 429, 999].includes(p.response.status)) await this.stop(`HTTP ${p.response.status}: ${p.response.url}`);
      const location = Object.entries(p.response.headers || {}).find(([k]) => k.toLowerCase() === 'location')?.[1];
      if (location && badURL(new URL(location, p.response.url).href)) await this.stop('redirect to checkpoint/authwall: ' + location);
    }
    if (method === 'Network.loadingFinished') {
      const rec = this.requests.get(p.requestId);
      if (!rec || !['Document', 'XHR', 'Fetch'].includes(rec.type)) return;
      let body;
      try {
        const r = await this.send('Network.getResponseBody', { requestId: p.requestId });
        body = r.base64Encoded ? Buffer.from(r.body, 'base64').toString() : r.body;
      } catch (e) { this.log({ event: 'BODY_UNAVAILABLE', url: rec.url, error: e.message }); return; }
      if (/unusual activity/i.test(body)) await this.stop('body mentions unusual activity: ' + rec.url);
      if (rec.url.includes('/voyager/api/')) this.log({ event: 'RESPONSE', ...rec, headers: redact(rec.headers), bytes: Buffer.byteLength(body), preview: Buffer.from(body).subarray(0, 2048).toString() });
    }
  }
  async init() {
    this.ws.on('message', raw => {
      const m = JSON.parse(raw);
      if (m.id) {
        const p = this.pending.get(m.id);
        if (p) { clearTimeout(p.timer); this.pending.delete(m.id); m.error ? p.reject(new Error(m.error.message)) : p.resolve(m.result || {}); }
      } else {
        const task = this.event(m.method, m.params).catch(e => this.stop('capture error: ' + e.message, false));
        this.tasks.add(task); task.finally(() => this.tasks.delete(task));
      }
    });
    await this.send('Network.enable', { maxTotalBufferSize: 20000000, maxResourceBufferSize: 5000000 });
    await this.send('Page.enable');
    await this.send('Fetch.enable', { patterns: [{ urlPattern: 'http*', requestStage: 'Request' }] });
  }
  async discover(o) {
    await this.send('Page.bringToFront');
    await this.send('Page.navigate', { url: searchURL(o) });
    await sleep(random(1500, 3500));
    const until = Date.now() + 25000;
    while (Date.now() < until) {
      this.check();
      const requests = [...this.observed.values()].filter(r => r.method === 'GET');
      const search = requests.find(r => new URL(r.url).pathname === '/voyager/api/voyagerJobsDashJobCards');
      const top = requests.find(r => /cardSectionTypes:List\(TOP_CARD,HOW_YOU_FIT_CARD\)/.test(r.url));
      const description = requests.find(r => /cardSectionTypes:List\(JOB_DESCRIPTION_CARD\)/.test(r.url));
      if (search && top && description) {
        if (new URL(top.url).searchParams.get('queryId') !== new URL(description.url).searchParams.get('queryId')) throw new Error('Observed section query IDs differ; cannot combine');
        return { search, top, description };
      }
      await sleep(250);
    }
    throw new Error('No complete live search/detail GET templates observed; no guessed IDs or fallback endpoint');
  }
  async get(url, template) {
    this.check();
    const u = new URL(url), t = new URL(template.url);
    if (u.origin !== 'https://www.linkedin.com' || u.pathname !== t.pathname || !['/voyager/api/voyagerJobsDashJobCards', '/voyager/api/graphql'].includes(u.pathname)) throw new Error('GET is outside observed job endpoints');
    if (u.pathname.endsWith('/graphql') && (!/^voyagerJobsDashJobPostingDetailSections\./.test(u.searchParams.get('queryId') || '') || u.searchParams.get('queryId') !== t.searchParams.get('queryId'))) throw new Error('Unobserved detail query ID');
    if (this.count >= 60) { await this.stop('60-request budget reached', false); this.check(); }
    const headers = Object.fromEntries(Object.entries(template.headers).filter(([k]) => /^(accept|x-restli-protocol-version|x-li-.*)$/.test(k.toLowerCase())));
    // The browser supplies cookies, Origin, Referer, User-Agent and Sec-* headers itself.
    async function pageGet(url, observed) {
      if (location.origin !== 'https://www.linkedin.com' || /\/(checkpoint|authwall)/i.test(location.href)) throw new Error('Tab is outside signed-in LinkedIn');
      const cookie = document.cookie.split(';').map(s => s.trim()).find(s => s.startsWith('JSESSIONID='));
      if (!cookie) throw new Error('No readable JSESSIONID');
      const headers = { ...observed, 'csrf-token': decodeURIComponent(cookie.slice(11)).replace(/^"|"$/g, '') };
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 15000);
      try {
        const r = await window.fetch(url, { method: 'GET', credentials: 'include', headers, redirect: 'manual', signal: controller.signal });
        return { status: r.status, type: r.type, url: r.url, body: await r.text() };
      } finally { clearTimeout(timer); }
    }
    this.permits.add(url);
    let r;
    try { r = await this.evaluate(`(${pageGet.toString()})(${JSON.stringify(url)},${JSON.stringify(headers)})\n//# sourceURL=gather-api-read`); }
    finally { this.permits.delete(url); }
    if ([403, 429, 999].includes(r.status) || badURL(r.url) || /unusual activity/i.test(r.body)) await this.stop(`blocked GET (HTTP ${r.status}): ${url}`);
    this.check();
    if (r.type === 'opaqueredirect' || r.status === 0) throw new Error('GET redirected; no redirect was followed');
    if (r.status !== 200) throw new Error(`GET returned HTTP ${r.status}; no retry`);
    let payload;
    try { payload = JSON.parse(r.body); } catch { throw new Error('GET did not return JSON; no retry'); }
    return payload;
  }
  async close() {
    this.closing = true;
    for (const id of [...this.paused]) await this.fail(id);
    await Promise.allSettled([...this.tasks]);
    await this.send('Fetch.disable').catch(() => {});
    for (const p of this.pending.values()) { clearTimeout(p.timer); p.reject(new Error('CDP closed')); }
    this.pending.clear(); this.ws.close();
  }
}

function lock() {
  fs.mkdirSync(LOGDIR, { recursive: true });
  // DOM gather is unmodified. Refuse its live process, then enforce a minute after its last output.
  const processes = execFileSync('ps', ['-eo', 'comm,args'], { encoding: 'utf8' });
  if (processes.split('\n').some(l => /^node\s/.test(l) && /(?:^|[ /])gather\.cjs(?:\s|$)/.test(l))) throw new Error('DOM gather is running; wait at least two minutes after it finishes');
  for (const f of fs.readdirSync(LOGDIR)) if (/^gather-\d.*\.json$/.test(f) && Date.now() - fs.statSync(path.join(LOGDIR, f)).mtimeMs < 60000) throw new Error('DOM gather ran in the last minute; wait two minutes');
  const file = path.join(LOGDIR, '.gather-api.lock');
  if (fs.existsSync(file)) {
    const old = JSON.parse(fs.readFileSync(file, 'utf8'));
    let alive = false; try { process.kill(old.pid, 0); alive = true; } catch (e) { if (e.code !== 'ESRCH') throw e; }
    if (alive) throw new Error('Another API gather holds the lock');
    fs.unlinkSync(file);
  }
  fs.writeFileSync(file, JSON.stringify({ pid: process.pid, at: new Date().toISOString() }), { flag: 'wx', mode: 0o600 });
  return () => fs.unlinkSync(file);
}

function table(run, stamp) {
  const cell = s => String(s || '').replace(/\|/g, '\\|').replace(/\n/g, ' ');
  const rows = run.postings.filter(r => !r.error).map(r => [r.jobId, r.title.slice(0, 45), r.company.slice(0, 25), [r.workplace, r.location].filter(Boolean).join(' · '), r.pay, (r.easy ? 'Easy' : 'external') + (r.applied ? ' (applied)' : ''), r.walls.map(w => w.wall).join(', ')]);
  return `# Gather API ${stamp} — "${run.keywords}", last ${run.hours} h, ${run.location}\n\n${run.postings.length} postings (${run.skippedSeen} skipped as seen, ${run.skippedNo} as no). ${run.verdict}.\nWalls are rule hits, not a verdict. ${run.stopReason || ''}\n\n| id | title | company | where | pay | apply | walls |\n|---|---|---|---|---|---|---|\n${rows.map(r => '| ' + r.map(cell).join(' | ') + ' |').join('\n')}\n`;
}

async function main() {
  const o = options(process.argv.slice(2)), unlock = lock();
  const stamp = new Date().toISOString().replace(/[:T]/g, '-').slice(0, 19);
  const base = path.join(LOGDIR, 'gather-api-' + stamp), started = Date.now();
  const readJSON = (f, d) => fs.existsSync(f) ? JSON.parse(fs.readFileSync(f, 'utf8')) : d;
  const seenFile = path.join(LOGDIR, 'seen.json'), seen = readJSON(seenFile, {}), no = readJSON(path.join(__dirname, 'no.json'), {});
  const rules = readJSON(path.join(__dirname, 'walls.json'), []);
  const run = { keywords: o.keywords, hours: o.hours, location: o.location, remote: o.remote, easy: o.easy, skippedSeen: 0, skippedNo: 0, gatheredAt: new Date().toISOString(), postings: [], source: 'page Voyager GET', requestedMax: o.max, questionsRequested: o.questions };
  let b, failed = false;
  try {
    const tabs = await (await fetch('http://127.0.0.1:19222/json')).json();
    const tab = tabs.find(t => t.type === 'page' && t.url.startsWith('https://www.linkedin.com/jobs/search/')) || tabs.find(t => t.type === 'page' && t.url.startsWith('https://www.linkedin.com/jobs/'));
    if (!tab) throw new Error('No existing LinkedIn jobs tab on 19222');
    const WS = (() => { try { return require('ws'); } catch { return require('/root/mbc-analytics/node_modules/ws'); } })();
    const ws = new WS(tab.webSocketDebuggerUrl);
    await new Promise((r, j) => { ws.once('open', r); ws.once('error', j); });
    b = new Browser(ws, base + '.network.jsonl'); await b.init();
    const templates = await b.discover(o);
    run.endpoints = [templates.search.url, templates.top.url, templates.description.url];
    const visited = new Set();
    for (let start = 0; run.postings.length < o.max && b.count < 60; start += 25) {
      const searchUrl = templates.search.url.replace(/([?&]count=)\d+/, (_, p) => p + '25').replace(/([?&]start=)\d+/, (_, p) => p + start);
      const search = await b.get(searchUrl, templates.search), cards = searchCards(search);
      if (!cards.length) break;
      for (const card of cards) {
        const id = (card.jobPostingUrn || card['*jobPosting'] || card.entityUrn).match(/(?:jobPosting:|jobPostingCard:\()(\d+)/)?.[1];
        if (!id || visited.has(id)) continue;
        visited.add(id);
        if (no[id]) { run.skippedNo++; continue; }
        if (seen[id] && !o.all) { run.skippedSeen++; continue; }
        if (run.postings.length >= o.max || b.count >= 60) break;
        const url = templates.top.url.replace('TOP_CARD,HOW_YOU_FIT_CARD', 'TOP_CARD,HOW_YOU_FIT_CARD,JOB_DESCRIPTION_CARD')
          .replace(/(jobPostingUrn:urn(?:%3A|:)li(?:%3A|:)fsd_jobPosting(?:%3A|:))\d+/i, (_, p) => p + id);
        const detail = await b.get(url, templates.top);
        const rec = decode(card, search, detail, rules, o.questions);
        run.postings.push(rec);
        seen[id] = { first: seen[id]?.first || rec.gatheredAt, title: rec.title, company: rec.company };
        fs.writeFileSync(seenFile, JSON.stringify(seen, null, 1), { mode: 0o600 });
        fs.writeFileSync(base + '.json', JSON.stringify(run, null, 1), { mode: 0o600 });
        console.log(`[${run.postings.length}/${o.max}] ${rec.title.slice(0, 55)} @ ${rec.company} · ${rec.pay || 'pay ?'}`);
      }
      const paging = search.data.paging;
      if (cards.length < 25 || (Number.isFinite(paging?.total) && start + 25 >= paging.total)) break;
    }
    if (b.count >= 60 && run.postings.length < o.max) run.stopReason = '60-request budget reached; no more reads';
    run.verdict = o.questions || run.stopReason ? 'partial' : 'works';
  } catch (e) {
    failed = true; run.stopReason = e.message; run.verdict = run.postings.length ? 'partial' : 'not viable';
    console.error('STOP ' + e.message);
  } finally {
    if (b) await b.close();
    run.elapsedSeconds = Math.round((Date.now() - started) / 100) / 10;
    run.jobsPerSecond = Number((run.postings.length / run.elapsedSeconds).toFixed(3));
    run.dataRequests = b?.count || 0;
    run.banSignal = b?.stopped?.ban ? b.stopped.reason : null;
    if (run.banSignal) { failed = true; run.verdict = 'partial'; run.stopReason = run.banSignal; }
    fs.writeFileSync(base + '.json', JSON.stringify(run, null, 1), { mode: 0o600 });
    fs.writeFileSync(base + '.md', table(run, stamp), { mode: 0o600 });
    unlock();
    console.log(JSON.stringify({ verdict: run.verdict, jobs: run.postings.length, seconds: run.elapsedSeconds, jobsPerSecond: run.jobsPerSecond, requests: run.dataRequests, banSignal: run.banSignal, file: path.relative(ROOT, base + '.json') }));
  }
  process.exitCode = failed ? 1 : 0;
}

module.exports = { options, graph, searchCards, decode, payIn, richText, wallsFor, Browser, table };
if (require.main === module) main().catch(e => { console.error(e.message); process.exitCode = 1; });
