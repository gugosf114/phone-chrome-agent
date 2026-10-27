#!/bin/bash
# RETIRED 2026-09-26. This copied George's login cookies from his daily Chrome into the Linux hidden Chrome.
# Google marks copied logins "signed out" within about an hour (9/26: copied 5:02pm, dead by 6:46pm,
# ListAccounts said valid=0 signed_out=1 for all 7 accounts). Every re-copy died the same way.
# Use the signed-in browser instead: web/phone-chrome.sh (Chrome Beta on the hidden screen, CDP 9335).
echo "pull-logins is retired: copied logins die within an hour. Use: bash /root/hidden-operator/web/phone-chrome.sh up  (CDP 127.0.0.1:9335)"
exit 1
