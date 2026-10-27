// ot_book.cjs <searchTerm> — book first available table, fully scripted, self-timed.
const WebSocket=require('ws'),fs=require('fs');
const PORT=process.env.CDP_PORT||'9222'; const TERM=process.argv[2]||'San Jose';
const fs2=require('fs');
// identity comes from booker.env (JSON, gitignored) or env vars — never hardcoded/committed
let NAME={first:'First',last:'Last',email:'you@example.com',phone:'0000000000'};
try{Object.assign(NAME,JSON.parse(fs2.readFileSync(__dirname+'/booker.env','utf8')));}catch(e){}
NAME={first:process.env.BOOK_FIRST||NAME.first,last:process.env.BOOK_LAST||NAME.last,email:process.env.BOOK_EMAIL||NAME.email,phone:process.env.BOOK_PHONE||NAME.phone};
const t0=Date.now(); const mark=[];
const stamp=(l)=>{mark.push([l,Date.now()-t0]);};
(async()=>{
 const tab=(await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`,{method:'PUT'})).json()).id;
 fs.writeFileSync('/tmp/ot_tab2.txt',tab);
 const ws=new WebSocket(`ws://127.0.0.1:${PORT}/devtools/page/${tab}`); let n=0,w={};
 const s=(m,p={})=>new Promise(r=>{const i=++n;w[i]=r;ws.send(JSON.stringify({id:i,method:m,params:p}))});
 ws.on('message',m=>{const d=JSON.parse(m);if(d.id&&w[d.id]){w[d.id](d);delete w[d.id]}});
 await new Promise(r=>ws.on('open',r)); await s('Page.enable');
 const ev=async e=>{const r=await s('Runtime.evaluate',{expression:e,returnByValue:true,awaitPromise:true});return r.result&&r.result.result?r.result.result.value:null;};
 const settle=async(ms=6000)=>{const end=Date.now()+ms;while(Date.now()<end){if(await ev('document.readyState==="complete"'))return;await new Promise(r=>setTimeout(r,100));}};
 // 1) search
 const url=`https://www.opentable.com/s?covers=2&dateTime=2026-09-21T19%3A00%3A00&term=${encodeURIComponent(TERM)}`;
 await s('Page.navigate',{url}); await settle(); await new Promise(r=>setTimeout(r,2500)); stamp('search loaded');
 await ev(`(()=>{const b=[...document.querySelectorAll("button")].find(x=>/accept|agree/i.test(x.innerText));if(b)b.click();})()`);
 // 2) first available time slot + which restaurant
 const who=await ev(`(()=>{const a=[...document.querySelectorAll('a[role=button]')].find(x=>/\\d{1,2}:\\d{2}\\s?(AM|PM)/i.test(x.innerText)&&/reserve/i.test(x.getAttribute('aria-label')||''));
   if(!a)return null; const lbl=a.getAttribute('aria-label')||''; a.scrollIntoView({block:'center'}); a.click(); return lbl.slice(0,80);})()`);
 stamp('clicked time slot'); if(!who){console.log(JSON.stringify({error:'no slot for '+TERM,mark}));ws.close();process.exit(0);}
 fs.writeFileSync('/tmp/ot_who.txt',who);
 await settle(); await new Promise(r=>setTimeout(r,2500));
 // 3) seating step if present
 const seat=await ev(`(()=>{const b=[...document.querySelectorAll('button,a')].find(x=>/^select$/i.test(x.innerText.trim()));if(b){b.click();return 'selected';}return 'no-seating-step';})()`);
 if(seat==='selected'){await settle();await new Promise(r=>setTimeout(r,2500));}
 stamp('seating: '+seat);
 // 4) resilient finish loop: fill terms/name, click complete/confirm (top doc + auth iframe), until confirmed
 const finish=`(()=>{
   const acc=[document, ...[...document.querySelectorAll('iframe')].filter(f=>/authenticate/.test(f.src)).map(f=>f.contentDocument).filter(Boolean)];
   let acted=[];
   for(const doc of acc){
     const set=(el,v)=>{if(!el||el.value)return;const p=Object.getOwnPropertyDescriptor(el.constructor.prototype,'value').set;el.focus();p.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));el.dispatchEvent(new Event('blur',{bubbles:true}));};
     const tc=doc.querySelector('input[name=tcAccepted]'); if(tc&&!tc.checked){tc.click();acted.push('terms');}
     // advance through any "Choose options"/seating/specials page: pick Standard (free) or first Select
     if(!tc){ const sels=[...doc.querySelectorAll('button,a')].filter(x=>/^select$/i.test(x.innerText.trim()));
       if(sels.length){ const std=sels.find(b=>/standard/i.test((b.closest('[class*=card],li,section,div')||{}).innerText||'')); (std||sels[0]).click(); acted.push('advance'); } }
     const byph=t=>[...doc.querySelectorAll('input')].find(e=>new RegExp(t,'i').test((e.placeholder||e.getAttribute('aria-label')||'')));
     const fn=byph('first name'),ln=byph('last name'),em=byph('email');
     if(fn&&!fn.value){set(fn,'${NAME.first}');acted.push('first');} if(ln&&!ln.value){set(ln,'${NAME.last}');acted.push('last');} if(em&&!em.value){set(em,'${NAME.email}');acted.push('email');}
     const btn=[...doc.querySelectorAll('button')].find(x=>/complete reservation/i.test(x.innerText)&&!x.disabled);
     if(btn){btn.click();acted.push('complete');}
   }
   const confirmed=/reservation confirmed|you.re all set|is confirmed|cancel reservation|add to calendar/i.test(document.body.innerText);
   const needPhone=[...document.querySelectorAll('iframe')].some(f=>/authenticate/.test(f.src)) && /enter your phone number/i.test(document.body.innerText);
   return JSON.stringify({acted,confirmed,needPhone});
 })()`;
 let confirmed=false, needPhone=false;
 for(let i=0;i<40;i++){ const r=JSON.parse(await ev(finish)||'{}'); if(r.confirmed){confirmed=true;break;} if(r.needPhone){needPhone=true;break;} await new Promise(r=>setTimeout(r,400)); }
 stamp(confirmed?'CONFIRMED':(needPhone?'NEEDS PHONE CODE':'stalled'));
 const total=Date.now()-t0;
 console.log(JSON.stringify({restaurant:who,confirmed,needPhone,total_ms:total,marks:mark},null,1));
 ws.close();process.exit(0);
})().catch(e=>{console.log('ERR',e.message);process.exit(1)});
