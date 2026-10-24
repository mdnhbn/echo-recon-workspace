"""Cleanup must not follow a redirected scratch root into unrelated data."""
import os
from pathlib import Path
import tempfile
import unittest

from echo_recon.storage import Store
from maintenance import remove_demos


class MaintenancePathTests(unittest.TestCase):
    def test_redirected_scratch_root_refuses_cleanup_before_deleting_records(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data, external = root / "data", root / "unrelated"
            data.mkdir()
            demo_id = "a" * 32
            artifact = external / demo_id
            artifact.mkdir(parents=True)
            evidence = artifact / "keep.txt"
            evidence.write_text("unrelated data", encoding="utf-8")
            store = Store(data / "history.sqlite3")
            demo = {"id": demo_id, "updated": "2026", "demo": True}
            store.save(demo)
            try:
                os.symlink(external, data / "scratch", target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"Directory symlinks unavailable: {exc}")
            try:
                with self.assertRaisesRegex(RuntimeError, "redirected"):
                    remove_demos(data)
                self.assertEqual(evidence.read_text(encoding="utf-8"), "unrelated data")
                self.assertEqual(store.get(demo_id), demo)
            finally:
                (data / "scratch").unlink()


if __name__ == "__main__":
    unittest.main()
