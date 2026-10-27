# Heirloom — Restore Photos · WEIGHT: FULL (testing done; waiting on Google; one press to production)

**What it is.** Android app that restores one old family photo at a time: repair damage, rebuild faces, upscale, check the
restored face still matches the original, add color only when asked. "For your family, not your followers." Three free
restorations per install, then Play packs of 5/20/50. No ads, accounts, subscriptions, or watermarks.
**How it is built.** Kotlin + Compose → Play Integrity + Play Billing → Cloudflare Worker with a D1 credit ledger → Cloud Run
L4 GPU: one image-editing model call (OpenAI gpt-image or Gemini), Real-ESRGAN upscale, AdaFace identity check. Photos are
streamed, not stored. A visible warning when the identity check detects drift; in-app reporting for bad AI output.
**Status (Play Console 2026-10-27).** Closed testing, 1.0.0 (vc10) updated today, installed audience 23. George: testing
finished, waiting on Google's approval, then production.
**What it proves.** A full consumer AI product with server-verified purchases, GPU backend, and honest AI-safety UX.
**The sentence.** "Heirloom restores old family photos with a Gemini/OpenAI image engine behind a Cloudflare credit ledger and a
GPU backend; Android, Google Play, going to production."
**Cite when:** image AI, consumer AI products, GPU/cloud backends, Play Billing, AI product safety and transparency.
**Proof.** github.com/gugosf114/heirloom-android · Play app id 4974990437391069681
