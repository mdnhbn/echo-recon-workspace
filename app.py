#!/usr/bin/env python3
"""Local entry point; installing or running as root is unnecessary."""
import os
from pathlib import Path
import signal
from echo_recon.web import create_app


if __name__ == "__main__":
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise SystemExit("Run as your normal user, not root.")
    os.umask(0o077)
    data = Path(__file__).resolve().parent / "data"
    data.mkdir(mode=0o700, exist_ok=True)
    # Acquire before recovery so a second instance cannot mark an active run interrupted.
    if os.name == "posix":
        import fcntl
        instance_lock = (data / "server.lock").open("a")
        try:
            fcntl.flock(instance_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("This data directory already has a running dashboard.")
    app = create_app()

    def stop(signum, frame):
        app.extensions["echo_manager"].close()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print("Echo Recon 6.0 — http://127.0.0.1:8001 (local only)")
    app.run(host="127.0.0.1", port=8001, debug=False, use_reloader=False, threaded=True)
