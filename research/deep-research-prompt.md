# The deep-research prompt (sent to Gemini Deep Research, 2026-10-14)

Paste the block below into any deep-research model. It produced `gemini-deep-research-2026-10-14.pdf`.

```
Deep research task. Produce a practical engineering report, not a survey.

CONTEXT
One person runs an AI coding agent (Claude Code) inside a Linux box on his own Android phone (Samsung, Android 16, Termux + Debian proot). The agent drives the phone's own Chrome browser through the Chrome DevTools Protocol (adb forward to the chrome_devtools_remote socket) and, when needed, Android apps through the accessibility tree. The phone's own Chrome passes every site's bot defenses (Akamai, Cloudflare) where rented cloud browsers (Bright Data Browser API, datacenter and residential) and Linux headless Chromium get blocked. Everything works. It is slow and brittle for three reasons, measured on 2026-10-14:
1. Round trips: the agent reads the page, thinks, writes one command, runs it, reads again. 20-30 seconds per step. An 8-step form costs 4 minutes.
2. The browser falls asleep: when the user switches from Chrome to another app, Android freezes Chrome's renderer and the DevTools socket stops answering ("fetch failed", Page.enable never returns). Same on a hidden virtual display. Each wake costs a turn.
3. Fresh scripts have fresh holes: a one-shot form filler missed drop-downs that start on "Select an option", skipped a question it could not answer, etc.
A one-shot run with a complete answer sheet ("any number = 5, any yes/no = yes") submitted a LinkedIn Easy Apply in 37 seconds. That is the target shape for everything.

MAIN QUESTION
What is the current best practice (last 6 months) for running an agent on a phone's OWN browser and apps, on-device or via adb, so that a multi-step web or app task (log in, fill a form, submit, read the result) runs in ONE pass from a saved answer sheet, without the agent re-reading the screen between steps, and without the browser's debug socket dying when the app is backgrounded?

SIDE QUESTIONS
A. Android specifics (go back up to 3 years, this part changes slowly): how to keep Chrome's DevTools socket responsive while Chrome is in the background or on a secondary/virtual display (foreground service tricks, keep-screen-on, split-screen, wake locks, "don't kill" settings, Samsung-specific battery/process settings, adb commands). What actually works on Android 14-16 and One UI 7-8.
B. One-pass form filling: proven patterns for filling multi-page forms (LinkedIn Easy Apply, Workday, Greenhouse, Ashby, Lever) from a stored answer sheet, including how to detect unanswered required fields (selects on placeholder values, custom radio groups, typeahead inputs), when to stop, and how to report. Open-source code preferred.
C. Phone-agent frameworks: Open-AutoGLM (Zhipu), Mobile-Agent v3/E (Alibaba), UI-TARS (ByteDance), AppAgent, DroidRun, Mobile-Use. For each: does it run on the user's own phone, how it keeps apps awake, speed per step, whether it can drive Chrome via DevTools rather than screenshots, license, last release date.
D. Why a real phone browser passes bot defenses that cloud browsers fail, from the bouncers' side (Akamai, Cloudflare, DataDome write-ups) and from scraper engineers. What signals matter in 2026: IP type, TLS fingerprint, automation flags, behavior.
E. The agent-passport trend: Web Bot Auth / signed agents, Cloudflare "Markdown for Agents", which sites honor them today.

SOURCES, IN THIS ORDER OF PRIORITY
1. Chinese-language engineering sources: Zhihu (知乎), Juejin (掘金), WeChat public accounts (微信公众号) of Zhipu/智谱, Alibaba/通义, ByteDance, Tencent; ChinaXiv; CNKI journals (计算机学报, 软件学报, 自动化学报). Search in Chinese: 手机智能体, 端侧 Agent, Android 自动化, Chrome DevTools 远程调试 后台 冻结, 无障碍服务 自动化, 一次性表单填写, AutoGLM, Mobile-Agent, UI-TARS.
2. Japanese and Korean engineering blogs (Qiita, Zenn, velog, Naver D2) on Android automation and DevTools.
3. GitHub repos and issues (microsoft/playwright-mcp, puppeteer Android, Chromium bug tracker on Android remote debugging and background renderer freezing, Open-AutoGLM, Mobile-Agent, UI-TARS, droidrun).
4. arXiv, last 6 months: phone/GUI agents, web agents, bot-detection measurement (e.g., FP-Agent 2605.01247).
5. Vendor write-ups from the bouncer side (Akamai, Cloudflare, DataDome) and scraper side (curl_cffi, Camoufox, Scrapling, Bright Data docs).
6. Reddit (r/webscraping, r/androiddev, r/termux), Hacker News.
Reputable English coverage is fine but do not stop there; the point is the non-English engineering sources.

OUTPUT FORMAT
- Lead with a one-page "do this" list: concrete commands, settings, and code patterns, ranked by expected impact on the three problems above.
- Then one section per side question, each ending with a verdict and confidence.
- Every claim gets a link. Mark anything that is a vendor claim or a single-source claim.
- Quote original-language sources with a one-line English translation.
- Flag anything that is older than 6 months (or 3 years for the Android part) and say whether it still applies.
- End with the 5 things you could not find, so the next search knows where to dig.
```
