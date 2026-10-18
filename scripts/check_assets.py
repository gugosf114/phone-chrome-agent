#!/usr/bin/env python3
"""Re-pull every source named in me/assets.md and confirm the number is still there.
Run: python3 scripts/check_assets.py   (prints OK / MISMATCH per line; exit 1 on any mismatch)"""
import json, re, subprocess, sys, urllib.request

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

def readme(repo):
    return sh(f'gh api repos/{repo}/readme -H "Accept: application/vnd.github.raw"')

def commits(repo):
    hdr = sh(f'gh api "repos/{repo}/commits?per_page=1" -i')
    m = re.search(r'page=(\d+)>; rel="last"', hdr)
    return int(m.group(1)) if m else None

def tracks(pkg):
    return sh(f'play tracks {pkg}')

def http(url):
    try:
        return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'check-assets'}), timeout=20).status
    except Exception as e:
        return getattr(e, 'code', str(e))

checks = []  # (label, got, expected, ok)
def add(label, got, expected):
    checks.append((label, got, expected, str(got) == str(expected) or (isinstance(expected, str) and expected in str(got))))

# commits
for repo, n in [('abrahamyants/wim-android', 659), ('abrahamyants/lavrentiy', 474), ('gugosf114/noisefile-android', 202),
                ('gugosf114/heirloom-android', 40), ('gugosf114/climate-permit', 41), ('gugosf114/bakers-agent', 443),
                ('gugosf114/gugosf114.github.io', 1414), ('gugosf114/Stratos', 114), ('gugosf114/audit-ledger', 97), ('gugosf114/yalta', 24)]:
    add(f'commits {repo}', commits(repo), n)

# Play tracks
t = tracks('com.wimlabs.wim'); add('WiM alpha 658', '"658 (1.0.0)"' in t and '"track": "production"\n  },' in t, True)
t = tracks('com.wimlabs.noisefile'); add('NoiseFile production 0.30.8 vc61', '"name": "0.30.8"' in t and '"61"' in t, True)
t = tracks('com.wimlabs.heirloom'); add('Heirloom alpha rc9 vc9', '"1.0.0-rc9"' in t and '"9"' in t, True)
t = tracks('app.climatepermit.android'); add('Climate Permit 1.1.1 vc6', '"1.1.1"' in t and '"6"' in t, True)

# READMEs
r = readme('abrahamyants/wim-android'); add('WiM README vc658 2026-10-13', 'vc658' in r and '2026-10-13' in r, True)
r = readme('abrahamyants/lavrentiy'); add('Lavrentiy README v1.7.11 ~508 MB', 'v1.7.11' in r and '508 MB' in r, True)
r = readme('gugosf114/gugosf114'); add('profile README patent 64/100,336', '64/100,336' in r, True)
r = readme('gugosf114/heirloom-android'); add('Heirloom README rc9', '1.0.0-rc9' in r, True)
r = sh('gh api repos/gugosf114/heirloom-android/contents/docs/ENGINE_REVIEW.md -H "Accept: application/vnd.github.raw"')
add('Heirloom engine review 126.5 s / 0.895', '126.5 seconds' in r and '0.895' in r, True)

# NoiseFile catalog counts
cat = json.loads(sh('gh api repos/gugosf114/noisefile-android/contents/app/src/main/assets/rules/catalog-v1.json -H "Accept: application/vnd.github.raw"'))
add('NoiseFile catalog cities', len(cat['jurisdictions']), 36)
add('NoiseFile catalog workflows', len(cat['rules']), 108)
man = json.loads(sh('gh api repos/gugosf114/noisefile-android/contents/legal-corpus/manifest.json -H "Accept: application/vnd.github.raw"'))
add('NoiseFile manifest entries', len(man['entries']), 67)

# site html count
add('bakery site HTML files', sh("gh api repos/gugosf114/gugosf114.github.io/git/trees/main --jq '.tree[].path'").count('.html\n'), 117)

# live sites
for url in ['https://www.mybakingcreations.com', 'https://bakers-agent.web.app', 'https://stratosjetdetail.com/', 'https://stratosjetdetail.com/ops/',
            'https://gugosf114.github.io/audit-ledger/', 'https://yalta.gugosf.workers.dev']:
    add(f'live {url}', http(url), 200)

bad = 0
for label, got, exp, ok in checks:
    print(('OK       ' if ok else 'MISMATCH ') + label + ('' if ok else f'  got={got} expected={exp}'))
    bad += (not ok)
print(f'\n{len(checks)-bad} ok, {bad} mismatch. Live traffic numbers (mbc-stats) are a dated snapshot, not re-checked here.')
sys.exit(1 if bad else 0)
