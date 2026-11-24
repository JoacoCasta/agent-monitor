# Contributing to Agent Monitor

Thank you for helping improve **Agent Monitor**! Please read the platform setup, coding rules, and verification steps below before opening a pull request.

## Repository Layout

- `Sources/` — macOS SwiftUI + AppKit application (`swiftc`, macOS 14.0+)
- `Resources/` — macOS `Info.plist` and `AppIcon.icns`
- `desktop/` — Windows & Linux Python + PySide6 (Qt6) tray application (`agent_monitor.py`, `core.py`, `i18n.py`)
- `Scripts/` — Shared Python helper scripts (`hook-handler.py`, `fetch-quota.py`, `claude-statusline.py`, `configure-hooks.py`)
- `assets/logos/` — Official monochrome 24x24 SVG provider logos
- `windows/` & `linux/` — Platform install/uninstall scripts, packaging assets, and icons
- `tests/` — Cross-platform unit tests (`unittest`)

## Development Setup

### macOS (14.0+, Xcode Command Line Tools)

Full Xcode is **not** required; the app builds directly with Command Line Tools (`swiftc`):

```bash
./build.sh
# Or build and install with LaunchAgent + hook sync:
./install.sh
```

Verify the signed bundle after building:

```bash
codesign --verify --deep --strict /Applications/AgentMonitor.app
```

> [!IMPORTANT]
> **CommandLineTools Swift Rule (`Sources/*.swift`)**
> Because Agent Monitor compiles with `/usr/bin/swiftc` from Xcode Command Line Tools (without SwiftPM/Xcode macro plugins), **NEVER use `@State`, `@Observable`, or SwiftUI macros in `Sources/*.swift`**. Use `ObservableObject` (`@ObservedObject` / `@Published`) and AppKit/Combine patterns already used across `Sources/`.

### Windows (10/11, Python 3.9+)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r desktop\requirements.txt
python desktop\agent_monitor.py
```

Or test the full local install:

```powershell
powershell -ExecutionPolicy Bypass -File .\windows\install.ps1
```

### Linux (X11 / Wayland, Python 3.9+)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r desktop/requirements.txt
python3 desktop/agent_monitor.py
```

On headless CI or machines without a display server, test Qt imports offscreen:

```bash
QT_QPA_PLATFORM=offscreen python3 -c "import PySide6.QtWidgets, desktop.agent_monitor"
```

## Running Tests & Checks

Before pushing, run the Python syntax checks and full `unittest` suite:

```bash
python3 -m py_compile Scripts/hook-handler.py Scripts/fetch-quota.py Scripts/claude-statusline.py Scripts/configure-hooks.py desktop/i18n.py desktop/core.py desktop/agent_monitor.py tests/test_cross_platform.py
python3 -m unittest discover -s tests -v
python3 desktop/agent_monitor.py --status-json
```

On macOS, also run `./build.sh` and `codesign --verify --deep --strict /Applications/AgentMonitor.app`.

## Guidelines & Privacy

- **Official interfaces only**: Never read private credentials or undocumented databases. Use only documented CLI/hook/statusLine contracts.
- **Preserve user configs**: Hook installation/removal in `Scripts/configure-hooks.py` must merge safely without overwriting existing user hooks, Codex `notify`, or pre-existing Claude Code `statusLine` commands.
- **No personal data**: Keep screenshots, fixtures, and commits free of personal emails, usernames, tokens, or private paths.
- **Keep docs in sync**: If you update user-facing features or setup instructions, update both `README.md` and `README.es.md`, and add an entry to `CHANGELOG.md` if appropriate.

## Pull Request Checklist

- [ ] Code compiles cleanly on target platform(s) (`./build.sh` on macOS; `py_compile` + PySide6 check on Windows/Linux).
- [ ] `python3 -m unittest discover -s tests -v` passes with zero failures.
- [ ] No `@State`, `@Observable`, or SwiftUI macros added in `Sources/*.swift`.
- [ ] `--status-json` backwards compatibility (`tag`, `displayName`, `status`, `percent`, `activeSessions`, `quota`) is preserved.
- [ ] `README.md` and `README.es.md` updated in sync if user-facing behavior changed.
- [ ] No personal data, local paths, or secrets included in diffs or screenshots.
