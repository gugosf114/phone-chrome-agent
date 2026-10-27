#!/bin/bash
# chrome.sh — open the back door to the phone's OWN Chrome (the browser that passes every bouncer).
# Run from the Debian box on the phone (Termux → proot). Needs adb connected (127.0.0.1:5555).
#   bash chrome.sh            -> wake Chrome, forward its DevTools socket to 127.0.0.1:9336, print tabs
#   bash chrome.sh <url>      -> same, then open <url> in Chrome
PORT=${CDP_PORT:-9336}
# 10/26: the freeze is fixed (anti_freeze.sh + sticky unfreeze), so a backgrounded Chrome answers. Only pull Chrome to the
# front if its socket is really dead, so George's screen is left alone when it is not needed.
probe() { for S in chrome_devtools_remote_$(adb shell pidof com.android.chrome | tr -d '\r' | awk '{print $1}') chrome_devtools_remote; do adb forward --remove tcp:$PORT >/dev/null 2>&1; adb forward tcp:$PORT localabstract:$S >/dev/null 2>&1; curl -s -m 4 127.0.0.1:$PORT/json/version | grep -q '"com.android.chrome"' && return 0; done; return 1; }
probe || adb shell am start -n com.android.chrome/com.google.android.apps.chrome.Main >/dev/null 2>&1   # bring Chrome to front only when its socket is dead
adb shell am unfreeze --sticky com.android.chrome >/dev/null 2>&1   # 10/26: per-app hold so the freezer leaves Chrome alone; dies with the process or a reboot, so re-run every open
sleep 1
# whichever Chrome started first owns the bare socket name; the other gets _<pid>. They SWAP when one restarts. Pick by app name, never by memory.
probe
curl -s -m 4 127.0.0.1:$PORT/json/version | grep -q Browser || { echo "no answer from Chrome on $PORT (is it frozen? see anti_freeze.sh)"; exit 1; }
[ -n "$1" ] && adb shell am start -a android.intent.action.VIEW -d "$1" com.android.chrome >/dev/null 2>&1 && sleep 3
curl -s -m 5 127.0.0.1:$PORT/json | python3 -c 'import json,sys;[print(t["id"],"|",t["title"][:50],"|",t["url"][:80]) for t in json.load(sys.stdin) if t["type"]=="page"]' | head -12
