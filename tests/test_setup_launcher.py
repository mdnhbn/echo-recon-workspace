import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import Mock, patch

from echo_recon.locking import InstanceLock
from echo_recon.setup_launcher import SetupLauncher
from echo_recon.web import create_app


class SetupLauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.data = self.root / "data"
        self.data.mkdir()
        (self.root / "setup_tools.py").write_text("# test fixture", encoding="utf-8")
        self.launcher = SetupLauncher(self.root, self.data)

    def tearDown(self):
        self.tmp.cleanup()

    def test_fixed_terminal_command_and_duplicate_refusal(self):
        process = Mock()
        process.poll.return_value = None
        with patch("echo_recon.setup_launcher.is_kali", return_value=True), \
                patch.dict(os.environ, {"DISPLAY": ":0"}), \
                patch("echo_recon.setup_launcher.shutil.which", return_value="/usr/bin/qterminal"), \
                patch("echo_recon.setup_launcher.subprocess.Popen", return_value=process) as launch:
            self.assertTrue(self.launcher.launch()["launched"])
            args = launch.call_args.args[0]
            self.assertEqual(args[-5:], [str(self.root / "setup_tools.py"), "--install", "--pause",
                                         "--data-dir", str(self.data)])
            self.assertNotIn("sudo", args)
            self.assertNotIn("shell", launch.call_args.kwargs)
            self.assertEqual(launch.call_args.kwargs["cwd"], self.root)
            with self.assertRaisesRegex(RuntimeError, "already open"):
                self.launcher.launch()
            self.assertEqual(launch.call_count, 1)

    def test_installer_lock_blocks_launch(self):
        lock = InstanceLock(self.data / "setup-tools.lock").acquire()
        try:
            self.assertTrue(self.launcher.busy())
        finally:
            lock.release()
        self.assertFalse(self.launcher.busy())

    def test_unsupported_platform_and_headless_fallback(self):
        with patch("echo_recon.setup_launcher.is_kali", return_value=False):
            with self.assertRaisesRegex(ValueError, "Kali Linux"):
                self.launcher.launch()
        with patch("echo_recon.setup_launcher.is_kali", return_value=True), patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "setup_tools.py --install"):
                self.launcher.launch()


class SetupRouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app(self.tmp.name, testing=True)
        self.client = self.app.test_client()
        page = self.client.get("/").text
        self.csrf = re.search('name="csrf-token" content="([a-f0-9]+)"', page)[1]
        self.headers = {"X-CSRF-Token": self.csrf}

    def tearDown(self):
        self.app.extensions["echo_manager"].close()
        self.tmp.cleanup()

    def test_setup_is_csrf_protected_and_accepts_no_commands(self):
        launcher = self.app.extensions["echo_setup"]
        with patch.object(launcher, "launch", return_value={"launched": True}) as launch:
            self.assertEqual(self.client.post("/api/setup-tools", json={}).status_code, 403)
            self.assertEqual(self.client.post("/api/setup-tools", json={"command": "anything"}, headers=self.headers).status_code, 400)
            self.assertEqual(self.client.post("/api/setup-tools", json={}, headers={**self.headers, "Origin": "https://elsewhere.invalid"}).status_code, 403)
            self.assertEqual(self.client.post("/api/setup-tools", json={}, headers=self.headers).status_code, 202)
            launch.assert_called_once_with()

    def test_assessment_and_setup_cannot_start_together(self):
        launcher = self.app.extensions["echo_setup"]
        manager = self.app.extensions["echo_manager"]
        with patch.object(launcher, "launch") as launch:
            manager.active["fixture"] = Mock()
            try:
                self.assertEqual(self.client.post("/api/setup-tools", json={}, headers=self.headers).status_code, 409)
                launch.assert_not_called()
            finally:
                manager.active.clear()
        with patch.object(launcher, "busy", return_value=True), patch.object(manager, "start") as start:
            self.assertEqual(self.client.post("/api/jobs", json={}, headers=self.headers).status_code, 409)
            start.assert_not_called()

    def test_guidance_and_theme_hooks_render_without_creating_history(self):
        page = self.client.get("/").text
        for content in ['id="theme-toggle"', 'id="usage-guide"', 'id="guide-rate"',
                        'id="guide-time"', 'data-setup-tools', '৫৬ মিনিট', '/static/theme.js']:
            self.assertTrue(content in page, f"Missing guide content: {content}")
        self.assertEqual(self.client.get("/api/jobs").json, [])


if __name__ == "__main__":
    unittest.main()
