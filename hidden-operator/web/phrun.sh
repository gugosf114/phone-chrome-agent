#!/bin/bash
# phrun.sh — drive a survey on the phone Chrome, auto-answering questions, and at every
# HUMAN GATE (drag / captcha / watch-video) it SPEAKS the instruction to George and waits
# for him to do it, then resumes. Runs until the survey ENDS. George never touches the
# terminal — he just listens and taps the gate on the Chrome screen.
export ANDROID_SERIAL=127.0.0.1:5555
adb forward tcp:9333 localabstract:chrome_devtools_remote >/dev/null 2>&1
S=/tmp/claude-0/-root/230036e1-2b32-446e-bae1-9fd1e19755b1/scratchpad
BLOB=$(base64 -w0 /root/hchrome/pauto1.js)
speak(){ say "$1" >/dev/null 2>&1 & }
lastgate=""; gatehits=0; answered=0
speak "Okay. I am driving the survey now. Just watch. I will tell you when to tap."
for i in $(seq 1 140); do
  timeout 22 bash -c "CDP_PORT=9333 node /root/hchrome/pdrive.cjs active 300 '$S/pr' '$BLOB'" >/dev/null 2>&1
  R=$(python3 -c "import json;print(json.load(open('$S/pr.log.json'))[-1]['result'])" 2>/dev/null)
  SAY=$(printf '%s' "$R" | python3 -c "import sys,json;
try: print(json.load(sys.stdin).get('say',''))
except: print('')" 2>/dev/null)
  case "$R" in
    *'"stop":"END"'*|*'"stop": "END"'*)
      speak "Done. You finished the survey. Nice work."; echo "END $R"; break;;
    *DRAG*|*CAPTCHA*|*VIDEO*)
      G=$(printf '%s' "$R" | grep -oE 'DRAG|CAPTCHA|VIDEO' | head -1)
      if [ "$G" != "$lastgate" ]; then speak "$SAY"; lastgate="$G"; gatehits=0; echo "GATE $G -> spoke: $SAY";
      else gatehits=$((gatehits+1)); [ $((gatehits % 8)) -eq 0 ] && speak "$SAY"; fi
      sleep 3;;
    "" )
      FG=$(adb shell "dumpsys activity activities 2>/dev/null|grep -m1 topResumedActivity|grep -o com.android.chrome||echo NO")
      echo "empty (fg=$FG)"; [ "$FG" = "NO" ] && speak "Please go back to the survey screen."; sleep 3;;
    *)
      lastgate=""; answered=$((answered+1)); echo "[$i] ans#$answered $R";;
  esac
  sleep 1.3
done
BAL=$(timeout 15 bash -c "CDP_PORT=9333 node /root/hchrome/pdrive.cjs active 400 '$S/prbal' \"\$(printf 'JSON.stringify({bal:(document.querySelector(\"#sbListItemNav\")||{}).innerText||\"?\",u:location.href.slice(0,50)})' | base64 -w0)\"" 2>&1; python3 -c "import json;print(json.load(open('$S/prbal.log.json'))[-1]['result'])" 2>/dev/null)
echo "ANSWERED=$answered  FINAL=$BAL"
