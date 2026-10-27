#!/bin/bash
# Sign-in viewer: shows the hidden Chrome screen inside the phone's normal Chrome at http://127.0.0.1:6080/vnc.html
# George uses it once per site to log in, or to pass a captcha. `viewer.sh off` hides it again.
LOG=/root/hchrome/logs; mkdir -p "$LOG"
if [ "$1" = "off" ]; then pkill -x x11vnc; pkill -f "websockify.*6080"; echo "viewer off"; exit 0; fi
pgrep -x x11vnc >/dev/null || (setsid nohup x11vnc -display :5 -localhost -rfbport 5905 -forever -shared -nopw -noxdamage -quiet >"$LOG/x11vnc.log" 2>&1 < /dev/null &)
pgrep -f "websockify.*6080" >/dev/null || (setsid nohup websockify --web /usr/share/novnc 127.0.0.1:6080 127.0.0.1:5905 >"$LOG/novnc.log" 2>&1 < /dev/null &)
sleep 2; curl -s -m 3 -o /dev/null -w "viewer http %{http_code}\n" "http://127.0.0.1:6080/vnc.html"
echo "open on the phone: http://127.0.0.1:6080/vnc.html?autoconnect=1&resize=scale"
