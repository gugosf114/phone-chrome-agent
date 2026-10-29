import csv,glob,collections,re,json,sys,datetime,os
X=sys.argv[1]; BOOK=sys.argv[2]
def norm(q):
    q=re.sub(r'<[^>]+>','',q); q=re.sub(r'\s+',' ',q).strip(); q=re.sub(r'[\s*:]+$','',q); return q.lower()
SKIPQ=re.compile(r'^(email address|mobile phone|phone country code|please submit a resume|please upload your resume|resume|photo|cover letter|description|dates|your title|company|school|degree|major|city|state|street|zip|country|postal|summary|headline|location \(city\)|geolocation|industry|job listing type|job linkedin id|job title|job company|public profile url|today.s date|middle name|initials|first name|last name|.*urn:li:)',re.I)
SKIPA=re.compile(r'^(urn:|\s*$|-?\d{6,}\.pdf|\[\]$|http|//)',re.I)
def parse(s):
    for part in s.split(' | '):
        if ':' not in part: continue
        if '?:' in part: q,a=part.split('?:',1); q+='?'
        else:
            q,a=part.rsplit(':',1)
            if a.startswith('//') or re.match(r'^\d{2}',a) and 'http' in part: q,a=part.split(':',1)
        yield q.strip(),a.strip()
def mdy(d):
    try: return datetime.datetime.strptime(d.split(',')[0],'%m/%d/%y').date().isoformat()
    except: return ''
hist=collections.defaultdict(lambda: collections.defaultdict(lambda: {'n':0,'last':''}))
rows=[]
for f in sorted(glob.glob(os.path.join(X,'Jobs/Job Applications*.csv'))): rows+=list(csv.DictReader(open(f,newline='',encoding='utf-8-sig')))
for x in rows:
    d=mdy(x.get('Application Date',''))
    for q,a in parse(x.get('Question And Answers','')):
        if SKIPQ.search(q) or SKIPA.search(a) or len(a)>200: continue
        e=hist[norm(q)][a]; e['n']+=1; e['last']=max(e['last'],d)
# LinkedIn prefill store: counts as one use, dated today
for f in glob.glob(os.path.join(X,'Job Applicant Saved Screening Question Responses*.csv')):
    for r in csv.DictReader(open(f,newline='',encoding='utf-8-sig')):
        q,a=r['Question'],r['Answer']
        if SKIPQ.search(q) or SKIPA.search(a): continue
        k=norm(q)
        if k not in hist: hist[k][a]={'n':1,'last':'prefill'}
out={}
for k,ans in hist.items():
    best=max(ans.items(), key=lambda kv:(kv[1]['n'],kv[1]['last']))
    o={'answer':best[0],'n':best[1]['n'],'last':best[1]['last']}
    others={a:v['n'] for a,v in ans.items() if a!=best[0]}
    if others: o['others']=others
    out[k]=o
book=json.load(open(BOOK))
book['history']=dict(sorted(out.items(), key=lambda kv:-kv[1]['n']))
book['_history_what']="George's own past Easy Apply answers, from his LinkedIn data export of 2026-10-29 (931 applications 2018-01 to 2026-09-04, Jobs/Job Applications*.csv) plus LinkedIn's saved screening prefill. Key = question text, lower-cased. 'answer' = the one he used most ('others' = the rest with counts). The walker checks an exact question match here after the per-job picks and before the regex rules (George 10/29: one book, most-used answer wins). Rebuild: scratchpad build_history.py."
json.dump(book,open(BOOK,'w'),indent=1,ensure_ascii=False)
print('history entries',len(out),'from',len(rows),'applications')
for k,o in list(book['history'].items())[:12]: print(o['n'],'|',k[:90],'=>',o['answer'][:60],o.get('others',''))
print('...'); 
for k in ['veteran status','disability','race/ethnicity','if required, would you be willing to relocate for this role?','how many years of work experience do you have with microsoft excel?','do you have client-facing consulting experience ?']:
    print(k,'=>',book['history'].get(k))
