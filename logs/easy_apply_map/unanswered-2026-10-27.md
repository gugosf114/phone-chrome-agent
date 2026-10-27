# Questions the book could not answer — 2026-10-27

From the 25-job harvest (`harvest-2026-10-27.jsonl`, "legal operations", nothing submitted). One row per distinct
question (same label = same row). "Jobs" = how many of the 25 asked it.

A question counts as unanswered when the book had no rule, a rule whose answer was not one of the options, or only a
test default (number 5, yes/no "Yes", text "Yes"). LinkedIn pre-filled 142 fields from its own memory; those were run
through the book afterwards, and the ones the book would miss are here too (marked "pre-filled").

**SAFE** = the dossier settles it; the rule is now in `scripts/answers.json` with its source as the third item.
**ASK** = needs George. Not written to the book.

## The list

| # | Question (exact label) | Type · options · required | Jobs | What the book did | Proposed answer | Mark |
|---|---|---|---|---|---|---|
| 1 | Have you completed the following level of education: Bachelor's Degree? | radio · Yes/No · required | 2 | pre-filled Yes by LinkedIn; book said "Doctorate" (not an option, so the test "Yes") | Yes (BA, UC Berkeley, 2015) | SAFE, added |
| 2 | Have you completed the following level of education: Doctor of Law? | radio · Yes/No · required | 1 | pre-filled Yes; book had no rule (test "Yes") | Yes (JD, UC Law SF, 2018) | SAFE, added (same rule as #1; a second rule answers No for PhD, MD, PharmD, MBA) |
| 3 | Degree | select · High School / Associate's / Bachelor's / Master's / M.B.A. / Juris Doctor (J.D.) / M.D. / Ph.D. … · optional | 1 | rule said "Doctorate", not an option → FAILED | Juris Doctor (J.D.) | SAFE, added |
| 4 | School | select · LinkedIn's school list, A to Z · optional | 1 | no rule | University of California, Hastings College of the Law | SAFE, added (match key "Hastings College of the Law"; the saved options stop at "Agnes Scott College", so the exact entry is not seen yet) |
| 5 | Are you fluent in both English and Spanish? | radio · Yes/No · required | 1 | no rule (test "Yes") | No (English, Armenian, Russian) | SAFE, added |
| 6 | This is a equity based position there is no base salary untill we secure funding would you be interested? | radio · Yes/No · required | 1 | salary rule said 150000, not an option (test "Yes") | No (dossier floor about $90k full time) | ASK |
| 7 | The salary for this role starts at $50,000 depending on experience. Does that align with your expectations? | radio · Yes/No · required | 1 | salary rule said 150000, not an option (test "Yes") | No ($50k is under the dossier's $60k line) | ASK |
| 8 | Do you have five to seven years of Civil Litigation Paralegal experience? | radio · Yes/No · required | 1 | legal-years rule said 8, not an option (test "Yes") | No (no paralegal role in the dossier) | ASK |
| 9 | When drafting and redlining agreements, can you change terms, delete, modify and add your own language? | radio · Yes/No · required | 1 | no rule (test "Yes") | Yes? (JD; drafted the 33-page permit and the ALJ decision; redlining agreements is not in the dossier) | ASK |
| 10 | Please specify the contracts you have experience with. | checkbox group · Nondisclosure Agreements, Consultant Agreements, Master Service Agreements, Purchase Orders, Statements of Work, Amendments, Assignments and Terminat… · required | 1 | walker read 7 blank labels, no answer; Review stayed shut (the one stuck job, Agile Legal) | George picks the boxes | ASK |

10 distinct questions: 5 SAFE (6 rules added, one is the No twin of #1/#2), 5 ASK.

One more rule was added for a question the book DID answer, wrongly: "Have you worked for Carta at any other time
previously?" got Yes from the broad "have you … worked" rule. New rule: worked for/at … previously → No (same intent as
the book's existing "previously worked" → No). Source line in the book. The picker must override it for Andersen,
Phenotopia, DOL, IRS, USPS.

## CHECK: the book answered, but the answer is likely false

These matched a broad rule ("do you have experience" → Yes, "are you comfortable" → Yes, "how many years" → 3,
legal years → 8). Not misses by the definition above; a reader or George should look before any Submit.

| Question (exact label) | Jobs | Book said | Likely true answer | Mark |
|---|---|---|---|---|
| Have you worked for Carta at any other time previously? | 1 | Yes | No | SAFE, fixed (above) |
| Do you have experience specifically with legal intake or personal injury law? | 1 | Yes | No? | CHECK |
| Are you comfortable with the Sunday to Thursday 8am-5pm schedule? | 1 | Yes | George's call | CHECK |
| Do you have extensive experience drafting and redlining agreements using track changes in Word? | 1 | Yes | George's call | CHECK |
| How many years of specialized experience do you have in construction contracts? | 1 | 8 (picked "8-9") | 0 (lowest option) | CHECK |
| How many years of work experience do you have with Civil Litigation? | 1 | 3 (LinkedIn had 5 saved) | 0 | CHECK |
| How many years of Hospitals and Health Care experience do you currently have? | 1 | 3 | 0 | CHECK |
| How many years of work experience do you have with Healthcare? | 1 | 3 | 0 | CHECK |
| How many years of Information Technology experience do you currently have? | 1 | 3 (LinkedIn had 1 saved) | George's call | CHECK |
| How many years of work experience do you have with Microsoft Office? / … Microsoft Word? | 1 | 3 (LinkedIn had 10 saved) | about 8 (since Andersen, 2018)? | CHECK |

## Walker gaps seen in the harvest (ideas, not done)

- **Checkbox groups have blank labels.** Agile Legal's seven contract boxes came back as `checkbox:` with no text, so
  the walker cannot answer or even name them. Fix: read the box's own row text and the group's question line.
- **Pre-filled answers are trusted blind.** LinkedIn re-uses answers it saved before. Some may be old test answers
  ("Civil Litigation" years = 5 matches the old "every number is 5" default; inference, not traced). Fix: run the book on pre-filled fields too and
  log where LinkedIn and the book disagree.
- **"Follow <company>" was checked on 16 of the 24 Review pages.** Harmless while nothing is submitted. On a real Submit it
  would follow the company, which George's rules forbid. Fix: uncheck it on Review before any Submit.
