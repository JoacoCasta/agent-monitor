#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="AgentMonitor.app"

if [ -w "/Applications" ]; then
    INSTALL_APP_DIR="/Applications/$APP_NAME"
else
    mkdir -p "$HOME/Applications"
    INSTALL_APP_DIR="$HOME/Applications/$APP_NAME"
fi

CONTENTS_DIR="$INSTALL_APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"
BUNDLED_SCRIPTS_DIR="$RESOURCES_DIR/Scripts"

mkdir -p "$MACOS_DIR" "$RESOURCES_DIR" "$BUNDLED_SCRIPTS_DIR"

/usr/bin/swiftc \
    -swift-version 5 \
    -O \
    -framework AppKit \
    -framework SwiftUI \
    -framework UserNotifications \
    -framework Combine \
    "$SCRIPT_DIR"/Sources/*.swift \
    -o "$MACOS_DIR/AgentMonitor"

cp "$SCRIPT_DIR/Resources/Info.plist" "$CONTENTS_DIR/Info.plist"
cp "$SCRIPT_DIR/Resources/AppIcon.icns" "$RESOURCES_DIR/AppIcon.icns"
cp "$SCRIPT_DIR"/Scripts/*.py "$BUNDLED_SCRIPTS_DIR/"
chmod 755 "$BUNDLED_SCRIPTS_DIR"/*.py

codesign --force --deep --sign - "$INSTALL_APP_DIR"

echo "$INSTALL_APP_DIR"
