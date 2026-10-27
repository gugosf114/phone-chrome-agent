#!/usr/bin/env bash
# tests/test_phone_env.sh — one adb device, one screen registry, nth button.
# adb can list the phone twice (127.0.0.1:5555 + its Tailscale IP); bare adb
# then fails "more than one device" and the keeper never heals. Stubs only.
set -u
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
W=$(mktemp -d); trap 'rm -rf "$W"' EXIT
cat >"$W/adb" <<'S'
#!/usr/bin/env bash
echo "$*" >>"$CALLS"
case "$1" in
  devices) echo "List of devices attached"; cat "$DEVLIST" ;;
  connect) echo "connected to $2"; printf '%s\tdevice\n' "$2" >>"$DEVLIST" ;;
  shell)   case "$*" in *btns.tsv*) cat "$BTNS" ;; esac ;;
esac
exit 0
S
chmod +x "$W/adb"
export ADB="$W/adb" DEVLIST="$W/devs" CALLS="$W/calls" BTNS="$W/btns"
pass=0; fail=0
eq() { if [ "$2" = "$3" ]; then pass=$((pass+1)); echo "PASS $1"; else fail=$((fail+1)); echo "FAIL $1: got '$2' want '$3'"; fi; }
pick() { env -u ANDROID_SERIAL -u HD_REG TERMUX_HOME_DIR="$W/th" bash -c ". '$ROOT/scripts/phone_env.sh'; echo \"\${ANDROID_SERIAL:-}|\${HD_REG:-}\""; }

printf '100.81.55.57:5555\tdevice\n127.0.0.1:5555\tdevice\n' >"$W/devs"
eq "two listed -> loopback" "$(pick | cut -d'|' -f1)" "127.0.0.1:5555"
printf '100.81.55.57:5555\tdevice\n' >"$W/devs"
eq "one listed -> that one" "$(pick | cut -d'|' -f1)" "100.81.55.57:5555"
printf '100.81.55.57:5555\toffline\n' >"$W/devs"; : >"$W/calls"
eq "none live -> connects loopback" "$(pick | cut -d'|' -f1)" "127.0.0.1:5555"
grep -q 'connect 127.0.0.1:5555' "$W/calls"; eq "connect was called" "$?" "0"
eq "set serial wins" "$(ANDROID_SERIAL=abc:1 bash -c ". '$ROOT/scripts/phone_env.sh'; echo \$ANDROID_SERIAL")" "abc:1"
mkdir -p "$W/th"
eq "registry -> termux home" "$(pick | cut -d'|' -f2)" "$W/th/.hidden-displays"
eq "no termux home -> HD_REG unset" "$(env -u HD_REG TERMUX_HOME_DIR="$W/none" bash -c ". '$ROOT/scripts/phone_env.sh'; echo \${HD_REG:-unset}")" "unset"

printf 'SESSIONS\t\t540\t990\nCONSOLE\t\t294\t1103\nSESSIONS\t\t786\t1104\n' >"$W/btns"
printf '127.0.0.1:5555\tdevice\n' >"$W/devs"
eq "find first SESSIONS" "$(bash "$ROOT/scripts/ui.sh" find SESSIONS 2>/dev/null)" "540 990"
eq "find 2nd SESSIONS" "$(bash "$ROOT/scripts/ui.sh" find SESSIONS 2 2>/dev/null)" "786 1104"
eq "partial match still works" "$(bash "$ROOT/scripts/ui.sh" find CONSO 2>/dev/null)" "294 1103"
echo "$pass passed, $fail failed"; [ "$fail" = 0 ]
