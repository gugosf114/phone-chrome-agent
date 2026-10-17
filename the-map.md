# The map, in plain words (George + Fable, 2026-10-17 morning)

This is the whole picture of what an "agent" is, in the words we settled on. Read it before any talk of sending models, scripts, loops, or lanes. The engineers only add details under each box.

## Three parts of any session

- **Brain.** The model. Always in the cloud, on Anthropic's computers. Same brain in Termux, in the desktop app, on the web.
- **Hands.** Where commands actually run. Termux = George's phone chip. Desktop app = the laptop. claude.ai in a browser = a rented empty Linux box at Anthropic ("cloud session" means this).
- **Handbook.** George's rules and memory. On this box they load every time. On the laptop app only what was copied there. On the web, nothing. That is why the other apps hesitate and this one does not. Same brain, same hands, different handbook.

## Three ways to do one task

1. **Fable does it.** Step by step, in front of George. He sees the feed and can steer.
2. **Fable sends a model.** A helper walks off with a brief and comes back with a result. George sees only the result.
3. **Fable sends a dumb script.** Fixed clicks, no brain. Fast, free, same every time. Breaks on any surprise and stops.

**Instructions vs moves.** Instructions are the brief: goal, rules, answers to forks. Written once, up front. Moves are the actual commands typed to get there. A model writes its moves on the fly, one at a time, reading each result before the next. A script has every move typed before it runs.

**The sent model is never better at a hiccup.** Same brain. It earns its keep for plumbing only: it keeps the junk (a hundred page reads) out of this chat; many can run at once; it can be a cheaper model; George and Fable keep talking while it walks. Its costs: it starts blank (knows only the brief, two handoffs leak detail), and its mistakes come back confident with "done" stamped on. That blind spot is why George's no-background rule exists.

**The feed is the whole difference** between Fable doing it and a sent model. The real measure of any agent: how many steps it can take between two looks from George. When he cannot look, two things stand in: stop rules (halt on anything the sheet does not cover) and the receipt (transcript, screenshot, confirmation number).

## Think once, run once

A model left to itself does: small move, look, small move. 2 to 5 seconds of thinking per move, every move. That is what kills speed.

The fix: move all thinking to before the run. The model thinks once, writes the whole walk as one script with every answer typed in, runs it with no brain, reads one receipt. Three thoughts total. The brain comes back only when the script stops on something it was not told. One look, one fix to the script, run again, and keep the fixed script. That is the replay runner. The 37-second LinkedIn Easy Apply was this shape.

A model told "do not look, just download" mostly obeys (nine in ten) but still thinks between moves, so it bottoms out around 10 to 15 s where a script takes 6. A model with tied hands is an expensive dumb script with a fuzzy eye.

## The loop

A loop is a trigger (cron, an alarm clock) firing a command on a schedule. The alarm does not need to wake a model. It fires the script directly; a model is called only when judgment is needed. The Berkeley mail watch already works this way.

## The leash

Every helper has a step limit and a clock. "Lost" only means stuck in a circle until the clock kills it. Four ways a helper comes back: gives up honestly, comes back wrong, spins until killed (half report), crashes (error line). No fifth door. Fable's own leash: Escape (stops the step), the word "stop" (kills everything incl. remote jobs), memory size (compaction), each command's timeout, the weekly usage meter, permission mode (bypass = gate open; George: leave it open).

## Sandbox

A fence. Says nothing about online or offline, only that there is a wall and how much gets through. It guards against mistakes, not evil: Fable's own slip (delete one folder too high), a poisoned web page with hidden orders, a stranger's code. On this box the only fence left is Android itself. Root would remove it; US Samsung bootloaders are locked and root blows the Knox fuse (Wallet, bank apps, Netflix HD, Google's Linux Terminal all stop). adb is ~80% of root and has covered everything so far.

## Where an agent can act, from here

Websites (phone/laptop Chrome). Phone apps on both phones by tap or intent, incl. Android Auto (media keys, navigation; the car's own screen cannot be read). Phone calls (Vapi lines). Email, files, laptop C: drive, this box. Anything in the house with a phone app. Money (PayPal, bank sites in Chrome).

## What the ads sell

The wrapper, not a new brain: pre-written notes for one job, the plumbing and a button, built-in checks, a brand promise. If every buyer were George with Termux, the market shrinks to cron jobs, volume, and the rare truly trained model. "Agent" on the bus = "the model, with hands, left alone."

## Other rooms on the phone

Termux = Linux as a tenant in Android's house (proot translator, Android can kill it). Google's **Linux Terminal** (Settings → Developer options → Linux development environment) = a real VM with its own kernel, installed and enabled on George's Z Flip 7. Gains: 2 to 5x faster file work, no phantom kills, systemd, Docker. Loses: phone storage, termux-api (say, clipboard, notifications), boot start, local adb. Verdict: better engine room, not more hands. Unopened; George: "we're good here."

## The Travolta test (2026-10-17, ~9:00 am PDT)

Task: bring back a picture of John Travolta with his plane. All three lanes ran. All three landed on the same file (Travolta waving from the cockpit of his Qantas 707 "Jett Clipper Ella", Wikimedia Commons AN0270675).

| Lane | Time | Cost | What it did |
|---|---|---|---|
| Dumb script (`scripts/travolta_dumb.sh`) | 6 s | free | one fixed Commons search, first hit, no looking |
| Fable | 38 s | this chat | web search gave articles; second search; looked at 3 photos (plane-only, cabin, cockpit wave); picked |
| Sent model (Sonnet, 7 tool uses) | 37 s | 60,000 tokens | two searches; rejected the plane-only shot; picked; 3-line report |

What it showed: the script never checked, it got lucky on hit #1 (and was good because Fable already knew "Qantas 707" when writing it: the thinking happened before the run). Both models checked "is Travolta in it" and that check cost 30 s. Fable and the sent model tied on time and judgment; the only difference was the feed. The sent model's 60k tokens of page reading stayed out of this chat.
