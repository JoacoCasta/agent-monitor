#!/usr/bin/python3
import argparse
import json
import os
import shutil
import sys
import tempfile
import time

MONITOR_DIR = os.path.expanduser("~/.gemini/agent-monitor")
HOOK_HANDLER_PATH = os.path.join(MONITOR_DIR, "hook-handler.py")
CLAUDE_STATUSLINE_PATH = os.path.join(MONITOR_DIR, "claude-statusline.py")
CLAUDE_PREV_STATUSLINE_PATH = os.path.join(MONITOR_DIR, "claude-prev-statusline.json")

ANTIGRAVITY_HOOKS_PATH = os.path.expanduser("~/.gemini/config/hooks.json")
CLAUDE_SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")

MONITOR_MARKERS = (
    "agent-monitor/hook-handler.py",
    "agent-monitor\\hook-handler.py",
    "antigravity-monitor/hook-handler.py",
)

STATUSLINE_MARKERS = (
    "claude-statusline.py",
)

PROVIDERS = ("antigravity", "codex", "claude", "copilot")


def get_codex_hooks_path():
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home and codex_home.strip():
        return os.path.join(os.path.expanduser(codex_home.strip()), "hooks.json")
    return os.path.expanduser("~/.codex/hooks.json")


COPILOT_HOOK_EVENTS = (
    "sessionStart",
    "userPromptSubmitted",
    "preToolUse",
    "postToolUse",
    "postToolUseFailure",
    "permissionRequest",
    "notification",
    "agentStop",
    "subagentStop",
    "sessionEnd",
)


def get_copilot_hooks_path():
    copilot_home = os.environ.get("COPILOT_HOME")
    if copilot_home and copilot_home.strip():
        return os.path.join(os.path.expanduser(copilot_home.strip()), "hooks", "agent-monitor.json")
    return os.path.expanduser("~/.copilot/hooks/agent-monitor.json")


def is_copilot_installed():
    return os.path.isfile(get_copilot_hooks_path())


def enable_copilot():
    py = resolve_python_for_hooks()
    hooks_obj = {}
    for ev in COPILOT_HOOK_EVENTS:
        cmd = "{} {} copilot {}".format(quote_path(py), quote_path(HOOK_HANDLER_PATH), ev)
        hooks_obj[ev] = [
            {
                "type": "command",
                "bash": cmd,
                "timeoutSec": 5,
            }
        ]
    write_json_atomic(get_copilot_hooks_path(), {"version": 1, "hooks": hooks_obj})


def disable_copilot():
    path = get_copilot_hooks_path()
    try:
        if os.path.isfile(path):
            os.unlink(path)
        parent = os.path.dirname(path)
        if os.path.isdir(parent) and not os.listdir(parent):
            os.rmdir(parent)
    except Exception:
        pass


def quote_path(path):
    if " " in path or "\t" in path:
        return '"{}"'.format(path)
    return path


def resolve_python_for_hooks():
    env_py = os.environ.get("AGENT_MONITOR_PYTHON")
    if env_py and os.path.isfile(env_py):
        return env_py
    if sys.platform == "darwin" and os.path.isfile("/usr/bin/python3"):
        return "/usr/bin/python3"
    if not getattr(sys, "frozen", False) and sys.executable and os.path.isfile(sys.executable):
        return sys.executable
    for cand in ("python3", "python"):
        found = shutil.which(cand)
        if found:
            return found
    return sys.executable or "python3"


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
        last_err = None
        for _ in range(3):
            try:
                os.replace(tmp_path, path)
                return
            except PermissionError as exc:
                last_err = exc
                time.sleep(0.03)
        if last_err is not None:
            raise last_err
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
    py_exe = resolve_python_for_hooks()
    data = read_json_dict(ANTIGRAVITY_HOOKS_PATH)
    data.pop("antigravity-monitor", None)

    def cmd(event):
        return {
            "type": "command",
            "command": "{} {} antigravity {}".format(
                quote_path(py_exe), quote_path(HOOK_HANDLER_PATH), event
            ),
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
    py_exe = resolve_python_for_hooks()
    codex_hooks_path = get_codex_hooks_path()
    os.makedirs(os.path.dirname(codex_hooks_path), exist_ok=True)
    data = read_json_dict(codex_hooks_path)
    hooks = strip_monitor_groups(data.get("hooks"))

    def group(event, matcher=None):
        entry = {
            "hooks": [
                {
                    "type": "command",
                    "command": "{} {} codex {}".format(
                        quote_path(py_exe), quote_path(HOOK_HANDLER_PATH), event
                    ),
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
    write_json_atomic(codex_hooks_path, data)


def disable_codex():
    codex_hooks_path = get_codex_hooks_path()
    if not os.path.exists(codex_hooks_path):
        return
    data = read_json_dict(codex_hooks_path)
    hooks = strip_monitor_groups(data.get("hooks"))
    if hooks:
        data["hooks"] = hooks
        write_json_atomic(codex_hooks_path, data)
    else:
        data.pop("hooks", None)
        remaining = {k: v for k, v in data.items() if k != "description"}
        if remaining:
            write_json_atomic(codex_hooks_path, data)
        else:
            os.remove(codex_hooks_path)


def is_codex_installed():
    codex_hooks_path = get_codex_hooks_path()
    if not os.path.exists(codex_hooks_path):
        return False
    try:
        data = read_json_dict(codex_hooks_path)
        return has_monitor_groups(data.get("hooks"))
    except Exception:
        return False


# --- Claude Code ---

def enable_claude():
    py_exe = resolve_python_for_hooks()
    os.makedirs(os.path.dirname(CLAUDE_SETTINGS_PATH), exist_ok=True)
    os.makedirs(MONITOR_DIR, exist_ok=True)
    data = read_json_dict(CLAUDE_SETTINGS_PATH)
    hooks = strip_monitor_groups(data.get("hooks"))

    def group(event, matcher=None):
        entry = {
            "hooks": [
                {
                    "type": "command",
                    "command": "{} {} claude {}".format(
                        quote_path(py_exe), quote_path(HOOK_HANDLER_PATH), event
                    ),
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
        and not any(m in str(existing_sl.get("command") or "") for m in STATUSLINE_MARKERS)
        and not os.path.exists(CLAUDE_PREV_STATUSLINE_PATH)
    ):
        write_json_atomic(CLAUDE_PREV_STATUSLINE_PATH, existing_sl)

    data["statusLine"] = {
        "type": "command",
        "command": "{} {}".format(quote_path(py_exe), quote_path(CLAUDE_STATUSLINE_PATH)),
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
        if isinstance(sl, dict) and any(
            m in str(sl.get("command") or "") for m in STATUSLINE_MARKERS
        ):
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


def detect_app_installed(provider):
    if sys.platform == "darwin":
        app_map = {
            "antigravity": "/Applications/Antigravity.app",
            "codex": "/Applications/ChatGPT.app",
            "claude": "/Applications/Claude.app",
            "copilot": "/Applications/GitHub Copilot.app",
        }
        return os.path.exists(app_map.get(provider, ""))

    if os.name == "nt":
        local_app = os.environ.get("LOCALAPPDATA", "")
        prog_files = os.environ.get("ProgramFiles", "")
        if provider == "antigravity":
            return any(
                os.path.exists(p)
                for p in [
                    os.path.join(local_app, "Programs", "Antigravity", "Antigravity.exe"),
                    os.path.join(local_app, "Antigravity", "Antigravity.exe"),
                    os.path.join(prog_files, "Antigravity", "Antigravity.exe"),
                ]
                if local_app or prog_files
            ) or os.path.isdir(os.path.expanduser("~/.gemini/antigravity"))
        if provider == "codex":
            return any(
                os.path.exists(p)
                for p in [
                    os.path.join(local_app, "Programs", "ChatGPT", "ChatGPT.exe"),
                    os.path.join(local_app, "Programs", "Codex", "Codex.exe"),
                ]
                if local_app
            ) or os.path.isdir(os.path.expanduser("~/.codex"))
        if provider == "claude":
            return any(
                os.path.exists(p)
                for p in [
                    os.path.join(local_app, "AnthropicClaude", "claude.exe"),
                    os.path.join(local_app, "Programs", "Claude", "Claude.exe"),
                ]
                if local_app
            ) or os.path.isdir(os.path.expanduser("~/.claude"))
        return False

    # Linux
    if provider == "antigravity":
        return (
            bool(shutil.which("antigravity"))
            or os.path.exists("/usr/share/applications/antigravity.desktop")
            or os.path.exists(os.path.expanduser("~/.local/share/applications/antigravity.desktop"))
            or os.path.isdir(os.path.expanduser("~/.gemini/antigravity"))
        )
    if provider == "codex":
        return bool(shutil.which("codex")) or os.path.isdir(os.path.expanduser("~/.codex"))
    if provider == "claude":
        return (
            bool(shutil.which("claude"))
            or os.path.exists("/usr/share/applications/claude.desktop")
            or os.path.exists(os.path.expanduser("~/.local/share/applications/claude.desktop"))
            or os.path.isdir(os.path.expanduser("~/.claude"))
        )
    return False


def get_status():
    local_app = os.environ.get("LOCALAPPDATA", "") if os.name == "nt" else ""
    appdata = os.environ.get("APPDATA", "") if os.name == "nt" else ""

    agy_candidates = [
        os.path.expanduser("~/.gemini/bin/agy"),
        os.path.expanduser("~/.gemini/bin/agy.exe"),
        shutil.which("agy"),
        shutil.which("agy.exe"),
        "/usr/local/bin/agy",
        "/opt/homebrew/bin/agy",
    ]
    if local_app:
        agy_candidates.extend(
            [
                os.path.join(local_app, "Antigravity", "agy.exe"),
                os.path.join(local_app, "Programs", "Antigravity", "agy.exe"),
            ]
        )

    codex_candidates = [
        shutil.which("codex"),
        shutil.which("codex.exe"),
        shutil.which("codex.cmd"),
        "/opt/homebrew/bin/codex",
        "/usr/local/bin/codex",
        os.path.expanduser("~/.local/bin/codex"),
        "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex",
    ]
    if appdata:
        codex_candidates.append(os.path.join(appdata, "npm", "codex.cmd"))
    if local_app:
        codex_candidates.extend(
            [
                os.path.join(local_app, "Programs", "ChatGPT", "resources", "codex-cli", "codex.exe"),
                os.path.join(local_app, "Programs", "Codex", "codex.exe"),
            ]
        )

    agy_bin = any(
        p and os.path.isfile(p) and (os.name == "nt" or os.access(p, os.X_OK))
        for p in agy_candidates
    )
    codex_bin = any(
        p and os.path.isfile(p) and (os.name == "nt" or os.access(p, os.X_OK))
        for p in codex_candidates
    )
    claude_bin = (
        bool(shutil.which("claude"))
        or bool(shutil.which("claude.exe"))
        or bool(shutil.which("claude.cmd"))
        or os.path.isdir(os.path.expanduser("~/.claude"))
    )

    import glob

    home = os.path.expanduser("~")
    copilot_bin = (
        bool(os.environ.get("COPILOT_BINARY", "").strip() and os.path.isfile(os.environ["COPILOT_BINARY"].strip()))
        or bool(shutil.which("copilot"))
        or any(os.path.isfile(p) and os.access(p, os.X_OK) for p in [
            os.path.join(home, ".local", "bin", "copilot"),
            "/opt/homebrew/bin/copilot",
            "/usr/local/bin/copilot",
        ])
        or bool(glob.glob(os.path.join(home, "Library", "Application Support", "orca", "agent-runtimes", "copilot", "*", "copilot")))
        or bool(glob.glob(os.path.join(home, "Library", "Caches", "github-copilot-sdk", "cli", "*", "copilot")))
    )

    return {
        "antigravity": {
            "hooksInstalled": is_antigravity_installed(),
            "binaryFound": agy_bin,
            "appInstalled": detect_app_installed("antigravity"),
        },
        "codex": {
            "hooksInstalled": is_codex_installed(),
            "binaryFound": codex_bin,
            "appInstalled": detect_app_installed("codex"),
        },
        "claude": {
            "hooksInstalled": is_claude_installed(),
            "binaryFound": claude_bin,
            "appInstalled": detect_app_installed("claude"),
        },
        "copilot": {
            "hooksInstalled": is_copilot_installed(),
            "binaryFound": copilot_bin,
            "appInstalled": detect_app_installed("copilot"),
        },
    }


def enable_provider(provider):
    if provider == "antigravity":
        enable_antigravity()
    elif provider == "codex":
        enable_codex()
    elif provider == "claude":
        enable_claude()
    elif provider == "copilot":
        enable_copilot()


def disable_provider(provider):
    if provider == "antigravity":
        disable_antigravity()
    elif provider == "codex":
        disable_codex()
    elif provider == "claude":
        disable_claude()
    elif provider == "copilot":
        disable_copilot()


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
