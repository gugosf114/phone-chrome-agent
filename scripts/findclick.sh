#!/bin/bash
# findclick.sh <tabSub> <exact-or-regex text> [nth]  — scroll the smallest element whose text matches into view, real-click its center
D=$(dirname "$0"); export NODE_PATH=/root/mbc-analytics/node_modules
TAB="$1"; RX="$2"; N="${3:-0}"
P=$(node $D/cdpx.cjs eval "$TAB" "(()=>{const rx=new RegExp($(python3 -I -c 'import json,sys;print(json.dumps(sys.argv[1]))' "$RX"),'i');const all=[];const walk=n=>{if(!n)return;if(n.nodeType===1){if(n.shadowRoot)walk(n.shadowRoot);for(const c of n.children)walk(c);const t=(n.innerText||'').trim();if(t&&rx.test(t)&&t.length<200){const r=n.getBoundingClientRect();if(r.width>0&&r.height>0)all.push(n)}}};walk(document.body);const leafs=all.filter(e=>!all.some(o=>o!==e&&e.contains(o)));const e=leafs[$N];if(!e)return 'NONE '+leafs.length;e.scrollIntoView({block:'center',inline:'center'});const r=e.getBoundingClientRect();return Math.round(r.x+r.width/2)+' '+Math.round(r.y+r.height/2)})()" | tr -d '"')
case "$P" in NONE*) echo "not found: $RX ($P)"; exit 1;; esac
node $D/cdpx.cjs click "$TAB" $P
