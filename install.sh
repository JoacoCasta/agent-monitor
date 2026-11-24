#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MONITOR_DIR="$HOME/.gemini/agent-monitor"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_LABEL="com.agentmonitor.app"
PLIST_PATH="$LAUNCH_AGENTS_DIR/$PLIST_LABEL.plist"
PREFS_FILE="$MONITOR_DIR/preferences.json"
USER_UID="$(id -u)"

# 1. Stage Python helper scripts
mkdir -p "$MONITOR_DIR" "$LAUNCH_AGENTS_DIR"

cp "$SCRIPT_DIR/Scripts/hook-handler.py" "$MONITOR_DIR/hook-handler.py"
cp "$SCRIPT_DIR/Scripts/claude-statusline.py" "$MONITOR_DIR/claude-statusline.py"
cp "$SCRIPT_DIR/Scripts/fetch-quota.py" "$MONITOR_DIR/fetch-quota.py"
cp "$SCRIPT_DIR/Scripts/configure-hooks.py" "$MONITOR_DIR/configure-hooks.py"
chmod 755 "$MONITOR_DIR/hook-handler.py" "$MONITOR_DIR/claude-statusline.py" "$MONITOR_DIR/fetch-quota.py" "$MONITOR_DIR/configure-hooks.py"

# 2. Build & sign before touching hooks
INSTALL_APP_DIR="$("$SCRIPT_DIR/build.sh" | tail -n 1)"
APP_BIN="$INSTALL_APP_DIR/Contents/MacOS/AgentMonitor"

# 3. Sync provider hooks safely
if [ -f "$PREFS_FILE" ]; then
    ENABLED_CSV="$(/usr/bin/python3 - "$PREFS_FILE" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    provs = [p for p in d.get("enabledProviders", []) if p in ("antigravity", "codex", "claude")]
    print(",".join(provs) if provs else "antigravity")
except Exception:
    print("antigravity")
PY
)"
    /usr/bin/python3 "$MONITOR_DIR/configure-hooks.py" sync "$ENABLED_CSV" >/dev/null
else
    /usr/bin/python3 "$MONITOR_DIR/configure-hooks.py" enable antigravity >/dev/null
fi

# 4. Install and start LaunchAgent
cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$APP_BIN</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>HOME</key>
        <string>$HOME</string>
        <key>PATH</key>
        <string>$HOME/.gemini/bin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>$MONITOR_DIR/app.log</string>
    <key>StandardErrorPath</key>
    <string>$MONITOR_DIR/app.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$USER_UID" "$PLIST_PATH" >/dev/null 2>&1 || true
pkill -x AgentMonitor >/dev/null 2>&1 || true
sleep 0.3
launchctl bootstrap "gui/$USER_UID" "$PLIST_PATH"

echo "Installed: $INSTALL_APP_DIR"
echo "LaunchAgent: $PLIST_PATH"
echo "Scripts: $MONITOR_DIR"
