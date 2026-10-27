# WiM (What I Meant) + the provisional patent · WEIGHT: FULL (app in Play closed testing; patent filed)

**What WiM is.** An Android voice-to-text app for people who stutter or speak accented or messy English. A floating bubble over
any app; you hold to record, you end the take (no timer cuts you off); speech is transcribed (on-device Whisper, or the WiM
cloud), cleaned, and pasted into the field you were in. Four layers: transcribe, reconstruct, personal profile, speech
disfluency. The disfluency layer handles blocks, part-word repetitions, prolongations, covert word-swapping (the app's
name), with a preservation guard so "really really" survives. Delayed auditory feedback built in. Password fields refused.
It never sends on its own. Lavrentiy is the Windows twin (v1.7.11, offline).
**Status.** Google Play closed testing, release 658 (1.0.0, Oct 13 2026); pricing live (Free / Cloud $4.99 / Cloud Plus
$7.99). George, 10/27: code review done, buying the 12 testers next, then the 14-day test, then production. Furthest of the
apps from public.
**The patent.** U.S. provisional App. No. 64/100,336, filed June 27 2026, sole inventor, micro entity, 18 pages, 35 claims.
Title: "Assistive overlay system for real-time bidirectional clarification and reconstruction of speech-recognized input
with application-context invariance, multilingual interlanguage normalization, dynamic target stabilization, and
write-integrity recovery." Claim 1: a persistent overlay captures speech, reconstructs it, shows up to three uncertain words
for the user to approve or fix WITHOUT changing the host app's focus, cursor, scroll, keyboard, or selection, writes the
revised text back, and keeps the text if the write fails. Other independent claims: user-gated send (a countdown that
disarms, never auto-sends; the bubble moves onto the app's own send button), spatial text-grab transformation, the
five-layer reconstruction stack (verbatim → intent → personal profile → clinical disfluency → interlanguage, detecting
non-native grammar transfer from text, not accent). Prior art named: Siri, Google Assistant, Wispr Flow, Gboard, Apple
Dictation. Provisional: pending; a non-provisional must follow within 12 months (by June 27 2027) to keep the date.
**Lavrentiy, the Windows twin (read 2026-10-27).** One Python program packaged as Lavrentiy.exe, v1.7.11 (Sept 6 2026),
~508 MB installer with the speech model inside, so dictation works with no internet and no account. Hotkey to record,
local Whisper small.en with multi-temperature voting and a disagreement map, disfluency filter, paralinguistic detection,
reconstruction with a deterministic meaning guard, paste into the active app. Per-user profiles with a 60-prompt
calibration where every transcript is confirmed by the user before it becomes ground truth; a local audio archive; covert
stuttering detection; a phonetic risk model; exposure difficulty scoring; redo detection against compulsion; delayed
auditory feedback. Interface in English, Spanish, Russian, Portuguese, French; cloud transcription in 11 languages;
first-language transfer packs for Russian, Spanish, Mandarin, Hindi, Arabic, Farsi, French, German, Korean. The README's
own origin line: built by a political refugee from Armenia who arrived without English and lives with a speech block and a
strong accent. Repo abrahamyants/lavrentiy, public, 474 commits, pushed Oct 11 2026.
**What the patent protects (George, 10/27; screenshots in Drive "WIM Android & Lavrentiy Screenshots", 6/27).** The
invention is the bubble: a persistent overlay on the phone that clarifies uncertain words without touching the app under
it, a send-ready countdown that disarms instead of sending, and the bubble that jumps onto the app's own Send button.
That is a phone thing; nobody needs a bubble on a desktop. The filing names a desktop embodiment in two of its 35 claims as a
drafter's hedge, but the product the patent protects is WiM. Lavrentiy is the engine and the lab: the speech pipeline, the
calibration, the stutter research, a full dashboard window (console, sessions, learning, insights, calibrate, profile). WiM
is the product. Next for WiM: buy the 12 testers, 14-day test, production. Beyond text: the phone-call lane (WiM Line) already
proved the far end hears clean speech, and there is a live FCC docket on replacing the human relay operator with ASR and
TTS, a market that pays per minute. That is the long road: a speech prosthesis for calls and chat, not a dictation toy.
**What it proves.** He designed a system and wrote the patent himself; he builds for his own disability; he ships to Play
with billing and a backend; he can write a technical legal document.
**The sentence.** "I built WiM, a voice-to-text Android app with a speech-disfluency layer, in Google Play testing with
pricing live, and I am the sole inventor on its 35-claim US provisional patent (App. No. 64/100,336)."
**Cite when:** speech, voice, dictation, accessibility, assistive tech, patents/IP, product design, Android, Windows desktop, on-device/offline AI, Whisper, multilingual products, AI products,
anything where "built it for myself and filed the patent" lands.
**Proof.** github.com/abrahamyants/wim-android (public) · Play app id 4972415189316953363 · me/samples/patent-provisional-64-100336-2026-06.pdf
