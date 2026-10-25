import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from echo_recon.locking import InstanceLock
from echo_recon.setup_launcher import SetupLauncher
from echo_recon.web import create_app


class SetupLauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="echo setup ")
        self.root = Path(self.tmp.name).resolve()
        self.data = self.root / "data"
        self.data.mkdir()
        (self.root / "setup_tools.py").write_text("# test fixture", encoding="utf-8")
        (self.root / "setup_tools_windows.py").write_text("# test fixture", encoding="utf-8")
        self.launcher = SetupLauncher(self.root, self.data)

    def tearDown(self):
        self.tmp.cleanup()

    def test_fixed_terminal_command_and_duplicate_refusal(self):
        process = Mock()
        process.poll.return_value = None
        with patch("echo_recon.setup_launcher.sys.platform", "linux"), \
                patch("echo_recon.setup_launcher.is_kali", return_value=True), \
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

    def test_startup_check_blocks_overlap_and_preserves_message(self):
        self.assertTrue(self.launcher.begin_startup_check())
        self.assertFalse(self.launcher.begin_startup_check())
        self.assertTrue(self.launcher.busy())
        self.assertTrue(self.launcher.status()["checking"])
        with self.assertRaisesRegex(RuntimeError, "already open"):
            self.launcher.launch()
        self.launcher.finish_startup_check("Tools already ready")
        self.assertFalse(self.launcher.busy())
        self.assertEqual(self.launcher.status()["message"], "Tools already ready")

    def test_gnome_and_kde_use_direct_argv_and_wait_for_installer(self):
        for terminal, flags in [
            ("gnome-terminal", ["--wait", "--title=Echo Recon — tool setup", "--"]),
            ("konsole", ["--separate", "-e"]),
        ]:
            with self.subTest(terminal=terminal):
                launcher = SetupLauncher(self.root, self.data)
                process = Mock()
                process.poll.return_value = None
                def find(name):
                    return f"/usr/bin/{terminal}" if name == terminal else None
                with patch("echo_recon.setup_launcher.sys.platform", "linux"), patch.dict(os.environ, {"DISPLAY": ":0"}), patch("echo_recon.setup_launcher.shutil.which", side_effect=find), patch("echo_recon.setup_launcher.subprocess.Popen", return_value=process) as launch:
                    launcher.launch()
                self.assertEqual(launch.call_args.args[0][:1+len(flags)], [f"/usr/bin/{terminal}", *flags])
                self.assertEqual(launch.call_args.args[0][-5:], [str(self.root / "setup_tools.py"), "--install", "--pause", "--data-dir", str(self.data)])
                self.assertNotIn("shell", launch.call_args.kwargs)

    def test_installer_lock_blocks_launch(self):
        lock = InstanceLock(self.data / "setup-tools.lock").acquire()
        try:
            self.assertTrue(self.launcher.busy())
        finally:
            lock.release()
        self.assertFalse(self.launcher.busy())

    def test_unsupported_platform_and_headless_fallback(self):
        with patch("echo_recon.setup_launcher.sys.platform", "freebsd14"), patch("echo_recon.setup_launcher.is_kali", return_value=False):
            with self.assertRaisesRegex(ValueError, "supported Linux"):
                self.launcher.launch()
        with patch("echo_recon.setup_launcher.sys.platform", "linux"), patch("echo_recon.setup_launcher.is_kali", return_value=True), patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as caught:
                self.launcher.launch()
            self.assertIn(str(self.root / "setup_tools.py"), str(caught.exception))
            self.assertIn("--data-dir", str(caught.exception))

    def test_windows_fixed_hidden_worker_logs_and_duplicate_refusal(self):
        process = Mock()
        process.poll.return_value = None
        def launch_worker(args, **options):
            options["stdout"].write(b"<script>plain log text</script>\n")
            return process
        with patch("echo_recon.setup_launcher.sys.platform", "win32"), \
                patch.dict(os.environ, {"PATH": "untouched path"}, clear=True), \
                patch("echo_recon.setup_launcher.subprocess.Popen", side_effect=launch_worker) as launch:
            result = self.launcher.launch()
            self.assertTrue(result["launched"])
            args, options = launch.call_args.args[0], launch.call_args.kwargs
            self.assertEqual(args, [sys.executable, str(self.root / "setup_tools_windows.py"),
                                    "--install", "--data-dir", str(self.data)])
            self.assertFalse(options["shell"])
            self.assertEqual(options["cwd"], self.root)
            self.assertEqual(options["creationflags"], getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000))
            self.assertEqual(options["stdin"], subprocess.DEVNULL)
            self.assertEqual(options["stderr"], subprocess.STDOUT)
            self.assertEqual(options["env"]["PATH"], "untouched path")
            self.assertEqual(options["env"]["PYTHONUNBUFFERED"], "1")
            self.assertEqual(os.environ["PATH"], "untouched path")
            self.assertNotIn("PYTHONUNBUFFERED", os.environ)
            self.assertTrue(options["stdout"].closed)
            self.assertEqual(self.launcher.log_path.parent, self.data / "setup-logs")
            status = self.launcher.status()
            self.assertTrue(status["running"])
            self.assertIsNone(status["exit_code"])
            self.assertEqual(status["log"], "<script>plain log text</script>\n")
            with self.assertRaisesRegex(RuntimeError, "already open"):
                self.launcher.launch()
            launch.assert_called_once()
            old_log = self.launcher.log_path
            process.poll.return_value = 0
            self.assertIn("successfully", self.launcher.status()["message"])
            self.launcher.launch()
            self.assertNotEqual(self.launcher.log_path, old_log)

    def test_windows_missing_installer_never_starts_a_process(self):
        (self.root / "setup_tools_windows.py").unlink()
        with patch("echo_recon.setup_launcher.sys.platform", "win32"), \
                patch("echo_recon.setup_launcher.subprocess.Popen") as launch:
            with self.assertRaisesRegex(ValueError, "Windows installer file is missing"):
                self.launcher.launch()
            launch.assert_not_called()
        self.assertFalse((self.data / "setup-logs").exists())

    def test_status_reports_idle_running_and_exit_results(self):
        self.assertEqual(self.launcher.status(), {"running": False, "exit_code": None,
                         "message": "No tool setup is running.", "log": ""})
        process = Mock()
        self.launcher.process = process
        self.launcher.log_path = self.data / "status.log"
        self.launcher.log_path.write_text("status fixture", encoding="utf-8")
        for code, message in [(None, "running"), (0, "successfully"),
                              (2, "manual action"), (1, "failed")]:
            with self.subTest(code=code):
                process.poll.return_value = code
                status = self.launcher.status()
                self.assertEqual(status["running"], code is None)
                self.assertEqual(status["exit_code"], code)
                self.assertIn(message, status["message"])

    def test_linux_terminal_exit_does_not_claim_installer_success(self):
        self.launcher.process = Mock()
        self.launcher.process.poll.return_value = 0
        status = self.launcher.status()
        self.assertFalse(status["running"])
        self.assertIn("terminal closed", status["message"])
        self.assertNotIn("success", status["message"])

    def test_status_reads_only_bounded_log_tail(self):
        log = self.data / "bounded.log"
        log.write_bytes(b"hidden prefix" + b"x" * (60 * 1024) + b"visible end")
        self.launcher.log_path = log
        original_open = Path.open
        reads = []
        class Reader:
            def __init__(self, stream):
                self.stream = stream
            def __enter__(self):
                return self
            def __exit__(self, *args):
                self.stream.close()
            def seek(self, *args):
                return self.stream.seek(*args)
            def tell(self):
                return self.stream.tell()
            def read(self, count):
                reads.append((self.stream.tell(), count))
                return self.stream.read(count)
        def open_bounded(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            return Reader(stream) if path == log else stream
        with patch.object(Path, "open", open_bounded):
            output = self.launcher.status()["log"]
        self.assertNotIn("hidden prefix", output)
        self.assertTrue(output.endswith("visible end"))
        self.assertEqual(reads, [(len(b"hidden prefixvisible end"), 60 * 1024)])
        self.assertLessEqual(len(output), 60 * 1024 + 50)


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

    def test_setup_status_is_read_only_and_local(self):
        launcher = self.app.extensions["echo_setup"]
        result = {"running": True, "exit_code": None, "message": "running", "log": "<b>literal output</b>"}
        with patch.object(launcher, "status", return_value=result) as status, \
                patch.object(launcher, "launch") as launch:
            response = self.client.get("/api/setup-status")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json, result)
            self.assertEqual(self.client.get("/api/setup-status", headers={"Host": "elsewhere.invalid"}).status_code, 403)
            self.assertEqual(self.client.get("/api/setup-status", environ_overrides={"REMOTE_ADDR": "192.168.1.5"}).status_code, 403)
            status.assert_called_once_with()
            launch.assert_not_called()

    def test_setup_launch_failure_uses_platform_neutral_error(self):
        launcher = self.app.extensions["echo_setup"]
        with patch.object(launcher, "launch", side_effect=OSError("fixture failure")):
            response = self.client.post("/api/setup-tools", json={}, headers=self.headers)
            self.assertEqual(response.status_code, 400)
            self.assertIn("your platform", response.json["error"])
            self.assertNotIn("Kali terminal", response.json["error"])

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
                        'id="guide-time"', 'data-setup-tools', 'No scan timer is set by Echo Recon', '/static/theme.js']:
            self.assertTrue(content in page, f"Missing guide content: {content}")
        self.assertEqual(self.client.get("/api/jobs").json, [])


if __name__ == "__main__":
    unittest.main()
