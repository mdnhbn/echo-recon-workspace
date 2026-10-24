"""Automatic setup checks use fixtures only: no real tools or installers run."""
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import threading
import unittest
from unittest.mock import Mock

from app import parse_args
from echo_recon.bootstrap import StartupToolSetup
from echo_recon.setup_launcher import SetupLauncher
from echo_recon.tools import TOOLS


def health(*missing):
    return {name: {"status": "missing" if name in missing else "ready"} for name in TOOLS}


class InlineThread:
    def __init__(self, *, target, daemon):
        self.target, self.daemon = target, daemon

    def start(self):
        self.target()


class DeferredThread(InlineThread):
    def start(self):
        pass


class FakeLauncher:
    def __init__(self, data):
        self.data = data
        self.guard = threading.RLock()
        self.checking = False
        self.message = ""
        self.supports_platform = Mock(return_value=True)
        self.launch = Mock(side_effect=self.fixed_launch)

    def fixed_launch(self):
        if self.checking:
            raise AssertionError("Checking must end before a fixed worker can launch")
        return {"launched": True}

    def begin_startup_check(self):
        self.checking = True
        self.message = "Checking local tools"
        return True

    def finish_startup_check(self, message):
        self.checking = False
        self.message = message


class StartupToolSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        self.setup = FakeLauncher(self.data)
        self.manager = SimpleNamespace(lock=threading.RLock(), active=None)

    def tearDown(self):
        self.tmp.cleanup()

    def startup(self, values=None, **options):
        check = Mock(return_value=values if values is not None else health())
        worker = StartupToolSetup(self.setup, self.manager, version="fixture-version",
                                  check_tools=check, thread_factory=InlineThread, **options)
        return worker, check

    def test_ready_tools_skip_setup_and_do_not_write_state(self):
        worker, checker = self.startup()
        self.assertTrue(worker.start())
        checker.assert_called_once_with(cancel=worker.cancel)
        self.setup.launch.assert_not_called()
        self.assertIn("All 8 tools", self.setup.message)
        self.assertFalse(worker.state_path.exists())

    def test_running_setup_or_existing_check_is_not_replaced(self):
        launcher = SetupLauncher(self.data, self.data)
        self.assertTrue(launcher.begin_startup_check())
        checker = Mock(return_value=health("httpx"))
        worker = StartupToolSetup(launcher, self.manager, version="fixture-version",
                                  check_tools=checker, thread_factory=InlineThread)
        self.assertFalse(worker.start())
        checker.assert_not_called()
        self.assertIsNone(worker.thread)
        self.assertTrue(launcher.status()["running"])
        self.assertFalse(worker.state_path.exists())
        launcher.finish_startup_check("Fixture check finished")

    def test_missing_backends_launch_one_fixed_worker_and_record_attempt(self):
        worker, _ = self.startup(health("httpx", "arjun"))
        self.assertTrue(worker.start())
        self.setup.launch.assert_called_once_with()
        self.assertFalse(self.setup.checking)
        record = json.loads(worker.state_path.read_text(encoding="utf-8"))
        self.assertEqual(record["attempts"], [worker.fingerprint(["httpx", "arjun"])])
        self.assertFalse(worker.start())
        self.assertEqual(self.setup.launch.call_count, 1)

    def test_same_failed_attempt_does_not_repeat_on_restart_but_explicit_setup_can(self):
        self.setup.launch.side_effect = ValueError("Python 3.12 is required")
        first, _ = self.startup(health("httpx"))
        first.start()
        self.assertIn("Python 3.12", self.setup.message)
        self.assertFalse(self.setup.checking)
        self.setup.launch.reset_mock(side_effect=True)
        restarted, _ = self.startup(health("httpx"))
        restarted.start()
        self.setup.launch.assert_not_called()
        self.assertIn("Use Setup all tools to retry", self.setup.message)
        # Recording an automatic attempt does not wrap/disable the launcher's
        # existing explicit manual setup operation.
        self.setup.launch()
        self.setup.launch.assert_called_once_with()

    def test_changed_missing_set_or_version_permits_new_automatic_attempt(self):
        first, _ = self.startup(health("httpx", "arjun"))
        first.start()
        second, _ = self.startup(health("arjun"))
        second.start()
        third = StartupToolSetup(self.setup, self.manager, version="next-version",
                                 check_tools=Mock(return_value=health("arjun")), thread_factory=InlineThread)
        third.start()
        self.assertEqual(self.setup.launch.call_count, 3)
        self.assertEqual(len(json.loads(first.state_path.read_text())["attempts"]), 3)

    def test_active_assessment_defers_without_state_or_launch(self):
        self.manager.active = "fixture-job"
        worker, _ = self.startup(health("nmap"))
        worker.start()
        self.setup.launch.assert_not_called()
        self.assertIn("deferred", self.setup.message)
        self.assertFalse(worker.state_path.exists())

    def test_checking_state_is_available_before_background_check_finishes(self):
        check = Mock(return_value=health("httpx"))
        worker = StartupToolSetup(self.setup, self.manager, version="fixture-version",
                                  check_tools=check, thread_factory=DeferredThread)
        worker.start()
        self.assertTrue(self.setup.checking)
        check.assert_not_called()
        worker.close()
        worker.thread.target()
        self.setup.launch.assert_not_called()
        self.assertTrue(worker.cancel.is_set())
        self.assertFalse(self.setup.checking)
        self.assertFalse(worker.state_path.exists())

    def test_close_does_not_terminate_a_launched_installer(self):
        worker, _ = self.startup(health("httpx"))
        worker.start()
        worker.close()
        self.setup.launch.assert_called_once_with()
        self.assertTrue(worker.cancel.is_set())

    def test_unsupported_platform_is_explicit_and_no_probe_or_state_write(self):
        self.setup.supports_platform.return_value = False
        worker, checker = self.startup(health("httpx"))
        worker.start()
        checker.assert_not_called()
        self.setup.launch.assert_not_called()
        self.assertIn("unavailable on this platform", self.setup.message)
        self.assertFalse(worker.state_path.exists())

    def test_unrecognized_state_is_preserved(self):
        state = self.data / "auto-setup.json"
        state.write_text('{"unrelated":"keep exactly"}', encoding="utf-8")
        before = state.read_bytes()
        worker, _ = self.startup(health("httpx"))
        worker.start()
        self.setup.launch.assert_not_called()
        self.assertEqual(state.read_bytes(), before)
        self.assertIn("preserved", self.setup.message)
        self.assertFalse(self.setup.checking)

    def test_redirected_state_is_preserved(self):
        external = self.data / "user-notes.json"
        external.write_text("keep me", encoding="utf-8")
        try:
            os.symlink(external, self.data / "auto-setup.json")
        except OSError as exc:
            self.skipTest(f"File symlinks unavailable: {exc}")
        worker, _ = self.startup(health("httpx"))
        worker.start()
        self.setup.launch.assert_not_called()
        self.assertEqual(external.read_text(), "keep me")
        self.assertIn("redirected", self.setup.message)

    def test_probe_error_clears_checking_without_installation(self):
        worker, checker = self.startup()
        checker.side_effect = OSError("fixture probe failure")
        worker.start()
        self.assertFalse(self.setup.checking)
        self.setup.launch.assert_not_called()
        self.assertIn("fixture probe failure", self.setup.message)
        self.assertFalse(worker.state_path.exists())

    def test_thread_error_clears_checking_without_installation(self):
        thread = Mock()
        thread.start.side_effect = RuntimeError("fixture thread unavailable")
        worker = StartupToolSetup(self.setup, self.manager, version="fixture-version",
                                  thread_factory=Mock(return_value=thread))
        self.assertFalse(worker.start())
        self.assertFalse(self.setup.checking)
        self.setup.launch.assert_not_called()
        self.assertIn("could not start", self.setup.message)

    def test_cli_default_and_opt_out_are_independent_of_browser_opening(self):
        normal = parse_args([])
        self.assertFalse(normal.no_tool_setup)
        self.assertFalse(normal.no_browser)
        manual = parse_args(["--no-tool-setup", "--no-browser"])
        self.assertTrue(manual.no_tool_setup)
        self.assertTrue(manual.no_browser)
        self.assertFalse(parse_args(["--no-browser"]).no_tool_setup)


if __name__ == "__main__":
    unittest.main()
