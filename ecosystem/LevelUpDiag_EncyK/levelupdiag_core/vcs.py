from __future__ import annotations

import stat
from pathlib import Path
from .commands import run_command, which


def git_info(target: Path):
    if not which("git") or not (target / ".git").exists():
        return {"available": bool(which("git")), "repository": False}
    def g(args, timeout=15):
        return run_command(["git", *args], cwd=target, timeout_seconds=timeout, capture_limit_kb=64)
    head = g(["rev-parse", "--verify", "HEAD"])
    branch = g(["branch", "--show-current"])
    status_result = g(["status", "--porcelain=v1", "--untracked-files=no"])
    return {
        "available": True,
        "repository": True,
        "head": head["stdout_tail"].strip() if head["exit_code"] == 0 else None,
        "branch": branch["stdout_tail"].strip() if branch["exit_code"] == 0 else None,
        "tracked_status": status_result["stdout_tail"],
    }


def _confined_file(target: Path, relative: str):
    rel = Path(relative)
    if rel.is_absolute():
        raise ValueError('Generated tracked file paths must be relative to the target repository.')
    root = target.resolve(strict=False)
    path = (root / rel).resolve(strict=False)
    if not path.is_relative_to(root) or path == root:
        raise ValueError('Generated tracked file paths must stay inside the target repository.')
    return path, rel.as_posix()


def snapshot_tracked_files(target: Path, relatives):
    """Capture exact baseline bytes for known build-generated tracked files.

    Only files already tracked by Git and present at campaign start are captured.
    This preserves any user pre-run modifications byte-for-byte.
    """
    if not which('git') or not (target / '.git').exists():
        return {}
    snapshots = {}
    for relative in relatives or ():
        path, rel = _confined_file(target, str(relative))
        tracked = run_command(['git', 'ls-files', '--error-unmatch', '--', rel], cwd=target,
                              timeout_seconds=15, capture_limit_kb=16)
        if tracked['exit_code'] != 0 or not path.is_file():
            continue
        snapshots[rel] = {
            'content': path.read_bytes(),
            'mode': stat.S_IMODE(path.stat().st_mode),
        }
    return snapshots


def restore_tracked_files(target: Path, snapshots):
    """Restore captured generated files to their exact pre-campaign contents."""
    restored = []
    for relative, snapshot in (snapshots or {}).items():
        path, rel = _confined_file(target, relative)
        content = snapshot['content']
        if path.is_file() and path.read_bytes() == content:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        try:
            path.chmod(snapshot['mode'])
        except OSError:
            pass
        restored.append(rel)
    return restored
