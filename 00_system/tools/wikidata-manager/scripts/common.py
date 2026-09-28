from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

ENCODING_OFFSETS = {"Q": 0, "P": 1_000_000_000, "L": 2_000_000_000}


def encode_wid(wid: str | None) -> int | None:
    if not wid or len(wid) < 2:
        return None
    p = wid[0].upper()
    if p not in ENCODING_OFFSETS or not wid[1:].isdigit():
        return None
    return ENCODING_OFFSETS[p] + int(wid[1:])


def decode_wid(value: int | None) -> str | None:
    if value is None:
        return None
    n = int(value)
    if n >= 2_000_000_000:
        return f"L{n - 2_000_000_000}"
    if n >= 1_000_000_000:
        return f"P{n - 1_000_000_000}"
    return f"Q{n}"


def normalize_name(value: str | None) -> str:
    if not value:
        return ""
    s = unicodedata.normalize("NFKD", value)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.casefold()
    s = re.sub(r"[^\w]+", " ", s, flags=re.UNICODE)
    return " ".join(s.split())


def human_bytes(n: int | float | None) -> str:
    if n is None:
        return "?"
    value = float(n)
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    for u in units:
        if value < 1024 or u == units[-1]:
            return f"{value:.2f} {u}"
        value /= 1024
    return f"{value:.2f} TiB"


def sha1_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def batched(seq: list[Any], n: int) -> Iterable[list[Any]]:
    for i in range(0, len(seq), n):
        yield seq[i:i+n]
