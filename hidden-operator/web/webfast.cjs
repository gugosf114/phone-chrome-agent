// webfast.cjs — the learn-once / fire-fast web engine.
//   observe <tab>                    list interactive elements + stable selectors
//   run <tab> <skill.json> [--arm]   fire a saved recipe fast; time each step; STOP before buy/pay unless --arm
// A skill is JSON: {"goal":"...","steps":[{do,...}]}. Step kinds:
//   {"do":"goto","url":"..."}  {"do":"clickText","text":".."}  {"do":"clickSel","sel":".."}
//   {"do":"fill","sel":"..","value":".."}  {"do":"waitText","text":".."}  {"do":"waitSel","sel":".."}
//   {"do":"assert","text":".."}   (a proof the step worked)
const WebSocket=require('ws'), fs=require('fs');
const {spawnSync}=require('child_process');
const {followStep, noteHit, writeButton, jobHappened}=require('./glance.cjs');
const port=process.env.CDP_PORT||'9222';
const [,, cmd, tab, arg3]=process.argv;
const ARM=process.argv.includes('--arm');
const STRICT=/\b(buy|pay|checkout|place order|confirm|reserve|book now|purchase|submit order|complete order)\b/i;
function conn(id){ return new Promise((res,rej)=>{ const ws=new WebSocket(`ws://127.0.0.1:${port}/devtools/page/${id}`); let n=0; const w={}; ws.on('open',()=>res({
  send:(m,p={})=>new Promise(r=>{const i=++n;w[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p}));}),
  close:()=>ws.close()})); ws.on('message',m=>{const d=JSON.parse(m); if(d.id&&w[d.id]){w[d.id](d);delete w[d.id];}}); ws.on('error',rej); }); }
const evaljs=async(c,expr)=>{ const r=await c.send('Runtime.evaluate',{expression:expr,returnByValue:true,awaitPromise:true,userGesture:true}); if(r.result&&r.result.exceptionDetails) throw new Error(r.result.exceptionDetails.exception?.description||'js error'); return r.result&&r.result.result?r.result.result.value:null; };
const OBSERVE=`(()=>{const out=[];const els=[...document.querySelectorAll('a,button,input,select,textarea,[role=button],[onclick]')];
for(const e of els){const r=e.getBoundingClientRect(); if(r.width<2||r.height<2) continue; if(r.bottom<0||r.top>innerHeight*3) continue;
let sel=e.id?('#'+CSS.escape(e.id)):(e.name?e.tagName.toLowerCase()+'[name="'+e.name+'"]':'');
out.push({tag:e.tagName.toLowerCase(),type:e.type||'',text:(e.innerText||e.value||e.placeholder||e.getAttribute('aria-label')||'').trim().slice(0,50),sel,href:(e.href||'').slice(0,60)});}
return out.slice(0,60);})()`;
const CLICKTEXT=t=>`(()=>{const t=${JSON.stringify(t)}.toLowerCase();const els=[...document.querySelectorAll('a,button,[role=button],input[type=submit],[onclick]')];
const hit=els.find(e=>((e.innerText||e.value||e.getAttribute('aria-label')||'').trim().toLowerCase()===t));
if(!hit)return 'MISS';hit.scrollIntoView({block:'center'});hit.click();return 'OK';})()`;
const has=t=>`document.body.innerText.toLowerCase().includes(${JSON.stringify(t.toLowerCase())})`;
async function waitFor(c,expr,ms=8000){const end=Date.now()+ms;while(Date.now()<end){try{if(await evaljs(c,expr))return true;}catch(e){}await new Promise(r=>setTimeout(r,120));}return false;}
function envModel(packet){
  if(!process.env.REPAIR_CMD) return '';
  const result=spawnSync(process.env.REPAIR_CMD,[],{input:JSON.stringify(packet),encoding:'utf8'});
  return ((result.stdout||'').trim().split('\n')[0])||'';
}
async function shot(c){
  try{ const reply=await c.send('Page.captureScreenshot',{format:'jpeg',quality:40}); return reply.result&&reply.result.data||null; }
  catch(e){ return null; }
}
(async()=>{
 const targets=await (await fetch(`http://127.0.0.1:${port}/json`)).json();
 const id=tab; const c=await conn(id); await c.send('Page.enable'); await c.send('Runtime.enable');
 if(cmd==='observe'){ const els=await evaljs(c,OBSERVE); console.log(JSON.stringify(els,null,1)); c.close(); return; }
 if(cmd==='run'){ const skill=JSON.parse(fs.readFileSync(arg3,'utf8')); console.log('GOAL:',skill.goal); const t0=Date.now();
   const actions=[]; let book=skill.book||{}; const failures=skill.failures||[]; let dirty=false;
   const model=process.env.REPAIR_CMD?envModel:null;
   for(const [i,s] of skill.steps.entries()){ const st=Date.now(); let res='';
     const label=s.text||s.sel||s.url||s.do;
     if((STRICT.test(s.do)||STRICT.test(label))&&!ARM){ console.log(`step ${i} ${s.do} "${label}" -> STOPPED (money step; needs --arm)`); break; }
     if(s.do==='goto'){ await c.send('Page.navigate',{url:s.url}); res=await waitFor(c,'document.readyState==="complete"')?'loaded':'timeout'; }
     else if(s.do==='clickText'||s.do==='clickSel'){
       const wanted=s.saved||s.text;
       if(wanted){
         const seen=await evaljs(c,OBSERVE);
         const controls=(Array.isArray(seen)?seen:[]).map((item,index)=>({id:item.sel||String(index),text:item.text||''}));
         let decision=followStep(skill.goal,s,controls,actions,null,failures,null,i);
         if(decision.action==='stop'){
           const picture=await shot(c);
           decision=followStep(skill.goal,s,controls,actions,model,failures,picture,i);
         }
         if(decision.action==='stop'){
           res='MISS';
           if(decision.rejected) failures.push({page:controls.map(item=>item.text||'').filter(Boolean).sort().join('|').toLowerCase(),button:decision.rejected,step:i});
           actions.push({step:i,status:'missed',cause:decision.reason});
           console.log(JSON.stringify(decision.packet||{instruction:skill.goal,observations:[{controls,picture:Boolean(decision.picture)}],actions}));
         } else {
           res=await evaljs(c,CLICKTEXT(decision.matched));
           if(res==='OK'){
             await waitFor(c,'document.readyState==="complete"',6000);
             let happened=null;
             if(s.check){
               const body=await evaljs(c,'(document.body&&document.body.innerText)||""');
               happened=jobHappened(s, body||'');
               if(happened===false){
                 res='FAIL';
                 actions.push({step:i,status:'missed',cause:'the job did not happen'});
                 console.log('the job did not happen');
                 console.log(`step ${i} ${s.do} "${label}" -> ${res} (${Date.now()-st}ms)`);
                 break;
               }
             }
             actions.push({step:i,status:'pressed'});
             if(decision.via==='model' && happened===true){
               const noted=noteHit(book,i,controls,decision.matched);
               book=noted.book;
               if(noted.admitted){ writeButton(skill.steps[i],noted.admitted); dirty=true; }
             }
           }
         }
       } else {
         res=await evaljs(c,`(()=>{const e=document.querySelector(${JSON.stringify(s.sel)});if(!e)return 'MISS';e.scrollIntoView({block:'center'});e.click();return 'OK';})()`);
       }
     }
     else if(s.do==='fill'){ res=await evaljs(c,`(()=>{const e=document.querySelector(${JSON.stringify(s.sel)});if(!e)return 'MISS';e.focus();const p=Object.getOwnPropertyDescriptor(e.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set;p.call(e,${JSON.stringify(s.value)});e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));return 'OK';})()`); }
     else if(s.do==='waitText'){ res=await waitFor(c,has(s.text))?'seen':'timeout'; }
     else if(s.do==='waitSel'){ res=await waitFor(c,`!!document.querySelector(${JSON.stringify(s.sel)})`)?'seen':'timeout'; }
     else if(s.do==='assert'){ res=await evaljs(c,has(s.text))?'PASS':'FAIL'; }
     const dt=Date.now()-st; console.log(`step ${i} ${s.do} "${label}" -> ${res} (${dt}ms)`);
     if(res==='MISS'||res==='FAIL'||res==='timeout'){ console.log('STOP: step did not prove out'); break; }
   }
   if(dirty){ skill.book=book; skill.failures=failures; fs.writeFileSync(arg3,JSON.stringify(skill,null,1)); }
   console.log('TOTAL',(Date.now()-t0),'ms'); c.close(); return; }
 console.log('usage: webfast.cjs observe <tab> | run <tab> <skill.json> [--arm]'); c.close();
})().catch(e=>{console.error('ERR',e.message);process.exit(1)});
