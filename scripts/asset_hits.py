#!/usr/bin/env python3
"""asset_hits.py <gather.json> [--json out.json]
For every gathered job, scan title + description with me/triggers.json and print which of George's assets and receipts
the posting calls for, with the exact words that tripped each one. The picker reads this before deciding, so the link
"noise ordinance -> NoiseFile, public on Play" or "patent -> App. No. 64/100,336" is mechanical, not memory.
Also prints the resume lane the hits point to (ai-eval / legal-ops / compliance / ai-governance). Built 2026-10-27."""
import json, re, sys, os, collections
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
trig = json.load(open(os.path.join(root, 'me/triggers.json')))
assets = {k: v for k, v in trig.items() if not k.startswith('_')}
rx = {k: [re.compile(w, re.I) for w in v['words']] for k, v in assets.items()}
if len(sys.argv) < 2: sys.exit(__doc__)
g = json.load(open(sys.argv[1]))
out = {}
for p in g.get('postings', []):
    if p.get('error'): continue
    text = (p.get('title', '') + '\n' + p.get('desc', ''))
    hits = {}
    for name, pats in rx.items():
        words = sorted({m.group(0).lower() for r in pats for m in r.finditer(text)})
        if words: hits[name] = words
    lanes = collections.Counter(assets[n]['lane'] for n in hits if assets[n]['lane'] != 'any')
    lane = lanes.most_common(1)[0][0] if lanes else 'legal-ops'
    out[p['jobId']] = {'title': p.get('title', ''), 'company': p.get('company', ''), 'lane': lane,
                       'hits': {n: {'words': w, 'say': assets[n]['say'], 'status': assets[n]['status']} for n, w in hits.items()}}
    print(f"\n{p['jobId']}  {p.get('title','')[:55]} @ {p.get('company','')[:25]}   lane: {lane}")
    for n, w in hits.items(): print(f"   {n:32} <- {', '.join(w)[:90]}")
    if not hits: print("   (no asset words; pick on the dossier alone)")
if '--json' in sys.argv:
    o = sys.argv[sys.argv.index('--json') + 1]; json.dump(out, open(o, 'w'), indent=1); print(f"\nwrote {o}")
