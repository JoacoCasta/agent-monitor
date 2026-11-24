#!/usr/bin/python3
import datetime
import json
import os
import subprocess
import sys
import tempfile
import time

MONITOR_DIR = os.path.expanduser("~/.gemini/agent-monitor")
CLAUDE_QUOTA_PATH = os.path.join(MONITOR_DIR, "claude-quota.json")
PREV_STATUSLINE_PATH = os.path.join(MONITOR_DIR, "claude-prev-statusline.json")


def to_iso_utc(epoch_sec):
    try:
        ts = float(epoch_sec)
        if ts <= 0:
            return ""
        return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except Exception:
        return ""


def write_claude_quota(payload):
    rate_limits = payload.get("rate_limits")
    if not isinstance(rate_limits, dict) or not rate_limits:
        return None

    now = time.time()
    buckets = []

    specs = [
        ("five_hour", "claude", "Claude Code", "5h", 5, "5-hour window", False),
        ("seven_day", "claude", "Claude Code", "weekly", 7, "Weekly limit", True),
        ("spend_limit", "claude", "Claude Code", "spend", 0, "Spend limit", True),
    ]

    for key, group_key, group, window_kind, window_amount, label, is_weekly in specs:
        item = rate_limits.get(key)
        if not isinstance(item, dict):
            continue
        used = item.get("used_percentage")
        if not isinstance(used, (int, float)):
            continue
        remaining_frac = max(0.0, min(1.0, 1.0 - (float(used) / 100.0)))
        resets_at = item.get("resets_at")
        reset_iso = to_iso_utc(resets_at) if resets_at is not None else ""
        reset_sec = 0
        if isinstance(resets_at, (int, float)):
            reset_sec = max(0, int(float(resets_at) - now))

        buckets.append(
            {
                "id": "claude-{}".format(key),
                "group": group,
                "groupKey": group_key,
                "label": label,
                "windowKind": window_kind,
                "windowAmount": window_amount,
                "isWeekly": is_weekly,
                "remainingFraction": remaining_frac,
                "resetTime": reset_iso,
                "resetInSeconds": reset_sec,
            }
        )

    if not buckets:
        return None

    os.makedirs(MONITOR_DIR, exist_ok=True)
    fetched_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    snapshot = {
        "provider": "claude",
        "fetchedAt": fetched_at,
        "planType": "",
        "buckets": buckets,
    }

    fd, tmp_path = tempfile.mkstemp(prefix=".claude-quota-", suffix=".json", dir=MONITOR_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tf:
            json.dump(snapshot, tf, ensure_ascii=False, indent=2)
        os.replace(tmp_path, CLAUDE_QUOTA_PATH)
    except Exception:
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass
    return snapshot


def run_previous_statusline(raw_stdin):
    if not os.path.exists(PREV_STATUSLINE_PATH):
        return False
    try:
        with open(PREV_STATUSLINE_PATH, "r", encoding="utf-8") as f:
            prev = json.load(f)
        if not isinstance(prev, dict):
            return False
        cmd = prev.get("command")
        if not isinstance(cmd, str) or not cmd.strip():
            return False
        if "claude-statusline.py" in cmd:
            return False
        proc = subprocess.run(
            ["/bin/sh", "-c", cmd],
            input=raw_stdin,
            capture_output=True,
            text=True,
            timeout=4,
        )
        if proc.returncode == 0 and proc.stdout:
            sys.stdout.write(proc.stdout)
            sys.stdout.flush()
            return True
    except Exception:
        pass
    return False


def format_default_statusline(payload, snapshot):
    parts = []
    model = payload.get("model")
    if isinstance(model, dict):
        name = model.get("display_name") or model.get("id")
        if isinstance(name, str) and name:
            parts.append(name)

    if snapshot and snapshot.get("buckets"):
        for b in snapshot["buckets"]:
            pct = int(round(b["remainingFraction"] * 100))
            if b["id"] == "claude-five_hour":
                parts.append("5h: {}%".format(pct))
            elif b["id"] == "claude-seven_day":
                parts.append("7d: {}%".format(pct))
            elif b["id"] == "claude-spend_limit":
                parts.append("Spend: {}%".format(pct))
    elif not parts:
        parts.append("Claude")

    sys.stdout.write(" | ".join(parts) + "\n")
    sys.stdout.flush()


def main():
    raw_stdin = ""
    payload = {}
    snapshot = None
    try:
        raw_stdin = sys.stdin.read()
        if raw_stdin and raw_stdin.strip():
            loaded = json.loads(raw_stdin)
            if isinstance(loaded, dict):
                payload = loaded
                snapshot = write_claude_quota(payload)
    except Exception:
        pass

    if not run_previous_statusline(raw_stdin):
        try:
            format_default_statusline(payload, snapshot)
        except Exception:
            pass


if __name__ == "__main__":
    main()
