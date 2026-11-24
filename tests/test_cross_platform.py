import datetime
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
DESKTOP_DIR = os.path.join(REPO_ROOT, "desktop")

if DESKTOP_DIR not in sys.path:
    sys.path.insert(0, DESKTOP_DIR)

from core import MonitorCore
from i18n import L10n, SUPPORTED_LANGUAGES


class CrossPlatformTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.fake_home = self.tmp_dir.name
        self.env = os.environ.copy()
        self.env["HOME"] = self.fake_home
        self.env["USERPROFILE"] = self.fake_home
        self.env["CODEX_HOME"] = os.path.join(self.fake_home, ".codex")
        self.env["AGENT_MONITOR_PYTHON"] = sys.executable

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _run_script(self, script_name, args, stdin_data=""):
        script_path = os.path.join(SCRIPTS_DIR, script_name)
        return subprocess.run(
            [sys.executable, script_path] + list(args),
            input=stdin_data,
            text=True,
            capture_output=True,
            env=self.env,
            timeout=15,
        )

    def test_hook_handler_all_providers_and_windows_paths(self):
        # Antigravity PreToolUse -> allow contract + Windows path normalization
        r1 = self._run_script(
            "hook-handler.py",
            ["antigravity", "PreToolUse"],
            json.dumps(
                {
                    "hookEventName": "PreToolUse",
                    "conversationId": "ag-1",
                    "modelName": "gemini-4-neon-xhigh",
                    "workspacePaths": ["C:\\Users\\Dev\\my-app"],
                    "toolCall": {"name": "run_command", "args": {}},
                }
            ),
        )
        self.assertEqual(r1.returncode, 0, r1.stderr)
        self.assertEqual(json.loads(r1.stdout), {"decision": "allow"})

        # Codex AskUserQuestion -> waiting + root drive ignored
        r2 = self._run_script(
            "hook-handler.py",
            ["codex", "PreToolUse"],
            json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "session_id": "cx-1",
                    "model": "gpt-6-luna",
                    "cwd": "C:\\",
                    "tool_name": "AskUserQuestion",
                    "tool_input": {},
                }
            ),
        )
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertEqual(r2.stdout.strip(), "")

        # Claude idle_prompt Notification ignored; permission_prompt sets waiting
        r3 = self._run_script(
            "hook-handler.py",
            ["claude", "Notification"],
            json.dumps(
                {
                    "hook_event_name": "Notification",
                    "session_id": "cc-1",
                    "notification_type": "idle_prompt",
                    "cwd": "/home/dev/proj-cc",
                }
            ),
        )
        self.assertEqual(r3.returncode, 0)

        r4 = self._run_script(
            "hook-handler.py",
            ["claude", "Notification"],
            json.dumps(
                {
                    "hook_event_name": "Notification",
                    "session_id": "cc-1",
                    "notification_type": "permission_prompt",
                    "cwd": "/home/dev/proj-cc",
                }
            ),
        )
        self.assertEqual(r4.returncode, 0)

        # Malformed JSON must still exit 0 and obey Stop contract
        r5 = self._run_script("hook-handler.py", ["antigravity", "Stop"], "{broken")
        self.assertEqual(r5.returncode, 0)
        self.assertEqual(json.loads(r5.stdout), {"decision": "stop"})

        state_path = os.path.join(self.fake_home, ".gemini", "agent-monitor", "state.json")
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)

        ag = state["sessions"]["antigravity:ag-1"]
        self.assertEqual(ag["workspace"], "my-app")
        self.assertEqual(ag["detailKey"], "running_tool")
        self.assertEqual(ag["detailArg"], "run_command")

        cx = state["sessions"]["codex:cx-1"]
        self.assertEqual(cx["status"], "waiting")
        self.assertEqual(cx["workspace"], "")
        self.assertEqual(cx["detailKey"], "waiting_question")

        cc = state["sessions"]["claude:cc-1"]
        self.assertEqual(cc["status"], "waiting")
        self.assertEqual(cc["detailKey"], "waiting_permission")

    def test_claude_statusline_and_configure_hooks_roundtrip(self):
        # Pre-seed user configs
        os.makedirs(os.path.join(self.fake_home, ".gemini", "config"), exist_ok=True)
        with open(os.path.join(self.fake_home, ".gemini", "config", "hooks.json"), "w", encoding="utf-8") as f:
            json.dump({"custom-user-hook": {"enabled": True, "Stop": []}}, f)

        os.makedirs(os.path.join(self.fake_home, ".claude"), exist_ok=True)
        with open(os.path.join(self.fake_home, ".claude", "settings.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "permissions": {"allow": ["Bash(ls)"]},
                    "statusLine": {"type": "command", "command": "echo PREV_STATUSLINE"},
                },
                f,
            )

        res_en = self._run_script("configure-hooks.py", ["sync", "antigravity,codex,claude"])
        self.assertEqual(res_en.returncode, 0, res_en.stderr)
        status_obj = json.loads(res_en.stdout)
        self.assertTrue(status_obj["antigravity"]["hooksInstalled"])
        self.assertTrue(status_obj["codex"]["hooksInstalled"])
        self.assertTrue(status_obj["claude"]["hooksInstalled"])

        sl_payload = json.dumps(
            {
                "model": {"display_name": "Claude Opus"},
                "rate_limits": {
                    "five_hour": {"used_percentage": 20.0, "resets_at": 1796000000},
                    "seven_day": {"used_percentage": 85.0, "resets_at": 1796500000},
                },
            }
        )
        sl_res = self._run_script("claude-statusline.py", [], sl_payload)
        self.assertEqual(sl_res.returncode, 0, sl_res.stderr)
        self.assertIn("PREV_STATUSLINE", sl_res.stdout)

        cq_path = os.path.join(self.fake_home, ".gemini", "agent-monitor", "claude-quota.json")
        with open(cq_path, "r", encoding="utf-8") as f:
            cq = json.load(f)
        self.assertEqual(cq["buckets"][0]["windowKind"], "5h")
        self.assertAlmostEqual(cq["buckets"][0]["remainingFraction"], 0.80, places=4)
        self.assertEqual(cq["buckets"][1]["windowKind"], "weekly")
        self.assertAlmostEqual(cq["buckets"][1]["remainingFraction"], 0.15, places=4)

        # Disable all -> verify lossless restoration
        res_dis = self._run_script("configure-hooks.py", ["sync", ""])
        self.assertEqual(res_dis.returncode, 0, res_dis.stderr)

        with open(os.path.join(self.fake_home, ".claude", "settings.json"), "r", encoding="utf-8") as f:
            cl = json.load(f)
        self.assertEqual(cl["statusLine"]["command"], "echo PREV_STATUSLINE")
        self.assertEqual(cl["permissions"], {"allow": ["Bash(ls)"]})
        self.assertNotIn("hooks", cl)
        self.assertFalse(os.path.exists(os.path.join(self.fake_home, ".codex", "hooks.json")))

        with open(os.path.join(self.fake_home, ".gemini", "config", "hooks.json"), "r", encoding="utf-8") as f:
            ag = json.load(f)
        self.assertIn("custom-user-hook", ag)
        self.assertNotIn("agent-monitor", ag)

    def test_i18n_all_seven_languages(self):
        now_dt = datetime.datetime(2026, 11, 24, 15, 0, 0, tzinfo=datetime.timezone.utc)
        future_dt = now_dt + datetime.timedelta(hours=3, minutes=25)
        for lang in SUPPORTED_LANGUAGES:
            t = L10n(lang)
            for st in ("waiting", "active", "idle"):
                self.assertTrue(t.status_title(st))
            self.assertTrue(t.choose_agents_title)
            self.assertTrue(t.settings_title)
            self.assertTrue(t.session_detail("running_tool", "Bash", "Running Bash"))
            self.assertTrue(t.bucket_label({"windowKind": "5h"}))
            self.assertTrue(t.bucket_label({"windowKind": "weekly"}))
            self.assertTrue(t.bucket_label({"windowKind": "monthly"}))
            cd = t.format_countdown(future_dt, 0, now_dt, now_dt)
            self.assertTrue(cd)
            self.assertTrue(t.resets_in_text(cd))
            self.assertTrue(t.format_reset_clock(future_dt, is_weekly=True))
            self.assertTrue(t.format_elapsed(1000, 1120))

    def test_monitor_core_priority_and_status_json(self):
        mon_dir = os.path.join(self.fake_home, ".gemini", "agent-monitor")
        os.makedirs(mon_dir, exist_ok=True)
        now = time.time()
        with open(os.path.join(mon_dir, "state.json"), "w", encoding="utf-8") as f:
            json.dump(
                {
                    "updatedAt": now,
                    "sessions": {
                        "antigravity:1": {
                            "id": "antigravity:1",
                            "provider": "antigravity",
                            "sessionId": "1",
                            "status": "active",
                            "detail": "Thinking...",
                            "detailKey": "thinking",
                            "detailArg": "",
                            "waitingReason": "",
                            "pendingFeedback": False,
                            "modelName": "claude-opus-5-5-high",
                            "workspace": "proj",
                            "updatedAt": now,
                            "statusChangedAt": now,
                        },
                        "antigravity:2": {
                            "id": "antigravity:2",
                            "provider": "antigravity",
                            "sessionId": "2",
                            "status": "waiting",
                            "detail": "Waiting for answer",
                            "detailKey": "waiting_question",
                            "detailArg": "",
                            "waitingReason": "question",
                            "pendingFeedback": False,
                            "modelName": "gemini-4-neon-high",
                            "workspace": "proj2",
                            "updatedAt": now - 5,
                            "statusChangedAt": now - 5,
                        },
                    },
                },
                f,
            )

        core = MonitorCore(mon_dir)
        # Yellow > Red priority
        self.assertEqual(core.status_by_provider["antigravity"], "waiting")
        # Prioritized waiting session uses Gemini model
        self.assertEqual(core.active_antigravity_group_key(now), "gemini")

        js = core.build_status_json(now)
        self.assertIn("providers", js)
        self.assertEqual(js["providers"]["antigravity"]["status"], "waiting")
        self.assertEqual(js["providers"]["antigravity"]["activeSessions"], 2)


if __name__ == "__main__":
    unittest.main()
