"""Skope-owned adapter for existing, verified Wikidata fast-access sidecars.

No index construction, full dump scan or cross-repository imports. The exact
reader and index formats are retained to reuse existing data-volume files.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from . import fastio


def dump_descriptor(root: Path, dump: Path) -> dict:
    root, dump = Path(root), Path(dump)
    verified = root / '20_evidence/manifests/wikidata-dump-verified.json'
    manifest = {}
    if verified.is_file():
        try:
            candidate = json.loads(verified.read_text(encoding='utf-8-sig'))
            if isinstance(candidate, dict):
                name = Path(str(candidate.get('file') or candidate.get('filename') or '')).name
                if not name or name == dump.name:
                    manifest = candidate
        except (ValueError, OSError):
            pass
    sha1 = str(manifest.get('sha1') or manifest.get('expected_sha1') or '').lower()
    if not re.fullmatch(r'[a-f0-9]{40}', sha1):
        weak = hashlib.sha256(f'{dump.name}|{dump.stat().st_size}'.encode()).hexdigest()[:24]
        dump_id = 'file-' + weak
    else:
        dump_id = 'sha1-' + sha1
    return {'dump_id': dump_id, 'filename': dump.name, 'sha1': sha1 or None}


def fast_access_status(root: Path, dump: Path) -> tuple[bool, dict]:
    root, dump = Path(root), Path(dump)
    descriptor = dump_descriptor(root, dump)
    index_dir = root / '30_working' / 'wikidata-fast' / descriptor['dump_id']
    locator = index_dir / 'qid-locator.bin'
    compression = index_dir / ('compression.gzindex' if dump.name.lower().endswith('.gz') else 'compression.bz2blocks.pkl')
    source = 'fast-access'
    if not locator.is_file():
        base = root / '30_working/wikidata'
        global_locator = base / 'qid-locator.bin'
        if global_locator.is_file():
            locator = global_locator
            compression = base / compression.name
            source = 'global-builder'
    backend = fastio.backend_capabilities(dump, root)
    ok = locator.is_file()
    ready = bool(ok and (dump.name.lower().endswith('.json') or compression.is_file()) and backend.get('random_access'))
    return ok, {'complete': ok, 'path': str(index_dir), 'locator_path': str(locator),
                'compression_index_path': str(compression), 'locator_source': source,
                'runtime_backend': backend, 'random_access_ready': ready}


def fast_fetch_raw(root: Path, dump: Path, qids, threads: int = 0) -> dict[str, bytes]:
    ok, info = fast_access_status(root, dump)
    if not ok or not info['random_access_ready']:
        return {}
    wanted = []
    with fastio.DenseQidLocatorReader(Path(info['locator_path'])) as locator:
        for wid in qids:
            if isinstance(wid, str) and re.fullmatch(r'Q[1-9][0-9]*', wid):
                loc = locator.get(int(wid[1:]))
                if loc:
                    wanted.append((loc[0], loc[1], wid))
    wanted.sort()
    data = {}
    compression = Path(info['compression_index_path'])
    with fastio.DumpStream(dump, threads=threads, index_path=compression if compression.is_file() else None, root=root) as stream:
        if not stream.random_access:
            return {}
        for offset, length, wid in wanted:
            stream.seek(offset)
            raw = fastio.normalize_dump_line(stream.read(length))
            if raw is not None:
                data[wid] = raw
    return data
