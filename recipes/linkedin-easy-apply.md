# LinkedIn Easy Apply (one job)
Machine: George's phone Chrome (proven) · laptop Chrome (proven for search, apply not yet run there)
Last worked: 2026-10-14 02:37 (37 s, "Legal Expert | Remote | $40–$60/hr")
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
Script: scripts/easy_apply.cjs (phone, CDP_PORT=9336); scripts/one_pass_form.js (answer-book filler, untested on LinkedIn)
