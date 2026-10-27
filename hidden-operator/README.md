# hidden-operator

**Operate the phone and the web on screens nobody sees, learn each flow once, then fire it fast.**
One phone, one door (`bin/op`), two halves that share one learning brain.

- **Hidden screens** — extra Android displays the physical panel never shows. Open any app on one,
  read its buttons *by name* from the accessibility tree, tap them (~0.8 s), while the owner keeps
  using the real screen. A keeper brings a dead screen back in seconds. → `HIDDEN-SCREEN.md`
- **Web agent** — a headless Chrome (CDP) that observes an unfamiliar site, fires a saved recipe fast,
  and stops before any money step. Proven on OpenTable: sign in, book, cancel — hands-free.
  Signed-in bookings need no per-booking SMS. → `web/README.md`
- **Learning brain** — versioned skills: propose → trial → evaluate on ≥2 inputs → promote. Real
  executions are the only evidence; a repeated request id never redoes a real action. → `LEARNING.md`

## The one door
```
bin/op screen start -n main phone          # a screen only the agent sees
bin/op screen launch -n main com.android.chrome
bin/op drive  seq main 7 plus 8            # tap buttons by name
bin/op sms    latest 1                     # read the phone's own text code
bin/op web    start                        # headless Chrome on 127.0.0.1:9222
bin/op web    observe <tab>                # every link/button/input + selector
bin/op web    run <tab> skill.json [--arm] # fire a recipe; STOPS before buy/pay unless --arm
bin/op web    book "Las Vegas"             # scripted OpenTable booker (identity from web/booker.env)
bin/op learn  schema                       # the skill runtime
bin/op browse list                         # persistent browser tasks
bin/op keeper boot                         # keep hidden screens alive (uses timer-add if installed)
```

## Layout
```
scripts/   hidden_display.sh  hidden_drive.sh  hidden_supervisor.sh  ui.sh  app_map.py
           teach_skill.sh  read_sms_code.sh  authority_core.sh  boot/start-hidden-operator
tools/hidden-display/   VD.java+vd.dex (display holder)  UD.java+ud.dex (shared reader)  match.py  frame_to_png.py
web/       phone-chrome.sh  ← the signed-in browser: Chrome Beta on the hidden screen "web", CDP 9335
           start.sh  cookies.cjs  shot.cjs  viewer.sh   ← Linux hidden Chrome (no Google login; pull-logins retired)
           webfast.cjs  pg.cjs  ot_book.cjs  drive*.cjs  booker.env.example  ← web agent
runtime/task-engine/   the learning brain (agent_bridge_task) + 130 tests
docs/research/         blueprint + Experiment 01 (not yet run)
```

## Setup on the phone
1. `cp web/booker.env.example web/booker.env` — your name/email/phone (gitignored, never committed).
2. `bash web/start.sh` — headless Chrome. `bin/op web logins` copies your real Chrome's logins into it.
3. `ln -s $PWD/scripts/boot/start-hidden-operator ~/.termux/boot/` — screens survive reboot.
4. Timers: use `timer-add <id> <ms> <script>` (one hook = one script). The keeper does this itself.

## Verify
```
(cd runtime/task-engine && python3 -m unittest discover -s tests -v)   # 130 tests
bash tests/test_learning_dispatch.sh
```

Lifted out of `gugosf114/agent-bridge` on 2026-09-22 (which stays intact). Never commit
`web/profile/` (live cookies/logins) or `booker.env`.

## Read an app like a web page (2026-10-26)

An app is a keyhole: the accessibility tree holds only what is drawn, one screenful. Two fixes, both proven on Settings:

1. **A tall screen.** `scripts/hidden_display.sh start -n tall 1080 6000 420` then `launch -n tall <pkg>`. The app lays out
   six screens of rows at once. Settings: all 31 rows in ONE read, no scroll. Most apps take any height; a few cap their own.
   (A second model claimed a private virtual display does not reflow the app and said to resize the REAL screen with `wm size`.
   Wrong on both counts here: the hidden screen reflowed Settings, and `wm size` would wreck George's own screen. Never run it.)
2. **Scroll and stitch.** `scripts/read_all.sh -n <screen> [max_pages] [--buttons]`. Finds the list itself (RecyclerView /
   ListView, else the biggest scrollable view), scrolls it to the top with the accessibility action, reads the tree, asks the
   list to scroll_forward one page, reads again, until Android answers "false" = the true bottom. No swipe, so no fling and no
   pull-to-refresh (a swipe once flung Settings off into the launcher). Rows cut by the screen edge are skipped. Furniture
   (status bar, nav bar, taskbar, sticky titles) is dropped. Overlap merged. One blob, in order. The whole loop runs on the
   phone in ONE adb round trip, through the reader's request/response files. Settings, 1080x2400: 33 rows, true bottom, 12 s.
   Apps with no scrollable view in the tree fall back to finger swipes. `--buttons` adds `cx cy` per row for a later tap.
   Trap found 10/26: the phone shell (mksh) does 32-bit math, so milliseconds overflow; build the deadline as seconds + "000".

Addresses: many apps export deep links. `am start --display <id> -a android.intent.action.VIEW -d '<app-link>'` lands on that
screen with no taps; then stitch. Check an app's exported links when mapping it (`app_map.py`). Blank-tree apps: `dumpsys activity
top` prints no text on this Samsung (checked 10/26); use the photo fallback.
