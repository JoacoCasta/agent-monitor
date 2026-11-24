#!/usr/bin/python3
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

if os.name == "nt":
    import msvcrt
else:
    import fcntl

PROVIDERS = ("antigravity", "codex", "claude")

PROVIDER_META = {
    "antigravity": {
        "short_tag": "AG",
        "display_name": "Antigravity",
        "supports_poll": True,
    },
    "codex": {
        "short_tag": "CX",
        "display_name": "ChatGPT (Codex)",
        "supports_poll": True,
    },
    "claude": {
        "short_tag": "CC",
        "display_name": "Claude Code",
        "supports_poll": False,
    },
}

STATUS_PRIORITY = {"waiting": 3, "active": 2, "idle": 1}
ACTIVE_STALE_TIMEOUT = 15 * 60
WAITING_STALE_TIMEOUT = 2 * 3600


def parse_iso_datetime(raw):
    if not isinstance(raw, str) or not raw.strip():
        return None
    val = raw.strip()
    if val.endswith("Z"):
        val = val[:-1] + "+00:00"
    try:
        dt = datetime.datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt
    except Exception:
        return None


def resolve_scripts_dir():
    candidates = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(os.path.join(meipass, "Scripts"))
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates.append(os.path.join(exe_dir, "Scripts"))
    here = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.abspath(os.path.join(here, "..", "Scripts")))
    candidates.append(os.path.abspath(os.path.join(here, "..")))
    candidates.append(os.path.expanduser("~/.gemini/agent-monitor"))

    for c in candidates:
        if os.path.isfile(os.path.join(c, "configure-hooks.py")):
            return c
    return os.path.expanduser("~/.gemini/agent-monitor")


def resolve_python_executable():
    env_py = os.environ.get("AGENT_MONITOR_PYTHON")
    if env_py and os.path.isfile(env_py):
        return env_py
    if not getattr(sys, "frozen", False) and sys.executable and os.path.isfile(sys.executable):
        return sys.executable
    if sys.platform == "darwin" and os.path.isfile("/usr/bin/python3"):
        return "/usr/bin/python3"
    for cand in ("python3", "python"):
        found = shutil.which(cand)
        if found:
            return found
    return sys.executable or "python3"


def antigravity_group_from_model(model_name):
    lower = (model_name or "").lower()
    markers = ("claude", "gpt", "o1", "o3", "o4", "3p", "opus", "sonnet", "haiku")
    if any(m in lower for m in markers):
        return "third_party"
    return "gemini"


def atomic_write_json(path, data):
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=".am-", suffix=".json", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tf:
            json.dump(data, tf, ensure_ascii=False, indent=2)
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


def _acquire_lock(lock_file, lock_path):
    if os.name == "nt":
        try:
            lock_file.seek(0)
            if os.path.getsize(lock_path) == 0:
                lock_file.write(" ")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
        except Exception:
            pass
    else:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)


def _release_lock(lock_file):
    if os.name == "nt":
        try:
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        except Exception:
            pass
    else:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def focus_provider_app(provider):
    if sys.platform == "darwin":
        bundle_map = {
            "antigravity": "com.google.antigravity",
            "codex": "com.openai.codex",
            "claude": "com.anthropic.claudefordesktop",
        }
        try:
            subprocess.Popen(["open", "-b", bundle_map[provider]])
            return
        except Exception:
            pass
        return

    if os.name == "nt":
        local_app = os.environ.get("LOCALAPPDATA", "")
        prog_files = os.environ.get("ProgramFiles", "")
        exe_candidates = {
            "antigravity": [
                os.path.join(local_app, "Programs", "Antigravity", "Antigravity.exe"),
                os.path.join(local_app, "Antigravity", "Antigravity.exe"),
                os.path.join(prog_files, "Antigravity", "Antigravity.exe"),
            ],
            "codex": [
                os.path.join(local_app, "Programs", "ChatGPT", "ChatGPT.exe"),
                os.path.join(local_app, "Programs", "Codex", "Codex.exe"),
            ],
            "claude": [
                os.path.join(local_app, "AnthropicClaude", "claude.exe"),
                os.path.join(local_app, "Programs", "Claude", "Claude.exe"),
            ],
        }
        for path in exe_candidates.get(provider, []):
            if path and os.path.isfile(path):
                try:
                    os.startfile(path)
                    return
                except Exception:
                    pass
        if shutil.which("wt.exe"):
            try:
                subprocess.Popen(["wt.exe"], creationflags=0x00000008)
                return
            except Exception:
                pass
        return

    # Linux
    desktop_candidates = {
        "antigravity": ["antigravity", "antigravity.desktop"],
        "codex": ["codex", "chatgpt"],
        "claude": ["claude", "claude.desktop"],
    }
    for cand in desktop_candidates.get(provider, []):
        if cand.endswith(".desktop") and shutil.which("gtk-launch"):
            try:
                subprocess.Popen(["gtk-launch", cand], start_new_session=True)
                return
            except Exception:
                pass
        exe = shutil.which(cand)
        if exe:
            try:
                subprocess.Popen([exe], start_new_session=True)
                return
            except Exception:
                pass
    for term in ("x-terminal-emulator", "gnome-terminal", "konsole", "kitty", "alacritty"):
        texe = shutil.which(term)
        if texe:
            try:
                subprocess.Popen([texe], start_new_session=True)
                return
            except Exception:
                pass


class MonitorCore:
    def __init__(self, monitor_dir=None):
        self.monitor_dir = os.path.expanduser(monitor_dir or "~/.gemini/agent-monitor")
        self.state_path = os.path.join(self.monitor_dir, "state.json")
        self.lock_path = os.path.join(self.monitor_dir, "state.lock")
        self.claude_quota_path = os.path.join(self.monitor_dir, "claude-quota.json")
        self.prefs_path = os.path.join(self.monitor_dir, "preferences.json")

        os.makedirs(self.monitor_dir, exist_ok=True)

        self.enabled_providers = list(PROVIDERS)
        self.has_completed_onboarding = False
        self.app_language = "system"

        self.all_sessions = []
        self.sessions_by_provider = {p: [] for p in PROVIDERS}
        self.status_by_provider = {p: "idle" for p in PROVIDERS}
        self.quotas_by_provider = {}
        self.last_updated_by_provider = {}
        self.last_seen_turn_by_provider = {}
        self.quota_errors = {}
        self.hook_statuses = {}

        self.notified_waiting_keys = set()
        self.notified_low_quota_keys = set()

        self.load_preferences()
        self.load_state(now_epoch=time.time())
        self.load_claude_quota()

    def load_preferences(self):
        if not os.path.exists(self.prefs_path):
            self.enabled_providers = list(PROVIDERS)
            self.has_completed_onboarding = False
            self.app_language = "system"
            return
        try:
            with open(self.prefs_path, "r", encoding="utf-8") as f:
                prefs = json.load(f)
            if not isinstance(prefs, dict):
                raise ValueError("invalid prefs")
            raw_list = prefs.get("enabledProviders") or []
            enabled = [p for p in PROVIDERS if p in raw_list]
            self.enabled_providers = enabled if enabled else ["antigravity"]
            self.has_completed_onboarding = bool(prefs.get("hasCompletedOnboarding", False))
            lang = prefs.get("language")
            self.app_language = lang if isinstance(lang, str) and lang else "system"
        except Exception:
            self.enabled_providers = list(PROVIDERS)
            self.has_completed_onboarding = False
            self.app_language = "system"

    def save_preferences(self):
        data = {
            "enabledProviders": list(self.enabled_providers),
            "hasCompletedOnboarding": bool(self.has_completed_onboarding),
            "language": self.app_language,
        }
        atomic_write_json(self.prefs_path, data)

    def complete_onboarding(self, selected):
        clean = [p for p in PROVIDERS if p in selected]
        self.enabled_providers = clean if clean else ["antigravity"]
        self.has_completed_onboarding = True
        self.save_preferences()

    def set_provider_enabled(self, provider, enabled):
        current = set(self.enabled_providers)
        if enabled:
            current.add(provider)
        else:
            if len(current) <= 1 and provider in current:
                return False
            current.discard(provider)
        self.enabled_providers = [p for p in PROVIDERS if p in current]
        self.save_preferences()
        if not enabled:
            self.quota_errors.pop(provider, None)
        return True

    def set_language(self, lang_code):
        self.app_language = lang_code
        self.save_preferences()

    @staticmethod
    def effective_status(session, now_epoch):
        raw = str(session.get("status") or "idle")
        updated = float(session.get("updatedAt") or 0)
        age = now_epoch - updated
        if raw == "active":
            return "idle" if age > ACTIVE_STALE_TIMEOUT else "active"
        if raw == "waiting":
            return "idle" if age > WAITING_STALE_TIMEOUT else "waiting"
        return "idle"

    def recompute_derived(self, now_epoch=None):
        if now_epoch is None:
            now_epoch = time.time()
        grouped = {p: [] for p in PROVIDERS}
        statuses = {p: "idle" for p in PROVIDERS}
        for s in self.all_sessions:
            prov = s.get("provider")
            if prov not in grouped:
                continue
            grouped[prov].append(s)
            eff = self.effective_status(s, now_epoch)
            if STATUS_PRIORITY.get(eff, 1) > STATUS_PRIORITY.get(statuses[prov], 1):
                statuses[prov] = eff
        self.sessions_by_provider = grouped
        self.status_by_provider = statuses

    def load_state(self, now_epoch=None):
        if now_epoch is None:
            now_epoch = time.time()
        newly_completed_providers = []
        if not os.path.exists(self.state_path):
            self.all_sessions = []
            self.recompute_derived(now_epoch)
            return newly_completed_providers
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                decoded = json.load(f)
            if not isinstance(decoded, dict):
                raise ValueError("invalid state")
        except Exception:
            self.all_sessions = []
            self.recompute_derived(now_epoch)
            return newly_completed_providers

        sessions_dict = decoded.get("sessions") or {}
        raw_sessions = [v for v in sessions_dict.values() if isinstance(v, dict)]
        raw_sessions.sort(
            key=lambda s: (
                STATUS_PRIORITY.get(str(s.get("status") or "idle"), 1),
                float(s.get("updatedAt") or 0),
            ),
            reverse=True,
        )
        self.all_sessions = raw_sessions
        self.recompute_derived(now_epoch)

        turn_map = decoded.get("lastTurnCompletedByProvider") or {}
        if isinstance(turn_map, dict):
            for prov, ts in turn_map.items():
                if prov not in PROVIDERS or not isinstance(ts, (int, float)):
                    continue
                prev = self.last_seen_turn_by_provider.get(prov, 0.0)
                if ts > prev:
                    self.last_seen_turn_by_provider[prov] = float(ts)
                    if prev > 0 and prov in self.enabled_providers and PROVIDER_META[prov]["supports_poll"]:
                        newly_completed_providers.append(prov)
        return newly_completed_providers

    def load_claude_quota(self):
        if "claude" not in self.enabled_providers or not os.path.exists(self.claude_quota_path):
            return False
        try:
            with open(self.claude_quota_path, "r", encoding="utf-8") as f:
                snap = json.load(f)
            if isinstance(snap, dict) and snap.get("provider") == "claude":
                self.quotas_by_provider["claude"] = snap
                dt = parse_iso_datetime(snap.get("fetchedAt"))
                self.last_updated_by_provider["claude"] = (
                    dt.timestamp() if dt is not None else time.time()
                )
                self.quota_errors.pop("claude", None)
                return True
        except Exception:
            pass
        return False

    def non_idle_sessions(self, provider, now_epoch=None):
        if now_epoch is None:
            now_epoch = time.time()
        return [
            s
            for s in self.sessions_by_provider.get(provider, [])
            if self.effective_status(s, now_epoch) != "idle"
        ]

    def active_antigravity_group_key(self, now_epoch=None):
        if now_epoch is None:
            now_epoch = time.time()
        sessions = self.sessions_by_provider.get("antigravity", [])
        non_idle = []
        for s in sessions:
            eff = self.effective_status(s, now_epoch)
            if eff != "idle" and s.get("modelName"):
                non_idle.append((s, eff))
        if non_idle:
            non_idle.sort(
                key=lambda item: (
                    STATUS_PRIORITY.get(item[1], 1),
                    float(item[0].get("updatedAt") or 0),
                ),
                reverse=True,
            )
            return antigravity_group_from_model(non_idle[0][0].get("modelName", ""))
        recent_idle = [
            s
            for s in sessions
            if s.get("modelName") and (now_epoch - float(s.get("updatedAt") or 0)) <= 600
        ]
        if recent_idle:
            recent_idle.sort(key=lambda s: float(s.get("updatedAt") or 0), reverse=True)
            return antigravity_group_from_model(recent_idle[0].get("modelName", ""))
        return "gemini"

    def menu_bar_percent(self, provider, now_epoch=None):
        snap = self.quotas_by_provider.get(provider)
        if not isinstance(snap, dict):
            return None
        buckets = [b for b in (snap.get("buckets") or []) if b.get("disabled") is not True]
        if provider == "antigravity":
            target_group = self.active_antigravity_group_key(now_epoch)
            filtered = []
            for b in buckets:
                gk = b.get("groupKey")
                if gk is not None:
                    if gk == target_group:
                        filtered.append(b)
                else:
                    is_3p = ("3P" in str(b.get("group", ""))) or ("3p" in str(b.get("id", "")))
                    if (target_group == "third_party" and is_3p) or (
                        target_group == "gemini" and not is_3p
                    ):
                        filtered.append(b)
            buckets = filtered
        if not buckets:
            return None
        pcts = [
            max(0, min(100, int(round(float(b.get("remainingFraction", 0.0)) * 100.0))))
            for b in buckets
        ]
        return min(pcts) if pcts else None

    def collect_waiting_notifications(self, now_epoch=None):
        if now_epoch is None:
            now_epoch = time.time()
        alerts = []
        enabled_set = set(self.enabled_providers)
        for s in self.all_sessions:
            prov = s.get("provider")
            if prov not in enabled_set:
                continue
            if self.effective_status(s, now_epoch) == "waiting":
                key = "{}|{}|{}".format(
                    s.get("id", ""),
                    s.get("waitingReason", ""),
                    int(float(s.get("statusChangedAt") or 0)),
                )
                if key not in self.notified_waiting_keys:
                    self.notified_waiting_keys.add(key)
                    alerts.append((prov, s))
        return alerts

    def collect_low_quota_notifications(self, snapshot):
        prov = snapshot.get("provider")
        if prov not in self.enabled_providers:
            return []
        alerts = []
        for b in snapshot.get("buckets") or []:
            if b.get("disabled") is True:
                continue
            pct = max(0, min(100, int(round(float(b.get("remainingFraction", 0.0)) * 100.0))))
            if pct < 20:
                key = "{}|{}|{}".format(prov, b.get("id", ""), b.get("resetTime", ""))
                if key not in self.notified_low_quota_keys:
                    self.notified_low_quota_keys.add(key)
                    alerts.append((prov, b, pct))
        return alerts

    def dismiss_session(self, session_id):
        self._mutate_state(lambda st: st.setdefault("sessions", {}).pop(session_id, None))
        self.load_state()

    def clear_all_sessions(self):
        self._mutate_state(lambda st: st.__setitem__("sessions", {}))
        self.load_state()

    def _mutate_state(self, mutator):
        os.makedirs(self.monitor_dir, exist_ok=True)
        with open(self.lock_path, "a+", encoding="utf-8") as lock_file:
            _acquire_lock(lock_file, self.lock_path)
            try:
                state = {"updatedAt": time.time(), "sessions": {}}
                if os.path.exists(self.state_path):
                    try:
                        with open(self.state_path, "r", encoding="utf-8") as sf:
                            loaded = json.load(sf)
                        if isinstance(loaded, dict):
                            state = loaded
                    except Exception:
                        pass
                mutator(state)
                state["updatedAt"] = time.time()
                atomic_write_json(self.state_path, state)
            finally:
                _release_lock(lock_file)

    def build_status_json(self, now_epoch=None):
        if now_epoch is None:
            now_epoch = time.time()
        providers_out = {}
        for prov in self.enabled_providers:
            providers_out[prov] = {
                "tag": PROVIDER_META[prov]["short_tag"],
                "displayName": PROVIDER_META[prov]["display_name"],
                "status": self.status_by_provider.get(prov, "idle"),
                "percent": self.menu_bar_percent(prov, now_epoch),
                "activeSessions": len(self.non_idle_sessions(prov, now_epoch)),
                "quota": self.quotas_by_provider.get(prov),
            }
        return {
            "enabledProviders": list(self.enabled_providers),
            "language": self.app_language,
            "providers": providers_out,
        }
