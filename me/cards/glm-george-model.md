# George's own retrainable open-weight model (GLM-4.5-Air QLoRA) · WEIGHT: FULL for AI/ML roles (in use; live endpoint)

**What it is.** His own fine-tune of the public GLM-4.5-Air model, trained to remove behaviors he does not want from an
assistant: hedging, claiming "done" when it is not, not reading, over-restriction. Method: 4-bit nf4 QLoRA adapters on an
H200 (RunPod), trained from question→answer flash cards he wrote and curated; each version tested against a fixed probe set
(47 probes at v3) and compared to the base and the prior version; answer-only continuation encoding; end-token repair so
replies stop naturally (median reply fell from 104 words to 6 at v9). Served as an OpenAI-compatible endpoint on Modal with
a phone client. Versions v1 through v9 recorded in the repo (v9 trained 2026-10-22); George says v11 as of 10/27. Public
adapters v4–v8 on Hugging Face under gabrahamyants; newer ones private.
**Rebuild recipe.** Public base + cards/ + trainer/ = the model again in about 40 minutes. Repo gugosf114/glm-george-recipe
(private): cards, trainer, probes, results, MODEL-LOG.md.
**What it proves.** Hands-on fine-tuning of an open model with a measured objective, versioned data, probe-based evaluation,
and deployment. For AI-evaluation and model-behavior roles this is the direct receipt.
**The sentence.** "I fine-tune my own GLM-4.5-Air with QLoRA on an H200, from hand-written training cards, versioned and
probe-tested through eleven releases, served on Modal, to train out hedging and false completion claims."
**Cite when:** fine-tuning, LoRA/QLoRA, open-weight models, model behavior, evaluation, RLHF-adjacent work, AI trainer gigs.
**Rule.** Describe the method and the objective. Never describe the card contents beyond "behaviors I wanted out."
**Proof.** huggingface.co/gabrahamyants (adapters v4–v8 public) · github.com/gugosf114/glm-george-recipe (private)
