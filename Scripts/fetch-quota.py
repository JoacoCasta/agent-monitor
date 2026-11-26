#!/usr/bin/python3
import argparse
import datetime
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time

if os.name != "nt":
    import pty
    import select


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


def quote_cmd_arg(path):
    if " " in path or "\t" in path:
        return '"{}"'.format(path)
    return path


def resolve_python_executable():
    env_py = os.environ.get("AGENT_MONITOR_PYTHON")
    if env_py and os.path.isfile(env_py):
        return env_py
    if not getattr(sys, "frozen", False) and sys.executable and os.path.isfile(sys.executable):
        return sys.executable
    if os.name != "nt" and os.path.isfile("/usr/bin/python3"):
        return "/usr/bin/python3"
    for cand in ("python3", "python"):
        found = shutil.which(cand)
        if found:
            return found
    return sys.executable or "python3"


def resolve_agy_binary():
    candidates = [
        os.path.expanduser("~/.gemini/bin/agy"),
        os.path.expanduser("~/.gemini/bin/agy.exe"),
        shutil.which("agy"),
        shutil.which("agy.exe"),
        shutil.which("agy.cmd"),
        "/usr/local/bin/agy",
        "/opt/homebrew/bin/agy",
    ]
    if os.name == "nt":
        local_app = os.environ.get("LOCALAPPDATA", "")
        if local_app:
            candidates.extend(
                [
                    os.path.join(local_app, "Antigravity", "agy.exe"),
                    os.path.join(local_app, "Programs", "Antigravity", "agy.exe"),
                ]
            )
    for path in candidates:
        if path and os.path.isfile(path) and (os.name == "nt" or os.access(path, os.X_OK)):
            return path
    return None


def resolve_codex_binary():
    candidates = [
        shutil.which("codex"),
        shutil.which("codex.exe"),
        shutil.which("codex.cmd"),
        "/opt/homebrew/bin/codex",
        "/usr/local/bin/codex",
        os.path.expanduser("~/.local/bin/codex"),
        "/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex",
    ]
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "")
        local_app = os.environ.get("LOCALAPPDATA", "")
        if appdata:
            candidates.append(os.path.join(appdata, "npm", "codex.cmd"))
        if local_app:
            candidates.extend(
                [
                    os.path.join(local_app, "Programs", "ChatGPT", "resources", "codex-cli", "codex.exe"),
                    os.path.join(local_app, "Programs", "Codex", "codex.exe"),
                ]
            )
    for path in candidates:
        if path and os.path.isfile(path) and (os.name == "nt" or os.access(path, os.X_OK)):
            return path
    return None


def no_window_kwargs():
    if os.name == "nt":
        return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)}
    return {}


def parse_antigravity_payload(got_payload):
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


def fetch_antigravity():
    agy_bin = resolve_agy_binary()
    if not agy_bin:
        raise RuntimeError("Binary 'agy' not found")

    py_exe = resolve_python_executable()
    with tempfile.TemporaryDirectory(prefix="agy-quota-") as td:
        out_file = os.path.join(td, "status.json")
        cap_script = os.path.join(td, "cap.py")
        with open(cap_script, "w", encoding="utf-8") as f:
            f.write(
                "import os, sys\n"
                "data = sys.stdin.read()\n"
                "out = sys.argv[1]\n"
                "tmp = out + '.tmp'\n"
                "with open(tmp, 'w', encoding='utf-8') as wf:\n"
                "    wf.write(data)\n"
                "os.replace(tmp, out)\n"
                "print('ok')\n"
            )

        cmd_str = "{} {} {}".format(
            quote_cmd_arg(py_exe), quote_cmd_arg(cap_script), quote_cmd_arg(out_file)
        )
        settings_json = json.dumps(
            {
                "statusLine": {
                    "type": "command",
                    "command": cmd_str,
                    "enabled": True,
                }
            }
        )

        env = os.environ.copy()
        env.setdefault("HOME", os.path.expanduser("~"))
        env.setdefault("TERM", "xterm-256color")

        got_payload = None
        if os.name == "nt":
            proc = subprocess.Popen(
                [agy_bin, "--settings", settings_json],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=td,
                env=env,
                **no_window_kwargs()
            )
            drain_thread = threading.Thread(
                target=lambda: proc.stdout.read() if proc.stdout else None,
                daemon=True,
            )
            drain_thread.start()
            deadline = time.time() + 15.0
            try:
                while time.time() < deadline:
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
                    time.sleep(0.15)
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
        else:
            master, slave = pty.openpty()
            proc = None
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

        return parse_antigravity_payload(got_payload)


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

    popen_kwargs = dict(
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if os.name == "nt":
        popen_kwargs.update(no_window_kwargs())
    else:
        popen_kwargs["start_new_session"] = True

    proc = subprocess.Popen([codex_bin, "app-server"], **popen_kwargs)

    lines_queue = queue.Queue()

    def reader_worker():
        try:
            for line in iter(proc.stdout.readline, ""):
                lines_queue.put(line)
        except Exception:
            pass
        finally:
            lines_queue.put(None)

    threading.Thread(target=reader_worker, daemon=True).start()

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
            remaining = max(0.05, min(0.25, deadline - time.time()))
            try:
                line = lines_queue.get(timeout=remaining)
            except queue.Empty:
                if proc.poll() is not None:
                    break
                continue
            if line is None:
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
            remaining = max(0.05, min(0.25, deadline - time.time()))
            try:
                line = lines_queue.get(timeout=remaining)
            except queue.Empty:
                if proc.poll() is not None:
                    break
                continue
            if line is None:
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


def resolve_copilot_binary():
    override = os.environ.get("COPILOT_BINARY", "").strip()
    if override and os.path.isfile(override) and os.access(override, os.X_OK):
        return override

    found = shutil.which("copilot")
    if found and os.path.isfile(found) and os.access(found, os.X_OK):
        return found

    home = os.path.expanduser("~")
    static_candidates = [
        os.path.join(home, ".local", "bin", "copilot"),
        "/opt/homebrew/bin/copilot",
        "/usr/local/bin/copilot",
    ]
    for cand in static_candidates:
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand

    import glob

    glob_patterns = [
        os.path.join(home, "Library", "Application Support", "orca", "agent-runtimes", "copilot", "*", "copilot"),
        os.path.join(home, "Library", "Caches", "github-copilot-sdk", "cli", "*", "copilot"),
    ]
    matches = []
    for pattern in glob_patterns:
        for cand in glob.glob(pattern):
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                try:
                    mtime = os.path.getmtime(cand)
                except OSError:
                    mtime = 0
                matches.append((mtime, cand))
    if matches:
        matches.sort(reverse=True)
        return matches[0][1]
    return None


def _write_lsp_frame(stream, payload):
    body = json.dumps(payload).encode("utf-8")
    header = "Content-Length: {}\r\n\r\n".format(len(body)).encode("ascii")
    stream.write(header + body)
    stream.flush()


def _read_lsp_frames(fd, deadline):
    import select
    import time

    buf = b""
    messages = []
    while time.monotonic() < deadline:
        remaining = max(0.05, deadline - time.monotonic())
        ready, _, _ = select.select([fd], [], [], min(0.25, remaining))
        if not ready:
            continue
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        buf += chunk
        while True:
            sep_idx = buf.find(b"\r\n\r\n")
            sep_len = 4
            if sep_idx == -1:
                sep_idx = buf.find(b"\n\n")
                sep_len = 2
            if sep_idx == -1:
                break
            header_bytes = buf[:sep_idx].decode("ascii", errors="ignore")
            content_length = None
            for line in header_bytes.splitlines():
                if line.lower().startswith("content-length:"):
                    try:
                        content_length = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        content_length = None
            if content_length is None:
                buf = buf[sep_idx + sep_len:]
                continue
            total_needed = sep_idx + sep_len + content_length
            if len(buf) < total_needed:
                break
            body = buf[sep_idx + sep_len:total_needed]
            buf = buf[total_needed:]
            try:
                messages.append(json.loads(body.decode("utf-8")))
            except Exception:
                pass
        if messages:
            return messages
    return messages


def _parse_iso_to_epoch(iso_str):
    if not iso_str or not isinstance(iso_str, str):
        return None
    from datetime import datetime, timezone

    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return None


def parse_copilot_quota(raw_result, now_epoch=None):
    import time
    from datetime import datetime, timezone

    if now_epoch is None:
        now_epoch = time.time()

    snapshots = raw_result.get("quotaSnapshots") if isinstance(raw_result, dict) else None
    if not isinstance(snapshots, dict):
        return []

    spec = [
        ("premium_interactions", "premium", "Premium requests"),
        ("chat", "chat", "Chat"),
        ("completions", "completions", "Completions"),
    ]

    finite_buckets = []
    fallback_buckets = []
    for key, window_kind, label in spec:
        snap = snapshots.get(key)
        if not isinstance(snap, dict):
            continue
        pct = snap.get("remainingPercentage")
        if pct is None:
            pct = 100.0
        try:
            rem_frac = max(0.0, min(1.0, float(pct) / 100.0))
        except (TypeError, ValueError):
            rem_frac = 1.0

        entitlement = snap.get("entitlementRequests")
        used = snap.get("usedRequests")
        is_unlimited = bool(snap.get("isUnlimitedEntitlement", False))

        reset_iso = ""
        reset_in_seconds = 0
        raw_reset = snap.get("resetDate")
        reset_ts = _parse_iso_to_epoch(raw_reset)
        if reset_ts is not None and reset_ts > now_epoch + 60:
            reset_iso = datetime.fromtimestamp(reset_ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            reset_in_seconds = int(round(reset_ts - now_epoch))

        bucket = {
            "id": "copilot-{}".format(key),
            "group": "Copilot",
            "groupKey": "copilot",
            "label": label,
            "windowKind": window_kind,
            "isWeekly": False,
            "remainingFraction": round(rem_frac, 4),
            "resetTime": reset_iso,
            "resetInSeconds": reset_in_seconds,
            "disabled": False,
        }
        if not is_unlimited:
            try:
                if entitlement is not None:
                    bucket["entitlementRequests"] = int(entitlement)
                if used is not None:
                    bucket["usedRequests"] = int(used)
            except (TypeError, ValueError):
                pass
            finite_buckets.append(bucket)
        else:
            fallback_buckets.append(bucket)

    return finite_buckets if finite_buckets else fallback_buckets[:1]


def fetch_copilot():
    import time

    binary = resolve_copilot_binary()
    if not binary:
        raise RuntimeError("copilot CLI not found")

    proc = subprocess.Popen(
        [binary, "--headless", "--stdio", "--no-auto-update"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    responses = {}
    try:
        deadline = time.monotonic() + 10.0
        _write_lsp_frame(proc.stdin, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        _write_lsp_frame(proc.stdin, {"jsonrpc": "2.0", "id": 2, "method": "auth.getStatus", "params": {}})
        _write_lsp_frame(proc.stdin, {"jsonrpc": "2.0", "id": 3, "method": "account.getQuota", "params": {}})

        fd = proc.stdout.fileno()
        while time.monotonic() < deadline and (2 not in responses or 3 not in responses):
            frames = _read_lsp_frames(fd, deadline)
            if not frames:
                break
            for msg in frames:
                if isinstance(msg, dict) and "id" in msg:
                    responses[msg["id"]] = msg
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    auth_resp = responses.get(2, {})
    auth_res = auth_resp.get("result") or {}
    if auth_resp and not auth_res.get("isAuthenticated", True):
        raise RuntimeError("Not authenticated with GitHub Copilot")

    quota_resp = responses.get(3, {})
    if not quota_resp:
        raise RuntimeError("Timed out waiting for Copilot account.getQuota")
    if "error" in quota_resp and quota_resp["error"]:
        err_msg = quota_resp["error"].get("message") if isinstance(quota_resp["error"], dict) else str(quota_resp["error"])
        raise RuntimeError(err_msg or "Copilot quota RPC error")

    buckets = parse_copilot_quota(quota_resp.get("result") or {})
    return {
        "provider": "copilot",
        "fetchedAt": utc_now_iso(),
        "planType": "",
        "buckets": buckets,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", required=True, choices=["antigravity", "codex", "copilot"])
    args = parser.parse_args()

    try:
        if args.provider == "antigravity":
            data = fetch_antigravity()
        elif args.provider == "copilot":
            data = fetch_copilot()
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
