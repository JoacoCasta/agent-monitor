# Changelog

All notable changes to **Agent Monitor** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.1] - 2026-11-24

### Fixed
- **macOS Menu Bar 96% CPU redraw loop**: Removed the re-entrant `NSStatusBarButton.effectiveAppearance` KVO observer that triggered AppKit's `NSStatusItem` replicant redraw loop on every frame, replacing it with system theme/space change notifications and `StatusBarRenderKey` equality guards.
- **Bitmap caching**: Pre-rasterized 2x Retina bitmaps for provider logos (`Sources/ProviderLogo.swift`) and status dots (`Sources/AppDelegate.swift`) instead of re-invoking CoreGraphics drawing closures on every repaint.
- **Adaptive idle timers**: Switched `Sources/StateStore.swift` and `desktop/agent_monitor.py` (Windows/Linux) to 15s coalesced background ticks when the popup is closed (1s only while open), added `Equatable` / tray-key guards to prevent redundant UI updates, and skipped hidden SwiftUI countdown churn.

## [2.3.0] - 2026-11-24

### Added
- **Official monochrome agent logos**: Normalized 24x24 vector brand marks (`assets/logos/antigravity.svg`, `assets/logos/codex.svg`, `assets/logos/claude.svg`) rendered 1:1 on macOS (`Sources/ProviderLogo.swift`) and Windows/Linux (`desktop/agent_monitor.py`).
- **Custom application icons**: Dedicated macOS bundle icon (`Resources/AppIcon.icns`), Windows installer/executable icon (`windows/icon.ico`), and Linux desktop/tray icon (`linux/agent-monitor.png`).
- **Project documentation & GitHub templates**: Added `CHANGELOG.md`, `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, and `.github/PULL_REQUEST_TEMPLATE.md`.
- **Polished READMEs**: Added shields.io status badges, live macOS screenshots, updated provider documentation, and a cross-platform FAQ / Troubleshooting section in both `README.md` and `README.es.md`.

### Changed
- Improved macOS Menu Bar contrast (pure white on dark menu bars, pure black on light menu bars) and logo sizing/alignment across the menu bar and popover cards.
- Updated cross-platform tests to validate official SVG logo assets and desktop rendering helpers.

## [2.2.0] - 2026-11-24

### Changed
- Replaced two-letter UI provider tags (`AG`, `CX`, `CC`) with scalable monochrome vector logos in the macOS Menu Bar/popover (`Sources/ProviderLogo.swift`) and Windows/Linux popup (`desktop/agent_monitor.py`).
- Preserved `short_tag` (`AG`, `CX`, `CC`) in `desktop/core.py` for `--status-json` backwards compatibility.

## [2.1.1] - 2026-11-24

### Fixed
- Fixed macOS menu bar label contrast across light and dark appearances.
- Fixed macOS popover layout spacing and reliable reopen behavior when clicking the status item.

## [2.1.0] - 2026-11-24

### Added
- Zero-terminal release installers: `AgentMonitor-macOS.dmg` / `.zip`, `AgentMonitor-Windows-Setup.exe` (Inno Setup via `windows/installer.iss`) / Portable ZIP, and `AgentMonitor-Linux-x64.deb` / `.tar.gz`.
- First-launch self-contained runtime script staging (`Sources/RuntimeSetup.swift` and `desktop/core.py`).
- **Start at Login** toggle in Settings across macOS, Windows, and Linux.

### Fixed
- Fixed macOS popover layout sizing and dynamic height adaptation for enabled providers.

## [2.0.0] - 2026-11-24

### Added
- **Windows and Linux support**: Added the PySide6 (Qt6) desktop tray application (`desktop/agent_monitor.py`, `desktop/core.py`, `desktop/i18n.py`) with dynamic multi-dot tray icons, low-quota alert badges, interactive popup, and 7-language localization.
- **`--status-json` CLI output**: Machine-readable live status, percentages, and quota windows for Waybar, Polybar, and custom scripts.
- **Native installers & CI/CD**: Added `windows/install.ps1`, `windows/uninstall.ps1`, `linux/install.sh`, `linux/uninstall.sh`, unit tests (`tests/test_cross_platform.py`), and GitHub Actions CI & Release workflows (`.github/workflows/ci.yml`, `.github/workflows/release.yml`).
- Built on the initial macOS release (`Sources/*.swift` + `Scripts/*.py`) supporting live traffic-light agent status, multi-window quota tracking, safe hook merging, and desktop notifications for Google Antigravity, ChatGPT (Codex), and Claude Code.
