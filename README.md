**Download (2026-10-14):** https://github.com/gugosf114/phone-chrome-agent/archive/refs/heads/main.zip

# phone-chrome-agent

The agent drives George's own phone Chrome. One command, one pass, no second look.

Read this file first. It is the whole story, so no session has to be told "remember when we did this."

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
| 4 | **Answer sheet**: George's standing answers in plain JSON (`scripts/answers.json`). Edit the file, never the code. | started, blanks to fill |
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
scripts/chrome.sh               wake phone Chrome + forward DevTools port + list tabs
scripts/keepalive.js            silent-audio keep-awake, paste into a tab via CDP
scripts/one_pass_form.js        answer-sheet form filler that stops on unknown questions (from the report)
scripts/easy_apply.cjs          the one-run LinkedIn Easy Apply that worked 2026-10-14
scripts/answers.json            George's standing answers
scripts/anti_freeze.sh          one-time Android settings (freezer off, phantom killer off, Doze whitelist)
research/deep-research-prompt.md  the prompt that produced the report
research/gemini-deep-research-2026-10-14.pdf / .txt   report 1 (Gemini)
research/second-deep-research-2026-10-14.pdf / .docx / .txt   report 2 (second model) + its saved sources folder
```
