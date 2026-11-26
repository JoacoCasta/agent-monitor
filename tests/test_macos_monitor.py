import glob
import json
import os
import plistlib
import py_compile
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "Scripts")
SOURCES_DIR = os.path.join(REPO_ROOT, "Sources")
RESOURCES_DIR = os.path.join(REPO_ROOT, "Resources")
LOGOS_DIR = os.path.join(REPO_ROOT, "assets", "logos")
PROVIDERS = ("antigravity", "codex", "claude", "copilot")


class MacOSMonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.fake_home = self.tmp_dir.name
        self.env = os.environ.copy()
        self.env["HOME"] = self.fake_home
        self.env["USERPROFILE"] = self.fake_home
        self.env["CODEX_HOME"] = os.path.join(self.fake_home, ".codex")
        self.env["COPILOT_HOME"] = os.path.join(self.fake_home, ".copilot")
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

    def test_scripts_compile_cleanly(self):
        for py_path in sorted(glob.glob(os.path.join(SCRIPTS_DIR, "*.py"))):
            py_compile.compile(py_path, doraise=True)

    def test_hook_handler_all_providers(self):
        # Antigravity PreToolUse -> allow contract
        r1 = self._run_script(
            "hook-handler.py",
            ["antigravity", "PreToolUse"],
            json.dumps(
                {
                    "hookEventName": "PreToolUse",
                    "conversationId": "ag-1",
                    "modelName": "gemini-4-neon-xhigh",
                    "workspacePaths": ["/Users/dev/projects/my-app"],
                    "toolCall": {"name": "run_command", "args": {}},
                }
            ),
        )
        self.assertEqual(r1.returncode, 0, r1.stderr)
        self.assertEqual(json.loads(r1.stdout), {"decision": "allow"})

        # Codex AskUserQuestion -> waiting state
        r2 = self._run_script(
            "hook-handler.py",
            ["codex", "PreToolUse"],
            json.dumps(
                {
                    "hook_event_name": "PreToolUse",
                    "session_id": "cx-1",
                    "model": "gpt-6-luna",
                    "cwd": "/",
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
                    "cwd": "/Users/dev/proj-cc",
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
                    "cwd": "/Users/dev/proj-cc",
                }
            ),
        )
        self.assertEqual(r4.returncode, 0)

        # Malformed JSON must still exit 0 and obey Stop contract
        r5 = self._run_script("hook-handler.py", ["antigravity", "Stop"], "{broken")
        self.assertEqual(r5.returncode, 0)
        self.assertEqual(json.loads(r5.stdout), {"decision": "stop"})

        # Copilot camelCase hooks: ask_user -> waiting_question, permissionRequest -> waiting_permission, agentStop -> idle
        r_cp1 = self._run_script(
            "hook-handler.py",
            ["copilot", "preToolUse"],
            json.dumps(
                {
                    "hookEventName": "preToolUse",
                    "sessionId": "cp-1",
                    "cwd": "/Users/dev/proj-cp",
                    "toolName": "ask_user",
                    "toolArgs": json.dumps({"question": "Proceed?"}),
                }
            ),
        )
        self.assertEqual(r_cp1.returncode, 0, r_cp1.stderr)

        r_cp2 = self._run_script(
            "hook-handler.py",
            ["copilot", "permissionRequest"],
            json.dumps(
                {
                    "hookEventName": "permissionRequest",
                    "sessionId": "cp-2",
                    "cwd": "/Users/dev/proj-cp",
                }
            ),
        )
        self.assertEqual(r_cp2.returncode, 0, r_cp2.stderr)

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

        cp1 = state["sessions"]["copilot:cp-1"]
        self.assertEqual(cp1["status"], "waiting")
        self.assertEqual(cp1["detailKey"], "waiting_question")
        self.assertEqual(cp1["workspace"], "proj-cp")

        cp2 = state["sessions"]["copilot:cp-2"]
        self.assertEqual(cp2["status"], "waiting")
        self.assertEqual(cp2["detailKey"], "waiting_permission")

    def test_claude_statusline_and_configure_hooks_roundtrip(self):
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

        os.makedirs(os.path.join(self.fake_home, ".copilot", "hooks"), exist_ok=True)
        with open(os.path.join(self.fake_home, ".copilot", "hooks", "custom-hook.json"), "w", encoding="utf-8") as f:
            json.dump({"version": 1, "hooks": {}}, f)

        res_en = self._run_script("configure-hooks.py", ["sync", "antigravity,codex,claude,copilot"])
        self.assertEqual(res_en.returncode, 0, res_en.stderr)
        status_obj = json.loads(res_en.stdout)
        self.assertTrue(status_obj["antigravity"]["hooksInstalled"])
        self.assertTrue(status_obj["codex"]["hooksInstalled"])
        self.assertTrue(status_obj["claude"]["hooksInstalled"])
        self.assertTrue(status_obj["copilot"]["hooksInstalled"])

        cp_hook_path = os.path.join(self.fake_home, ".copilot", "hooks", "agent-monitor.json")
        self.assertTrue(os.path.isfile(cp_hook_path))
        with open(cp_hook_path, "r", encoding="utf-8") as f:
            cp_cfg = json.load(f)
        self.assertEqual(cp_cfg["version"], 1)
        self.assertIn("preToolUse", cp_cfg["hooks"])

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

        self.assertFalse(os.path.exists(cp_hook_path))
        self.assertTrue(os.path.exists(os.path.join(self.fake_home, ".copilot", "hooks", "custom-hook.json")))

    def test_parse_copilot_quota(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("fetch_quota", os.path.join(SCRIPTS_DIR, "fetch-quota.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Pro plan: finite premium_interactions + unlimited chat/completions -> returns only premium_interactions
        now_ts = 1795700000
        buckets = mod.parse_copilot_quota(
            {
                "quotaSnapshots": {
                    "chat": {"isUnlimitedEntitlement": True, "remainingPercentage": 100, "resetDate": "2026-11-26T14:00:00Z"},
                    "completions": {"isUnlimitedEntitlement": True, "remainingPercentage": 100},
                    "premium_interactions": {
                        "isUnlimitedEntitlement": False,
                        "entitlementRequests": 200,
                        "usedRequests": 50,
                        "remainingPercentage": 75,
                        "resetDate": "2026-12-01T00:00:00Z",
                    },
                }
            },
            now_epoch=now_ts,
        )
        self.assertEqual(len(buckets), 1)
        b = buckets[0]
        self.assertEqual(b["groupKey"], "copilot")
        self.assertEqual(b["windowKind"], "premium")
        self.assertAlmostEqual(b["remainingFraction"], 0.75, places=4)
        self.assertEqual(b["usedRequests"], 50)
        self.assertEqual(b["entitlementRequests"], 200)
        self.assertFalse(b["isWeekly"])
        self.assertTrue(b["resetInSeconds"] > 0)

        # Equal/non-future resetDate must clear resetTime/resetInSeconds
        b_same = mod.parse_copilot_quota(
            {
                "quotaSnapshots": {
                    "premium_interactions": {
                        "isUnlimitedEntitlement": False,
                        "entitlementRequests": 200,
                        "usedRequests": 0,
                        "remainingPercentage": 100,
                        "resetDate": "2026-11-26T13:33:20Z",
                    }
                }
            },
            now_epoch=1795700000,
        )
        self.assertEqual(b_same[0]["resetTime"], "")
        self.assertEqual(b_same[0]["resetInSeconds"], 0)

    def test_official_svg_logos_match_swift_paths_1_to_1(self):
        with open(os.path.join(SOURCES_DIR, "ProviderLogo.swift"), "r", encoding="utf-8") as f:
            swift_src = f.read()

        for prov in PROVIDERS:
            svg_path = os.path.join(LOGOS_DIR, "{}.svg".format(prov))
            self.assertTrue(os.path.isfile(svg_path), "Missing SVG: {}".format(svg_path))

            tree = ET.parse(svg_path)
            root = tree.getroot()
            self.assertTrue(root.tag.endswith("svg"), "Unexpected root tag: {}".format(root.tag))
            self.assertEqual(root.attrib.get("viewBox"), "0 0 24 24")
            self.assertEqual(root.attrib.get("fill"), "currentColor")

            paths = [elem for elem in root.iter() if elem.tag.endswith("path")]
            self.assertGreaterEqual(len(paths), 1, "No <path> found in {}".format(svg_path))
            d_attr = paths[0].attrib.get("d", "").strip()
            self.assertTrue(d_attr, "Empty <path d> in {}".format(svg_path))

            m = re.search(rf'private static let {prov}SVGPath = "([^"]+)"', swift_src)
            self.assertIsNotNone(m, "Missing {}SVGPath in ProviderLogo.swift".format(prov))
            self.assertEqual(m.group(1), d_attr, "Swift path differs from {}.svg".format(prov))

    def test_retina_bitmap_ctm_ordering(self):
        for fname in ("ProviderLogo.swift", "AppDelegate.swift"):
            with open(os.path.join(SOURCES_DIR, fname), "r", encoding="utf-8") as f:
                src = f.read()
            pos_size = src.find("rep.size = NSSize(")
            pos_ctx = src.find("NSGraphicsContext(bitmapImageRep: rep)")
            self.assertGreater(pos_size, -1, "Missing rep.size assignment in {}".format(fname))
            self.assertGreater(pos_ctx, -1, "Missing NSGraphicsContext(bitmapImageRep: rep) in {}".format(fname))
            self.assertLess(
                pos_size,
                pos_ctx,
                "rep.size must be set BEFORE NSGraphicsContext(bitmapImageRep: rep) in {}".format(fname),
            )

    def test_info_plist_and_app_icon_and_swift_constraints(self):
        plist_path = os.path.join(RESOURCES_DIR, "Info.plist")
        with open(plist_path, "rb") as f:
            plist = plistlib.load(f)
        self.assertRegex(str(plist.get("CFBundleShortVersionString", "")), r"^\d+\.\d+\.\d+$")
        self.assertEqual(plist.get("CFBundleIconFile"), "AppIcon")
        self.assertIs(plist.get("LSUIElement"), True)

        icns_path = os.path.join(RESOURCES_DIR, "AppIcon.icns")
        self.assertTrue(os.path.isfile(icns_path), "Missing Resources/AppIcon.icns")
        with open(icns_path, "rb") as f:
            magic = f.read(4)
        self.assertEqual(magic, b"icns")

        forbidden = re.compile(r"@State\b|@Observable\b|#Preview\b")
        for swift_path in sorted(glob.glob(os.path.join(SOURCES_DIR, "*.swift"))):
            with open(swift_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIsNone(
                forbidden.search(content),
                "Forbidden Swift macro/@State/@Observable found in {}".format(swift_path),
            )


if __name__ == "__main__":
    unittest.main()
