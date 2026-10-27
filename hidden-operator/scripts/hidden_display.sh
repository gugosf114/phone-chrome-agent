#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# hidden_display.sh — screens only the agent can see (verified SM-F766U/A16).
#
# Runs an app on a private, always-on VIRTUAL display the phone's physical panel
# never shows, so the agent can drive that app (see + tap) WHILE the owner uses
# the real screen. No root, no scrcpy.
#
# Now supports MANY hidden screens at once, each with its own NAME, size, and id
# — a crew of invisible phones out of one phone. Pick a screen with `-n <name>`
# (default "main"); size it phone or tablet at start.
#
# HOW IT WORKS
#   - tools/hidden-display/vd.dex (a tiny app_process program, source VD.java)
#     runs at SHELL uid (adb/Shizuku — holds ADD_TRUSTED_DISPLAY on A14+) and
#     calls DisplayManager.createVirtualDisplay with a TRUSTED+PRESENTATION+
#     SYSTEM_DECORATIONS surface backed by an ImageReader. Each screen gets its
#     own folder /data/local/tmp/vd/<name> (its id + frames live there), so many
#     holders run side by side. The owner-uid check requires the shell package,
#     so the holder builds its context as com.android.shell.
#   - Eyes: the accessibility word-reader CANNOT see a non-default display, so
#     this drives by PICTURE — `shot`/`grid`/`zoom` capture one frame on demand.
#   - Hands: `input -d <id> tap` dispatches to the chosen hidden display.
#   - Liveness is by the logical display id (dumpsys `mDisplayId=`), so each named
#     screen is tracked on its own, even though all share the dex's display name.
#
# CONTRACT   (any verb takes an optional `-n <name>` right after it; default main)
#   start [-n name] [phone|tablet|W H DPI]   create a hidden screen; prints id
#                                            phone=1080x2400@420  tablet=1600x2560@320
#   stop [-n name] | stopall                 tear one down / tear them all down
#   reap                                     free the phone's accessibility services from a stranded reader
#   status [-n name] | id [-n name] | list   is it up? / print id / list all screens
#   launch [-n name] <pkg>[/<act>]           run an app on that screen
#   shot  [-n name] [out.png]                capture one frame -> PNG
#   grid  [-n name] [step]                   frame + labeled grid (numbers = real tap coords)
#   zoom  [-n name] <cx> <cy> [r] [scale]    crop+enlarge a spot, gridded in real coords
#   tap/swipe/text/key [-n name] ...         act on that screen
#   activate                                 reboot-heal the default `main` screen
#
# INERT WHEN ABSENT: needs a live adb device; every verb prints one line and
# exits non-zero if the phone isn't reachable — never hangs.
# ============================================================================
set -u
_HERE=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || _HERE=.
_ROOT=$(CDPATH= cd -- "$_HERE/.." 2>/dev/null && pwd) || _ROOT=.
[ -f "$_HERE/bridge.env" ] && . "$_HERE/bridge.env"
: "${ADB:=adb}"
. "$_HERE/phone_env.sh"   # one adb device + one screen registry
DEX_SRC="$_ROOT/tools/hidden-display/vd.dex"
DEX_DEV=/data/local/tmp/vd.dex
UD_DEX_SRC="$_ROOT/tools/hidden-display/ud.dex"   # the resident a11y reader daemon
UD_DEX_DEV=/data/local/tmp/ud.dex
BASE=/data/local/tmp/vd
FRAME_TO_PNG="${FRAME_TO_PNG:-$_ROOT/tools/hidden-display/frame_to_png.py}"
# Registry of live screens so a watchdog/`ensure` can respawn them with the same
# size and re-open the app they were showing. One TSV line: name W H DPI app.
REG="${HD_REG:-$HOME/.hidden-displays}"

# ---- verb + optional "-n <name>" -------------------------------------------
CMD="${1:-status}"; shift || true
NAME="${HD_NAME:-main}"
if [ "${1:-}" = "-n" ]; then NAME="${2:-main}"; shift 2; fi
[[ "$NAME" =~ ^[A-Za-z0-9_-]{1,64}$ ]] || { echo "[hidden] invalid display name" >&2; exit 2; }
DIR="$BASE/$NAME"

_adb_up(){ $ADB get-state >/dev/null 2>&1; }
_id(){ $ADB shell "cat $BASE/${1:-$NAME}/id 2>/dev/null" | tr -d '\r'; }
# A screen is up iff its stored logical display id still exists in DisplayManager.
_running(){ local n="${1:-$NAME}" id; id=$(_id "$n"); [ -n "$id" ] || return 1
  $ADB shell "dumpsys display 2>/dev/null | grep -qE 'mDisplayId=$id([^0-9]|\$)'" 2>/dev/null; }
# Capture ONE fresh frame from screen $NAME into $1/frame.raw + $1/frame.meta.
_capture(){ local d="$1" i=0
  $ADB shell "rm -f $DIR/frame.ready; touch $DIR/req"
  while [ $i -lt 20 ]; do $ADB shell "[ -f $DIR/frame.ready ]" 2>/dev/null && break; sleep 0.2; i=$((i+1)); done
  $ADB shell "[ -f $DIR/frame.ready ]" 2>/dev/null || return 1
  $ADB pull "$DIR/frame.raw"  "$d/frame.raw"  >/dev/null 2>&1
  $ADB pull "$DIR/frame.meta" "$d/frame.meta" >/dev/null 2>&1; return 0; }
_need_py(){ command -v python3 >/dev/null 2>&1 && [ -f "$FRAME_TO_PNG" ] || { echo "[hidden] need python3+pillow"; exit 1; }; }
# --- registry helpers (name W H DPI app) ------------------------------------
_reg_get(){ awk -F'\t' -v n="${1:-$NAME}" '$1==n{print;exit}' "$REG" 2>/dev/null; }
_reg_put(){ local n="$1" t; mkdir -p "$(dirname "$REG")" 2>/dev/null; t=$(mktemp)
  awk -F'\t' -v n="$n" 'NF && $1!=n' "$REG" 2>/dev/null > "$t"
  printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "${5:-}" >> "$t"; mv "$t" "$REG"; }
_reg_setapp(){ local l; l=$(_reg_get "$1"); [ -n "$l" ] || return 0
  _reg_put "$1" "$(echo "$l"|cut -f2)" "$(echo "$l"|cut -f3)" "$(echo "$l"|cut -f4)" "$2"; }
# --- resident a11y reader daemon (writes $DIR/tree.xml + $DIR/hb) ------------
_daemon_running(){ local hb; hb=$($ADB shell "cat $BASE/hb 2>/dev/null" | tr -d '\r')
  [[ "$hb" =~ ^[0-9]+$ ]] || return 1
  local age=$(( $(date +%s%3N) - hb )); [ "$age" -ge 0 ] && [ "$age" -lt 5000 ]; }
# Kill the reader for ONE screen: its own pid file first (exact), pattern second.
# A stranded reader holds a UiAutomation, and a UiAutomation with flags=0 unbinds
# EVERY accessibility service on the phone - see the note in UD.java.
_daemon_stop(){ local d="${1:-$DIR}"
  # Per-display pid files belong to legacy readers. Check process identity before
  # killing: a recycled pid must never terminate an unrelated app or the shared reader.
  $ADB shell "P=\$(cat $d/ud.pid 2>/dev/null); case \"\$P\" in ''|*[!0-9]*) exit 0;; esac
C=\$(tr '\\0' ' ' < /proc/\$P/cmdline 2>/dev/null)
case \"\$C\" in app_process*' /system/bin UD daemon '*|/system/bin/app_process*' /system/bin UD daemon '*)
  case \"\$C\" in *' $d ') kill -9 \$P 2>/dev/null;; esac;; esac; true"; }
# Kill EVERY reader on the device, whatever its cmdline spacing (pkill -f has
# missed these before). Walks /proc, so nothing can hide.
_daemon_sweep(){ $ADB shell 'for q in /proc/[0-9]*; do c=$(tr "\0" " " < $q/cmdline 2>/dev/null); case "$c" in app_process*" /system/bin UD daemon "*|/system/bin/app_process*" /system/bin UD daemon "*) kill -9 ${q##*/} 2>/dev/null;; esac; done; true'; }
_daemon_start(){ local id; id=$(_id "$NAME"); [ -n "$id" ] || return 1
  _daemon_running && return 0
  $ADB push "$UD_DEX_SRC" "$UD_DEX_DEV" >/dev/null 2>&1
  # Android has one UiAutomation slot. A device-side lock serializes its owner.
  if ! $ADB shell "mkdir $BASE/.reader-lock 2>/dev/null"; then
    # A crashed starter must not leave a permanent lock. Use the device's clock.
    $ADB shell "T=\$(stat -c %Y $BASE/.reader-lock 2>/dev/null); N=\$(date +%s); [ -n \"\$T\" ] && [ \$((N-T)) -gt 30 ] && rmdir $BASE/.reader-lock && mkdir $BASE/.reader-lock" || {
      local waiting=0; while [ "$waiting" -lt 25 ]; do _daemon_running && return 0; sleep 0.2; waiting=$((waiting+1)); done
      return 1
    }
  fi
  _daemon_sweep; sleep 0.2
  $ADB shell "umask 077; nohup setsid env CLASSPATH=$UD_DEX_DEV app_process /system/bin UD daemon all $BASE </dev/null >$BASE/ud.log 2>&1 &"
  local tries=0; while [ "$tries" -lt 20 ]; do _daemon_running && break; sleep 0.2; tries=$((tries+1)); done
  $ADB shell "rmdir $BASE/.reader-lock 2>/dev/null" || true
  _daemon_running; }
# True when no UiAutomation is registered, i.e. real accessibility services can bind.
_a11y_free(){ ! $ADB shell "dumpsys accessibility | grep -q '^Ui Automation\['"; }
# Start a holder for screen $NAME at W H DPI (idempotent).
_start(){ local W="$1" H="$2" DPI="$3"
  if _running "$NAME"; then echo "[hidden] $NAME already up (display $(_id "$NAME"))"; return 0; fi
  $ADB shell "mkdir -p $DIR"
  $ADB push "$DEX_SRC" "$DEX_DEV" >/dev/null 2>&1
  $ADB shell "rm -f $DIR/id $DIR/frame.*"
  # nohup+setsid so it outlives the adb shell session as long as the OS allows;
  # the supervisor/`ensure` respawns it if the OS reaps it anyway.
  $ADB shell "nohup setsid env CLASSPATH=$DEX_DEV app_process /system/bin VD $W $H $DPI $DIR </dev/null >$DIR/run.log 2>&1 &"
  local i=0; while [ $i -lt 20 ]; do [ -n "$(_id "$NAME")" ] && break; sleep 0.3; i=$((i+1)); done
  local ID; ID=$(_id "$NAME")
  if [ -n "$ID" ]; then _reg_put "$NAME" "$W" "$H" "$DPI" "$(_reg_get "$NAME" | cut -f5)"
    _daemon_start || { echo "[hidden] display exists but shared reader failed; see $BASE/ud.log" >&2; return 1; }
    echo "[hidden] $NAME up — display $ID (${W}x${H}@${DPI})"
  else echo "[hidden] $NAME FAILED; see: adb shell cat $BASE/dbg.log"; return 1; fi; }

case "$CMD" in
  start|activate)
    _adb_up || { echo "[hidden] no live adb — skip"; exit 1; }
    case "${1:-}" in
      tablet|--tablet) W=1600 H=2560 DPI=320 ;;
      phone|--phone|"") W=1080 H=2400 DPI=420 ;;
      *) W="${1:-1080}" H="${2:-2400}" DPI="${3:-420}" ;;
    esac
    _start "$W" "$H" "$DPI" ;;
  stop)
    _daemon_stop "$DIR"
    $ADB shell "pkill -f 'VD [0-9].* $DIR\$' 2>/dev/null"; sleep 0.3
    $ADB shell "rm -rf $DIR" 2>/dev/null
    t=$(mktemp); awk -F'\t' -v n="$NAME" 'NF && $1!=n' "$REG" 2>/dev/null > "$t"; mv "$t" "$REG" 2>/dev/null
    echo "[hidden] $NAME stopped" ;;
  stopall)
    _daemon_sweep
    $ADB shell "pkill -f 'app_process.*VD' 2>/dev/null"; sleep 0.3
    $ADB shell "rm -rf $BASE" 2>/dev/null; : > "$REG" 2>/dev/null
    _a11y_free || echo "[hidden] WARNING: a UiAutomation is still registered - phone accessibility services stay unbound"
    echo "[hidden] all stopped" ;;
  reap)
    # Emergency: free the phone's accessibility services from any stranded reader.
    _daemon_sweep; sleep 0.5
    if _a11y_free; then echo "[hidden] no UiAutomation held - accessibility services can bind"
    else echo "[hidden] a UiAutomation is STILL registered by something else; reboot frees it"; exit 1; fi ;;
  status)
    if _running "$NAME"; then echo "[hidden] $NAME UP — display $(_id "$NAME")"; else echo "[hidden] $NAME down"; exit 1; fi ;;
  id) _id "$NAME" ;;
  list)
    any=0
    for n in $($ADB shell "ls -1 $BASE 2>/dev/null" | tr -d '\r'); do
      [ -n "$n" ] || continue
      id=$(_id "$n"); [ -n "$id" ] || continue
      if _running "$n"; then st=UP; else st=down; fi
      printf '  %-10s id=%-4s %s\n' "$n" "$id" "$st"; any=1
    done
    [ "$any" = 1 ] || echo "  (no hidden screens)" ;;
  launch)
    ID=$(_id "$NAME"); [ -n "$ID" ] || { echo "[hidden] $NAME not running — start first"; exit 1; }
    APP="${1:-}"; [ -n "$APP" ] || { echo "usage: launch [-n name] <pkg>[/<activity>]"; exit 2; }
    # Reliable path: resolve the launcher activity, then am start --display <id> -n <comp>.
    # (`monkey --display` does NOT honour the display — it drops the app on screen 0.)
    case "$APP" in
      */*) COMP="$APP" ;;
      *)   COMP=$($ADB shell "cmd package resolve-activity --brief $APP 2>/dev/null | tail -1" | tr -d '\r') ;;
    esac
    [ -n "$COMP" ] || { echo "[hidden] could not resolve an activity for $APP"; exit 1; }
    $ADB shell "am start --display $ID -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n $COMP" 2>&1 | sed 's/^/[hidden] /'
    _reg_setapp "$NAME" "$COMP" ;;      # remember the app so `ensure` can re-open it
  ensure)
    # heal-if-down, inline and fast (used before each drive step + by the watchdog).
    _adb_up || { echo "[hidden] no live adb"; exit 1; }
    if _running "$NAME"; then
      _daemon_running "$NAME" || { _daemon_start; echo "[hidden] $NAME reader restarted"; }
      echo "[hidden] $NAME ok — display $(_id "$NAME")"; exit 0; fi
    L=$(_reg_get "$NAME"); [ -n "$L" ] || { echo "[hidden] $NAME not in registry — start it once first"; exit 1; }
    W=$(echo "$L"|cut -f2); H=$(echo "$L"|cut -f3); DPI=$(echo "$L"|cut -f4); APP=$(echo "$L"|cut -f5)
    _start "$W" "$H" "$DPI" || exit 1
    if [ -n "$APP" ]; then ID=$(_id "$NAME")
      $ADB shell "am start --display $ID -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n $APP" >/dev/null 2>&1
      echo "[hidden] $NAME healed — re-opened $APP on $ID"
    else echo "[hidden] $NAME healed (no app to re-open)"; fi ;;
  shot)
    ID=$(_id "$NAME"); [ -n "$ID" ] || { echo "[hidden] $NAME not running"; exit 1; }
    OUT="${1:-$DIR/hidden.png}"; TMP=$(mktemp -d)
    _capture "$TMP" || { echo "[hidden] no frame"; exit 1; }
    if command -v python3 >/dev/null 2>&1 && [ -f "$FRAME_TO_PNG" ]; then
      python3 "$FRAME_TO_PNG" "$TMP/frame.raw" "$TMP/frame.meta" "$OUT" && echo "$OUT"
    else echo "[hidden] raw frame at $TMP/frame.raw (need python3+pillow for PNG)"; fi ;;
  grid)
    ID=$(_id "$NAME"); [ -n "$ID" ] || { echo "[hidden] $NAME not running"; exit 1; }
    STEP="${1:-100}"; OUT="${2:-$DIR/grid.png}"; _need_py; TMP=$(mktemp -d)
    _capture "$TMP" || { echo "[hidden] no frame"; exit 1; }
    python3 "$FRAME_TO_PNG" "$TMP/frame.raw" "$TMP/frame.meta" "$OUT" --grid "$STEP" && echo "$OUT" ;;
  zoom)
    ID=$(_id "$NAME"); [ -n "$ID" ] || { echo "[hidden] $NAME not running"; exit 1; }
    CX="${1:-}"; CY="${2:-}"; [ -n "$CX" ] && [ -n "$CY" ] || { echo "usage: zoom [-n name] <cx> <cy> [r=120] [scale=4] [out]"; exit 2; }
    R="${3:-120}"; SCALE="${4:-4}"; OUT="${5:-$DIR/zoom.png}"; _need_py; TMP=$(mktemp -d)
    _capture "$TMP" || { echo "[hidden] no frame"; exit 1; }
    python3 "$FRAME_TO_PNG" "$TMP/frame.raw" "$TMP/frame.meta" "$OUT" --crop "$CX" "$CY" "$R" --scale "$SCALE" --grid 10 && echo "$OUT" ;;
  tap)   ID=$(_id "$NAME"); $ADB shell "input -d $ID tap ${1:-0} ${2:-0}" ;;
  swipe) ID=$(_id "$NAME"); $ADB shell "input -d $ID swipe ${1:-0} ${2:-0} ${3:-0} ${4:-0} ${5:-300}" ;;
  text)  ID=$(_id "$NAME"); $ADB shell "input -d $ID text '$*'" ;;
  key)   ID=$(_id "$NAME"); $ADB shell "input -d $ID keyevent ${1:-}" ;;
  *) echo "usage: hidden_display.sh <verb> [-n name] ...  (start|stop|stopall|reap|status|id|list|launch|ensure|shot|grid|zoom|tap|swipe|text|key|activate)" >&2; exit 2 ;;
esac
