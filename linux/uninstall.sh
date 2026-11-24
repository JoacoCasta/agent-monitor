#!/bin/bash
set -euo pipefail

MONITOR_DIR="$HOME/.gemini/agent-monitor"
CONFIGURE_PY="$MONITOR_DIR/configure-hooks.py"

if [ -f "$CONFIGURE_PY" ] && command -v python3 >/dev/null 2>&1; then
    python3 "$CONFIGURE_PY" disable antigravity >/dev/null 2>&1 || true
    python3 "$CONFIGURE_PY" disable codex >/dev/null 2>&1 || true
    python3 "$CONFIGURE_PY" disable claude >/dev/null 2>&1 || true
fi

pkill -f "agent_monitor.py" >/dev/null 2>&1 || true

rm -f "$HOME/.local/bin/agent-monitor"
rm -f "$HOME/.local/share/applications/agent-monitor.desktop"
rm -f "$HOME/.config/autostart/agent-monitor.desktop"
rm -rf "$MONITOR_DIR"

echo "Agent Monitor uninstalled cleanly."
