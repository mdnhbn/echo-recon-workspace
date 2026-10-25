"""Open our local dashboard after the already-bound server becomes ready."""
import http.client
import os
import sys
import time
import webbrowser

URL = "http://127.0.0.1:8001"


def ready():
    # HTTPConnection to a literal loopback address ignores proxy environment settings.
    conn = http.client.HTTPConnection("127.0.0.1", 8001, timeout=.5)
    try:
        conn.request("GET", "/")
        response = conn.getresponse()
        return response.status == 200
    except (OSError, http.client.HTTPException):
        return False
    finally:
        conn.close()


def open_when_ready(stop, *, probe=ready, opener=webbrowser.open, timeout=10):
    """Called only after CLI server binding, never from app factories or tests."""
    deadline = time.monotonic() + timeout
    while not stop.is_set() and time.monotonic() < deadline:
        if probe():
            if stop.is_set():
                return False
            try:
                opened = opener(URL, new=2)
            except (webbrowser.Error, OSError):
                opened = False
            if not opened:
                print(f"Browser did not open. Open this address manually: {URL}", flush=True)
            return bool(opened)
        stop.wait(.2)
    return False


def has_desktop():
    # A headless Linux/WSL session should not unexpectedly start lynx/w3m in its terminal.
    if sys.platform == "darwin":
        return not bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_TTY"))
    return os.name == "nt" or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
