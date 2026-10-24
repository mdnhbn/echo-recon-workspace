import json
import os
from pathlib import Path
import re
import socket
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from echo_recon.runner import Result, run
from echo_recon.locking import InstanceLock
from echo_recon.browser import open_when_ready, URL
from echo_recon.security import redact, resolve_public, scoped_urls, validate_scope
from echo_recon.service import Manager
from echo_recon.storage import Store
from echo_recon.tools import TOOLS, diagnostics, parse_findings
from echo_recon.web import create_app
from maintenance import remove_demos


# Existing orchestration fixtures must not depend on a developer's native tools.
_native_tool_patch = None


def setUpModule():
    global _native_tool_patch
    _native_tool_patch = patch("echo_recon.tools.native_tool_command", return_value=None)
    _native_tool_patch.start()


def tearDownModule():
    _native_tool_patch.stop()


def ready(**kwargs):
    return {name: {"status": "ready", "detail": "test fixture"} for name in TOOLS}


def public_resolver(host, port, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.215.14", port))]


class SecurityTests(unittest.TestCase):
    def test_scope_rejects_commands_urls_wildcards_and_suffix_confusion(self):
        for value in ["https://example.com", "example.com;id", "*.example.com", "127.0.0.1", "--help"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_scope(value, [value])
        for entries in [["example.com", "example.com.attacker.net"], ["example.com", "other.com"], []]:
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                validate_scope("example.com", entries)
        self.assertEqual(validate_scope("Example.COM", ["example.com", "app.example.com"])[1],
                         ["example.com", "app.example.com"])

    def test_private_and_mixed_dns_answers_are_rejected(self):
        for ip in ["127.0.0.1", "10.1.2.3", "169.254.169.254", "::1"]:
            with self.subTest(ip=ip), self.assertRaises(ValueError):
                resolve_public("example.com", lambda *a, **k: [(0, 0, 0, "", (ip, 443))])
        self.assertTrue(resolve_public("example.com", public_resolver))

    def test_live_urls_cannot_expand_scope(self):
        output = "https://example.com\nhttps://evil.net\nhttps://example.com:9999\nhttps://user:pass@example.com\nnot-a-url"
        self.assertEqual(scoped_urls(output, ["example.com"]), ["https://example.com"])

    def test_common_credentials_are_redacted(self):
        text = redact("https://user:pass@example.com/?api_key=abc&password=secret Cookie=abc")
        for secret in ["user:pass", "=abc", "=secret"]:
            self.assertNotIn(secret, text)

    def test_nuclei_parser_rejects_malformed_and_out_of_scope(self):
        valid = {"template-id": "test", "matched-at": "https://example.com/", "info": {"name": "test", "severity": "low"}}
        outside = {**valid, "matched-at": "https://other.net"}
        items, invalid = parse_findings(json.dumps(valid) + "\n" + json.dumps(outside) + "\nnot-json", ["example.com"])
        self.assertEqual((len(items), invalid), (1, 2))
        self.assertIn("unverified", items[0]["verification"])

    def test_wrong_python_httpx_is_not_ready(self):
        with patch("echo_recon.tools.shutil.which", return_value="/bin/fake"), patch("echo_recon.tools.run", return_value=Result("done", 0, "Python HTTPX client")):
            self.assertEqual(diagnostics()["httpx"]["status"], "unverified")


class RunnerTests(unittest.TestCase):
    def test_nonzero_is_error_even_with_empty_stdout(self):
        result = run([sys.executable, "-c", "import sys;sys.stderr.write('failed');sys.exit(7)"], cancel=threading.Event())
        self.assertEqual((result.status, result.returncode), ("error", 7))
        self.assertIn("failed", result.stderr)

    def test_timeout(self):
        result = run([sys.executable, "-c", "import time;time.sleep(10)"], cancel=threading.Event(), timeout=.15)
        self.assertEqual(result.status, "timeout")
        self.assertLess(result.duration, 4)

    def test_cancel(self):
        event = threading.Event()
        timer = threading.Timer(.15, event.set)
        timer.start()
        result = run([sys.executable, "-c", "import time;time.sleep(10)"], cancel=event)
        timer.join()
        self.assertEqual(result.status, "cancelled")

    def test_output_cap(self):
        result = run([sys.executable, "-c", "print('x'*100000)"], cancel=threading.Event(), max_bytes=1000)
        self.assertEqual(result.status, "output_limit")
        self.assertLessEqual(len(result.stdout.encode()) + len(result.stderr.encode()), 1000)

    @unittest.skipUnless(os.name == "nt", "Windows process tree")
    def test_windows_cancel_removes_child_tree(self):
        import csv
        import io
        import subprocess
        event = threading.Event()
        child = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); print(p.pid,flush=True);time.sleep(30)"
        timer = threading.Timer(.6, event.set)
        timer.start()
        result = run([sys.executable, "-c", child], cancel=event)
        timer.join()
        self.assertEqual(result.status, "cancelled")
        pid = result.stdout.strip()
        self.assertTrue(pid.isdigit(), result.stdout)
        check = subprocess.run(["tasklist.exe", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=True)
        rows = list(csv.reader(io.StringIO(check.stdout)))
        self.assertFalse(any(len(row) > 1 and row[1] == pid for row in rows))

    @unittest.skipUnless(os.name == "posix", "Linux process groups")
    def test_cancel_removes_child_process_group(self):
        event = threading.Event()
        child = "import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); print(p.pid,flush=True);time.sleep(30)"
        timer = threading.Timer(.3, event.set)
        timer.start()
        result = run([sys.executable, "-c", child], cancel=event)
        timer.join()
        self.assertEqual(result.status, "cancelled")
        pid = result.stdout.strip()
        if pid and Path(f"/proc/{pid}/stat").exists():
            self.assertIn(Path(f"/proc/{pid}/stat").read_text().split()[2], {"Z", "X"})


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "history.sqlite3")

    def tearDown(self):
        self.tmp.cleanup()

    def manager(self, execute):
        return Manager(self.store, self.tmp.name, execute=execute, resolver=public_resolver, check_tools=ready)

    def payload(self, tools):
        return dict(domain="example.com", scope=["example.com"], authorized=True, understands_limits=True, tools=tools)

    def test_failure_is_not_reported_as_success(self):
        manager = self.manager(lambda *a, **kw: Result("error", 2, "", "bad flags"))
        job_id = manager.start(self.payload(["nuclei"]), background=False)
        job = self.store.get(job_id)
        self.assertEqual(job["status"], "partial")
        self.assertEqual(job["phases"][0]["status"], "error")
        self.assertNotIn("No automated findings", job["phases"][0]["evidence"])

    def test_subdomain_discovery_does_not_expand_active_scope(self):
        calls = []
        def execute(args, **kwargs):
            calls.append((args, kwargs["stdin"]))
            return Result("done", 0, "outside.example.com" if args[0] == "subfinder" else "https://example.com\n")
        manager = self.manager(execute)
        manager.start(self.payload(["subfinder", "httpx"]), background=False)
        self.assertEqual(calls[1][1], "example.com\n")
        self.assertNotIn("outside.example.com", calls[1][1])

    def test_no_automatic_crawl_fallback(self):
        called = []
        manager = self.manager(lambda *a, **k: called.append(a))
        job = self.store.get(manager.start(self.payload(["photon", "arjun"]), background=False))
        self.assertFalse(called)
        self.assertTrue(all(p["status"] == "skipped" for p in job["phases"]))

    def test_aggregate_evidence_truncation_is_not_clean_success(self):
        manager = self.manager(lambda *a, **k: Result("done", 0, "x" * 110_000))
        job = self.store.get(manager.start(self.payload(["dnsrecon"]), background=False))
        self.assertEqual(job["status"], "partial")
        self.assertEqual(job["phases"][0]["status"], "output_limit")
        self.assertTrue(job["phases"][0]["evidence_truncated"])

    def test_restart_marks_work_incomplete(self):
        self.store.save({"id": "a"*32, "updated": "2026", "status": "running", "log": [], "phases": [{"status": "running"}]})
        Manager(self.store, self.tmp.name)
        self.assertEqual(self.store.get("a"*32)["status"], "interrupted")

    def test_removed_demo_cannot_execute_or_create_history(self):
        fail = lambda *a, **kw: self.fail("Removed demo must not execute anything")
        manager = Manager(self.store, self.tmp.name, execute=fail, resolver=fail, check_tools=fail)
        with self.assertRaisesRegex(ValueError, "removed"):
            manager.start({"demo": True}, background=False)
        self.assertEqual(self.store.recent(), [])


class MaintenanceTests(unittest.TestCase):
    def test_cleanup_removes_only_strict_demo_records_and_artifacts(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            store = Store(data / "history.sqlite3")
            demo_id, real_id = "a" * 32, "b" * 32
            real = {"id": real_id, "updated": "2026", "domain": "example.com", "demo": False, "status": "partial", "evidence": "keep this exact record"}
            store.save({"id": demo_id, "updated": "2026", "demo": True})
            store.save(real)
            for key in [demo_id, real_id]:
                path = data / "scratch" / key
                path.mkdir(parents=True)
                (path / "evidence.txt").write_text(key)
            self.assertEqual(remove_demos(data), 1)
            self.assertIsNone(store.get(demo_id))
            self.assertEqual(store.get(real_id), real)
            self.assertFalse((data / "scratch" / demo_id).exists())
            self.assertTrue((data / "scratch" / real_id / "evidence.txt").exists())
            self.assertEqual(remove_demos(data), 0)

    def test_cleanup_refuses_while_server_lock_is_held(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            store = Store(data / "history.sqlite3")
            store.save({"id": "a" * 32, "updated": "2026", "demo": True})
            lock = InstanceLock(data / "server.lock").acquire()
            try:
                with self.assertRaises(RuntimeError):
                    remove_demos(data)
            finally:
                lock.release()
            self.assertIsNotNone(store.get("a" * 32))


class LockTests(unittest.TestCase):
    def test_second_process_cannot_lock_until_release(self):
        import subprocess
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "server.lock"
            owner = InstanceLock(path).acquire()
            code = "from echo_recon.locking import InstanceLock;import sys;lock=InstanceLock(sys.argv[1]).acquire();lock.release()"
            try:
                blocked = subprocess.run([sys.executable, "-c", code, str(path)], capture_output=True, text=True)
                self.assertNotEqual(blocked.returncode, 0)
                self.assertIn("already has a running dashboard", blocked.stderr)
            finally:
                owner.release()
            allowed = subprocess.run([sys.executable, "-c", code, str(path)], capture_output=True, text=True)
            self.assertEqual(allowed.returncode, 0, allowed.stderr)


class BrowserTests(unittest.TestCase):
    def test_browser_waits_for_readiness(self):
        probes = iter([False, True])
        opened = []
        def opener(url, **kwargs):
            opened.append(url)
            return True
        self.assertTrue(open_when_ready(threading.Event(), probe=lambda: next(probes), opener=opener))
        self.assertEqual(opened, [URL])

    def test_stop_prevents_browser_open(self):
        stopped = threading.Event()
        stopped.set()
        self.assertFalse(open_when_ready(stopped, probe=lambda: self.fail("Should not probe"),
                                         opener=lambda *a, **k: self.fail("Should not open")))


class WebTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        def execute(args, **kwargs):
            cancelled = kwargs["cancel"].wait(.6)
            return Result("cancelled" if cancelled else "done", -15 if cancelled else 0, "local fixture only")
        self.app = create_app(self.tmp.name, testing=True, execute=execute,
                              resolver=public_resolver, check_tools=ready, allow_live=True)
        self.client = self.app.test_client()
        page = self.client.get("/").text
        self.csrf = re.search('name="csrf-token" content="([a-f0-9]+)"', page)[1]

    def tearDown(self):
        self.app.extensions["echo_manager"].close()
        deadline = time.time() + 3
        while self.app.extensions["echo_manager"].active and time.time() < deadline:
            time.sleep(.02)
        self.tmp.cleanup()

    def test_host_remote_and_csrf_boundaries(self):
        self.assertEqual(self.client.get("/", headers={"Host": "evil.net"}).status_code, 403)
        self.assertEqual(self.client.get("/", environ_overrides={"REMOTE_ADDR": "192.168.1.5"}).status_code, 403)
        self.assertEqual(self.client.post("/api/jobs", json={"demo": True}).status_code, 403)
        self.assertEqual(self.client.post("/api/jobs", json={"demo": True}, headers={"X-CSRF-Token": self.csrf, "Origin": "https://evil.net"}).status_code, 403)

    def test_explicit_disabled_mode_blocks_live_and_removed_demo(self):
        manager = self.app.extensions["echo_manager"]
        manager.allow_live = False
        response = self.client.post("/api/jobs", json={"domain": "example.com", "scope": ["example.com"], "authorized": True, "understands_limits": True}, headers={"X-CSRF-Token": self.csrf})
        self.assertEqual(response.status_code, 400)
        self.assertIn("disabled for this dashboard", response.json["error"])
        self.assertFalse(manager.active)
        demo = self.client.post("/api/jobs", json={"demo": True}, headers={"X-CSRF-Token": self.csrf})
        self.assertEqual(demo.status_code, 400)

    def test_mock_job_report_download_and_cancel(self):
        payload = dict(domain="example.com", scope=["example.com"], authorized=True, understands_limits=True, tools=["dnsrecon"])
        response = self.client.post("/api/jobs", json=payload, headers={"X-CSRF-Token": self.csrf})
        self.assertEqual(response.status_code, 202)
        job_id = response.json["id"]
        second = self.client.post("/api/jobs", json=payload, headers={"X-CSRF-Token": self.csrf})
        self.assertEqual(second.status_code, 409)
        stop = self.client.post(f"/api/jobs/{job_id}/cancel", json={}, headers={"X-CSRF-Token": self.csrf})
        self.assertTrue(stop.json["requested"])
        for _ in range(60):
            job = self.client.get(f"/api/jobs/{job_id}").json
            if job["status"] == "cancelled":
                break
            time.sleep(.03)
        self.assertEqual(job["status"], "cancelled")
        self.assertEqual(self.client.get(f"/reports/{job_id}.html").status_code, 200)
        self.assertIn("attachment", self.client.get(f"/reports/{job_id}.json").headers["Content-Disposition"])
        self.assertEqual(len(self.client.get("/api/jobs").json), 1)

    def test_legacy_demo_is_hidden_and_official_downloads_are_available(self):
        store = self.app.extensions["echo_store"]
        job_id = "a" * 32
        store.save(dict(id=job_id, updated="2026", created="2026", domain="example.com", demo=True, status="partial"))
        self.assertEqual(self.client.get("/api/jobs").json, [])
        self.assertEqual(self.client.get(f"/reports/{job_id}.html").status_code, 404)
        self.assertEqual(self.client.get(f"/api/jobs/{job_id}").status_code, 404)
        sources = self.client.get("/api/tool-sources").json
        self.assertEqual(set(sources), set(TOOLS))
        self.assertTrue(all(item["url"].startswith("https://") for item in sources.values()))
        page = self.client.get("/").text
        self.assertIn('id="download-tools"', page)
        self.assertNotIn('id="demo"', page)

    def test_legacy_demos_do_not_consume_real_history_limit(self):
        store = self.app.extensions["echo_store"]
        real_id = "f" * 32
        store.save(dict(id=real_id, updated="2025", created="2025", domain="example.com", status="partial"))
        for index in range(50):
            store.save(dict(id=f"{index:032x}", updated="2026", created="2026", domain="example.com", demo=True, status="partial"))
        self.assertEqual(len(store.recent()), 50)
        self.assertTrue(all(job.get("demo") is True for job in store.recent()))
        self.assertEqual([job["id"] for job in store.recent(limit=1, include_demos=False)], [real_id])
        self.assertEqual(store.recent(limit=0, include_demos=False), [])
        self.assertEqual([job["id"] for job in self.client.get("/api/jobs").json], [real_id])
        self.assertIsNotNone(store.get(real_id))

    def test_report_escapes_html_evidence(self):
        store = self.app.extensions["echo_store"]
        job_id = "f"*32
        store.save(dict(id=job_id, updated="2026", created="2026", domain="example.com", scope=["example.com"], status="partial", limitations=[], phases=[dict(label="Test", tool="test", status="error", evidence="<script>alert(1)</script>", stderr="", returncode=1, duration=0, findings=[])]))
        text = self.client.get(f"/reports/{job_id}.html").text
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;", text)


if __name__ == "__main__":
    unittest.main()
