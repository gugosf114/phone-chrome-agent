// cdpx.cjs — one-shot CDP driver, frame-aware. Wrote it 2026-10-14 for the Google Ads run on the phone's hidden Chrome Beta.
// Port: CDP_PORT (default 9335 = hidden Chrome Beta; 9336 = phone Chrome via chrome.sh; 19222 = laptop via laptop_chrome.sh).
// <tabSub> = any piece of the tab's URL; the FIRST matching tab is used.
//   cdpx eval   <tabSub> <js>                 run JS in the top page
//   cdpx frames <tabSub>                      list frames + cross-site iframes (Google's payment box is one)
//   cdpx feval  <tabSub> <frameUrlSub> <js>   run JS INSIDE a frame, e.g. 'billingaccountmanager'
//   cdpx click  <tabSub> <x> <y>              real mouse click at page CSS coords (reaches into iframes too)
//   cdpx tap    <tabSub> <x> <y>              touch tap (times out on a tab that has no screen)
//   cdpx chars  <tabSub> <text>               type key by key into the focused field (Google's app search ignored pasted text)
//   cdpx type   <tabSub> <text>               paste text in one go (insertText)
//   cdpx key    <tabSub> <Tab|Enter|Escape|Backspace>
//   cdpx nav    <tabSub> <url>
// Coordinates inside an iframe = the iframe's page offset + the element's offset inside it.
const WebSocket = globalThis.WebSocket || require('ws');
const PORT = process.env.CDP_PORT || 9335;
const [,, cmd, tabSub, a1, a2, a3] = process.argv;
const T = (p, ms, what) => Promise.race([p, new Promise((_, r) => setTimeout(() => r(new Error('timeout: ' + what)), ms))]);
(async () => {
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json`)).json();
  const tab = list.find(o => o.type === 'page' && o.url.includes(tabSub));
  if (!tab) { console.log('NO TAB matching', tabSub); process.exit(2); }
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await T(new Promise(r => ws.onopen = r), 10000, 'open');
  let id = 0; const pend = {}; const events = [];
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m); delete pend[m.id]; } else events.push(m); };
  const send = (method, params = {}, sessionId) => T(new Promise(res => { const i = ++id; pend[i] = res; const msg = { id: i, method, params }; if (sessionId) msg.sessionId = sessionId; ws.send(JSON.stringify(msg)); }), 30000, method);
  const ev = async (expr, sessionId, contextId) => { const p = { expression: expr, returnByValue: true, awaitPromise: true }; if (contextId) p.contextId = contextId; const r = await send('Runtime.evaluate', p, sessionId); return r.result && (r.result.exceptionDetails ? 'EXC ' + JSON.stringify(r.result.exceptionDetails).slice(0, 400) : r.result.result.value); };
  const keymap = { Tab: [9, 'Tab'], Enter: [13, 'Enter'], Escape: [27, 'Escape'], Backspace: [8, 'Backspace'] };
  if (cmd === 'eval') console.log(JSON.stringify(await ev(a1)));
  else if (cmd === 'nav') { await send('Page.navigate', { url: a1 }); console.log('nav'); }
  else if (cmd === 'click') { const X = +a1, Y = +a2; for (const type of ['mouseMoved', 'mousePressed', 'mouseReleased']) await send('Input.dispatchMouseEvent', { type, x: X, y: Y, button: 'left', clickCount: 1 }); console.log('clicked', X, Y); }
  else if (cmd === 'tap') { const X = +a1, Y = +a2; await send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: X, y: Y }] }); await new Promise(r => setTimeout(r, 80)); await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] }); console.log('tapped', X, Y); }
  else if (cmd === 'chars') { for (const ch of a1) { await send('Input.dispatchKeyEvent', { type: 'keyDown', key: ch, text: ch, unmodifiedText: ch }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: ch }); await new Promise(r => setTimeout(r, 60)); } console.log('chars typed'); }
  else if (cmd === 'type') { await send('Input.insertText', { text: a1 }); console.log('typed'); }
  else if (cmd === 'key') { const [code, key] = keymap[a1]; for (const type of ['keyDown', 'keyUp']) await send('Input.dispatchKeyEvent', { type, key, code: key, windowsVirtualKeyCode: code, nativeVirtualKeyCode: code }); console.log('key', a1); }
  else if (cmd === 'frames' || cmd === 'feval') {
    const tree = (await send('Page.getFrameTree')).result.frameTree;
    const flat = []; const walk = (n, d) => { flat.push({ id: n.frame.id, url: n.frame.url, d }); (n.childFrames || []).forEach(c => walk(c, d + 1)); }; walk(tree, 0);
    await send('Target.setAutoAttach', { autoAttach: true, waitForDebuggerOnStart: false, flatten: true });
    await new Promise(r => setTimeout(r, 1500));
    const attached = events.filter(m => m.method === 'Target.attachedToTarget').map(m => ({ sessionId: m.params.sessionId, url: m.params.targetInfo.url, type: m.params.targetInfo.type }));
    if (cmd === 'frames') { console.log(JSON.stringify({ frames: flat.map(f => ' '.repeat(f.d) + f.url.slice(0, 150)), oopif: attached.map(a => a.type + ' ' + a.url.slice(0, 150)) }, null, 1)); }
    else {
      const oop = attached.find(a => a.url.includes(a1));
      if (oop) { console.log(JSON.stringify(await ev(a2, oop.sessionId))); }
      else { const f = flat.find(f => f.url.includes(a1)); if (!f) { console.log('NO FRAME', a1); process.exit(3); }
        const w = await send('Page.createIsolatedWorld', { frameId: f.id, worldName: 'cdpx' }); console.log(JSON.stringify(await ev(a2, undefined, w.result.executionContextId))); }
    }
  } else console.log('unknown cmd');
  ws.close(); process.exit(0);
})().catch(e => { console.log('ERR', e.message); process.exit(1); });
