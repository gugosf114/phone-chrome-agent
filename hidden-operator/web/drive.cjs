// node cdpflow.cjs <url> <waitMs> <outBase> <stepB64>... ; each step = JS expr evaluated in page (may navigate); sleeps waitMs after each; dumps text/url/png
let [,, url, waitMsStr, outBase, ...steps] = process.argv; if(steps[0]&&steps[0].startsWith('@')){ steps=require('fs').readFileSync(steps[0].slice(1),'utf8').split(/\s+/).filter(Boolean); }
const fs=require('fs'); const WebSocket=globalThis.WebSocket||require('ws');
const waitMs=parseInt(waitMsStr||'8000',10); const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36';
(async()=>{
  const ver=await (await fetch('http://127.0.0.1:'+(process.env.CDP_PORT||'9222')+'/json/version')).json();
  const ws=new WebSocket(ver.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
  let id=0; const pend={}; ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
  const send=(method,params={},sessionId)=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method,params,sessionId}));});
  let targetId; if(url.startsWith('target:')){ targetId=url.slice(7); } else { const ct=await send('Target.createTarget',{url:'about:blank'}); targetId=ct.result.targetId; }
  const {result:{sessionId:s}}=await send('Target.attachToTarget',{targetId,flatten:true});
  await send('Network.setUserAgentOverride',{userAgent:UA},s);
  await send('Emulation.setDeviceMetricsOverride',{width:1400,height:2200,deviceScaleFactor:1,mobile:false},s);
  await send('Page.enable',{},s); if(!url.startsWith('target:')){ await send('Page.navigate',{url},s); await sleep(waitMs); }
  const log=[];
  for(const [i,b64] of steps.entries()){
    const expr=Buffer.from(b64,'base64').toString('utf8');
    if(expr.startsWith('KEY:')){ const key=expr.slice(4); const map={Enter:{code:'Enter',key:'Enter',windowsVirtualKeyCode:13,text:'\r'},ArrowDown:{code:'ArrowDown',key:'ArrowDown',windowsVirtualKeyCode:40},Tab:{code:'Tab',key:'Tab',windowsVirtualKeyCode:9},Escape:{code:'Escape',key:'Escape',windowsVirtualKeyCode:27}}; const k=map[key]||{key,text:key};
      await send('Input.dispatchKeyEvent',Object.assign({type:'keyDown'},k),s); await send('Input.dispatchKeyEvent',Object.assign({type:'keyUp'},k),s); await sleep(Math.min(waitMs,2500)); log.push({step:i,result:'key '+key}); continue; }
    if(expr.startsWith('KEYS:')){ const text=expr.slice(5); for(const ch of text){ const isAlnum=/^[A-Za-z0-9]$/.test(ch); const code=isAlnum?ch.toUpperCase().charCodeAt(0):undefined; const down={type:'keyDown',text:ch,unmodifiedText:ch,key:ch}; const up={type:'keyUp',key:ch}; if(code){down.windowsVirtualKeyCode=code; up.windowsVirtualKeyCode=code;} await send('Input.dispatchKeyEvent',down,s); await send('Input.dispatchKeyEvent',up,s); await sleep(40);} await sleep(Math.min(waitMs,2000)); log.push({step:i,result:'keys '+text.length}); continue; }
    if(expr.startsWith('TDRAG:')){ const p=expr.slice(6).split(',').map(Number); const sx=p[0],sy=p[1],tx=p[2],ty=p[3];
      await send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:1},s);
      try{ await send('Emulation.setEmitTouchEventsForMouse',{enabled:true,configuration:'mobile'},s); }catch(e){}
      const TT=(type,x,y)=>send('Input.dispatchTouchEvent',{type,touchPoints:type==='touchEnd'?[]:[{x,y}]},s);
      await TT('touchStart',sx,sy); await sleep(180);
      for(let j=1;j<=14;j++){ await TT('touchMove',Math.round(sx+(tx-sx)*j/14),Math.round(sy+(ty-sy)*j/14)); await sleep(45); }
      await TT('touchMove',tx,ty); await sleep(220); await TT('touchEnd',tx,ty); await sleep(200);
      log.push({step:i,result:'tdrag '+sx+','+sy+'->'+tx+','+ty}); continue; }
    if(expr.startsWith('TYPE:')){ const text=expr.slice(5); await send('Input.insertText',{text},s); await sleep(Math.min(waitMs,2000)); log.push({step:i,result:'typed '+text.length}); continue; }
    if(expr.startsWith('MOUSE:')){ const ex=expr.slice(6); const ft=await send('Page.getFrameTree',{},s); const frames=[]; (function walk(n){frames.push(n.frame); (n.childFrames||[]).forEach(walk);})(ft.result.frameTree);
      let pt=null, info=[]; for(const f of frames){ try{ const iw=await send('Page.createIsolatedWorld',{frameId:f.id},s); const cid=iw.result&&iw.result.executionContextId; if(!cid) continue; const rr=await send('Runtime.evaluate',{expression:ex,contextId:cid,returnByValue:true,awaitPromise:true},s); const v=rr.result&&rr.result.result?rr.result.result.value:null; info.push({url:(f.url||'').slice(0,80),v}); if(v&&typeof v.x==='number'&&!pt){ pt=v; } }catch(e){} }
      let res='no point'; if(pt){ for(const type of ['mouseMoved','mousePressed','mouseReleased']) await send('Input.dispatchMouseEvent',{type,x:pt.x,y:pt.y,button:'left',clickCount:1},s); res='clicked '+pt.x+','+pt.y; }
      await sleep(waitMs); const u0=await send('Runtime.evaluate',{expression:'location.href',returnByValue:true},s); log.push({step:i,result:res,info,url:u0.result&&u0.result.result?u0.result.result.value:null}); continue; }
    if(expr.startsWith('ALLFRAMES:')){ const ex=expr.slice(10); const ft=await send('Page.getFrameTree',{},s); const frames=[]; (function walk(n){frames.push(n.frame); (n.childFrames||[]).forEach(walk);})(ft.result.frameTree);
      const out=[]; for(const f of frames){ try{ const iw=await send('Page.createIsolatedWorld',{frameId:f.id},s); const cid=iw.result&&iw.result.executionContextId; if(!cid){out.push({url:f.url,err:'no ctx'}); continue;} const rr=await send('Runtime.evaluate',{expression:ex,contextId:cid,returnByValue:true,awaitPromise:true},s); out.push({url:(f.url||'').slice(0,100),v:rr.result&&rr.result.result?rr.result.result.value:rr.error}); }catch(e){out.push({url:f.url,err:String(e)});} }
      await sleep(waitMs); log.push({step:i,frames:out}); continue; }
    if(expr.startsWith('FILE:')){ let path=expr.slice(5); let selJs='(function f(root){let x=root.querySelector("input[type=file]"); if(x) return x; for(const el of root.querySelectorAll("*")){ if(el.shadowRoot){ const y=f(el.shadowRoot); if(y) return y; } } return null;})(document)'; if(path.includes('||')){ const parts=path.split('||'); path=parts[0]; selJs=parts[1]; }
      const fe=await send('Runtime.evaluate',{expression:selJs,returnByValue:false},s);
      const oid=fe.result&&fe.result.result&&fe.result.result.objectId;
      let res='no file input'; if(oid){ const sr=await send('DOM.setFileInputFiles',{files:[path],objectId:oid},s); res=sr.error?('ERR '+JSON.stringify(sr.error)):'file set'; }
      await sleep(waitMs); const u0=await send('Runtime.evaluate',{expression:'location.href',returnByValue:true},s); log.push({step:i,result:res,url:u0.result&&u0.result.result?u0.result.result.value:null}); continue; }
    const r=await Promise.race([send('Runtime.evaluate',{expression:expr,awaitPromise:true,returnByValue:true},s), sleep(30000).then(()=>({timeout:true}))]);
    const v=r.result&&r.result.result?r.result.result.value:(r.error||r.timeout||r);
    await sleep(waitMs);
    const u=await send('Runtime.evaluate',{expression:'location.href',returnByValue:true},s);
    log.push({step:i,result:v,url:u.result&&u.result.result?u.result.result.value:null});
  }
  const t=await send('Runtime.evaluate',{expression:'document.body?document.body.innerText:""',returnByValue:true},s);
  fs.writeFileSync(outBase+'.txt',(t.result&&t.result.result&&t.result.result.value)||'');
  fs.writeFileSync(outBase+'.log.json',JSON.stringify(log,null,1));
  const shot=await send('Page.captureScreenshot',{format:'png'},s); if(shot.result) fs.writeFileSync(outBase+'.png',Buffer.from(shot.result.data,'base64'));
  if(process.env.KEEP){ console.log('TARGET:'+targetId); } else { await send('Target.closeTarget',{targetId}); } ws.close(); process.exit(0);
})().catch(e=>{console.error('ERR',e); process.exit(1);});
