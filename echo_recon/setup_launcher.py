"""Launch only the repository's fixed platform installer and report progress."""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import threading
import time
import uuid

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
        self.log_path = None
        self.startup_checking = False
        self.startup_message = None

    def supports_platform(self):
        return sys.platform in {"win32", "linux", "darwin"}

    def begin_startup_check(self):
        with self.guard:
            if self.busy():
                return False
            self.startup_checking = True
            self.startup_message = "Checking required tools for first-run setup / প্রয়োজনীয় টুল যাচাই হচ্ছে…"
            return True

    def finish_startup_check(self, message):
        with self.guard:
            self.startup_checking = False
            self.startup_message = message

    def busy(self):
        if self.startup_checking:
            return True
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
                raise RuntimeError("Tool setup is already open. Wait for it to finish or close its terminal first.")
            if sys.platform == "win32":
                return self.launch_windows()
            if sys.platform == "darwin":
                return self.launch_macos()
            if not self.supports_platform():
                raise ValueError("Automatic tool setup supports native Windows, macOS and supported Linux distributions. See the setup guide for this platform.")
            script = self.root / "setup_tools.py"
            if not script.is_file():
                raise ValueError("Installer file is missing. Update the complete repository first.")
            manual = shlex.join([sys.executable, str(script), "--install", "--data-dir", str(self.data)])
            if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
                raise ValueError(f"No desktop terminal is available. In your Linux/WSL terminal run: {manual}")
            candidates = (
                ("qterminal", ["--title", "Echo Recon — tool setup", "-e"]),
                ("xfce4-terminal", ["--disable-server", "--title=Echo Recon — tool setup", "--execute"]),
                ("gnome-terminal", ["--wait", "--title=Echo Recon — tool setup", "--"]),
                ("konsole", ["--separate", "-e"]),
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
                    self.log_path = None
                    return {"launched": True, "message": "Setup terminal opened. Follow its progress; enter your sudo password only there if asked. Then close it and check installed tools again. / সেটআপ terminal দেখুন; প্রয়োজন হলে শুধু সেখানেই sudo password দিন। শেষে terminal বন্ধ করে আবার tool check করুন।"}
            raise ValueError(f"No supported desktop terminal found. In your Linux/WSL terminal run: {manual}")

    def launch_windows(self):
        """Run a fixed hidden worker; installer output is shown in the dashboard."""
        return self.launch_logged_worker("setup_tools_windows.py", "Windows")

    def launch_macos(self):
        """Use native Homebrew as the normal user; no password passes over HTTP."""
        return self.launch_logged_worker("setup_tools_macos.py", "macOS")

    def launch_logged_worker(self, filename, label):
        script = self.root / filename
        if not script.is_file():
            raise ValueError(f"{label} installer file is missing. Update the complete repository first.")
        logs = self.data / "setup-logs"
        logs.mkdir(parents=True, exist_ok=True, mode=0o700)
        log_path = logs / f"{uuid.uuid4().hex}.log"
        env = os.environ.copy()
        env.update(PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
        args = [sys.executable, str(script), "--install", "--data-dir", str(self.data)]
        options = ({"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)}
                   if label == "Windows" else {"start_new_session": True})
        with log_path.open("xb") as output:
            process = subprocess.Popen(args, cwd=self.root, shell=False,
                                       stdin=subprocess.DEVNULL, stdout=output,
                                       stderr=subprocess.STDOUT, env=env, **options)
        self.process, self.log_path = process, log_path
        self.pending_until = 0
        return {"launched": True,
                "message": f"{label} tool setup started. Follow progress here; the final result will identify any manual steps."}

    def status(self):
        with self.guard:
            if self.startup_checking:
                return {"running": True, "checking": True, "exit_code": None,
                        "message": self.startup_message, "log": ""}
            running = self.busy()
            exit_code = self.process.poll() if self.process else None
            if running:
                message = ("Tool setup is running. Follow progress below." if self.log_path else
                           "Tool setup is open. Follow its terminal and close it when finished.")
            elif self.process and not self.log_path:
                message = "Setup terminal closed. Review its output and check installed tools again."
            elif exit_code == 0:
                message = "Tool setup finished successfully. Installed tools are being checked again."
            elif exit_code == 2:
                message = "Tool setup needs manual action. Review the progress below, including any platform prerequisite steps."
            elif exit_code is not None:
                message = f"Tool setup failed (exit {exit_code}). Review the progress below before retrying."
            else:
                message = self.startup_message or "No tool setup is running."
            log = ""
            if self.log_path:
                try:
                    limit = 60 * 1024
                    with self.log_path.open("rb") as output:
                        output.seek(0, os.SEEK_END)
                        size = output.tell()
                        output.seek(max(0, size - limit))
                        log = output.read(limit).decode("utf-8", errors="replace")
                    if size > limit:
                        log = "[Earlier setup output omitted.]\n" + log
                except OSError:
                    log = "Setup output is temporarily unavailable."
            return {"running": running, "exit_code": exit_code,
                    "message": message, "log": log}
