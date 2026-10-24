"""Cancellable subprocesses with bounded combined output and wall time."""
from dataclasses import dataclass
import os
import signal
import subprocess
import threading
import time


class WindowsProcessJob:
    """Own a suspended child's complete process tree without elevation.

    The child is assigned before its initial thread runs. Closing this handle
    kills any descendants, including after the top-level executable exits.
    If Windows cannot create/assign the job, callers fail closed.
    """
    creationflags = 0x00000004 | 0x08000000  # CREATE_SUSPENDED | CREATE_NO_WINDOW

    def __init__(self):
        import ctypes
        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                        ("flags", wintypes.DWORD), ("minimum_working_set", ctypes.c_size_t),
                        ("maximum_working_set", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("scheduling", wintypes.DWORD)]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in
                        ("read_operations", "write_operations", "other_operations",
                         "read_bytes", "write_bytes", "other_bytes")]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("basic", BasicLimits), ("io", IoCounters),
                        ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                        ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]

        class ThreadEntry(ctypes.Structure):
            _fields_ = [("size", wintypes.DWORD), ("usage", wintypes.DWORD),
                        ("thread_id", wintypes.DWORD), ("owner_pid", wintypes.DWORD),
                        ("base_priority", wintypes.LONG), ("delta_priority", wintypes.LONG),
                        ("flags", wintypes.DWORD)]

        self.ctypes, self.ThreadEntry = ctypes, ThreadEntry
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        declarations = {
            "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
            "CreateToolhelp32Snapshot": ([wintypes.DWORD, wintypes.DWORD], wintypes.HANDLE),
            "Thread32First": ([wintypes.HANDLE, ctypes.POINTER(ThreadEntry)], wintypes.BOOL),
            "Thread32Next": ([wintypes.HANDLE, ctypes.POINTER(ThreadEntry)], wintypes.BOOL),
            "OpenThread": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "ResumeThread": ([wintypes.HANDLE], wintypes.DWORD),
        }
        for name, (arguments, result) in declarations.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = arguments, result
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x00002000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def attach_and_resume(self, proc):
        ctypes = self.ctypes
        handle = self.kernel.OpenProcess(0x0101, False, proc.pid)  # SET_QUOTA | TERMINATE
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not self.kernel.AssignProcessToJobObject(self.handle, handle):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.kernel.CloseHandle(handle)
        snapshot = self.kernel.CreateToolhelp32Snapshot(0x00000004, 0)  # SNAPTHREAD
        if snapshot == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        threads = []
        try:
            entry = self.ThreadEntry()
            entry.size = ctypes.sizeof(entry)
            present = self.kernel.Thread32First(snapshot, ctypes.byref(entry))
            while present:
                if entry.owner_pid == proc.pid:
                    threads.append(entry.thread_id)
                entry.size = ctypes.sizeof(entry)
                present = self.kernel.Thread32Next(snapshot, ctypes.byref(entry))
        finally:
            self.kernel.CloseHandle(snapshot)
        if len(threads) != 1:
            raise OSError("Cannot identify the suspended tool's initial thread; tool was not run.")
        thread = self.kernel.OpenThread(0x0002, False, threads[0])  # THREAD_SUSPEND_RESUME
        if not thread:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if self.kernel.ResumeThread(thread) == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            self.kernel.CloseHandle(thread)

    def close(self):
        if getattr(self, "handle", None):
            self.kernel.CloseHandle(self.handle)
            self.handle = None


@dataclass
class Result:
    status: str
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration: float = 0


def terminate(proc, job=None):
    try:
        if os.name == "posix":
            os.killpg(proc.pid, signal.SIGTERM)
        elif job is not None:
            job.close()
        else:
            # taskkill is invoked directly; no shell or interpolated command text.
            killer = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "taskkill.exe")
            try:
                subprocess.run([killer, "/PID", str(proc.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=3, check=False)
            except OSError:
                proc.terminate()
        proc.wait(timeout=1)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            if os.name == "posix":
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        except (ProcessLookupError, OSError):
            pass


def run(args, *, cancel, timeout=120, stdin="", cwd=None, max_bytes=250_000):
    if cancel.is_set():
        return Result("cancelled")
    start = time.monotonic()
    proc, job = None, None
    try:
        if os.name == "nt":
            job = WindowsProcessJob()
        proc = subprocess.Popen(args, shell=False, cwd=cwd, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=(os.name == "posix"),
                                creationflags=job.creationflags if job else 0)
        if job:
            job.attach_and_resume(proc)
    except OSError as exc:
        if job:
            job.close()
        if proc:
            try:
                proc.kill()
                proc.wait(timeout=3)
            finally:
                for pipe in (proc.stdin, proc.stdout, proc.stderr):
                    pipe.close()
        missing = proc is None and isinstance(exc, FileNotFoundError)
        return Result("missing" if missing else "error",
                      stderr="Executable not found." if missing else str(exc))
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
            terminate(proc, job)
            break
        time.sleep(0.05)
    proc.wait()
    if job:
        # Close before draining: a surviving descendant may still hold pipes.
        job.close()
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
