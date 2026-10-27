#!/bin/bash
# phone-chrome.sh — the signed-in browser. Chrome Beta on George's phone, on the hidden screen "web".
# It is signed in by the phone's own Google account (tapped "Continue as George" once, 2026-09-26).
# Nothing is copied: the phone keeps the login alive the same way it keeps his daily Chrome alive.
# The keeper re-makes the "web" screen and re-opens Chrome Beta if Android kills either one.
#
#   phone-chrome.sh up      make sure it runs; forward its debug port to 127.0.0.1:9335 (default verb)
#   phone-chrome.sh check   print which Google accounts are live in it (from Google itself)
#
# Drive it with any CDP tool on port 9335, e.g.:
#   CDP_PORT=9335 node /root/.play/cdp.cjs play.google.com '<js>'
# Open a page by setting location.href on an existing tab (/json/new is refused on Android).
HERE=$(cd "$(dirname "$0")" && pwd); ROOT=$(cd "$HERE/.." && pwd)
. "$ROOT/scripts/phone_env.sh" >/dev/null 2>&1
PKG=com.chrome.beta; SCREEN=web; PORT=${PHONE_CHROME_PORT:-9335}
HD="$ROOT/scripts/hidden_display.sh"

up() {
  adb shell pm path $PKG >/dev/null 2>&1 || { echo "Chrome Beta is not installed on the phone"; return 1; }
  bash "$HD" status -n $SCREEN >/dev/null 2>&1 || bash "$HD" start -n $SCREEN phone >/dev/null 2>&1
  PID=$(adb shell pidof $PKG 2>/dev/null | tr -d '\r' | awk '{print $1}')
  if [ -z "$PID" ]; then bash "$HD" launch -n $SCREEN $PKG >/dev/null 2>&1; sleep 4
    PID=$(adb shell pidof $PKG 2>/dev/null | tr -d '\r' | awk '{print $1}'); fi
  [ -n "$PID" ] || { echo "Chrome Beta did not start"; return 1; }
  # Whichever Chrome starts first takes the bare chrome_devtools_remote; the other gets _<pid>.
  # So ask each socket which app it is, and keep the one that says Chrome Beta.
  SOCKS=$(adb shell cat /proc/net/unix | tr -d '\r' | grep -o '@chrome_devtools_remote[^ ]*' | tr -d '@' | sort -u)
  for s in chrome_devtools_remote_$PID $SOCKS; do
    adb forward --remove tcp:$PORT >/dev/null 2>&1
    adb forward tcp:$PORT localabstract:$s >/dev/null 2>&1 || continue
    curl -s -m 5 127.0.0.1:$PORT/json/version | grep -q "\"Android-Package\": \"$PKG\"" \
      && { echo "phone chrome up: cdp=127.0.0.1:$PORT (Chrome Beta, pid $PID, socket $s, hidden screen $SCREEN)"; return 0; }
  done
  adb forward --remove tcp:$PORT >/dev/null 2>&1
  echo "no debug socket answered as Chrome Beta"; return 1
}

check() {
  up >/dev/null || { up; return 1; }
  NODE_PATH=${NODE_PATH:-/root/mbc-analytics/node_modules} PORT=$PORT node - <<'EOF'
const WebSocket=globalThis.WebSocket||require('ws'); const P=process.env.PORT;
(async()=>{
  const tabs=await (await fetch(`http://127.0.0.1:${P}/json`)).json();
  const t=tabs.find(x=>x.type==='page'); if(!t){console.log('no tab open');process.exit(1)}
  const ws=new WebSocket(t.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
  // ListAccounts is what Chrome itself asks Google; [9]=valid, [14]=signed out.
  const expr=`fetch("https://accounts.google.com/ListAccounts?gpsia=1&source=ChromiumBrowser&json=standard",{method:"POST",credentials:"include"}).then(r=>r.text())`;
  ws.send(JSON.stringify({id:1,method:'Runtime.evaluate',params:{expression:expr,awaitPromise:true,returnByValue:true}}));
  ws.onmessage=m=>{const d=JSON.parse(m.data); if(d.id!==1)return;
    try{ const a=JSON.parse(d.result.result.value)[1]||[];
      if(!a.length) console.log('no Google accounts in it');
      for(const x of a) console.log(`${x[3]}: ${x[9]===1&&x[14]!==1?'signed in':'SIGNED OUT'}`);
    }catch(e){ console.log('could not read accounts:', d.result?.result?.value||e.message) }
    process.exit(0)};
})();
EOF
}

case "${1:-up}" in up) up;; check) check;; *) echo "usage: phone-chrome.sh [up|check]"; exit 2;; esac
