#!/data/data/com.termux/files/usr/bin/bash
# ============================================================================
# teach_skill.sh — the "photo way": teach the phone a task ONCE, replay it by
# finding each button's photo again. Works on a HIDDEN screen (no button-names
# needed), because it matches pictures, not the accessibility tree.
#
# Teach: perform the task with `tap` (it snaps a photo of each button, saves it
# as a step, then taps). Replay: for each step, snap the screen, find that photo,
# tap where it is now — so it survives the button moving a little.
#
#   new    <name>                 start/clear a skill
#   tap    <name> <cx> <cy> [r]   record ONE step (snap+crop photo, then tap it)
#   steps  <name>                 show the recorded steps
#   replay <name>                 run the whole skill by photo-match
#   list                          list skills
#   drop   <name>                 delete a skill
#
# Targets hidden screen $HD_NAME (default "main"); skills live in $HD_SKILLS
# (default ~/.hidden-skills). Needs python3 + PIL (+ OpenCV or NumPy) for matching.
# ============================================================================
set -u
_HERE=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || _HERE=.
HD="$_HERE/hidden_display.sh"
MATCH="$_HERE/../tools/hidden-display/match.py"
: "${HD_NAME:=main}"
SKILLS="${HD_SKILLS:-$HOME/.hidden-skills}"

CMD="${1:-}"; NAME="${2:-}"
DIR="$SKILLS/$NAME"
_shot(){ bash "$HD" shot -n "$HD_NAME" "$1" >/dev/null; }

case "$CMD" in
  new)
    [ -n "$NAME" ] || { echo "usage: new <name>"; exit 2; }
    rm -rf "$DIR"; mkdir -p "$DIR"; : > "$DIR/steps.tsv"; echo "[skill] new '$NAME' (screen $HD_NAME)" ;;
  tap)
    [ -d "$DIR" ] || { echo "[skill] no skill '$NAME' — run: new $NAME"; exit 1; }
    CX="${3:-}"; CY="${4:-}"; R="${5:-90}"
    [ -n "$CX" ] && [ -n "$CY" ] || { echo "usage: tap <name> <cx> <cy> [r]"; exit 2; }
    IDX=$(printf '%03d' "$(( $(wc -l < "$DIR/steps.tsv") + 1 ))")
    F=$(mktemp --suffix=.png); _shot "$F" || { echo "[skill] no frame"; exit 1; }
    python3 - "$F" "$DIR/$IDX.png" "$CX" "$CY" "$R" <<'PY'
import sys
from PIL import Image
f,out,cx,cy,r = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
im=Image.open(f); W,H=im.size
im.crop((max(0,cx-r),max(0,cy-r),min(W,cx+r),min(H,cy+r))).save(out)
PY
    printf '%s\t%s\t%s\t%s\n' "$IDX" "$CX" "$CY" "$R" >> "$DIR/steps.tsv"
    bash "$HD" tap -n "$HD_NAME" "$CX" "$CY" >/dev/null
    echo "[skill] $NAME step $IDX: saved photo + tapped ($CX,$CY)" ;;
  steps)
    cat "$DIR/steps.tsv" 2>/dev/null || echo "[skill] no skill '$NAME'" ;;
  replay)
    [ -d "$DIR" ] || { echo "[skill] no skill '$NAME'"; exit 1; }
    # read steps on FD 3 so adb/python inside the loop can't eat the step list
    while IFS=$'\t' read -r -u 3 IDX CX CY R; do
      [ -n "${IDX:-}" ] || continue
      F=$(mktemp --suffix=.png); _shot "$F" || { echo "[skill] no frame"; exit 1; }
      read MX MY CONF < <(python3 "$MATCH" "$F" "$DIR/$IDX.png" --near "$CX" "$CY" 220)
      OK=$(python3 -c "print(1 if float('${CONF:-0}')>=0.55 else 0)")
      if [ "$OK" = 1 ]; then TX=$MX; TY=$MY; NOTE=""; else TX=$CX; TY=$CY; NOTE=" (low conf, taught spot)"; fi
      bash "$HD" tap -n "$HD_NAME" "$TX" "$TY" >/dev/null </dev/null
      echo "[skill] step $IDX: conf=$CONF -> tap ($TX,$TY)$NOTE"
      sleep 0.6
    done 3< "$DIR/steps.tsv" ;;
  list) ls -1 "$SKILLS" 2>/dev/null || echo "(no skills)" ;;
  drop) rm -rf "$DIR"; echo "[skill] dropped '$NAME'" ;;
  *) echo "usage: teach_skill.sh new|tap|steps|replay|list|drop <name> [args]" >&2; exit 2 ;;
esac
