"""Check local backends once at CLI startup, then use the fixed setup launcher.

This module never accepts assessment targets or installer commands. Automatic
attempts are recorded so a failed setup does not loop on every app restart;
the dashboard's explicit setup button remains available for a deliberate retry.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import threading

from .tools import TOOLS, diagnostics


OWNER = "Echo Recon automatic tool setup"
SCHEMA = 1


def _redirected(path):
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        return True
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) &
                    getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 1024))
    except FileNotFoundError:
        return False


class StartupToolSetup:
    def __init__(self, setup, manager, *, version, check_tools=None, thread_factory=None):
        self.setup, self.manager = setup, manager
        self.version = str(version)
        self.check_tools = check_tools or diagnostics
        self.thread_factory = thread_factory or threading.Thread
        self.cancel = threading.Event()
        self.thread = None
        self.state_path = Path(setup.data) / "auto-setup.json"

    def start(self):
        """Mark the check pending before serving requests, without blocking startup."""
        with self.setup.guard:
            if self.thread is not None:
                return False
            if not self.setup.begin_startup_check():
                return False
            self.thread = self.thread_factory(target=self._run, daemon=True)
            try:
                self.thread.start()
            except (OSError, RuntimeError):
                self.setup.finish_startup_check(
                    "Automatic tool checking could not start. Use Check installed tools, then Setup all tools.")
                return False
        return True

    def close(self):
        """Cancel only our help checks; never terminate an installation in progress."""
        self.cancel.set()

    def fingerprint(self, missing):
        payload = [self.version, sys.platform, list(sys.version_info[:2]), sorted(missing)]
        return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()

    def attempts(self):
        if any(_redirected(part) for part in (*reversed(self.state_path.parents), self.state_path)):
            raise ValueError("Automatic setup state is redirected. Kept untouched; use Setup all tools manually.")
        if not self.state_path.exists():
            return []
        if not self.state_path.is_file() or self.state_path.stat().st_size > 8192:
            raise ValueError("Unrecognized automatic setup state was preserved. Use Setup all tools manually.")
        try:
            record = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError) as exc:
            raise ValueError("Unreadable automatic setup state was preserved. Use Setup all tools manually.") from exc
        valid = (isinstance(record, dict) and set(record) == {"owner", "schema", "attempts"} and
                 record["owner"] == OWNER and record["schema"] == SCHEMA and
                 isinstance(record["attempts"], list) and len(record["attempts"]) <= 32 and
                 all(isinstance(item, str) and len(item) == 64 and
                     all(char in "0123456789abcdef" for char in item) for item in record["attempts"]))
        if not valid:
            raise ValueError("Unrecognized automatic setup state was preserved. Use Setup all tools manually.")
        return record["attempts"]

    def remember(self, key, attempts):
        record = {"owner": OWNER, "schema": SCHEMA, "attempts": [*attempts[-31:], key]}
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.state_path.parent,
                                             prefix=".auto-setup-", suffix=".tmp", delete=False) as output:
                temporary = Path(output.name)
                json.dump(record, output, sort_keys=True)
                output.write("\n")
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.state_path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def _run(self):
        try:
            if not self.setup.supports_platform():
                self.setup.finish_startup_check(
                    "Automatic backend setup is unavailable on this platform. Use the official setup guide.")
                return
            health = self.check_tools(cancel=self.cancel)
            with self.setup.guard, self.manager.lock:
                if self.cancel.is_set():
                    self.setup.finish_startup_check("Automatic tool checking stopped.")
                    return
                missing = [name for name in TOOLS if health.get(name, {}).get("status") != "ready"]
                if not missing:
                    self.setup.finish_startup_check("All 8 tools passed local help/identity checks. No setup was needed.")
                    return
                if self.manager.active:
                    self.setup.finish_startup_check(
                        "Automatic setup was deferred while an assessment is active. Use Setup all tools afterward.")
                    return
                attempts = self.attempts()
                key = self.fingerprint(missing)
                if key in attempts:
                    self.setup.finish_startup_check(
                        "Automatic setup was already attempted for these missing tools. Use Setup all tools to retry.")
                    return
                self.remember(key, attempts)
                # Both locks remain held so an assessment/manual setup cannot
                # race between ending the check and launching the fixed worker.
                self.setup.finish_startup_check("Starting missing backend tools together.")
                self.setup.launch()
        except (ValueError, RuntimeError, OSError) as exc:
            self.setup.finish_startup_check(f"Automatic tool setup needs attention: {exc}")
        except Exception:
            self.setup.finish_startup_check(
                "Automatic tool checking failed. Use Check installed tools, then Setup all tools.")
