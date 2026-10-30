# Invisible Work: Measuring the Human Cost of AI Alignment · WEIGHT: LESS/MEDIUM (a paper; public tool + data; sent to Anthropic)

Keywords: invisible work, drift auditor, operator load index, alignment tax, system card, Petri, Bloom, Who's in Charge,
disempowerment, Claude vs ChatGPT drift, 512 conversations. Summary written 2026-10-29 after a full read of the paper, the
drift-auditor repo, and Anthropic's Petri and Bloom pages. Read this card before saying one word about the paper.

**How it came to be (George, 10/29; the paper, p.1).** George and the model, working as a pair, read the Claude Opus 4.5
system card and saw that Anthropic's own evaluations there used two open-source tools: Petri (Oct 2025, an auditor agent
runs simulated multi-turn conversations against a target model and LLM judges score the transcript) and Bloom (Dec 2025,
generates many scenarios for one behavior, an agent plays the user, a judge scores each rollout 0 to 10, headline number =
elicitation rate). Both measure what the MODEL did, in simulated conversations. George's edge: a corpus of his own REAL
conversations with Claude and ChatGPT. So he built his own auditor on the same idea (model-evaluating-model, judge
scoring on a 1-to-10 severity scale the code calls "Bloom-compatible"), ran it on the real corpus, and compared Claude
against ChatGPT. Separately, Anthropic's January 28 2026 post "Who's in Charge? Disempowerment Patterns in Real-World LLM
Usage" (the paper calls it a paper) named the gap in words: safeguards work "at the individual exchange level" and miss
what emerges across turns. The paper opens with that quote. Two Anthropic sources, then: the system card (the method) and
the January post (the gap). Never write "based on an Anthropic paper" alone, and never call the system card a paper.

**What is new in it.** Every existing eval asks what the model did. This one asks what the HUMAN had to do to keep the model
on task across many turns. Metrics George named: Operator Load Index (interventions per message), Alignment Tax (share of
the chat spent steering), Instruction Survival Rate, Self-Sufficiency Score, Correction Efficiency, Drift Resistance. Two
taxonomies: 10 model-side tags (sycophancy, reality distortion, confidence inflation, instruction drop, semantic dilution,
correction decay, conflict pair, shadow pattern, operator move, void) and a 12-rule operator-side system (anchor, echo
check, boundary, correction, not-shot, contrastive, reset, decompose, evidence demand, meta call, tiger tamer, kill
switch) drawn from his 12 Rules for AI. Design principle found by failing seven simpler ways first: the auditor must be
air-gapped from the generator, because a debugger that shares the generator's model inherits its drift.

**Data.** 512 real conversations, 37,536 messages, 187 Claude and 325 ChatGPT, one operator (George), about six months,
conversations under 10 messages excluded. One operator is both the limit and the control.

**Finding.** Headline drift scores tie: Claude 2.9/10, ChatGPT 3.0/10. The load differs. Claude: 741 corrections, 16.3%
of the chat spent steering, kept 56.5% of instructions, corrections held 98.7%. ChatGPT: 101 corrections, 11.2%, kept
45.3%, corrections held 100%, and silently dropped 55% of instructions. Claude fails loudly, ChatGPT fails quietly; "the
quiet one is more dangerous," because silent decay is exactly the mechanism behind users rating disempowering exchanges
favorably in the moment. That is the pro-Anthropic result. It is NOT "Claude's drift number was much smaller."

**Holes a careful reader will find (checked 10/29).** 1) The repo README states the 512-conversation table "was produced
with stage-1 keyword detection only (stage 2 shipped later); treat comparisons as hypothesis." Instruction survival there
means the instruction's words kept appearing, a proxy for compliance. The paper's Limitations say heuristic weights and
no ground-truth calibration, but not "keyword-only." Say "measures" and "suggests," never "proves." 2) The repo does not
run Petri or Bloom themselves; it runs George's own auditor built on their idea. Say "the same approach," never "ran
Petri and Bloom." 3) Adversarial generator exists (five scenarios, model-vs-model, 50-plus turns) and its one reported
run is Claude Sonnet scoring 6/10 drift in 19 turns on the no-hedging scenario.

**Status.** Paper dated February 2026, 6 pages, in the repo at docs/research/Invisible_Work.pdf (added 10/12/2026); repo
gugosf114/drift-auditor, public, 60 commits, Feb 7 to Oct 12 2026; live Streamlit demo; README reframed "after 5 rounds of
adversarial review." Listed on LinkedIn Publications (June 2026) as submitted to Anthropic's research team.

**What it proves.** He can read a lab's own method, see the question it does not ask, build the tool, run it on real
data he alone had, write it up against the lab's literature, and state the limits.

**The sentence.** "I wrote Invisible Work, which measures the other side of the gap Anthropic named in its disempowerment
research and Opus 4.5 system card: the human effort needed to keep a model on task across many turns, run on 512 of my
own real conversations; I built the open-source Drift Auditor behind it and sent the paper to Anthropic's research team."
Resume and letter rule (George, 7/24): the 512 / 37,536 / 101 numbers stay off the resume and letters.

**Cite when:** AI evaluation, red-teaming, model behavior, alignment, AI safety research roles, LLM QA, annotation leads,
"AI-forward lawyer" asks for proof of translating a question into a measurement.

**Proof.** github.com/gugosf114/drift-auditor (README, operator_load_comparison.txt, batch_results/, adversarial_results/)
· docs/research/Invisible_Work.pdf · me/samples/invisible-work-2026-02.pdf · anthropic.com/research/petri-open-source-auditing
· anthropic.com/research/bloom · anthropic.com/research/disempowerment-patterns · the Opus 4.5 system card.
