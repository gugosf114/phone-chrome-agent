#!/bin/bash
# push_apply_files.sh <jobId> — copy one job's resume and cover letter PDFs to the laptop, under their upload names.
# Built 2026-10-27. Reads apply/<jobId>/meta.json for the names ("George_Abrahamyants_Resume_<Company>.pdf",
# "George_Abrahamyants_Cover_Letter_<Company>.pdf"); lands them in C:\Users\georg\job-applications\<jobId>\ and prints
# the Windows paths. The applier (map_easy_apply.cjs) hands those paths to the laptop Chrome's file box.
set -e
ID="$1"; [ -n "$ID" ] || { echo "usage: bash scripts/push_apply_files.sh <jobId>"; exit 2; }
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; DIR="$ROOT/apply/$ID"
[ -f "$DIR/meta.json" ] || { echo "no $DIR/meta.json"; exit 1; }
RES=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["resume_name"])' "$DIR/meta.json")
LET=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["letter_name"])' "$DIR/meta.json")
WIN="C:/Users/georg/job-applications/$ID"
ssh -o ConnectTimeout=15 -o BatchMode=yes wimlaptop "powershell -NoProfile -Command \"New-Item -ItemType Directory -Force -Path '$WIN' | Out-Null\""
scp -q -o ConnectTimeout=15 -o BatchMode=yes "$DIR/resume.pdf" "wimlaptop:$WIN/$RES"
scp -q -o ConnectTimeout=15 -o BatchMode=yes "$DIR/cover-letter.pdf" "wimlaptop:$WIN/$LET"
# read back from the laptop: both files there, with their sizes
ssh -o ConnectTimeout=15 -o BatchMode=yes wimlaptop "powershell -NoProfile -Command \"Get-ChildItem -LiteralPath '$WIN' -Filter *.pdf | ForEach-Object { \$_.FullName + ' (' + \$_.Length + ' bytes)' }\""
