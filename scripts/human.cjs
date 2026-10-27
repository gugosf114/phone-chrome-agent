// human.cjs — the agent's hands, made to move like a person's. Plain CDP, no Playwright. Built 2026-10-26.
// v2 (same night): folded in the other model's helper (hidden-operator/web/human.cjs on the phone): no Runtime.enable,
// bring the tab to front and refuse to act on a hidden tab, settle + one idle move before the first action, wheel-scroll
// (not JS scrollIntoView) until the target is in view, Shift held for capitals, a real finger (touch events) on Android.
//
// Why: our scripts clicked with element.click() and filled boxes by setting .value. No pointer ever moved,
// no key was ever pressed. Captcha scoring (reCAPTCHA v3/Enterprise, Cloudflare) watches exactly that.
// The browser is already real (headed Chrome, home IP, real profile); this makes the HANDS real too.
//
// It is an imitation inside Chrome. Chrome is told "the pointer moved here, pressed, released." Your real
// mouse never moves. On the phone it is a pretend finger. Nothing outside the browser is touched.
//
// Use from any script:
//   const human = require('./human.cjs');
//   const h = await human.attach(tab);          // tab = an entry from http://127.0.0.1:<port>/json (type page)
//   await h.click('button[aria-label="Easy Apply"]');       // CSS selector, or {text:/^Next$/i}
//   await h.type('input[name=email]', 'name@example.com'); // clears the box first, then key by key
//   await h.key('Enter');                                   // one key, no box
//   await h.keys('University of C');                        // keys into the focused element, no click, no clearing
//   h.on('Page.fileChooserOpened', p => ...);               // CDP events
//   await h.pause();                                        // a short human pause (250–900 ms)
//   h.close();
//
// Command line test:
//   CDP_PORT=9222 node human.cjs <tabUrlSubstring> click '<css or text:regex>'
//   CDP_PORT=9222 node human.cjs <tabUrlSubstring> type '<css>' '<text>'
//
// Speed dial: HUMAN_SPEED=0 makes every pause zero (still real pointer + real keys). Default 1.

const WebSocket = globalThis.WebSocket || (() => { try { return require('ws'); } catch { return require('/root/mbc-analytics/node_modules/ws'); } })();
const SPEED = process.env.HUMAN_SPEED === undefined ? 1 : +process.env.HUMAN_SPEED;
const sleep = ms => new Promise(r => setTimeout(r, ms * SPEED));
const rnd = (a, b) => a + Math.random() * (b - a);
const jitter = (a, b) => sleep(rnd(a, b));

const VK = { Enter: 13, Tab: 9, Escape: 27, Backspace: 8, ArrowDown: 40, ArrowUp: 38, ArrowLeft: 37, ArrowRight: 39, ' ': 32 };
const keyOf = (ch) => {
  if (/^[a-z]$/.test(ch)) return { key: ch, code: 'Key' + ch.toUpperCase(), vk: ch.toUpperCase().charCodeAt(0), text: ch, shift: false };
  if (/^[A-Z]$/.test(ch)) return { key: ch, code: 'Key' + ch, vk: ch.charCodeAt(0), text: ch, unmod: ch.toLowerCase(), shift: true };
  if (/^[0-9]$/.test(ch)) return { key: ch, code: 'Digit' + ch, vk: ch.charCodeAt(0), text: ch, shift: false };
  if (ch === ' ') return { key: ' ', code: 'Space', vk: 32, text: ' ', shift: false };
  if (ch === '\n') return { key: 'Enter', code: 'Enter', vk: 13, text: '\r', shift: false };
  const shifted = '~!@#$%^&*()_+{}|:"<>?';
  return { key: ch, code: '', vk: 0, text: ch, shift: shifted.includes(ch) };
};

async function attach(tab, opts = {}) {
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0; const pend = {}; const listeners = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m); delete pend[m.id]; } else if (m.method && listeners[m.method]) listeners[m.method].forEach(f => f(m.params)); };
  const on = (method, fn) => { (listeners[method] = listeners[method] || []).push(fn); }; // CDP events, e.g. Page.fileChooserOpened
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pend[i] = m => m.error ? rej(new Error(method + ': ' + m.error.message)) : res(m.result || {}); ws.send(JSON.stringify({ id: i, method, params })); });
  // No Runtime.enable on purpose: it is one of the automation marks pages can see. evaluate works without it.
  const evaluate = async (expression) => { const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true, userGesture: true }); if (r.exceptionDetails) throw new Error(r.exceptionDetails.text || 'page error'); return r.result.value; };
  const log = opts.log || (() => {});

  // Which kind of hand: a finger on Android Chrome, a mouse everywhere else.
  const env = await evaluate(`({touch: navigator.maxTouchPoints > 0 && /Android/i.test(navigator.userAgent), vw: innerWidth, vh: innerHeight})`);
  const touch = opts.touch === undefined ? env.touch : opts.touch;
  const pointer = { x: rnd(env.vw * 0.2, env.vw * 0.6), y: rnd(env.vh * 0.2, env.vh * 0.5) };

  // The tab must be in front and visible, or the page scores the action as coming from nowhere.
  const front = async () => {
    await send('Page.bringToFront').catch(() => {});
    const hidden = await evaluate('document.hidden');
    if (hidden) throw new Error('human: tab is hidden (document.hidden). Bring Chrome to the front first.');
  };

  const finder = (sel) => typeof sel === 'string'
    ? `document.querySelector(${JSON.stringify(sel)})`
    : `[...document.querySelectorAll(${JSON.stringify(sel.tag || 'button, a, [role=button], input[type=submit], label, summary')})].filter(e=>e.getBoundingClientRect().height>0).find(e=>${sel.text.toString()}.test((e.innerText||e.value||e.getAttribute('aria-label')||'').trim()))`;
  // hit: the element owns the point at its own centre (nothing on top of it, like LinkedIn's chat layer at the bottom edge).
  const readBox = async (sel) => evaluate(`(()=>{const e=${finder(sel)}; if(!e) return null; const b=e.getBoundingClientRect(); const t=document.elementFromPoint(b.left+b.width/2,b.top+b.height/2); return {x:b.left,y:b.top,w:b.width,h:b.height,vw:innerWidth,vh:innerHeight,hit:!!t&&(t===e||e.contains(t)),tag:e.tagName,name:(e.innerText||e.value||e.getAttribute('aria-label')||'').trim().slice(0,40)}})()`);
  const inView = b => b.y >= 0 && b.y + b.h <= b.vh && b.x >= 0 && b.x + b.w <= b.vw && b.hit;

  // A curved path from the pointer to (x,y): 8–18 steps, fast start, slow landing.
  const path = (x, y) => {
    const steps = Math.round(rnd(8, 18)), sx = pointer.x, sy = pointer.y;
    const cx = (sx + x) / 2 + rnd(-40, 40), cy = (sy + y) / 2 + rnd(-40, 40);
    const pts = [];
    for (let i = 1; i <= steps; i++) { const t = i / steps, e = 1 - Math.pow(1 - t, 2); pts.push({ x: (1 - e) * (1 - e) * sx + 2 * (1 - e) * e * cx + e * e * x, y: (1 - e) * (1 - e) * sy + 2 * (1 - e) * e * cy + e * e * y }); }
    return pts;
  };
  const moveTo = async (x, y) => {
    for (const p of path(x, y)) { await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: p.x, y: p.y, button: 'none', buttons: 0, pointerType: 'mouse' }); pointer.x = p.x; pointer.y = p.y; await jitter(8, 22); }
  };
  const tp = (p, force) => ({ x: p.x, y: p.y, id: 1, radiusX: rnd(7, 12), radiusY: rnd(7, 12), force });
  const finger = async (from, to) => {
    const pts = [from, ...path.call(null, to.x, to.y)];
    await send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [tp(pts[0], rnd(0.4, 0.7))] });
    for (let i = 1; i < pts.length; i++) { await jitter(8, 20); await send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [tp(pts[i], rnd(0.4, 0.8))] }); }
    await jitter(40, 110);
    await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
    pointer.x = to.x; pointer.y = to.y;
  };

  // Wheel (or a finger swipe on the phone) until the element is in view. Never a JS scroll.
  const scrollTo = async (sel) => {
    let b = null;
    for (let i = 0; i < 14; i++) {
      b = await readBox(sel);
      if (!b) throw new Error(`human: no element for ${JSON.stringify(sel)}`);
      if (b.w < 2 || b.h < 2) throw new Error(`human: element has no size ${JSON.stringify(sel)}`);
      if (inView(b)) { // a wheel can still be gliding: take the box only when it has stopped moving
        await new Promise(r => setTimeout(r, 120)); const b2 = await readBox(sel);
        if (b2 && Math.abs(b2.x - b.x) < 2 && Math.abs(b2.y - b.y) < 2 && inView(b2)) return b2;
        continue;
      }
      const centre = b.y + b.h / 2 - b.vh / 2;
      const dy = Math.sign(centre) * Math.min(Math.abs(centre), rnd(200, 420));
      const at = { x: b.vw * rnd(0.35, 0.65), y: b.vh * rnd(0.35, 0.65) };
      if (touch) await finger({ x: at.x, y: b.vh * 0.62 }, { x: at.x + rnd(-10, 10), y: b.vh * 0.62 - dy });
      else { await moveTo(at.x, at.y); await send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: at.x, y: at.y, deltaX: 0, deltaY: dy, pointerType: 'mouse' }); }
      await jitter(90, 220);
    }
    throw new Error(`human: could not scroll ${JSON.stringify(sel)} into view`);
  };

  const click = async (sel) => {
    await jitter(150, 450);
    await front();
    const b = await scrollTo(sel);
    const hit = { x: b.x + b.w * rnd(0.3, 0.7), y: b.y + b.h * rnd(0.3, 0.7) };
    if (touch) {
      await finger({ x: hit.x + rnd(-2, 2), y: hit.y + rnd(-2, 2) }, hit);
    } else {
      await moveTo(hit.x, hit.y);
      await jitter(60, 180);
      await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: hit.x, y: hit.y, button: 'left', buttons: 1, pointerType: 'mouse', clickCount: 1 });
      await jitter(50, 130);
      await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: hit.x, y: hit.y, button: 'left', buttons: 0, pointerType: 'mouse', clickCount: 1 });
    }
    log(`${touch ? 'tap' : 'click'} ${b.tag} "${b.name}"`);
    await jitter(200, 600);
    return hit;
  };

  const shift = (type, modifiers) => send('Input.dispatchKeyEvent', { type, key: 'Shift', code: 'ShiftLeft', windowsVirtualKeyCode: 16, nativeVirtualKeyCode: 16, modifiers, location: 1 });
  const pressChar = async (ch) => {
    const d = keyOf(ch);
    const gap = rnd(55, 150), hold = Math.min(rnd(28, 70), gap - 15);
    if (d.shift) await shift('rawKeyDown', 8);
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: d.key, code: d.code, text: d.text, unmodifiedText: d.unmod || d.text, windowsVirtualKeyCode: d.vk, nativeVirtualKeyCode: d.vk, modifiers: d.shift ? 8 : 0 });
    await sleep(hold);
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: d.key, code: d.code, windowsVirtualKeyCode: d.vk, nativeVirtualKeyCode: d.vk, modifiers: d.shift ? 8 : 0 });
    if (d.shift) await shift('keyUp', 0);
    await sleep(gap - hold + (ch === ' ' ? rnd(30, 90) : 0));
    if (Math.random() < 0.04) await jitter(250, 700); // sometimes a person just stops to think
  };

  // Type key by key. Clears the box first with a real select-all + backspace.
  const type = async (sel, text, { clear = true } = {}) => {
    await click(sel);
    if (clear) {
      await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65, modifiers: 2, commands: ['selectAll'] });
      await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65, modifiers: 2 });
      await jitter(40, 90);
      await key('Backspace');
    }
    for (const ch of [...String(text)]) await pressChar(ch);
    log(`type ${JSON.stringify(sel)} (${[...String(text)].length} keys)`);
    await jitter(150, 400);
  };

  // One named key with no box in mind (Enter, Tab, Escape, ArrowDown, Backspace).
  const key = async (name) => {
    const base = { key: name, code: name, windowsVirtualKeyCode: VK[name], nativeVirtualKeyCode: VK[name] };
    await send('Input.dispatchKeyEvent', { type: 'keyDown', ...base, ...(name === 'Enter' ? { text: '\r' } : {}) });
    await jitter(40, 110);
    await send('Input.dispatchKeyEvent', { type: 'keyUp', ...base });
    await jitter(120, 350);
  };

  // Keys into whatever has focus, no click and no clearing first (a drop-down's type-to-find, a box already focused).
  const keys = async (text) => { for (const ch of [...String(text)]) await pressChar(ch); };

  const pause = (a = 250, b = 900) => jitter(a, b);
  const close = () => ws.close();

  // Settle: a page mints its first score token in the first instant. Give it a few seconds and one idle move
  // before the first real action, like a person reading the page. Skipped when HUMAN_SPEED=0.
  if (opts.settle !== false) {
    await front().catch(() => {});
    await jitter(1500, 3500);
    if (!touch) await moveTo(rnd(env.vw * 0.3, env.vw * 0.7), rnd(env.vh * 0.3, env.vh * 0.6));
  }

  return { click, type, key, keys, scrollTo, pause, evaluate, send, on, close, pointer, touch };
}

async function tabByUrl(port, needle) {
  const list = await (await fetch(`http://127.0.0.1:${port}/json`)).json();
  const t = list.find(o => o.type === 'page' && o.url.includes(needle));
  if (!t) throw new Error(`no tab matching ${needle} on port ${port}`);
  return t;
}

module.exports = { attach, tabByUrl, sleep, jitter };

if (require.main === module) {
  (async () => {
    const [,, needle, verb, sel, text] = process.argv;
    const port = process.env.CDP_PORT || 9222;
    const h = await attach(await tabByUrl(port, needle), { log: m => console.log('[human]', m) });
    const s = sel && sel.startsWith('text:') ? { text: new RegExp(sel.slice(5), 'i') } : sel;
    if (verb === 'click') await h.click(s);
    else if (verb === 'type') await h.type(s, text);
    else if (verb === 'key') await h.key(sel);
    else console.log('verbs: click <sel> | type <sel> <text> | key <Enter|Tab|Escape>');
    h.close();
  })().catch(e => { console.error(e.message); process.exit(1); });
}
