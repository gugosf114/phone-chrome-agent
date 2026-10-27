// tdrag.cjs — CDP TOUCH drag on headless tab (for Angular CDK). node tdrag.cjs <targetId> <sx> <sy> <tx> <ty>
const [,, targetId, sx, sy, tx, ty] = [process.argv[2],process.argv[3],process.argv[4],process.argv[5],process.argv[6],process.argv[7]]
  .map((v,i)=>i===0?v:Number(v));
const WebSocket=globalThis.WebSocket||require('/root/mbc-analytics/node_modules/ws');
const PORT=process.env.CDP_PORT||'9222'; const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const ver=await (await fetch('http://127.0.0.1:'+PORT+'/json/version')).json();
  const ws=new WebSocket(ver.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
  let id=0; const pend={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
  const send=(method,params={},sessionId)=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method,params,sessionId}));});
  const {result:{sessionId:s}}=await send('Target.attachToTarget',{targetId,flatten:true});
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:2200,deviceScaleFactor:1,mobile:true},s);
  await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1},s);
  const T=(type,x,y)=>send('Input.dispatchTouchEvent',{type,touchPoints:type==='touchEnd'?[]:[{x,y}]},s);
  await T('touchStart',sx,sy); await sleep(150);
  const steps=14;
  for(let i=1;i<=steps;i++){ const x=Math.round(sx+(tx-sx)*i/steps), y=Math.round(sy+(ty-sy)*i/steps); await T('touchMove',x,y); await sleep(45); }
  await T('touchMove',tx,ty); await sleep(200);
  await T('touchEnd',tx,ty); await sleep(150);
  console.log('touch drag done', sx,sy,'->',tx,ty);
  ws.close(); process.exit(0);
})().catch(e=>{console.error('ERR',e.message); process.exit(1);});
