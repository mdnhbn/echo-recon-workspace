"""Cancellable subprocesses with bounded combined output and wall time."""
from dataclasses import dataclass
import os
import signal
import subprocess
import threading
import time


@dataclass
class Result:
    status: str
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration: float = 0


def terminate(proc):
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGTERM)
        else:
            proc.terminate()
        proc.wait(timeout=1)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            if os.name == "posix":
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        except ProcessLookupError:
            pass


def run(args, *, cancel, timeout=120, stdin="", cwd=None, max_bytes=250_000):
    if cancel.is_set():
        return Result("cancelled")
    start = time.monotonic()
    try:
        proc = subprocess.Popen(args, shell=False, cwd=cwd, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=(os.name == "posix"))
    except FileNotFoundError:
        return Result("missing", stderr="Executable not found.")
    except OSError as exc:
        return Result("error", stderr=str(exc))
    buffers = [bytearray(), bytearray()]
    total = [0]
    guard = threading.Lock()
    exceeded = threading.Event()

    def drain(stream, index):
        while True:
            chunk = stream.read(4096)
            if not chunk:
                break
            with guard:
                remaining = max(0, max_bytes - total[0])
                buffers[index].extend(chunk[:remaining])
                total[0] += len(chunk)
                if total[0] > max_bytes:
                    exceeded.set()
        stream.close()

    readers = [threading.Thread(target=drain, args=(proc.stdout, 0), daemon=True),
               threading.Thread(target=drain, args=(proc.stderr, 1), daemon=True)]
    for reader in readers:
        reader.start()
    try:
        proc.stdin.write(stdin.encode())
        proc.stdin.close()
    except BrokenPipeError:
        pass
    state = None
    while proc.poll() is None:
        if cancel.is_set():
            state = "cancelled"
        elif exceeded.is_set():
            state = "output_limit"
        elif time.monotonic() - start >= timeout:
            state = "timeout"
        if state:
            terminate(proc)
            break
        time.sleep(0.05)
    proc.wait()
    # A child may hold inherited pipes open after the parent exits.
    for reader in readers:
        reader.join(timeout=1)
    if any(reader.is_alive() for reader in readers) and os.name == "posix":
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        for reader in readers:
            reader.join(timeout=1)
    state = state or ("output_limit" if exceeded.is_set() else
                      "done" if proc.returncode == 0 else "error")
    return Result(state, proc.returncode, buffers[0].decode(errors="replace"),
                  buffers[1].decode(errors="replace"), round(time.monotonic() - start, 2))
