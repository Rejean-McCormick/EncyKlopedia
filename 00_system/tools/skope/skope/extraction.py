"""Opt-in full Wikidata entity extraction from an existing Skope QID inventory.

Never scans an entire Wikidata dump or updates the compact SQLite index. A verified
local dump and an already built random-access locator are prerequisites. All work
is resumable in the data volume; the Kristal canon is never opened for writing.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from . import massive

TOOL = Path(__file__).resolve().parents[1]
REPO = TOOL.parents[2]
PROFILES = TOOL / 'config' / 'extraction-profiles'
_LOCK = threading.RLock()
_RUNNING = {}
JOB_RE = re.compile(r'^[a-f0-9]{32}$')
QID_RE = re.compile(r'^Q[1-9][0-9]*$')
PID_RE = re.compile(r'^[a-z0-9][a-z0-9_-]{0,100}$')


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _atomic(path, obj):
    path = Path(path)
    tmp = path.with_name(path.name + '.part')
    tmp.write_text(_json(obj) + '\n', encoding='utf8')
    os.replace(tmp, path)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _sha_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def _module():
    path = REPO / '00_system/tools/scope-builder/scripts'
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    import scope_common
    return scope_common


def profiles():
    result = []
    for path in sorted(PROFILES.glob('*.json')):
        if path.is_symlink():
            continue
        try:
            p = json.loads(path.read_text(encoding='utf-8-sig'))
            if p.get('format') == 'skope.extraction-profile/draft-1':
                result.append({'id': path.stem, 'title': p.get('title', path.stem), 'profile_id': p.get('profile_id')})
        except (OSError, ValueError):
            pass
    return result


def load_profile(profile_id):
    if not isinstance(profile_id, str) or not PID_RE.fullmatch(profile_id):
        raise ValueError('Select an installed extraction profile')
    path = PROFILES / (profile_id + '.json')
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 256_000:
        raise ValueError('Extraction profile is missing or too large')
    profile = json.loads(path.read_text(encoding='utf-8-sig'))
    if profile.get('format') != 'skope.extraction-profile/draft-1':
        raise ValueError('Unsupported extraction profile format')
    spec = profile.get('extraction') or {}
    if spec.get('mode') != 'full_source_entity_json' or spec.get('output_compression') != 'gzip-jsonl':
        raise ValueError('This version supports full JSON entity extraction to gzip-jsonl only')
    size = spec.get('batch_size')
    if not isinstance(size, int) or isinstance(size, bool) or not 1 <= size <= 2000:
        raise ValueError('batch_size must be 1..2000')
    source = profile.get('source') or {}
    if source.get('allow_full_dump_scan') or source.get('auto_build_new_index') or not source.get('abort_if_no_verified_random_access'):
        raise ValueError('Unsafe extraction profile: full scans or new indexing are disallowed')
    if not source.get('require_verified_source_identity'):
        raise ValueError('Source identity verification must be enabled')
    if (profile.get('selection') or {}).get('inventory_record_field') not in (None, 'wikidata_qid'):
        raise ValueError('Only wikidata_qid records are supported')
    if (profile.get('selection') or {}).get('rediscover_scope') is not False:
        raise ValueError('This action only extracts existing QID inventories')
    if (profile.get('selection') or {}).get('preserve_exact_inventory') is not True:
        raise ValueError('Must preserve the exact source inventory')
    if spec.get('on_missing_qid') not in (None, 'report_and_pause'):
        raise ValueError('Missing source QIDs must be reported and paused')
    if (profile.get('target') or {}).get('write_to_canon') is not False:
        raise ValueError('Cannot write to the Kristal canon')
    if (profile.get('safety') or {}).get('no_kristal_canonical_modification') is not True:
        raise ValueError('Explicit no-canon safety declaration is required')
    return profile


def _data_root(index):
    index = Path(index).resolve(strict=True)
    if index.parent.name.lower() != 'wikidata' or index.parent.parent.name.lower() != '30_working':
        raise ValueError('Skope index must be under the data volume / 30_working / wikidata')
    return index.parent.parent.parent


def _within(path, folder):
    return path == folder or folder in path.parents


def _source_path(obj, root):
    p = Path(obj).resolve(strict=False)
    if not _within(p, root):
        raise ValueError('Extraction paths must remain within the EncyK data root')
    return p


def _inventory(index, profile, requested_job=None):
    source_job = requested_job or profile['selection'].get('source_job')
    if not isinstance(source_job, str) or not JOB_RE.fullmatch(source_job):
        raise ValueError('Choose a completed 32-character Skope QID job ID')
    folder = massive._path(index, source_job)
    try:
        summary = massive.status(index, source_job)
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError('Source QID recipe/status is invalid or has changed') from exc
    if summary['state'] != 'completed' or not summary['output_ready']:
        raise ValueError('The source QID inventory must be completed')
    inventory = folder / 'selected-qids.jsonl'
    if inventory.is_symlink() or not inventory.is_file():
        raise ValueError('QID inventory must be an ordinary local file')
    return source_job, inventory, summary


def _inventory_info(path):
    h = hashlib.sha256()
    count = 0
    last = 0
    with path.open('rb') as stream:
        for line in stream:
            h.update(line)
            if not line.strip():
                raise ValueError('Blank line in QID inventory')
            v = json.loads(line)
            if not isinstance(v, dict) or not QID_RE.fullmatch(str(v.get('wikidata_qid', ''))):
                raise ValueError('Invalid QID inventory record')
            n = int(v['wikidata_qid'][1:])
            if n <= last:
                raise ValueError('QID inventory must be strictly sorted with no duplicates')
            last = n
            count += 1
    return count, h.hexdigest()


def _check_source(profile, root):
    source = profile['source']
    dump = _source_path(source['dump_path'], root)
    manifest_path = _source_path(source['verify_dump_identity_from_manifest'], root)
    fast_dir = _source_path(source['existing_fast_index_root'], root)
    blockers = []
    result = {'dump': str(dump), 'manifest': str(manifest_path), 'fast_index_root': str(fast_dir),
              'verified': False, 'random_access_ready': False}
    if not dump.is_file():
        blockers.append('Source dump not found: ' + str(dump))
        return result, blockers
    if not manifest_path.is_file():
        blockers.append('Verified dump manifest not found: ' + str(manifest_path))
        return result, blockers
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
        sha1 = str(manifest.get('sha1') or manifest.get('expected_sha1') or '').lower()
        filename = Path(str(manifest.get('file') or manifest.get('filename') or '')).name
        byte_count = manifest.get('bytes') or manifest.get('file_size') or manifest.get('size_bytes')
        declared_verified = manifest.get('verified') is True or manifest.get('verification_status') in ('verified', 'ok')
        if not re.fullmatch(r'[a-f0-9]{40}', sha1) or not declared_verified:
            blockers.append('Dump manifest lacks an explicitly verified SHA-1; no 96 GiB hash or full scan will run automatically')
        if filename and filename != dump.name:
            blockers.append('Dump filename differs from its verification manifest')
        if byte_count is not None and int(byte_count) != dump.stat().st_size:
            blockers.append('Dump size differs from its verification manifest')
        if byte_count is None:
            blockers.append('Verified dump manifest must include the dump size')
        result['sha1'] = sha1
        result['source_size_bytes'] = dump.stat().st_size
    except (ValueError, OSError, TypeError) as exc:
        blockers.append('Invalid verification manifest: ' + str(exc))
        return result, blockers
    result['verified'] = not blockers
    # Use the *existing* Scope Builder access-check and locator. No new index and no dump scan.
    if not _within(fast_dir, root / '30_working') or fast_dir.name != 'wikidata-fast':
        blockers.append('Fast index root must be 30_working/wikidata-fast')
        return result, blockers
    # Old 0.10 builder's dump identity is SHA-1 based. Confirm matching sidecar identity.
    expected = fast_dir / ('sha1-' + sha1)
    sidecar = expected / 'manifest.json'
    if not sidecar.is_file():
        blockers.append('Matching fast-access manifest is missing: ' + str(sidecar))
    else:
        try:
            side = json.loads(sidecar.read_text(encoding='utf8'))
            desc = side.get('dump') or {}
            if side.get('complete') is not True or desc.get('sha1') != sha1 or desc.get('bytes') != dump.stat().st_size:
                blockers.append('Fast-access sidecar does not match the verified dump')
        except (OSError, ValueError) as exc:
            blockers.append('Invalid fast-access sidecar: ' + str(exc))
    if not blockers:
        try:
            common = _module()
            ok, info = common.fast_access_status(root, dump)
            result['random_access_ready'] = bool(ok and info.get('random_access_ready'))
            result['fast_backend'] = (info.get('runtime_backend') or {}).get('backend', 'unknown')
            if not result['random_access_ready']:
                blockers.append('Random access unavailable; check indexed_bzip2 and existing qid-locator.bin / compression.bz2blocks.pkl')
        except Exception as exc:
            blockers.append('Random-access dependency check failed: ' + type(exc).__name__ + ': ' + str(exc))
    return result, blockers


def preflight(index, profile_id, source_job=None):
    p = load_profile(profile_id)
    root = _data_root(index)
    job, inventory, summary = _inventory(index, p, source_job)
    count, fingerprint = _inventory_info(inventory)
    blockers = []
    if p['selection'].get('expected_qids') and count != p['selection']['expected_qids']:
        blockers.append(f'Inventory has {count} QIDs, expected {p["selection"]["expected_qids"]}')
    if summary['selected'] != count:
        blockers.append('QID inventory count differs from the completed job state')
    recipe = massive._path(index, job) / 'recipe.json'
    if recipe.is_symlink() or not recipe.is_file():
        blockers.append('Source QID recipe is missing or linked outside the job')
    recipe_sha = _sha_file(recipe) if recipe.is_file() and not recipe.is_symlink() else None
    profile_sha = _sha(_json(p).encode('utf8'))
    source, source_blockers = _check_source(p, root)
    blockers.extend(source_blockers)
    output = p['output']
    evidence = _source_path(output['evidence_root'], root)
    working = _source_path(output['working_root'], root)
    if not _within(evidence, root / '20_evidence') or not _within(working, root / '30_working'):
        blockers.append('Outputs must stay in 20_evidence and 30_working')
    if not PID_RE.fullmatch(output.get('scope_key','')):
        blockers.append('Invalid output scope key')
    if not output.get('no_extra_backup_or_archive'):
        blockers.append('Extra backup/archive generation is forbidden')
    free = shutil.disk_usage(root).free
    min_bytes = int((p['safety'].get('minimum_free_space_gib') or 20) * 1024**3)
    if free < min_bytes:
        blockers.append('Insufficient free space on data volume (required: at least ' + str(min_bytes // 1024**3) + ' GiB)')
    return {'profile': profile_id, 'profile_title': p.get('title', profile_id), 'source_job': job,
            'total': count, 'inventory_sha256': fingerprint, 'qid_recipe_sha256': recipe_sha,
            'profile_sha256': profile_sha,
            'batch_size': p['extraction']['batch_size'], 'workers': p['extraction'].get('workers', 1),
            'source': source, 'evidence_root': str(evidence), 'working_root': str(working),
            'ready': not blockers, 'blockers': blockers,
            'warnings': ['This is lossless Wikidata JSON, not certified biological or medical evidence.',
                         'Canada / North America are annotation priorities, not verified occurrence filters.',
                         'The dump manifest is trusted as an existing verification record; the 96 GiB checksum is not recalculated.',
                         'No changes to Kristal canon, Wikidata dump or SQLite index.']}


def _extract_root(index):
    return _data_root(index) / '30_working/skope-extractions'


def _folder(index, extract_id):
    if not isinstance(extract_id, str) or not JOB_RE.fullmatch(extract_id):
        raise ValueError('Invalid extraction job ID')
    p = _extract_root(index) / extract_id
    if not p.is_dir() or p.is_symlink():
        raise ValueError('Extraction job not found')
    return p


def _state(folder):
    result = json.loads((folder / 'state.json').read_text(encoding='utf8'))
    if result['state'] in ('running', 'queued', 'finalizing') and folder.name not in _RUNNING:
        result['state'] = 'interrupted'
        result['message'] = 'Server stopped; resume to continue at the last committed batch.'
    result['job'] = folder.name
    result['evidence_ready'] = result['state'] == 'completed' and Path(result.get('evidence_path', '')).is_dir()
    return result


def status(index, extract_id):
    return _state(_folder(index, extract_id))


def latest(index):
    folder = _extract_root(index)
    if not folder.is_dir():
        return None
    jobs = [p for p in folder.iterdir() if p.is_dir() and not p.is_symlink() and JOB_RE.fullmatch(p.name) and (p / 'state.json').is_file()]
    return _state(max(jobs, key=lambda x: x.stat().st_mtime)) if jobs else None


def _recover_published(index, folder, state, profile):
    root = _data_root(index)
    evidence = _source_path(profile['output']['evidence_root'], root)
    if evidence.is_dir():
        for candidate in evidence.glob('wikidata-*'):
            p = candidate / 'snapshot-manifest.json'
            if not p.is_file() or candidate.is_symlink(): continue
            try:
                m = json.loads(p.read_text(encoding='utf8'))
            except (OSError, ValueError): continue
            if (m.get('source_job') == state['source_job'] and m.get('source_sha1') == state['source_sha1']
                    and m.get('inventory_sha256') == state['inventory_sha256']
                    and m.get('record_count') == state['total']):
                # Ensure all published chunks are intact after a crash before reporting completion.
                if all((candidate/x['file']).is_file() and _sha_file(candidate/x['file']) == x['sha256'] for x in m.get('parts',[])):
                    _save(folder, state, state='completed', evidence_path=str(candidate),
                          message='Recovered an already completed immutable evidence snapshot')
                    return _state(folder)
    return None


def start(index, profile_id, source_job=None, resume=None, confirmed=False):
    if confirmed is not True:
        raise ValueError('Explicit user confirmation is required')
    check = preflight(index, profile_id, source_job)
    if not check['ready']:
        raise ValueError('Extraction blocked: ' + '; '.join(check['blockers']))
    with _LOCK:
        if _RUNNING:
            raise ValueError('Another full-record extraction is currently running')
        if resume:
            folder = _folder(index, resume)
            state = _state(folder)
            if state['state'] not in ('paused', 'interrupted', 'failed', 'missing_source_records'):
                raise ValueError('Only paused/interrupted/failed extractions can resume')
            if (state['profile'] != profile_id or state['source_job'] != check['source_job']
                    or state['inventory_sha256'] != check['inventory_sha256'] or state['source_sha1'] != check['source']['sha1']
                    or state.get('qid_recipe_sha256') != check['qid_recipe_sha256']
                    or state.get('profile_sha256') != check['profile_sha256']):
                raise ValueError('Cannot resume: profile, QID inventory or source changed')
            if state['state'] == 'interrupted' and state.get('processed') == state.get('total'):
                found = _recover_published(index, folder, state, load_profile(profile_id))
                if found: return found
            _save(folder, state, state='queued', message='Queued to resume from verified batches')
        else:
            root = _extract_root(index)
            root.mkdir(parents=True, exist_ok=True)
            folder = root / uuid.uuid4().hex
            folder.mkdir()
            p = load_profile(profile_id)
            _atomic(folder / 'profile.json', p)
            _atomic(folder / 'state.json', {
                'state': 'queued', 'profile': profile_id, 'source_job': check['source_job'],
                'source_sha1': check['source']['sha1'], 'inventory_sha256': check['inventory_sha256'],
                'qid_recipe_sha256': check['qid_recipe_sha256'], 'profile_sha256': check['profile_sha256'],
                'processed': 0, 'total': check['total'], 'chunks': 0, 'missing': 0,
                'message': 'Queued', 'evidence_path': '', 'updated_at': time.time()})
        event = threading.Event()
        _RUNNING[folder.name] = event
        threading.Thread(target=_worker, args=(str(index), folder, event), daemon=True, name='skope-full-' + folder.name[:8]).start()
    return _state(folder)


def pause(index, extract_id):
    _folder(index, extract_id)
    with _LOCK:
        event = _RUNNING.get(extract_id)
        if event is None:
            raise ValueError('Extraction is not running')
        event.set()
    return {'job': extract_id, 'state': 'pausing', 'message': 'Pause requested; current batch will finish.'}


def _save(folder, record, **kwargs):
    record.update(kwargs)
    record['updated_at'] = time.time()
    _atomic(folder / 'state.json', record)


def _read_ids(inventory):
    with Path(inventory).open('rb') as fh:
        for line in fh:
            yield json.loads(line)['wikidata_qid']


def _batches(inventory, size):
    block = []
    for qid in _read_ids(inventory):
        block.append(qid)
        if len(block) == size:
            yield block
            block = []
    if block:
        yield block


def _save_batch(folder, index, qids, offset, profile, root):
    common = _module()
    dump = _source_path(profile['source']['dump_path'], root)
    dest = folder / 'chunks'
    dest.mkdir(exist_ok=True)
    piece = dest / ('part-%06d.jsonl.gz' % offset)
    meta_path = dest / ('part-%06d.manifest.json' % offset)
    if piece.exists() and meta_path.exists():
        manifest = json.loads(meta_path.read_text(encoding='utf8'))
        if (manifest.get('qids') == qids and manifest.get('sha256') == _sha_file(piece)
                and manifest.get('source_sha1') == json.loads((folder / 'state.json').read_text())['source_sha1']):
            return manifest, True
        raise ValueError('Existing partial batch has changed: ' + piece.name)
    if piece.exists() or meta_path.exists():
        raise ValueError('Incomplete batch files: manual review required: ' + piece.name)
    raw_map = common.fast_fetch_raw(root, dump, qids, threads=min(8, max(1, int(profile['extraction'].get('workers', 1)))))
    missing = [q for q in qids if q not in raw_map]
    if missing:
        _atomic(folder / 'missing-qids.json', {'count': len(missing), 'qids': missing, 'batch': offset,
                                               'policy': 'pause_and_review', 'source': dump.name})
        raise LookupError(f'{len(missing)} QIDs not available through verified random access; no full-scan fallback')
    records = []
    part = piece.with_name(piece.name + '.part')
    try:
        with part.open('wb') as stream:
            with gzip.GzipFile(fileobj=stream, filename='', mode='wb', compresslevel=6, mtime=0) as gz:
                for qid in qids:
                    raw = raw_map[qid]
                    entity = json.loads(raw)
                    if not isinstance(entity, dict) or entity.get('id') != qid:
                        raise ValueError('Source entity JSON ID mismatch for ' + qid)
                    gz.write(raw + b'\n')
                    records.append({'wikidata_qid': qid, 'sha256': _sha(raw), 'raw_bytes': len(raw)})
        digest = _sha_file(part)
        os.replace(part, piece)
        manifest = {'qids': qids, 'source_sha1': json.loads((folder / 'state.json').read_text())['source_sha1'],
                    'records': records, 'record_count': len(qids), 'sha256': digest, 'filename': piece.name}
        _atomic(meta_path, manifest)
        return manifest, False
    finally:
        if part.exists():
            part.unlink()


def _finalize(index, folder, profile, state, root):
    output = profile['output']
    evidence_root = _source_path(output['evidence_root'], root)
    evidence_root.mkdir(parents=True, exist_ok=True)
    summaries = []
    for path in sorted((folder / 'chunks').glob('*.manifest.json')):
        item = json.loads(path.read_text(encoding='utf8'))
        part = folder / 'chunks' / item['filename']
        if _sha_file(part) != item['sha256']:
            raise ValueError('Part digest mismatch during finalization')
        summaries.append({'file': item['filename'], 'sha256': item['sha256'], 'count': item['record_count'],
                          'manifest_file': path.name})
    if sum(v['count'] for v in summaries) != state['total']:
        raise ValueError('Batch count mismatch; refusing finalization')
    identity = _sha(_json({'inventory_sha256': state['inventory_sha256'],
                           'source_sha1': state['source_sha1'], 'parts': summaries}).encode())[:20]
    snapshot = evidence_root / ('wikidata-' + identity)
    manifest = {'schema_version': 'skope.full-wikidata-evidence/1', 'scope_key': output['scope_key'],
                'source_job': state['source_job'], 'source_sha1': state['source_sha1'],
                'inventory_sha256': state['inventory_sha256'], 'qid_recipe_sha256': state['qid_recipe_sha256'],
                'profile_sha256': state['profile_sha256'], 'record_count': state['total'],
                'parts': summaries, 'profile': profile['profile_id'], 'source_dump': profile['source']['dump_path'],
                'data_preservation': 'Original complete Wikidata JSON with labels, aliases, claims, qualifiers, references and sitelinks',
                'geography': profile['geography'],
                'geography_coverage': 'not_assessed; no geographic absence inferred',
                'kristal_canon_modified': False, 'created_at': time.time()}
    if snapshot.exists():
        if (snapshot / 'snapshot-manifest.json').is_file() and json.loads((snapshot / 'snapshot-manifest.json').read_text(encoding='utf8')).get('parts') == summaries:
            return snapshot
        raise ValueError('Snapshot destination exists with different content; refusing overwrite')
    chunks = folder / 'chunks'
    if not chunks.is_dir():
        raise ValueError('No chunk directory available for publication')
    _atomic(chunks / 'snapshot-manifest.json', manifest)
    os.replace(chunks, snapshot)  # D: -> D:, atomic directory promotion; no duplicate backup
    return snapshot


def _worker(index, folder, stop):
    state = json.loads((folder / 'state.json').read_text(encoding='utf8'))
    profile = json.loads((folder / 'profile.json').read_text(encoding='utf8'))
    root = _data_root(index)
    inv = massive._path(index, state['source_job']) / 'selected-qids.jsonl'
    try:
        count, digest = _inventory_info(inv)
        if count != state['total'] or digest != state['inventory_sha256']:
            raise ValueError('QID inventory changed since preflight: refusing extraction')
        _save(folder, state, state='running', message='Extracting verified full JSON entities from existing fast index')
        for batch_number, qids in enumerate(_batches(inv, profile['extraction']['batch_size'])):
            if stop.is_set():
                _save(folder, state, state='paused', message='Paused at a complete batch boundary')
                return
            if batch_number * profile['extraction']['batch_size'] < state['processed']:
                continue
            item, reused = _save_batch(folder, index, qids, batch_number, profile, root)
            _save(folder, state, processed=state['processed'] + len(qids), chunks=state['chunks'] + 1,
                  message=f'Committed batch {batch_number + 1}: {len(qids)} complete source entities'+(' (resumed)' if reused else ''))
        if state['processed'] != state['total']:
            raise ValueError('Processed count mismatch; cannot complete')
        _save(folder, state, state='finalizing', message='Verifying checksums and promoting immutable evidence')
        snapshot = _finalize(index, folder, profile, state, root)
        _save(folder, state, state='completed', evidence_path=str(snapshot), message='Complete Wikidata evidence ready; review before any Kristal integration')
    except LookupError as exc:
        _save(folder, state, state='missing_source_records', message=str(exc))
    except Exception as exc:
        _save(folder, state, state='failed', message=f'{type(exc).__name__}: {exc}'[:350])
    finally:
        with _LOCK:
            _RUNNING.pop(folder.name, None)


def open_results(index, extract_id):
    state = status(index, extract_id)
    if not state['evidence_ready']:
        raise ValueError('Completed evidence folder is not ready')
    folder = Path(state['evidence_path'])
    root = _data_root(index)
    if not folder.is_dir() or not _within(folder.resolve(), (root / '20_evidence').resolve()):
        raise ValueError('Unsafe evidence folder')
    if os.name != 'nt':
        return {'message': 'Windows Explorer is available on Windows only', 'path': str(folder)}
    subprocess.Popen(['explorer.exe', str(folder)])
    return {'message': 'Opened evidence folder', 'path': str(folder)}
