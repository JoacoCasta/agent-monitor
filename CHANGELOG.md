# Changelog

All notable changes to **Agent Monitor** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-11-24

### Added
- **Toggleable Antigravity 3P Models**: Added a switch inside the Antigravity card in **Settings** (`Show 3P Models (Claude / GPT)` in all 7 languages) persisted via `showAntigravity3PModels` in `~/.gemini/agent-monitor/preferences.json`. Disabling it hides the 3P Models section on the Dashboard, shrinks the popover height cleanly, ignores 3P buckets for Menu Bar percentages, and suppresses low-quota notifications for 3P models.

## [3.0.0] - 2026-11-24

### Added
- **Universal macOS binary (`arm64` + `x86_64`)**: CI and Release workflows now compile and `lipo` both Apple Silicon and Intel slices for macOS 14.0+, shipping `AgentMonitor-macOS.dmg` and `AgentMonitor-macOS.zip`.
- **Dedicated macOS unit test suite**: Replaced cross-platform desktop tests with `tests/test_macos_monitor.py` covering `Scripts/*.py`, SVG logo 1:1 parity with `Sources/ProviderLogo.swift`, `Resources/Info.plist`, `Resources/AppIcon.icns`, and Swift CommandLineTools compliance.

### Changed
- **Refocused project exclusively on native macOS**: Removed the experimental Python/PySide6 desktop tray implementation (`desktop/`, `windows/`, `linux/`) to keep the codebase lean, native SwiftUI + AppKit, and focused on macOS 14+.
- **Full-size Retina 2x Menu Bar rendering**: Fixed `NSGraphicsContext` initialization order in `Sources/ProviderLogo.swift` (`menuBarImage`) and `Sources/AppDelegate.swift` (`statusDotImage`) so `rep.size` is set prior to creating the graphics context, rendering crisp full-size 14.5pt logos and 8.5pt status dots at `~0.0%` idle CPU.
- **Polished macOS-only CI, Release, docs, and GitHub templates**: Updated `.github/workflows/ci.yml`, `.github/workflows/release.yml`, `README.md`, `README.es.md`, `CONTRIBUTING.md`, and issue/PR templates exclusively for macOS.

## [2.3.0] - 2026-11-24

### Added
- **Official monochrome agent logos**: Normalized 24x24 vector brand marks (`assets/logos/antigravity.svg`, `assets/logos/codex.svg`, `assets/logos/claude.svg`) rendered 1:1 in `Sources/ProviderLogo.swift`.
- **Custom application icon**: Added `Resources/AppIcon.icns` (`CFBundleIconFile=AppIcon`) and bundled it into `AgentMonitor.app`.
- **Project documentation & GitHub templates**: Added `CHANGELOG.md`, `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md`, and `.github/PULL_REQUEST_TEMPLATE.md`.

### Changed
- Improved macOS Menu Bar contrast (pure white on dark menu bars, pure black on light menu bars) and logo sizing/alignment across the menu bar and popover cards.

## [2.2.0] - 2026-11-24

### Changed
- Replaced two-letter UI provider tags (`AG`, `CX`, `CC`) with scalable monochrome vector logos in the macOS Menu Bar and popover (`Sources/ProviderLogo.swift`).

## [2.1.1] - 2026-11-24

### Fixed
- Fixed macOS menu bar label contrast across light and dark appearances.
- Fixed macOS popover layout spacing and reliable reopen behavior when clicking the status item.

## [2.1.0] - 2026-11-24

### Added
- Zero-terminal macOS release installers (`AgentMonitor-macOS.dmg` and `AgentMonitor-macOS.zip`).
- First-launch self-contained runtime script staging (`Sources/RuntimeSetup.swift`).
- **Start at login** toggle in Settings.

### Fixed
- Fixed macOS popover layout sizing and dynamic height adaptation for enabled providers.

## [2.0.0] - 2026-11-24

### Added
- Automated GitHub Actions CI & Release workflows, expanded multi-provider hook/quota support, and unit test coverage building on the initial macOS SwiftUI + AppKit release (`Sources/*.swift` + `Scripts/*.py`).
