"""Process-group cleanup, including descendants which close inherited pipes."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, call, patch

from echo_recon.runner import run, terminate, _signal_group


class PosixTerminationUnitTests(unittest.TestCase):
    def test_darwin_permission_race_requires_empty_or_zombie_only_group(self):
        for output in ("12 S\n", "7654321 Z\n", "7654321 Z+\n12 S\n"):
            with self.subTest(output=output), \
                 patch("echo_recon.runner.sys.platform", "darwin"), \
                 patch("echo_recon.runner.os.killpg", side_effect=PermissionError, create=True), \
                 patch("echo_recon.runner.subprocess.run",
                       return_value=Mock(returncode=0, stdout=output)) as snapshot:
                _signal_group(7654321, 9)
                self.assertEqual(snapshot.call_args.args[0], ["/bin/ps", "-axo", "pgid=,stat="])
                self.assertNotIn("shell", snapshot.call_args.kwargs)

    def test_darwin_live_or_unknown_group_permission_is_not_hidden(self):
        for code, output in ((0, "7654321 S\n"), (0, "7654321 Z\n7654321 R+\n"),
                             (0, "unexpected-format\n"), (0, ""), (1, "")):
            with self.subTest(code=code, output=output), \
                 patch("echo_recon.runner.sys.platform", "darwin"), \
                 patch("echo_recon.runner.os.killpg", side_effect=PermissionError, create=True), \
                 patch("echo_recon.runner.subprocess.run", return_value=Mock(returncode=code, stdout=output)):
                with self.assertRaises(PermissionError):
                    _signal_group(7654321, 9)

    def test_failed_darwin_snapshot_does_not_hide_permission_error(self):
        for error in (OSError("fixture"), subprocess.TimeoutExpired("ps", 2)):
            with self.subTest(error=type(error).__name__), \
                 patch("echo_recon.runner.sys.platform", "darwin"), \
                 patch("echo_recon.runner.os.killpg", side_effect=PermissionError, create=True), \
                 patch("echo_recon.runner.subprocess.run", side_effect=error):
                with self.assertRaises(PermissionError):
                    _signal_group(7654321, 9)

    def test_non_darwin_permission_error_stays_an_error(self):
        with patch("echo_recon.runner.sys.platform", "linux"), \
             patch("echo_recon.runner.os.killpg", side_effect=PermissionError, create=True), \
             patch("echo_recon.runner.subprocess.run") as snapshot:
            with self.assertRaises(PermissionError):
                _signal_group(7654321, 9)
            snapshot.assert_not_called()

    def test_exited_parent_still_kills_remaining_group(self):
        proc = Mock(pid=7654321)
        proc.wait.return_value = 0
        with patch("echo_recon.runner.os.name", "posix"), \
             patch("echo_recon.runner.os.killpg", create=True) as killpg, \
             patch("echo_recon.runner.signal.SIGKILL", 9, create=True):
            terminate(proc)
            self.assertEqual(killpg.call_args_list,
                             [call(proc.pid, signal.SIGTERM), call(proc.pid, 9)])

    def test_slow_parent_still_kills_remaining_group(self):
        proc = Mock(pid=7654321)
        proc.wait.side_effect = subprocess.TimeoutExpired("fixture", 1)
        with patch("echo_recon.runner.os.name", "posix"), \
             patch("echo_recon.runner.os.killpg", create=True) as killpg, \
             patch("echo_recon.runner.signal.SIGKILL", 9, create=True):
            terminate(proc)
            self.assertEqual(killpg.call_args_list,
                             [call(proc.pid, signal.SIGTERM), call(proc.pid, 9)])


@unittest.skipUnless(os.name == "posix", "Native Linux/macOS process groups")
class PosixDescendantCleanupTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "darwin", "Native Darwin zombie-group behavior")
    def test_darwin_zombie_only_group_is_already_stopped(self):
        child = subprocess.Popen([sys.executable, "-c", "pass"], start_new_session=True,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                # Do not poll/wait the Popen: keep the exited child unreaped so
                # Darwin's real zombie-only process group remains observable.
                status = subprocess.run(["/bin/ps", "-p", str(child.pid), "-o", "stat="],
                                        capture_output=True, text=True, check=True).stdout.strip()
                if status.startswith("Z"):
                    break
                time.sleep(.02)
            else:
                self.fail("Fixture never reached the exited/unreaped state")
            _signal_group(child.pid, signal.SIGKILL)
        finally:
            child.wait(timeout=5)

    def assert_stopped(self, pid):
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
            time.sleep(.05)
        self.fail(f"Owned descendant {pid} remained alive after tool completion")

    def exercise_descendant(self, cancel_parent):
        with tempfile.TemporaryDirectory() as folder:
            ready = Path(folder) / "child-ready"
            child_source = ("import os,signal,time;from pathlib import Path;"
                            "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
                            f"Path({str(ready)!r}).write_text(str(os.getpid()));"
                            "time.sleep(30)")
            parent_source = (
                "import subprocess,sys,time;from pathlib import Path;"
                f"p=subprocess.Popen([sys.executable,'-c',{child_source!r}],"
                "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
                f"ready=Path({str(ready)!r});"
                "\nwhile not ready.exists():time.sleep(.01)\n"
                "print(p.pid,flush=True);"
                + ("time.sleep(30)" if cancel_parent else ""))
            event = threading.Event()
            watcher = None
            if cancel_parent:
                def stop_after_ready():
                    deadline = time.monotonic() + 10
                    while not ready.exists() and time.monotonic() < deadline:
                        time.sleep(.01)
                    event.set()
                watcher = threading.Thread(target=stop_after_ready, daemon=True)
                watcher.start()
            pid = None
            try:
                result = run([sys.executable, "-c", parent_source], cancel=event)
                if ready.exists():
                    pid = int(ready.read_text())
                self.assertIsNotNone(pid, result.stderr)
                self.assertEqual(result.status, "cancelled" if cancel_parent else "done",
                                 result.stderr)
                self.assert_stopped(pid)
            finally:
                if watcher:
                    watcher.join(timeout=11)
                if pid is None and ready.exists():
                    pid = int(ready.read_text())
                if pid:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_normal_parent_exit_removes_detached_stdio_descendant_only(self):
        unrelated = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"],
                                     start_new_session=True, stdin=subprocess.DEVNULL,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self.exercise_descendant(cancel_parent=False)
            self.assertIsNone(unrelated.poll(), "Cleanup touched an unrelated process group")
        finally:
            if unrelated.poll() is None:
                os.killpg(unrelated.pid, signal.SIGKILL)
            unrelated.wait(timeout=5)

    def test_cancel_removes_sigterm_ignoring_detached_stdio_descendant(self):
        self.exercise_descendant(cancel_parent=True)


if __name__ == "__main__":
    unittest.main()
