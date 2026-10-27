#!/usr/bin/env bash
set -euo pipefail
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
export HOME="$WORK/home"
mkdir -p "$HOME"
bash "$ROOT/bin/op" learn --db "$WORK/skills.db" schema > "$WORK/schema.json"
python3 - "$WORK/schema.json" <<'PY'
import json,sys
value=json.load(open(sys.argv[1]))
assert "trial" in value["operations"] and "promote" in value["operations"]
PY
payload=$(python3 - <<'PY'
import json,base64
request=json.dumps({"operation":"catalog","query":"new\nline"},indent=2)
print(base64.b64encode(json.dumps({"tool":"learn","arguments":["request","--json",request]}).encode()).decode())
PY
)
bash "$ROOT/bin/op" --b64 "$payload" > "$WORK/catalog.json"
python3 - "$WORK/catalog.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1])) == []
PY
echo 'Learning dispatch: schema and newline-preserving transport passed'
