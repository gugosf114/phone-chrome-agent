# Lavrentiy (Лаврентий), the Windows engine · WEIGHT: FULL (shipped installer, 12 releases, in daily use; George to confirm)

**What it is.** A Windows program for voice-to-intent dictation, built for people whose speech has blocks, repetitions,
long pauses, or a strong accent. Hold F9 (or click the dial) and talk; release; the text lands in whatever window the
cursor was in. One Python process, no frameworks, no Electron: `lavrentiy.py` (10,172 lines) is the engine and a small
HTTP server on localhost:7878; `dashboard.html` (6,948 lines) is the control panel, shown in the app's own WebView2
window. The installer is ~508 MB because the English speech model is inside it, so Layer 1 works with no internet and no
account. Repo abrahamyants/lavrentiy, public, 474 commits from Mar 10 to Oct 11 2026, 53 merged PRs, two CI workflows
(tests on push; a tag push builds and publishes the installer). Releases v1.7.0 to v1.7.11 (Jul 17 to Sep 7 2026).

**The four layers, in order.** I. Transcribe: local faster-whisper, multi-temperature voting (0.0/0.2/0.4) with a
disagreement map, pre-roll buffer so the first word is not lost, disfluency filter, repunctuation. II. Reconstruct: the
transcript (never the audio) goes to a reconstruction model with the chosen tone (casual, professional, friend, formal)
and a deterministic meaning guard (SAFE mode keeps names, numbers, dates, amounts, negation). III. Profile: per-user
vocabulary, corrections, style examples, rejection store, decay rules, first-language transfer packs for ten languages.
IV. Stutter: Claude Sonnet with extended thinking, onset-weight learning (which starting sounds this speaker blocks on),
covert-avoidance scoring (the word-swapping that gives WiM its name), Brown's-factors risk scoring, silent-block bridging
(the engine offers a completion when the speaker blocks mid-sentence; the user chooses). Also: delayed auditory feedback,
Patience mode (a 4.5 s endpointer so a block is not read as "done"), auto Quiet Mode calibrated to the speaker's own
level, a 60-prompt calibration where every transcript is confirmed by the user before it counts, a local audio archive,
a clipboard predictor that pre-scores risky words before a phone call or interview, Command Mode (highlight text, F8,
speak an edit), interface in English, Spanish, Russian, Portuguese, French; cloud dictation in 11 languages.

**The dashboard (seen in the repo's baseline screenshots, 1900x914; not yet seen running).** Dark instrument panel.
Left rail: the Лаврентий nameplate, Sign in with Google, EN/RU switch, a round dial that reads IDLE and the take timer,
Tone (Casual / Professional), Layer I to IV with one-line labels, Enhancements (Quiet Mode and more). Top: counters for
words, sessions, WPM, corrections, fillers, vocabulary, triggers, edit distance. Tabs: Console, Sessions, Learning,
Insights (plus Calibrate and Profile per the 10/27 read). While the engine boots, the page shows STARTING ENGINE and a
tic-tac-toe board "against young Garry Kasparov's bot" (rendered on this box 10/29).

**Shared brain with the phone app.** `wim/api/prompt_builder.py` is one file imported by both the desktop engine and the
`wim-reconstruct` Cloud Function, so the Layer 2/3 prompts cannot drift between the two. `docs/LAV_WIM_COMPARISON.md`
is a line-by-line parity table between Lavrentiy and WiM Android (every claim cites file:line; each gap marked
INTENTIONAL or DRIFT). The WiM billing, quota, and user-data backend tests live in this repo too.

**The giveaway build.** `Lavrentiy-Setup-<v>-eval.exe` carries its own provider keys: every layer works on install with
no account and no key, capped at 300 cloud requests per month per installation; after the cap, Layer 1 keeps working
offline. This is the "anyone can download and use it on my keys" design, with the spend cap already built in. The
`-online.exe` variant downloads the model at install time. Installer is unsigned (SmartScreen: More info → Run anyway).

**What it proves.** A 10,000-line real-time audio and LLM pipeline he designed and shipped as a Windows installer through
CI; a product with layers and many parts stitched together (local ASR, cloud models, profiles, calibration, a backend
shared with a phone app, billing tests); the research behind the WiM patent, written down and runnable; built for his own
speech, then for others.

**The sentence.** "I built Lavrentiy, a Windows voice-to-intent app for people who stutter or speak accented English: a
four-layer pipeline from on-device Whisper to a Claude reconstruction layer, shipped as a 500 MB installer through CI
across twelve releases, sharing one prompt module with my Android app's backend."

**Cite when:** desktop apps, Windows, Python, real-time audio, Whisper/ASR, LLM pipelines, prompt engineering, on-device
and offline AI, accessibility and assistive tech, multilingual products, CI/release engineering, "many parts stitched
together," anything that asks for a system rather than a script.

**Still to do before it goes on the portfolio page.** 1) Screenshot or 20-second clip of the dashboard running (laptop:
launch Lavrentiy, open localhost:7878 in Chrome 9222, capture; or George's Drive folder "WIM Android & Lavrentiy
Screenshots," 6/27). 2) George decides whether the public page points at the eval installer (his keys, 300/month cap) or
the standard one. 3) Download counts are single digits per release; leave them off the page.

**Proof.** github.com/abrahamyants/lavrentiy (public) · releases/latest (two installers) · docs/LAV_WIM_COMPARISON.md ·
EVALUATOR_GUIDE.md · me/cards/wim-and-patent.md (the 10/27 read and the patent).
