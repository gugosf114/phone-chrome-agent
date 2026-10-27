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
**Opened and read live, 2026-10-27, signed in.** Today tile: "6 people are waiting. Money this week: $3,990." Leads this week 31
(vs 39), paid $3,990 (up 105% vs $1,947), website visits 383, reply time 1 h (12 of 28 answered within the hour). Six replies
drafted and waiting: three website-form cake orders (reply ready), three Instagram thank-yous. "What's working": a baby-shower
cake post, 47 views; Google Fiber branded cake pops, 37. A "call before the holidays" list of 4 customers who ordered last
Oct–Dec and not yet this year. Posts tab: upload a photo, Claude writes, pick Google Business / Facebook / Instagram / Pinterest,
Single / Multiple / Reel. Money tab: every number for any period against the same days before (visits 436, page views 1,030,
quote forms sent 54 up 17%, where visits came from incl. AI apps). More: Social, Google Profile, Website & search, Activity,
System, Businesses, Fleet. Build 58651d6.
**Bakers Agent 2, the commercial build (WEIGHT: LESS, work in progress).** Repo gugosf114/bakers-agent-2, started
2026-07-04, last push 2026-10-04. A full copy that diverges from the bakery repo; the bakery is never touched and joins later
as tenant one. Plan: early clients get isolated deployments, not shared multi-tenant; free first month, SF Bay local, George
onboards in person; the bar is a couple of paying clients. Two doors: the GitHub door (SEO fixes as pull requests, proven)
and the "snippet door", one script line pasted into Wix, Squarespace, WordPress, or GoDaddy that applies approved title,
meta, JSON-LD, alt, and canonical fixes client-side. The pitch: photo-to-post, one-click SEO fixes, and AI-visibility
monitoring in one bundle with human onboarding, where the closest competitors (Predis, Alli AI, Otterly, Birdeye) sell each
piece alone for $18–$499 a month. Has: onboarding, site audits, private dashboards, scheduled drafts, guided pilots. Does
not have yet: a paying client. In a letter: one clause at most, "and a multi-client version in progress"; never a platform claim.
**What it proves.** He designed, built, and operates a real multi-model agent system with approval gates, event-driven
cloud architecture, observability, and a feedback loop, for a business that depends on it. This is the strongest "I ship
AI operations" receipt he has.
**The sentence.** "I built and run Bakers Agent, a 40-function Google Cloud agent system that runs a live bakery's marketing
and SEO behind human approval gates, posting to five platforms and opening its own pull requests."
**Cite when:** AI operations, agentic systems, LLM products, marketing automation, GCP/serverless, approval-gated AI,
small-business tech, AI governance in practice, SEO/AI search.
**Proof.** github.com/gugosf114/bakers-agent (public) · bakers-agent.web.app/mbc/ (dashboard) · the bakery's live posts
