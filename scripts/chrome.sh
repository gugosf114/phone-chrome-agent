#!/bin/bash
# chrome.sh — open the back door to the phone's OWN Chrome (the browser that passes every bouncer).
# Run from the Debian box on the phone (Termux → proot). Needs adb connected (127.0.0.1:5555).
#   bash chrome.sh            -> wake Chrome, forward its DevTools socket to 127.0.0.1:9336, print tabs
#   bash chrome.sh <url>      -> same, then open <url> in Chrome
PORT=${CDP_PORT:-9336}
adb shell am start -n com.android.chrome/com.google.android.apps.chrome.Main >/dev/null 2>&1   # bring Chrome to front (a backgrounded Chrome's socket goes dead)
sleep 1
P=$(adb shell pidof com.android.chrome | tr -d '\r' | awk '{print $1}')
adb forward --remove tcp:$PORT >/dev/null 2>&1
# whichever Chrome started first owns the bare socket name; the other gets _<pid>. Try pid first, then bare.
adb forward tcp:$PORT localabstract:chrome_devtools_remote_$P >/dev/null 2>&1
curl -s -m 4 127.0.0.1:$PORT/json/version | grep -q '"com.android.chrome"' || {
  adb forward --remove tcp:$PORT >/dev/null 2>&1
  adb forward tcp:$PORT localabstract:chrome_devtools_remote >/dev/null 2>&1
}
curl -s -m 4 127.0.0.1:$PORT/json/version | grep -q Browser || { echo "no answer from Chrome on $PORT (is it frozen? see anti_freeze.sh)"; exit 1; }
[ -n "$1" ] && adb shell am start -a android.intent.action.VIEW -d "$1" com.android.chrome >/dev/null 2>&1 && sleep 3
curl -s -m 5 127.0.0.1:$PORT/json | python3 -c 'import json,sys;[print(t["id"],"|",t["title"][:50],"|",t["url"][:80]) for t in json.load(sys.stdin) if t["type"]=="page"]' | head -12
