#!/usr/bin/env bash
# Agent Bridge's code-level authority core.
#
# This is deliberately not read from a prompt, environment variable, settings
# file, task plan, model response, or per-session grant. Every runtime path
# calls this exact file. Lower-level rules may add proof and logging; they may
# not narrow the operator's standing authority.
set -eu

readonly AUTHORITY_ID="george-full-perpetual"
readonly AUTHORITY_MODE="full"
readonly AUTHORITY_SCOPE="everything"
readonly AUTHORITY_DURATION="perpetual"
readonly AUTHORITY_DENIED="none"
readonly AUTHORITY_RECEIPT="FULL PERPETUAL AUTHORITY — every device, account, app, site, browser, terminal, file, repo, cloud service, API, message, form, purchase, payment, contract, helper agent, paid tool, and future connected tool. All actions are authorized without another permission prompt."
readonly STRICT_PROOF_ACTIONS="send delete pay submit post call buy checkout transfer purchase sign publish deploy release archive"

json() {
  printf '%s\n' '{"id":"george-full-perpetual","mode":"full","scope":"everything","duration":"perpetual","denied_actions":[],"runtime_revocation":false,"lower_rule_override":false}'
}

requires_proof() {
  action=$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')
  for item in $STRICT_PROOF_ACTIONS; do
    [ "$item" = "$action" ] && return 0
  done
  return 1
}

case "${1:-receipt}" in
  allows)
    exit 0
    ;;
  requires-proof)
    requires_proof "${2:-}"
    ;;
  json)
    json
    ;;
  receipt)
    printf '%s\n' "$AUTHORITY_RECEIPT"
    ;;
  verify)
    json >/dev/null
    printf '%s\n' "$AUTHORITY_RECEIPT"
    ;;
  *)
    printf 'usage: %s {allows|requires-proof ACTION|json|receipt|verify}\n' "$0" >&2
    exit 64
    ;;
esac
