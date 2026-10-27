// floor plan crawler, read only; first used 2026-10-26 on github.com in the box Chromium on 9222
// floorplan.cjs — draw a site's floor plan: rooms (pages), doors (links), signs (buttons/inputs), READ ONLY.
// node floorplan.cjs <startUrl> <depth> <maxPages> <out.json>   (CDP_PORT env, default 9222)
// Follows same-origin links by GET navigation only. Never clicks a button. Never follows a URL on the deny list.
const WebSocket = globalThis.WebSocket || require("/root/mbc-analytics/node_modules/ws");
const fs = require("fs");
const [,, start, depthS, maxS, out] = process.argv;
const PORT = process.env.CDP_PORT || "9222";
const DEPTH = +(depthS || 2), MAX = +(maxS || 45);
const DENY = /logout|signout|sign_out|\/login|\/signup|\/join|settings|\/delete|\/new\b|\/edit|\/upload|\/remove|\/archive|\/transfer|\/billing|\/sponsors?\b|\/marketplace|\/security\/advisories|\/codespaces\/new|\/apps\/|oauth|\/sessions|\/account|\/password|\/2fa|\/invitations|\/unsubscribe|\/star\b|\/fork\b|\/watch\b|\/subscribe|\/follow|\/block|\/report|\/compare|\/pulls\/new|\/issues\/new|\/releases\/new|\/wiki\/_new|\.(png|jpg|svg|zip|tar|gz|pdf)$/i;
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function cdp(port) {
  const ver = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
  const ws = new WebSocket(ver.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0; const pend = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m); delete pend[m.id]; } };
  const send = (method, params = {}, sessionId) => new Promise(res => { const i = ++id; pend[i] = res; ws.send(JSON.stringify({ id: i, method, params, sessionId })); });
  return { ws, send };
}

const READ = `(() => {
  const vis = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const name = el => (el.getAttribute('aria-label') || el.innerText || el.value || el.placeholder || el.title || el.getAttribute('name') || '').trim().replace(/\\s+/g,' ').slice(0, 80);
  const links = [], buttons = [], inputs = [];
  document.querySelectorAll('a[href]').forEach(a => { const n = name(a); const h = a.href; if (!n && !h) return; links.push({ n, h, v: vis(a) }); });
  document.querySelectorAll('button, [role=button], input[type=submit]').forEach(b => { const n = name(b); if (!n) return; buttons.push({ n, v: vis(b) }); });
  document.querySelectorAll('input:not([type=hidden]):not([type=submit]), select, textarea').forEach(i => { inputs.push({ n: name(i) || i.id, t: i.type || i.tagName.toLowerCase(), v: vis(i) }); });
  const uniq = (arr, k) => { const s = new Set(); return arr.filter(x => { const key = k(x); if (s.has(key)) return false; s.add(key); return true; }); };
  return JSON.stringify({ title: document.title, url: location.href, h1: (document.querySelector('h1')||{}).innerText || '',
    links: uniq(links, x => x.n + '|' + x.h).slice(0, 400), buttons: uniq(buttons, x => x.n).slice(0, 150), inputs: uniq(inputs, x => x.n + x.t).slice(0, 60) });
})()`;

(async () => {
  const origin = new URL(start).origin;
  const { ws, send } = await cdp(PORT);
  const { result: { targetId } } = await send("Target.createTarget", { url: "about:blank" });
  const { result: { sessionId } } = await send("Target.attachToTarget", { targetId, flatten: true });
  await send("Page.enable", {}, sessionId); await send("Runtime.enable", {}, sessionId);
  const norm = u => { try { const x = new URL(u); x.hash = ""; x.search = ""; return x.href.replace(/\/$/, ""); } catch { return null; } };
  const seen = new Set(), queue = [{ u: norm(start), d: 0, from: "start" }], pages = [];
  while (queue.length && pages.length < MAX) {
    const { u, d, from } = queue.shift();
    if (!u || seen.has(u)) continue; seen.add(u);
    try {
      await send("Page.navigate", { url: u }, sessionId);
      await sleep(3500);
      const r = await send("Runtime.evaluate", { expression: READ, returnByValue: true }, sessionId);
      const page = JSON.parse(r.result.result.value); page.depth = d; page.from = from;
      pages.push(page);
      process.stderr.write(`[${pages.length}/${MAX}] d${d} ${page.title.slice(0, 60)} | ${u} | links ${page.links.length} buttons ${page.buttons.length}\n`);
      if (d < DEPTH) {
        let added = 0;
        for (const l of page.links) {
          const n = norm(l.h); if (!n || !n.startsWith(origin) || seen.has(n) || DENY.test(n)) continue;
          if (queue.some(q => q.u === n)) continue;
          queue.push({ u: n, d: d + 1, from: u }); if (++added >= 25) break;
        }
      }
    } catch (e) { process.stderr.write(`ERR ${u}: ${e.message}\n`); }
  }
  fs.writeFileSync(out, JSON.stringify({ start, depth: DEPTH, drawn: new Date().toISOString(), pages }, null, 1));
  await send("Target.closeTarget", { targetId });
  ws.close();
  console.log(`wrote ${out}: ${pages.length} pages`);
})();
