# Google Ads: fix card, pay, publish an app-installs campaign
Machine: phone hidden-screen Chrome Beta (worked, painfully); next time laptop Chrome
Last worked: 2026-10-14 (about 1 hour, ~50 round trips; sibling session)
Last broke: 2026-10-14 — first "Confirm it's you" passed but Chrome froze before Publish landed; port died twice; pasted text ignored; buttons off the narrow screen; "get the app" door on every page
Needs from the answer book: card on file (George's wallet list), app Play link, region (Bay Area), end date, daily budget, headlines
Steps:
1. Billing → "Fix it" → pick a different card from the wallet list → "Maybe later" on moving other services
2. Account paused → make a payment ($20 became ad credit)
3. New campaign → app installs → find app by Play link → location Bay Area → end date → headlines → $4/day → Publish
4. "Confirm it's you" passkey check → wait for it to close → Publish again if the first did not land
Stop on: passkey/2-step prompt that does not close by itself; payment box that will not take typed digits
Receipt: campaign shows as published in the Ads campaigns list
Script: scripts/clickread.cjs (finger clicks, letter-by-letter typing, reads inside the payment box)
