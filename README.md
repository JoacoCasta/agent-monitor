# Agent Monitor

[Español](README.es.md)

A lightweight, native macOS Menu Bar app built with SwiftUI and AppKit to monitor live agent status and remaining quotas across **Google Antigravity**, **ChatGPT (Codex)**, and **Claude Code**.

## Features

- **Compact Menu Bar strip**: Displays only the agents you enable, each with its own live traffic-light dot and lowest remaining quota percentage (e.g., `AG ● 80%  CX ● 100%  CC ● 74%`).
- **Live traffic-light state**:
  - **Yellow**: Agent is blocked waiting for explicit user input (questions, permissions, elicitation, or plan approval).
  - **Red**: Agent is actively thinking, running tools, or executing background tasks.
  - **Green**: Agent is idle.
- **Multi-window quota tracking**: Shows 5-hour rolling windows, weekly/monthly limits, color-coded progress bars, low-quota warnings (`< 20%`), and live reset countdowns.
- **Provider selection & safe hook management**: Pick which agents to monitor on first launch or anytime in **Settings**. Enabling or disabling a provider safely merges or removes only its monitor hooks while preserving existing configs (including Codex `notify` and any pre-existing Claude Code `statusLine`).
- **Native macOS notifications**: Optional desktop banners when an agent waits for your input or when any quota drops below `20%`. Clicking a notification focuses that agent's app.
- **7 built-in languages**: Automatic macOS language detection plus manual switcher for **English**, **Español**, **Português**, **Français**, **Deutsch**, **简体中文**, and **日本語**.

## Supported Providers

| Provider | Tag | Quota Source | Live Status Source |
| :--- | :--- | :--- | :--- |
| **Antigravity** | `AG` | `agy` CLI `statusLine` (`gemini` & `3p` 5h/weekly) | `~/.gemini/config/hooks.json` |
| **ChatGPT (Codex)** | `CX` | `codex app-server` JSON-RPC (`account/rateLimits/read`) | `~/.codex/hooks.json` |
| **Claude Code** | `CC` | `~/.claude/settings.json` `statusLine` (`rate_limits`) | `~/.claude/settings.json` hooks |

### Provider Notes

- **Codex**: If Codex CLI asks you to review newly added hooks in `~/.codex/hooks.json`, run `/hooks` once inside Codex to trust them.
- **Claude Code**: Claude Code delivers `rate_limits` (`five_hour` and `seven_day`) through its official `statusLine` during active sessions. Your previous `statusLine` command (if any) is preserved and chained automatically, and restored on disable/uninstall.

## Requirements

- macOS 14.0 or later
- Xcode Command Line Tools (`xcode-select --install`) for `swiftc` and `/usr/bin/python3`

## Installation

```bash
git clone https://github.com/JoacoCasta/agent-monitor.git
cd agent-monitor
./install.sh
```

This compiles `/Applications/AgentMonitor.app` (or `~/Applications/AgentMonitor.app` if `/Applications` is not writable), installs helper scripts into `~/.gemini/agent-monitor`, configures a `LaunchAgent` (`com.agentmonitor.app`), and opens the initial provider chooser in your menu bar.

## Uninstallation

```bash
./uninstall.sh
```

Cleanly removes the app bundle, `LaunchAgent`, helper scripts, and all monitor hooks (restoring any previously configured Claude Code `statusLine`).

## Privacy & Official Interfaces Only

Agent Monitor reads no private credentials or undocumented internal databases. It relies strictly on documented CLI/hook interfaces (`agy --settings`, `codex app-server`, and official `hooks` / `statusLine` contracts) and stores state locally under `~/.gemini/agent-monitor/`.

## License

MIT — see [LICENSE](LICENSE).
