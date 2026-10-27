#!/usr/bin/env python3
"""picks_sync.py <picks.json> — after the picker writes a picks file, run this once.
- every "no" goes into scripts/no.json (the finder never shows that job again)
- prints the ASK lines for George, one per line
- prints the walker command with the yes ids
Built 2026-10-27. Idempotent."""
import json, sys, os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
picks_f = sys.argv[1] if len(sys.argv) > 1 else sys.exit("usage: picks_sync.py picks/picks-<stamp>.json")
picks = json.load(open(picks_f)); no_f = os.path.join(root, 'scripts/no.json')
no = json.load(open(no_f)) if os.path.exists(no_f) else {}
yes, ask, added = [], [], 0
for jid, p in picks.items():
    if jid.startswith('_') or not isinstance(p, dict): continue   # notes like "_run" ride along in the picks file
    d = (p.get('decision') or '').lower()
    if d == 'no':
        if jid not in no: no[jid] = p.get('skip') or p.get('why') or 'picker: no'; added += 1
    elif d == 'yes': yes.append(jid)
    elif d == 'ask': ask.append(f"{jid}: {p.get('ask') or p.get('why') or '?'}")
json.dump(no, open(no_f, 'w'), indent=1); open(no_f, 'a').write('\n')
print(f"no.json: +{added} (now {len(no)})")
if ask: print("\nASK George:"); [print("  " + a) for a in ask]
missing = [j for j in yes if not (picks[j].get('resume_file') or os.path.exists(os.path.join(root, 'apply', j, 'meta.json')))]
if missing: print("\nyes jobs with NO apply/<jobId>/ folder yet (make the resume + letter first):", ", ".join(missing))
if yes:
    print(f"\nwalk ({len(yes)} yes):\n  CDP_PORT=19222 node scripts/map_easy_apply.cjs --ids {','.join(yes)} --jobs {len(yes)} --overrides {picks_f}")
