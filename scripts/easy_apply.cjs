// node easy_apply.cjs [keywords]  — one run: open Easy Apply jobs in order, skip any with questions, submit first resume-only one
const WebSocket=globalThis.WebSocket||require('ws'); const sleep=ms=>new Promise(r=>setTimeout(r,ms)); setTimeout(()=>{console.log('TIMEOUT');process.exit(3)},170000);
const KW=encodeURIComponent(process.argv[2]||'legal operations'); const PORT=process.env.CDP_PORT||9336;
(async()=>{const list=await (await fetch(`http://127.0.0.1:${PORT}/json`)).json(); const tab=list.find(o=>o.type==='page'&&o.url.includes('linkedin.com'))||list.find(o=>o.type==='page');
 const ws=new WebSocket(tab.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r); let id=0; const pend={};
 ws.onmessage=e=>{const m=JSON.parse(e.data); if(m.id&&pend[m.id]){pend[m.id](m); delete pend[m.id];}};
 const send=(m,p={})=>new Promise(res=>{const i=++id; pend[i]=res; ws.send(JSON.stringify({id:i,method:m,params:p}));});
 const ev=async(x)=>{const r=await send('Runtime.evaluate',{expression:x,awaitPromise:true,returnByValue:true,userGesture:true}); return r.result&&r.result.result?r.result.result.value:JSON.stringify(r).slice(0,200)};
 await send('Page.enable');
 const STATE=`(()=>{const vis=e=>e.getBoundingClientRect().height>0;const d=document.querySelector("[role=dialog]");if(!d)return {modal:false};const btns=[...d.querySelectorAll("button")].filter(vis);const pick=t=>btns.find(b=>t.test((b.innerText||"")+" "+(b.getAttribute("aria-label")||"")));const un=[];[...d.querySelectorAll("select")].filter(vis).forEach(s=>{if(/select an option/i.test(s.options[s.selectedIndex]?.text||"")||!s.value)un.push("select:"+(s.getAttribute("aria-label")||s.id).slice(0,40))});[...d.querySelectorAll("input[type=text],input[type=number],input:not([type]),textarea")].filter(vis).forEach(i=>{if(!i.value)un.push("text:"+(i.getAttribute("aria-label")||i.id||i.placeholder).slice(0,40))});const g={};[...d.querySelectorAll("input[type=radio]")].forEach(r=>{g[r.name]=g[r.name]||r.checked});Object.entries(g).forEach(([n,c])=>{if(!c)un.push("radio:"+n.slice(0,30))});const b=pick(/^Submit application/i)||pick(/^Review/i)||pick(/^Next/i)||pick(/^Continue/i);return {modal:true,un,next:b?(b.innerText||b.getAttribute("aria-label")).trim().slice(0,25):null,text:d.innerText.replace(/\\s+/g," ").slice(0,120)}})()`;
 const CLICK=t=>`(()=>{const vis=e=>e.getBoundingClientRect().height>0;const b=[...document.querySelectorAll("button")].filter(vis).find(b=>${t}.test((b.innerText||"")+" "+(b.getAttribute("aria-label")||"")));if(!b)return false;b.click();return true})()`;
 const DISMISS=async()=>{await ev(CLICK('/^Dismiss|^Close|Dismiss$/i')); await sleep(1200); await ev(CLICK('/^Discard/i')); await sleep(1200);};
 await send('Page.navigate',{url:`https://www.linkedin.com/jobs/search/?f_AL=true&keywords=${KW}&location=United%20States`}); await sleep(6000);
 const cards=await ev('[...document.querySelectorAll("a[href*=\\"/jobs/view/\\"]")].map(a=>(a.href.match(/jobs\\/view\\/(\\d+)/)||[])[1]).filter(Boolean).filter((v,i,a)=>a.indexOf(v)===i).slice(0,8)');
 console.log('jobs:', cards);
 for(const jid of cards){
   await send('Page.navigate',{url:'https://www.linkedin.com/jobs/view/'+jid+'/'}); await sleep(5000);
   const title=await ev('(document.querySelector("h1")||{}).innerText||document.title');
   const ea=await ev(CLICK('/^Easy Apply/i')); if(!ea){console.log('skip (no Easy Apply):', title); continue;} await sleep(3000);
   let done=false, reason='';
   for(let step=0;step<8;step++){
     const st=JSON.parse(await ev('JSON.stringify('+STATE+')'));
     if(!st.modal){reason='modal gone'; break;}
     if(st.un.length){reason='questions: '+st.un.join(', '); break;}
     if(!st.next){reason='no button: '+st.text; break;}
     await ev(CLICK('/^'+st.next.split(' ')[0]+'/i')); await sleep(2500);
     if(/^Submit/.test(st.next)){done=true; break;}
   }
   if(done){ await sleep(2500); console.log('SUBMITTED:', title, '|', await ev('(()=>{const d=document.querySelector("[role=dialog]");return (d?d.innerText:document.body.innerText).replace(/\\s+/g," ").slice(0,140)})()')); break; }
   console.log('skip:', title, '|', reason); await DISMISS();
 }
 ws.close(); process.exit(0);})();
