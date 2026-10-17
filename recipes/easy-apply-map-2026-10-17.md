# Easy Apply map summary

Run file: map-2026-10-17-20-30.jsonl. Nothing was submitted.

## Runs

| run | seconds | status | screens | filled | unanswered | new forks | job title @ company |
|---|---|---|---|---|---|---|---|
| 1 | 34.0 | READY_TO_SUBMIT | 4 | 1 | 0 | 1 | Remote Litigation & Civil Procedure Expert / Turing / LinkedIn @ Turing |
| 2 | 28.9 | READY_TO_SUBMIT | 4 | 0 | 0 | 1 | Legal Expert (Remote / $100–$170/hr) / Synthires / LinkedIn @ Synthires |
| 3 | 34.6 | READY_TO_SUBMIT | 4 | 2 | 0 | 0 | Regulatory Intelligence & Implementation Specialist - Global Security Organizati @ TikTok |
| 4 | 31.0 | READY_TO_SUBMIT | 4 | 1 | 0 | 2 | Coding Compliance Specialist / Vistec Partners / LinkedIn @ Vistec Partners |
| 5 | 37.5 | READY_TO_SUBMIT | 4 | 2 | 0 | 2 | Legal Operations / Healthcare Shares / LinkedIn @ Healthcare Shares |
| 6 | 31.0 | READY_TO_SUBMIT | 4 | 1 | 0 | 2 | Legal Operations Contractor / Legal.io / LinkedIn @ Legal.io |
| 7 | 17.4 | READY_TO_SUBMIT | 1 | 0 | 0 | 5 | Senior Project Lead, Legal / talentpluto / LinkedIn @ talentpluto |
| 8 | 35.4 | STUCK_REQUIRED | 3 | 5 | 1 | 6 | Business Law Subject Matter Expert (SME) / Straive / LinkedIn @ Straive |
| 9 | 32.9 | READY_TO_SUBMIT | 4 | 1 | 0 | 0 | Remote Contract Law Expert / Turing / LinkedIn @ Turing |
| 10 | 18.4 | READY_TO_SUBMIT | 1 | 0 | 0 | 4 | Legal Specialist (Remote / $100–$170/hr) / Synthires / LinkedIn @ Synthires |

## Learning curve

1, 1, 0, 2, 2, 2, 5, 6, 0, 4

New forks were still appearing in the last run (run 10). No saturation point yet.

## Every fork seen

### Apply to The Sentinel Firm, APC
- select|email address
- select|phone country code
- text|mobile phone number

### Contact info
- select|email address
- select|phone country code
- text|mobile phone number
- text|first name
- text|last name

### Resume*
- radio|george_abrahamyants_resume_sept2026.pdf

### Additional Questions
- radio|are you legally authorized to work in the us without restriction?
- radio|will you now or in the future require visa sponsorship or a visa transfer?
- radio|by clicking "yes" you agree to our privacy policy and data processing. providing accurate information is essential, as any dishonesty may lead to rejection of a
- text|how many years of information technology experience do you currently have?
- radio|have you completed the following level of education: bachelor's degree?
- radio|do you have the following license or certification: certified professional coder (cpc)?
- radio|do you have 1-2 hours per month available to participate on our venture capital advisory board?
- radio|a benefit we offer is the opportunity for our advisory board members to make an angel investment in the company of $25k+ (an ira/401k can be used). would you co
- radio|do you have the following license or certification: professional paralegal?
- text|how many years of work experience do you have with jira?
- radio|do you have formal academic or professional experience in business law (e.g., as a lecturer, professor, legal academic, or practicing legal professional)?
- radio|have you previously developed or reviewed higher education academic supplements, such as test banks, instructor manuals, or solution guides?
- radio|do you hold a master’s degree, juris doctor (jd), ll.m., or ph.d. in law, business law, or a closely related field?
- radio|we must fill this position urgently. can you start immediately?
- radio|would you be available to commit at least 20-35 hours per week within standard business hours starting immediately?
- text|what is your expected hourly rate in usd? (please note, this is for informational purposes only, and we cannot make any 

### Apply to talentpluto
- select|phone country code
- select|email address
- text|first name
- text|last name
- text|mobile phone number

### Apply to Synthires
- select|email
- select|phone country code
- radio|george_abrahamyants_resume_sept2026.pdf
- text|phone

## Stuck points

- Run 8: STUCK_REQUIRED. [{"heading":"Additional Questions","fields":["radio:Do you hold a Master’s degree, Juris Doctor (JD), LL.M., or Ph.D. in Law, Business Law, or a closely related field? [Yes/No]"]}]

## Unanswered questions

- Run 8: "Do you hold a Master’s degree, Juris Doctor (JD), LL.M., or Ph.D. in Law, Business Law, or a closely related field?" | type radio | options ["Yes","No"] | source FAILED:rule:highest (level of )?education|

## Timing

- Fastest: run 7, 17.4 s
- Slowest: run 5, 37.5 s
- Average: 30.1 s
- Total wall time: 10.1 min (from the done: line)

## Verdict

The map is not saturating. Runs 7, 8 and 10 still found 5, 6 and 4 new forks, and 34 forks are known after 10 runs. The script cannot yet answer the "Master's, JD, LL.M. or Ph.D. in Law" question (its education rule failed), so run 8 stopped. Runs 7 and 10 had only 1 screen, so those forms were not walked in full.
