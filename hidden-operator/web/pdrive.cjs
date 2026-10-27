// pdrive.cjs — drive the REAL phone Chrome (CDP 9333) with NO emulation/UA override,
// so the page keeps the true Samsung mobile fingerprint. Attaches to the active tab
// (or the one whose URL matches $MATCH), runs JS steps, dumps text/json/png.
//   node pdrive.cjs <match|active> <waitMs> <outBase> <stepB64>...
// step prefixes: EVAL(default), NAV:<url>, TYPE:<text>, KEY:<name>
let [,, match, waitMsStr, outBase, ...steps] = process.argv;
const fs=require('fs'); const WebSocket=globalThis.WebSocket||require('/root/mbc-analytics/node_modules/ws');
const PORT=process.env.CDP_PORT||'9333';
const waitMs=parseInt(waitMsStr||'4000',10); const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const list=await (await fetch('http://127.0.0.1:'+PORT+'/json')).json();
  const pages=list.filter(t=>t.type==='page');
  let page = (match && match!=='active') ? pages.find(p=>(p.url||'').includes(match)) : null;
  if(!page) page = pages.find(p=>!/^chrome-|devtools|about:blank/.test(p.url||'')) || pages[0];
  if(!page){ console.log('no page'); process.exit(1); }
  const ws=new WebSocket(page.webSocketDebuggerUrl); await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
  let id=0; const pend={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
  const send=(method,params={})=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method,params}));});
  await send('Page.enable'); await send('Runtime.enable');
  const log=[];
  for(const [i,b64] of steps.entries()){
    const expr=Buffer.from(b64,'base64').toString('utf8');
    if(expr.startsWith('NAV:')){ await send('Page.navigate',{url:expr.slice(4)}); await sleep(waitMs); log.push({step:i,result:'nav'}); continue; }
    if(expr.startsWith('TYPE:')){ await send('Input.insertText',{text:expr.slice(5)}); await sleep(Math.min(waitMs,1500)); log.push({step:i,result:'typed'}); continue; }
    if(expr.startsWith('KEY:')){ const key=expr.slice(4); const map={Enter:{code:'Enter',key:'Enter',windowsVirtualKeyCode:13,text:'\r'}}; const k=map[key]||{key}; await send('Input.dispatchKeyEvent',Object.assign({type:'keyDown'},k)); await send('Input.dispatchKeyEvent',Object.assign({type:'keyUp'},k)); await sleep(Math.min(waitMs,1500)); log.push({step:i,result:'key'}); continue; }
    const r=await Promise.race([send('Runtime.evaluate',{expression:expr,awaitPromise:true,returnByValue:true}), sleep(parseInt(process.env.EVAL_TIMEOUT||'20000')).then(()=>({timeout:true}))]);
    const v=r.result&&r.result.result?r.result.result.value:(r.error||r.timeout||null);
    await sleep(waitMs);
    log.push({step:i,result:v});
  }
  fs.writeFileSync(outBase+'.log.json',JSON.stringify(log,null,1));
  try{ const shot=await send('Page.captureScreenshot',{format:'png'}); if(shot.result) fs.writeFileSync(outBase+'.png',Buffer.from(shot.result.data,'base64')); }catch(e){}
  const u=await send('Runtime.evaluate',{expression:'location.href',returnByValue:true});
  console.log('URL', u.result&&u.result.result?u.result.result.value:'?');
  ws.close(); process.exit(0);
})().catch(e=>{console.error('ERR',e.message); process.exit(1);});
