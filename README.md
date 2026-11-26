# Agent Monitor

[![Latest Release](https://img.shields.io/github/v/release/JoacoCasta/agent-monitor)](https://github.com/JoacoCasta/agent-monitor/releases/latest)
[![CI](https://img.shields.io/github/actions/workflow/status/JoacoCasta/agent-monitor/ci.yml?branch=main&label=CI)](https://github.com/JoacoCasta/agent-monitor/actions/workflows/ci.yml)
[![macOS 14+ Universal](https://img.shields.io/badge/macOS-14%2B%20Universal%20(Apple%20Silicon%20%26%20Intel)-blue)](https://github.com/JoacoCasta/agent-monitor/releases/latest)
[![SwiftUI + AppKit](https://img.shields.io/badge/built%20with-SwiftUI%20%2B%20AppKit-orange)](Sources/)
[![License: MIT](https://img.shields.io/github/license/JoacoCasta/agent-monitor)](LICENSE)

[Español](README.es.md) · [Changelog](CHANGELOG.md) · [Contributing](CONTRIBUTING.md)

A lightweight, native **macOS Menu Bar** app (Universal binary for **Apple Silicon & Intel**, macOS 14+) to track live agent status and remaining quotas across **Google Antigravity**, **ChatGPT (Codex)**, **Claude Code**, and **GitHub Copilot**.

## Screenshots

![macOS Menu Bar indicator with official Antigravity, OpenAI, and Claude logos](docs/screenshots/menubar.png)

| Dashboard | Settings |
| :---: | :---: |
| ![Agent Monitor dashboard popover](docs/screenshots/dashboard.png) | ![Agent Monitor settings popover](docs/screenshots/settings.png) |

## Download (No Terminal Required)

Download the latest Universal macOS build (`arm64` + `x86_64`) from [GitHub Releases](https://github.com/JoacoCasta/agent-monitor/releases/latest):

- **DMG Installer (`AgentMonitor-macOS.dmg`)**: Open the `.dmg`, drag **Agent Monitor** to **Applications**, and launch it.
- **ZIP Archive (`AgentMonitor-macOS.zip`)**: Unzip and move `AgentMonitor.app` to **Applications**.
- *First launch on macOS*: Because this open-source app is not Apple-notarized yet, if macOS shows an "unidentified developer" notice, **Right-click (or Control-click) `AgentMonitor.app` → Open** once.

`AgentMonitor.app` is **self-contained**: on first launch it stages its bundled helper scripts, shows an initial agent chooser, lets you toggle **Start at login** in **Settings**, and configures provider hooks safely with zero terminal setup.

## Features

- **Native Retina Menu Bar indicator**: Renders each enabled agent's official monochrome vector logo at crisp 2x Retina resolution alongside a live traffic-light dot and lowest remaining quota percentage, automatically adapting between dark and light macOS Menu Bars with near-zero (`~0.0%`) idle CPU usage.
- **Live traffic-light state**:
  - **Yellow**: Agent is blocked waiting for explicit user input (questions, permissions, elicitation, or plan approval).
  - **Red**: Agent is actively thinking, running tools, or executing background tasks.
  - **Green**: Agent is idle.
- **Multi-window quota tracking**: Shows 5-hour rolling windows, weekly/monthly limits, color-coded progress bars, low-quota warnings (`< 20%`), and live reset countdowns.
- **Provider selection & safe hook management**: Pick which agents to monitor on first launch or anytime in **Settings**. Enabling or disabling a provider safely merges or removes only its monitor hooks while preserving existing configs (including Codex `notify` and any pre-existing Claude Code `statusLine`).
- **Native macOS notifications**: Alerts via `UserNotifications` when an agent waits for your input or when any quota drops below `20%`. Clicking a notification brings that agent's app to focus.
- **7 built-in languages**: Automatic macOS language detection plus manual switcher for **English**, **Español**, **Português**, **Français**, **Deutsch**, **简体中文**, and **日本語**.

## Supported Providers

| Provider | Official Logo | Quota Source | Live Status Source |
| :--- | :--- | :--- | :--- |
| **Google Antigravity** | Antigravity mark | `agy` CLI `statusLine` (`gemini` & `3p` 5h/weekly) | `~/.gemini/config/hooks.json` |
| **ChatGPT (Codex)** | OpenAI mark | `codex app-server` JSON-RPC (`account/rateLimits/read`) | `~/.codex/hooks.json` |
| **Claude Code** | Claude mark | `~/.claude/settings.json` `statusLine` (`rate_limits`) | `~/.claude/settings.json` hooks |
| **GitHub Copilot** | Copilot Octicon mark | `copilot --headless --stdio` JSON-RPC (`account.getQuota`) | `~/.copilot/hooks/agent-monitor.json` |

## Build / Install from Source (Optional)

Requires **macOS 14.0+** and **Xcode Command Line Tools** (`xcode-select --install`; full Xcode is not required):

```bash
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
./install.sh
```

`./install.sh` builds `/Applications/AgentMonitor.app`, stages helper scripts under `~/.gemini/agent-monitor/`, syncs enabled provider hooks, and installs/starts the LaunchAgent (`com.agentmonitor.app`).

**Uninstall:** `./uninstall.sh`

## FAQ & Troubleshooting

- **macOS says `"AgentMonitor.app" cannot be opened because it is from an unidentified developer`**:
  Open **Finder → Applications**, **Right-click (or Control-click) `AgentMonitor.app` → Open**, and confirm **Open**. This is only required on first launch.
- **Codex CLI asks to approve or review hooks in `~/.codex/hooks.json`**:
  Run `/hooks` once inside Codex CLI to trust the newly added Agent Monitor hooks. Existing `notify` hooks are preserved.
- **Claude Code already uses a custom `statusLine`**:
  Agent Monitor automatically wraps and chains your previous `statusLine` command so both continue working, and restores your original command cleanly if you disable Claude Code or uninstall. Quota updates (`five_hour` and `seven_day`) appear during active Claude Code sessions.
- **Menu Bar item is hidden behind the MacBook notch**:
  Hold `⌘` (Command) and drag the Agent Monitor menu bar item closer to the right side, or hide unused menu bar icons.

## Privacy & Official Interfaces Only

Agent Monitor reads no private credentials or undocumented internal databases. It relies strictly on documented CLI/hook interfaces (`agy --settings`, `codex app-server`, `copilot --headless --stdio`, and official `hooks` / `statusLine` contracts) and stores state locally under `~/.gemini/agent-monitor/`.

## License

MIT — see [LICENSE](LICENSE).
