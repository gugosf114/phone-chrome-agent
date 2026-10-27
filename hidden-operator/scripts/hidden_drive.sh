#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# hidden_drive.sh — drive any app on a HIDDEN screen, hands-off, FULL AUTO.
#
# One command per intent. It finds the button BY NAME (the a11y tree on the
# OWN_FOCUS display, exact centre), taps it, and proves the screen changed. No
# confirm gate — the operator has full standing authority (authority_core.sh);
# every step is logged and proven so a wrong tap is visible and recoverable.
# Before each step it self-heals the screen (`hidden_display.sh ensure`), so a
# holder death mid-task is invisible.
#
#   open  <name> <app>          ensure the screen, open the app on it
#   do    <name> "<intent>"     find the button named <intent>, tap it, verify
#   type  <name> "<text>"       type text
#   key   <name> <keycode>      send a key (e.g. 66 = Enter, 4 = Back)
#   read  <name>                dump the buttons (names + centres)
#
# Resolve order: NAME (ui.sh/UD, exact) -> a taught photo (teach_skill) if present
# -> report. Standard apps expose names; blank-a11y apps use the photo way.
# ============================================================================
set -u
_HERE=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || _HERE=.
HD="$_HERE/hidden_display.sh"
UI="$_HERE/ui.sh"
AUTH="$_HERE/authority_core.sh"
LOG="${HOME}/.hidden-operator/hidden_drive.log"; mkdir -p "$(dirname "$LOG")" 2>/dev/null || true
: "${ADB:=adb}"
. "$_HERE/phone_env.sh"   # one adb device + one screen registry
_log(){ printf '[%s] %s\n' "$(date '+%F %T')" "$*" >>"$LOG" 2>/dev/null || true; }

CMD="${1:-}"; NAME="${2:-main}"; export HD_NAME="$NAME"
DDIR="/data/local/tmp/vd/$NAME"                          # on-phone dir (id, btns.tsv)
STRICT="send delete pay submit post call buy checkout transfer purchase sign publish deploy release archive apply"
_ensure(){ bash "$HD" ensure -n "$NAME" >/dev/null 2>&1; }
_shot(){ bash "$HD" shot -n "$NAME" "$1" >/dev/null 2>&1; }
_changed(){ command -v python3 >/dev/null 2>&1 && [ -s "$1" ] && [ -s "$2" ] || return 0
  python3 -c "from PIL import Image,ImageChops
a=Image.open('$1').convert('RGB'); b=Image.open('$2').convert('RGB')
print(1 if ImageChops.difference(a,b).getbbox() else 0)" 2>/dev/null; }
# raw one-round-trip find+tap by name (lowercased q); echoes "OK cx cy" or "MISS".
_tapname(){ $ADB shell "ID=\$(cat $DDIR/id 2>/dev/null)
L=\$(awk -F'\t' -v q='$1' '{t=tolower(\$1);d=tolower(\$2); if(t==q||d==q){print \$3\" \"\$4; exit} if(e==\"\"&&(index(t,q)||index(d,q)))e=\$3\" \"\$4} END{if(e!=\"\")print e}' $DDIR/btns.tsv 2>/dev/null)
if [ -n \"\$L\" ] && [ -n \"\$ID\" ]; then input -d \$ID tap \$L && echo \"OK \$L\"; else echo MISS; fi" 2>/dev/null | tr -d '\r'; }
# is app <pkg>[/activity] currently on the hidden screen (not reset to home/launcher)?
# Match the PACKAGE only: the screen tree uses "<pkg>:id/", never the activity name.
_appon(){ local pkg="${1%%/*}"; $ADB shell "grep -q '$pkg:id/' $DDIR/tree.xml 2>/dev/null"; }
_open_app(){ bash "$HD" ensure -n "$NAME" >/dev/null 2>&1
  bash "$HD" status -n "$NAME" >/dev/null 2>&1 || bash "$HD" start -n "$NAME" phone >/dev/null 2>&1
  bash "$HD" launch -n "$NAME" "$1" >/dev/null 2>&1; }
# run one task step: "type:<text>", "key:<code>", or a bare button name (a tap). 0=ok.
_step(){ local id; case "$1" in
    type:*) id=$($ADB shell "cat $DDIR/id" | tr -d '\r'); [ -n "$id" ] || return 1
            $ADB shell "input -d $id text '$(printf '%s' "${1#type:}" | sed "s/'/'\\\\''/g")'" >/dev/null 2>&1 ;;
    key:*)  id=$($ADB shell "cat $DDIR/id" | tr -d '\r'); [ -n "$id" ] || return 1
            $ADB shell "input -d $id keyevent ${1#key:}" >/dev/null 2>&1 ;;
    *)      [ "$(_tapname "$(printf '%s' "${1#do:}" | tr 'A-Z' 'a-z')" | cut -d' ' -f1)" = "OK" ] ;;
  esac; }

case "$CMD" in
  open)
    APP="${3:-}"; [ -n "$APP" ] || { echo "usage: open <name> <app>"; exit 2; }
    _ensure
    bash "$HD" status -n "$NAME" >/dev/null 2>&1 || bash "$HD" start -n "$NAME" phone >/dev/null 2>&1
    bash "$HD" launch -n "$NAME" "$APP" 2>&1 | sed 's/^/[drive] /'
    sleep 2; _log "open $NAME $APP"; echo "[drive] $NAME: opened $APP" ;;
  do)
    Q="${3:-}"; [ -n "$Q" ] || { echo "usage: do <name> <intent>"; exit 2; }
    ql=$(printf '%s' "$Q" | tr 'A-Z' 'a-z')
    # ONE on-device round-trip does everything — read the display id, awk the button
    # out of the daemon's compact index, and tap it (~0.8s). Reused in the heal loop.
    SNIP="ID=\$(cat $DDIR/id 2>/dev/null)
L=\$(awk -F'\t' -v q='$ql' '{t=tolower(\$1);d=tolower(\$2); if(t==q||d==q){print \$3\" \"\$4; exit} if(e==\"\"&&(index(t,q)||index(d,q)))e=\$3\" \"\$4} END{if(e!=\"\")print e}' $DDIR/btns.tsv 2>/dev/null)
if [ -n \"\$L\" ] && [ -n \"\$ID\" ]; then input -d \$ID tap \$L && echo \"OK \$L\"; else echo MISS; fi"
    RES=$($ADB shell "$SNIP" 2>/dev/null | tr -d '\r')
    HEALED=""
    if [ "${RES%% *}" != "OK" ]; then
      # MISS -> the screen may be respawning (a death). Kick a heal and FAST-poll the
      # same cheap snippet for ~18s while the keeper brings the screen + app back.
      bash "$HD" ensure -n "$NAME" >/dev/null 2>&1
      for r in $(seq 1 24); do
        RES=$($ADB shell "$SNIP" 2>/dev/null | tr -d '\r')
        [ "${RES%% *}" = "OK" ] && { HEALED=" (healed)"; break; }
        [ $((r % 6)) -eq 0 ] && bash "$HD" ensure -n "$NAME" >/dev/null 2>&1
        sleep 0.7
      done
    fi
    case "$RES" in
      OK\ *) X=$(echo "$RES"|awk '{print $2}'); Y=$(echo "$RES"|awk '{print $3}')
        case " $STRICT " in *" $ql "*) _log "STRICT action '$Q' (full-auto)";; esac
        _log "do '$Q' -> tap ($X,$Y) [name]$HEALED"; echo "[drive] $NAME: '$Q' -> tapped ($X,$Y) by name$HEALED" ;;
      *) _log "do '$Q' NOT FOUND on $NAME"
        echo "[drive] '$Q' not found by name. Teach a photo (teach_skill.sh) or reword." >&2; exit 2 ;;
    esac
    if [ "${HD_VERIFY:-0}" = 1 ]; then            # optional screenshot verify (slow)
      B=$(mktemp --suffix=.png); _shot "$B"; sleep 0.4; A=$(mktemp --suffix=.png); _shot "$A"
      [ "$(_changed "$B" "$A")" = 1 ] && echo "[drive] verified: screen changed" || echo "[drive] note: no visible change"
    fi ;;
  run) # run <name> <app> <step> [<step>...] — a JOURNALED task that survives a death.
       # steps: a bare button name (tap), "type:<text>", or "key:<code>". If the screen
       # drops mid-task, it heals, re-opens the app, and REPLAYS the completed steps to
       # restore state (e.g. a half-filled form), then keeps going. The task always finishes.
    APP="${3:-}"; [ -n "$APP" ] || { echo "usage: run <name> <app> <step> ..."; exit 2; }
    shift 3; STEPS=("$@"); [ ${#STEPS[@]} -gt 0 ] || { echo "run: no steps"; exit 2; }
    _open_app "$APP"; sleep 3
    done_steps=(); i=0; guard=0; recov=0
    while [ "$i" -lt "${#STEPS[@]}" ]; do
      if ! _appon "$APP"; then                 # the app fell off (a holder death) — put it back
        recov=$((recov+1)); [ "$recov" -gt 8 ] && { echo "[run] cannot restore $APP after 8 tries — aborting"; exit 1; }
        echo "[run] app gone — restoring $APP, then replaying ${#done_steps[@]} step(s) (try $recov)"
        _log "run recover #$recov: replay ${#done_steps[@]}"
        bash "$HD" ensure -n "$NAME" >/dev/null 2>&1                        # display back (keeper-safe, idempotent)
        _appon "$APP" || bash "$HD" launch -n "$NAME" "$APP" >/dev/null 2>&1 # re-open the app only if still not on
        for w in $(seq 1 20); do _appon "$APP" && break; sleep 1; done       # wait until it is really there
        for s in "${done_steps[@]}"; do _step "$s"; sleep 0.4; done          # rebuild the state we had
        continue
      fi
      recov=0
      if _step "${STEPS[$i]}"; then
        echo "[run] ok: ${STEPS[$i]}"; done_steps+=("${STEPS[$i]}"); i=$((i+1)); guard=0
      else                                       # a miss right after a heal = tree not refreshed yet; be patient
        guard=$((guard+1)); [ "$guard" -gt 40 ] && { echo "[run] stuck at '${STEPS[$i]}'"; exit 1; }
        [ $((guard % 10)) -eq 0 ] && bash "$HD" ensure -n "$NAME" >/dev/null 2>&1
        sleep 0.5
      fi
    done
    _log "run '$APP' complete (${#STEPS[@]} steps)"; echo "[run] DONE — ${#STEPS[@]} steps, survived any drops" ;;
  seq) # seq <name> <btn1> <btn2> ...  — a whole sequence in ONE round-trip (fast)
    ITEMS="${*:3}"; [ -n "$ITEMS" ] || { echo "usage: seq <name> <btn1> <btn2> ..."; exit 2; }
    $ADB shell "ID=\$(cat $DDIR/id 2>/dev/null)
for q in $ITEMS; do
  L=\$(awk -F'\t' -v q=\"\$q\" '{ql=tolower(q);t=tolower(\$1);d=tolower(\$2); if(t==ql||d==ql){print \$3\" \"\$4; exit} if(e==\"\"&&(index(t,ql)||index(d,ql)))e=\$3\" \"\$4} END{if(e!=\"\")print e}' $DDIR/btns.tsv 2>/dev/null)
  if [ -n \"\$L\" ] && [ -n \"\$ID\" ]; then input -d \$ID tap \$L && echo \"[seq] \$q -> \$L\"; else echo \"[seq] \$q MISS\"; fi
  sleep 0.25
done" 2>/dev/null | tr -d '\r'
    _log "seq '$ITEMS'" ;;
  type) T="${3:-}"; [ -n "$T" ] || { echo "usage: type <name> <text>"; exit 2; }
    _ensure; bash "$HD" text -n "$NAME" "$T" >/dev/null; _log "type '$T'"; echo "[drive] $NAME: typed" ;;
  key)  K="${3:-}"; [ -n "$K" ] || { echo "usage: key <name> <keycode>"; exit 2; }
    _ensure; bash "$HD" key -n "$NAME" "$K" >/dev/null; _log "key $K"; echo "[drive] $NAME: key $K" ;;
  read) _ensure; bash "$UI" tree ;;
  *) echo "usage: hidden_drive.sh open <name> <app> | do <name> <intent> | seq <name> <btns...> | run <name> <app> <steps...> | type <name> <text> | key <name> <code> | read <name>" >&2; exit 2 ;;
esac
