#!/bin/bash
# marks.sh — read the phone's current screen into NUMBERED buttons (set-of-marks), then tap by number.
#   marks.sh read        screenshot + accessibility dump -> annotated png + numbered list
#   marks.sh tap <n>     tap the center of element <n> from the last read
# Uses Android's own uiautomator (the real UI element tree) + a screenshot. No heavy model.
export ANDROID_SERIAL=127.0.0.1:5555
S=/tmp/claude-0/-root/230036e1-2b32-446e-bae1-9fd1e19755b1/scratchpad
case "$1" in
  read)
    fg(){ adb shell "dumpsys activity activities 2>/dev/null | grep -m1 topResumedActivity" 2>/dev/null | grep -oE 'u0 [A-Za-z0-9_./]+' | head -1; }
    OK=""; DUMPED=0
    for try in 1 2 3 4; do
      adb shell "rm -f /sdcard/window_dump.xml /sdcard/marks_shot.png" >/dev/null 2>&1   # no stale reuse
      A=$(fg)
      # ONE on-device breath: photo then fresh button-list, back to back
      D=$(adb shell "screencap -p /sdcard/marks_shot.png; uiautomator dump /sdcard/window_dump.xml 2>&1")
      B=$(fg)
      echo "$D" | grep -q 'dumped to' && DUMPED=1 || DUMPED=0
      if [ -n "$A" ] && [ "$A" = "$B" ] && [ "$DUMPED" = 1 ]; then OK="$A"; break; fi
      echo "grab $try no good (fg $A->$B, dumped=$DUMPED) — retry"
      sleep 0.6
    done
    adb pull /sdcard/marks_shot.png "$S/marks_shot.png" >/dev/null 2>&1
    adb pull /sdcard/window_dump.xml "$S/window_dump.xml" >/dev/null 2>&1
    if [ "$DUMPED" != 1 ]; then echo "NO BUTTONS on this screen (a terminal/video has none). Use CDP for web, or open a real-UI app."; exit 0; fi
    echo "screen held still: $OK"
    python3 /root/hchrome/marks.py "$S/marks_shot.png" "$S/window_dump.xml" "$S/marks_annot.png" "$S/marks_list.json"
    echo "annotated: $S/marks_annot.png"
    ;;
  tap)
    N="$2"
    python3 - "$N" <<'PY'
import sys,json
n=int(sys.argv[1]); L=json.load(open('/tmp/claude-0/-root/230036e1-2b32-446e-bae1-9fd1e19755b1/scratchpad/marks_list.json'))
e=next((x for x in L if x['n']==n),None)
print(f"{e['cx']} {e['cy']} {e['t']}" if e else "NONE")
PY
    ;;
  *) echo "usage: marks.sh read | tap <n>";;
esac
