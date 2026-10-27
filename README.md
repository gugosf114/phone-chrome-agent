**Download (2026-10-17):** https://github.com/gugosf114/phone-chrome-agent/archive/refs/heads/main.zip

# phone-chrome-agent

The agent drives a real, headed Chrome on George's own machines. One command, one pass, no second look.

Read this file first. It is the whole story, so no session has to be told "remember when we did this."

## Start here (state as of 2026-10-17, 9:30 am)

- **Read "The menu" below to pick an option fast** (who does the work, where the browser lives, where the hands live, how the model sees), one good-for / bad-at line each.
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
| **George's phone Chrome** (port 9336) | When George wants to watch on his phone; passes every bouncer (home IP, real phone) | Android freezes it the moment he switches apps; shares his screen; door shuts on app switch |
| **Phone Chrome Beta on the hidden screen** (port 9335) | Play Console, Google Ads, pages that need a signed-in Google without stealing George's screen | Same Android freezing; hidden tabs go stale; `/json/new` refused |
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
| 1 | **Freezer switch**: two Android settings so background Chrome is not frozen (`scripts/anti_freeze.sh`). Use the word `disabled`, not `0`, on Samsung One UI 8. | written, not run; George's call |
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
- Phone: Chrome Beta on the hidden screen (port 9335: Play Console lane, Google Ads) and George's own Chrome (port 9336). Separate machine, separate lane, left alone.

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
the-map.md                      what an agent is, in plain words, + the Travolta three-lane test (2026-10-17)
scripts/travolta_dumb.sh        the 6-second dumb script from the Travolta test (one fixed search, first hit)
scripts/chrome.sh               wake phone Chrome + forward DevTools port + list tabs
scripts/laptop_chrome.sh        start the laptop's headed Chrome (scheduled task) + tunnel + show window + list tabs
scripts/cdpx.cjs                the 10/14 Google Ads driver: reads and clicks INSIDE Google's payment box (iframes), real mouse clicks, key-by-key typing
scripts/findclick.sh            find an element by its text, scroll it into view, real-click it (uses cdpx.cjs)
scripts/fill.sh                 fill a field by its label, key by key, and read the value back (uses cdpx.cjs)
scripts/clickread.cjs           one mouse click at x,y, then one read; no typing, no iframes
scripts/laptop_show_window.ps1  runs inside the laptop's desktop session (task ShowAgentChrome, /it) and brings the agent Chrome window to the front
scripts/keepalive.js            silent-audio keep-awake, paste into a tab via CDP
scripts/one_pass_form.js        answer-sheet form filler that stops on unknown questions (from the report)
scripts/easy_apply.cjs          the one-run LinkedIn Easy Apply that worked 2026-10-14
scripts/answers.json            George's answer book (rules + facts + never-yes), merged from Agent Bridge + job-vault
scripts/anti_freeze.sh          one-time Android settings (freezer off, phantom killer off, Doze whitelist)
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
