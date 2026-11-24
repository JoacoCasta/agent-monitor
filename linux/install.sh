#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MONITOR_DIR="$HOME/.gemini/agent-monitor"
DESKTOP_DIR="$MONITOR_DIR/desktop"
VENV_DIR="$MONITOR_DIR/venv"
PREFS_FILE="$MONITOR_DIR/preferences.json"
BIN_DIR="$HOME/.local/bin"
APPS_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
AUTOSTART_DIR="$HOME/.config/autostart"

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 (3.9+) is required." >&2
    exit 1
fi

SYS_PYTHON="$(command -v python3)"
if ! "$SYS_PYTHON" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "Error: Python 3.9 or higher is required." >&2
    exit 1
fi

# Stop any running instance
pkill -f "agent_monitor.py" >/dev/null 2>&1 || true

mkdir -p "$MONITOR_DIR" "$DESKTOP_DIR" "$BIN_DIR" "$APPS_DIR" "$ICON_DIR" "$AUTOSTART_DIR"

# 1. Stage shared scripts & desktop UI
cp "$REPO_ROOT"/Scripts/*.py "$MONITOR_DIR/"
cp "$REPO_ROOT"/desktop/*.py "$DESKTOP_DIR/"
cp "$REPO_ROOT/desktop/requirements.txt" "$DESKTOP_DIR/requirements.txt"
chmod 755 "$MONITOR_DIR"/*.py "$DESKTOP_DIR"/*.py

if [ -f "$SCRIPT_DIR/agent-monitor.png" ]; then
    cp "$SCRIPT_DIR/agent-monitor.png" "$ICON_DIR/agent-monitor.png"
elif [ -f "$REPO_ROOT/linux/agent-monitor.png" ]; then
    cp "$REPO_ROOT/linux/agent-monitor.png" "$ICON_DIR/agent-monitor.png"
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

# 2. Create/update venv with PySide6
if [ ! -x "$VENV_DIR/bin/python" ]; then
    "$SYS_PYTHON" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip --quiet
"$VENV_DIR/bin/python" -m pip install -r "$DESKTOP_DIR/requirements.txt" --quiet

# 3. Sync provider hooks safely using real system Python
export AGENT_MONITOR_PYTHON="$SYS_PYTHON"
if [ -f "$PREFS_FILE" ]; then
    ENABLED_CSV="$("$SYS_PYTHON" - "$PREFS_FILE" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    provs = [p for p in d.get("enabledProviders", []) if p in ("antigravity", "codex", "claude")]
    print(",".join(provs) if provs else "antigravity")
except Exception:
    print("antigravity")
PY
)"
    "$SYS_PYTHON" "$MONITOR_DIR/configure-hooks.py" sync "$ENABLED_CSV" >/dev/null
else
    "$SYS_PYTHON" "$MONITOR_DIR/configure-hooks.py" enable antigravity >/dev/null
fi

# 4. Install CLI launcher & .desktop autostart entries
cat > "$BIN_DIR/agent-monitor" <<EOF
#!/bin/sh
export AGENT_MONITOR_PYTHON="$SYS_PYTHON"
exec "$VENV_DIR/bin/python" "$DESKTOP_DIR/agent_monitor.py" "\$@"
EOF
chmod 755 "$BIN_DIR/agent-monitor"

cat > "$APPS_DIR/agent-monitor.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Agent Monitor
Comment=System tray monitor for Antigravity, Codex, and Claude Code
Exec=$BIN_DIR/agent-monitor
Icon=agent-monitor
Terminal=false
Categories=Development;Utility;
StartupNotify=false
EOF

cp "$APPS_DIR/agent-monitor.desktop" "$AUTOSTART_DIR/agent-monitor.desktop"

# 5. Launch in background if graphical session is active
if [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; then
    nohup "$BIN_DIR/agent-monitor" >"$MONITOR_DIR/app.log" 2>&1 &
fi

echo "Installed Agent Monitor for Linux!"
echo "Launcher: $BIN_DIR/agent-monitor"
echo "Autostart: $AUTOSTART_DIR/agent-monitor.desktop"
if [ "${XDG_CURRENT_DESKTOP:-}" = "GNOME" ]; then
    echo "Note: On GNOME, make sure the 'AppIndicator and KStatusNotifierItem Support' extension is enabled so tray icons are visible."
fi
