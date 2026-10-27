# Picks — the picker's one file per gather

The picker is the model (Fable) that reads a gather file against `me/george-dossier.md`, `me/writings.md`,
`me/assets.md`, and `me/resume-master.md`, and decides. It writes ONE file here per run instead of talking in chat:
`picks/picks-<stamp>.json`. The apply walker reads that same file as `--overrides`, so nothing is retyped.

Shape (one entry per gathered job id):

```json
{
  "4483601187": {
    "decision": "yes",
    "why": "AI legal-expert gig, remote, hourly; matches the Turing/Synthires lane in the dossier",
    "letter": "First line: WiM patent + 449-case correction corpus; second: Andersen SALT controversy; close with hourly availability",
    "resume": "ai-eval",
    "rules": [["years of experience with (contract|legal) review", "8"], ["rate|hourly", "75"]]
  },
  "4483292009": {
    "decision": "no",
    "skip": "wall: bar admission (Active CA Bar Required)"
  },
  "4480235281": {
    "decision": "ask",
    "ask": "Corporate Counsel at loanDepot wants 'licensed in any US state' — George never took the bar; confirm no"
  }
}
```

Keys the walker uses: `skip` (job is skipped, reason logged) and `rules` (per-job answer rules, tried before the book).
Keys for people: `decision` (yes | no | ask), `why`, `letter` (the cover-letter angle, 1–2 lines), `resume` (which one-page
cut from the master: `ai-eval`, `legal-ops`, `compliance`, `ai-governance`), `ask` (the one question only George can answer).

Rules:
- Every `no` gets a reason; walls from `walls.json` are quoted as-is. Every `no` also goes into `scripts/no.json` so the
  gather never shows that job again.
- `ask` entries are read to George in chat, one line each. His answer turns them into `yes` + `rules` or `no`.
- The walker is run as `node scripts/map_easy_apply.cjs --ids <yes ids> --overrides picks/picks-<stamp>.json` (map only).
  `--submit` only on George's word, per job.
- The picks file is committed. It is the receipt of what was chosen and why.

Flow: gather → picks → George answers the asks → walk the yes list → receipt.
