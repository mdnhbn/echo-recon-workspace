"""Native adapter orchestration uses fixtures; no public requests are made."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from echo_recon import runner, tools
from echo_recon.service import Manager
from echo_recon.storage import Store


def public_fixture(host, port, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", port))]


class NativeWindowsAssessmentTests(unittest.TestCase):
    def test_nine_adapters_use_managed_prefixes_scope_and_nikto_fallback(self):
        with tempfile.TemporaryDirectory(prefix="echo Windows paths ") as directory:
            folder = Path(directory)
            prefixes = {name: (str(folder / "isolated tools" / name / (name + ".exe")),)
                        for name in tools.TOOLS}
            prefixes["photon"] = (str(folder / "Photon tool" / "python.exe"),
                                  str(folder / "Photon tool" / "photon.py"))
            prefixes["arjun"] = (str(folder / "Arjun tool" / "python.exe"), "-m", "arjun")
            calls = []
            scope = ["example.com", "app.example.com"]
            def execute(args, **options):
                name = next(name for name, prefix in prefixes.items()
                            if tuple(args[:len(prefix)]) == prefix)
                calls.append((name, args, options))
                if name == "subfinder":
                    output = "outside.example.com\n"
                elif name == "httpx":
                    output = "\n".join("https://" + host for host in scope) + "\nhttps://outside.example.com\n"
                elif name == "nuclei":
                    return runner.Result("error", 1, "", "fixture Nuclei failure", duration=.01)
                else:
                    output = "Local fixture; no tool or network request was run."
                return runner.Result("done", 0, output, duration=.01)
            def health(**kwargs):
                return {name: {"status": "ready", "detail": "fixture", "command": list(prefix)}
                        for name, prefix in prefixes.items()}
            store = Store(folder / "history.sqlite3")
            manager = Manager(store, folder, execute=execute, resolver=public_fixture, check_tools=health)
            payload = {"domain": scope[0], "scope": scope, "authorized": True,
                       "understands_limits": True, "tools": list(tools.TOOLS), "rate": 2, "timeout": 30}
            with patch.object(tools, "is_windows", return_value=True), \
                    patch("echo_recon.service.is_windows", return_value=True), \
                    patch.object(tools, "native_tool_command", side_effect=lambda name: prefixes[name]):
                job = store.get(manager.start(payload, background=False))
            self.assertEqual(job["status"], "partial")
            self.assertEqual({name for name, _, _ in calls}, set(tools.TOOLS))
            nuclei = next(phase for phase in job["phases"] if phase["tool"] == "nuclei")
            nikto = next(phase for phase in job["phases"] if phase["tool"] == "nikto")
            self.assertEqual(nuclei["status"], "error")
            self.assertEqual(nikto["status"], "done")
            self.assertIn("Nuclei status was error", nikto["evidence"])
            for name, args, options in calls:
                self.assertEqual(args[:len(prefixes[name])], list(prefixes[name]))
                self.assertNotIn("timeout", options)
                self.assertIsInstance(options["cancel"], threading.Event)
                self.assertTrue(options["cwd"].is_relative_to(folder / "scratch" / job["id"]))
                self.assertNotIn("outside.example.com", args)
                self.assertNotIn("outside.example.com", options["stdin"])
                if name in {"httpx", "nuclei"}:
                    self.assertIn(options["stdin"].strip(), ["https://" + host + "/" for host in scope])
                if name == "nmap":
                    self.assertIn("-sT", args)
                    self.assertIn("-Pn", args)
                    self.assertEqual(args[args.index("--max-rate") + 1], "2")
                    self.assertEqual(args[args.index("--top-ports") + 1], "100")
                    self.assertNotIn("-sS", args)
                    self.assertNotIn("-sU", args)
                    self.assertNotIn("-O", args)
                if name in {"httpx", "arjun", "nuclei"}:
                    flag = "--rate-limit" if name == "arjun" else "-rl"
                    self.assertEqual(args[args.index(flag) + 1], "2")
            self.assertTrue(any("-sT -Pn" in text for text in job["limitations"]))

    def test_non_windows_nmap_keeps_existing_discovery_behavior(self):
        with patch.object(tools, "is_windows", return_value=False), \
                patch.object(tools, "native_tool_command", return_value=None):
            args = tools.command("nmap", "example.com", 1, Path("unused"))
        self.assertIn("-sT", args)
        self.assertNotIn("-Pn", args)

    def test_disabled_deployment_rejects_before_any_scope_or_network_check(self):
        with tempfile.TemporaryDirectory() as folder:
            store = Store(Path(folder) / "history.sqlite3")
            def forbidden(*args, **kwargs):
                self.fail("A disabled dashboard must not execute or resolve anything")
            manager = Manager(store, folder, execute=forbidden, resolver=forbidden,
                              check_tools=forbidden, allow_live=False)
            with self.assertRaisesRegex(ValueError, "disabled"):
                manager.start({"authorized": True, "understands_limits": True})
            self.assertEqual(store.recent(), [])


@unittest.skipUnless(os.name == "nt", "Windows process job containment")
class WindowsProcessJobTests(unittest.TestCase):
    def assert_process_gone(self, pid):
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if handle:
            try:
                self.assertEqual(kernel.WaitForSingleObject(handle, 2000), 0)
            finally:
                kernel.CloseHandle(handle)

    def test_parent_exit_closes_descendants_and_inherited_pipes(self):
        child = ("import subprocess,sys; "
                 "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); "
                 "print(p.pid,flush=True)")
        started = time.monotonic()
        result = runner.run([sys.executable, "-c", child], cancel=threading.Event())
        self.assertEqual(result.status, "done", result.stderr)
        self.assertLess(time.monotonic() - started, 4)
        self.assertTrue(result.stdout.strip().isdigit(), result.stdout)
        self.assert_process_gone(int(result.stdout.strip()))

    def test_job_assignment_failure_never_runs_suspended_tool(self):
        with tempfile.TemporaryDirectory() as folder:
            marker = Path(folder) / "must-not-exist"
            code = "from pathlib import Path;import sys;Path(sys.argv[1]).write_text('ran')"
            with patch.object(runner.WindowsProcessJob, "attach_and_resume", side_effect=OSError("fixture assignment failure")):
                result = runner.run([sys.executable, "-c", code, str(marker)], cancel=threading.Event())
            self.assertEqual(result.status, "error")
            self.assertIn("assignment failure", result.stderr)
            self.assertFalse(marker.exists())

    def test_job_creation_failure_refuses_process_start(self):
        with patch.object(runner, "WindowsProcessJob", side_effect=OSError("fixture unavailable")), \
                patch.object(runner.subprocess, "Popen") as start:
            result = runner.run(["fixture.exe"], cancel=threading.Event())
        self.assertEqual(result.status, "error")
        start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
