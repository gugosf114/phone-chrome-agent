// make_pdf.cjs — HTML in, PDF out, through the box Chromium's Page.printToPDF. Letter size, 0.6 in margins. Built 2026-10-27.
//
//   node scripts/make_pdf.cjs apply/<jobId>/resume.html apply/<jobId>/resume.pdf
//
// Printer: the box Chromium on 127.0.0.1:9222 (start it with `bash /root/hchrome/start.sh` if it is down). PDF_CDP_PORT
// picks another port. The page opens from file://, so fonts and images resolve next to the HTML. Prints the page count:
// a resume must come out at 1 page; the script says so loudly when it does not.

const fs = require('fs'); const path = require('path');
const WebSocket = globalThis.WebSocket || (() => { try { return require('ws'); } catch { return require('/root/mbc-analytics/node_modules/ws'); } })();
const PORT = process.env.PDF_CDP_PORT || '9222';
const [,, inHtml, outPdf] = process.argv;
if (!inHtml || !outPdf) { console.log('usage: node scripts/make_pdf.cjs <in.html> <out.pdf>'); process.exit(2); }
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const tab = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`, { method: 'PUT' })).json();
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0; const pend = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m); delete pend[m.id]; } };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pend[i] = m => m.error ? rej(new Error(method + ': ' + m.error.message)) : res(m.result || {}); ws.send(JSON.stringify({ id: i, method, params })); });
  try {
    await send('Page.navigate', { url: 'file://' + path.resolve(inHtml) });
    for (let i = 0; i < 40; i++) { const r = await send('Runtime.evaluate', { expression: 'document.readyState==="complete" && document.fonts.status==="loaded"', returnByValue: true }); if (r.result && r.result.value) break; await sleep(250); }
    const { data } = await send('Page.printToPDF', { paperWidth: 8.5, paperHeight: 11, marginTop: 0.6, marginBottom: 0.6, marginLeft: 0.6, marginRight: 0.6, printBackground: true, preferCSSPageSize: false });
    const buf = Buffer.from(data, 'base64');
    fs.mkdirSync(path.dirname(path.resolve(outPdf)), { recursive: true });
    fs.writeFileSync(outPdf, buf);
    const pages = (buf.toString('latin1').match(/\/Type\s*\/Page(?!s)/g) || []).length;
    console.log(`${outPdf}: ${pages} page${pages === 1 ? '' : 's'}, ${(buf.length / 1024).toFixed(0)} KB`);
    if (/resume/i.test(path.basename(outPdf)) && pages !== 1) console.log('WARNING: a resume must be one page');
  } finally {
    ws.close();
    await fetch(`http://127.0.0.1:${PORT}/json/close/${tab.id}`).catch(() => {});
  }
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
