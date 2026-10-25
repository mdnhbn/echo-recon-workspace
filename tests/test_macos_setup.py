"""Native macOS setup fixtures; no scanners, Homebrew or network are run."""
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import setup_tools as common
import setup_tools_macos as setup
import setup_tools_windows as assets
from echo_recon.locking import InstanceLock
from tests.test_setup_tools import health


def archive(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as output:
        for name, data in entries:
            output.writestr(name, data)
    return stream.getvalue()


class MacSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="echo Mac fixture ")
        self.home = Path(self.tmp.name).resolve()
        self.calls, self.fetches, self.messages = [], [], []
        self.payloads = {}
        self.release_pins = {name: dict(item) for name, item in assets.WINDOWS_RELEASES.items()}
        self.source_pins = {name: dict(item) for name, item in assets.SOURCE_ARCHIVES.items()}
        for name, item in self.release_pins.items():
            rows = []
            for arch in ("amd64", "arm64"):
                filename = f"{name}_{item['version']}_macOS_{arch}.zip"
                payload = archive([(name, b"fixture Mach-O, never execute"), ("LICENSE.md", b"license")])
                self.payloads[item["url"].rsplit("/", 1)[0] + "/" + filename] = payload
                rows.append(hashlib.sha256(payload).hexdigest() + "  " + filename)
            manifest = ("\n".join(rows) + "\n").encode()
            self.payloads[item["checksums_url"]] = manifest
            item["checksums_sha256"] = hashlib.sha256(manifest).hexdigest()
        for name, item in self.source_pins.items():
            leaf = "photon.py" if name == "photon" else "pyproject.toml"
            payload = archive([(item["prefix"] + "/" + leaf, b"# fixture source")])
            self.payloads[item["url"]] = payload
            item["sha256"] = hashlib.sha256(payload).hexdigest()
        guards = [patch.object(assets, "WINDOWS_RELEASES", self.release_pins),
                  patch.object(assets, "SOURCE_ARCHIVES", self.source_pins),
                  patch.object(setup.platform, "machine", return_value="arm64"),
                  patch.object(setup.subprocess, "run", side_effect=AssertionError("real process forbidden")),
                  patch.object(setup.urllib.request, "build_opener", side_effect=AssertionError("real network forbidden"))]
        for guard in guards:
            guard.start()
            self.addCleanup(guard.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def run_command(self, args, **options):
        self.calls.append((list(args), options))
        if "venv" in args:
            folder = Path(args[-1]) / "bin"
            folder.mkdir(parents=True)
            for name in ("python", "arjun", "dnsrecon", "theHarvester"):
                (folder / name).write_text("fixture executable", encoding="utf-8")
        return SimpleNamespace(stdout="fixture", returncode=0)

    def fetch(self, url, **options):
        self.fetches.append(url)
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
        return setup.MacInstaller(home=self.home, run=self.run_command, fetch=self.fetch,
                                  check_tools=check_tools, output=self.messages.append)

    def test_default_plan_does_not_probe_write_or_download(self):
        with redirect_stdout(io.StringIO()), patch.object(setup, "MacInstaller", side_effect=AssertionError("installer constructed")), \
                patch.object(setup, "validate_platform", side_effect=AssertionError("platform probed")):
            self.assertEqual(setup.main([]), 0)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(self.calls, [])
        self.assertEqual(self.fetches, [])

    def test_all_ready_skips_homebrew_downloads_and_storage(self):
        installer = self.installer(health())
        self.assertEqual(installer.install(), 0)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.fetches, [])
        self.assertFalse(installer.base.exists())

    def test_native_homebrew_paths_and_fixed_missing_formula_command(self):
        for machine, prefix in (("arm64", "/opt/homebrew"), ("x86_64", "/usr/local")):
            with self.subTest(machine=machine), patch.object(setup.platform, "machine", return_value=machine):
                installer = self.installer()
                with patch.object(Path, "is_file", return_value=True):
                    installer.prerequisites(["nmap", "nikto"])
                args, options = self.calls[-1]
                self.assertEqual(args, [str(Path(prefix) / "bin/brew"), "install", "--formula", "homebrew/core/nmap", "homebrew/core/nikto"])
                self.assertFalse(options["shell"])
                self.assertIn(str(Path(prefix) / "bin"), options["env"]["PATH"])
                self.assertEqual(options["env"]["HOMEBREW_NO_AUTO_UPDATE"], "1")
                self.assertEqual(options["env"]["HOMEBREW_NO_ANALYTICS"], "1")
                self.assertNotIn("sudo", args)
                self.assertNotIn("upgrade", args)
        self.assertEqual(self.fetches, [])

    def test_missing_homebrew_and_old_python_stop_before_commands(self):
        installer = self.installer()
        with patch.object(Path, "is_file", return_value=False), self.assertRaisesRegex(setup.SetupError, "Homebrew is missing"):
            installer.prerequisites(["nmap"])
        with patch.object(setup.sys, "version_info", (3, 11, 0)), self.assertRaisesRegex(setup.SetupError, "Python >=3.12"):
            installer.prerequisites(["dnsrecon"])
        self.assertEqual(self.calls, [])

    def test_homebrew_redirecting_environment_is_scrubbed(self):
        with patch.dict(os.environ, {"HOMEBREW_BREW_GIT_REMOTE": "https://example.invalid/malicious", "HOMEBREW_API_DOMAIN": "https://example.invalid"}):
            installer = self.installer()
        self.assertNotIn("HOMEBREW_BREW_GIT_REMOTE", installer.env)
        self.assertNotIn("HOMEBREW_API_DOMAIN", installer.env)

    def test_verified_macOS_assets_selected_for_both_architectures(self):
        for machine in ("arm64", "x86_64"):
            for name in common.GO_MODULES:
                with self.subTest(machine=machine, name=name), tempfile.TemporaryDirectory() as folder, \
                        patch.object(setup.platform, "machine", return_value=machine):
                    installer = setup.MacInstaller(home=Path(folder).resolve(), run=self.run_command,
                                                   fetch=self.fetch, output=self.messages.append)
                    installer.prepare()
                    installer.install_release(name)
                    target, _ = common.tool_target(installer.home, name)
                    self.assertEqual(target.read_bytes(), b"fixture Mach-O, never execute")
                    self.assertEqual((installer.home / ".local/bin" / name).read_text(), common.wrapper_text(installer.home, name))
        self.assertTrue(any("macOS_arm64.zip" in url for url in self.fetches))
        self.assertTrue(any("macOS_amd64.zip" in url for url in self.fetches))
        self.assertFalse(any("linux_" in url or "windows_" in url for url in self.fetches))
        self.assertEqual(self.calls, [])

    def test_modified_manifest_or_archive_never_extracts(self):
        for corrupt in ("manifest", "archive"):
            with self.subTest(corrupt=corrupt):
                installer = self.installer()
                installer.prepare()
                item = self.release_pins["httpx"]
                url = item["checksums_url"] if corrupt == "manifest" else item["url"].rsplit("/", 1)[0] + "/httpx_1.12.0_macOS_arm64.zip"
                original = self.payloads[url]
                self.payloads[url] = b"modified download"
                with self.assertRaises(assets.SetupError):
                    installer.install_release("httpx")
                self.assertFalse(common.go_target(self.home, "httpx").exists())
                self.payloads[url] = original
        self.assertEqual(self.calls, [])

    def test_python_source_tools_get_separate_native_venvs(self):
        installer = self.installer()
        installer.prepare()
        for name in ("dnsrecon", "theHarvester", "photon", "arjun"):
            installer.install_source(name)
            target, _ = common.tool_target(self.home, name)
            self.assertTrue(target.is_file())
        venvs = [Path(args[-1]) for args, _ in self.calls if "venv" in args]
        self.assertEqual(len(venvs), 4)
        self.assertEqual(len(set(venvs)), 4)
        self.assertTrue(all(path.is_relative_to(installer.base) for path in venvs))
        self.assertTrue(all(args[:3] == [sys.executable, "-I", "-m"] for args, _ in self.calls if "venv" in args))
        self.assertFalse(any(args[0] in {"/usr/bin/python3", "/usr/bin/git"} for args, _ in self.calls))

    def test_nuclei_template_only_repair_keeps_engine_and_other_tools(self):
        initial, final = health(), health()
        initial["nuclei"].update(status="unverified", engine_status="ready", template_status="missing")
        final["nuclei"].update(engine_status="ready", template_status="ready", template_version="v10.5.0")
        installer = self.installer(initial, final)
        self.assertEqual(installer.install(), 0)
        self.assertEqual(self.calls[0][0], ["/usr/bin/nuclei", "-update-templates", "-duc"])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.fetches, [])

    def test_existing_partial_folder_or_unverified_shadow_is_preserved(self):
        installer = self.installer(health("httpx"))
        folder = installer.version_folder("httpx")
        folder.mkdir(parents=True)
        sentinel = folder / "personal.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "preserved"):
            installer.install()
        self.assertEqual(sentinel.read_text(), "keep")
        initial = health("nmap")
        initial["nmap"]["path"] = str(self.home / "unrelated-nmap")
        with self.assertRaisesRegex(setup.SetupError, "shadows"):
            self.installer(initial).install()
        self.assertEqual(self.calls, [])
        self.assertEqual(self.fetches, [])

    def test_unknown_architecture_and_untrusted_downloads_are_rejected(self):
        with patch.object(setup.platform, "machine", return_value="ppc64"), self.assertRaisesRegex(setup.SetupError, "native Intel"):
            setup.architecture()
        with self.assertRaisesRegex(setup.SetupError, "outside"):
            setup.download("https://example.invalid/payload.zip")
        item = self.release_pins["httpx"]
        with self.assertRaisesRegex(setup.SetupError, "outside"):
            setup.download(item["url"])

    def test_platform_and_rosetta_validation_run_before_install(self):
        with patch.object(setup.sys, "platform", "linux"), self.assertRaisesRegex(setup.SetupError, "native macOS"):
            setup.validate_platform()
        with patch.object(setup.sys, "platform", "darwin"), patch.object(setup.os, "geteuid", create=True, return_value=0), \
                self.assertRaisesRegex(setup.SetupError, "without sudo"):
            setup.validate_platform()
        with patch.object(setup.sys, "platform", "darwin"), patch.object(setup.os, "geteuid", create=True, return_value=501), \
                patch.object(setup.sys, "version_info", (3, 12, 0)), patch.object(setup.platform, "machine", return_value="x86_64"), \
                patch.object(setup.subprocess, "run", return_value=SimpleNamespace(stdout="1\n", returncode=0)) as call, \
                self.assertRaisesRegex(setup.SetupError, "Rosetta"):
            setup.validate_platform()
        self.assertEqual(call.call_args.args[0], ["/usr/sbin/sysctl", "-in", "sysctl.proc_translated"])
        self.assertFalse(call.call_args.kwargs["shell"])

    def test_shared_setup_lock_prevents_a_second_worker(self):
        data = self.home / "data"
        data.mkdir()
        lock = InstanceLock(data / "setup-tools.lock").acquire()
        try:
            with patch.object(setup, "validate_platform"), patch.object(setup, "MacInstaller") as installer, \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(setup.main(["--install", "--data-dir", str(data)]), 1)
                installer.assert_not_called()
        finally:
            lock.release()

    def test_final_health_failure_never_reports_success(self):
        installer = self.installer(health("httpx"), health("httpx"))
        self.assertEqual(installer.install(), 1)
        self.assertTrue(any("incomplete" in message for message in self.messages))


@unittest.skipUnless(sys.platform == "darwin", "native macOS copied-venv layout")
class NativeMacVenvLayoutTests(unittest.TestCase):
    def test_copied_python_venv_passes_managed_tree_checks(self):
        with tempfile.TemporaryDirectory(prefix="echo native Mac venv ") as folder:
            installer = setup.MacInstaller(home=Path(folder).resolve(), output=lambda message: None)
            installer.prepare()
            venv = installer.base / "layout-probe/venv"
            subprocess.run([sys.executable, "-I", "-m", "venv", "--copies", "--without-pip", str(venv)], check=True)
            installer.check_managed_tree(venv)
            result = subprocess.run([str(venv / "bin/python"), "-I", "-c", "print('native-venv-ready')"],
                                    check=True, text=True, capture_output=True)
            self.assertEqual(result.stdout.strip(), "native-venv-ready")


if __name__ == "__main__":
    unittest.main()
