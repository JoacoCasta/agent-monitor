# Agent Monitor

[Español](README.es.md)

A lightweight, native system-tray / menu-bar monitor for **macOS**, **Windows**, and **Linux** to track live agent status and remaining quotas across **Google Antigravity**, **ChatGPT (Codex)**, and **Claude Code**.

## Features

- **Compact tray / menu-bar indicator**:
  - **macOS (SwiftUI + AppKit)**: Shows each selected agent with a live traffic-light dot and lowest remaining quota percentage (e.g., `AG ● 80%  CX ● 100%  CC ● 74%`).
  - **Windows & Linux (Python + PySide6 / Qt6)**: Dynamic multi-dot tray icon reflecting each selected agent's live status, low-quota alert badge (`< 20%`), hover summary tooltip, and interactive popup panel.
- **Live traffic-light state**:
  - **Yellow**: Agent is blocked waiting for explicit user input (questions, permissions, elicitation, or plan approval).
  - **Red**: Agent is actively thinking, running tools, or executing background tasks.
  - **Green**: Agent is idle.
- **Multi-window quota tracking**: Shows 5-hour rolling windows, weekly/monthly limits, color-coded progress bars, low-quota warnings (`< 20%`), and live reset countdowns.
- **Provider selection & safe hook management**: Pick which agents to monitor on first launch or anytime in **Settings**. Enabling or disabling a provider safely merges or removes only its monitor hooks while preserving existing configs (including Codex `notify` and any pre-existing Claude Code `statusLine`).
- **Native desktop notifications**: Alerts when an agent waits for your input or when any quota drops below `20%`. Clicking a notification focuses that agent's app.
- **7 built-in languages**: Automatic OS language detection plus manual switcher for **English**, **Español**, **Português**, **Français**, **Deutsch**, **简体中文**, and **日本語**.

## Supported Providers

| Provider | Tag | Quota Source | Live Status Source |
| :--- | :--- | :--- | :--- |
| **Antigravity** | `AG` | `agy` CLI `statusLine` (`gemini` & `3p` 5h/weekly) | `~/.gemini/config/hooks.json` |
| **ChatGPT (Codex)** | `CX` | `codex app-server` JSON-RPC (`account/rateLimits/read`) | `~/.codex/hooks.json` |
| **Claude Code** | `CC` | `~/.claude/settings.json` `statusLine` (`rate_limits`) | `~/.claude/settings.json` hooks |

### Provider Notes

- **Codex**: If Codex CLI asks you to review newly added hooks in `~/.codex/hooks.json`, run `/hooks` once inside Codex to trust them.
- **Claude Code**: Claude Code delivers `rate_limits` (`five_hour` and `seven_day`) through its official `statusLine` during active sessions. Your previous `statusLine` command (if any) is preserved and chained automatically, and restored on disable/uninstall.

## Installation

Prebuilt archives for **macOS**, **Windows**, and **Linux** are also built via GitHub Actions on tagged releases (`Releases` tab).

### macOS (14.0+, Xcode Command Line Tools)

```bash
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
./install.sh
```

Builds `/Applications/AgentMonitor.app`, installs helper scripts in `~/.gemini/agent-monitor`, and registers a `LaunchAgent` (`com.agentmonitor.app`).

**Uninstall:** `./uninstall.sh`

### Windows (10/11, Python 3.9+)

```powershell
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
powershell -ExecutionPolicy Bypass -File .\windows\install.ps1
```

Creates an isolated virtual environment with `PySide6` under `%USERPROFILE%\.gemini\agent-monitor\venv`, configures hooks, adds Startup & Start Menu shortcuts using `pythonw.exe` (no console window), and starts in the system tray.

**Uninstall:** `powershell -ExecutionPolicy Bypass -File .\windows\uninstall.ps1`

### Linux (X11 / Wayland, Python 3.9+)

```bash
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
./linux/install.sh
```

Installs into `~/.gemini/agent-monitor/venv` with `PySide6`, adds `~/.local/bin/agent-monitor`, registers autostart at `~/.config/autostart/agent-monitor.desktop`, and starts in the background.

- **GNOME users**: Enable the *AppIndicator and KStatusNotifierItem Support* extension so tray icons appear in the top bar.
- **Waybar / Polybar / scripts**: Run `agent-monitor --status-json` to get live JSON with each enabled provider's status, percentage, and quotas.

**Uninstall:** `./linux/uninstall.sh`

## Privacy & Official Interfaces Only

Agent Monitor reads no private credentials or undocumented internal databases. It relies strictly on documented CLI/hook interfaces (`agy --settings`, `codex app-server`, and official `hooks` / `statusLine` contracts) and stores state locally under `~/.gemini/agent-monitor/`.

## License

MIT — see [LICENSE](LICENSE).
