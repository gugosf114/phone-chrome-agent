# LinkedIn Easy Apply (one job)
Machine: George's phone Chrome (proven) · laptop Chrome (proven 10/27: 25 walks to Review, nothing submitted)
Last worked: 2026-10-27 3:38–4:03 am PDT, walk only (no Submit): 25 jobs with the new human.cjs hands, 24 reached Review.
  Seconds per job, open the posting → Review: average 27.5, median 27.6 (min 8.6, max 80.1); with Dismiss + Discard: 33.3 / 33.4.
  Versus 37 s (10/14, one job, phone Chrome, Submit pressed) and ~100 s/job (10/17 race, Fable thinking every click).
  Not counted: the walker's 15–45 s pause between jobs. Receipt: logs/easy_apply_map/harvest-2026-10-27.md
Last submitted: 2026-10-14 02:37 (37 s, "Legal Expert | Remote | $40–$60/hr")
Last broke: 2026-10-14 02:11 — pressed Next into a drop-down that still said "Select an option"; fixed by treating placeholder selects as empty
Needs from the answer book: rules + facts in scripts/answers.json; test defaults (number=5, yes/no=Yes) only when George says so
Steps:
1. Open https://www.linkedin.com/jobs/search/?f_AL=true&keywords=<words>&location=United%20States
2. For each job link /jobs/view/<id>: open it, press "Easy Apply"
3. In the box: fill every select/radio/text from the answer book; placeholder "Select an option" counts as empty
4. Press "Next" / "Review" until "Submit application"; press it once
5. Press "Dismiss" / "Discard" if backing out
Stop on: a required question the book cannot answer (return its label and options); a CAPTCHA; a "Submit" with no receipt
Receipt: the dialog after Submit says "Application sent" (or the job appears under My items → Applied)
Script: scripts/map_easy_apply.cjs (laptop, CDP_PORT=19222; walk + map, --submit only on George's word); scripts/easy_apply.cjs (phone, CDP_PORT=9336); scripts/one_pass_form.js (answer-book filler, untested on LinkedIn)
