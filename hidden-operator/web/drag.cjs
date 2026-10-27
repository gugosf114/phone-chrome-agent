// drag.cjs — CDP mouse drag on headless tab. node drag.cjs <targetId> <sx> <sy> <tx> <ty>
const [,, targetId, sx, sy, tx, ty] = process.argv.map((v,i)=>i>=2?(i===2?v:Number(v)):v);
const WebSocket=globalThis.WebSocket||require('/root/mbc-analytics/node_modules/ws');
const PORT=process.env.CDP_PORT||'9222'; const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const ver=await (await fetch('http://127.0.0.1:'+PORT+'/json/version')).json();
  const ws=new WebSocket(ver.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
  let id=0; const pend={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
  const send=(method,params={},sessionId)=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method,params,sessionId}));});
  const {result:{sessionId:s}}=await send('Target.attachToTarget',{targetId,flatten:true});
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:2200,deviceScaleFactor:1,mobile:false},s);
  const M=(type,x,y,extra)=>send('Input.dispatchMouseEvent',Object.assign({type,x,y,button:'left',buttons:1,clickCount:1},extra||{}),s);
  const steps=12;
  await M('mouseMoved',sx,sy,{buttons:0}); await sleep(60);
  await M('mousePressed',sx,sy); await sleep(120);
  for(let i=1;i<=steps;i++){ const x=Math.round(sx+(tx-sx)*i/steps), y=Math.round(sy+(ty-sy)*i/steps); await M('mouseMoved',x,y); await sleep(40); }
  await M('mouseMoved',tx,ty); await sleep(120);
  await M('mouseReleased',tx,ty); await sleep(150);
  console.log('drag done', sx,sy,'->',tx,ty);
  ws.close(); process.exit(0);
})().catch(e=>{console.error('ERR',e.message); process.exit(1);});
