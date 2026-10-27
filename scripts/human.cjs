// human.cjs — the agent's hands, made to move like a person's. Plain CDP, no Playwright. Built 2026-10-26.
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
//   await h.pause();                                        // a short human pause (250–900 ms)
//   await h.scrollTo('#submit');                            // scroll the element into view, wheel steps
//   h.close();
//
// Command line test:
//   CDP_PORT=9222 node human.cjs <tabUrlSubstring> click '<selector>'
//   CDP_PORT=9222 node human.cjs <tabUrlSubstring> type '<selector>' '<text>'

const WebSocket = globalThis.WebSocket || (() => { try { return require('ws'); } catch { return require('/root/mbc-analytics/node_modules/ws'); } })();
const sleep = ms => new Promise(r => setTimeout(r, ms));
const rnd = (a, b) => a + Math.random() * (b - a);
const jitter = (a, b) => sleep(rnd(a, b));

// Where the pretend pointer is right now, per attached tab (so paths start from the last spot, like a real hand).
async function attach(tab, opts = {}) {
  const ws = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  let id = 0; const pend = {};
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m); delete pend[m.id]; } };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pend[i] = m => m.error ? rej(new Error(m.error.message)) : res(m.result); ws.send(JSON.stringify({ id: i, method, params })); });
  const evaluate = async (expression) => { const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true, userGesture: true }); if (r.exceptionDetails) throw new Error(r.exceptionDetails.text || 'page error'); return r.result.value; };
  await send('Page.enable'); await send('Runtime.enable');
  const pointer = { x: rnd(80, 300), y: rnd(120, 400) };
  const log = opts.log || (() => {});

  // Find the element. selector = CSS string, or {text:/regex/i, tag:'button'} to match visible text.
  const finder = (sel) => typeof sel === 'string'
    ? `document.querySelector(${JSON.stringify(sel)})`
    : `[...document.querySelectorAll(${JSON.stringify(sel.tag || 'button, a, [role=button], input[type=submit], label')})].filter(e=>e.getBoundingClientRect().height>0).find(e=>${sel.text.toString()}.test((e.innerText||e.value||e.getAttribute('aria-label')||'').trim()))`;

  // Centre of the element in viewport coords, with a little off-centre wobble like a thumb or a mouse.
  const where = async (sel) => {
    const r = await evaluate(`(()=>{const e=${finder(sel)}; if(!e) return null; e.scrollIntoView({block:'center',inline:'center'}); const b=e.getBoundingClientRect(); return {x:b.left,y:b.top,w:b.width,h:b.height,tag:e.tagName,name:(e.innerText||e.value||e.getAttribute('aria-label')||'').trim().slice(0,40)}})()`);
    if (!r) throw new Error(`human: no element for ${JSON.stringify(sel)}`);
    if (r.w === 0 || r.h === 0) throw new Error(`human: element has no size ${JSON.stringify(sel)}`);
    return { x: r.x + r.w * rnd(0.3, 0.7), y: r.y + r.h * rnd(0.3, 0.7), name: r.name, tag: r.tag };
  };

  // Move the pretend pointer along a slightly curved path in 8–18 steps, slower near the end.
  const moveTo = async (x, y) => {
    const steps = Math.round(rnd(8, 18));
    const sx = pointer.x, sy = pointer.y;
    const cx = (sx + x) / 2 + rnd(-40, 40), cy = (sy + y) / 2 + rnd(-40, 40); // one control point = a gentle curve
    for (let i = 1; i <= steps; i++) {
      const t = i / steps, e = 1 - Math.pow(1 - t, 2); // ease-out: fast start, slow landing
      const px = (1 - e) * (1 - e) * sx + 2 * (1 - e) * e * cx + e * e * x;
      const py = (1 - e) * (1 - e) * sy + 2 * (1 - e) * e * cy + e * e * y;
      await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: px, y: py, button: 'none' });
      await jitter(8, 22);
    }
    pointer.x = x; pointer.y = y;
  };

  const click = async (sel) => {
    await jitter(150, 450);
    const p = await where(sel);
    await moveTo(p.x, p.y);
    await jitter(60, 180); // hover a beat
    await send('Input.dispatchMouseEvent', { type: 'mousePressed', x: p.x, y: p.y, button: 'left', clickCount: 1 });
    await jitter(50, 130); // a real press lasts a moment
    await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: p.x, y: p.y, button: 'left', clickCount: 1 });
    log(`click ${p.tag} "${p.name}"`);
    await jitter(200, 600);
    return p;
  };

  // Type key by key. Clears the box first with a real select-all + backspace. Keeps Unicode and punctuation.
  const type = async (sel, text, { clear = true } = {}) => {
    await click(sel);
    if (clear) {
      await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'a', code: 'KeyA', modifiers: 2, commands: ['selectAll'] });
      await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'a', code: 'KeyA', modifiers: 2 });
      await jitter(40, 90);
      await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 });
      await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Backspace', code: 'Backspace', windowsVirtualKeyCode: 8 });
      await jitter(80, 160);
    }
    for (const ch of [...text]) {
      if (ch === '\n') {
        await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13, text: '\r' });
        await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter', windowsVirtualKeyCode: 13 });
      } else {
        await send('Input.dispatchKeyEvent', { type: 'keyDown', key: ch, text: ch, unmodifiedText: ch });
        await send('Input.dispatchKeyEvent', { type: 'keyUp', key: ch });
      }
      await jitter(ch === ' ' ? 90 : 55, ch === ' ' ? 220 : 150); // people pause a bit longer at spaces
      if (Math.random() < 0.04) await jitter(250, 700);              // and sometimes just stop to think
    }
    log(`type ${JSON.stringify(sel)} (${[...text].length} keys)`);
    await jitter(150, 400);
  };

  // Press one key with no box in mind (Enter, Tab, Escape, ArrowDown).
  const key = async (name) => {
    const codes = { Enter: 13, Tab: 9, Escape: 27, ArrowDown: 40, ArrowUp: 38, Backspace: 8 };
    const base = { key: name, code: name, windowsVirtualKeyCode: codes[name] };
    await send('Input.dispatchKeyEvent', { type: 'keyDown', ...base, ...(name === 'Enter' ? { text: '\r' } : {}) });
    await jitter(40, 110);
    await send('Input.dispatchKeyEvent', { type: 'keyUp', ...base });
    await jitter(120, 350);
  };

  // Scroll with wheel steps until the element is in view (pages watch scroll too).
  const scrollTo = async (sel) => {
    for (let i = 0; i < 12; i++) {
      const d = await evaluate(`(()=>{const e=${finder(sel)}; if(!e) return null; const b=e.getBoundingClientRect(); return b.top + b.height/2 - innerHeight/2})()`);
      if (d === null) throw new Error(`human: no element for ${JSON.stringify(sel)}`);
      if (Math.abs(d) < 120) return;
      await send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: pointer.x, y: pointer.y, deltaX: 0, deltaY: Math.sign(d) * Math.min(Math.abs(d), rnd(200, 420)) });
      await jitter(90, 220);
    }
  };

  const pause = () => jitter(250, 900);
  const close = () => ws.close();
  return { click, type, key, scrollTo, pause, evaluate, send, close, pointer };
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
