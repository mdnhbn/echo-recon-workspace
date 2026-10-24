"""Installer tests: every external command is mocked; never install or scan."""
import io
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout, redirect_stderr

import setup_tools as setup
from echo_recon.locking import InstanceLock
from echo_recon.tools import TOOLS


def health(*missing):
    return {name: {"status": "missing" if name in missing else "ready",
                   "path": None if name in missing else f"/usr/bin/{name}",
                   "detail": "mocked local identity check"} for name in TOOLS}


class FakeCommands:
    """Make only test-directory artifacts that a successful command would make."""
    def __init__(self):
        self.calls = []
        self.origin = setup.PHOTON_URL
        self.version = "go version go1.26.0 linux/amd64"
        self.failure = None

    def __call__(self, args, **kwargs):
        self.calls.append((list(args), kwargs))
        if self.failure and self.failure(args):
            raise subprocess.CalledProcessError(9, args)
        if args[1:] == ["version"]:
            return SimpleNamespace(stdout=self.version, returncode=0)
        if args[1:3] == ["install", "-v"]:
            name = args[-1].rsplit("/", 1)[1].split("@", 1)[0]
            binary = Path(kwargs["env"]["GOBIN"]) / name
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_text("test artifact", encoding="utf-8")
        if args[1:3] == ["-m", "venv"]:
            binary = Path(args[-1]) / "bin/python"
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_text("test interpreter", encoding="utf-8")
            (binary.parent / "arjun").write_text("test arjun", encoding="utf-8")
        if args[0] == "/usr/bin/git":
            if "init" in args:
                Path(args[-1]).mkdir(parents=True, exist_ok=True)
            if args[-3:] == ["remote", "get-url", "origin"]:
                return SimpleNamespace(stdout=self.origin, returncode=0)
            if "checkout" in args:
                source = Path(args[args.index("-C") + 1])
                (source / "photon.py").write_text("# test photon", encoding="utf-8")
            if args[-2:] == ["rev-parse", "HEAD"]:
                return SimpleNamespace(stdout=setup.PHOTON_COMMIT, returncode=0)
        return SimpleNamespace(stdout="installed", returncode=0)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name)
        self.commands = FakeCommands()
        self.messages = []

    def tearDown(self):
        self.temporary.cleanup()

    def installer(self, *states):
        iterator = iter(states or [health()])
        return setup.Installer(home=self.home, run=self.commands,
                               check_tools=lambda: next(iterator), output=self.messages.append)

    def test_plan_is_read_only_and_never_probes_or_runs_commands(self):
        with patch.object(setup, "ROOT", self.home), patch.object(setup.subprocess, "run", side_effect=AssertionError("command forbidden")), patch.object(setup, "diagnostics", side_effect=AssertionError("probe forbidden")), patch.object(Path, "mkdir", side_effect=AssertionError("write forbidden")), patch.object(Path, "write_text", side_effect=AssertionError("write forbidden")), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(setup.main(["--plan"]), 0)
        text = output.getvalue()
        self.assertIn("READ-ONLY PLAN", text)
        self.assertIn(setup.PHOTON_COMMIT, text)
        self.assertIn("@v2.17.0", text)
        self.assertIn("Go >=1.26", text)
        self.assertIn("not a pinned template snapshot", text)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_install_rejects_root_and_selects_supported_linux(self):
        with patch.object(setup.sys, "platform", "linux"), patch.object(setup.os, "geteuid", return_value=0, create=True):
            with self.assertRaisesRegex(setup.SetupError, "normal Linux user"):
                setup.validate_platform()
        with patch.object(setup.sys, "platform", "linux"), patch.object(setup.os, "geteuid", return_value=1000, create=True), patch.object(Path, "read_text", return_value='ID=ubuntu\nID_LIKE=debian\n'):
            self.assertEqual(setup.validate_platform(), "apt")
        with patch.object(setup.sys, "platform", "win32"):
            with self.assertRaisesRegex(setup.SetupError, "Windows"):
                setup.validate_platform()

    def test_all_ready_skips_every_install_and_keeps_path_and_files(self):
        old_path = os.environ.get("PATH")
        marker = self.home / "keep.txt"
        marker.write_text("do not change", encoding="utf-8")
        result = self.installer(health()).install()
        self.assertEqual(result, 0)
        self.assertEqual(self.commands.calls, [])
        self.assertEqual(os.environ.get("PATH"), old_path)
        self.assertEqual(marker.read_text(), "do not change")
        self.assertFalse(setup.managed_root(self.home).exists())

    def test_unmanaged_wrapper_conflict_stops_before_apt_or_download(self):
        binary = self.home / ".local/bin/httpx"
        binary.parent.mkdir(parents=True)
        binary.write_text("another project's Python HTTPX", encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "Command conflict"):
            self.installer(health("httpx")).install()
        self.assertEqual(binary.read_text(), "another project's Python HTTPX")
        self.assertEqual(self.commands.calls, [])

    def test_only_exact_managed_wrapper_can_be_reused(self):
        binary = self.home / ".local/bin/httpx"
        binary.parent.mkdir(parents=True)
        binary.write_text(setup.wrapper_text(self.home, "httpx"), encoding="utf-8")
        setup.check_wrapper(self.home, "httpx")
        binary.write_text(setup.WRAPPER_MARKER + "\nexec arbitrary\n", encoding="utf-8")
        with self.assertRaises(setup.SetupError):
            setup.check_wrapper(self.home, "httpx")

    def test_broken_symlink_launcher_is_never_replaced(self):
        binary = self.home / ".local/bin/httpx"
        binary.parent.mkdir(parents=True)
        try:
            binary.symlink_to(self.home / "missing")
        except OSError:
            self.skipTest("This host does not allow test symlinks")
        with self.assertRaises(setup.SetupError):
            setup.check_wrapper(self.home, "httpx")
        self.assertTrue(binary.is_symlink())

    def test_go_installs_use_exact_modules_isolated_caches_and_safe_argv(self):
        installer = self.installer(health(*setup.GO_MODULES), health())
        with patch.object(installer, "choose_go", return_value="/usr/bin/go"), patch.object(installer, "package_present", return_value=True):
            self.assertEqual(installer.install(), 0)
        builds = [(args, options) for args, options in self.commands.calls if args[1:3] == ["install", "-v"]]
        self.assertEqual([args[-1] for args, _ in builds], list(setup.GO_MODULES.values()))
        for args, options in self.commands.calls:
            self.assertFalse(options["shell"])
            self.assertNotIn("--break-system-packages", args)
            self.assertNotIn("sudo", args[0])
        for args, options in builds:
            env = options["env"]
            self.assertEqual(env["GOTOOLCHAIN"], "local")
            self.assertEqual(env["GOSUMDB"], "sum.golang.org")
            self.assertEqual(env["GOPROXY"], "https://proxy.golang.org")
            self.assertTrue(Path(env["GOBIN"]).is_relative_to(setup.managed_root(self.home)))
        for name in setup.GO_MODULES:
            self.assertEqual((self.home / ".local/bin" / name).read_text(), setup.wrapper_text(self.home, name))
        self.assertTrue(any(args[-2:] == ["-update-templates", "-duc"] for args, _ in self.commands.calls))

    def test_apt_needs_tty_and_only_fixed_missing_packages(self):
        installer = self.installer()
        with patch.object(installer, "package_present", return_value=True), patch.object(setup.sys.stdin, "isatty", return_value=False):
            with self.assertRaisesRegex(setup.SetupError, "interactive terminal"):
                installer.prerequisites(["nmap"])
        self.assertEqual(self.commands.calls, [])
        with patch.object(installer, "package_present", return_value=True), patch.object(setup.sys.stdin, "isatty", return_value=True):
            installer.prerequisites(["nmap"])
        self.assertEqual(self.commands.calls[0][0], ["/usr/bin/sudo", "/usr/bin/apt-get", "update"])
        self.assertEqual(self.commands.calls[1][0], ["/usr/bin/sudo", "/usr/bin/apt-get", "install", "--yes", "--no-install-recommends", "nmap"])
        self.assertNotIn("input", self.commands.calls[1][1])

    def test_old_go_after_apt_fails_with_actionable_message(self):
        installer = self.installer()
        with patch.object(installer, "choose_go", return_value=None), patch.object(installer, "package_present", return_value=True), patch.object(setup.sys.stdin, "isatty", return_value=True):
            with self.assertRaisesRegex(setup.SetupError, "Go >=1.26"):
                installer.prerequisites(["subfinder"])
        self.assertIn("golang-go", self.commands.calls[-1][0])
        self.assertFalse(any("curl" in args or "wget" in args for args, _ in self.commands.calls))

    def test_go_version_requires_126_and_uses_suitable_system_fallback(self):
        installer = self.installer()
        def versions(args, **kwargs):
            return SimpleNamespace(stdout="go version go1.25.2 linux/amd64" if args[0] == "/old/go" else "go version go1.26.1 linux/amd64")
        installer.run = versions
        with patch.object(setup.shutil, "which", return_value="/old/go"), patch.object(Path, "is_file", return_value=True):
            self.assertEqual(installer.choose_go(), "/usr/bin/go")

    def test_arjun_installs_into_own_venv_with_all_runtime_pins(self):
        installer = self.installer(health("arjun"), health())
        with patch.object(installer, "package_present", return_value=True):
            self.assertEqual(installer.install(), 0)
        installs = [args for args, _ in self.commands.calls if "pip" in args and "install" in args]
        self.assertEqual(len(installs), 2)
        self.assertTrue(all("--isolated" in args and "--no-deps" in args for args in installs))
        self.assertTrue(set(setup.ARJUN_PINS).issubset(installs[-1]))
        self.assertIn("--no-build-isolation", installs[-1])
        self.assertTrue(Path(installs[-1][0]).is_relative_to(setup.managed_root(self.home)))

    def test_photon_checks_official_origin_and_pinned_commit(self):
        installer = self.installer(health("photon"), health())
        # Prerequisite availability belongs to separate apt tests. Do not probe
        # host /usr/bin paths here: Windows normalizes their path separators.
        with patch.object(installer, "prerequisites", return_value=None) as prerequisites:
            self.assertEqual(installer.install(), 0)
        prerequisites.assert_called_once_with(["photon"])
        git_calls = [args for args, _ in self.commands.calls if args[0] == "/usr/bin/git"]
        fetch = next(args for args in git_calls if "fetch" in args)
        self.assertEqual(fetch[-4:], ["--depth", "1", "origin", setup.PHOTON_COMMIT])
        self.assertTrue(any(args[-3:] == ["checkout", "--detach", setup.PHOTON_COMMIT] for args in git_calls))
        self.assertTrue(any(setup.PHOTON_URL in args for args in git_calls))
        self.assertFalse(any(args[0] == "/usr/bin/sudo" for args, _ in self.commands.calls))

    def test_photon_origin_mismatch_is_rejected_before_fetch(self):
        installer = self.installer()
        installer.prepare()
        self.commands.origin = "https://example.invalid/other.git"
        with self.assertRaisesRegex(setup.SetupError, "origin differs"):
            installer.install_photon()
        self.assertFalse(any("fetch" in args for args, _ in self.commands.calls))

    def test_successful_processes_do_not_hide_failed_final_identity_checks(self):
        installer = self.installer(health("arjun"), health("arjun"))
        with patch.object(installer, "package_present", return_value=True):
            self.assertEqual(installer.install(), 1)
        self.assertTrue(any("incomplete" in message for message in self.messages))

    def test_template_failure_is_reported_even_if_all_engines_are_ready(self):
        installer = self.installer(health(), health())
        self.commands.failure = lambda args: "-update-templates" in args
        self.assertEqual(installer.install(update_templates=True), 1)
        self.assertTrue(any("TEMPLATE ERROR" in message for message in self.messages))

    def test_unrecognized_managed_folder_is_preserved(self):
        folder = setup.managed_root(self.home)
        folder.mkdir(parents=True)
        marker = folder / "personal.txt"
        marker.write_text("keep", encoding="utf-8")
        with self.assertRaisesRegex(setup.SetupError, "Unrecognized existing folder"):
            self.installer().prepare()
        self.assertEqual(marker.read_text(), "keep")
        self.assertFalse((folder / ".echo-recon-managed").exists())

    def test_redirected_managed_targets_stop_before_any_command(self):
        installer = self.installer()
        installer.prepare()
        sentinel = self.home / "outside-personal.txt"
        sentinel.write_text("keep untouched", encoding="utf-8")
        injected_paths = [
            (setup.go_target(self.home, "httpx").parent, lambda: installer.install_go("httpx", "/usr/bin/go")),
            (installer.base / "go-cache", lambda: installer.install_go("httpx", "/usr/bin/go")),
            (installer.base / f"photon-{setup.PHOTON_COMMIT}" / "source", installer.install_photon),
            (installer.base / f"arjun-{setup.ARJUN_VERSION}" / "venv", lambda: installer.install_python(installer.base / f"arjun-{setup.ARJUN_VERSION}", setup.ARJUN_PINS)),
            (installer.base / f"arjun-{setup.ARJUN_VERSION}" / "venv/bin", lambda: installer.install_python(installer.base / f"arjun-{setup.ARJUN_VERSION}", setup.ARJUN_PINS)),
        ]
        original_is_symlink = Path.is_symlink
        for redirected, action in injected_paths:
            with self.subTest(path=redirected), patch.object(Path, "is_symlink", autospec=True, side_effect=lambda path, selected=redirected: path == selected or original_is_symlink(path)):
                with self.assertRaisesRegex(setup.SetupError, "symlink"):
                    action()
            self.assertEqual(self.commands.calls, [])
            self.assertEqual(sentinel.read_text(), "keep untouched")

    def test_symlinked_user_bin_rejected_before_prerequisites(self):
        installer = self.installer(health("httpx"))
        redirected = self.home / ".local/bin"
        original_is_symlink = Path.is_symlink
        with patch.object(Path, "is_symlink", autospec=True, side_effect=lambda path: path == redirected or original_is_symlink(path)):
            with self.assertRaisesRegex(setup.SetupError, "symlink"):
                installer.install()
        self.assertEqual(self.commands.calls, [])

    def test_unverified_apt_shadow_is_preserved_with_actionable_error(self):
        state = health()
        state["nmap"].update(status="unverified", path=str(self.home / ".local/bin/nmap"))
        with self.assertRaisesRegex(setup.SetupError, "shadows Kali"):
            self.installer(state).install()
        self.assertEqual(self.commands.calls, [])

    def test_trusted_data_directory_places_lock_in_configured_folder(self):
        data = self.home / "custom-data"
        with patch.object(setup, "ROOT", self.home), patch.object(setup, "validate_platform", return_value="kali"), patch.object(setup, "Installer") as installer, redirect_stdout(io.StringIO()):
            installer.return_value.install.return_value = 0
            self.assertEqual(setup.main(["--install", "--data-dir", str(data)]), 0)
        self.assertTrue((data / "setup-tools.lock").is_file())
        self.assertFalse((self.home / "data").exists())

    def test_singleton_lock_stops_second_installer(self):
        data = self.home / "data"
        data.mkdir()
        lock = InstanceLock(data / "setup-tools.lock").acquire()
        try:
            with patch.object(setup, "ROOT", self.home), patch.object(setup, "validate_platform", return_value="kali"), patch.object(setup, "Installer") as installer, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(setup.main(["--install"]), 1)
                installer.assert_not_called()
                self.assertIn("already running", errors.getvalue())
        finally:
            lock.release()

    def test_pause_on_error_keeps_terminal_visible(self):
        with patch.object(setup, "validate_platform", side_effect=setup.SetupError("test failure")), patch.object(setup.sys.stdin, "isatty", return_value=True), patch("builtins.input", return_value="") as prompt, redirect_stderr(io.StringIO()):
            self.assertEqual(setup.main(["--install", "--pause"]), 1)
            prompt.assert_called_once()


if __name__ == "__main__":
    unittest.main()
