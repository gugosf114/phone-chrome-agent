# Ashby application (one job, staged to the Submit button)
Machine: laptop Chrome (port 9222, tunnel 19222)
Last worked: 2026-10-26 10:56 pm (76 s, OpenAI "Compliance Program Manager — Regulatory Compliance": 13 filled, resume attached, 2 left for George)
Last broke: never
Needs from the answer book: facts (full_legal_name, email, phone, location, city, resume_file) + rules (preferred name, start date, authorized to work, sponsorship via never_yes, "able to work", gender, race, veteran)
Steps:
1. `bash scripts/laptop_chrome.sh "https://www.linkedin.com/feed/"` (opens the tunnel)
2. `CDP_PORT=19222 node scripts/stage_ashby.cjs https://jobs.ashbyhq.com/<org>/<posting-id> [--overrides file.json]`
3. The script opens a new tab, presses the "Application" tab, skims, then fills box by box: text by keys, "Yes"/"No" buttons, location by typing the city and pressing the row, radios by their label, the date picker with today for "Immediately"
4. Resume: copied to the laptop (`C:\Users\georg\job-applications-resumes\`), attached with DOM.setFileInputFiles
5. It wheels "Submit Application" into view and stops. It never presses it.
Stop on: a verify-you-are-human page or a visible captcha (CAPTCHA_STOP, exit 4); no form (NO_FORM); a required question the book cannot answer (listed, never guessed)
Receipt: the 6-line print + logs/stage/ashby-<stamp>.json (every field: label, type, value, source rule) + the full-page .png; the staged tab stays open on the laptop
Script: scripts/stage_ashby.cjs (+ scripts/stage_lib.cjs)
Notes: Ashby saves each answer to its server as a draft while you fill; that is not a submission. OpenAI caps applications at 5 per 180 days. The arbitration and "I certify" boxes have no rule in the book on purpose: George ticks them or a picker writes an override.
