// setmetrics.cjs <match> <mode> — mode 'clear' clears device-metrics override; 'w,h,dpr' sets it.
// Then reads the cdk drag tile + drop-box rects and prints them. Keeps session only as long as needed.
const [,, match, mode] = process.argv;
const WebSocket=globalThis.WebSocket||require('/root/mbc-analytics/node_modules/ws');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const list=await (await fetch('http://127.0.0.1:9222/json')).json();
  const page=list.find(t=>t.type==='page'&&(t.url||'').includes(match))||list.find(t=>t.type==='page');
  const ws=new WebSocket(page.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
  let id=0; const pend={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
  const send=(method,params={})=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method,params}));});
  if(mode==='clear'){ await send('Emulation.clearDeviceMetricsOverride'); }
  else { const [w,h,d]=mode.split(',').map(Number); await send('Emulation.setDeviceMetricsOverride',{width:w,height:h,deviceScaleFactor:d,mobile:false}); }
  await sleep(700);
  const expr="(function(){function rect(e){var r=e.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};}var d=[...document.querySelectorAll('.cdk-drag')].filter(e=>e.getBoundingClientRect().width>30).map(rect);var L=[...document.querySelectorAll('.cdk-drop-list')];var box=L.find(l=>{var r=l.getBoundingClientRect();return Math.abs(r.width-r.height)<40&&r.width<300;});return JSON.stringify({dpr:window.devicePixelRatio,iw:window.innerWidth,ih:window.innerHeight,tiles:d,box:box?rect(box):null});})()";
  const r=await send('Runtime.evaluate',{expression:expr,returnByValue:true});
  console.log(r.result&&r.result.result?r.result.result.value:JSON.stringify(r.error));
  ws.close(); process.exit(0);
})().catch(e=>{console.error('ERR',e.message);process.exit(1);});
