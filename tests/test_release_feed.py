"""Real Debian version comparisons for the release feed; no network or install."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.platform == "linux" and shutil.which("dpkg-deb") and shutil.which("bash"),
                     "Debian archive tools are required")
class ReleaseFeedTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="echo release feed ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.pool = self.root / "pool"
        self.pool.mkdir()

    def add_package(self, version):
        package = self.root / ("source-" + version)
        control = package / "DEBIAN/control"
        control.parent.mkdir(parents=True)
        control.write_text(f"Package: echo-recon\nVersion: {version}\nArchitecture: all\n"
                           "Maintainer: Test <test@example.invalid>\nDescription: Test fixture\n",
                           encoding="utf-8")
        archive = self.pool / f"echo-recon_{version}_all.deb"
        subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(package), str(archive)],
                       check=True, capture_output=True, text=True, timeout=20)
        return archive

    def check_version(self, version):
        return subprocess.run(["bash", str(ROOT / "packaging/check-feed-version.sh"),
                               version, str(self.pool)], capture_output=True, text=True, timeout=10)

    def test_older_release_is_refused_without_changing_published_bytes(self):
        archive = self.add_package("6.7.1")
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        result = self.check_version("6.7.0")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("older version 6.7.0", result.stderr)
        self.assertEqual(list(self.pool.iterdir()), [archive])
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), digest)

    def test_same_version_is_allowed_for_existing_idempotent_publish_check(self):
        self.add_package("6.7.1")
        self.assertEqual(self.check_version("6.7.1").returncode, 0)

    def test_debian_numeric_order_is_used_instead_of_text_order(self):
        self.add_package("6.7.9")
        self.assertEqual(self.check_version("6.7.10").returncode, 0)

    def test_every_published_archive_is_considered(self):
        self.add_package("6.7.0")
        self.add_package("6.8.0")
        self.assertNotEqual(self.check_version("6.7.1").returncode, 0)

    def test_first_release_accepts_empty_feed(self):
        self.assertEqual(self.check_version("6.7.1").returncode, 0)


if __name__ == "__main__":
    unittest.main()
