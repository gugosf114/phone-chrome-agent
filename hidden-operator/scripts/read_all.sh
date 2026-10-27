#!/bin/bash
# read_all.sh — read a hidden-screen app like a web page: scroll and stitch, on the phone, in ONE adb round trip.
# Built 2026-10-26; v2 same night after a second model's review. The keyhole fix #2 (fix #1 is a tall screen:
# `hidden_display.sh start -n tall 1080 6000 420`, which lays out six screens of rows at once).
#
#   bash read_all.sh -n <screen> [max_pages=14] [--buttons]
#
# How: finds the biggest scrollable view in the reader's snapshot, scrolls it to the TOP with the accessibility action
# scroll_backward, then reads the tree, asks the view to scroll_forward one page, reads again, until Android answers
# "false" to scroll_forward = the real bottom. No swipe, so no fling and no pull-to-refresh. If the app has no scrollable
# view in the tree, it falls back to finger swipes and stops when two reads match.
# Rows cut by the screen edge are skipped (they come whole on the next page). Furniture (status bar, nav bar, taskbar,
# sticky titles = same text at the same spot on two pages) is dropped. Overlap is merged. You get ONE blob, in order.
# --buttons prints "text<TAB>cx cy" so a script can tap a stitched row later.
#
# Needs: the screen up with its reader (hidden_display.sh start/ensure). Files per screen in /data/local/tmp/vd/<name>/:
# tree.xml + snapshot.json (written on a11y events by the shared reader), request-<id>.json in / response-<id>.json out.
# Blank-tree apps: `dumpsys activity top` gives NO text on this Samsung (checked 10/26); use the photo fallback instead.
set -e
_HERE="$(cd "$(dirname "$0")" && pwd)"; . "$_HERE/phone_env.sh" 2>/dev/null || true; : "${ADB:=adb -s ${ANDROID_SERIAL:-127.0.0.1:5555}}"
NAME=main; while [ $# -gt 0 ]; do case "$1" in -n) NAME="$2"; shift 2;; --buttons) BTN=1; shift;; *) MAX="$1"; shift;; esac; done
MAX=${MAX:-14}; BASE=/data/local/tmp/vd; DIR="$BASE/$NAME"
ID=$($ADB shell "cat $DIR/id 2>/dev/null" | tr -d '\r'); [ -n "$ID" ] || { echo "[read_all] screen '$NAME' is not up" >&2; exit 1; }
read -r W H < <($ADB shell "wm size -d $ID 2>/dev/null | sed -n 's/.*: *\([0-9]*\)x\([0-9]*\).*/\1 \2/p' | tail -1" | tr -d '\r'); W=${W:-1080}; H=${H:-2400}
X=$((W/2)); Y1=$((H*72/100)); Y2=$((H*28/100))

# The whole loop runs on the phone (toybox sh): one adb shell, no round trip per page.
$ADB shell "I=$ID; D=$DIR; T=$DIR/tree.xml; S=$DIR/snapshot.json; HH=$H; MAXP=$MAX
extract(){ grep -o '<node [^>]*>' \$T 2>/dev/null | sed -n 's/.*text=\"\([^\"]*\)\".*desc=\"\([^\"]*\)\".*bounds=\"\[\([0-9-]*\),\([0-9-]*\)\]\[\([0-9-]*\),\([0-9-]*\)\]\".*cx=\"\([0-9]*\)\" cy=\"\([0-9]*\)\".*/\1\t\2\t\4\t\6\t\7 \8/p' | awk -F'\t' -v H=\$HH '{t=\$1; if(t==\"\")t=\$2; if(t==\"\")next; if(\$3<=0 || \$4>=H) next; print t \"\t\" \$5}'; }
# the list itself (RecyclerView/ListView/GridView) if there is one, else the biggest scrollable view; never a pager
target(){ grep -o '{[^{}]*\"scrollable\":true[^{}]*}' \$S 2>/dev/null | grep '\"visible\":true' | grep -v -i 'pager' | sed -n 's/.*\"token\":\"\([^\"]*\)\".*\"package\":\"\([^\"]*\)\".*\"class\":\"\([^\"]*\)\".*\"bounds\":\[\([0-9-]*\),\([0-9-]*\),\([0-9-]*\),\([0-9-]*\)\].*/\1 \2 \3 \4 \5 \6 \7/p' | awk '{a=(\$6-\$4)*(\$7-\$5); if(\$3 ~ /Recycler|ListView|GridView/) a=a*1000; if(a>best){best=a; out=\$1\" \"\$2}} END{print out}'; }
# ask the reader to perform one accessibility action; prints ok|end|err|none
act(){ a=\$1; tries=0
  while [ \$tries -lt 4 ]; do
    set -- \$(target); tok=\$1; pkg=\$2; [ -n \"\$tok\" ] || { echo none; return; }
    gen=\$(grep -o '\"generation\":\"[^\"]*\"' \$S | head -1 | cut -d'\"' -f4); rev=\$(grep -o '\"revision\":[0-9]*' \$S | head -1 | cut -d: -f2)
    rid=\$(head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n'); dl=\$(( \$(date +%s) + 6 ))000   # mksh math is 32-bit: seconds+6, then append 000 as text
    printf '{\"action\":\"%s\",\"token\":\"%s\",\"package\":\"%s\",\"display_id\":%s,\"generation\":\"%s\",\"revision\":%s,\"deadline_ms\":%s}' \"\$a\" \"\$tok\" \"\$pkg\" \"\$I\" \"\$gen\" \"\$rev\" \"\$dl\" > \$D/request-\$rid.json.tmp && mv \$D/request-\$rid.json.tmp \$D/request-\$rid.json
    k=0; while [ \$k -lt 40 ] && [ ! -f \$D/response-\$rid.json ]; do sleep 0.1; k=\$((k+1)); done
    r=\$(cat \$D/response-\$rid.json 2>/dev/null); rm -f \$D/response-\$rid.json
    case \"\$r\" in *'\"ok\":true'*) echo ok; return;; *'snapshot changed'*) tries=\$((tries+1)); sleep 0.3; continue;; *'\"dispatched\":true'*) echo end; return;; *) echo \"err \$r\" | tr -d '\n' | cut -c1-120; return;; esac
  done; echo err-retries; }
MODE=a11y; [ -n \"\$(target)\" ] || MODE=swipe
if [ \$MODE = a11y ]; then k=0; while [ \$k -lt 20 ]; do [ \"\$(act scroll_backward)\" = ok ] || break; k=\$((k+1)); sleep 0.35; done; sleep 0.9
else for k in 1 2 3; do input -d \$I swipe $X $Y2 $X $Y1 200; sleep 0.3; done; sleep 1.5; fi
echo \"@@MODE \$MODE\"
prev=''; n=0
while [ \$n -lt \$MAXP ]; do
  cur=\$(extract); echo \"\$cur\"; echo '@@PAGE@@'; n=\$((n+1))
  if [ \$MODE = a11y ]; then [ \"\$cur\" = \"\$prev\" ] && { echo '@@STOP end'; break; }; prev=\$cur; r=\$(act scroll_forward); [ \"\$r\" = ok ] || { echo \"@@STOP \$r\"; break; }; sleep 0.9
  else [ \"\$cur\" = \"\$prev\" ] && break; prev=\$cur; input -d \$I swipe $X $Y1 $X $Y2 \$((280 + \$RANDOM % 160)); sleep 1.2; fi
done
if [ \$MODE = a11y ]; then sleep 0.6; extract; echo '@@PAGE@@'; fi
" | tr -d '\r' | python3 -c '
import sys
from collections import Counter
raw=sys.stdin.read()
mode=next((l.split()[1] for l in raw.splitlines() if l.startswith("@@MODE")),"?"); stop=next((l[7:].strip() for l in raw.splitlines() if l.startswith("@@STOP")),"")
raw="\n".join(l for l in raw.splitlines() if not l.startswith("@@MODE") and not l.startswith("@@STOP"))
pages=[[r for r in p.strip("\n").split("\n") if r.strip()] for p in raw.split("@@PAGE@@") if p.strip()]
spot=Counter((r.split("\t")[0], r.split("\t")[1] if "\t" in r else "") for p in pages for r in set(p))
furn={k for k,c in spot.items() if len(pages)>=3 and c>=max(2,(len(pages)*3+4)//5)}   # on most pages; never with 1-2 pages
out=[]
for rows in pages:
    rows=[r for r in rows if (r.split("\t")[0], r.split("\t")[1] if "\t" in r else "") not in furn]
    texts=[r.split("\t")[0] for r in rows]; have=[o.split("\t")[0] for o in out]
    k=0
    for j in range(min(len(have),len(texts)),0,-1):
        if have[-j:]==texts[:j]: k=j; break
    if k==0 and have:
        last=set(have[-40:]); rows=[r for r in rows if r.split("\t")[0] not in last]
    out.extend(rows[k:])
clean=[]
for r in out:
    if not clean or clean[-1].split("\t")[0]!=r.split("\t")[0]: clean.append(r)
btn="--buttons" in sys.argv
for r in clean: print(r if btn else r.split("\t")[0])
print(f"[read_all] mode={mode} {len(pages)} screens, {len(clean)} rows, {len(furn)} furniture rows dropped" + (", reached the bottom" if stop=="end" or (mode=="swipe" and not stop) else f", stopped: {stop}"), file=sys.stderr)
' ${BTN:+--buttons}
