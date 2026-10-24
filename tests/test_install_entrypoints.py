"""Exercise real installer entry scripts with inert temporary interpreters."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell.exe")


@unittest.skipUnless(os.name == "nt" and POWERSHELL, "Windows PowerShell installer entrypoint")
class WindowsInstallEntrypointTests(unittest.TestCase):
    def run_installer(self, existing=False):
        temporary = tempfile.TemporaryDirectory(prefix="echo installer fixture ")
        self.addCleanup(temporary.cleanup)
        folder = Path(temporary.name)
        shutil.copyfile(ROOT / "install.ps1", folder / "install.ps1")
        calls = folder / "calls.jsonl"
        fake_python = folder / "fake-py.ps1"
        fake_python.write_text(r'''
$entry = @{kind='selected'; argv=@($args)} | ConvertTo-Json -Compress
Add-Content -LiteralPath $env:ECHO_TEST_CALLS -Value $entry
if ($args -contains 'venv') { $global:LASTEXITCODE=55; return }
if (($args -join ' ') -match 'print') {
    if ($args[0] -eq '-3.12') { Write-Output '3.12' } else { Write-Output '3.14' }
}
$global:LASTEXITCODE=0
''', encoding="utf-8")
        existing_python = folder / "fake-existing.ps1"
        existing_python.write_text(r'''
Add-Content -LiteralPath $env:ECHO_TEST_CALLS -Value '{"kind":"existing","argv":[]}'
Write-Output '3.11'
$global:LASTEXITCODE=0
''', encoding="utf-8")
        sentinel = folder / ".venv" / "personal.txt"
        if existing:
            sentinel.parent.mkdir()
            sentinel.write_bytes(b"keep this environment unchanged")
        harness = folder / "harness.ps1"
        harness.write_text(r'''
function Get-Command {
    param([string]$Name, [string]$ErrorAction)
    if ($Name -eq 'py') { [pscustomobject]@{Source=$env:ECHO_TEST_PY} }
    else { throw 'Unexpected command lookup in inert installer fixture.' }
}
function Join-Path {
    param([string]$Path, [string]$ChildPath)
    if ($env:ECHO_TEST_HAS_VENV -eq 'yes' -and $ChildPath.Replace('\','/') -eq '.venv/Scripts/python.exe') {
        return $env:ECHO_TEST_EXISTING
    }
    Microsoft.PowerShell.Management\Join-Path -Path $Path -ChildPath $ChildPath
}
& (Microsoft.PowerShell.Management\Join-Path $env:ECHO_TEST_FOLDER 'install.ps1') -DashboardOnly
''', encoding="utf-8")
        env = dict(os.environ, ECHO_TEST_CALLS=str(calls), ECHO_TEST_PY=str(fake_python),
                   ECHO_TEST_EXISTING=str(existing_python), ECHO_TEST_FOLDER=str(folder),
                   ECHO_TEST_HAS_VENV="yes" if existing else "no")
        result = subprocess.run([POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(harness)],
                                capture_output=True, text=True, env=env, timeout=20)
        entries = [json.loads(line) for line in calls.read_text(encoding="utf-8-sig").splitlines()] if calls.exists() else []
        return result, entries, sentinel

    def test_first_run_prefers_available_312_over_newer_default_python(self):
        result, entries, sentinel = self.run_installer()
        selected = [entry["argv"] for entry in entries if entry["kind"] == "selected"]
        self.assertNotEqual(result.returncode, 0)  # Inert venv command deliberately stops here.
        self.assertIn("Virtual environment creation failed", result.stdout + result.stderr)
        self.assertTrue(selected, result.stdout + result.stderr)
        self.assertTrue(all(args[0] == "-3.12" for args in selected), selected)
        self.assertTrue(any("venv" in args for args in selected))
        self.assertFalse(any("pip" in args for args in selected))
        self.assertFalse(sentinel.parent.exists())

    def test_mismatched_existing_venv_is_preserved_before_venv_or_pip(self):
        result, entries, sentinel = self.run_installer(existing=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("different Python version", result.stdout + result.stderr)
        self.assertIn("preserved", result.stdout + result.stderr)
        self.assertEqual(sentinel.read_bytes(), b"keep this environment unchanged")
        self.assertTrue(any(entry["kind"] == "existing" for entry in entries))
        self.assertFalse(any("venv" in entry["argv"] or "pip" in entry["argv"] for entry in entries))


@unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "Linux Bash installer entrypoint")
class LinuxInstallEntrypointTests(unittest.TestCase):
    def test_mismatched_existing_venv_stops_before_venv_or_pip(self):
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            self.skipTest("Installer intentionally refuses root; run this fixture as a normal user")
        with tempfile.TemporaryDirectory(prefix="echo installer fixture ") as directory:
            folder = Path(directory)
            shutil.copyfile(ROOT / "install.sh", folder / "install.sh")
            fake_bin = folder / "fake bin"
            fake_bin.mkdir()
            selected = fake_bin / "python3"
            selected.write_text('''#!/bin/sh
printf 'selected %s\\n' "$*" >> "$ECHO_TEST_CALLS"
case "$*" in
  *print*) printf '3.12\\n' ;;
  *venv*|*pip*) exit 55 ;;
esac
exit 0
''', encoding="utf-8")
            selected.chmod(0o755)
            existing = folder / ".venv/bin/python"
            existing.parent.mkdir(parents=True)
            existing.write_text('''#!/bin/sh
printf 'existing %s\\n' "$*" >> "$ECHO_TEST_CALLS"
printf '3.11\\n'
''', encoding="utf-8")
            existing.chmod(0o755)
            sentinel = folder / ".venv/personal.txt"
            sentinel.write_bytes(b"keep exactly")
            calls = folder / "calls.txt"
            env = dict(os.environ, PATH=str(fake_bin) + os.pathsep + os.environ.get("PATH", ""),
                       ECHO_TEST_CALLS=str(calls))
            result = subprocess.run([shutil.which("bash"), str(folder / "install.sh"), "--dashboard-only"],
                                    env=env, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("different Python version", result.stdout + result.stderr)
            self.assertIn("preserved", result.stdout + result.stderr)
            self.assertEqual(sentinel.read_bytes(), b"keep exactly")
            log = calls.read_text(encoding="utf-8")
            self.assertIn("existing -c", log)
            self.assertNotIn("-m venv", log)
            self.assertNotIn("-m pip", log)


if __name__ == "__main__":
    unittest.main()
