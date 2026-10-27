# web-booking — learn-once / fire-fast web agent

Drives a headless Chrome (via CDP) to observe an unfamiliar site, run a saved
recipe fast, and stop before any money step. Proven end-to-end on OpenTable:
account sign-in, book a table, cancel — hands-free.

## Pieces
- `webfast.cjs observe <tab>` — list every link/button/input with a stable selector.
- `webfast.cjs run <tab> <skill.json> [--arm]` — fire a saved recipe; times each
  step; STOPS before buy/pay/checkout/reserve/confirm unless `--arm`.
- `pg.cjs <tab> <js|@file> | --fill <css> <text> | --key Enter` — reliable single-tab driver.
- `ot_book.cjs <city>` — full scripted OpenTable booker (self-timed). Identity is read
  from `booker.env` (JSON, gitignored) or `BOOK_*` env vars — never hardcoded.
- `drive.cjs` / `drive_mobile.cjs` — step driver (desktop / mobile UA).
- `start.sh` — launch the headless Chrome on an Xvfb display, CDP on 127.0.0.1:9222.

## Setup
1. `cp booker.env.example booker.env` and fill in your name/email/phone.
2. `bash start.sh` to bring up the headless Chrome.
3. Sign in once (phone OTP) — after that, bookings need no per-booking SMS.

## Findings (2026-09-21)
- Signed-in OpenTable booking ≈ 16s, **no SMS**. Guest booking needs a code every time.
- Cancel (identical learned flow) ≈ 2s.
- A recipe partly transfers across restaurants on the same site; each venue can add
  a page (seating, "choose options", card hold) — a finite set to learn.
