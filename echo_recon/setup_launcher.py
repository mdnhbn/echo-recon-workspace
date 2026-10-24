"""Open only the repository's fixed installer in a local Kali terminal."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

from .locking import InstanceLock


def is_kali():
    if sys.platform != "linux":
        return False
    try:
        return "ID=kali" in Path("/etc/os-release").read_text(encoding="utf-8").splitlines()
    except OSError:
        return False


class SetupLauncher:
    def __init__(self, root, data):
        self.root, self.data = Path(root).resolve(), Path(data).resolve()
        self.guard = threading.RLock()
        self.process = None
        self.pending_until = 0

    def busy(self):
        if time.monotonic() < self.pending_until or (self.process and self.process.poll() is None):
            return True
        lock = InstanceLock(self.data / "setup-tools.lock")
        if not lock.path.parent.exists():
            return False
        try:
            lock.acquire()
        except RuntimeError:
            return True
        else:
            lock.release()
            return False

    def launch(self):
        with self.guard:
            if self.busy():
                raise RuntimeError("Tool setup is already open. Finish or close its terminal first.")
            if not is_kali():
                raise ValueError("Automatic tool setup runs inside Kali Linux. On Windows use the Kali WSL terminal and the setup guide.")
            if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
                raise ValueError("No desktop terminal is available. In your Kali terminal run: .venv/bin/python setup_tools.py --install")
            script = self.root / "setup_tools.py"
            if not script.is_file():
                raise ValueError("Installer file is missing. Update the complete repository first.")
            candidates = (
                ("qterminal", ["--title", "Echo Recon — tool setup", "-e"]),
                ("xfce4-terminal", ["--disable-server", "--title=Echo Recon — tool setup", "--execute"]),
                ("xterm", ["-T", "Echo Recon — tool setup", "-e"]),
                ("x-terminal-emulator", ["-T", "Echo Recon — tool setup", "-e"]),
            )
            for name, flags in candidates:
                executable = shutil.which(name)
                if executable:
                    args = [executable, *flags, sys.executable, str(script), "--install", "--pause",
                            "--data-dir", str(self.data)]
                    self.process = subprocess.Popen(args, cwd=self.root, start_new_session=True,
                                                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                                    stderr=subprocess.DEVNULL)
                    self.pending_until = time.monotonic() + 5
                    return {"launched": True, "message": "Setup terminal opened. Follow its progress; enter your sudo password only there if asked. Then close it and check installed tools again. / সেটআপ terminal দেখুন; প্রয়োজন হলে শুধু সেখানেই sudo password দিন। শেষে terminal বন্ধ করে আবার tool check করুন।"}
            raise ValueError("No supported desktop terminal found. In your Kali terminal run: .venv/bin/python setup_tools.py --install")
