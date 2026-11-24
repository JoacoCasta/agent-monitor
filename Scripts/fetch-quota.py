#!/usr/bin/python3
import argparse
import datetime
import json
import os
import pty
import select
import shutil
import subprocess
import sys
import tempfile
import time


def utc_now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def epoch_to_iso(epoch_sec):
    try:
        ts = float(epoch_sec)
        if ts <= 0:
            return ""
        return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    except Exception:
        return ""


def resolve_agy_binary():
    candidates = [
        os.path.expanduser("~/.gemini/bin/agy"),
        shutil.which("agy"),
        "/usr/local/bin/agy",
        "/opt/homebrew/bin/agy",
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def resolve_codex_binary():
    candidates = [
        shutil.which("codex"),
        "/opt/homebrew/bin/codex",
        "/usr/local/bin/codex",
        os.path.expanduser("~/.local/bin/codex"),
        "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex",
    ]
    for path in candidates:
        if path and os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def fetch_antigravity():
    agy_bin = resolve_agy_binary()
    if not agy_bin:
        raise RuntimeError("Binary 'agy' not found")

    with tempfile.TemporaryDirectory(prefix="agy-quota-") as td:
        out_file = os.path.join(td, "status.json")
        cap_script = os.path.join(td, "cap.sh")
        with open(cap_script, "w", encoding="utf-8") as f:
            f.write(
                "#!/bin/sh\n"
                "cat > \"{0}.tmp\" && mv \"{0}.tmp\" \"{0}\"\n"
                "echo ok\n".format(out_file)
            )
        os.chmod(cap_script, 0o755)

        settings_json = json.dumps(
            {
                "statusLine": {
                    "type": "command",
                    "command": cap_script,
                    "enabled": True,
                }
            }
        )

        env = os.environ.copy()
        env.setdefault("HOME", os.path.expanduser("~"))
        env.setdefault("TERM", "xterm-256color")

        master, slave = pty.openpty()
        proc = None
        got_payload = None
        try:
            proc = subprocess.Popen(
                [agy_bin, "--settings", settings_json],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                cwd=td,
                env=env,
                close_fds=True,
                start_new_session=True,
            )
        except Exception:
            os.close(slave)
            os.close(master)
            raise

        os.close(slave)
        deadline = time.time() + 15.0
        try:
            while time.time() < deadline:
                r, _, _ = select.select([master], [], [], 0.15)
                if r:
                    try:
                        os.read(master, 4096)
                    except OSError:
                        break
                if os.path.exists(out_file):
                    try:
                        with open(out_file, "r", encoding="utf-8") as sf:
                            data = json.load(sf)
                        if (
                            isinstance(data, dict)
                            and isinstance(data.get("quota"), dict)
                            and data["quota"]
                        ):
                            got_payload = data
                            break
                    except Exception:
                        pass
                if proc.poll() is not None:
                    break
        finally:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2.0)
                except Exception:
                    proc.kill()
                    try:
                        proc.wait(timeout=1.0)
                    except Exception:
                        pass
            try:
                os.close(master)
            except OSError:
                pass

        if not got_payload:
            raise RuntimeError("Timeout fetching quota from agy")

        raw_quota = got_payload.get("quota") or {}
        plan_tier = str(got_payload.get("plan_tier") or "")

        specs = [
            ("gemini-5h", "gemini", "Gemini", "5h", 5, "5-hour window", False),
            ("gemini-weekly", "gemini", "Gemini", "weekly", 7, "Weekly limit", True),
            ("3p-5h", "third_party", "3P Models (Claude / GPT)", "5h", 5, "5-hour window", False),
            ("3p-weekly", "third_party", "3P Models (Claude / GPT)", "weekly", 7, "Weekly limit", True),
        ]

        buckets = []
        seen = set()
        for bucket_id, group_key, group, window_kind, window_amount, label, is_weekly in specs:
            if bucket_id in raw_quota and isinstance(raw_quota[bucket_id], dict):
                seen.add(bucket_id)
                item = raw_quota[bucket_id]
                frac = item.get("remaining_fraction")
                if not isinstance(frac, (int, float)):
                    amount = item.get("remaining_amount")
                    frac = float(amount) if isinstance(amount, (int, float)) else 0.0
                entry = {
                    "id": bucket_id,
                    "group": group,
                    "groupKey": group_key,
                    "label": label,
                    "windowKind": window_kind,
                    "windowAmount": window_amount,
                    "isWeekly": is_weekly,
                    "remainingFraction": max(0.0, min(1.0, float(frac))),
                    "resetTime": str(item.get("reset_time") or ""),
                    "resetInSeconds": int(item.get("reset_in_seconds") or 0),
                }
                if "disabled" in item:
                    entry["disabled"] = bool(item["disabled"])
                buckets.append(entry)

        for bucket_id, item in raw_quota.items():
            if bucket_id in seen or not isinstance(item, dict):
                continue
            frac = item.get("remaining_fraction")
            if not isinstance(frac, (int, float)):
                amount = item.get("remaining_amount")
                frac = float(amount) if isinstance(amount, (int, float)) else 0.0
            is_weekly = "weekly" in bucket_id.lower()
            is_3p = "3p" in bucket_id.lower()
            group_key = "third_party" if is_3p else "gemini"
            group = "3P Models (Claude / GPT)" if is_3p else "Gemini"
            window_kind = "weekly" if is_weekly else "5h"
            window_amount = 7 if is_weekly else 5
            label = "Weekly limit" if is_weekly else "5-hour window"
            entry = {
                "id": str(bucket_id),
                "group": group,
                "groupKey": group_key,
                "label": label,
                "windowKind": window_kind,
                "windowAmount": window_amount,
                "isWeekly": is_weekly,
                "remainingFraction": max(0.0, min(1.0, float(frac))),
                "resetTime": str(item.get("reset_time") or ""),
                "resetInSeconds": int(item.get("reset_in_seconds") or 0),
            }
            if "disabled" in item:
                entry["disabled"] = bool(item["disabled"])
            buckets.append(entry)

        return {
            "provider": "antigravity",
            "fetchedAt": utc_now_iso(),
            "planType": plan_tier,
            "buckets": buckets,
        }


def describe_codex_window(mins):
    if not isinstance(mins, (int, float)) or mins <= 0:
        return "generic", 0, "Window", False
    m = int(mins)
    if m <= 360:
        return "5h", 5, "5-hour window", False
    if m <= 10800:
        return "weekly", 7, "Weekly limit", True
    if m >= 40000:
        return "monthly", 30, "Monthly limit", True
    if m % 1440 == 0:
        days = m // 1440
        return "days", days, "{}d window".format(days), True
    hours = max(1, m // 60)
    return "hours", hours, "{}h window".format(hours), m > 360


def fetch_codex():
    codex_bin = resolve_codex_binary()
    if not codex_bin:
        raise RuntimeError("Binary 'codex' not found")

    env = os.environ.copy()
    env.setdefault("HOME", os.path.expanduser("~"))

    proc = subprocess.Popen(
        [codex_bin, "app-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        start_new_session=True,
    )

    deadline = time.time() + 10.0
    rate_result = None
    try:
        init_req = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"clientInfo": {"name": "agent-monitor", "version": "1.0"}},
            }
        )
        proc.stdin.write(init_req + "\n")
        proc.stdin.flush()

        init_ok = False
        while time.time() < deadline:
            r, _, _ = select.select([proc.stdout], [], [], 0.2)
            if r:
                line = proc.stdout.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line)
                except Exception:
                    continue
                if msg.get("id") == 1:
                    if "error" in msg:
                        raise RuntimeError(str(msg["error"]))
                    init_ok = True
                    break
            if proc.poll() is not None:
                break

        if not init_ok:
            raise RuntimeError("Timeout starting codex app-server")

        proc.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "initialized", "params": {}}) + "\n"
        )
        proc.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "account/rateLimits/read",
                    "params": {},
                }
            )
            + "\n"
        )
        proc.stdin.flush()

        while time.time() < deadline:
            r, _, _ = select.select([proc.stdout], [], [], 0.2)
            if r:
                line = proc.stdout.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line)
                except Exception:
                    continue
                if msg.get("id") == 2:
                    if "error" in msg:
                        raise RuntimeError(str(msg["error"]))
                    rate_result = msg.get("result")
                    break
            if proc.poll() is not None:
                break
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except Exception:
                proc.kill()
                try:
                    proc.wait(timeout=1.0)
                except Exception:
                    pass

    if not isinstance(rate_result, dict):
        raise RuntimeError("No Codex rate limits returned")

    rl = rate_result.get("rateLimits")
    if not isinstance(rl, dict):
        by_id = rate_result.get("rateLimitsByLimitId")
        if isinstance(by_id, dict) and by_id:
            rl = next(iter(by_id.values()))
        else:
            rl = {}

    plan_type = str(rl.get("planType") or "")
    if plan_type:
        plan_type = plan_type[:1].upper() + plan_type[1:]

    now = time.time()
    buckets = []
    for slot in ("primary", "secondary"):
        window = rl.get(slot)
        if not isinstance(window, dict):
            continue
        used = window.get("usedPercent")
        if not isinstance(used, (int, float)):
            continue
        mins = window.get("windowDurationMins")
        window_kind, window_amount, label, is_weekly = describe_codex_window(mins)
        resets_at = window.get("resetsAt")
        reset_iso = epoch_to_iso(resets_at) if resets_at is not None else ""
        reset_sec = 0
        if isinstance(resets_at, (int, float)):
            reset_sec = max(0, int(float(resets_at) - now))

        buckets.append(
            {
                "id": "codex-{}".format(slot),
                "group": "Codex",
                "groupKey": "codex",
                "label": label,
                "windowKind": window_kind,
                "windowAmount": window_amount,
                "isWeekly": is_weekly,
                "remainingFraction": max(0.0, min(1.0, 1.0 - (float(used) / 100.0))),
                "resetTime": reset_iso,
                "resetInSeconds": reset_sec,
            }
        )

    return {
        "provider": "codex",
        "fetchedAt": utc_now_iso(),
        "planType": plan_type,
        "buckets": buckets,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, choices=["antigravity", "codex"])
    args = parser.parse_args()

    try:
        if args.provider == "antigravity":
            data = fetch_antigravity()
        else:
            data = fetch_codex()
        sys.stdout.write(json.dumps(data) + "\n")
        sys.stdout.flush()
    except Exception as exc:
        sys.stderr.write(json.dumps({"error": str(exc)}) + "\n")
        sys.stderr.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
