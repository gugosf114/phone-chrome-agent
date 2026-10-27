#!/bin/bash
# read_all.sh — read a hidden-screen app like a web page: scroll and stitch, on the phone, in ONE adb round trip.
# Built 2026-10-26. The keyhole fix #2 (fix #1 is a tall screen: `hidden_display.sh start -n tall 1080 6000 420`).
#
#   bash read_all.sh -n <screen> [max_swipes=12] [--buttons]
#
# Reads the shared accessibility tree the resident reader keeps for that display, prints every text/desc in screen
# order, swipes up like a finger, waits for the tree to change, reads again, until the bottom (two reads the same)
# or max_swipes. Then de-duplicates overlapping rows (consecutive and 3-line windows) so you get ONE blob.
# Known gap (10/26): the last row or two at the very bottom can lag the reader; a tall screen has no such gap.
# Read-only except the swipe. Never taps. --buttons prints "text<TAB>cx cy" so a script can tap a stitched row later.
#
# Needs: the screen up with its reader (hidden_display.sh start/ensure). The tree lives in /data/local/tmp/vd/tree.xml
# per screen: /data/local/tmp/vd/<name>/tree.xml (one shared reader writes all of them on a11y events).
set -e
_HERE="$(cd "$(dirname "$0")" && pwd)"; . "$_HERE/phone_env.sh" 2>/dev/null || true; : "${ADB:=adb -s ${ANDROID_SERIAL:-127.0.0.1:5555}}"
NAME=main; while [ $# -gt 0 ]; do case "$1" in -n) NAME="$2"; shift 2;; --buttons) BTN=1; shift;; *) MAX="$1"; shift;; esac; done
MAX=${MAX:-12}; BASE=/data/local/tmp/vd; DIR="$BASE/$NAME"
ID=$($ADB shell "cat $DIR/id 2>/dev/null" | tr -d '\r'); [ -n "$ID" ] || { echo "[read_all] screen '$NAME' is not up" >&2; exit 1; }
read -r W H < <($ADB shell "wm size -d $ID 2>/dev/null | sed -n 's/.*: *\([0-9]*\)x\([0-9]*\).*/\1 \2/p' | tail -1" | tr -d '\r'); W=${W:-1080}; H=${H:-2400}
X=$((W/2)); Y1=$((H*72/100)); Y2=$((H*28/100))   # one swipe = about 44% of the screen, so rows overlap and nothing is skipped

# The whole loop runs on the phone: one adb shell, no round trip per page.
$ADB shell "set -- ; I=$ID; T=$DIR/tree.xml; prev=''; n=0
for k in 1 2 3; do input -d \$I swipe $X $Y2 $X $Y1 200; sleep 0.3; done; sleep 1.5   # to the top first, then let the reader catch up
extract(){ grep -o '<node [^>]*>' \$T 2>/dev/null | sed -n 's/.*text=\"\([^\"]*\)\".*desc=\"\([^\"]*\)\".*cx=\"\([0-9]*\)\" cy=\"\([0-9]*\)\".*/\1\t\2\t\3 \4/p' | awk -F'\t' '{t=\$1; if(t==\"\")t=\$2; if(t!=\"\") print t \"\t\" \$3}'; }
while [ \$n -le $MAX ]; do
  cur=\$(extract)
  [ \"\$cur\" = \"\$prev\" ] && [ \$n -gt 0 ] && break
  echo \"\$cur\"; echo '@@PAGE@@'
  prev=\$cur; n=\$((n+1))
  [ \$n -gt $MAX ] && break
  input -d \$I swipe $X $Y1 $X $Y2 \$((280 + \$RANDOM % 160))
  # the reader rewrites the tree on a11y events; the clock and status bar fire events too, so a 'changed' check lies.
  # A fixed settle is honest: 1.2 s is enough for a list to land on this phone.
  sleep 1.2
done" | tr -d '\r' | python3 -c '
import sys
from collections import Counter
pages=[[r for r in p.strip("\n").split("\n") if r.strip()] for p in sys.stdin.read().split("@@PAGE@@") if p.strip()]
# furniture = a row with the same text at the same screen spot on 2+ pages (status bar, nav bar, taskbar, sticky header)
spot=Counter((r.split("\t")[0], r.split("\t")[1] if "\t" in r else "") for p in pages for r in set(p))
furn={k for k,c in spot.items() if c>=2 and len(pages)>1}
out=[]
for rows in pages:
    rows=[r for r in rows if (r.split("\t")[0], r.split("\t")[1] if "\t" in r else "") not in furn]
    texts=[r.split("\t")[0] for r in rows]; have=[o.split("\t")[0] for o in out]
    k=0
    for j in range(min(len(have),len(texts)),0,-1):      # overlap: a tail of what we have == a head of this page
        if have[-j:]==texts[:j]: k=j; break
    if k==0 and have:                                    # no clean overlap: skip rows still visible from the last page
        last=set(have[-40:]); rows=[r for r in rows if r.split("\t")[0] not in last]
        k=0
    out.extend(rows[k:])
clean=[]
for r in out:
    if not clean or clean[-1].split("\t")[0]!=r.split("\t")[0]: clean.append(r)
btn="--buttons" in sys.argv
for r in clean: print(r if btn else r.split("\t")[0])
print(f"[read_all] {len(pages)} screens, {len(clean)} rows, {len(furn)} furniture rows dropped", file=sys.stderr)
' ${BTN:+--buttons}
