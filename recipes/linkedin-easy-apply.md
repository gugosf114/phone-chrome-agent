# LinkedIn Easy Apply (one job)

## How the pipeline works
The finder (gather.cjs) brings in the pile of jobs. No letters yet.
The picker (Fable) reads the pile against the dossier and resume-master and writes picks/picks-<stamp>.json: yes/no/ask
   per job, why, letter text, resume cut, per-job rules. For every yes it makes the job's files (below) before the applier runs.
The applier (map_easy_apply.cjs) walks each yes job's form with that job's letter and resume ready. Map only by
   default; --submit per job only on George's word.

## The job's files
- Folder `apply/<jobId>/`: `resume.pdf`, `cover-letter.pdf`, `cover-letter.txt`, `meta.json` {company, title, resume_name, letter_name}
  (the `.html` sources sit beside them so the PDFs can be rebuilt).
- Upload names: `George_Abrahamyants_Resume_<Company>.pdf`, `George_Abrahamyants_Cover_Letter_<Company>.pdf` (Company = letters and spaces only).
- PDF: `node scripts/make_pdf.cjs <in.html> <out.pdf>` (box Chromium, CDP 9222, letter size, 0.6 in margins; prints the page count; a resume must be 1 page).
- To the laptop: `bash scripts/push_apply_files.sh <jobId>` copies both PDFs to `C:\Users\georg\job-applications\<jobId>\` under the upload names and prints the Windows paths.
- A picks entry may carry `resume_file` and `letter_file` (laptop paths); without them the applier uses the `apply/<jobId>/` convention.
- Example set (made by hand 10/27): `apply/4483565124/` (Agile Legal, Senior Contract Management Paralegal - Logistics).

Machine: George's phone Chrome (proven) · laptop Chrome (proven 10/27: 25 walks to Review, nothing submitted)
Last worked: 2026-10-27 3:38–4:03 am PDT, walk only (no Submit): 25 jobs with the new human.cjs hands, 24 reached Review.
  Seconds per job, open the posting → Review: average 27.5, median 27.6 (min 8.6, max 80.1); with Dismiss + Discard: 33.3 / 33.4.
  Versus 37 s (10/14, one job, phone Chrome, Submit pressed) and ~100 s/job (10/17 race, Fable thinking every click).
  Not counted: the walker's 15–45 s pause between jobs. Receipt: logs/easy_apply_map/harvest-2026-10-27.md
Last submitted: 2026-10-14 02:37 (37 s, "Legal Expert | Remote | $40–$60/hr")
Last broke: 2026-10-14 02:11 — pressed Next into a drop-down that still said "Select an option"; fixed by treating placeholder selects as empty
Needs from the answer book: rules + facts in scripts/answers.json (George's own 10/27 rules sit at the top; first hit wins); test defaults (number=5, yes/no=Yes) only when George says so
Steps:
1. Find: `CDP_PORT=19222 node scripts/gather_api.cjs --keywords "<words>" --hours 48 --max 30` (LinkedIn's own data calls from inside the page: full descriptions every time, 3.5 s a job, Easy Apply only, seen jobs and no.json skipped, walls applied). Spare: `scripts/gather.cjs`, the page reader, which went blank once on 10/26. The seen list lives at /root/.local/state/phone-chrome-agent/seen.json, one copy for every clone (10/27).
   Then: `python3 scripts/picks_sync.py picks/picks-<stamp>.json` after the picker writes picks: every no into no.json, the ASK lines printed, the walk command printed.
2. Pick: first `python3 scripts/asset_hits.py logs/gather/<gather>.json` prints, per job, which of George's assets and receipts the posting calls for and the exact words that tripped them (me/triggers.json: noise ordinance -> NoiseFile public on Play; patent -> App. No. 64/100,336; speech/voice -> WiM; SALT -> Andersen; cannabis/permits -> Santa Rosa; LLM/red-team -> the correction corpus; ...). The picker reads those hits plus the four me/ files, then writes `picks/picks-<stamp>.json` and, for every yes, `apply/<jobId>/` (resume.pdf, cover-letter.pdf,
   cover-letter.txt, meta.json; PDFs by `node scripts/make_pdf.cjs`), then `bash scripts/push_apply_files.sh <jobId>`.
3. Walk: `CDP_PORT=19222 node scripts/map_easy_apply.cjs --ids <yes ids> --jobs <n> --overrides picks/picks-<stamp>.json` (map only).
   Per screen the walker:
   - Resume: selects the job's file if LinkedIn's saved list shows it, else presses "Upload resume" and hands Chrome the laptop
     path (file chooser answered in code, no dialog). No job file: the book's resume_file from the saved list.
   - Cover letter: upload button -> the job's PDF; text box -> cover-letter.txt typed key by key. Required or optional, always.
   - Every field from the book / picks; placeholder "Select an option" counts as empty; long lists by type-to-find.
   - Pre-filled values (LinkedIn's memory of old applications) get the same book check; a disagreeing rule overwrites them:
     "overwrote saved: <label> <old> -> <new>". A test default never overwrites.
   - Checkbox groups: the book value ALL ticks every box ("ticked N of M in ...").
   - Review page: unticks "Follow <company>" with a real press, logged every time.
4. Stops one click before Submit, then Dismiss + Discard (never Save, Follow, or Message).
5. Submit: `--submit`, per job, only on George's word; press it once; Submit counts only with the receipt below.
Stop on (status in the log; the walker never skips a field):
- STOPPED_BLOCKED: a captcha, /checkpoint/, a login wall, or HTTP 999. The whole run ends (exit 4); report it, touch nothing.
- NEEDS_LETTER: the form offers a cover letter and there is no letter in picks and no apply/<jobId>/ folder.
- NEEDS_INPUT: a field the book and picks cannot fill, named with its type and options (required or optional); a value that
  will not take; an upload other than resume / cover letter; a resume that cannot be selected or uploaded.
- STUCK_SAME_SCREEN / STUCK_REQUIRED: Next did not move the form; the screen's errors are in the log.
- READY_TO_SUBMIT: the good end of a map-only walk (Review reached).
Receipt: the dialog after Submit says "Application sent" (or the job appears under My items → Applied)
Proof of the five fixes (10/27 re-walk): logs/easy_apply_map/rewalk-2026-10-27.md
Script: scripts/map_easy_apply.cjs (laptop, CDP_PORT=19222; walk + map, --submit only on George's word); scripts/easy_apply.cjs (phone, CDP_PORT=9336); scripts/one_pass_form.js (answer-book filler, untested on LinkedIn)


No guessing (George, 2026-10-27): the test defaults (5 / Yes / Yes) are gone. A question the book cannot answer stops the job as NEEDS_INPUT. Every stop is a line for the book. Stops are many at first, rare after a few weeks.
