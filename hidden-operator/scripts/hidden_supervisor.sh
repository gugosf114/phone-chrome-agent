#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# hidden_supervisor.sh — keeps the hidden screens ALIVE on their own.
#
# The virtual-display holder is a shell-uid app_process launched via adb; Android
# reaps it after a while (backgrounded-shell process, Doze, memory). This wraps it
# in the same pattern phone_supervisor.sh uses for the watcher:
#   wake-lock + phantom-killer-off + a fast watch loop + a persisted 15-min tick
#   that resurrects the watch loop. Each pass re-`ensure`s every screen in the
#   registry (~/.hidden-displays) — respawns the holder and re-opens its app.
#
#   boot     one-shot at phone boot (Termux:Boot / ACTIVATE): wake-lock, phantom
#            killer off, register the tick, start the watch loop, ensure screens.
#   tick     periodic (job-scheduler, 15 min): ensure screens + resurrect watch.
#   watch    fast loop (every 25s): ensure screens. (started/kept alive by boot+tick)
#   ensure   one pass now.   status   up/down per screen.   stop   tear the loop down.
# ============================================================================
set -u
_HERE=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || _HERE=.
HD="$_HERE/hidden_display.sh"
. "$_HERE/phone_env.sh"   # one adb device + one screen registry
REG="${HD_REG:-$HOME/.hidden-displays}"
LOG="${HOME}/.hidden-operator/hidden_supervisor.log"
mkdir -p "$(dirname "$LOG")" 2>/dev/null || true
: "${ADB:=adb}"
BASH_BIN=/data/data/com.termux/files/usr/bin/bash; [ -x "$BASH_BIN" ] || BASH_BIN=$(command -v bash)
JOB_ID=7733

_log(){ printf '[%s] %s\n' "$(date '+%F %T')" "$*" >>"$LOG" 2>/dev/null || true; }
_names(){ awk -F'\t' 'NF{print $1}' "$REG" 2>/dev/null; }
_ensure_all(){ local n; for n in $(_names); do [ -n "$n" ] || continue
  bash "$HD" ensure -n "$n" >>"$LOG" 2>&1; done; }
# ONE watch loop per phone. Android runs a new periodic job at once, so boot's
# own start and the first tick raced and left two loops that could both respawn
# the same screen. The lock sits next to the shared registry, so a loop started
# from Termux and one from the Debian box see the same lock.
LOCKD="$(dirname "$REG")/.hidden-watch.lock"
# Alive = the lock's owner is a running watch loop. (pgrep -f matched any shell
# whose command line merely MENTIONED the loop, so boot skipped the start.)
_watch_alive(){ local p; p=$(cat "$LOCKD/pid" 2>/dev/null); [ -n "$p" ] || return 1
  tr '\0' ' ' <"/proc/$p/cmdline" 2>/dev/null | grep -q 'hidden_supervisor.sh watch'; }
_watch_lock(){ local p i
  for i in 1 2 3; do
    mkdir "$LOCKD" 2>/dev/null && { echo $$ >"$LOCKD/pid"; return 0; }
    p=$(cat "$LOCKD/pid" 2>/dev/null)
    [ -n "$p" ] || { sleep 0.5; continue; }            # owner still writing its pid
    tr '\0' ' ' <"/proc/$p/cmdline" 2>/dev/null | grep -q 'hidden_supervisor.sh watch' && return 1
    rm -rf "$LOCKD"                                     # stale: owner is gone
  done; return 1; }
_watch_start(){
  setsid "$BASH_BIN" "$_HERE/hidden_supervisor.sh" watch </dev/null >>"${HOME}/.hidden-operator/hidden_watch.log" 2>&1 &
  disown 2>/dev/null || true; }

case "${1:-tick}" in
  boot)
    _log "BOOT — wake-lock + phantom-off + tick + watch"
    termux-wake-lock 2>/dev/null || true
    $ADB shell device_config put activity_manager max_phantom_processes 2147483647 2>/dev/null || true
    $ADB shell settings put global settings_enable_monitor_phantom_procs false 2>/dev/null || true
    # One hook = one script. Prefer the timer table (timer-add refuses a taken hook);
    # fall back to a raw registration only when timer-add is not installed.
    if command -v timer-add >/dev/null 2>&1 || [ -x "$HOME/.local/bin/timer-add" ]; then
      "${TIMER_ADD:-$HOME/.local/bin/timer-add}" "$JOB_ID" 900000 "$_HERE/hidden_supervisor.sh" >>"$LOG" 2>&1 || _log "WARN: timer-add refused hook $JOB_ID (taken?) — pick a free id"
    else
      termux-job-scheduler --script "$_HERE/hidden_supervisor.sh" --job-id "$JOB_ID" \
          --period-ms 900000 --persisted true 2>/dev/null || _log "WARN: job-scheduler reg failed"
    fi
    _ensure_all; _watch_alive || _watch_start ;;
  tick)  _ensure_all; _watch_alive || _watch_start ;;
  watch) _watch_lock || { _log "watch already running - this one exits"; exit 0; }
    trap 'rm -rf "$LOCKD"' EXIT
    _log "watch loop up"; while true; do adb_heal; _ensure_all; sleep "${HD_WATCH_SEC:-3}"; done ;;
  ensure) _ensure_all ;;
  status)
    for n in $(_names); do
      if bash "$HD" status -n "$n" >/dev/null 2>&1; then echo "  $n: UP"; else echo "  $n: DOWN"; fi
    done
    _watch_alive && echo "  watch: ALIVE" || echo "  watch: DEAD" ;;
  stop)
    termux-job-scheduler --cancel --job-id "$JOB_ID" 2>/dev/null || true
    pkill -f "hidden_supervisor.sh watch" 2>/dev/null || true
    _log "STOPPED by request" ; echo "[super] stopped" ;;
  *) echo "usage: hidden_supervisor.sh boot|tick|watch|ensure|status|stop" >&2; exit 2 ;;
esac
