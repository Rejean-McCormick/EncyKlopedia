from __future__ import annotations

import os
from pathlib import Path
from .util import is_excluded


def iter_files(root: Path, cfg, *, max_files=None, extra_globs=()):
    scan = cfg.get("scan", {})
    excluded = set(scan.get("exclude_dirs", []))
    limit = int(max_files or scan.get("max_files", 20000))
    count = 0
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dp = Path(dirpath)
        rel_dir = dp.relative_to(root)
        dirnames[:] = [d for d in dirnames if d not in excluded]
        for name in filenames:
            p = dp / name
            try:
                rel = p.relative_to(root).as_posix()
                parts = p.relative_to(root).parts[:-1]
            except ValueError:
                continue
            if is_excluded(rel, parts, excluded, extra_globs):
                continue
            yield p, rel
            count += 1
            if count >= limit:
                return
