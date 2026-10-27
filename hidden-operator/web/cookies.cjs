// cookies.cjs — copy every cookie from the phone's own Chrome (CDP via `adb forward tcp:9333 localabstract:chrome_devtools_remote`)
const WebSocket = globalThis.WebSocket || (()=>{ try { return require("ws"); } catch(e) { return require("/root/mbc-analytics/node_modules/ws"); } })();
// into the hidden Chrome (CDP 127.0.0.1:9222). Partial-tolerant: a cookie that will not store is skipped and counted, never a rollback.
// Env: SRC_PORT (default 9333), DST_PORT (default 9222).
async function cdp(port){
  let ver=null, err=null;
  for(let i=0;i<6 && !ver;i++){ try{ ver=await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); }catch(e){ err=e; await new Promise(r=>setTimeout(r,2000)); } }
  if(!ver) throw new Error(`no CDP on ${port}: ${err&&err.message}`);
  const ws=new WebSocket(ver.webSocketDebuggerUrl);
  await new Promise((r,j)=>{ws.onopen=r; ws.onerror=j;});
  let id=0; const pend={};
  ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
  const send=(method,params={})=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method,params}));});
  return {ws,send};
}
(async()=>{
  const src=await cdp(process.env.SRC_PORT||9333);
  const got=await src.send('Storage.getCookies',{});
  const cookies=(got.result&&got.result.cookies)||[];
  src.ws.close();
  if(!cookies.length){ console.log(JSON.stringify({source:0,error:got.error||'no cookies read'})); process.exit(2); }
  const dst=await cdp(process.env.DST_PORT||9222);
  let ok=0, fail=0; const failed={};
  for(const c of cookies){
    const k={name:c.name,value:c.value,domain:c.domain,path:c.path,secure:!!c.secure,httpOnly:!!c.httpOnly};
    if(c.expires && c.expires>0) k.expires=c.expires;
    if(c.sameSite) k.sameSite=c.sameSite;
    let res=await dst.send('Storage.setCookies',{cookies:[k]});
    if(res.error && k.sameSite){ delete k.sameSite; res=await dst.send('Storage.setCookies',{cookies:[k]}); }
    if(res.error){ fail++; failed[c.domain]=(failed[c.domain]||0)+1; } else ok++;
  }
  const after=await dst.send('Storage.getCookies',{});
  console.log(JSON.stringify({source:cookies.length,set:ok,failed:fail,nowInHidden:((after.result||{}).cookies||[]).length,failedDomains:Object.entries(failed).sort((a,b)=>b[1]-a[1]).slice(0,12)}));
  dst.ws.close(); process.exit(0);
})().catch(e=>{console.error('ERR',e); process.exit(1);});
