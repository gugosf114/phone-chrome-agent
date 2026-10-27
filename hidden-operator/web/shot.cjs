// shot.cjs [outfile] — screenshot the hidden Chrome's active tab as it really renders (no emulation). Default out: /root/hchrome/logs/shot.png
const WebSocket = globalThis.WebSocket || require('/root/mbc-analytics/node_modules/ws');
const fs=require('fs'); const out=process.argv[2]||'/root/hchrome/logs/shot.png';
(async()=>{
  const list=await (await fetch('http://127.0.0.1:9222/json/list')).json();
  const page=list.find(t=>t.type==='page'&&!/CheckConnection|about:blank/.test(t.url))||list.find(t=>t.type==='page');
  if(!page){ console.log('no page'); process.exit(1); }
  const ws=new WebSocket(page.webSocketDebuggerUrl); await new Promise((r,j)=>{ws.onopen=r; ws.onerror=j;});
  let id=0; const pend={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
  const send=(method,params={})=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method,params}));});
  const r=await send('Page.captureScreenshot',{format:'png'});
  fs.writeFileSync(out,Buffer.from(r.result.data,'base64'));
  const t=await send('Runtime.evaluate',{expression:'document.title+" | "+innerWidth+"x"+innerHeight+" | "+location.href.slice(0,90)',returnByValue:true});
  console.log(out, '|', t.result.result.value); ws.close(); process.exit(0);
})().catch(e=>{console.error('ERR',e.message); process.exit(1);});
