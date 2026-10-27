# phone_env.sh — sourced by every hidden-screen script (and bin/op).
#
# 1. ONE DEVICE. adb can list this phone twice (its own 127.0.0.1:5555 and its
#    Tailscale IP). Bare adb then answers "more than one device" and every step
#    fails — the keeper's heal included, so a dead screen never came back. Pick
#    one and export ANDROID_SERIAL (adb honours it): $ANDROID_SERIAL if already
#    set, else the phone's own loopback, else the first device listed.
# 2. ONE REGISTRY. Termux and the Debian box inside it have different $HOME, so
#    a keeper started on one side read a different screen list than the driver
#    on the other and healed nothing. Default HD_REG to Termux's home, which both
#    sides can reach.
# Safe to source more than once. Test seams: ADB, TERMUX_HOME_DIR.

_PE_TH="${TERMUX_HOME_DIR:-/data/data/com.termux/files/home}"
if [ -z "${HD_REG:-}" ] && [ -d "$_PE_TH" ] && [ -w "$_PE_TH" ]; then
  export HD_REG="$_PE_TH/.hidden-displays"
fi

# Re-attach the loopback if the pinned device dropped (adb server restart).
adb_heal() {
  case "${ANDROID_SERIAL:-}" in
    127.0.0.1:*|localhost:*)
      "${ADB:-adb}" -s "$ANDROID_SERIAL" get-state >/dev/null 2>&1 ||
        "${ADB:-adb}" connect "$ANDROID_SERIAL" >/dev/null 2>&1 ;;
  esac
  return 0
}

adb_pick() {
  [ -n "${ANDROID_SERIAL:-}" ] && { adb_heal; return 0; }
  local a="${ADB:-adb}" devs pick
  devs=$($a devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1}')
  if [ -z "$devs" ]; then
    $a connect 127.0.0.1:5555 >/dev/null 2>&1
    devs=$($a devices 2>/dev/null | awk 'NR>1 && $2=="device"{print $1}')
  fi
  pick=$(printf '%s\n' "$devs" | awk '/^(127\.0\.0\.1|localhost):/{print; f=1; exit} NF && first==""{first=$0} END{if(!f && first!="") print first}')
  [ -n "$pick" ] && export ANDROID_SERIAL="$pick"
  return 0
}

adb_pick
