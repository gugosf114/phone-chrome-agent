#!/bin/sh
set -eu

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PHONE_HOME=${HOME:-/data/data/com.termux/files/home}
INSTALL_ROOT=$PHONE_HOME/.local/share/agent-bridge/task-engine
STATE_ROOT=$PHONE_HOME/.local/state/agent-bridge
STATE_DB=$STATE_ROOT/task-engine.sqlite3

mkdir -p "$INSTALL_ROOT" "$STATE_ROOT"
rm -rf "$INSTALL_ROOT/agent_bridge_task" "$INSTALL_ROOT/phone"
cp -R "$SOURCE_DIR/agent_bridge_task" "$INSTALL_ROOT/agent_bridge_task"
cp -R "$SOURCE_DIR/phone" "$INSTALL_ROOT/phone"
chmod 700 "$INSTALL_ROOT/phone/agentbridge-task"

"$INSTALL_ROOT/phone/agentbridge-task" --help >/dev/null
if ! command -v browser-runner-daemon >/dev/null 2>&1; then
    printf '%s\n' 'AGENT_BRIDGE_TASK_INSTALL_ERROR browser-runner-daemon is unavailable' >&2
    exit 1
fi
printf '{"status":"installed","taskEngine":"%s","state":"%s","browserRunnerSocket":"%s"}\n' \
    "$INSTALL_ROOT/phone/agentbridge-task" \
    "$STATE_DB" \
    "$PHONE_HOME/.cache/browser-headless/browser-daemon.sock"
