**Download (2026-10-26):** https://github.com/gugosf114/phone-chrome-agent/archive/refs/heads/main.zip

# phone-chrome-agent

The agent drives a real, headed Chrome on George's own machines. One command, one pass, no second look.

Read this file first. It is the whole story, so no session has to be told "remember when we did this."

## Start here (state as of 2026-10-17, 9:30 am)

- **Read "The menu" below to pick an option fast** (who does the work, where the browser lives, where the hands live, how the model sees), one good-for / bad-at line each.
- **The picker reads `me/george-dossier.md`, `me/writings.md`, `me/assets.md`, and `me/resume-master.md` before any pick or letter.** (2026-10-26)
- **Read `me/george-dossier.md` before picking jobs or writing a cover letter.** Who George is, what he built, YES and NO job lanes, how to write. The thinker reads it once per batch; the script never needs it.
- **Read `the-map.md` for what an agent is, in our words:** brain / hands / handbook, the three ways to do a task (Fable, sent model, dumb script), think-once-run-once, the leash, the sandbox. Settled 2026-10-17 with the Travolta test receipts.
- **The browser pipe is the laptop's real Chrome.** One command: `bash scripts/laptop_chrome.sh "<url>"`. It starts Chrome if needed, opens the tunnel, opens the page, and puts the window on George's laptop screen. 7 to 15 seconds. The laptop Chrome is signed into LinkedIn.
- **Do not start any other Chrome on any other port.** The old ones were turned off on purpose. See "One pipeline" below.
- **The phone has two lanes, left alone.** George's own Chrome (port 9336) when he wants to watch on the phone. Chrome Beta on the hidden screen (port 9335) for Play Console and Google Ads.
- **Tasks that already work are in `recipes/`,** one card each. Read the card before doing the task. When George says "recipe it," write or update a card.
- **George's answers for forms are in `scripts/answers.json`.** Three choices are still his: email, salary, portfolio link.
- **Two sessions can push here at the same time.** Pull before you push. Never force-push.
- **Before a session closes,** add a dated entry to `journal.md` and push.

- **hidden-operator is folded in here too (2026-10-26):** [`hidden-operator/`](hidden-operator/), whole repo, byte for byte. Hidden phone screens, Chrome Beta on the hidden screen (port 9335, `hidden-operator/web/phone-chrome.sh`), the `bin/op` door. `FOLDED.md` has its history.

## The menu (every option, where it is good, where it is bad)

Pick from here. One line each so George can recall it without re-reading the story.

**Who does the work**

| Option | Good for | Bad at |
|---|---|---|
| **Fable does it, step by step** | Anything new, anything George wants to watch and steer; one-off jobs; the first run of any task | Slow: ~20 s of thinking per move; every page read lands in this chat and fills it |
| **Sent model** (helper with a brief) | Long walks whose junk should stay out of the chat; many jobs at once; cheaper model for a dumb walk | Starts blank (knows only the brief); George cannot see it; its mistakes come back stamped "done" |
| **Dumb script** (fixed clicks, no brain) | Any path already walked once; repeats; speed (6 s vs 37 s); zero tokens | Any surprise (moved button, new pop-up, captcha): it stops; needs the stop rule + a brain for the fix |
| **Think once, run once** (model writes the whole script, runs it, reads the receipt) | The target shape for every task: 37-s Easy Apply, Travolta script | Needs every fork answered up front; first run of a new site still has holes |
| **Cron loop** (alarm clock fires a script) | Anything on a schedule: mail watch, 9 am call, nightly check | Runs blind; needs a receipt and a "wake a model only if X" rule |
| **Vapi phone line** (Ava calls) | Phone-only jobs: T-Mobile dispute, bank, any hold line; George's stutter stays out of it | Costs per minute; no eyes on a screen; receipt is the transcript only; must say it is an AI |

**Where the browser lives**

| Option | Good for | Bad at |
|---|---|---|
| **Laptop headed Chrome** (port 9222, task `GeorgeJobApplicationsChrome`, tunnel 19222) | THE default pipe. Passes bouncers (Home Depot 11 s), never frozen by Android, nobody uses its screen, logged into LinkedIn | Laptop must be on and plugged in; its window is in George's desktop session (needs `ShowAgentChrome` to show it) |
| **George's phone Chrome** (`com.android.chrome`, port 9336) | His daily browser, proven 10/26 (he opened his icon, this app came up). His logins. Chrome keeps several windows: his window had 1 tab, the agent's tabs (Modal, Runpod, GitHub) sit in another window of the same app, 17 of them. Passes every bouncer (home IP, real phone); since 10/26 keeps answering in the background | Android freezes it the moment he switches apps; shares his screen; door shuts on app switch |
| **Phone Chrome Beta on the hidden screen** (`com.chrome.beta`, port 9335) | A second Chrome app, the agent's. Its own logins (George signed into Google there once), 43 tabs on 10/26. Play Console, Google Ads, without stealing his screen | Same Android freezing; hidden tabs go stale; `/json/new` refused |
| **Yana's phone** (adb `100.68.147.84:5555`, ssh 8022) | Second real phone address when one is not enough; fixing her phone from anywhere | Her screen, her apps; only touch when George says |
| **Box Chromium (headed window on an invisible X screen, Termux/proot)** | ON again 2026-10-26 (George's call). Port 9222 on the box. Start: `bash /root/hchrome/start.sh`; stop: `bash /root/hchrome/start.sh stop`. Profile `george`. | Bounced by bouncer sites (Home Depot, Bright Data sign-up); use it where there is no bouncer |
| **Laptop headless Chrome** (port 9224) | ON again 2026-10-26 (George's call). Task `GeorgeGoogleConsoleHeadless`, runs at logon. From the box: `ssh -N -L 127.0.0.1:19224:127.0.0.1:9224 wimlaptop`, then `CDP_PORT=19224`. Off: `schtasks /change /tn GeorgeGoogleConsoleHeadless /disable` | Bounced by bouncer sites ("Oops, something went wrong"); headless is a robot flag. Use it where there is no bouncer |
| **Bright Data fetcher** (`bdata scrape`, Unlocker) | Reading a page that blocks everything else (got Home Depot); clean markdown of a page | Reading only: no clicks, no login, no forms; $8/GB after the free GB |
| **Bright Data rented browser** (Browser API) | Hour-long jobs while George drives and does not need to watch | Bounced by Home Depot even after paying; out of sight makes George anxious |

**Where the agent's hands live**

| Option | Good for | Bad at |
|---|---|---|
| **Termux on George's phone** (this box) | Home. Full handbook loads every time; adb to both phones; ssh to laptop; termux-api (say, clipboard, notifications); boots with the phone | Android is the landlord (can freeze or kill it); proot translator makes file work 2-5x slower |
| **Google's Linux Terminal VM** (installed on the Z Flip 7, unopened) | Heavy file work, systemd services, Docker, Playwright; nothing phantom-killed inside | Sealed box: no phone storage, no termux-api, no boot start, reaches the phone only over Wi-Fi adb |
| **Laptop (WSL2 or the Claude desktop app)** | Real Linux with no landlord; the browser is already there; free | Handbook not there yet (so it hesitates); laptop must be awake |
| **claude.ai on the web** ("cloud session") | Nothing of ours; a rented empty box at Anthropic | None of George's files, keys, phones, or rules |
| **Rented Linux box** ($4-6/mo Hetzner/DigitalOcean) | Always on, even with the phone off; services | Data-center address gets bounced by the same sites; not home |
| **Root on the phone** | Would remove Android's wall (app-sleep list, adb forever, killers off) | Off: US Samsung bootloader locked; Knox fuse blows (Wallet, bank apps, Netflix HD, Linux Terminal) |

**How the model sees**

| Option | Good for | Bad at |
|---|---|---|
| **Whole page as text** (CDP `document.body.innerText`) | Web pages in one gulp; fast | Misses layout, hidden iframes (Google's payment box needed `cdpx.cjs`) |
| **Accessibility tree / uiautomator dump** | Phone apps; buttons by name | Keyhole, one screen at a time; fails when "could not get idle state" |
| **Screenshot** | Proof for George; captcha look; when text lies | Slow, big, costs tokens; last resort |
| **Fetcher markdown** | Clean reading of a blocked page | Reading only |

## What we were trying to do

Give the model (Claude Code, running in Termux + Debian proot on George's Samsung) a way to use the internet on George's behalf, fast, without a bouncer saying "you are a robot," and without George having to explain the setup every session.

## What we found out (2026-10-13 night, about eight hours)

1. **The phone's own Chrome walks into every site.** Home Depot, LinkedIn, Bright Data's own sign-up: all open. Every other browser we tried got bounced:
   - Linux Chromium on a fake screen inside the box: Home Depot "Oops, something went wrong." Bright Data sign-up: "we think you're a bot."
   - Chrome Beta on a hidden Android screen: gets in, but its tabs show up in George's own tab list (same app), and Android freezes it when it is not in front.
   - Bright Data's rented browser (Browser API, paid, $10): Home Depot "Error Page" and "no peers." Their page fetcher (`bdata scrape`) *did* get the Home Depot search page.
2. **The slowness was never the site. It was the model.** Three causes, measured:
   - Round trips: look, think, write one command, run, look again. 20 to 30 seconds each. An 8-step form = 4 minutes.
   - The door closing: when George switches from Chrome to Termux, Android freezes Chrome and its DevTools socket dies ("fetch failed"). Each wake costs a turn.
   - Fresh scripts, fresh holes: a drop-down that starts on "Select an option" counts as "answered"; a question the script can't answer makes it press Next into a wall.
3. **The fix is complete instructions plus one pass.** George said: "two jobs, resume on file, any number = 5, any yes/no = yes, don't think." One script, one run, LinkedIn Easy Apply submitted in **37 seconds** ("Legal Expert | Remote"). That is the target shape for everything.

## Where we looked

- Our own repos: `agent-bridge` (browser-control, hidden-chrome), `hidden-operator` (hidden screens, phone-chrome.sh). Both work, both are built for the Termux side; sessions run inside Debian one layer down, so `bridge web` says "not configured" from here. Use the scripts in this repo instead.
- Web: Bright Data docs and plugin, Browserbase pricing, Camoufox / Scrapling / curl_cffi / browser_oxide / Lightpanda (stealth and agent browsers), Web Bot Auth and Cloudflare "Markdown for Agents" (the agent-passport trend), the FP-Agent paper (arXiv 2605.01247: local agents pass, server-side agents get blocked), Open-AutoGLM / Mobile-Agent / UI-TARS (Chinese phone agents).
- A deep-research run (Gemini, prompt in `research/deep-research-prompt.md`, report in `research/`), which read Chinese Android engineering sources and gave the five fixes below with commands.

## The five fixes (the plan)

| # | Fix | State |
|---|-----|-------|
| 1 | **Freezer switch**: two Android settings so background Chrome is not frozen (`scripts/anti_freeze.sh`). Use the word `disabled`, not `0`, on Samsung One UI 8. | **RUN 2026-10-26 on George's word.** Read back: freezer `disabled`, phantom killer off, Chrome + Termux on the never-sleep list, screen stays on while charging. Freezer setting fully applies after the next reboot. Undo: `settings delete global cached_apps_freezer` etc., one per line. |
| 2 | **Silent sound in the tab**: a sub-audible audio loop makes Chrome treat the tab like a music player and never freeze it (`scripts/keepalive.js`). | written, not yet tested |
| 3 | **One-pass form script**: fills a whole multi-page form from the answer sheet, stops only on a question the sheet can't answer, returns the list (`scripts/one_pass_form.js`, from the report). | written, not yet tested on LinkedIn |
| 4 | **Answer book**: George's standing answers in plain JSON (`scripts/answers.json`): 50 question rules from Agent Bridge's LinkedIn answer sheet plus the facts from 10 job-vault packets, and a never-say-yes list. Three things for George to pick (email, salary, portfolio link) are flagged at the top of the file. | merged 10/14 |
| 5 | **Hidden screen kept alive**: the third lane for app tasks George doesn't want on his screen (`hidden-operator` repo). | exists; benefits from 1 and 2 |

Lanes, by where George is: watching → his own Chrome on his screen (he wants to see it). Driving or away for an hour → the rented browser. App tasks he does not want in his face → the hidden screen.


## We asked two research models the same question. Here is what we keep from each.

Same prompt (`research/deep-research-prompt.md`), two different models, two reports in `research/`. We read both and took the best pieces. Plain words below.

### What we take from report 1 (Gemini)

- **The phone switch that stops Android from freezing Chrome.** Two settings, typed once over adb. Written down in `scripts/anti_freeze.sh`. One warning from this report: on Samsung, use the word `disabled`, not the number `0`, or the phone may reboot in a loop.
- **The silent sound trick.** A tiny sound loop in the Chrome tab, too quiet to hear. Chrome then treats the tab like a music player and does not put it to sleep. Written down in `scripts/keepalive.js`.
- **The form-filling code.** A script that fills a whole multi-page form from the answer sheet and stops only when it hits a question the sheet does not cover. Written down in `scripts/one_pass_form.js`.
- **The "Select an option" fix.** Drop-downs that still say "Select an option" count as empty. Our first script got that wrong. This one gets it right.

### What we take from report 2 (second model)

- **Split screen first.** Before touching any phone setting, put Chrome on the top half of the screen and Termux on the bottom. Both stay awake. No risk, no settings changed.
- **The Samsung battery menus.** Settings → Apps → Chrome → Battery → Unrestricted. Settings → Battery → Background limits → take Chrome and Termux off the sleeping lists, put them on Never sleeping. Recents → app icon → Keep open. Done by hand, once.
- **Check three things, not one, when Chrome stops answering.** Is the adb tunnel up? Is the browser answering? Is the page itself answering? Tonight a live tunnel fooled us into thinking the page was alive.
- **Submit is not done until we see the receipt.** After pressing Submit, look for proof on the page. Never press Submit a second time on our own.
- **Keep real answers and test answers apart.** "Every number is 5" was a test. The real answer book has real facts: years, salary, city. Two files, never mixed.
- **A log of every run.** What was filled, what was pressed, what came back. So a question answered once is never asked twice.
- **A new lead for the hidden screen.** scrcpy 4.0 (May 2026) has a virtual-display mode with a keep-active switch. Untested on this phone. Parked as an experiment.
- **Borrow, do not switch.** Keep our own Chrome route. Borrow Mobilerun's replay-and-check code and its keep-awake service when we build the app lane.

### Where the two disagree

- Report 1 says: flip the freezer switch and add the sound, then everything stays awake. Report 2 says: nobody has proven that on a Samsung yet. Both are on the table. George decides the order.

## Machines (George decided, 2026-10-14)

- **The laptop is the browser's home.** Windows does not freeze a background Chrome, nobody uses its screen, it is plugged in, and Agent Bridge already drives its Chrome (proven Ashby submission, Aug 2026). It needs its own Chrome profile for the agent (new Chrome refuses remote control of the daily profile) and a power setting so it never sleeps.
- **Yana's phone is the second home address** (ssh over Tailscale from this box) when a second real phone browser is needed.
- **George's own phone Chrome** stays the lane for when he wants to watch.
- **Maybe later: one machine in a drawer** whose only job is to host a Chrome. A used mini PC or a spare Android. The spare Android also gives the app lane.

## The laptop lane, proven (2026-10-14, 6:28 pm)

The laptop's real Chrome opened the Home Depot search page and listed products in 11 seconds, through an ssh tunnel over Tailscale. Same page that bounced the box's Chromium, Bright Data's rented browser, and the laptop's own *headless* Chrome ("Oops, something went wrong"). Headless is a robot flag. Headed is not.

What made it work, in plain words:

- The laptop already had a scheduled task, `GeorgeJobApplicationsChrome`, that starts a real Chrome with remote control on port 9222 and its own profile. Run the task, not `Start-Process` over ssh: a Chrome started inside an ssh session dies when the session ends.
- Tunnel from the box: `ssh -N -L 127.0.0.1:19222:127.0.0.1:9222 wimlaptop` (bind 127.0.0.1 explicitly). Then drive it with `CDP_PORT=19222 node /root/.play/cdp.cjs ...` like any Chrome.
- One command does all of it: `bash scripts/laptop_chrome.sh "<url>"`.
- **Two rooms.** My ssh commands land in Windows session 0, which has no screen. Chrome lives in session 1, George's desktop. From session 0 I can open tabs through the control port but cannot show the window. To put a window in front of George, run a scheduled task made with `/it` (interactive): `ShowAgentChrome` runs `scripts/laptop_show_window.ps1` inside session 1 and brings the LinkedIn/Home Depot window to the front. Proven 10/14 7:40 pm: George saw the LinkedIn sign-in window appear.

Laptop facts (read-only check): Intel i7-1185G7 at full 3.0 GHz, not throttled, on the charger, battery at about half its original capacity, Windows 11 Home, booted 10/13 7:33 pm.

## One pipeline (George decided, 2026-10-14 ~8:30 pm)

Too many Chromes on too many ports kept tripping the model. Now there is one pipe.

**Keep:**
- Laptop: headed Chrome on port 9222, started by the task `GeorgeJobApplicationsChrome`, profile `C:\Users\georg\job-applications-chrome-profile`.
- Laptop: task `ShowAgentChrome` (puts the window in front of George).
- Laptop: task `AgentBridgeLaptop` (Windows desktop control; not a Chrome).
- Box: one tunnel, `127.0.0.1:19222` to the laptop's 9222, opened by `scripts/laptop_chrome.sh`.
- Phone: Chrome Beta on the hidden screen (port 9335: Play Console lane, Google Ads; the agent's app) and George's own Chrome (port 9336, `com.android.chrome`, his daily browser; the agent's tabs live in a second window of it). Separate machine, separate lane, left alone.

**Retired** (turned off, not deleted; XML backups in `C:\Users\georg\retired-chrome-tasks-2026-10-14\`):
- `CaptureCurrentChrome`, `OpenMainChrome`, `OpenMainChromeFinal`, `OpenMainChromeInspect`, `OpenSavedGoogleChrome`, `StartChromeBridge` (one-time launchers from old experiments).
- `GeorgeGoogleConsoleHeadless` (ran at every logon: a headless Chrome on 9224 for the old Analytics/Search Console reader; the API does that job). Its Chrome and daemon were stopped. **Turned back ON 2026-10-26 on George's word**, together with the box's hidden Chromium on 9222. Rule from George: we know where a headless works and where it does not; we pick, we take the hit.
- Tonight's dead try on 9229 and its `C:\agent-chrome` profile folder: removed. Leftover box tunnels: closed.

**Bring one back:** on the laptop, `schtasks /change /tn <name> /enable`. Or re-import: `schtasks /create /tn <name> /xml C:\Users\georg\retired-chrome-tasks-2026-10-14\<name>.xml`.

## Every line that worked, for Termux (Debian proot on the phone)

Open the door to the phone's Chrome and list tabs (also wakes Chrome and re-forwards the port):

```bash
bash scripts/chrome.sh
bash scripts/chrome.sh "https://www.linkedin.com/feed/"
```

What `chrome.sh` does by hand, if you need the pieces:

```bash
adb shell am start -n com.android.chrome/com.google.android.apps.chrome.Main   # Chrome to front
P=$(adb shell pidof com.android.chrome | tr -d '\r' | awk '{print $1}')
adb forward tcp:9336 localabstract:chrome_devtools_remote_$P                   # or ..._remote (bare) if that one answers
curl -s 127.0.0.1:9336/json/version | grep Android-Package                     # must say com.android.chrome
curl -s 127.0.0.1:9336/json                                                    # tabs
```

Run JavaScript in a tab / navigate (driver from `/root/.play/cdp.cjs`, port via `CDP_PORT`):

```bash
CDP_PORT=9336 node /root/.play/cdp.cjs 'linkedin.com' 'location.href="https://www.linkedin.com/jobs/"; "nav"' - 7000
CDP_PORT=9336 node /root/.play/cdp.cjs 'linkedin.com' 'document.body.innerText.slice(0,400)' - 300
```

One-run Easy Apply, the thing that went in at 37 s (tries jobs in order, submits the first that needs only the resume; the 5/yes answer-sheet version is the next step with `one_pass_form.js`):

```bash
cd scripts && NODE_PATH=/root/mbc-analytics/node_modules CDP_PORT=9336 node easy_apply.cjs "legal operations"
```

Bright Data (account exists, CLI logged in on the box, MCP `bright-data` registered in `~/.claude.json`; keys live on the box, not here):

```bash
bdata budget                                   # balance
bdata scrape --country us "https://www.homedepot.com/s/fiberglass%20rod"   # the fetcher; this one got in
bdata browser open "https://example.com" && bdata browser snapshot --compact  # the rented browser; Home Depot bounces it
```

One-time phone settings (not run yet; reversible):

```bash
bash scripts/anti_freeze.sh
```

## The freeze, measured on the live phone (2026-10-26, another session + this one)

- The phone is **Android 17, One UI 9** (build F766USQUCCZIH), not 16/8 as older notes say.
- Chrome was `isFrozen=true` at adj 900. This phone freezes any process at adj 850 or worse.
- **Per-app hold:** `adb shell am unfreeze --sticky com.android.chrome` (same for `com.chrome.beta`). Dies with the process or a reboot. `chrome.sh` now runs it on every open.
- **Phone-wide:** `anti_freeze.sh` was run; `dumpsys activity | grep use_freezer` now says `false` with no reboot.
- **Unrestricted battery by shell:** `cmd activity set-bg-restriction-level --user 0 com.android.chrome unrestricted` (done 10/26 for Chrome and Beta).
- **Standby bucket** is already 5 (exempted, the best). Never run `set-standby-bucket active`; active is 10, worse.
- **Never sleeping apps** has no shell insert. The screen opens with `am start -a com.samsung.android.sm.ACTION_OPEN_CHECKABLE_LISTACTIVITY -p com.samsung.android.lool --ei activity_type 2`; George taps Chrome, then Add. Not done.
- Silent audio and PiP hold Chrome only while really playing or really on screen. Weak.
- **Check:** `dumpsys activity | grep -A 25 "Apps frozen:"` should show no Chrome pid. 10/26 after all of the above: none.
- **PROVEN 2026-10-26, no reboot:** George in Termux, Chrome in the background, `isFrozen=false`, the socket on 9336 answered `/json/version` and listed 19 tabs. The one false alarm was a wrong socket name: Chrome owned the bare `chrome_devtools_remote`, Beta owned `_<pid>`. Ask `/proc/net/unix` which is which.
- Open catch: OLAF can still pause Chrome about a second on each app switch. No off switch known.

## The hands (2026-10-26)

Captcha scoring watches the hands: pointer movement, press and release, key timing, scroll. Our old scripts
clicked by code (`element.click()`) and filled boxes in one shot (`.value=`). No pointer, no keys. `scripts/human.cjs`
fixes that: `click` walks the pretend pointer along a curved path and presses; `type` sends one key at a time, 55–150 ms
apart, longer at spaces; `scrollTo` wheels; `pause` waits a human beat. It is all inside Chrome over CDP; the real mouse
never moves. Proven 10/26 on GitHub search in the box Chromium: click box, 28 keys, Enter, results in 10.9 s.
Rule: a new script never calls `element.click()` or sets `.value`; it requires `./human.cjs`. Old scripts get moved over as they are touched.

v2, same night, after a second model wrote its own helper and a 13-point list of what still moves the score (its file sits on the
phone at `~/hidden-operator/web/human.cjs`; the ideas are folded into ours): no `Runtime.enable` (an automation mark); bring the tab
to front and refuse a hidden tab; settle 1.5–3.5 s and one idle move before the first action (the page mints its first score token
early); wheel-scroll into view, never a JS scroll; Shift held for capitals; a real finger (touch events) on Android Chrome. Proven
10/26 twice: mouse on the box Chromium (GitHub search, 28 keys, 16 s with the settle) and finger on Chrome Beta on the hidden screen
(22 keys, results page). `HUMAN_SPEED=0` zeroes every pause for a fast run, hands stay real.
Two more from that list we already do: let the tab load pages (never a Node fetch for a page the site scores), leave the window size alone.
Trap seen twice today: the two phone Chromes SWAP socket names when one restarts. `chrome.sh` now picks by app name on every open.
Same night, on LinkedIn: "in view" now also means "nothing sits on top of it". The laptop window is small (845×517) and LinkedIn's
chat layer (`#interop-outlet`, z-index 500) covers the bottom strip; a press there landed on the layer, not the button. `scrollTo`
now checks the element owns the point at its own centre, and wheels it up when it does not.

## Gather (2026-10-26)

`scripts/gather.cjs` is the job gather. It is read-only. It searches LinkedIn with set filters, opens each posting, and copies
title, company, where, pay, the apply button, and the full description. Easy Apply jobs only by default; `--any` lets every
apply kind in. It marks walls from `scripts/walls.json`: a rule hit,
with the exact sentence it matched. It never presses Apply or Easy Apply, never fills a form, never saves, never follows.

How to run it:
1. `bash scripts/laptop_chrome.sh "https://www.linkedin.com/feed/"` (the laptop's Chrome, tunnel on 19222).
2. `CDP_PORT=19222 node scripts/gather.cjs --keywords "legal operations" --max 20 --hours 24 --pages 2` (add `--remote`, `--any`, `--all`, `--location "..."`). About 10 s a posting.
3. Read `logs/gather/gather-<stamp>.json` (every description in full) and the `.md` beside it (the table). The stamp is UTC. `logs/` is not in git.

**Seen list (2026-10-26).** Every posting read goes into `logs/gather/seen.json` (`{ "<jobId>": {first, title, company} }`, local, not in
git). Next run, a job already in it is skipped: not opened, not in the table. `--all` shows seen jobs again. `scripts/no.json`
(`{ "<jobId>": "reason" }`, committed) holds the jobs George or the picker said no to; **the picker writes to it**, and those jobs never
come back, even with `--all`. Each run prints one line: `N skipped (seen), M skipped (no)`. Proven 10/26: run 1 read 5, run 2 printed
"5 skipped (seen), 0 skipped (no)" and read 5 new ones; a run with one id in no.json and `--all` printed "0 skipped (seen), 1 skipped (no)".

**The rule: the script never picks.** The picker (a model) reads `me/george-dossier.md`, `me/writings.md`, `me/assets.md`, and
`me/resume-master.md` in full, then every description in the JSON, and writes overrides for `scripts/map_easy_apply.cjs` (`--overrides`: skip a job, or give it its own answers).
A wall is a rule hit, not a verdict.

How it reads LinkedIn's 2026 job page (no `<h1>`, scrambled class names): title and company from `document.title`
("<title> | <company> | LinkedIn"); the description from the box with id `JobDetails_AboutTheJob_<jobId>`, after a human.cjs click
on its "… more" button; location, age, and Remote / Hybrid / On-site from the top line. When LinkedIn shows no workplace type,
"where" is the city alone. Pay comes from the top line first, then the description; a lone amount counts only next to a pay word.

Proof run 10/26, 9:59 pm (file stamp `2026-10-27-04-59-38`): 20 postings in 3.5 min, 0 empty fields. Wall test the same night
(`--keywords attorney --max 4`): first pass missed "admission to the New York Bar" and "qualification to practice law"; both are in
the bar wall now, and the rerun on the saved pages hit 4 of 4. No "sales or recruiting or support" hits on legal ops postings; that
wall now looks at the title only, and "sales" must be a whole word (so "Salesforce" passes).

| id | title | company | where | pay | apply | walls |
|---|---|---|---|---|---|---|
| 4483601187 | Remote Contract Law Expert | Turing | Remote · United States |  | Easy | bar admission |
| 4483288827 | Legal Document Reviewer - Expert | Mercor | Remote · San Francisco, CA | $60/hour | external |  |
| 4483285727 | Senior Contracts Manager | Juniper Square | Remote · United States | $140,000 - $170,000 | external |  |
| 4483292009 | Fully Remote Employment Law Attorney | Ascendion | Remote · California, United States | $180K/yr - $300K/yr | Easy | bar admission |
| 4459564944 | Food Regulatory Affairs (RA) Specialist | HYH America | On-site · Irvine, CA | $70K/yr - $90K/yr | external |  |
| 4481828337 | Legal Operations Manager | DNOW | On-site · Greater Houston |  | external |  |
| 4483784172 | Senior Business Immigration Associate | Fragomen | Hybrid · Los Angeles, CA | $196,000.00 - $245,000.00 | external |  |
| 4483781385 | Compliance Specialist | MaryRuth's | Remote · Los Angeles, CA | $85,000 to $100,000 | external |  |
| 4480749051 | Legal Externs Spring 2027 - Justice Megan E.  | State of Ohio | Columbus, OH |  | external |  |
| 4480235281 | Corporate Counsel (Litigation) | loanDepot | Remote · United States | $141,000 to $175,000 | external | bar admission |
| 4483721677 | Litigation Docket Specialist | Crowell & Moring | Remote · United States | $70,000 - $110,000 | external |  |
| 4483708712 | Regulatory Correspondence Specialist | Newrez | Fort Washington, PA |  | external |  |
| 4483778203 | Senior Counsel, US Litigation | Mondelēz International | East Hanover, NJ | $142,700 to $235,455 | external | bar admission |
| 4483767207 | Lead Compliance Oversight | Centene Corporation | Remote · Missouri, United States |  | external |  |
| 4474084030 | Contract Management Team Lead | Boeing | On-site · Oklahoma City, OK | $102,850 – $139,150 | external |  |
| 4483714801 | Regulatory & Product Counsel | Harbinger | On-site · Garden Grove, CA | $150,000—$170,000 | Easy | bar admission |
| 4483254992 | Principal, Contracts Management | Tract Capital Management | Remote · United States | $180,000 to $200,000 | external |  |
| 4483266437 | Litigation Legal Secretary (Pasadena) | Adams & Martin Group | On-site · Los Angeles County, CA | $80K/yr - $92K/yr | Easy |  |
| 4483754737 | Administrative Judicial Legal Assistant | California Department of  | On-site · Sonoma, CA | $3,689/month - $5,159/month | external |  |
| 4483749732 | Contract Manager | Pace® Analytical Services | Hybrid · Roseville, MN | $77,025 to $128,400 | external |  |

## Gather by API (10/26)

**Verdict: partial.** Live Voyager GETs return job lists and full details; `walls.json`, seen/no lists, and the seven table columns match the DOM gather.
`CDP_PORT=19222 node scripts/gather_api.cjs --keywords "legal operations" --hours 48 --max 30 --questions`
Measured: **30 jobs in 104.5 s (0.287 jobs/s)**; 33 data/document GETs, 2.50–3.96 s apart. See `docs/linkedin-api-notes.md` for endpoints and proof.
Ban signals: **none**. Easy Apply questions: unavailable without opening Apply; `questions:null` has an explicit reason. Keep a two-minute gap from the DOM gather.

Follow-up 1 (10/27): the one authorized Easy Apply dialog tried a POST navigation action, blocked by the GET-only guard; no form fields or Next appeared, Dismiss closed it, and schema extraction remains unavailable (exact evidence in `docs/linkedin-api-notes.md`).

Follow-up guardrails: every run discovers today's `decorationId`/`queryId` from live `/voyager/api/` requests; any future authorized form replay must be checked on the reloaded job, `/jobs/tracker/` and `/my-items/saved-jobs/`, and any started/in-progress trace rules out pre-reading; the first HTTP 999 stops immediately with a persistent stop flag and no retry.

## The picker file (2026-10-27)

The picker is the model that reads a gather against the dossier, writings, assets, and resume-master and decides. It writes
ONE file per run, `picks/picks-<stamp>.json`: per job `decision` yes/no/ask, `why`, the cover-letter angle, which one-page
resume cut, and per-job form `rules`. The apply walker takes that same file as `--overrides`. Every `no` also lands in
`scripts/no.json`. `ask` lines are the only thing George has to read. Shape and rules: `picks/README.md`.

## Rules learned the hard way

- When George gives the answers for every fork, run the whole thing in one command. No look between presses.
- Count wins as they happen. A `SUBMITTED` line is a win; do not report "zero applied" after it.
- George's eyes beat the log when they disagree.
- Never `pkill -f <pattern>` from a shell whose own command line contains the pattern. It kills itself (exit 144).
- `/json/new` is refused on Android Chrome. Open pages by setting `location.href` on an existing tab, or `am start -a VIEW -d <url>`.
- Whichever Chrome starts first owns the bare `chrome_devtools_remote` socket; the other gets `_<pid>`. Ask `/json/version` which app answered.

## Files

```
README.md                       this
me/george-dossier.md            George on one page: credentials, receipts, YES/NO job lanes, cover-letter voice (2026-10-17)
me/resume-master.md             every sourced bullet about George (121, each tagged with its file), by role + projects + lanes; never sent whole, each application cuts one page from it (2026-10-26)
the-map.md                      what an agent is, in plain words, + the Travolta three-lane test (2026-10-17)
scripts/travolta_dumb.sh        the 6-second dumb script from the Travolta test (one fixed search, first hit)
scripts/chrome.sh               wake phone Chrome + forward DevTools port + list tabs
scripts/laptop_chrome.sh        start the laptop's headed Chrome (scheduled task) + tunnel + show window + list tabs
scripts/cdpx.cjs                the 10/14 Google Ads driver: reads and clicks INSIDE Google's payment box (iframes), real mouse clicks, key-by-key typing
scripts/findclick.sh            find an element by its text, scroll it into view, real-click it (uses cdpx.cjs)
scripts/fill.sh                 fill a field by its label, key by key, and read the value back (uses cdpx.cjs)
scripts/clickread.cjs           one mouse click at x,y, then one read; no typing, no iframes
me/cards/                       eleven one-page cards with WEIGHTS (FULL = live/in pipeline, LESS = GitHub-only/paper): Bakers Agent, mybakingcreations.com, Thursday (the order book), the GLM fine-tune, NoiseFile, WiM+patent, Heirloom, the Santa Rosa CUP, the Baba writing sample, Invisible Work, Audit Ledger; the picker reads these, not the raw (10/27)
me/resume/                      the current resume, the one saved on LinkedIn (George_Abrahamyants_Resume_Sept2026.pdf, last used 10/14/2026) + its text (10/27)
me/raw/                         raw LinkedIn text, dated reads (10/17 and 10/27: profile, experience, education+honors+publications+languages, posts, featured); read once, never per job
me/samples/                     the documents in full: the 33-page CUP application, the 23-page Baba decision (PDF, for writing-sample uploads), the 18-page provisional patent (PDF), Invisible Work (PDF)
me/triggers.json                word triggers that tie a posting to George's assets and receipts (say line, proof, status, resume lane); refresh status with check_assets.py (10/27)
scripts/asset_hits.py           prints, per gathered job, which assets the posting calls for and the words that tripped them; the picker reads it first (10/27)
picks/README.md                 the picker file: one file per gather, yes/no/ask + why + letter angle + resume cut + per-job rules; the walker reads it as --overrides (10/27)
scripts/human.cjs               the hands, made to move like a person's (10/26): pointer path + press/release, key-by-key typing with jitter, wheel scroll, pauses; plain CDP; every new script clicks and types through this
scripts/laptop_show_window.ps1  runs inside the laptop's desktop session (task ShowAgentChrome, /it) and brings the agent Chrome window to the front
scripts/keepalive.js            silent-audio keep-awake, paste into a tab via CDP
scripts/one_pass_form.js        answer-sheet form filler that stops on unknown questions (from the report)
scripts/easy_apply.cjs          the one-run LinkedIn Easy Apply that worked 2026-10-14
scripts/answers.json            George's answer book (rules + facts + never-yes), merged from Agent Bridge + job-vault
scripts/anti_freeze.sh          one-time Android settings (freezer off, phantom killer off, Doze whitelist)
scripts/floorplan.cjs           read-only site crawler: GET only, 2 doors deep, writes pages/links/buttons/inputs as JSON
scripts/gather.cjs              read-only LinkedIn job gather (10/26): Easy Apply only unless --any; skips seen jobs (logs/gather/seen.json) unless --all and no.json jobs always; copy every posting + full description, mark walls, write logs/gather/<stamp>.json + .md; never applies, never picks
scripts/gather_api.cjs          paced GET-only Voyager gather in the signed-in laptop tab, CDP 19222; observed query IDs, normalized graph decoding, 60-call limit, same table/walls plus applicant/pay/company fields; questions explicitly unavailable
docs/linkedin-api-notes.md      observed endpoints, headers, query shapes, failures, request limits, 30-job timing and five-job DOM comparison (10/26)
scripts/no.json                 jobs George or the picker said no to ({ "<jobId>": "reason" }); the picker writes here; gather.cjs never shows them again
scripts/walls.json              George's walls for gather.cjs: name + regex (+ "field": "title" for title-only); a hit = the rule name + the sentence it matched
scripts/stage_ashby.cjs         fill one Ashby application to the "Submit Application" button with human hands, never submit (10/26); log + screenshot in logs/stage/
scripts/stage_greenhouse.cjs    the same for Greenhouse (job-boards.greenhouse.io), stops at "Submit application" (10/26)
scripts/stage_lib.cjs           what the two stagers share: answer book order, type-and-pick boxes, resume upload to the laptop, screenshot, 6-line receipt; refuses any press on a "submit" target
recipes/ashby-apply.md          card: Ashby staging, proven 10/26 on OpenAI (76 s, 13 filled, 2 for George)
recipes/greenhouse-apply.md     card: Greenhouse staging, proven 10/26 on Scale AI (95 s, 15 filled, 2 for George)
floor-plans/github.md           plain-words floor plan of github.com (pages, links, buttons, fastest URLs), drawn 2026-10-26
floor-plans/github-raw.json     the raw crawl behind it: 45 pages with links, buttons, inputs
research/deep-research-prompt.md  the prompt that produced the report
research/gemini-deep-research-2026-10-14.pdf / .txt   report 1 (Gemini)
research/second-deep-research-2026-10-14.pdf / .docx / .txt   report 2 (second model) + its saved sources folder
```

## The eleven buckets (everything we found, sorted)

1. **The instruction (what George says):** every fork answered up front; a stop line; the answer book, real facts apart from test defaults.
2. **The run (how the model acts):** one pass, one command, no look between presses; Submit counts only with a receipt, never twice; a log of every run, read before speaking; three checks when a browser goes quiet (tunnel, browser, page).
3. **The machine (where the browser lives):** laptop headed Chrome (proven); George's phone Chrome (when he watches); hidden screen for app tasks; Yana's phone; rented browser for long jobs; Bright Data's fetcher for pages that block the rest.
4. **The paper (what survives the session):** this repo; one saved recipe per site or app; the run log; this journal.
5. **Getting in (the bouncer and the doors):** headed, never headless; a home address; logged-in profiles kept warm; email codes read from Gmail, text codes read on the phone; captchas by live view or George's thumb (parked); agent passports: watch, do not build; keys on the box, never in the repo; account lockouts for "unusual activity": no recipe yet.
6. **Eyes (how the model reads):** web page = whole page as text in one gulp; app = keyhole, one screen at a time; fetcher and markdown for clean reading; screenshots last.
7. **Speed (where the seconds go):** ~20 s a turn is the model thinking; ~3 s the phone's Linux shell starting a command; ~2 s the page. Fewer turns is the only big lever.
8. **Money:** model tokens per turn; Bright Data $8/GB after the free GB ($10 on the account); the rest free or owned.
9. **George watching:** visible lane when he watches, rented browser when he drives; split screen, Chrome on top; a buzz or spoken "ten done" at batch end (not built).
10. **Recovery (when it breaks):** wake Chrome, re-forward the port, re-run the laptop task; the traps list in "Rules learned the hard way."
11. **Research (where to look next):** the two reports and the prompt; Chinese engineer forums first for phone agents; six-month window for agents, three years for Android.

## Case study from another session (2026-10-14, Google Ads on the phone's hidden Chrome)

A sibling session fixed the Google Ads card, paid $20, and published an app-installs campaign, all through Chrome Beta on the phone's hidden screen. No API. It hit the same three walls: about 50 look-think-press round trips (an hour), Chrome's port died twice and the hidden screen got rebuilt twice, and fresh holes (pasted text ignored, buttons off the right edge of the narrow screen, a "get the app" door on every page). It wrote `scripts/cdpx.cjs` (with `findclick.sh` and `fill.sh`) to read and click inside Google's payment box, click like a finger, and type key by key. The "Confirm it's you" step passed on the second try; best guess is the first passed but Chrome froze before publish landed. Lesson matches this repo: next time run it on the laptop's headed Chrome (no freeze, wide screen, no app door) from a saved recipe, one pass.

## Recipes and journal

- `recipes/`: one card per task that has worked. George says "recipe it," a card gets written. Shape in `recipes/README.md`.
- `journal.md`: one dated entry per session, newest first, written before the session closes.
