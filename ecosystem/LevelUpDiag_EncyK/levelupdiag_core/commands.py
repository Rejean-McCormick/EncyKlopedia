from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import time
import signal
import tempfile
from pathlib import Path
from .util import redact, tail_text

class CommandBlocked(RuntimeError):
    pass


def normalize_command(command):
    if isinstance(command, str):
        return shlex.split(command, posix=(os.name != "nt"))
    if isinstance(command, list) and all(isinstance(x, str) for x in command):
        return command
    raise ValueError("command must be a string or list of strings")


def which(name):
    return shutil.which(name)


def run_command(command, *, cwd: Path, timeout_seconds: int, capture_limit_kb=256,
                env=None, redact_output=True):
    argv = normalize_command(command)
    if not argv:
        raise ValueError("empty command")
    started = time.monotonic()
    limit = max(1, int(capture_limit_kb)) * 1024
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        cp = subprocess.Popen(
            argv,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=stdout_file,
            stderr=stderr_file,
            shell=False,
            start_new_session=os.name != 'nt',
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        )
        try:
            code = cp.wait(timeout=timeout_seconds)
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out, code = True, None
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(cp.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15, check=False)
            else:
                try: os.killpg(cp.pid, signal.SIGKILL)
                except ProcessLookupError: pass
            if cp.poll() is None: cp.kill()
            cp.wait(timeout=15)
        def bounded_read(stream):
            size = stream.seek(0, os.SEEK_END)
            # A small overlap lets redaction match secrets around the final capture boundary.
            stream.seek(max(0, size-limit-16384))
            return stream.read().decode('utf-8', errors='replace')
        out, err = bounded_read(stdout_file), bounded_read(stderr_file)
    duration = round(time.monotonic() - started, 3)
    if redact_output:
        out, err = redact(out), redact(err)
    return {
        "argv": [redact(arg) for arg in argv] if redact_output else argv,
        "cwd": str(cwd),
        "exit_code": code,
        "timed_out": timed_out,
        "duration_seconds": duration,
        "stdout_tail": tail_text(out, limit),
        "stderr_tail": tail_text(err, limit),
    }
