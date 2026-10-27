# Greenhouse application (one job, staged to the Submit button)
Machine: laptop Chrome (port 9222, tunnel 19222)
Last worked: 2026-10-26 11:01 pm (95 s, Scale AI "Legal Fellow - Human Frontier Collective (US)": 15 filled, resume attached, 2 left for George)
Last broke: 2026-10-26 10:58 pm — "state of residence" lists codes (AL … CA), the book says "California"; fixed with a state-name-to-code match
Needs from the answer book: facts (first_name, last_name, email, phone, country, location, city, resume_file, juris_doctor) + rules (degree, state, sponsorship via never_yes, "previously worked", gender, veteran)
Steps:
1. `bash scripts/laptop_chrome.sh "https://www.linkedin.com/feed/"` (opens the tunnel)
2. `CDP_PORT=19222 node scripts/stage_greenhouse.cjs https://job-boards.greenhouse.io/<org>/jobs/<id> [--overrides file.json]`
3. The script opens a new tab, reads down the job text, then fills the form under it: text by keys; each drop-down box (react-select) by pressing it, typing to narrow it, pressing the row
4. Resume: copied to the laptop (`C:\Users\georg\job-applications-resumes\`), attached with DOM.setFileInputFiles; Greenhouse then shows the file name in place of the box
5. It wheels "Submit application" into view and stops. It never presses it.
Stop on: a verify-you-are-human page or a visible captcha (CAPTCHA_STOP, exit 4; the page carries an invisible reCAPTCHA that only scores on Submit); no form (NO_FORM); a required question the book cannot answer (listed, never guessed)
Receipt: the 6-line print + logs/stage/greenhouse-<stamp>.json (every field: label, type, value, source rule, form valid yes/no) + the full-page .png; the staged tab stays open on the laptop
Script: scripts/stage_greenhouse.cjs (+ scripts/stage_lib.cjs)
Notes: "Doctorate" in the book picks the JD row ("Juris Doctor (J.D.)", "Professional (MD, JD, etc.)") because facts.juris_doctor is Yes. EEO boxes with no rule get the decline row.
