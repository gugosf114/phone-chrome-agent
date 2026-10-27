// ctouch.cjs — CDK drag via CDP TOUCH events. node ctouch.cjs <match> <sx> <sy> <tx> <ty>
const M=process.argv[2], SX=+process.argv[3], SY=+process.argv[4], TX=+process.argv[5], TY=+process.argv[6];
const WebSocket=globalThis.WebSocket||require('/root/mbc-analytics/node_modules/ws');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const list=await (await fetch('http://127.0.0.1:9222/json')).json();
  const page=list.find(t=>t.type==='page'&&(t.url||'').includes(M))||list.find(t=>t.type==='page');
  const ws=new WebSocket(page.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
  let id=0; const pend={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
  const send=(method,params={})=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method,params}));});
  await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1});
  await send('Runtime.evaluate',{expression:"[...document.querySelectorAll('img,.cdk-drag,a')].forEach(function(e){e.setAttribute('draggable','false');e.draggable=false;});'ok'"});
  const T=(type,x,y)=>send('Input.dispatchTouchEvent',{type,touchPoints:type==='touchEnd'?[]:[{x,y,id:0,radiusX:8,radiusY:8,force:1}]});
  await T('touchStart',SX,SY); await sleep(250);
  const N=18;
  for(let i=1;i<=N;i++){ const x=Math.round(SX+(TX-SX)*i/N), y=Math.round(SY+(TY-SY)*i/N); await T('touchMove',x,y); await sleep(70); }
  await T('touchMove',TX,TY); await sleep(300);
  await T('touchEnd',TX,TY); await sleep(400);
  const r=await send('Runtime.evaluate',{expression:"JSON.stringify({counts:[...document.querySelectorAll('.cdk-drop-list')].map(function(l){return l.querySelectorAll('.cdk-drag').length;}),done:!/drag and drop the number/i.test(document.body.innerText),body:(document.body.innerText||'').replace(/\\s+/g,' ').slice(0,60)})",returnByValue:true});
  console.log(r.result&&r.result.result?r.result.result.value:JSON.stringify(r.error));
  ws.close(); process.exit(0);
})().catch(e=>{console.error('ERR',e.message);process.exit(1);});
