# Contributing to Agent Monitor

Thank you for helping improve **Agent Monitor**! Agent Monitor is a native **macOS 14.0+ Menu Bar** application built with SwiftUI, AppKit, and Python helper scripts.

## Repository Layout

- `Sources/` — Native macOS SwiftUI + AppKit application (`swiftc`, macOS 14.0+, Apple Silicon & Intel)
- `Resources/` — macOS `Info.plist` and `AppIcon.icns`
- `Scripts/` — Bundled Python 3 helper scripts (`hook-handler.py`, `fetch-quota.py`, `claude-statusline.py`, `configure-hooks.py`)
- `assets/logos/` — Official monochrome 24x24 SVG provider logos
- `docs/screenshots/` — Showcase screenshots used in READMEs
- `tests/` — macOS unit tests (`tests/test_macos_monitor.py`)
- `build.sh`, `install.sh`, `uninstall.sh` — Local build, LaunchAgent install, and clean uninstall scripts

## Development Setup (macOS 14.0+)

Full Xcode is **not** required; Agent Monitor builds directly with **Xcode Command Line Tools** (`swiftc`):

```bash
./build.sh
# Or build, stage helper scripts, sync hooks, and start the LaunchAgent:
./install.sh
```

Verify the signed bundle after building:

```bash
codesign --verify --deep --strict /Applications/AgentMonitor.app
```

To build a Universal (`arm64` + `x86_64`) binary matching CI/Release:

```bash
swiftc -swift-version 5 -O -target arm64-apple-macosx14.0 -framework AppKit -framework SwiftUI -framework UserNotifications -framework Combine Sources/*.swift -o /tmp/AgentMonitor-arm64
swiftc -swift-version 5 -O -target x86_64-apple-macosx14.0 -framework AppKit -framework SwiftUI -framework UserNotifications -framework Combine Sources/*.swift -o /tmp/AgentMonitor-x86_64
lipo -create /tmp/AgentMonitor-arm64 /tmp/AgentMonitor-x86_64 -output /tmp/AgentMonitor-universal
lipo -info /tmp/AgentMonitor-universal
```

> [!IMPORTANT]
> **CommandLineTools Swift Rule (`Sources/*.swift`)**
> Because Agent Monitor compiles directly with `/usr/bin/swiftc` from Xcode Command Line Tools (without SwiftPM or Xcode macro plugins), **NEVER use `@State`, `@Observable`, or SwiftUI macros in `Sources/*.swift`**. Use `ObservableObject` (`@ObservedObject` / `@Published`) and AppKit/Combine patterns already used across `Sources/`.

## Running Tests & Checks

Before pushing, run all Python, shell, Swift, and codesign checks:

```bash
python3 -m py_compile Scripts/*.py
python3 -m unittest discover -s tests -v
bash -n build.sh install.sh uninstall.sh
./build.sh
codesign --verify --deep --strict /Applications/AgentMonitor.app
```

## Guidelines & Privacy

- **Official interfaces only**: Never read private credentials or undocumented databases. Use only documented CLI/hook/statusLine contracts (`agy --settings`, `codex app-server`, and official `hooks` / `statusLine` JSON schemas).
- **Preserve user configs**: Hook installation/removal in `Scripts/configure-hooks.py` must merge safely without overwriting existing user hooks, Codex `notify`, or pre-existing Claude Code `statusLine` commands.
- **Zero idle CPU impact**: Keep Menu Bar bitmap caching and render deduplication intact so idle CPU usage stays near `0.0%`.
- **No personal data**: Keep screenshots, fixtures, and commits free of personal emails, usernames, tokens, or private paths.
- **Keep docs in sync**: If you update user-facing features or setup instructions, update both `README.md` and `README.es.md`, and add an entry to `CHANGELOG.md` when appropriate.

## Pull Request Checklist

- [ ] `./build.sh` compiles with zero errors and `codesign --verify --deep --strict /Applications/AgentMonitor.app` passes.
- [ ] `python3 -m py_compile Scripts/*.py` and `python3 -m unittest discover -s tests -v` pass with zero failures.
- [ ] `bash -n build.sh install.sh uninstall.sh` passes.
- [ ] No `@State`, `@Observable`, or SwiftUI macros added in `Sources/*.swift`.
- [ ] `README.md` and `README.es.md` updated in sync if user-facing behavior changed.
- [ ] No personal data, local paths, or secrets included in diffs or screenshots.
