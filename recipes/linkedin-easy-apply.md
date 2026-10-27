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
