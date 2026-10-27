# Bakers Agent ("Agent Dun") · WEIGHT: FULL (in production, runs a real business every day)

**What it is.** An autonomous marketing and operations system for a small business, running live for My Baking Creations
since 2026 on Google Cloud. Photos or a reel go in on the Content page; Gemini looks at the photos, Claude writes the title,
caption, labels and alt text; George or Yana taps Approve; the post goes out to Google Business Profile (both listings),
Facebook, Instagram, Pinterest, and YouTube Shorts. Nothing posts without the tap. Reels: 3–8 photos become a 1080x1920
video with Pillow and ffmpeg, Claude Opus picks the kind of reel and writes each app's words, an optional AI clip (Veo)
opens it.
**What runs on its own.** A traditional SEO track (Search Console data → opportunities → content briefs → pull requests
on the website repo, with a quality gate); an AI-search-visibility track (does ChatGPT, Gemini, Perplexity, Copilot mention
the business; schema audit; llms.txt); a feedback loop that measures merged PRs and feeds results back; persistent
confidence-weighted memory; daily GA4 and Search Console snapshots with anomaly alerts; GBP review fetch and drafted
replies (human tone check); brand NAP consistency across GBP, Yelp, Facebook, Apple Maps; AI commerce feeds; customer
segmentation to Klaviyo; Google Ads drafts (human budget gate); reorder prediction; a weekly digest email; MCP tool
discovery behind an approval gate. A System tile turns red when a function is stuck, behind GitHub, or a post failed.
**How it is built.** Python 3.12 on Google Cloud Functions (2nd gen), 40+ functions in named pipelines, Firestore, Pub/Sub with
dead-letter queues, Cloud Scheduler, Secret Manager, GitHub Actions CI, a React + TypeScript + Tailwind dashboard on Firebase
Hosting. Models: Claude Sonnet 4.6 and Opus 5.5, Gemini 2.5/3.1 Pro, GPT-4o and Perplexity for visibility checks. Bakers
Agent 2 is the multi-client commercial build (isolated deployments, onboarding, site audits).
**Status.** Production. README last updated 2026-09-30; repo pushed through October. Public repo, live dashboard.
**What it proves.** He designed, built, and operates a real multi-model agent system with approval gates, event-driven
cloud architecture, observability, and a feedback loop, for a business that depends on it. This is the strongest "I ship
AI operations" receipt he has.
**The sentence.** "I built and run Bakers Agent, a 40-function Google Cloud agent system that runs a live bakery's marketing
and SEO behind human approval gates, posting to five platforms and opening its own pull requests."
**Cite when:** AI operations, agentic systems, LLM products, marketing automation, GCP/serverless, approval-gated AI,
small-business tech, AI governance in practice, SEO/AI search.
**Proof.** github.com/gugosf114/bakers-agent (public) · bakers-agent.web.app/mbc/ (dashboard) · the bakery's live posts
