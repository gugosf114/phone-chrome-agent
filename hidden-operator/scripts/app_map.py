#!/usr/bin/env python3
"""app_map — LEARN THE APP, not just one process.

Builds a durable map of an app on a hidden screen: each screen (by its stable
button-id fingerprint, so it's the same node even when the data changes) and which
button leads to which screen. Once mapped, you navigate anywhere by name.

  snap    <name>            record the current screen into the map
  tap     <name> "<btn>"    tap the button (fast, by name) then record where it led
  explore <name> [max]      auto-crawl SAFE buttons from here (skips send/pay/apply/…),
                            recording screens + edges (taps, snaps, presses Back)
  goto    <name> "<q>"      find a screen with a button matching q and print the route;
                            add --go to actually walk there
  show    <name>            print the learned map (screens + edges)

Reads the reader daemon's live tree ($DIR/tree.xml) — no extra connection. Taps via
hidden_drive.sh (the ~0.8 s by-name path). Map per app package in ~/.hidden-maps/.
NEVER taps an irreversible action during explore.
"""
import subprocess, os, re, json, hashlib, time, sys
from collections import Counter, deque

HERE = os.path.dirname(os.path.abspath(__file__))
ADB = os.environ.get("ADB", "adb")
MAPS = os.path.expanduser("~/.hidden-maps")
ATTR = re.compile(r'(\w+)="([^"]*)"')
# words that mean an irreversible / social action — never auto-tapped while learning
DENY = {"send","delete","pay","submit","post","call","buy","checkout","transfer",
        "purchase","sign","publish","apply","connect","follow","unfollow","message",
        "like","share","save","dismiss","report","block","comment","react","subscribe",
        "join","accept","decline","withdraw","remove","unsubscribe","logout","log out",
        "sign out","confirm","continue","next","pay now","place order"}
LAUNCHER = "com.sec.android.app.launcher"

def sh(cmd):
    return subprocess.run([ADB, "shell", cmd], capture_output=True, text=True).stdout
def read(name, f):
    return sh(f"cat /data/local/tmp/vd/{name}/{f} 2>/dev/null")
def hb_age(name):
    hb = read(name, "hb").strip()
    return (int(time.time() * 1000) - int(hb)) if hb.isdigit() else 9_000_000
def has_app(name):
    # any real app node present (not just the Samsung taskbar / launcher)?
    for m in re.finditer(r'id="([^"]+):id/', read(name, "tree.xml")):
        p = m.group(1)
        if p != "android" and not p.startswith(LAUNCHER):
            return True
    return False
def ensure_up(name):
    # the holder dies mid-task, and the reader stays alive on the dead screen — so
    # heal when the APP is missing, not just when the heartbeat is stale. `ensure`
    # respawns the screen + reader and re-opens the registered app; wait for it.
    if hb_age(name) > 4000 or not has_app(name):
        subprocess.run(["bash", f"{HERE}/hidden_display.sh", "ensure", "-n", name], capture_output=True)
        for _ in range(12):
            time.sleep(1)
            if has_app(name):
                break
def key_back(name):
    subprocess.run(["bash", f"{HERE}/hidden_display.sh", "key", "-n", name, "4"],
                   capture_output=True)
def do_tap(name, btn):
    subprocess.run(["bash", f"{HERE}/hidden_drive.sh", "do", name, btn], capture_output=True)
def reopen(name, pkg):
    subprocess.run(["bash", f"{HERE}/hidden_drive.sh", "open", name, pkg], capture_output=True)

def parse(name):
    nodes = []
    for line in read(name, "tree.xml").splitlines():
        m = dict(ATTR.findall(line))
        if m:
            nodes.append(m)
    return nodes

def pkg_of(nodes):
    c = Counter()
    for n in nodes:
        i = n.get("id", "")
        if ":id/" in i:
            p = i.split(":id/")[0]
            if p and p != "android" and not p.startswith(LAUNCHER):
                c[p] += 1
    return c.most_common(1)[0][0] if c else "unknown"

def screen_of(nodes, pkg):
    ids = sorted(set(n["id"].split(":id/")[1] for n in nodes
                     if ":id/" in n.get("id", "") and n["id"].split(":id/")[0] == pkg))
    fp = hashlib.sha1("|".join(ids).encode()).hexdigest()[:8] if ids else "empty"
    btns = [{"text": n.get("text", ""), "desc": n.get("desc", ""),
             "id": n.get("id", "").split(":id/")[-1] if ":id/" in n.get("id", "") else "",
             "cls": n.get("class", "").split(".")[-1],
             "cx": n.get("cx", ""), "cy": n.get("cy", "")}
            for n in nodes if n.get("clickable") == "true" and (n.get("text") or n.get("desc"))
            and not n.get("id", "").startswith(LAUNCHER)]   # drop the Samsung taskbar
    # a human label for the screen: the longest non-clickable text near the top
    labels = [n.get("text", "") for n in nodes
              if n.get("clickable") != "true" and n.get("text") and int(n.get("cy", "99999")) < 500]
    label = max(labels, key=len) if labels else (pkg.split(".")[-1])
    return fp, label, btns

def load(pkg):
    p = f"{MAPS}/{pkg}.json"
    return json.load(open(p)) if os.path.exists(p) else {"package": pkg, "screens": {}, "edges": []}
def save(pkg, m):
    os.makedirs(MAPS, exist_ok=True)
    json.dump(m, open(f"{MAPS}/{pkg}.json", "w"), indent=1)

def snap(name, quiet=False):
    ensure_up(name)
    nodes = parse(name)
    pkg = pkg_of(nodes)
    fp, label, btns = screen_of(nodes, pkg)
    m = load(pkg)
    scr = m["screens"].get(fp, {"label": label, "buttons": btns, "seen": 0})
    scr["label"] = label; scr["buttons"] = btns; scr["seen"] = scr.get("seen", 0) + 1
    m["screens"][fp] = scr
    save(pkg, m)
    if not quiet:
        print(f"[map] {pkg}  screen {fp}  \"{label}\"  {len(btns)} buttons")
    return pkg, fp, label, btns

def add_edge(pkg, frm, btn, to):
    m = load(pkg)
    e = {"from": frm, "btn": btn, "to": to}
    if e not in m["edges"]:
        m["edges"].append(e); save(pkg, m)

def btn_name(b):
    return (b["text"] or b["desc"]).strip()

def safe(b):
    nm = btn_name(b).lower()
    if not nm: return False
    if b["cls"] in ("Switch", "CheckBox", "ToggleButton", "SwitchCompat"): return False
    return not any(w in nm for w in DENY)

def cmd_snap(name): snap(name)

def cmd_tap(name, btn):
    pkg, f0, _, _ = snap(name, quiet=True)
    do_tap(name, btn); time.sleep(0.8)
    _, f1, lbl, _ = snap(name, quiet=True)
    if f1 != f0:
        add_edge(pkg, f0, btn, f1)
        print(f"[map] {btn!r}: {f0} -> {f1}  \"{lbl}\"")
    else:
        print(f"[map] {btn!r}: stayed on {f0}")

def cmd_explore(name, mx=12):
    mx = int(mx)
    pkg, base, base_label, base_btns = snap(name)
    print(f"[map] explore from {base} \"{base_label}\" — up to {mx} safe buttons")
    tried = 0
    for b in [x for x in base_btns if safe(x)]:
        if tried >= mx: break
        nm = btn_name(b)
        do_tap(name, nm); time.sleep(1.2)
        _, f1, lbl, _ = snap(name, quiet=True)
        if f1 != base:
            add_edge(pkg, base, nm, f1)
            print(f"  + {nm!r} -> {f1} \"{lbl}\"")
        else:
            print(f"  · {nm!r} (no new screen)")
        # return to the base screen: cheap Back first, relaunch the app if it drifted
        key_back(name); time.sleep(1.2)
        _, fb, _, _ = snap(name, quiet=True)
        if fb != base:
            reopen(name, pkg); time.sleep(3.0); snap(name, quiet=True)
        tried += 1
    m = load(pkg)
    print(f"[map] {pkg}: {len(m['screens'])} screens, {len(m['edges'])} edges learned")

def cmd_goto(name, q, go=False):
    pkg, cur, _, _ = snap(name, quiet=True)
    m = load(pkg); ql = q.lower()
    targets = [fp for fp, s in m["screens"].items()
               if any(ql in (btn_name(b).lower()) for b in s["buttons"]) or ql in s["label"].lower()]
    if not targets:
        print(f"[map] nothing matching '{q}' in the learned map — explore more first"); return
    # BFS over edges
    adj = {}
    for e in m["edges"]:
        adj.setdefault(e["from"], []).append((e["btn"], e["to"]))
    prev = {cur: None}; q1 = deque([cur])
    while q1:
        u = q1.popleft()
        if u in targets: break
        for btn, v in adj.get(u, []):
            if v not in prev:
                prev[v] = (u, btn); q1.append(v)
    dest = next((t for t in targets if t in prev), None)
    if dest is None:
        print(f"[map] '{q}' is on a known screen but no route from here yet — explore more"); return
    path = []
    node = dest
    while prev.get(node):
        u, btn = prev[node]; path.append(btn); node = u
    path.reverse()
    print(f"[map] route to '{q}' ({dest}): " + (" -> ".join(f"tap {p!r}" for p in path) or "(already here)"))
    if go:
        for p in path:
            do_tap(name, p); time.sleep(1.0)
        print("[map] arrived")

def cmd_show(name):
    nodes = parse(name); pkg = pkg_of(nodes)
    m = load(pkg)
    print(f"=== app map: {pkg} ===  {len(m['screens'])} screens, {len(m['edges'])} edges")
    for fp, s in m["screens"].items():
        names = ", ".join(sorted({btn_name(b) for b in s["buttons"] if btn_name(b)}))[:160]
        print(f"  [{fp}] \"{s['label']}\" ({len(s['buttons'])} btns): {names}")
    for e in m["edges"]:
        print(f"   {e['from']} --{e['btn']!r}--> {e['to']}")

def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__); sys.exit(2)
    v, name = a[0], a[1]
    if v == "snap": cmd_snap(name)
    elif v == "tap": cmd_tap(name, a[2])
    elif v == "explore": cmd_explore(name, a[2] if len(a) > 2 else 12)
    elif v == "goto": cmd_goto(name, a[2], go=("--go" in a))
    elif v == "show": cmd_show(name)
    else: print(__doc__); sys.exit(2)

if __name__ == "__main__":
    main()
