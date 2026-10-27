# Invisible Work: Measuring the Human Cost of AI Alignment · WEIGHT: LESS/MEDIUM (a paper; public tool + data; submitted to Anthropic)

**What it is.** A 6-page paper, February 2026, answering a gap Anthropic named in its January 28 2026 "Who's in Charge?"
paper (safeguards only look at single exchanges). George built the other side: what the human has to do, across many turns,
to keep a model on task. Metrics: Operator Load Index, Alignment Tax, Instruction Survival Rate, Self-Sufficiency Score,
Correction Efficiency. A 10-tag model-side taxonomy plus a 12-rule operator-side system. Tool: Drift Auditor (public repo,
live demo), air-gapped from the generator because a debugger using the same model inherits the drift.
**Data and finding.** 512 of his own conversations, 37,536 messages, 187 Claude / 325 ChatGPT, one operator. Drift scores
nearly equal (2.9 vs 3.0) but very different load: Claude took 741 corrections and held 98.7% of them (fails loud); ChatGPT
took 101 and silently dropped 55% of instructions (fails quiet). "The quiet one is more dangerous."
**Honest limits (in the paper).** Heuristic weights, one operator, a light embedding model, no ground-truth calibration.
**What it proves.** He can frame a measurement nobody had, build the tool, run it on real data, and write it up against the
lab's own literature. Listed on LinkedIn Publications as submitted to Anthropic's research team.
**The sentence.** "I wrote Invisible Work, a measurement of the human correction burden across 512 real conversations, built
the open-source Drift Auditor behind it, and submitted it to Anthropic's research team."
**Cite when:** AI evaluation, red-teaming, model behavior, alignment, AI safety research roles, LLM QA, annotation leads.
**Proof.** github.com/gugosf114/drift-auditor/docs/research/Invisible_Work.pdf · me/samples/invisible-work-2026-02.pdf
