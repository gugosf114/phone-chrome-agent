# George Abrahamyants — master resume (every sourced bullet, never sent as is)

Each application takes a one-page cut from this file. Nothing here is sent whole. Every bullet ends with the file it came
from; a claim with no source is not written. Built 2026-10-26 from a full read of: in this repo me/george-dossier.md,
me/writings.md, me/assets.md, me/linkedin-profile-2026-10-17.txt, me/linkedin-experience-2026-10-17.txt,
me/linkedin-posts-2026-10-17.txt; in gugosf114/job-vault vault/resumes/current/resume.txt, vault/george-facts.json, and every
file under vault/archive/documents/resume-rebuild-2026-08-04/ (10 resume PDFs, 3 cover-letter PDFs, 10 Word letters, 9 Python
builders, 1 .pyc, 5 .txt, 1 evidence .md, 19 page pictures; the pictures and .txt copies hold no words the PDFs lack).

House rules carried from the sources: George is a JD who never took the bar; never call him a lawyer licensed to practice.
On screeners say "highly regulated California businesses" and do not name the crop (george-facts.json form_rules). The
2026-08 resume checker also bans "software engineer", "enterprise-grade", "autonomous", and "cut review time"
(verify_resumes.py). Bullet IDs ([S1], [A1] ...) are used by the Lanes block at the end.

## Contact

- George Abrahamyants (legal name Gurgen Abrahamyants, for legal or official forms only) <!-- src: george-facts.json -->
- Daly City, CA 94015 · 415-632-8008 · gugosf@berkeley.edu <!-- src: resume.txt -->
- linkedin.com/in/george-abrahamyan · github.com/gugosf114 · github.com/abrahamyants <!-- src: george-dossier.md -->
- LinkedIn headline: AI Evaluations & Operations | JD, UC Hastings | LLM Reliability | AI Governance; open to work in the San Francisco Bay Area, on-site, hybrid, or remote <!-- src: linkedin-profile-2026-10-17.txt -->
- Approved one-line bio: JD with a tax concentration; SALT work at Andersen; DOL ALJ clerk whose decision was affirmed on appeal; licensing and compliance for highly regulated California businesses; self-employed legal consultant building AI tools; daily LLM user who shipped Android apps, AI phone agents, and chatbots; sole inventor on a pending speech patent; runs bakery e-commerce and marketing <!-- src: george-facts.json -->

## Experience

### AI Developer & Independent Researcher — Self-Employed — June 2025 to present (San Francisco, hybrid)
Titles used for this role in past applications: AI Evaluation Researcher & Product Builder; Applied AI Researcher & Legal
Systems Builder; Legal AI Workflow Builder & Independent Researcher; Legal Consultant; Founder and Product Owner.

Bakers Agent
- [S1] Built and operate Bakers Agent, a Google Cloud system (22 Cloud Functions, React/TypeScript dashboard) that runs a live business's marketing behind human approval gates: photos become approved posts on Google Business Profile, Facebook, and Pinterest; Search Console findings become GitHub pull requests with a quality gate and feedback loop; photo batches become priced Google menus; review replies are drafted for approval; one dashboard tracks traffic, search, reviews, AI-search visibility, social reach, and payments <!-- src: resume.txt -->
- [S2] Bakers Agent manages content, traditional and AI-search optimization, analytics, brand monitoring, and reviews behind approval controls <!-- src: linkedin-experience-2026-10-17.txt -->
- [S3] Built Bakers Agent 2, the commercial multi-client version, with isolated deployments, automated onboarding and site audits, private dashboards, approval-controlled website fixes, scheduled drafts, and guided pilots <!-- src: linkedin-experience-2026-10-17.txt -->
- [S4] Firebase/GCP platform: React/TypeScript dashboards and Python services route content through human approval and convert Search Console opportunities into proposed website changes through GitHub pull requests; status and evidence tracking, brand and review workflows <!-- src: George_Abrahamyants_Resume_AI_Governance.pdf, George_Abrahamyants_Resume_Compliance_Legal_Operations.pdf -->
- [S5] Governance by design: customer-facing and budget paths use human approval; one verified run turned a Search Console finding into a GitHub pull request and then a live page <!-- src: George_Abrahamyants_Resume_Amgen_Responsible_AI_Manager.pdf -->
- [S6] Claude-generated content with human approval gates, posting across five platforms (Google, Facebook, Instagram, Pinterest, YouTube); the SEO agent opens pull requests on the site by itself for owner approval <!-- src: linkedin-profile-2026-10-17.txt, assets.md -->
- [S7] Bakers Agent is also the shared backend for WiM and Lavrentiy <!-- src: resume.txt -->
- [S8] In production at bakers-agent.web.app; repo gugosf114/bakers-agent, 443 commits (checked 2026-10-17) <!-- src: assets.md -->

WiM and Lavrentiy (voice-to-intent)
- [S9] Built WiM for Android and Lavrentiy for Windows, voice-to-intent apps: the user speaks, and clean text lands in the app in use <!-- src: resume.txt -->
- [S10] Dedicated speech-disfluency support for repetitions, false starts, prolongations, long pauses, blocks, circumlocution, and word substitution; uses personal speech patterns to reconstruct intended meaning, clarify uncertain language, and place text into other applications <!-- src: linkedin-experience-2026-10-17.txt -->
- [S11] The disfluency layer lets the user end the recording, detects blocks and covert word substitutions, and asks at most three clarifying questions <!-- src: resume.txt -->
- [S12] Designed register-specific response rules and content-based tone selection; after an app-based heuristic misread context, replaced it with message-level classification and a bounded clarification question for genuine ambiguity <!-- src: George_Abrahamyants_Resume_OpenAI_Model_Designer.pdf -->
- [S13] Designed a learning loop that treats regeneration as rejection and accepted outputs as style examples, adapting rhythm, contractions, and tone to the user's demonstrated voice <!-- src: George_Abrahamyants_Resume_OpenAI_Model_Designer.pdf -->
- [S14] Added guards that reject a rewrite when names, figures, dates, or negations are lost or invented, and fall back to the original words; flags uncertain words for review. Design rule: change the delivery without changing what the person meant <!-- src: George_Abrahamyants_Resume_OpenAI_Model_Designer.pdf, George_Abrahamyants_Cover_Letter_OpenAI_Model_Designer.pdf -->
- [S15] WiM uses speech recognition, context-based reconstruction, user-controlled insertion, and an accessibility overlay; used daily for cross-application speech input; CI passes <!-- src: George_Abrahamyants_Resume_Amgen_Responsible_AI_Manager.pdf, George_Abrahamyants_Resume_OpenAI_Program_Manager_Alignment.pdf -->
- [S16] WiM: Google Play alpha, release 658 (1.0.0), production track empty (Play API 2026-10-17); repo abrahamyants/wim-android, 659 commits <!-- src: assets.md -->
- [S17] Lavrentiy v1.7.11 (released 2026-09-06) installs on Windows as one ~508 MB installer and works offline; repo abrahamyants/lavrentiy, 474 commits <!-- src: assets.md, resume.txt -->
- [S18] Sole inventor on the related 35-claim U.S. provisional patent application covering persistent cross-application controls, disfluency-aware reconstruction, bidirectional clarification, context preservation, failed-write recovery, and user-controlled insertion (App. No. 64/100,336; filed June 27, 2026) <!-- src: linkedin-experience-2026-10-17.txt -->

Model evaluation and research
- [S19] Built Drift Auditor, a multi-turn diagnostic for dropped instructions, correction persistence, and operator burden; analyzed 512 Claude and ChatGPT conversations containing 37,536 messages and documented 101 model failures involving source use, authorization, context recovery, and proof of completion (see the check-before-use note on these numbers) <!-- src: linkedin-experience-2026-10-17.txt -->
- [S20] Drift Auditor is a two-stage system: it processed the 512-conversation corpus with zero errors using local candidate detection plus an optional LLM judge; documented repeatable review rules; CI passes on Python 3.10-3.13 <!-- src: George_Abrahamyants_Resume_Legora_Legal_Engineer_Tax_Consulting.pdf -->
- [S21] Drift Auditor detects dropped instructions, correction decay, semantic dilution, false context, and unsupported completion claims; designed two-stage review, per-instruction lifecycle tracking, operator-side measures, and adversarial multi-turn tests <!-- src: George_Abrahamyants_Resume_OpenAI_Model_Designer.pdf -->
- [S22] Drift Auditor's 10-tag taxonomy: sycophancy, reality distortion, confidence inflation, instruction drop, semantic dilution, correction decay, conflict pair, shadow pattern, operator move, void; measures how hard the human worked <!-- src: writings.md -->
- [S23] Built AI Operator Field Notes, a source-linked 101-entry corpus of model-authored failures from dated logs across six repositories, organized into five control categories with a cross-referenced evidence file; dated notes turn recurring failures into prevention rules <!-- src: George_Abrahamyants_Resume_Kirkland_AI_Innovation_Advisor.pdf, George_Abrahamyants_Resume_OpenAI_Model_Designer.pdf -->
- [S24] The work separated model mistakes from process and control failures, kept every claim tied to evidence, and defined where human review, scoped permission, logs, and stop gates belong <!-- src: George_Abrahamyants_Cover_Letter_Amgen_Responsible_AI_Manager.pdf -->
- [S25] Wrote Invisible Work: Measuring the Human Cost of AI Alignment (Feb 2026, 6 pages), a reply to Anthropic's Jan 28 2026 disempowerment paper; defines the Operator Load Index, Alignment Tax, Instruction Survival Rate, and Self-Sufficiency Score; finding: equal drift scores, different failure styles (Claude fails loudly, ChatGPT quietly); live Streamlit demo <!-- src: writings.md -->
- [S26] Invisible Work states the question, method, results, and limits, and was sent to an Anthropic researcher <!-- src: George_Abrahamyants_Resume_Anthropic_Research_Operations.pdf -->
- [S27] Built conversation-corpus, 449 adjudicated correction cases (private) <!-- src: writings.md, george-dossier.md -->
- [S28] Wrote 12 Rules for AI: An Operator's Field Manual (Dec 2025, 29 pages, 17 academic citations), protocols for people using LLMs in legal, finance, audit, and compliance work <!-- src: writings.md, linkedin-posts-2026-10-17.txt -->
- [S29] Wrote NotebookLM as a Deterministic Compiler (Dec 2025, 4 pages): a three-layer lock (Cognitive Mode, Hierarchical Truth, Format Lock) used to extract 400k+ characters from 35 operator logs with zero drift; the first post on it reached 1,825 impressions <!-- src: writings.md, linkedin-profile-2026-10-17.txt -->
- [S30] Wrote AEGIS: A 10-Layer Prompt Architecture (Dec 2025, 9 pages, MIT license), which constrains an LLM into an auditable forensic analyst, plus Newton Sentinel, a Python runtime that turns the model's signals into machine-verifiable escalation objects <!-- src: writings.md -->
- [S31] Wrote Air-Gapped Compilation (Jan 2026, 9 pages): the Iron Pipeline of Generator, Auditor (cannot see the generator's reasoning), and Regenerator; tested on GPT-4, Gemini, and Claude; thesis: enforcement must live outside the model <!-- src: writings.md, linkedin-posts-2026-10-17.txt -->
- [S32] Documented that Claude's sandbox writes full transcripts to /mnt/transcripts on each compaction and the model can read them back (13 files, ~4.5 MB across two conversations); post reached 442 impressions <!-- src: linkedin-posts-2026-10-17.txt -->
- [S33] Built reply-shape (public): deterministic reply-shape enforcement around an LLM, built as an accessibility accommodation <!-- src: writings.md -->

Legal, compliance, and agent tools
- [S34] Built Audit Ledger, a tamper-evident evidence and AI-governance system using SHA-256 hash chains, pre-commit confidence declarations, compliance mapping, gap detection, and adversarial claim verification <!-- src: linkedin-experience-2026-10-17.txt -->
- [S35] Audit Ledger is a California residency audit-defense system: the 19 Bragg factors, a SHA-256 hash chain that detects chain breaks and changed record data, and contradiction checks; live dashboard, 97 commits <!-- src: resume.txt, George_Abrahamyants_Resume_Amgen_Responsible_AI_Manager.pdf, assets.md -->
- [S36] Built NoiseFile, an Android noise-complaint kit that checks a noise complaint against the city's own ordinance and files it the way that city wants; public on Google Play as "Neighbor Noise Complaint Kit" (production 0.30.8, $7.99 unlock); catalog of 36 cities and 108 rule workflows; legal-corpus manifest of 67 entries across 15 cities; 202 commits <!-- src: assets.md, george-dossier.md -->
- [S37] NoiseFile keeps source links and evidence limits visible; stored source hashes matched; CI passed 58 unit tests, Android lint, builds, and signed-bundle verification <!-- src: George_Abrahamyants_Resume_Harvey_Applied_Legal_Researcher.pdf -->
- [S38] Built Agent Bridge, an agent that operates the owner's own phone and laptop: it reads notifications, drives apps on hidden screens, reads SMS sign-in codes, and pauses for approval before any irreversible step; a companion web agent booked and cancelled a live restaurant reservation end to end <!-- src: resume.txt -->
- [S39] Agent Bridge / phone-chrome-agent: one LinkedIn Easy Apply submitted in 37 s; 30+ mapped walks <!-- src: george-dossier.md -->

Sites and client work
- [S40] Built and operate mybakingcreations.com, the first thing he ever built: PayPal checkout, chatbot, 117 HTML files in the repo, 1,414 commits; last 30 days to 2026-10-17: 2,192 sessions, 1,684 users, 757 Search Console clicks, 32,879 impressions <!-- src: assets.md, resume.txt -->
- [S41] About 2,000 monthly visitors on zero ad spend from SEO; client work includes Fortune 500 logo cookies and Ice Cube's 55th birthday cake <!-- src: linkedin-profile-2026-10-17.txt -->
- [S42] GA4, July 21 to August 17 2026: the AI Assistant channel brought 64 sessions and 328 key events, with chatgpt.com named as a source; kept the public order surface separate from the private Bakers Agent owner console <!-- src: george-facts.json -->
- [S43] Delivered a paid website and field-operations app for a private-jet detailing company (Stratos), with photo inspections, damage markup, manager-only quality sign-off, and shareable customer reports; live at stratosjetdetail.com and /ops/ <!-- src: resume.txt, assets.md -->

### Andersen — Senior Associate, State & Local Tax — November 2023 to April 2025 (San Francisco, hybrid)
- [A1] Managed multistate tax compliance and controversy for corporate and startup clients, including audit defense, refund claims, voluntary disclosures, and nexus reviews, with structured recommendations across conflicting legal rules <!-- src: linkedin-experience-2026-10-17.txt, George_Abrahamyants_Resume_OpenAI_Model_Designer.pdf -->
- [A2] Led engagements where the state tax consequences of major technology transactions were in dispute; negotiated audit resolutions that reduced client liabilities <!-- src: linkedin-experience-2026-10-17.txt -->
- [A3] Translated the disputed tax treatment of major technology transactions into clear client and audit positions <!-- src: George_Abrahamyants_Resume_Harvey_Applied_Legal_Researcher.pdf -->
- [A4] Drafted legal memoranda and structured recommendations on filing positions across income/franchise and sales & use tax <!-- src: linkedin-experience-2026-10-17.txt -->
- [A5] Used LLM tools to analyze public clients' SEC filings, surfacing active sales & use tax audits, pending litigation, and credits & incentives positions, to prepare client intake and identify additional service opportunities; used LLM tools for first-pass analysis and checked conclusions against the underlying record <!-- src: linkedin-experience-2026-10-17.txt, George_Abrahamyants_Resume_Anthropic_Research_Operations.pdf -->
- [A6] Translated statutes, agency rules, audit evidence, and legal risk into clear recommendations, work plans, and defensible records <!-- src: George_Abrahamyants_Resume_Amgen_Responsible_AI_Manager.pdf -->
- [A7] Synthesized statutes, administrative records, public-company SEC filings, and client evidence into legal memoranda and structured recommendations <!-- src: George_Abrahamyants_Resume_Anthropic_Research_Operations.pdf -->
- [A8] Coordinated parallel audit defense, refund, voluntary-disclosure, and nexus matters across clients and jurisdictions, tracking source records, deadlines, and stakeholder decisions; worked across legal, finance, operations, and government stakeholders without owning their underlying systems <!-- src: George_Abrahamyants_Resume_Amgen_Responsible_AI_Manager.pdf, George_Abrahamyants_Resume_OpenAI_Program_Manager_Alignment.pdf -->
- [A9] Translated complex tax and regulatory issues into clear, actionable guidance for cross-functional teams <!-- src: linkedin-experience-2026-10-17.txt -->
- [A10] More than four years at Andersen <!-- src: George_Abrahamyants_Resume_Legora_Legal_Engineer_Tax_Consulting.pdf, George_Abrahamyants_Cover_Letter_Kirkland_AI_Innovation_Advisor.pdf -->

### Phenotopia — Chief Operations Officer — February 2021 to May 2023 (Santa Rosa, on-site)
- [P1] Directed a $1.75 million retail construction buildout through building permits, construction, final municipal inspections, and opening; managed contractors, engineers, consultants, municipal departments, vendor contracts, MSAs, NDAs, purchasing, SOPs, and compliance while requirements and operating conditions changed. The business remains open <!-- src: linkedin-experience-2026-10-17.txt, George_Abrahamyants_Resume_OpenAI_Model_Designer.pdf -->
- [P2] Separately authored the 33-page conditional-use-permit application to the City of Santa Rosa for a 9,990 sq. ft. cultivation, distribution, and non-volatile manufacturing facility; assembled its 11 exhibits from five outside firms (civil engineering, traffic, HVAC odor control, security, water treatment), about $300,000 of work, through 16 months of drafts and city review; the project won unanimous local approval and state licensing <!-- src: resume.txt -->
- [P3] The permit package integrated land-use requirements, operating procedures, security, traffic, odor control, water treatment, fire and building compliance, and work from outside engineering and environmental consultants; outside work spanned civil, mechanical, traffic, odor, HVAC, noise, security, water, fire, building, and operating plans <!-- src: linkedin-experience-2026-10-17.txt, George_Abrahamyants_Resume_Harvey_Legal_Engineering_Program_Manager.pdf -->
- [P4] Built audit systems and compliance frameworks across construction, licensing, and business operations <!-- src: linkedin-experience-2026-10-17.txt -->
- [P5] Coordinated legal, finance, operations, vendors, consultants, and government staff, turning operating risk into clear plans and defensible records <!-- src: George_Abrahamyants_Cover_Letter_Amgen_Responsible_AI_Manager.pdf -->

### Andersen — Associate, State & Local Tax — August 2018 to January 2021 (San Francisco Bay Area, on-site)
- [B1] Conducted nexus studies, multistate compliance reviews, and exposure analyses across 20+ jurisdictions <!-- src: linkedin-experience-2026-10-17.txt -->
- [B2] Supported audits, voluntary disclosures, refund claims, and tax controversy matters <!-- src: linkedin-experience-2026-10-17.txt -->
- [B3] Prepared legal memoranda and structured recommendations for client tax positions <!-- src: linkedin-experience-2026-10-17.txt -->
- [B4] Researched federal, state, and local codes to ensure accurate regulatory interpretation <!-- src: linkedin-experience-2026-10-17.txt -->

### Andersen — State & Local Tax Intern — February 2018 to August 2018
- [B5] Supported senior associates in delivering multistate tax planning and compliance services <!-- src: linkedin-experience-2026-10-17.txt -->
- [B6] Researched federal, state, and local tax codes to ensure regulatory alignment <!-- src: linkedin-experience-2026-10-17.txt -->
- [B7] Prepared legal memoranda and nexus studies to clarify client tax obligations <!-- src: linkedin-experience-2026-10-17.txt -->

### Internal Revenue Service, Office of Chief Counsel — Legal Extern — August 2017 to November 2017
- [E1] Drafted pleadings, motions, and legal memoranda for tax litigation <!-- src: linkedin-experience-2026-10-17.txt -->
- [E2] Researched complex tax issues to support case strategies <!-- src: linkedin-experience-2026-10-17.txt -->
- [E3] Reviewed extensive documentation, including tax returns and financial records, for evidentiary value <!-- src: linkedin-experience-2026-10-17.txt -->

### United States Postal Service, Pacific Area Law Office — Legal Extern — May 2017 to August 2017
- [E4] Drafted motions and settlement agreements for EEOC and MSPB cases <!-- src: linkedin-experience-2026-10-17.txt -->
- [E5] Researched employment law issues to support litigation strategy <!-- src: linkedin-experience-2026-10-17.txt -->
- [E6] Attended proceedings and analyzed briefs and testimony <!-- src: linkedin-experience-2026-10-17.txt -->

### U.S. Department of Labor, OALJ — Judicial Extern to ALJ Richard M. Clark — January 2017 to April 2017
- [E7] Drafted the 23-page Decision and Order Denying Compensation and Benefits in a Defense Base Act psychological-injury claim under the judge's direct supervision, weighing conflicting expert opinions and symptom-validity testing <!-- src: resume.txt, linkedin-experience-2026-10-17.txt -->
- [E8] Affirmed by the Benefits Review Board on appeal: Baba v. SOS International, LLC, BRB No. 17-0440 (Jan. 30, 2018); underlying matter No. 2015-LDA-00761; writing sample on LinkedIn <!-- src: linkedin-experience-2026-10-17.txt -->
- [E9] Analyzed briefs and testimony; conducted in-depth legal research and wrote memoranda <!-- src: linkedin-experience-2026-10-17.txt -->

### City and County of San Francisco, Office of the Assessor-Recorder — Policy Intern — August 2016 to November 2016
- [E10] Researched property tax regulations and public finance policies <!-- src: linkedin-experience-2026-10-17.txt -->
- [E11] Created outreach materials on tax relief programs for veterans and people with disabilities; translated communications into Russian and Armenian <!-- src: linkedin-experience-2026-10-17.txt -->

### AIDS Legal Referral Panel — Law Clerk — May 2016 to August 2016
- [E12] Conducted client intake and drafted legal memoranda in housing and consumer law, and on bankruptcy and debt-related issues <!-- src: linkedin-experience-2026-10-17.txt -->
- [E13] Represented clients in grievance meetings to resolve disputes <!-- src: linkedin-experience-2026-10-17.txt -->

## Projects (one entry per repo on the shelf, with its proof)

- WiM (What I Meant): Android voice-to-text that cleans messy, stuttered, or accented speech and pastes it into any text field; Play alpha. Proof: https://github.com/abrahamyants/wim-android <!-- src: assets.md -->
- Lavrentiy: the same voice-to-intent engine for Windows, one installer, works offline; v1.7.11. Proof: https://github.com/abrahamyants/lavrentiy/releases/latest <!-- src: assets.md -->
- NoiseFile: Android noise-complaint kit; public on Google Play. Proof: https://play.google.com/store/apps/details?id=com.wimlabs.noisefile <!-- src: assets.md -->
- Heirloom: Android photo restoration for old family photos (repair, faces, upscale, face check, optional color); Play alpha; engine review: 126.5 s run, face similarity 0.895. Proof: https://github.com/gugosf114/heirloom-android <!-- src: assets.md -->
- Climate Permit: satirical Android quiz that sorts drivers into 16 types by their climate-control habits; Play alpha. Proof: https://github.com/gugosf114/climate-permit <!-- src: assets.md -->
- Bakers Agent: the system that runs the bakery's marketing; in production. Proof: https://bakers-agent.web.app <!-- src: assets.md -->
- mybakingcreations.com: the bakery's site; live. Proof: https://mybakingcreations.com (repo gugosf114/gugosf114.github.io) <!-- src: assets.md -->
- Stratos: paid client site plus ops page for a private-jet detailing company. Proof: https://stratosjetdetail.com/ops/ <!-- src: assets.md -->
- Audit Ledger: tamper-evident California residency audit-defense ledger (SHA-256 hash chains, 19 Bragg factors). Proof: https://gugosf114.github.io/audit-ledger <!-- src: assets.md -->
- Yalta: game, live at https://yalta.gugosf.workers.dev plus APK (found running; not on George's shelf list) <!-- src: assets.md -->
- Signal: card-price app, APK 3.6 on portfolio-assets (found running; not on George's shelf list) <!-- src: assets.md -->
- phone-errands: phone-ask and phone-do through Bland (found running; not on George's shelf list) <!-- src: assets.md -->
- cookie-robot: brain tested, hardware not ordered (found running; not on George's shelf list) <!-- src: assets.md -->

## Education

- UC College of the Law, San Francisco (formerly UC Hastings): JD, Tax Concentration, 2018; CALI Award; Production Editor, Hastings Business Law Journal <!-- src: resume.txt -->
- University of California, Berkeley: BA with honors, Political Science; Minor, Southeast Asian Studies, 2015; Distinction in General Scholarship; GPA 3.85 <!-- src: resume.txt, george-dossier.md, George 2026-10-26 -->
- Came to the US at 17; City College of San Francisco night classes at 26, then Berkeley, then Hastings <!-- src: george-dossier.md -->

## Patent

- Sole inventor, U.S. provisional patent application No. 64/100,336, filed June 27, 2026, 35 claims, covering the combined mobile and desktop voice-to-intent architecture behind WiM and Lavrentiy <!-- src: linkedin-experience-2026-10-17.txt, resume.txt -->

## Languages

- English; Armenian, native; Russian, fluent <!-- src: resume.txt, george-dossier.md -->

## Settled 2026-10-26 (Fable, from George's own files; two items still wait for George)

- Drift Auditor numbers (512 conversations / 37,536 messages / 101 failures): OFF every resume and letter. George's order of 2026-07-24 stands; the 2026-08-04 re-add was without his word. His LinkedIn page is his to edit. <!-- src: resume-master check block, george order 7/24 -->
- GPA 3.85 belongs to the Berkeley BA (Political Science, 2015, Distinction in General Scholarship). The JD line carries the CALI Award and Hastings Business Law Journal, no GPA. <!-- src: george-dossier.md line 9, resume.txt -->
- JD is NOT cum laude (George, 2026-10-26). Never write it; the four 2026-08 resumes that say so are wrong. The Berkeley BA is with honors: Distinction in General Scholarship, 3.85. <!-- src: George 2026-10-26 -->
- Years of legal, compliance, and regulated-operations work: 8. Never "ten" or "a decade". <!-- src: answers.json, george-facts.json years_experience -->
- NoiseFile numbers: use the newest read, assets.md 2026-10-17 (36 cities, 108 workflows, public on Play). Re-read the repo README before the next letter; numbers move. <!-- src: assets.md -->
- Bakery site: 117 HTML files and 1,414 commits as of 2026-10-17; "44 pages / 917 commits" is stale. <!-- src: assets.md -->
- Baba v. SOS International decision: the public DOL copy is live, checked 2026-10-26 (HTTP 200, PDF): https://www.dol.gov/sites/dolgov/files/brb/decisions/lngshore/unpublished/Jan18/17-0440.pdf <!-- src: curl 2026-10-26 -->
- Audit Ledger: the repo is private; a live public dashboard exists (assets.md). A letter may cite the dashboard, never a repo link. <!-- src: assets.md, george-dossier.md -->
- WiM and Lavrentiy repo owner: abrahamyants/wim-android and abrahamyants/lavrentiy. The old gugosf114/... links redirect there (checked 2026-10-26), so either works, write abrahamyants. <!-- src: gh repo view 2026-10-26 -->
- Email on resumes and forms: gugosf@berkeley.edu. <!-- src: george-dossier.md, every resume -->
- Standing rule (George, 2026-10-18): read the README of any asset in full before it goes in a letter. <!-- src: assets.md -->
- The ten lines that lived only in 2025 cover letters: removed on George's order 2026-10-26. The resume already covers that ground.

## Lanes (which bullets serve which kind of job; the picker cuts one page from these)

AI evaluation / legal expert gigs: S19, S20, S21, S22, S23, S24, S25, S26, S27, S28, S29, S31, S32, S10, S11, S12, S13, S14, A5, E7, E8, E9, E1, E2, E4, E5, A4, B3
Legal ops & contracts: P1, P2, P3, P4, A2, A4, A8, A9, A10, S36, S37, S38, S39, S43, E4, E6, E12, E13, B1
Compliance & regulatory: A1, A2, A3, A6, A7, A8, A10, B1, B2, B4, B5, B6, B7, P2, P3, P4, P5, S34, S35, S36, S37, E10, E11, E3
AI governance: S5, S4, S1, S2, S3, S24, S34, S35, S19, S23, S25, S30, S31, S38, S15, S18, A5, A6, P4
Not in a lane on purpose: product and site facts (S6-S9, S16, S17, S33, S40-S42) are proof lines a letter can borrow; the L block is letter-only and stays out until George confirms it.
