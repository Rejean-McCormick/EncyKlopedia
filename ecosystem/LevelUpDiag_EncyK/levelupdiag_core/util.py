from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

SECRET_VALUE_RE = re.compile(
    r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token)"
    r"(\s*[:=]\s*)([^\s,;\]\[}\{]{4,})"
)
BEARER_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}")


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def safe_rel(path: Path, root: Path):
    try:
        return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()
    except Exception:
        return str(path)


def is_excluded(rel: str, parts, excluded_dirs, extra_globs=()):
    if any(p in excluded_dirs for p in parts):
        return True
    return any(fnmatch.fnmatch(rel, pat) for pat in extra_globs)


def bounded_text(path: Path, max_bytes: int):
    try:
        with path.open("rb") as f:
            raw = f.read(max_bytes + 1)
        if len(raw) > max_bytes:
            return None
        if b"\x00" in raw:
            return None
        return raw.decode("utf-8", errors="replace")
    except (OSError, PermissionError):
        return None


def sha256_file(path: Path, max_bytes=None):
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk: break
            total += len(chunk)
            if max_bytes is not None and total > max_bytes:
                return None
            h.update(chunk)
    return h.hexdigest()


def redact(text: str, replacement="<REDACTED>"):
    for key, value in os.environ.items():
        if len(value) >= 4 and re.search(r'password|secret|token|database_url|api_?key', key, re.I):
            text = text.replace(value, replacement)
    text = re.sub(r'(?i)\b([a-z][a-z0-9+.-]*://)[^\s/"\'<>]+@', lambda m: m.group(1)+replacement+'@', text)
    text = SECRET_VALUE_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}{replacement}", text)
    text = BEARER_RE.sub(f"Bearer {replacement}", text)
    return text


def tail_text(text: str, limit_bytes: int):
    raw = text.encode("utf-8", errors="replace")
    if len(raw) <= limit_bytes:
        return text
    return "<truncated>\n" + raw[-limit_bytes:].decode("utf-8", errors="replace")
