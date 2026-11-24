#!/usr/bin/python3
import argparse
import json
import os
import shutil
import sys
import tempfile

MONITOR_DIR = os.path.expanduser("~/.gemini/agent-monitor")
HOOK_HANDLER_PATH = os.path.join(MONITOR_DIR, "hook-handler.py")
CLAUDE_STATUSLINE_PATH = os.path.join(MONITOR_DIR, "claude-statusline.py")
CLAUDE_PREV_STATUSLINE_PATH = os.path.join(MONITOR_DIR, "claude-prev-statusline.json")

ANTIGRAVITY_HOOKS_PATH = os.path.expanduser("~/.gemini/config/hooks.json")
CODEX_HOOKS_PATH = os.path.expanduser("~/.codex/hooks.json")
CLAUDE_SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")

MONITOR_MARKERS = (
    "agent-monitor/hook-handler.py",
    "antigravity-monitor/hook-handler.py",
)

PROVIDERS = ("antigravity", "codex", "claude")


def read_json_dict(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    if isinstance(loaded, dict):
        return loaded
    return {}


def write_json_atomic(path, data):
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".cfg-", suffix=".json", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tf:
            json.dump(data, tf, indent=2, ensure_ascii=False)
            tf.write("\n")
        os.replace(tmp_path, path)
    except Exception:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass
        raise


def is_monitor_hook_group(group):
    if not isinstance(group, dict):
        return False
    hooks_list = group.get("hooks")
    if not isinstance(hooks_list, list):
        return False
    for h in hooks_list:
        if isinstance(h, dict):
            cmd = str(h.get("command") or "")
            if any(m in cmd for m in MONITOR_MARKERS):
                return True
    return False


def strip_monitor_groups(events_dict):
    if not isinstance(events_dict, dict):
        return {}
    cleaned = {}
    for ev_name, groups in events_dict.items():
        if not isinstance(groups, list):
            cleaned[ev_name] = groups
            continue
        kept = [g for g in groups if not is_monitor_hook_group(g)]
        if kept:
            cleaned[ev_name] = kept
    return cleaned


def has_monitor_groups(events_dict):
    if not isinstance(events_dict, dict):
        return False
    for groups in events_dict.values():
        if isinstance(groups, list) and any(is_monitor_hook_group(g) for g in groups):
            return True
    return False


# --- Antigravity ---

def enable_antigravity():
    data = read_json_dict(ANTIGRAVITY_HOOKS_PATH)
    data.pop("antigravity-monitor", None)

    def cmd(event):
        return {
            "type": "command",
            "command": "/usr/bin/python3 {} antigravity {}".format(HOOK_HANDLER_PATH, event),
            "timeout": 5,
        }

    data["agent-monitor"] = {
        "enabled": True,
        "SessionStart": [cmd("SessionStart")],
        "PreInvocation": [cmd("PreInvocation")],
        "PostInvocation": [cmd("PostInvocation")],
        "PreToolUse": [{"matcher": "*", "hooks": [cmd("PreToolUse")]}],
        "PostToolUse": [{"matcher": "*", "hooks": [cmd("PostToolUse")]}],
        "Stop": [cmd("Stop")],
    }
    write_json_atomic(ANTIGRAVITY_HOOKS_PATH, data)


def disable_antigravity():
    if not os.path.exists(ANTIGRAVITY_HOOKS_PATH):
        return
    data = read_json_dict(ANTIGRAVITY_HOOKS_PATH)
    changed = False
    for key in ("agent-monitor", "antigravity-monitor"):
        if key in data:
            del data[key]
            changed = True
    if not changed:
        return
    if data:
        write_json_atomic(ANTIGRAVITY_HOOKS_PATH, data)
    else:
        os.remove(ANTIGRAVITY_HOOKS_PATH)


def is_antigravity_installed():
    if not os.path.exists(ANTIGRAVITY_HOOKS_PATH):
        return False
    try:
        data = read_json_dict(ANTIGRAVITY_HOOKS_PATH)
        entry = data.get("agent-monitor")
        return isinstance(entry, dict) and entry.get("enabled", True) is True
    except Exception:
        return False


# --- Codex ---

def enable_codex():
    os.makedirs(os.path.dirname(CODEX_HOOKS_PATH), exist_ok=True)
    data = read_json_dict(CODEX_HOOKS_PATH)
    hooks = strip_monitor_groups(data.get("hooks"))

    def group(event, matcher=None):
        entry = {
            "hooks": [
                {
                    "type": "command",
                    "command": "/usr/bin/python3 {} codex {}".format(HOOK_HANDLER_PATH, event),
                    "timeout": 5,
                }
            ]
        }
        if matcher is not None:
            entry["matcher"] = matcher
        return entry

    codex_events = [
        ("SessionStart", None),
        ("UserPromptSubmit", None),
        ("PreModelRequest", None),
        ("PostModelRequest", None),
        ("PreToolUse", ".*"),
        ("PermissionRequest", ".*"),
        ("PostToolUse", ".*"),
        ("Interrupt", None),
        ("Stop", None),
        ("SessionEnd", None),
    ]

    for ev_name, matcher in codex_events:
        arr = hooks.get(ev_name)
        if not isinstance(arr, list):
            arr = []
        arr.append(group(ev_name, matcher))
        hooks[ev_name] = arr

    data["hooks"] = hooks
    write_json_atomic(CODEX_HOOKS_PATH, data)


def disable_codex():
    if not os.path.exists(CODEX_HOOKS_PATH):
        return
    data = read_json_dict(CODEX_HOOKS_PATH)
    hooks = strip_monitor_groups(data.get("hooks"))
    if hooks:
        data["hooks"] = hooks
        write_json_atomic(CODEX_HOOKS_PATH, data)
    else:
        data.pop("hooks", None)
        remaining = {k: v for k, v in data.items() if k != "description"}
        if remaining:
            write_json_atomic(CODEX_HOOKS_PATH, data)
        else:
            os.remove(CODEX_HOOKS_PATH)


def is_codex_installed():
    if not os.path.exists(CODEX_HOOKS_PATH):
        return False
    try:
        data = read_json_dict(CODEX_HOOKS_PATH)
        return has_monitor_groups(data.get("hooks"))
    except Exception:
        return False


# --- Claude Code ---

def enable_claude():
    os.makedirs(os.path.dirname(CLAUDE_SETTINGS_PATH), exist_ok=True)
    os.makedirs(MONITOR_DIR, exist_ok=True)
    data = read_json_dict(CLAUDE_SETTINGS_PATH)
    hooks = strip_monitor_groups(data.get("hooks"))

    def group(event, matcher=None):
        entry = {
            "hooks": [
                {
                    "type": "command",
                    "command": "/usr/bin/python3 {} claude {}".format(HOOK_HANDLER_PATH, event),
                    "timeout": 5,
                }
            ]
        }
        if matcher is not None:
            entry["matcher"] = matcher
        return entry

    claude_events = [
        ("SessionStart", None),
        ("UserPromptSubmit", None),
        ("PreToolUse", ".*"),
        ("PermissionRequest", ".*"),
        ("Notification", "permission_prompt|elicitation_dialog"),
        ("Elicitation", None),
        ("ElicitationResult", None),
        ("PostToolUse", ".*"),
        ("PostToolUseFailure", ".*"),
        ("Stop", None),
        ("StopFailure", None),
        ("SessionEnd", None),
    ]

    for ev_name, matcher in claude_events:
        arr = hooks.get(ev_name)
        if not isinstance(arr, list):
            arr = []
        arr.append(group(ev_name, matcher))
        hooks[ev_name] = arr

    data["hooks"] = hooks

    existing_sl = data.get("statusLine")
    if (
        isinstance(existing_sl, dict)
        and "claude-statusline.py" not in str(existing_sl.get("command") or "")
        and not os.path.exists(CLAUDE_PREV_STATUSLINE_PATH)
    ):
        write_json_atomic(CLAUDE_PREV_STATUSLINE_PATH, existing_sl)

    data["statusLine"] = {
        "type": "command",
        "command": "/usr/bin/python3 {}".format(CLAUDE_STATUSLINE_PATH),
    }

    write_json_atomic(CLAUDE_SETTINGS_PATH, data)


def disable_claude():
    if os.path.exists(CLAUDE_SETTINGS_PATH):
        data = read_json_dict(CLAUDE_SETTINGS_PATH)
        hooks = strip_monitor_groups(data.get("hooks"))
        if hooks:
            data["hooks"] = hooks
        else:
            data.pop("hooks", None)

        sl = data.get("statusLine")
        if isinstance(sl, dict) and "claude-statusline.py" in str(sl.get("command") or ""):
            if os.path.exists(CLAUDE_PREV_STATUSLINE_PATH):
                try:
                    prev = read_json_dict(CLAUDE_PREV_STATUSLINE_PATH)
                    if prev:
                        data["statusLine"] = prev
                    else:
                        data.pop("statusLine", None)
                except Exception:
                    data.pop("statusLine", None)
                try:
                    os.remove(CLAUDE_PREV_STATUSLINE_PATH)
                except Exception:
                    pass
            else:
                data.pop("statusLine", None)

        if data:
            write_json_atomic(CLAUDE_SETTINGS_PATH, data)
        else:
            os.remove(CLAUDE_SETTINGS_PATH)


def is_claude_installed():
    if not os.path.exists(CLAUDE_SETTINGS_PATH):
        return False
    try:
        data = read_json_dict(CLAUDE_SETTINGS_PATH)
        return has_monitor_groups(data.get("hooks"))
    except Exception:
        return False


def get_status():
    agy_bin = any(
        p and os.path.isfile(p) and os.access(p, os.X_OK)
        for p in [
            os.path.expanduser("~/.gemini/bin/agy"),
            shutil.which("agy"),
            "/usr/local/bin/agy",
            "/opt/homebrew/bin/agy",
        ]
    )
    codex_bin = any(
        p and os.path.isfile(p) and os.access(p, os.X_OK)
        for p in [
            shutil.which("codex"),
            "/opt/homebrew/bin/codex",
            "/usr/local/bin/codex",
            os.path.expanduser("~/.local/bin/codex"),
            "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex",
        ]
    )
    claude_bin = bool(shutil.which("claude")) or os.path.isdir(
        os.path.expanduser("~/.claude")
    )

    return {
        "antigravity": {
            "hooksInstalled": is_antigravity_installed(),
            "binaryFound": agy_bin,
            "appInstalled": os.path.exists("/Applications/Antigravity.app"),
        },
        "codex": {
            "hooksInstalled": is_codex_installed(),
            "binaryFound": codex_bin,
            "appInstalled": os.path.exists("/Applications/ChatGPT.app"),
        },
        "claude": {
            "hooksInstalled": is_claude_installed(),
            "binaryFound": claude_bin,
            "appInstalled": os.path.exists("/Applications/Claude.app"),
        },
    }


def enable_provider(provider):
    if provider == "antigravity":
        enable_antigravity()
    elif provider == "codex":
        enable_codex()
    elif provider == "claude":
        enable_claude()


def disable_provider(provider):
    if provider == "antigravity":
        disable_antigravity()
    elif provider == "codex":
        disable_codex()
    elif provider == "claude":
        disable_claude()


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="action", required=True)

    p_en = sub.add_parser("enable")
    p_en.add_argument("provider", choices=PROVIDERS)

    p_dis = sub.add_parser("disable")
    p_dis.add_argument("provider", choices=PROVIDERS)

    p_sync = sub.add_parser("sync")
    p_sync.add_argument("providers", nargs="?", default="")

    sub.add_parser("status")

    args = parser.parse_args()

    if args.action == "enable":
        enable_provider(args.provider)
    elif args.action == "disable":
        disable_provider(args.provider)
    elif args.action == "sync":
        wanted = set(
            p.strip() for p in args.providers.split(",") if p.strip() in PROVIDERS
        )
        for p in PROVIDERS:
            if p in wanted:
                enable_provider(p)
            else:
                disable_provider(p)

    sys.stdout.write(json.dumps(get_status()) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
