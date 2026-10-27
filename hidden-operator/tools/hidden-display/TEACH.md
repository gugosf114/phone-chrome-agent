# Teach-once (the "photo way") — a taught skill on a hidden screen

Teach the phone a task **once**, then it replays it by itself — on a hidden screen the
owner never sees. It finds each button by a **photo** of it, not by the button's name,
so it works where the accessibility tree can't reach (see "Why the photo way" below).

`scripts/teach_skill.sh` (+ `tools/hidden-display/match.py`). Verified on SM-F766U/A16:
taught "789" on a hidden calculator, then replayed it onto a fresh calculator — the phone
typed 789 on its own, matching each key at confidence 1.000.

## Use
```sh
# teach: perform the task with `tap` — each tap snaps a photo of that button, saves it
# as the next step, then presses it.
bash scripts/teach_skill.sh new    pay-rent
bash scripts/teach_skill.sh tap    pay-rent 180 1640     # (cx cy of the button you mean)
bash scripts/teach_skill.sh tap    pay-rent 415 1640
...
bash scripts/teach_skill.sh steps  pay-rent              # show the recorded steps

# replay: for each step, snap the screen, find that photo, tap where it is NOW.
bash scripts/teach_skill.sh replay pay-rent

bash scripts/teach_skill.sh list                         # all skills
bash scripts/teach_skill.sh drop   pay-rent
```
Targets hidden screen `$HD_NAME` (default `main`). Skills live in `$HD_SKILLS`
(default `~/.hidden-skills`): one folder per skill with `NNN.png` button photos + a
`steps.tsv` (`idx cx cy radius`). Needs python3 + PIL, and OpenCV **or** NumPy for the match.

## How the match works
`match.py FRAME.png TEMPLATE.png [--near CX CY R]` slides the button photo over the
screen (OpenCV `matchTemplate`, normalized) and prints `<cx> <cy> <conf>` — the best
spot and a 0..1 score. Replay searches **near** the taught spot first, so it prefers the
button where it was taught and isn't fooled by an identical-looking button elsewhere.
It survives the button **moving** (finds it wherever it went); it does NOT survive the
button **changing look** (new theme/text) — that's the photo way's one limit.

## Why the photo way (and not button-names)
On a hidden screen the OS hands over its **system** bar but not an **app's** buttons:
the accessibility "names" pipe only opens for the display holding input focus, and a
hidden display can't take focus (measured — no command sets it, a tap doesn't move it).
So we match pictures instead. The button-name route (`UD.java`) is kept as a probe and
still works on the **visible** screen; the hunt for a hidden-screen name-read continues.
