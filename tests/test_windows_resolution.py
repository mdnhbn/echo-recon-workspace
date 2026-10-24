import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from echo_recon import tools
from echo_recon.runner import Result


class WindowsResolutionTests(unittest.TestCase):
    def test_managed_httpx_precedes_path_without_changing_environment(self):
        prefix = ("C:/Example User/EchoRecon/httpx/httpx.exe",)
        before = os.environ.get("PATH")
        def execute(args, **kwargs):
            return Result("done", 0, "ProjectDiscovery httpx -rate-limit -silent")
        with patch.object(tools, "is_windows", return_value=True), \
             patch.object(tools, "managed_windows_command", side_effect=lambda name: prefix if name == "httpx" else None), \
             patch.object(tools.shutil, "which", return_value=None), patch.object(tools, "run", side_effect=execute):
            health = tools.diagnostics()
            self.assertEqual(health["httpx"]["status"], "ready")
            self.assertEqual(health["httpx"]["command"], list(prefix))
            self.assertEqual(tools.command("httpx", "example.com", 2, Path("unused"))[0], prefix[0])
        self.assertEqual(os.environ.get("PATH"), before)

    def test_python_tool_uses_explicit_interpreter_and_entrypoint(self):
        prefix = ("C:/isolated/python.exe", "C:/isolated/photon.py")
        with patch.object(tools, "native_tool_command", side_effect=lambda name: prefix if name == "photon" else None), \
             patch.object(tools.shutil, "which", return_value=None), \
             patch.object(tools, "run", return_value=Result("done", 0, "Photon -h")) as execute:
            self.assertEqual(tools.diagnostics()["photon"]["status"], "ready")
            self.assertEqual(execute.call_args.args[0], [*prefix, "-h"])
            self.assertEqual(tools.command("photon", "example.com", 1, Path("output"))[:2], list(prefix))

    def test_official_nmap_directory_is_found_without_path_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            nmap = Path(directory) / "Nmap" / "nmap.exe"
            nmap.parent.mkdir()
            nmap.write_bytes(b"fixture only")
            with patch.object(tools, "is_windows", return_value=True), \
                 patch.object(tools, "managed_windows_command", return_value=None), \
                 patch.dict(os.environ, {"ProgramFiles": directory}):
                self.assertEqual(tools.native_tool_command("nmap"), (str(nmap),))

    def test_non_windows_does_not_read_windows_installations(self):
        with patch.object(tools, "is_windows", return_value=False), \
             patch.object(tools, "managed_windows_command") as managed, \
             patch.object(tools.shutil, "which", return_value="/usr/bin/nmap"):
            self.assertEqual(tools.resolve_tool("nmap"), ("/usr/bin/nmap",))
            managed.assert_not_called()

    def test_missing_managed_install_stays_missing(self):
        with patch.object(tools, "native_tool_command", return_value=None), \
             patch.object(tools.shutil, "which", return_value=None), patch.object(tools, "run") as execute:
            self.assertTrue(all(item["status"] == "missing" for item in tools.diagnostics().values()))
            execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
