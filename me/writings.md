# George's writings and public receipts (read before writing any cover letter)

Everything here is public on LinkedIn or GitHub. Cite the one that fits the job. Never invent a paper.

## Papers and manuals

1. **12 Rules for AI: An Operator's Field Manual** (Dec 2025, 29 pages, 17 academic citations). github.com/gugosf114/12-rules-for-ai. Protocols for people using LLMs in legal, finance, audit, compliance work. The twelve rules: Name the Disease; the Rumsfeld Protocol (knowns vs unknowns); the Operator Boundary; Force the Contradiction; the Not-Shot Rule; the Ledger (off-model audit trail); Never Let the Model Architect; the Sunday Rule (every session is a cold start); Shadow Memory; Manufactured Agreement; the Tiger Tamer; Document the Failures. Built from months of his own logged sessions. 277 impressions.
2. **NotebookLM as a Deterministic Compiler** (Dec 2025, 4 pages). github.com/gugosf114/notebooklm-compiler. Three-layer lock: Cognitive Mode, Hierarchical Truth ("the Draft is the Rule, the Log is the Fact"), Format Lock. Triage Protocol, Null Protocol, Extraction Protocol. Used to extract 400k+ characters from 35 operator logs with zero drift. The first post on it reached 1,825 impressions.
3. **AEGIS: A 10-Layer Prompt Architecture** (Dec 2025, 9 pages, MIT). github.com/gugosf114/aegis. Constrains an LLM into an auditable forensic analyst: truth hierarchies, conflict triage, void detection, adversarial deception detection, format-locked outputs, plus Newton Sentinel, a Python runtime that turns the model's signals into machine-verifiable escalation objects.
4. **Air-Gapped Compilation: A Procedural Solution to LLM Drift in Structured Extraction** ("Why LLMs Can't Police: 3-Validation Architecture", Jan 2026, 9 pages, LinkedIn document). The Iron Pipeline: Generator, Auditor (cannot see the generator's reasoning), Regenerator (rebuilds from scratch). Tested on GPT-4, Gemini, Claude. Thesis: the model cannot police itself; enforcement must live outside the model.
5. **Invisible Work: Measuring the Human Cost of AI Alignment** (Feb 2026, 6 pages; listed Jun 2026 on LinkedIn). github.com/gugosf114/drift-auditor, docs/research/Invisible_Work.pdf. Written as a reply to Anthropic's Jan 28 2026 "Who's in Charge?" disempowerment paper. Introduces the Operator Load Index, Alignment Tax, Instruction Survival Rate, Self-Sufficiency Score. Run on 512 of his own Claude and ChatGPT conversations, 37,536 messages. Finding: equal drift scores, different failure styles: Claude fails loudly (more corrections, more instructions kept), ChatGPT quietly. Live demo on Streamlit.

## Tools behind the papers
- **Drift Auditor**: multi-turn omission-drift diagnostic, 10-tag taxonomy (sycophancy, reality distortion, confidence inflation, instruction drop, semantic dilution, correction decay, conflict pair, shadow pattern, operator move, void) and a 12-rule operator-side system. The one eval category nobody had: how hard the human worked.
- **ai-operator-field-notes** (private): the record behind Drift Auditor and Invisible Work; ~90 numbered, dated, model-authored failure logs.
- **conversation-corpus** (private): 449 adjudicated correction cases; the evidence base behind his Claude rules file.
- **reply-shape** (public): deterministic reply-shape enforcement around an LLM, built as an accessibility accommodation for his OCD.

## Legal writing receipts
- Decision and Order in a Defense Base Act psychological-injury claim, drafted as judicial extern to ALJ Richard M. Clark (DOL OALJ, 2017), 23 pages, affirmed on appeal: Baba v. SOS International, LLC, BRB No. 17-0440 (Jan 30 2018). Writing sample on LinkedIn.
- 33-page conditional-use-permit application, City of Santa Rosa, 2021, with 11 exhibits from five outside firms; unanimous approval, state licensing. Project description PDF on LinkedIn.
- Production Editor, Hastings Business Law Journal. CALI Award.

## LinkedIn posts worth citing (all public)
- /mnt/transcripts discovery (Mar 2026): Claude's sandbox writes full transcripts per compaction; the model can read them back; cited the open claude-code issue #26771. 442 impressions, 2 screenshots.
- "How to get on your AI's nerves #1": contradictory-instruction test on Claude.
- "I have no programming background. None." The origin post for 12 Rules: JD, ten years in contracts/compliance/state tax, documented sycophancy, lost-in-the-middle, context degradation as structural, not user, failures.
- Google AI Mode / "Google foots the bill" joke post (Jul 2026).

## Profile facts (LinkedIn, Oct 17 2026)
Headline: AI Evaluations & Operations | JD, UC Hastings | LLM Reliability | AI Governance. 430 connections, 450 followers. Open to work (recruiters only): San Francisco Bay Area, on-site, hybrid, remote. Top skills: AI Governance, Tax Compliance, LLMs, SALT, Regulatory Compliance. Featured: the ALJ decision, the bakery site (917 commits, ~2,000 monthly visitors on zero ad spend, Fortune 500 logo cookies, Ice Cube's 55th birthday cake), Bakers Agent, WiM + Lavrentiy. Earlier roles not on the resume: SF Assessor-Recorder policy intern (2016; outreach materials, translated into Russian and Armenian), AIDS Legal Referral Panel law clerk (2016; housing, consumer, bankruptcy memoranda; represented clients in grievance meetings), USPS Pacific Area Law Office extern (EEOC/MSPB motions and settlements), IRS Chief Counsel extern (pleadings, motions for tax litigation).

## How a cover letter uses this
Match one receipt to the job's main ask. AI eval or red-team job: Invisible Work + Drift Auditor numbers. AI governance or compliance: AEGIS + Audit Ledger + Andersen. Legal ops or contracts: Phenotopia ($1.75M buildout, MSAs, NDAs, vendor contracts) + the CUP. Legal writing: the ALJ decision affirmed on appeal. Research or annotation gigs: 12 Rules + 512-conversation study. Say "JD" and "lawyer by training," never "attorney." Under 150 words unless asked.
