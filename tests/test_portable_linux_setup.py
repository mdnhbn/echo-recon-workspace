"""Portable Linux fixtures: no real downloads, sudo, installation or targets."""
import hashlib
import io
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import setup_tools as setup
import setup_tools_windows as assets
from tests.test_setup_tools import health


def archive(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as out:
        for name, data in entries:
            out.writestr(name, data)
    return stream.getvalue()


class PortableLinuxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.calls, self.fetches, self.messages = [], [], []
        self.payloads = {}
        self.release_pins = {name: dict(item) for name, item in assets.WINDOWS_RELEASES.items()}
        self.source_pins = {name: dict(item) for name, item in assets.SOURCE_ARCHIVES.items()}
        for name, item in self.release_pins.items():
            rows = []
            for arch in ("amd64", "arm64"):
                filename = f"{name}_{item['version']}_linux_{arch}.zip"
                payload = archive([(name, b"fixture ELF, never execute"), ("LICENSE.md", b"license")])
                self.payloads[item["url"].rsplit("/", 1)[0] + "/" + filename] = payload
                rows.append(hashlib.sha256(payload).hexdigest() + "  " + filename)
            manifest = ("\n".join(rows) + "\n").encode()
            self.payloads[item["checksums_url"]] = manifest
            item["checksums_sha256"] = hashlib.sha256(manifest).hexdigest()
        for name, item in self.source_pins.items():
            filename = ("photon.py" if name == "photon" else
                        "program/nikto.pl" if name == "nikto" else "pyproject.toml")
            payload = archive([(item["prefix"] + "/" + filename, b"# fixture source")])
            self.payloads[item["url"]] = payload
            item["sha256"] = hashlib.sha256(payload).hexdigest()
        for name, value in (("WINDOWS_RELEASES", self.release_pins), ("SOURCE_ARCHIVES", self.source_pins)):
            guard = patch.object(assets, name, value)
            guard.start()
            self.addCleanup(guard.stop)
        trust = patch.object(setup.ssl, "get_default_verify_paths", return_value=SimpleNamespace(cafile="/fixture/ca.pem", capath=None))
        trust.start()
        self.addCleanup(trust.stop)
        machine = patch.object(setup.platform, "machine", return_value="x86_64")
        machine.start()
        self.addCleanup(machine.stop)
        process = patch.object(setup.subprocess, "run", side_effect=AssertionError("real process forbidden"))
        network = patch.object(setup.urllib.request, "build_opener", side_effect=AssertionError("real network forbidden"))
        for guard in (process, network):
            guard.start()
            self.addCleanup(guard.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def run_command(self, args, **options):
        self.calls.append((args, options))
        if "venv" in args:
            folder = Path(args[-1]) / "bin"
            folder.mkdir(parents=True)
            for name in ("python", "arjun", "dnsrecon", "theHarvester"):
                (folder / name).write_text("fixture executable", encoding="utf-8")
        return SimpleNamespace(stdout="fixture", returncode=0)

    def fetch(self, url, **options):
        self.fetches.append(url)
        return self.payloads[url]

    def installer(self, family="apt", *states):
        iterator = iter(states or [health()])
        last = [None]
        def check_tools():
            try:
                last[0] = next(iterator)
            except StopIteration:
                pass
            return last[0]
        return setup.PortableInstaller(family, home=self.home, run=self.run_command,
                                       check_tools=check_tools, output=self.messages.append, fetch=self.fetch)

    def test_family_detection_uses_id_like_and_explicit_unsupported_matrix(self):
        pairs = [("kali", "kali"), ("ubuntu", "apt"), ("debian", "apt"), ("fedora", "dnf"),
                 ("rocky", "dnf"), ("arch", "pacman"), ("manjaro", "pacman"), ("opensuse-tumbleweed", "zypper")]
        for distro, expected in pairs:
            with self.subTest(distro=distro):
                self.assertEqual(setup.linux_family({"ID": distro}), expected)
        self.assertEqual(setup.linux_family({"ID": "custom", "ID_LIKE": "ubuntu debian"}), "apt")
        for distro in ("alpine", "nixos", "unknown"):
            with self.subTest(distro=distro), self.assertRaises(setup.SetupError):
                setup.linux_family({"ID": distro})

    def test_all_ready_has_no_commands_downloads_or_managed_writes(self):
        installer = self.installer("apt", health())
        self.assertEqual(installer.install(), 0)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.fetches, [])
        self.assertFalse(installer.base.exists())

    def test_nuclei_template_only_repair_does_not_reinstall_engine_or_other_tools(self):
        initial, final = health(), health()
        initial["nuclei"].update(status="unverified", engine_status="ready", template_status="missing")
        final["nuclei"].update(engine_status="ready", template_status="ready", template_version="v10.5.0")
        installer = self.installer("apt", initial, final)
        self.assertEqual(installer.install(), 0)
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][0], ["/usr/bin/nuclei", "-update-templates", "-duc"])
        self.assertEqual(self.fetches, [])

    def test_fixed_package_manager_argv_for_nmap_and_no_system_upgrade(self):
        expected = {"apt": ["install", "--yes", "--no-install-recommends", "nmap"],
                    "dnf": ["install", "--assumeyes", "nmap"],
                    "pacman": ["-S", "--needed", "--noconfirm", "nmap"],
                    "zypper": ["--non-interactive", "install", "--no-recommends", "nmap"]}
        for family, args in expected.items():
            self.calls.clear()
            installer = self.installer(family)
            with patch.object(Path, "is_file", return_value=True), patch.object(setup.sys.stdin, "isatty", return_value=True):
                installer.prerequisites(["nmap"])
            self.assertEqual(self.calls[-1][0], ["/usr/bin/sudo", setup.LINUX_FAMILIES[family]["manager"], *args])
            self.assertTrue(all(options["shell"] is False for _, options in self.calls))
            self.assertFalse(any("upgrade" in arg for command, _ in self.calls for arg in command))
            if family == "apt":
                self.assertEqual(self.calls[0][0][-1], "update")

    def test_sudo_needs_tty_and_missing_manager_never_guesses(self):
        installer = self.installer()
        with patch.object(Path, "is_file", return_value=True), patch.object(setup.sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(setup.SetupError, "interactive terminal"):
                installer.prerequisites(["nmap"])
        with patch.object(Path, "is_file", return_value=False):
            with self.assertRaisesRegex(setup.SetupError, "manager is missing"):
                installer.prerequisites(["nmap"])
        self.assertEqual(self.calls, [])

    def test_old_python_refused_before_commands_or_downloads(self):
        installer = self.installer()
        with patch.object(setup.sys, "version_info", (3, 11, 0)):
            with self.assertRaisesRegex(setup.SetupError, "Python >=3.12"):
                installer.prerequisites(["dnsrecon"])
        self.assertEqual(self.calls, [])
        self.assertEqual(self.fetches, [])

    def test_official_linux_releases_verified_for_both_supported_architectures(self):
        for machine in ("x86_64", "aarch64"):
            for name in setup.GO_MODULES:
                installer = self.installer()
                installer.prepare()
                with patch.object(setup.platform, "machine", return_value=machine):
                    installer.install_release(name)
                target, _ = setup.tool_target(self.home, name)
                self.assertEqual(target.read_bytes(), b"fixture ELF, never execute")
                self.assertEqual((self.home / ".local/bin" / name).read_text(), setup.wrapper_text(self.home, name))
                # Separate fixture homes prevent replacing an existing version.
                self.tmp.cleanup()
                self.tmp = tempfile.TemporaryDirectory()
                self.home = Path(self.tmp.name)
        self.assertTrue(any("linux_amd64.zip" in url for url in self.fetches))
        self.assertTrue(any("linux_arm64.zip" in url for url in self.fetches))
        self.assertEqual(self.calls, [])  # No Go SDK or downloaded shell scripts.

    def test_modified_manifest_or_payload_never_extracts_or_executes(self):
        for corrupt in ("manifest", "payload"):
            installer = self.installer()
            installer.prepare()
            item = self.release_pins["httpx"]
            original = dict(self.payloads)
            url = item["checksums_url"] if corrupt == "manifest" else item["url"].rsplit("/", 1)[0] + "/httpx_1.12.0_linux_amd64.zip"
            self.payloads[url] = b"modified download"
            with patch.object(setup.platform, "machine", return_value="x86_64"), self.assertRaises(assets.SetupError):
                installer.install_release("httpx")
            self.assertFalse(setup.go_target(self.home, "httpx").exists())
            self.payloads = original
        self.assertEqual(self.calls, [])

    def test_portable_source_tools_use_separate_final_venvs_and_os_requirements(self):
        installer = self.installer()
        installer.prepare()
        for name in ("dnsrecon", "theHarvester", "photon", "arjun", "nikto"):
            installer.install_source(name)
            target, _ = setup.tool_target(self.home, name)
            self.assertTrue(target.is_file())
            self.assertEqual((self.home / ".local/bin" / name).read_text(), setup.wrapper_text(self.home, name))
        venvs = [Path(args[-1]) for args, _ in self.calls if "venv" in args]
        self.assertEqual(len(venvs), 4)
        self.assertEqual(len(set(venvs)), 4)
        self.assertTrue(all(path.is_relative_to(installer.base) for path in venvs))
        sources = [args for args, _ in self.calls if "install" in args and args[-1].endswith("source")]
        self.assertEqual(len(sources), 2)
        self.assertTrue(all("--no-deps" not in args and "--no-build-isolation" in args for args in sources))
        self.assertFalse(any("--break-system-packages" in args for args, _ in self.calls))

    def test_existing_tool_or_launcher_conflict_stops_before_packages_and_network(self):
        installer = self.installer("apt", health("httpx"))
        folder = installer.version_folder("httpx")
        folder.mkdir(parents=True)
        sentinel = folder / "personal.txt"
        sentinel.write_text("keep", encoding="utf-8")
        with patch.object(setup.platform, "machine", return_value="x86_64"), self.assertRaisesRegex(setup.SetupError, "preserved"):
            installer.install()
        self.assertEqual(sentinel.read_text(), "keep")
        self.assertEqual(self.calls, [])
        self.assertEqual(self.fetches, [])

    def test_unknown_architecture_and_untrusted_download_url_fail_closed(self):
        installer = self.installer()
        with patch.object(setup.platform, "machine", return_value="riscv64"), self.assertRaisesRegex(setup.SetupError, "architecture"):
            installer.architecture()
        with self.assertRaisesRegex(setup.SetupError, "outside"):
            setup.portable_download("https://example.invalid/not-official.zip")
        self.assertEqual(self.calls, [])

    def test_final_health_failure_is_not_reported_as_success(self):
        installer = self.installer("apt", health("httpx"), health("httpx"))
        with patch.object(setup.platform, "machine", return_value="x86_64"), patch.object(installer, "prerequisites"):
            self.assertEqual(installer.install(), 1)
        self.assertTrue(any("incomplete" in message for message in self.messages))


if __name__ == "__main__":
    unittest.main()
