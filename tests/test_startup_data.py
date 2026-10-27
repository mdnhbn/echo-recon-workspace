"""Fresh per-user data paths must work before the local server starts."""
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class DataDirectoryStartupTests(unittest.TestCase):
    def test_fresh_nested_data_directory_is_created_before_app_and_lock(self):
        class ReachedApp(Exception):
            pass

        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder) / "new-user" / ".local" / "share" / "echo-recon"

            def reached_app(*, data_dir):
                self.assertEqual(data_dir, data)
                self.assertTrue(data.is_dir())
                raise ReachedApp

            with patch.dict(os.environ, {"ECHO_RECON_DATA_DIR": str(data)}), \
                 patch.object(sys, "argv", ["app.py", "--no-browser", "--no-tool-setup"]), \
                 patch("os.geteuid", return_value=1000, create=True), \
                 patch("os.umask"), \
                 patch("echo_recon.locking.InstanceLock") as lock, \
                 patch("echo_recon.web.create_app", side_effect=reached_app):
                with self.assertRaises(ReachedApp):
                    runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
                lock.assert_called_once_with(data / "server.lock")
                lock.return_value.acquire.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
