// cap.cjs — reliably capture Swagbucks survey launch URLs by installing a fetch/XHR
// hook BEFORE the surveys page loads (Page.addScriptToEvaluateOnNewDocument), then
// navigating and reading window.__net. Prints the survey-click URLs with pout.
//   CDP_PORT=9222 node cap.cjs <targetId> <outfile>
const [,, targetId, out] = process.argv;
const WebSocket=globalThis.WebSocket||require('/root/mbc-analytics/node_modules/ws');
const fs=require('fs'); const PORT=process.env.CDP_PORT||'9222'; const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const HOOK=`(function(){window.__net=[];var g=function(t){try{if(/survey-click|projectid/i.test(t))window.__net.push(t);}catch(e){}};
try{var _f=window.fetch;window.fetch=function(){var a=arguments;return _f.apply(this,a).then(function(res){res.clone().text().then(g);return res;});};}catch(e){}
try{var xo=XMLHttpRequest.prototype.open,xs=XMLHttpRequest.prototype.send;XMLHttpRequest.prototype.open=function(m,u){this.__u=u;return xo.apply(this,arguments);};XMLHttpRequest.prototype.send=function(){var s=this;s.addEventListener('load',function(){g(s.responseText);});return xs.apply(this,arguments);};}catch(e){}})();`;
(async()=>{
  const ver=await (await fetch('http://127.0.0.1:'+PORT+'/json/version')).json();
  const ws=new WebSocket(ver.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
  let id=0; const pend={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
  const send=(method,params={},sessionId)=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method,params,sessionId}));});
  const {result:{sessionId:s}}=await send('Target.attachToTarget',{targetId,flatten:true});
  await send('Page.enable',{},s); await send('Runtime.enable',{},s);
  await send('Page.addScriptToEvaluateOnNewDocument',{source:HOOK},s);
  await send('Page.navigate',{url:'https://www.swagbucks.com/surveys'},s);
  await sleep(9000);
  const r=await send('Runtime.evaluate',{expression:'JSON.stringify(window.__net||[])',returnByValue:true},s);
  fs.writeFileSync(out, (r.result&&r.result.result&&r.result.result.value)||'[]');
  console.log('captured bytes', fs.statSync(out).size);
  ws.close(); process.exit(0);
})().catch(e=>{console.error('ERR',e.message); process.exit(1);});
