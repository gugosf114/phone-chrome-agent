# Picks — the picker's one file per gather

The picker is the model (Fable) that reads a gather file against `me/george-dossier.md`, `me/writings.md`,
`me/assets.md`, `me/resume-master.md`, and the per-job asset hits from `python3 scripts/asset_hits.py <gather.json>`
(me/triggers.json ties job words to assets: noise ordinance -> NoiseFile, patent -> the WiM patent, ...), and decides. It writes ONE file here per run instead of talking in chat:
`picks/picks-<stamp>.json`. The apply walker reads that same file as `--overrides`, so nothing is retyped.

Shape (one entry per gathered job id):

```json
{
  "4483601187": {
    "decision": "yes",
    "why": "AI legal-expert gig, remote, hourly; matches the Turing/Synthires lane in the dossier",
    "letter": "<the letter's full text, under 150 words, in the dossier's voice>",
    "resume": "ai-eval",
    "resume_file": "C:\\Users\\georg\\job-applications\\4483601187\\George_Abrahamyants_Resume_Turing.pdf",
    "letter_file": "C:\\Users\\georg\\job-applications\\4483601187\\George_Abrahamyants_Cover_Letter_Turing.pdf",
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

Keys the walker uses: `skip` (job is skipped, reason logged), `rules` (per-job answer rules, tried before the book),
`letter_text` (the letter itself, typed key by key when a form offers a text box; `letter` is the human angle and is never typed), `resume_file` and `letter_file` (10/27: Windows paths on the laptop, e.g.
`C:\Users\georg\job-applications\<jobId>\George_Abrahamyants_Resume_<Company>.pdf`; the walker uploads or selects these),
and `letter` (10/27: the letter's full text, under 150 words; typed into a cover-letter text box when there is no
`apply/<jobId>/cover-letter.txt`). Without `resume_file` / `letter_file` the walker uses the `apply/<jobId>/` folder
(meta.json names, pushed by `scripts/push_apply_files.sh`). A form that offers a cover letter with no letter in picks and
no folder stops that job: NEEDS_LETTER.
Keys for people: `decision` (yes | no | ask), `why`, `resume` (which one-page cut from the master: `ai-eval`, `legal-ops`,
`compliance`, `ai-governance`), `ask` (the one question only George can answer).

Rules:
- Every `no` gets a reason; walls from `walls.json` are quoted as-is. Every `no` also goes into `scripts/no.json` so the
  gather never shows that job again.
- `ask` entries are read to George in chat, one line each. His answer turns them into `yes` + `rules` or `no`.
- The walker is run as `node scripts/map_easy_apply.cjs --ids <yes ids> --overrides picks/picks-<stamp>.json` (map only).
  `--submit` only on George's word, per job.
- The picks file is committed. It is the receipt of what was chosen and why.

Flow: gather → picks (+ apply/<jobId>/ files for every yes, pushed to the laptop) → George answers the asks → walk the yes list → receipt.
