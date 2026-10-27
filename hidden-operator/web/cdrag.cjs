// cdrag.cjs — CDK pointer-drag via CDP trusted mouse events, in CSS coords, with native
// image-drag disabled first. node cdrag.cjs <match> <sx> <sy> <tx> <ty>
const [,, match, sx, sy, tx, ty] = [process.argv[2],+process.argv[3],+process.argv[4],+process.argv[5],+process.argv[6]] && process.argv;
const M=process.argv[2], SX=+process.argv[3], SY=+process.argv[4], TX=+process.argv[5], TY=+process.argv[6];
const WebSocket=globalThis.WebSocket||require('/root/mbc-analytics/node_modules/ws');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const list=await (await fetch('http://127.0.0.1:9222/json')).json();
  const page=list.find(t=>t.type==='page'&&(t.url||'').includes(M))||list.find(t=>t.type==='page');
  const ws=new WebSocket(page.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
  let id=0; const pend={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
  const send=(method,params={})=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method,params}));});
  const ev=(type,x,y,extra)=>send('Input.dispatchMouseEvent',Object.assign({type,x,y,button:'left',buttons:1,pointerType:'mouse',clickCount:1},extra||{}));
  await send('Runtime.evaluate',{expression:"[...document.querySelectorAll('img,.cdk-drag,a')].forEach(function(e){e.setAttribute('draggable','false');e.draggable=false;});'ok'"});
  await ev('mouseMoved',SX,SY,{buttons:0}); await sleep(120);
  await ev('mousePressed',SX,SY); await sleep(200);
  const N=18;
  for(let i=1;i<=N;i++){ const x=Math.round(SX+(TX-SX)*i/N), y=Math.round(SY+(TY-SY)*i/N); await ev('mouseMoved',x,y); await sleep(70); }
  await ev('mouseMoved',TX,TY); await sleep(250);
  await ev('mouseReleased',TX,TY); await sleep(400);
  const r=await send('Runtime.evaluate',{expression:"JSON.stringify({counts:[...document.querySelectorAll('.cdk-drop-list')].map(function(l){return l.querySelectorAll('.cdk-drag').length;}),done:!/drag and drop the number/i.test(document.body.innerText)})",returnByValue:true});
  console.log(r.result&&r.result.result?r.result.result.value:JSON.stringify(r.error));
  ws.close(); process.exit(0);
})().catch(e=>{console.error('ERR',e.message);process.exit(1);});
