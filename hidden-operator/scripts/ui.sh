#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# ui.sh — read + drive a HIDDEN screen BY NAME (button text), the "name way".
#
# Works because the hidden display is built with OWN_FOCUS (its own independent
# focus), so its app window is interactive and the accessibility tree exposes the
# buttons — with exact centres, so no coordinate guessing.
#
#   tree                 dump every button: text / id / desc / clickable / bounds / cx,cy
#   find <text> [n]      print "<cx> <cy>" of the clickable button whose text|desc matches
#   tap  <text> [n]      tap that button. n picks the nth exact match, top-down, when
#                        two buttons share a name (WiM: the SESSIONS header vs the tab)
#   push                 (re)push ud.dex to the phone
#
# Reads UD.java's dumper (tools/hidden-display/ud.dex) on hidden screen $HD_NAME.
# ============================================================================
set -u
_HERE=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || _HERE=.
HD="$_HERE/hidden_display.sh"
UD_LOCAL="$_HERE/../tools/hidden-display/ud.dex"
UD_DEV=/data/local/tmp/ud.dex
: "${ADB:=adb}"; : "${HD_NAME:=main}"
. "$_HERE/phone_env.sh"   # one adb device + one screen registry
DIR="/data/local/tmp/vd/$HD_NAME"

_ensure(){ $ADB shell "[ -f $UD_DEV ]" 2>/dev/null || $ADB push "$UD_LOCAL" "$UD_DEV" >/dev/null 2>&1; }
# FAST: the resident daemon keeps a compact clickable index in $DIR/btns.tsv
# (text<TAB>desc<TAB>cx<TAB>cy) and the full tree in $DIR/tree.xml — just read them.
_fastbtns(){ $ADB shell "cat $DIR/btns.tsv 2>/dev/null"; }
_fasttree(){ $ADB shell "cat $DIR/tree.xml 2>/dev/null"; }
# SLOW fallback (daemon down/empty): one-shot reader + a corner nudge to fire the
# window event the a11y list needs.
_tree(){ local ID; ID=$(bash "$HD" id -n "$HD_NAME")
  [ -n "$ID" ] || { echo "[ui] screen '$HD_NAME' not up" >&2; return 1; }; _ensure
  local o; o=$(mktemp)
  ( $ADB shell "CLASSPATH=$UD_DEV app_process /system/bin UD $ID" >"$o" 2>/dev/null ) &
  local p=$!
  sleep 1.3
  $ADB shell "input -d $ID tap ${UI_NUDGE:-8 8}" >/dev/null 2>&1
  wait $p; cat "$o"; rm -f "$o"; }
# find the clickable node whose text|desc == q; print "cx cy" (nothing if none).
PYFIND='
import sys, re
q = sys.argv[1].strip().lower()
n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
for line in sys.stdin:
    m = dict(re.findall(r"(\w+)=\"([^\"]*)\"", line))
    if m.get("clickable") != "true": continue
    t = m.get("text","").strip().lower(); d = m.get("desc","").strip().lower()
    if q == t or q == d:
        n -= 1
        if n == 0:
            print(m["cx"], m["cy"]); break
'

case "${1:-tree}" in
  push) $ADB push "$UD_LOCAL" "$UD_DEV" >/dev/null && echo "[ui] pushed ud.dex" ;;
  tree) T=$(_fasttree); [ -n "$T" ] && printf '%s\n' "$T" || _tree ;;
  find|tap)
    Q="${2:-}"; [ -n "$Q" ] || { echo "usage: ui.sh $1 <text> [n]" >&2; exit 2; }
    NTH="${3:-1}"; [[ "$NTH" =~ ^[1-9][0-9]*$ ]] || { echo "[ui] n must be 1, 2, 3..." >&2; exit 2; }
    CX=""; CY=""; ql=$(printf '%s' "$Q" | tr 'A-Z' 'a-z')
    # FAST path: read the daemon's compact clickable index (tiny, ~100ms) and match
    # text or desc. Retry briefly (it refreshes on the tap event within ~150ms).
    for _try in 1 2 3 4 5 6; do
      read CX CY < <(_fastbtns | awk -F'\t' -v q="$ql" -v n="$NTH" -v first="$([ "$NTH" = 1 ] && echo 1 || echo 0)" '{t=tolower($1);d=tolower($2); if(t==q||d==q){if(--n==0){print $3, $4; exit}} if(e==""&&(index(t,q)||index(d,q)))e=$3" "$4} END{if(n>0 && first==1 && e!="")print e}')
      [ -n "${CX:-}" ] && break
      sleep 0.15
    done
    # SLOW fallback: daemon empty/down -> heal + one-shot full read (fires a nudge).
    if [ -z "${CX:-}" ]; then
      bash "$HD" ensure -n "$HD_NAME" >/dev/null 2>&1
      read CX CY < <(_tree 2>/dev/null | python3 -c "$PYFIND" "$Q" "$NTH")
    fi
    [ -n "${CX:-}" ] || { echo "[ui] no clickable button matching '$Q'" >&2; exit 1; }
    if [ "$1" = find ]; then echo "$CX $CY"
    else bash "$HD" tap -n "$HD_NAME" "$CX" "$CY" >/dev/null; echo "[ui] tapped '$Q' at ($CX,$CY)"; fi ;;
  *) echo "usage: ui.sh push|tree|find <text>|tap <text>" >&2; exit 2 ;;
esac
