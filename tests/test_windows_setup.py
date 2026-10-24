"""Native Windows setup tests: all network/process work uses tiny local fixtures."""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import setup_tools_windows as setup
from echo_recon.locking import InstanceLock


def health(*missing):
    return {name: {"status": "missing" if name in missing else "ready",
                   "path": None if name in missing else str(Path("C:/mock-tools") / (name + ".exe")),
                   "detail": "fixture local identity check"} for name in setup.TOOL_NAMES}


def zipped(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, contents in entries:
            if isinstance(name, str):
                raw = zipfile.ZipInfo("fixture")
                raw.filename = raw.orig_filename = name
                name = raw
            archive.writestr(name, contents)
    return stream.getvalue()


class FakeCommands:
    def __init__(self):
        self.calls = []
        self.failure = None

    def __call__(self, args, **options):
        self.calls.append((list(args), options))
        if self.failure and self.failure(args):
            raise subprocess.CalledProcessError(9, args)
        if "venv" in args:
            scripts = Path(args[-1]) / "Scripts"
            scripts.mkdir(parents=True)
            for filename in ("python.exe", "dnsrecon.exe", "theHarvester.exe"):
                (scripts / filename).write_bytes(b"fixture executable, never run")
        return SimpleNamespace(stdout="fixture", returncode=0)


class WindowsSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.local = Path(self.tmp.name)
        self.messages = []
        self.commands = FakeCommands()
        self.fetches = []
        self.payloads = {}
        self.perl_path = self.local / "perl.exe"
        perl_path = self.perl_path
        which_guard = patch.object(setup.shutil, "which",
                                   side_effect=lambda name: str(perl_path) if name in {"perl", "perl.exe"} else None)
        which_guard.start()
        self.addCleanup(which_guard.stop)
        self.releases = {name: dict(item) for name, item in setup.WINDOWS_RELEASES.items()}
        self.sources = {name: dict(item) for name, item in setup.SOURCE_ARCHIVES.items()}
        for name, item in self.releases.items():
            payload = zipped([(name + ".exe", b"fixture binary"), ("LICENSE.md", b"fixture license"),
                              ("ignored.txt", b"must not extract")])
            item["sha256"] = hashlib.sha256(payload).hexdigest()
            manifest = (item["sha256"] + "  " + item["asset"] + "\n").encode()
            item["checksums_sha256"] = hashlib.sha256(manifest).hexdigest()
            self.payloads[item["url"]] = payload
            self.payloads[item["checksums_url"]] = manifest
        for name, item in self.sources.items():
            entry = ("photon.py" if name == "photon" else
                     "program/nikto.pl" if name == "nikto" else "pyproject.toml")
            payload = zipped([(item["prefix"] + "/" + entry, b"# fixture source"),
                              (item["prefix"] + "/LICENSE", b"fixture license")])
            item["sha256"] = hashlib.sha256(payload).hexdigest()
            self.payloads[item["url"]] = payload
        # No test can accidentally launch a real command or make a real request.
        for target, replacement in (("WINDOWS_RELEASES", self.releases), ("SOURCE_ARCHIVES", self.sources)):
            guard = patch.object(setup, target, replacement)
            guard.start()
            self.addCleanup(guard.stop)
        process_guard = patch.object(setup.subprocess, "run", side_effect=AssertionError("real process forbidden"))
        network_guard = patch.object(setup.urllib.request, "build_opener", side_effect=AssertionError("real network forbidden"))
        process_guard.start()
        network_guard.start()
        self.addCleanup(process_guard.stop)
        self.addCleanup(network_guard.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def fetch(self, url, **options):
        self.fetches.append((url, options))
        return self.payloads[url]

    def installer(self, *states):
        iterator = iter(states or [health()])
        last = [None]
        def check_tools():
            try:
                last[0] = next(iterator)
            except StopIteration:
                pass
            return last[0]
        return setup.Installer(local_app_data=self.local, run=self.commands, fetch=self.fetch,
                               check_tools=check_tools, output=self.messages.append,
                               python=str(self.local / "trusted-python.exe"))

    def test_default_and_explicit_plan_are_read_only(self):
        for args in ([], ["--plan"]):
            with patch.object(Path, "home", return_value=self.local / "home"), patch.dict(os.environ, {"LOCALAPPDATA": str(self.local)}), patch.object(Path, "mkdir", side_effect=AssertionError("write forbidden")), patch.object(Path, "write_text", side_effect=AssertionError("write forbidden")), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(setup.main(args), 0)
            self.assertIn("READ-ONLY PLAN", output.getvalue())
            self.assertIn(setup.PHOTON_COMMIT, output.getvalue())
            self.assertIn("windows_amd64.zip", output.getvalue())
            self.assertIn("not a pinned snapshot", output.getvalue())
            self.assertEqual(list(self.local.iterdir()), [])

    def test_default_storage_ignores_appdata_context_and_preserves_explicit_override(self):
        home = self.local / "home"
        expected = home / "Tools/EchoRecon/tooling"
        with patch.object(Path, "home", return_value=home):
            for appdata in (self.local / "ordinary", self.local / "package/LocalCache/Local"):
                with patch.dict(os.environ, {"LOCALAPPDATA": str(appdata)}):
                    self.assertEqual(setup.managed_root(), expected)
                    self.assertEqual(setup.Installer().base, expected)
                    self.assertEqual(setup.tool_folder("httpx").parent, expected)
            self.assertEqual(setup.managed_root(self.local), self.local / "EchoRecon/tooling")
            with self.assertRaisesRegex(setup.SetupError, "absolute"):
                setup.managed_root("relative")
        self.assertEqual(list(self.local.iterdir()), [])

    def test_default_installer_and_resolver_share_storage_across_appdata_contexts(self):
        home = self.local / "home"
        old_appdata = self.local / "package/LocalCache/Local"
        old_folder = old_appdata / "EchoRecon/tooling/httpx-1.12.0"
        old_folder.mkdir(parents=True)
        sentinel = old_folder / "keep.txt"
        sentinel.write_text("preserve old installation")
        states = iter((health("httpx"), health()))
        with patch.object(Path, "home", return_value=home):
            with patch.dict(os.environ, {"LOCALAPPDATA": str(old_appdata)}):
                installer = setup.Installer(run=self.commands, fetch=self.fetch,
                    check_tools=lambda: next(states), output=self.messages.append)
                self.assertEqual(installer.install(), 0)
                command = setup.tool_command("httpx")
                self.assertTrue(command)
                self.assertTrue(Path(command[0]).is_relative_to(home / "Tools/EchoRecon/tooling"))
            with patch.dict(os.environ, {"LOCALAPPDATA": str(self.local / "ordinary")}):
                self.assertEqual(setup.tool_command("httpx"), command)
                self.assertEqual(sentinel.read_text(), "preserve old installation")

    def test_existing_ready_tools_skip_every_write_download_and_command(self):
        sentinel = self.local / "keep.txt"
        sentinel.write_text("keep")
        self.assertEqual(self.installer(health()).install(), 0)
        self.assertEqual(self.commands.calls, [])
        self.assertEqual(self.fetches, [])
        self.assertEqual(sentinel.read_text(), "keep")
        self.assertFalse(setup.managed_root(self.local).exists())

    def test_nuclei_template_only_repair_does_not_reinstall_engine_or_other_tools(self):
        initial, final = health(), health()
        initial["nuclei"].update(status="unverified", engine_status="ready", template_status="missing")
        final["nuclei"].update(engine_status="ready", template_status="ready", template_version="v10.5.0")
        installer = self.installer(initial, final)
        self.assertEqual(installer.install(), 0)
        self.assertEqual(len(self.commands.calls), 1)
        self.assertEqual(self.commands.calls[0][0], [str(Path("C:/mock-tools/nuclei.exe")), "-update-templates", "-duc"])
        self.assertEqual(self.fetches, [])

    def test_missing_nmap_only_is_manual_exit_two_with_no_installer_launch(self):
        self.assertEqual(self.installer(health("nmap")).install(), 2)
        self.assertEqual(self.commands.calls, [])
        self.assertEqual(self.fetches, [])
        self.assertTrue(any("nmap: manual" in message for message in self.messages))
        self.assertFalse(any("All 8" in message for message in self.messages))

    def test_supported_tools_install_with_explicit_paths_and_manual_nmap(self):
        self.perl_path.write_bytes(b"fixture Perl executable; never run")
        installer = self.installer(health(*setup.TOOL_NAMES), health("nmap"))
        original_path = os.environ.get("PATH")
        self.assertEqual(installer.install(), 2)
        self.assertEqual(os.environ.get("PATH"), original_path)
        for name in setup.TOOL_VERSIONS:
            command = setup.tool_command(name, self.local)
            self.assertTrue(command, name)
            if name == "nikto":
                self.assertEqual(Path(command[0]), self.perl_path)
                self.assertTrue(Path(command[1]).is_relative_to(installer.base))
            else:
                self.assertTrue(Path(command[0]).is_relative_to(installer.base))
            self.assertFalse(any(arg.endswith((".cmd", ".bat")) for arg in command))
            folder = setup.tool_folder(name, self.local)
            self.assertEqual(json.loads((folder / setup.TOOL_MARKER).read_text()), setup.marker_data(name))
        self.assertTrue(any(args[-2:] == ["-update-templates", "-duc"] for args, _ in self.commands.calls))
        for args, options in self.commands.calls:
            self.assertFalse(options["shell"])
            self.assertNotIn("--break-system-packages", args)
            self.assertNotIn("powershell", args[0].lower())
            self.assertNotIn("wsl", args[0].lower())
        self.assertFalse(any("All 8" in message for message in self.messages))

    def test_release_download_checks_manifest_and_archive_before_extracting(self):
        installer = self.installer(health("httpx"), health())
        self.assertEqual(installer.install(), 0)
        item = self.releases["httpx"]
        self.assertEqual([url for url, _ in self.fetches], [item["checksums_url"], item["url"]])
        folder = setup.tool_folder("httpx", self.local) / "bin"
        self.assertTrue((folder / "httpx.exe").is_file())
        self.assertTrue((folder / "LICENSE.md").is_file())
        self.assertFalse((folder / "ignored.txt").exists())
        self.assertEqual(self.commands.calls, [])

    def test_bad_manifest_stops_before_binary_download_or_folder_creation(self):
        item = self.releases["httpx"]
        self.payloads[item["checksums_url"]] = b"tampered"
        installer = self.installer(health("httpx"), health("httpx"))
        self.assertEqual(installer.install(), 1)
        self.assertEqual(len(self.fetches), 1)
        self.assertFalse(setup.tool_folder("httpx", self.local).exists())
        self.assertEqual(self.commands.calls, [])

    def test_bad_zip_digest_is_never_extracted(self):
        item = self.releases["httpx"]
        self.payloads[item["url"]] = b"tampered ZIP"
        self.assertEqual(self.installer(health("httpx"), health("httpx")).install(), 1)
        self.assertFalse(setup.tool_folder("httpx", self.local).exists())

    def test_manifest_requires_unique_exact_selected_filename(self):
        digest = "a" * 64
        self.assertEqual(setup.checksum_for((digest + " *tool.zip\n").encode(), "tool.zip"), digest)
        for manifest in (digest + "  other.zip\n", (digest + "  tool.zip\n") * 2, "garbage"):
            with self.subTest(manifest=manifest), self.assertRaises(setup.SetupError):
                setup.checksum_for(manifest.encode(), "tool.zip")

    def test_zip_traversal_absolute_ads_reserved_and_backslash_members_refused(self):
        unsafe = ("../outside.exe", "/outside.exe", "C:/outside.exe", "name:stream", "NUL.txt", "folder\\outside.exe", "name. ")
        for name in unsafe:
            with self.subTest(name=name), self.assertRaises(setup.SetupError):
                setup.extract_zip(zipped([("httpx.exe", b"ok"), (name, b"bad")]), self.local / "output", binary="httpx.exe")
            self.assertFalse((self.local / "output").exists())

    def test_zip_symlinks_case_collisions_and_size_limits_refused(self):
        info = zipfile.ZipInfo("httpx.exe")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(setup.SetupError):
            setup.extract_zip(zipped([(info, b"outside")]), self.local / "output", binary="httpx.exe")
        with self.assertRaises(setup.SetupError):
            setup.extract_zip(zipped([("httpx.exe", b"1"), ("HTTPX.EXE", b"2")]), self.local / "output", binary="httpx.exe")
        with patch.object(setup, "MAX_UNPACKED", 1), self.assertRaises(setup.SetupError):
            setup.extract_zip(zipped([("httpx.exe", b"large")]), self.local / "output", binary="httpx.exe")
        self.assertFalse((self.local / "output").exists())

    def test_source_archive_requires_exact_commit_root(self):
        with self.assertRaisesRegex(setup.SetupError, "pinned commit"):
            setup.extract_zip(zipped([("different/photon.py", b"bad")]), self.local / "source", prefix="expected")
        self.assertFalse((self.local / "source").exists())

    def test_unmanaged_storage_and_version_collisions_are_preserved(self):
        base = setup.managed_root(self.local)
        base.mkdir(parents=True)
        sentinel = base / "personal.txt"
        sentinel.write_text("keep")
        with self.assertRaisesRegex(setup.SetupError, "Unrecognized existing"):
            self.installer(health("httpx")).install()
        self.assertEqual(sentinel.read_text(), "keep")
        self.assertEqual(self.fetches, [])
        self.assertEqual(self.commands.calls, [])

    def test_partial_or_unverified_managed_folder_is_never_overwritten(self):
        installer = self.installer(health("httpx"))
        installer.prepare()
        folder = installer.new_folder("httpx")
        (folder / "keep.txt").write_text("keep")
        with self.assertRaisesRegex(setup.SetupError, "Existing version folder"):
            installer.install()
        self.assertIsNone(setup.tool_command("httpx", self.local))
        self.assertEqual((folder / "keep.txt").read_text(), "keep")
        self.assertEqual(self.fetches, [])

    def test_redirected_storage_or_entrypoint_is_never_written_or_resolved(self):
        installer = self.installer(health("httpx"), health())
        self.assertEqual(installer.install(), 0)
        binary = Path(setup.tool_command("httpx", self.local)[0])
        for redirected in (installer.base.parent, installer.base, binary):
            original = setup._redirected
            with self.subTest(path=redirected), patch.object(setup, "_redirected", side_effect=lambda path: path == redirected or original(path)):
                self.assertIsNone(setup.tool_command("httpx", self.local))
                with self.assertRaisesRegex(setup.SetupError, "reparse point"):
                    setup.plain_path(binary)

    def test_metadata_cannot_supply_an_arbitrary_executable(self):
        installer = self.installer(health("arjun"), health())
        self.assertEqual(installer.install(), 0)
        marker = setup.tool_folder("arjun", self.local) / setup.TOOL_MARKER
        metadata = json.loads(marker.read_text())
        metadata["command"] = ["arbitrary.exe"]
        marker.write_text(json.dumps(metadata))
        self.assertIsNone(setup.tool_command("arjun", self.local))

    def test_python_venvs_have_separate_final_paths_and_exact_pins(self):
        installer = self.installer(health(*setup.PYTHON_PINS), health())
        self.assertEqual(installer.install(), 0)
        creations = [args for args, _ in self.commands.calls if "venv" in args]
        self.assertEqual(len(creations), 4)
        self.assertEqual(len({args[-1] for args in creations}), 4)
        for name in setup.PYTHON_PINS:
            python = str(setup.tool_folder(name, self.local) / "venv/Scripts/python.exe")
            installs = [args for args, _ in self.commands.calls if args[0] == python and "install" in args]
            self.assertTrue(all("--isolated" in args and "--no-deps" in args and "https://pypi.org/simple" in args for args in installs))
            self.assertTrue(any(set(setup.PYTHON_PINS[name]).issubset(args) for args in installs))
            self.assertTrue(any(args[-1] == "check" and args[0] == python for args, _ in self.commands.calls))
        self.assertTrue(any(setup.ARJUN_SOURCE in args for args, _ in self.commands.calls))
        self.assertTrue(any(setup.DNSRECON_COMMIT in url for url, _ in self.fetches))
        self.assertTrue(any(setup.HARVESTER_COMMIT in url for url, _ in self.fetches))

    def test_inherited_python_pip_and_git_configuration_is_scrubbed(self):
        with patch.dict(os.environ, {"PYTHONPATH": "untrusted", "PIP_EXTRA_INDEX_URL": "https://evil.invalid", "GIT_CONFIG_GLOBAL": "untrusted"}):
            installer = self.installer()
        self.assertNotIn("PYTHONPATH", installer.env)
        self.assertNotIn("PIP_EXTRA_INDEX_URL", installer.env)
        self.assertNotIn("GIT_CONFIG_GLOBAL", installer.env)
        self.assertEqual(installer.env["PIP_CONFIG_FILE"], os.devnull)

    def test_process_success_does_not_hide_failed_final_local_checks(self):
        self.assertEqual(self.installer(health("arjun"), health("arjun")).install(), 1)
        self.assertFalse(any("All 8" in message for message in self.messages))

    def test_failed_python_command_preserves_partial_environment_without_metadata(self):
        self.commands.failure = lambda args: "pip" in args
        self.assertEqual(self.installer(health("arjun"), health("arjun")).install(), 1)
        folder = setup.tool_folder("arjun", self.local)
        self.assertTrue((folder / ".echo-recon-pending").is_file())
        self.assertFalse((folder / setup.TOOL_MARKER).exists())
        self.assertIsNone(setup.tool_command("arjun", self.local))

    def test_templates_are_only_updated_for_new_engine_or_explicit_request(self):
        self.assertEqual(self.installer(health()).install(), 0)
        self.assertEqual(self.commands.calls, [])
        self.assertEqual(self.installer(health(), health()).install(update_templates=True), 0)
        self.assertEqual(self.commands.calls[-1][0][-2:], ["-update-templates", "-duc"])
        self.commands.failure = lambda args: "-update-templates" in args
        self.assertEqual(self.installer(health(), health()).install(update_templates=True), 1)
        self.assertTrue(any("TEMPLATE ERROR" in message for message in self.messages))

    def test_url_allowlist_and_redirect_validation_reject_untrusted_sources(self):
        for url in ("http://github.com/a", "https://github.com.evil.invalid/a", "https://evil.invalid/a", "https://user@github.com/a", "https://github.com:8080/a"):
            with self.subTest(url=url), self.assertRaises(setup.SetupError):
                setup._check_https_host(url)
        with self.assertRaisesRegex(setup.SetupError, "fixed official"):
            setup.download("https://github.com/unreviewed/arbitrary.zip")
        setup._check_https_host("https://release-assets.githubusercontent.com/github-production-release-asset/example?token=example")

    def test_downloader_enforces_bounded_size_with_mock_response(self):
        response = io.BytesIO(b"oversized")
        response.geturl = lambda: self.releases["httpx"]["url"]
        opener = SimpleNamespace(open=lambda *args, **kwargs: response)
        with patch.object(setup.urllib.request, "build_opener", return_value=opener), self.assertRaisesRegex(setup.SetupError, "size limit"):
            setup.download(self.releases["httpx"]["url"], limit=2)

    def test_platform_rejects_linux_wrong_arch_wrong_python_and_admin(self):
        with patch.object(setup.sys, "platform", "linux"), self.assertRaisesRegex(setup.SetupError, "native Windows"):
            setup.validate_platform()
        with patch.object(setup.sys, "platform", "win32"), patch.object(setup.platform, "machine", return_value="ARM64"), self.assertRaisesRegex(setup.SetupError, "x64"):
            setup.validate_platform()
        with patch.object(setup.sys, "platform", "win32"), patch.object(setup.platform, "machine", return_value="AMD64"), patch.object(setup.sys, "version_info", (3, 13)), self.assertRaisesRegex(setup.SetupError, "3.12"):
            setup.validate_platform()
        windll = SimpleNamespace(shell32=SimpleNamespace(IsUserAnAdmin=lambda: True))
        with patch.object(setup.sys, "platform", "win32"), patch.object(setup.platform, "machine", return_value="AMD64"), patch.object(setup.sys, "version_info", (3, 12)), patch.object(setup.ctypes, "windll", windll, create=True), self.assertRaisesRegex(setup.SetupError, "normal Windows user"):
            setup.validate_platform()

    def test_shared_singleton_lock_blocks_second_setup_before_installer(self):
        data = self.local / "data"
        data.mkdir()
        lock = InstanceLock(data / "setup-tools.lock").acquire()
        try:
            with patch.object(setup, "validate_platform"), patch.object(setup, "Installer") as installer, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(setup.main(["--install", "--data-dir", str(data)]), 1)
                installer.assert_not_called()
                self.assertIn("already running", errors.getvalue())
        finally:
            lock.release()

    def test_configured_trusted_data_folder_and_optional_pause(self):
        data = self.local / "custom data"
        with patch.object(setup, "validate_platform"), patch.object(setup, "Installer") as installer, redirect_stdout(io.StringIO()):
            installer.return_value.install.return_value = 2
            self.assertEqual(setup.main(["--install", "--data-dir", str(data)]), 2)
        self.assertTrue((data / "setup-tools.lock").is_file())
        with patch.object(setup, "validate_platform", side_effect=setup.SetupError("fixture")), patch.object(setup.sys.stdin, "isatty", return_value=True), patch("builtins.input", return_value="") as prompt, redirect_stderr(io.StringIO()):
            self.assertEqual(setup.main(["--install", "--pause"]), 1)
            prompt.assert_called_once()


if __name__ == "__main__":
    unittest.main()
