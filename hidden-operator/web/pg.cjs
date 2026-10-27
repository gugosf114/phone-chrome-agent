// pg.cjs — talk straight to ONE tab of a Chrome (works on Android Chrome where drive.cjs hangs).
// usage: CDP_PORT=9333 node pg.cjs <tabId> <jsExpr | @file>      prints the value as JSON
//        CDP_PORT=9333 node pg.cjs <tabId> --type "<text>"        types into the focused field
const WebSocket=require('ws'); const fs=require('fs');
const port=process.env.CDP_PORT||'9333'; const [,, tab, a, b]=process.argv; // --fill <cssSelector> <text>: focus, select all, type like a person
const ws=new WebSocket(`ws://127.0.0.1:${port}/devtools/page/${tab}`); let id=0; const wait={};
const send=(method,params={})=>new Promise(r=>{const i=++id; wait[i]=r; ws.send(JSON.stringify({id:i,method,params}));});
ws.on('message',m=>{const d=JSON.parse(m); if(d.id&&wait[d.id]){wait[d.id](d); delete wait[d.id];}});
ws.on('error',e=>{console.log(JSON.stringify({error:String(e)})); process.exit(1);});
ws.on('open',async()=>{
  if(a==='--fill'){ const [sel,text]=[b,process.argv[5]]; const f=await send('Runtime.evaluate',{expression:`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return 'MISSING';e.scrollIntoView({block:'center'});e.focus();e.select&&e.select();return 'ok';})()`,returnByValue:true,userGesture:true}); if(f.result.result.value!=='ok'){console.log(JSON.stringify(sel+': MISSING'));} else { await send('Input.insertText',{text}); const v=await send('Runtime.evaluate',{expression:`document.querySelector(${JSON.stringify(sel)}).value`,returnByValue:true}); console.log(JSON.stringify(sel+' = '+v.result.result.value)); } }
  else if(a==='--key'){ const k={Enter:{key:'Enter',code:'Enter',windowsVirtualKeyCode:13,text:'\r'}}[b]; await send('Input.dispatchKeyEvent',{type:'keyDown',...k}); await send('Input.dispatchKeyEvent',{type:'keyUp',key:k.key,code:k.code,windowsVirtualKeyCode:k.windowsVirtualKeyCode}); console.log('"key"'); }
  else if(a==='--type'){ await send('Input.insertText',{text:b}); console.log('"typed"'); }
  else { const expr=a.startsWith('@')?fs.readFileSync(a.slice(1),'utf8'):a;
    const r=await send('Runtime.evaluate',{expression:expr,returnByValue:true,awaitPromise:true,userGesture:true});
    const ex=r.result&&r.result.exceptionDetails; console.log(JSON.stringify(ex?{exception:(ex.exception&&ex.exception.description)||ex.text}:(r.result&&r.result.result?r.result.result.value:r),null,1)); }
  ws.close(); process.exit(0);
});
setTimeout(()=>{console.log('"timeout"');process.exit(2);},25000);
