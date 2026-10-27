#!/usr/bin/env bash
# tests/test_one_keeper.sh — two keeper loops started at once leave ONE running,
# and a stale lock (dead owner) does not block a new loop. Stubs only.
set -u
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
W=$(mktemp -d)
printf '#!/usr/bin/env bash\n[ "$1" = devices ] && printf "List of devices attached\\n127.0.0.1:5555\\tdevice\\n"\nexit 0\n' >"$W/adb"; chmod +x "$W/adb"
export ADB="$W/adb" HD_REG="$W/reg" HOME="$W" HD_WATCH_SEC=0.2; : >"$W/reg"
cleanup(){ pkill -f "$ROOT/scripts/hidden_supervisor.sh watch" 2>/dev/null; rm -rf "$W"; }; trap cleanup EXIT
pass=0; fail=0
eq() { if [ "$2" = "$3" ]; then pass=$((pass+1)); echo "PASS $1"; else fail=$((fail+1)); echo "FAIL $1: got '$2' want '$3'"; fi; }
bash "$ROOT/scripts/hidden_supervisor.sh" watch </dev/null >/dev/null 2>&1 &
bash "$ROOT/scripts/hidden_supervisor.sh" watch </dev/null >/dev/null 2>&1 &
sleep 2
eq "two started -> one runs" "$(pgrep -fc "$ROOT/scripts/hidden_supervisor.sh watch")" "1"
pkill -9 -f "$ROOT/scripts/hidden_supervisor.sh watch"; sleep 0.3
eq "killed owner leaves a stale lock" "$([ -d "$W/.hidden-watch.lock" ] && echo yes)" "yes"
bash "$ROOT/scripts/hidden_supervisor.sh" watch </dev/null >/dev/null 2>&1 &
sleep 1.5
eq "stale lock -> new loop runs" "$(pgrep -fc "$ROOT/scripts/hidden_supervisor.sh watch")" "1"
pkill -9 -f "$ROOT/scripts/hidden_supervisor.sh watch"; sleep 0.3
# a shell that only MENTIONS the loop must not count as the loop
bash -c 'sleep 4 # hidden_supervisor.sh watch' &
bash "$ROOT/scripts/hidden_supervisor.sh" tick >/dev/null 2>&1; sleep 1.5
eq "decoy does not block the start" "$(pgrep -fc "$ROOT/scripts/hidden_supervisor.sh watch")" "1"
echo "$pass passed, $fail failed"; [ "$fail" = 0 ]
