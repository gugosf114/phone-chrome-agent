#!/bin/bash
# dumb script: one fixed search on Wikimedia Commons, take the first hit, download it. No thinking.
Q="John Travolta Boeing 707"
URL=$(curl -s "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$Q")&gsrnamespace=6&gsrlimit=1&prop=imageinfo&iiprop=url&iiurlwidth=1200&format=json" -A "george-travolta-test/1.0" | python3 -c 'import json,sys; p=json.load(sys.stdin)["query"]["pages"]; print(list(p.values())[0]["imageinfo"][0]["thumburl"])')
[ -z "$URL" ] && { echo "NOT FOUND"; exit 1; }
curl -s -A "george-travolta-test/1.0" -o dumb.jpg "$URL" && echo "OK $URL"
