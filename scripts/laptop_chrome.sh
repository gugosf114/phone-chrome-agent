#!/bin/bash
# laptop_chrome.sh — the laptop's real (headed) Chrome, started by its scheduled task, tunneled to this box.
# Proven 2026-10-14 18:28: Home Depot search page opened and listed products in 11 s.
#   bash laptop_chrome.sh            -> start the task if needed, hold the tunnel, print tabs; leaves the tunnel running (pid in /tmp/laptop_tunnel.pid)
#   bash laptop_chrome.sh <url>      -> same, then open <url> in a new tab
#   CDP_PORT=19222 node /root/.play/cdp.cjs 'homedepot.com' '<js>'   -> drive it like any Chrome
# Notes: the laptop's 9224 Chrome is HEADLESS (bouncers reject it). Use the 9222 one from task "GeorgeJobApplicationsChrome".
# A Chrome started by Start-Process over ssh dies when the ssh session ends; the scheduled task is what survives.
# Tunnel must bind 127.0.0.1 explicitly; a detached (setsid) ssh died here, a plain backgrounded one holds.
PORT=${CDP_PORT:-19222}
ssh -o ConnectTimeout=15 -o BatchMode=yes wimlaptop 'powershell -NoProfile -Command "try { $null = Invoke-WebRequest -UseBasicParsing -TimeoutSec 4 http://127.0.0.1:9222/json/version; \"up\" } catch { schtasks /run /tn GeorgeJobApplicationsChrome | Out-Null; Start-Sleep 8; \"started\" }"' 2>/dev/null
if ! curl -s -m 4 127.0.0.1:$PORT/json/version | grep -q Browser; then
  # tunnel output goes to /dev/null so it cannot hold this script's pipe open after we exit
  ssh -o ConnectTimeout=15 -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=20 -N -L 127.0.0.1:$PORT:127.0.0.1:9222 wimlaptop >/dev/null 2>&1 &
  echo $! > /tmp/laptop_tunnel.pid
  for i in $(seq 1 12); do curl -s -m 2 127.0.0.1:$PORT/json/version | grep -q Browser && break; sleep 0.5; done
fi
curl -s -m 6 127.0.0.1:$PORT/json/version | grep -q Browser || { echo "laptop Chrome not reachable on $PORT"; exit 1; }
[ -n "$1" ] && curl -s -m 12 -X PUT "127.0.0.1:$PORT/json/new?$1" >/dev/null && sleep 1.5
# bring the window in front of George (runs inside his desktop session via the interactive task ShowAgentChrome)
ssh -o ConnectTimeout=10 -o BatchMode=yes wimlaptop "schtasks /run /tn ShowAgentChrome" >/dev/null 2>&1
curl -s -m 6 127.0.0.1:$PORT/json | python3 -c 'import json,sys;[print(t["id"],"|",t["title"][:50],"|",t["url"][:80]) for t in json.load(sys.stdin) if t["type"]=="page"]' | head -10
