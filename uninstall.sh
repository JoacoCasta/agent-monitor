#!/bin/bash
set -euo pipefail

MONITOR_DIR="$HOME/.gemini/agent-monitor"
CONFIGURE_PY="$MONITOR_DIR/configure-hooks.py"
PLIST_LABEL="com.agentmonitor.app"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"
USER_UID="$(id -u)"

if [ -f "$CONFIGURE_PY" ]; then
    /usr/bin/python3 "$CONFIGURE_PY" disable antigravity >/dev/null 2>&1 || true
    /usr/bin/python3 "$CONFIGURE_PY" disable codex >/dev/null 2>&1 || true
    /usr/bin/python3 "$CONFIGURE_PY" disable claude >/dev/null 2>&1 || true
fi

launchctl bootout "gui/$USER_UID" "$PLIST_PATH" >/dev/null 2>&1 || true
pkill -x AgentMonitor >/dev/null 2>&1 || true
rm -f "$PLIST_PATH"

rm -rf "/Applications/AgentMonitor.app" "$HOME/Applications/AgentMonitor.app" "$MONITOR_DIR"

echo "AgentMonitor uninstalled cleanly."
