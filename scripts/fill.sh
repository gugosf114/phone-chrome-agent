#!/bin/bash
# fill.sh <tabSub> <aria-label exact> <text>  — focus the input by aria-label, clear it, type text key by key, Tab
D=$(dirname "$0"); export NODE_PATH=/root/mbc-analytics/node_modules
TAB="$1"; LABEL="$2"; TEXT="$3"
L=$(python3 -I -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$LABEL")
R=$(node $D/cdpx.cjs eval "$TAB" "(()=>{let f=null;const walk=n=>{if(!n||f)return;if(n.nodeType===1){if((n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&(n.getAttribute('aria-label')||'')===$L){f=n;return}if(n.shadowRoot)walk(n.shadowRoot);for(const c of n.children)walk(c)}};walk(document.body);if(!f)return 'NOFIELD';f.scrollIntoView({block:'center'});f.focus();f.select();return 'ok'})()" | tr -d '"')
[ "$R" = "ok" ] || { echo "no field: $LABEL"; exit 1; }
node $D/cdpx.cjs key "$TAB" Backspace >/dev/null
node $D/cdpx.cjs chars "$TAB" "$TEXT" >/dev/null
V=$(node $D/cdpx.cjs eval "$TAB" "(()=>{let f=null;const walk=n=>{if(!n||f)return;if(n.nodeType===1){if((n.tagName==='INPUT'||n.tagName==='TEXTAREA')&&(n.getAttribute('aria-label')||'')===$L){f=n;return}if(n.shadowRoot)walk(n.shadowRoot);for(const c of n.children)walk(c)}};walk(document.body);return f.value})()")
echo "$LABEL = $V"
