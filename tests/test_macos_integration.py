"""macOS platform routing and a native local-server smoke check; no scan targets."""
import os
import http.client
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

from echo_recon import __version__, tools
from echo_recon.browser import has_desktop
from echo_recon.runner import run
from echo_recon.setup_launcher import SetupLauncher
from echo_recon.web import create_app


ROOT = Path(__file__).resolve().parents[1]


class MacOSIntegrationTests(unittest.TestCase):
    def test_native_macos_desktop_does_not_require_x11_but_ssh_is_headless(self):
        with patch("echo_recon.browser.sys.platform", "darwin"), patch.dict(os.environ, {}, clear=True):
            self.assertTrue(has_desktop())
            with patch.dict(os.environ, {"SSH_CONNECTION": "fixture"}):
                self.assertFalse(has_desktop())
            with patch.dict(os.environ, {"SSH_TTY": "fixture"}):
                self.assertFalse(has_desktop())

    def test_both_native_homebrew_paths_resolve_to_explicit_tool_arguments(self):
        for arch, prefix in [("arm64", "/opt/homebrew"), ("x86_64", "/usr/local")]:
            with self.subTest(arch=arch), patch.object(tools, "is_windows", return_value=False), \
                 patch.object(tools.sys, "platform", "darwin"), \
                 patch.object(tools.platform, "machine", return_value=arch), \
                 patch.object(tools.shutil, "which", return_value=prefix + "/bin/nmap") as which:
                before = os.environ.get("PATH")
                self.assertEqual(tools.resolve_tool("nmap"), (prefix + "/bin/nmap",))
                self.assertIn(prefix + "/bin", which.call_args.kwargs["path"])
                self.assertEqual(tools.command("nmap", "example.com", 2, Path("unused"))[0], prefix + "/bin/nmap")
                self.assertEqual(os.environ.get("PATH"), before)

    def test_setup_worker_runs_without_linux_display_or_osascript(self):
        with tempfile.TemporaryDirectory(prefix="echo mac setup ") as folder:
            root = Path(folder).resolve()
            data = root / "data"
            data.mkdir()
            (root / "setup_tools_macos.py").write_text("# inert fixture", encoding="utf-8")
            launcher = SetupLauncher(root, data)
            process = Mock()
            process.poll.return_value = None
            def fixed_worker(args, **options):
                options["stdout"].write(b"macOS progress fixture\n")
                return process
            with patch("echo_recon.setup_launcher.sys.platform", "darwin"), \
                 patch.dict(os.environ, {}, clear=True), \
                 patch("echo_recon.setup_launcher.subprocess.Popen", side_effect=fixed_worker) as launch:
                self.assertTrue(launcher.launch()["launched"])
                self.assertEqual(launch.call_args.args[0], [sys.executable, str(root / "setup_tools_macos.py"),
                                 "--install", "--data-dir", str(data)])
                self.assertTrue(launch.call_args.kwargs["start_new_session"])
                self.assertFalse(launch.call_args.kwargs["shell"])
                self.assertIn("macOS progress fixture", launcher.status()["log"])
                with self.assertRaisesRegex(RuntimeError, "already open"):
                    launcher.launch()
                launch.assert_called_once()
                process.poll.return_value = 0
                self.assertIn("successfully", launcher.status()["message"])

    def test_mac_guidance_and_download_sources_are_platform_specific(self):
        with tempfile.TemporaryDirectory() as folder, patch("echo_recon.web.sys.platform", "darwin"):
            app = create_app(Path(folder), testing=True)
            page = app.test_client().get("/").text
            self.assertIn("macOS setup:", page)
            self.assertIn("setup_tools_macos.py --plan", page)
            self.assertNotIn("opens a visible Linux terminal", page)
            self.assertTrue(all(item["setup_url"].endswith("/MACOS.md") for item in tools.tool_sources().values()))
            app.extensions["echo_manager"].close()


@unittest.skipUnless(sys.platform == "darwin", "Native macOS runtime")
class NativeMacOSRuntimeTests(unittest.TestCase):
    def test_cli_server_responds_and_stops_without_running_scanners(self):
        with tempfile.TemporaryDirectory(prefix="echo native mac ") as folder:
            folder = str(Path(folder).resolve())
            env = dict(os.environ, ECHO_RECON_DATA_DIR=folder, PYTHONUNBUFFERED="1")
            log_path = Path(folder) / "server.log"
            log = log_path.open("w", encoding="utf-8")
            process = subprocess.Popen([sys.executable, str(ROOT / "app.py"), "--no-browser", "--no-tool-setup"],
                                       cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                                       text=True, start_new_session=True)
            try:
                deadline = time.monotonic() + 15
                last_error = "No connection attempted"
                while time.monotonic() < deadline:
                    if process.poll() is not None:
                        self.fail("Local server exited before responding: " + log_path.read_text())
                    try:
                        connection = http.client.HTTPConnection("127.0.0.1", 8001, timeout=1)
                        try:
                            connection.request("GET", "/")
                            response = connection.getresponse()
                            page = response.read().decode()
                            self.assertEqual(response.status, 200, page)
                        finally:
                            connection.close()
                        break
                    except (OSError, http.client.HTTPException) as exc:
                        last_error = str(exc)
                        time.sleep(.1)
                else:
                    self.fail(f"Local macOS server did not become ready ({last_error}): {log_path.read_text()}")
                self.assertIn(__version__, page)
                self.assertIn("macOS setup:", page)
                process.send_signal(signal.SIGTERM)
                process.wait(timeout=10)
                self.assertEqual(process.returncode, 0, log_path.read_text())
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
                log.close()

    def test_cancel_stops_the_macos_process_group(self):
        event = threading.Event()
        source = ("import subprocess,sys,time; "
                  "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); "
                  "print(p.pid,flush=True);time.sleep(30)")
        timer = threading.Timer(.5, event.set)
        timer.start()
        try:
            result = run([sys.executable, "-c", source], cancel=event)
        finally:
            timer.join()
        self.assertEqual(result.status, "cancelled")
        pid = int(result.stdout.strip())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            status = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "stat="],
                                    capture_output=True, text=True, check=False).stdout.strip()
            if not status or status.startswith(("Z", "X")):
                return
            time.sleep(.1)
        self.fail(f"Cancelled child process {pid} remained alive")


if __name__ == "__main__":
    unittest.main()
