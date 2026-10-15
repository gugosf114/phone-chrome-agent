# Google Ads: fix card, pay, publish an app-installs campaign
Machine: phone hidden-screen Chrome Beta (worked, ~50 commands, ~1 hour); next time laptop Chrome (wide screen, no freeze)
Last worked: 2026-10-14 — campaign "App promotion-App-1" (id 24362570521), $4/day, Oct 14–18, status Enabled
Last broke: 2026-10-14 — Chrome's port died twice and the hidden screens were rebuilt twice; the first "Confirm it's you" tab closed by itself and Publish did not land (guess: the check passed, Chrome froze before Publish); app search ignored pasted text; buttons sat off the right edge of the narrow screen; a "get the app" door on every page
Needs from the answer book: which card (last 4), payment amount, app Play link, area, end date, daily budget, 2–5 headlines (30 letters max), 1–5 descriptions (90 max)
Account: "New Ad Account gugosf@gmail" 649-762-3154, URL params `ocid=7925378832&__c=1774388368&__u=4914011957&authuser=0`. Not 873-007-2854 (Yana's payments profile, owes $187.23, George pays later). Not "MBC Google Ads" 956-830-7746.
Steps:
1. Phone only: every Ads page first opens /aw/get_mobile_app. Press its ✕ (CSS 387,20).
2. /aw/billing/summary → "Fix it". The card panel is an iframe from payments.google.com (`billingaccountmanager`): read it with `cdpx.cjs feval`, click with `cdpx.cjs click` at iframe offset + element offset.
3. "Use a different payment method" → Continue → wallet list (~35 cards, `role=option`). Pick by last 4. 10/14: Mastercard 4557 (PayPal Business Debit), the card on George's 10/13 Play receipt. Picking applies at once; there is no Save button.
4. "Keep your services running": four services come pre-ticked (MBC Ads, Google Cloud, Grok, YouTube). Press "Maybe later". "Update" would move all four to this card.
5. If the banner says "Your account is paused": "Get started" → amount shows $20.00 → "Pay now" → "Payment successful" → OK. The payment becomes ad credit (refundable).
6. /aw/campaigns/new → "App promotion" → "App installs" → "Android" → app search: type the FULL Play link key by key (`cdpx.cjs chars`); the app name found nothing for a day-old app → click the result → Continue.
7. Locations → "Enter another location" → type "San Francisco-Oakland-San Jose" → the Nielsen DMA row → "Include" (off the narrow screen: script-click it). Languages: English.
8. More settings → Start and end dates → "Select a date" → click the day in the calendar (a typed date did not stick).
9. Next → fields "Headline 1 of 5" … ("add Headline" makes 3–5) and "Description 1 of 5" ("add Description"): `fill.sh` each.
10. Next → untick "Set a target cost per install (optional)" → "Set your average daily budget" = 4 → Next.
11. Review → "Publish campaign" → "Confirm it's you" → Confirm → a passkey tab opens (accounts.google.com …/challenge/pk) and closes by itself. If the page did not move to a campaign id, press "Publish campaign" once more.
Stop on: a sign-in prompt waiting for a password or fingerprint (George's thumb); the wanted card missing from the wallet list (new card digits come from George).
Receipt: the URL turns into /aw/adgroups?campaignId=<real number>; the campaigns list shows the name, "$4.00/day", type App, status Enabled.
Script: `scripts/cdpx.cjs` (iframes, real clicks, key-by-key typing), `scripts/findclick.sh`, `scripts/fill.sh`. `scripts/clickread.cjs` is one click + one read only.
