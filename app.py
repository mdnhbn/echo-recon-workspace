#!/usr/bin/env python3
"""Local entry point; installing or running as root is unnecessary."""
import os
import argparse
from pathlib import Path
import signal
import threading
from werkzeug.serving import make_server
from echo_recon import __version__
from echo_recon.browser import URL, has_desktop, open_when_ready
from echo_recon.web import create_app
from echo_recon.locking import InstanceLock
from echo_recon.bootstrap import StartupToolSetup


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Echo Recon local dashboard")
    parser.add_argument("--version", action="version", version=f"Echo Recon {__version__}")
    parser.add_argument("--no-browser", action="store_true", help="Start the server without opening a browser")
    parser.add_argument("--no-tool-setup", action="store_true",
                        help="Skip automatic backend setup at startup; manual setup remains available")
    return parser.parse_args(argv)


def data_directory():
    """Use an explicit per-user data folder when packaged; keep clone defaults."""
    configured = os.environ.get("ECHO_RECON_DATA_DIR")
    return Path(configured).expanduser() if configured else Path(__file__).resolve().parent / "data"


if __name__ == "__main__":
    args = parse_args()
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise SystemExit("Run as your normal user, not root.")
    os.umask(0o077)
    data = data_directory()
    data.mkdir(mode=0o700, exist_ok=True)
    # Acquire before recovery so a second instance cannot mark an active run interrupted.
    try:
        instance_lock = InstanceLock(data / "server.lock").acquire()
    except RuntimeError as exc:
        raise SystemExit(str(exc))
    app = create_app(data_dir=data)
    browser_stop = threading.Event()
    startup_setup = None

    def stop(signum, frame):
        browser_stop.set()
        if startup_setup:
            startup_setup.close()
        app.extensions["echo_manager"].close()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print(f"Echo Recon {__version__} — {URL} (local only)", flush=True)
    server = None
    try:
        # Bind first: never open another app's page if this port is already occupied.
        server = make_server("127.0.0.1", 8001, app, threaded=True)
        if not args.no_tool_setup:
            startup_setup = StartupToolSetup(app.extensions["echo_setup"],
                                             app.extensions["echo_manager"], version=__version__)
            startup_setup.start()
        if not args.no_browser and has_desktop():
            threading.Thread(target=open_when_ready, args=(browser_stop,), daemon=True).start()
        elif not args.no_browser:
            print(f"No desktop session detected. Open {URL} in your browser.", flush=True)
        print("Local development server. Keep this terminal open; Ctrl+C stops it.", flush=True)
        server.serve_forever()
    finally:
        browser_stop.set()
        if startup_setup:
            startup_setup.close()
        if server:
            server.server_close()
        app.extensions["echo_manager"].close()
        instance_lock.release()
