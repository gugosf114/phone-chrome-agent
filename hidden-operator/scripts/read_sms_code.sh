#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# read_sms_code.sh — read the phone's own texts and pull out a login code.
#
# This is the piece that lets the agent finish a login that texts a one-time
# code (the wall most bots die at). The phone's SIM is the owner's, so the code
# comes to this phone; the agent reads it and types it in.
#
# It uses `adb content query content://sms/inbox` — the shell uid can read SMS,
# so it needs NO Termux:API app. Read-only: it never sends or deletes anything.
#
#   code                  print the newest login code found (last few texts)
#   latest [n]            list the last n texts (time  sender  first 70 chars)
#   wait [seconds]        watch, and print a code the moment a NEW text brings one
#
# INERT WHEN ABSENT: prints one line and exits non-zero if no adb device.
# ============================================================================
set -u
: "${ADB:=adb}"
_HERE=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || _HERE=.
. "$_HERE/phone_env.sh"   # one adb device + one screen registry
$ADB get-state >/dev/null 2>&1 || { echo "[sms] no live adb — skip"; exit 1; }

_query(){ $ADB shell "content query --uri content://sms/inbox --projection date:address:body --sort 'date DESC' 2>/dev/null" | tr -d '\r'; }

read -r -d '' PYX <<'PY' || true
import sys, re
mode = sys.argv[1] if len(sys.argv) > 1 else 'code'
rows = []
for line in sys.stdin:
    m = re.match(r'Row:\s*\d+\s+date=(\d+),\s*address=(.*?),\s*body=(.*)$', line.rstrip('\n'))
    if m:
        rows.append((int(m.group(1)), m.group(2), m.group(3)))

KW = r'(?:one[- ]?time|passcode|verification|verify|security|otp|code|pin)'

def find_otp(body):
    """A code that is clearly a login code (sits next to an OTP word). No guessing."""
    b = re.sub(r'https?://\S+', '', body)                 # drop links (they hold digits)
    m = re.search(r'\bG-(\d{4,8})', b)                    # Google's "G-123456"
    if m:
        return m.group(1)
    m = re.search(KW + r'\D{0,25}(\d{4,8})', b, re.I)     # "code is 123456"
    if m:
        return m.group(1)
    m = re.search(r'(?<!\d)(\d{4,8})\D{0,25}' + KW, b, re.I)  # "123456 is your code"
    if m:
        return m.group(1)
    return None

def find_any(body):
    """OTP first; else a lone 4-8 digit run. Only safe for a brand-new text mid-login."""
    c = find_otp(body)
    if c:
        return c
    b = re.sub(r'https?://\S+', '', body)
    m = re.search(r'(?<!\d)(\d{4,8})(?!\d)', b)
    return m.group(1) if m else None

if mode == 'maxdate':
    print(rows[0][0] if rows else 0)
elif mode == 'code':
    for ts, addr, body in rows:
        c = find_otp(body)                                # strict: real OTPs only
        if c:
            print(c); break
elif mode == 'newcode':
    base = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    for ts, addr, body in rows:
        if ts > base:
            c = find_any(body)                            # a new text mid-login = the code
            if c:
                print(c); break
elif mode == 'latest':
    import datetime
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    for ts, addr, body in rows[:n]:
        t = datetime.datetime.fromtimestamp(ts / 1000).strftime('%m-%d %H:%M')
        print(f"{t}  {addr:<14} {body.replace(chr(10),' ')[:70]}")
PY

command -v python3 >/dev/null 2>&1 || { echo "[sms] need python3"; exit 1; }

case "${1:-code}" in
  code)   _query | python3 -c "$PYX" code ;;
  latest) _query | python3 -c "$PYX" latest "${2:-5}" ;;
  wait)
    to="${2:-120}"; base=$(_query | python3 -c "$PYX" maxdate); end=$(( $(date +%s) + to ))
    while [ "$(date +%s)" -lt "$end" ]; do
      c=$(_query | python3 -c "$PYX" newcode "$base")
      [ -n "$c" ] && { echo "$c"; exit 0; }
      sleep 3
    done
    echo "[sms] no new code in ${to}s" >&2; exit 1 ;;
  *) echo "usage: read_sms_code.sh code|latest [n]|wait [seconds]" >&2; exit 2 ;;
esac
