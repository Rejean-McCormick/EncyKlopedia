from __future__ import annotations

import bz2
import contextlib
import gzip
import importlib.util
import json
import mmap
import os
import pickle
import struct
from pathlib import Path
from typing import Any, Iterator

ENTRY_STRUCT = struct.Struct('<QII')  # decoded offset, raw line bytes, flags
ENTRY_SIZE = ENTRY_STRUCT.size


def _try_import(name: str):
    try:
        return __import__(name)
    except Exception:
        return None

_ORJSON = _try_import('orjson')
_RAPIDGZIP = _try_import('rapidgzip')
_INDEXED_BZIP2 = _try_import('indexed_bzip2')


def json_backend() -> str:
    return 'orjson' if _ORJSON is not None else 'json'


def loads(data: bytes | str) -> Any:
    if _ORJSON is not None:
        return _ORJSON.loads(data)
    if isinstance(data, bytes):
        data = data.decode('utf-8')
    return json.loads(data)


def dumps(obj: Any, *, sort_keys: bool = False) -> bytes:
    if _ORJSON is not None:
        opt = 0
        if sort_keys:
            opt |= _ORJSON.OPT_SORT_KEYS
        return _ORJSON.dumps(obj, option=opt)
    return json.dumps(obj, ensure_ascii=False, sort_keys=sort_keys, separators=(',', ':')).encode('utf-8')


def recommended_threads(root: Path | None = None) -> int:
    logical = os.cpu_count() or 4
    physical = None
    if root is not None:
        p = Path(root) / '00_system' / 'config' / 'environment.json'
        try:
            env = json.loads(p.read_text(encoding='utf-8-sig'))
            physical = int((env.get('cpu') or {}).get('physical_cores') or 0) or None
        except Exception:
            pass
    if physical is None:
        physical = max(1, logical // 2) if logical >= 8 else logical
    return max(1, min(physical, 12))


def backend_capabilities(path: Path, root: Path | None = None) -> dict[str, Any]:
    low = path.name.lower()
    threads = recommended_threads(root)
    if low.endswith('.gz'):
        if _RAPIDGZIP is not None:
            return {'compression': 'gzip', 'backend': 'rapidgzip', 'parallel': True, 'random_access': True, 'threads': threads}
        return {'compression': 'gzip', 'backend': 'gzip-stdlib', 'parallel': False, 'random_access': False, 'threads': 1}
    if low.endswith('.bz2'):
        if _INDEXED_BZIP2 is not None:
            return {'compression': 'bzip2', 'backend': 'indexed_bzip2', 'parallel': True, 'random_access': True, 'threads': threads}
        return {'compression': 'bzip2', 'backend': 'bz2-stdlib', 'parallel': False, 'random_access': False, 'threads': 1}
    return {'compression': 'plain', 'backend': 'plain', 'parallel': False, 'random_access': True, 'threads': 1}


class DumpStream:
    def __init__(self, path: Path, *, threads: int = 0, index_path: Path | None = None, root: Path | None = None):
        self.path = Path(path)
        self.root = root
        self.threads = threads or recommended_threads(root)
        self.index_path = Path(index_path) if index_path else None
        self.file = None
        self.backend = None
        self.random_access = False
        self._index_loaded = False

    def __enter__(self):
        low = self.path.name.lower()
        if low.endswith('.gz') and _RAPIDGZIP is not None:
            self.file = _RAPIDGZIP.open(str(self.path), parallelization=self.threads)
            self.backend = 'rapidgzip'
            self.random_access = True
            if self.index_path and self.index_path.exists():
                try:
                    self.file.import_index(str(self.index_path))
                    self._index_loaded = True
                except Exception:
                    pass
        elif low.endswith('.bz2') and _INDEXED_BZIP2 is not None:
            self.file = _INDEXED_BZIP2.open(str(self.path), parallelization=self.threads)
            self.backend = 'indexed_bzip2'
            self.random_access = True
            if self.index_path and self.index_path.exists():
                try:
                    with self.index_path.open('rb') as f:
                        self.file.set_block_offsets(pickle.load(f))
                    self._index_loaded = True
                except Exception:
                    pass
        elif low.endswith('.gz'):
            self.file = gzip.open(self.path, 'rb')
            self.backend = 'gzip-stdlib'
            self.random_access = False
        elif low.endswith('.bz2'):
            self.file = bz2.open(self.path, 'rb')
            self.backend = 'bz2-stdlib'
            self.random_access = False
        else:
            self.file = self.path.open('rb')
            self.backend = 'plain'
            self.random_access = True
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.file is not None:
            self.file.close()
        self.file = None

    def tell(self) -> int:
        return int(self.file.tell())

    def seek(self, offset: int):
        if not self.random_access:
            raise RuntimeError(f'Random access unavailable for backend {self.backend}')
        return self.file.seek(offset)

    def read(self, n: int = -1) -> bytes:
        return self.file.read(n)

    def readline(self) -> bytes:
        return self.file.readline()

    def export_index(self, path: Path | None = None) -> Path | None:
        target = Path(path or self.index_path) if (path or self.index_path) else None
        if target is None:
            return None
        target.parent.mkdir(parents=True, exist_ok=True)
        if self.backend == 'rapidgzip':
            self.file.export_index(str(target))
            return target
        if self.backend == 'indexed_bzip2':
            offsets = self.file.block_offsets()
            with target.open('wb') as f:
                pickle.dump(offsets, f, protocol=pickle.HIGHEST_PROTOCOL)
            return target
        return None


def normalize_dump_line(raw: bytes) -> bytes | None:
    s = raw.strip()
    if not s or s in {b'[', b']'}:
        return None
    if s.endswith(b','):
        s = s[:-1]
    return s


def iter_dump_raw(path: Path, *, threads: int = 0, index_path: Path | None = None, root: Path | None = None, with_offsets: bool = False, export_index_path: Path | None = None) -> Iterator[Any]:
    with DumpStream(path, threads=threads, index_path=index_path, root=root) as ds:
        while True:
            start = ds.tell()
            raw = ds.readline()
            if not raw:
                break
            end = ds.tell()
            s = normalize_dump_line(raw)
            if s is None:
                continue
            if with_offsets:
                yield s, start, end - start, ds.backend
            else:
                yield s
        if export_index_path is not None:
            try:
                ds.export_index(export_index_path)
            except Exception:
                pass


class DenseQidLocatorWriter:
    def __init__(self, path: Path, initial_capacity: int = 160_000_000, *, resume: bool = False, max_seen: int = 0):
        self.path = Path(path)
        self.initial_capacity = max(1_000_000, int(initial_capacity))
        self.resume = bool(resume)
        self.capacity = 0
        self.max_seen = max(0, int(max_seen))
        self._fh = None
        self._mm = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.resume and self.path.exists() and self.path.stat().st_size >= ENTRY_SIZE:
            self._fh = self.path.open('r+b')
            self.capacity = self.path.stat().st_size // ENTRY_SIZE
        else:
            self._fh = self.path.open('w+b')
            self.capacity = self.initial_capacity
            self._fh.truncate(self.capacity * ENTRY_SIZE)
        self._mm = mmap.mmap(self._fh.fileno(), 0, access=mmap.ACCESS_WRITE)
        return self

    def _grow(self, qid: int):
        if qid < self.capacity:
            return
        self._mm.flush(); self._mm.close()
        new_capacity = max(qid + 1, int(self.capacity * 1.35))
        self._fh.truncate(new_capacity * ENTRY_SIZE)
        self.capacity = new_capacity
        self._mm = mmap.mmap(self._fh.fileno(), 0, access=mmap.ACCESS_WRITE)

    def set(self, qid: int, decoded_offset: int, raw_bytes: int, flags: int = 1):
        if qid < 0:
            return
        self._grow(qid)
        ENTRY_STRUCT.pack_into(self._mm, qid * ENTRY_SIZE, int(decoded_offset), int(raw_bytes), int(flags))
        if qid > self.max_seen:
            self.max_seen = qid

    def __exit__(self, exc_type, exc, tb):
        if self._mm is not None:
            self._mm.flush(); self._mm.close()
        if self._fh is not None:
            if exc_type is None:
                self._fh.truncate((self.max_seen + 1) * ENTRY_SIZE)
            self._fh.close()
        self._mm = None; self._fh = None


class DenseQidLocatorReader:
    def __init__(self, path: Path):
        self.path = Path(path)
        self._fh = None
        self._mm = None
        self.count = 0

    def __enter__(self):
        self._fh = self.path.open('rb')
        size = self.path.stat().st_size
        self.count = size // ENTRY_SIZE
        self._mm = mmap.mmap(self._fh.fileno(), 0, access=mmap.ACCESS_READ)
        return self

    def get(self, qid: int) -> tuple[int, int, int] | None:
        if qid < 0 or qid >= self.count:
            return None
        off, length, flags = ENTRY_STRUCT.unpack_from(self._mm, qid * ENTRY_SIZE)
        if flags == 0 or length == 0:
            return None
        return int(off), int(length), int(flags)

    def __exit__(self, exc_type, exc, tb):
        if self._mm is not None: self._mm.close()
        if self._fh is not None: self._fh.close()
        self._mm = None; self._fh = None


def module_status(root: Path | None = None) -> dict[str, Any]:
    return {
        'json_backend': json_backend(),
        'orjson': _ORJSON is not None,
        'rapidgzip': _RAPIDGZIP is not None,
        'indexed_bzip2': _INDEXED_BZIP2 is not None,
        'recommended_threads': recommended_threads(root),
    }
