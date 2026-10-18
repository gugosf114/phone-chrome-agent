# The shelf — what George built that runs and can be shown

> **Standing note (George, 2026-10-18 00:10):** this shelf and every job letter built from it rest on a partial read. Of 40 repos, 23 READMEs were read in full, WiM's in full, and 16 only their top 50 to 110 lines. Code was not read. So any letter or form answer that shows off an asset may carry errors, and those errors can surface in an interview. George said: "whatever you do is going to contain lots of errors... sorry but I should have prepared the better." Every session that drafts from this page must know that and must read the full README of any asset it puts in a letter before writing the line.

Built 2026-10-17 by reading, not memory: all 33 repos on gugosf114, all 7 on abrahamyants, the Play Console by API (`play apps`, `play tracks`), and every live site by fetch. Every number names its source. `scripts/check_assets.py` re-pulls each source and confirms the number is still there.

Rule (George, 2026-10-17): only things that run and can be shown. No drift tools, no papers, no field notes, no Agent Bridge, no Vapi lines, nothing without a repo, nothing half built.

## Apps on Google Play (five packages on the Console; four are his)

- **WiM (What I Meant)** — Android voice-to-text that cleans messy, stuttered, or accented speech and pastes it into any text field. Status: Play alpha, release 658 (1.0.0), completed; production track empty (Play API 2026-10-17). Testers: one Google group on the track. Latest APK vc658, 2026-10-13. Repo abrahamyants/wim-android, 659 commits. Patent: U.S. provisional App. No. 64/100,336, 35 claims, sole inventor (profile README). Proof: https://github.com/abrahamyants/wim-android. Lane: product, accessibility, AI build.
- **Lavrentiy** — the same voice-to-intent engine for Windows, one installer, works offline. Status: v1.7.11 released 2026-09-06, installer ~508 MB (README). Repo abrahamyants/lavrentiy, 474 commits. Proof: https://github.com/abrahamyants/lavrentiy/releases/latest. Lane: product, accessibility, AI build.
- **NoiseFile** — Android noise-complaint kit: measure, check the city's own rule, file it the way that city wants; $7.99 unlock. Status: PUBLIC on Google Play as "Neighbor Noise Complaint Kit" by WiM Labs, production release 0.30.8 (vc61), in-app purchases, 5+ downloads (store page read in the laptop's Chrome 2026-10-17; the Play API shows the same release completed). Store: https://play.google.com/store/apps/details?id=com.wimlabs.noisefile Numbers from the catalog file itself: 36 cities, 108 rule workflows; legal-corpus manifest 67 entries across 15 cities. Repo gugosf114/noisefile-android, 202 commits. Proof: https://github.com/gugosf114/noisefile-android. Lane: legal ops, civic tech, AI build.
- **Heirloom** — Android photo restoration for old family photos: repair, faces, upscale, face check, optional color; 3 free, then Play packs. Status: Play alpha and internal, 1.0.0-rc9 (vc9), completed; production track empty (Play API 2026-10-17). The README line "Google Play's current release remains RC6" does not match the API. Engine review 2026-10-11: real run 126.5 s total, face similarity 0.895 (docs/ENGINE_REVIEW.md). Repo gugosf114/heirloom-android, 40 commits. Proof: https://github.com/gugosf114/heirloom-android. Lane: product, AI build.
- **Climate Permit** — satirical Android quiz: your car's climate controls sort you into one of 16 types; shareable California-license-style card. Status: Play alpha and internal, 1.1.1 (vc6), completed; production empty (Play API 2026-10-17). Repo gugosf114/climate-permit, 41 commits. Proof: https://github.com/gugosf114/climate-permit. Lane: product, fun, shows range.
- Not on the shelf: Samizdat (me.aap.fermata.auto.samizdat, internal only) is a rebrand of someone else's open-source player, not George's product.

## Things that run a business

- **Bakers Agent** — the robot that runs the bakery's marketing: photos in, Claude writes, George approves, posts go to Google, Facebook, Instagram, Pinterest, YouTube; SEO opens pull requests on the site by itself. Status: in production, live at https://bakers-agent.web.app (fetched 200, 2026-10-17); last README update 2026-09-30. Repo gugosf114/bakers-agent, 443 commits. Lane: AI ops, agent build, marketing automation.
- **mybakingcreations.com** — the bakery's site, the first thing George ever built. Status: live (fetched 200, 2026-10-17). Repo gugosf114/gugosf114.github.io, 1,414 commits (the profile README still says 917: stale), 117 HTML files in the repo (README says 44 pages: stale). Last 30 days (mbc-stats, 2026-10-17): 2,192 sessions, 1,684 users, 1 paid-search session; Search Console 757 clicks, 32,879 impressions. Lane: web build, SEO, small-business ops.
- **Stratos** — a real client's site plus an ops page (the field app) for a private-jet detailing company. Status: live at https://stratosjetdetail.com (200) and https://stratosjetdetail.com/ops/ (200), 2026-10-17; repo gugosf114/Stratos, 114 commits, last 2026-09-24. Paid client work (George's own words in journal NEXT). Lane: client web build, ops tooling.

## Paper outcomes (no repo; proof is the document on LinkedIn)

- **ALJ decision** — a 23-page Defense Base Act decision George drafted as judicial extern to ALJ Richard M. Clark, DOL OALJ, 2017; affirmed on appeal, Baba v. SOS International, LLC, BRB No. 17-0440 (Jan. 30, 2018). Proof: writing sample on LinkedIn (https://www.linkedin.com/in/george-abrahamyan). A public DOL copy was searched for 2026-10-17 and not found. Lane: legal writing.
- **Santa Rosa permit** — the 33-page conditional-use-permit application for a cultivation, distribution, and manufacturing facility, City of Santa Rosa, 2021, with 11 exhibits from five outside firms; unanimous approval, state licensing (LinkedIn experience text, saved 2026-10-17). Proof: project-description PDF on LinkedIn. Lane: legal ops, regulatory, project lead.

## George decides

- **Audit Ledger** — tamper-evident California residency audit-defense ledger: SHA-256 hash chains, the 19 Bragg factors. Status: live dashboard https://gugosf114.github.io/audit-ledger (200, 2026-10-17); repo gugosf114/audit-ledger, 97 commits, last 2026-07-31. Lane: tax law as code.
- Also found running, not on your list: Yalta (game, https://yalta.gugosf.workers.dev live + APK, 24 commits), Signal (card-price app, APK 3.6 on portfolio-assets), phone-errands (phone-ask / phone-do via Bland), cookie-robot (brain tested, hardware not ordered).

## Mismatches found while reading

- Profile README (gugosf114/gugosf114): "917 commits" on the bakery site; GitHub says 1,414.
- Bakery site README: "44 pages"; repo holds 117 HTML files.
- Heirloom README: "Play's current release remains RC6"; the Play production track is empty.
- NoiseFile README top says 108 workflows / 36 cities; a lower paragraph says 45 workflows / 15 cities. The catalog file says 108 / 36.
