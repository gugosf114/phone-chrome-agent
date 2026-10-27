#!/bin/bash
# Hidden Chrome on the phone. A real (headed) Chromium window on an invisible X screen (Xvfb :5), CDP on 127.0.0.1:9222.
# Profile = agent-bridge's browser-headless profile "george" — the same dir browser-cookie-import / browser-runner use.
# George signs in once (see viewer.sh); the profile keeps the sessions.
export DISPLAY=:5
PROFILE=${HCHROME_PROFILE:-/root/.local/share/browser-headless/profiles/george}
LOG=/root/hchrome/logs; mkdir -p "$LOG" "$PROFILE"
if [ "$1" = "stop" ]; then pkill -f "^/usr/lib/chromium/chromium .*user-data-dir=$PROFILE"; sleep 1; pkill -x Xvfb; echo "stopped"; exit 0; fi
if ! pgrep -x Xvfb >/dev/null; then
  setsid nohup Xvfb :5 -screen 0 1080x2100x24 -nolisten tcp >"$LOG/xvfb.log" 2>&1 < /dev/null &
  sleep 1.5
fi
if ! curl -s -m 2 127.0.0.1:9222/json/version >/dev/null; then
  rm -f "$PROFILE/SingletonLock" "$PROFILE/SingletonSocket" "$PROFILE/SingletonCookie"
  setsid nohup /usr/lib/chromium/chromium \
    --no-sandbox --disable-gpu --disable-dev-shm-usage \
    --no-first-run --no-default-browser-check --password-store=basic \
    --disable-blink-features=AutomationControlled --disable-background-networking \
    --remote-debugging-port=9222 --remote-allow-origins='*' \
    --user-data-dir="$PROFILE" \
    --window-size=540,1050 --window-position=0,0 --force-device-scale-factor=2 \
    --disable-features=TranslateUI,MediaRouter \
    about:blank >"$LOG/chromium.log" 2>&1 < /dev/null &
fi
for i in $(seq 1 20); do curl -s -m 2 127.0.0.1:9222/json/version | grep -q Browser && { echo "hidden chrome up: profile=$PROFILE cdp=127.0.0.1:9222"; exit 0; }; sleep 1; done
echo "hidden chrome did NOT come up; see $LOG/chromium.log"; exit 1
