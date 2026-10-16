"""EncyK -> standalone Skope v0.14.x, local pull-only integration.

Reads bounded loopback HTTP API. Only an explicit `pull` creates an immutable
noncanonical evidence intake; no EncyK pipeline or Kristal authority is invoked.
Neither EncyK nor its existing SQLite/dump/sidecars are modified by a pull.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
import zipfile

CONTRACT = 'encyk.skope-pull/1.0'
JOB = re.compile(r'^[0-9a-f]{32}$')
QID = re.compile(r'^Q[1-9][0-9]*$')
MAX_META = 512 * 1024
MAX_ZIP = 2 * 1024**3
MAX_TOTAL_UNPACKED = 8 * 1024**3
MAX_ENTRIES = 20
MAX_LINE = 4096
ALLOWED_ENTRIES = frozenset({
    'selected-qids.jsonl', 'recipe.json', 'summary.json', 'README.txt',
    'matched-people.jsonl', 'unresolved-people.jsonl',
    'author-work-links.jsonl', 'provenance-manifest.json',
})


class BridgeError(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise BridgeError('Skope redirect refused (loopback-only client)')


class SkopeClient:
    def __init__(self, url='http://127.0.0.1:8767', timeout=15):
        parsed = urlparse(url)
        if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost', '::1')
                or parsed.username or parsed.password or parsed.path not in ('', '/')
                or parsed.query or parsed.fragment):
            raise BridgeError('Skope URL must be loopback HTTP, e.g. http://127.0.0.1:8767')
        try:
            port = parsed.port or 80
        except ValueError as exc:
            raise BridgeError('Invalid Skope local port') from exc
        self.base = 'http://' + ('[' + parsed.hostname + ']' if ':' in parsed.hostname else parsed.hostname) + ':' + str(port)
        self.timeout = timeout
        self.opener = build_opener(NoRedirect())

    def _open(self, endpoint, params=None):
        uri = self.base + endpoint + ('?' + urlencode(params) if params else '')
        return self.opener.open(Request(uri, headers={'Accept': 'application/json, application/zip',
                                                      'User-Agent': 'EncyK-SkopeBridge/1.0'}), timeout=self.timeout)

    def json(self, endpoint, params=None, optional=False):
        try:
            with self._open(endpoint, params) as response:
                if response.status != 200:
                    raise BridgeError(f'{endpoint}: unexpected HTTP {response.status}')
                data = response.read(MAX_META + 1)
            if len(data) > MAX_META:
                raise BridgeError(f'{endpoint}: API response exceeds {MAX_META} bytes')
            return json.loads(data)
        except (HTTPError, URLError, OSError, ValueError) as exc:
            if optional and isinstance(exc, HTTPError) and exc.code in (404, 400):
                return None
            raise BridgeError(f'{endpoint}: {exc}') from exc

    def optional_json(self, endpoint, params=None):
        try:
            return self.json(endpoint, params, optional=True), None
        except BridgeError as exc:
            return None, str(exc)

    def download_zip(self, job, destination):
        total = 0
        digest = hashlib.sha256()
        with self._open('/api/large/result.zip', {'job': job}) as r, Path(destination).open('xb') as f:
            if r.status != 200 or 'zip' not in r.headers.get('Content-Type', '').lower():
                raise BridgeError('Expected a ZIP from the completed Skope job')
            while True:
                chunk = r.read(256 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_ZIP:
                    raise BridgeError('Skope result ZIP exceeds 2 GiB download safety limit')
                digest.update(chunk)
                f.write(chunk)
        return {'bytes': total, 'sha256': digest.hexdigest()}


def _job(job):
    if not isinstance(job, str) or not JOB.fullmatch(job):
        raise BridgeError('A complete 32-character hexadecimal Skope job ID is required')
    return job


def _file_entry(zf, filename):
    try:
        with zf.open(filename) as reader:
            data = reader.read(MAX_META + 1)
        if len(data) > MAX_META:
            raise BridgeError(filename + ': metadata file too large')
        return json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise BridgeError(filename + ': invalid JSON') from exc


def inspect_result(path, job, expected_selected=None):
    """Streaming validation of a Skope ZIP; never writes/extracts it."""
    _job(job)
    with zipfile.ZipFile(path, allowZip64=True) as zf:
        info = zf.infolist()
        if len(info) > MAX_ENTRIES:
            raise BridgeError('Too many ZIP entries')
        names = [x.filename for x in info]
        if len(set(names)) != len(names) or any(x not in ALLOWED_ENTRIES for x in names):
            raise BridgeError('Unexpected or duplicate ZIP member (no directory traversal allowed)')
        if 'selected-qids.jsonl' not in names or 'recipe.json' not in names:
            raise BridgeError('Skope results require selected-qids.jsonl and recipe.json')
        if sum(x.file_size for x in info) > MAX_TOTAL_UNPACKED:
            raise BridgeError('ZIP uncompressed data exceeds safety limit')
        if any((x.external_attr >> 16) & 0o170000 == 0o120000 for x in info):
            raise BridgeError('ZIP symlinks are forbidden')
        recipe = _file_entry(zf, 'recipe.json')
        summary = _file_entry(zf, 'summary.json') if 'summary.json' in names else None
        provenance = _file_entry(zf, 'provenance-manifest.json') if 'provenance-manifest.json' in names else None
        if not isinstance(recipe, dict):
            raise BridgeError('recipe must be a JSON object')
        if summary:
            if summary.get('state') != 'completed' or summary.get('job') != job:
                raise BridgeError('Job ID or completed status in summary does not match Skope')
            if summary.get('contains_source_wikidata_json') is True:
                raise BridgeError('Unexpected ZIP claiming complete source JSON records')
        seen = 0
        last = 0
        checksum = hashlib.sha256()
        with zf.open('selected-qids.jsonl') as reader:
            for raw in reader:
                checksum.update(raw)
                if len(raw) > MAX_LINE:
                    raise BridgeError('Invalid/oversized JSONL line')
                try:
                    obj = json.loads(raw)
                except ValueError as exc:
                    raise BridgeError('Invalid JSONL record') from exc
                wid = obj.get('wikidata_qid') if isinstance(obj, dict) else None
                if not isinstance(wid, str) or not QID.fullmatch(wid):
                    raise BridgeError('Invalid Wikidata QID in selected-qids.jsonl')
                number = int(wid[1:])
                if number <= last:
                    raise BridgeError('QIDs must be unique and numerically sorted in source inventory')
                last = number
                seen += 1
        if not seen:
            raise BridgeError('Empty QID inventory')
        if expected_selected is not None and seen != expected_selected:
            raise BridgeError(f'Count mismatch: Skope reports {expected_selected}, ZIP holds {seen}')
        if summary and summary.get('selected_qids') != seen:
            raise BridgeError('summary.json QID count mismatch')
        if provenance and provenance.get('unique_qids') != seen:
            raise BridgeError('provenance-manifest.json QID count mismatch')
        if any(x.CRC != __import__('zlib').crc32(zf.read(x)) for x in info if x.file_size <= MAX_META):
            raise BridgeError('ZIP member CRC mismatch')
        return {'qid_count': seen, 'selected_qids_sha256': checksum.hexdigest(),
                'zip_members': names, 'summary': summary, 'provenance': provenance,
                'source_kind': 'author_campaign' if provenance else 'qid_inventory'}


def _base_dir(data_root):
    base = Path(data_root).expanduser().resolve() / '20_evidence' / 'external-intake' / 'skope'
    if base.is_symlink():
        raise BridgeError('Import destination must not be a symlink')
    return base


def doctor(client):
    return {'contract': CONTRACT, 'skope_config': client.json('/api/config'),
            'skope_meta': client.json('/api/meta'), **list_jobs(client)}


def list_jobs(client):
    paths = {'latest_large_job': '/api/large/latest', 'latest_author_campaign': '/api/author-campaign/latest',
             'latest_extraction': '/api/extract/latest'}
    result = {}
    warnings = []
    for key, route in paths.items():
        result[key], error = client.optional_json(route)
        if error:
            warnings.append(error)
    if warnings:
        result['warnings'] = warnings
    return result


def pull(client, job, data_root, max_zip=MAX_ZIP):
    job = _job(job)
    status = client.json('/api/large/status', {'job': job})
    if not isinstance(status, dict) or status.get('state') != 'completed':
        raise BridgeError('Only completed Skope inventories can be pulled')
    if status.get('job') != job:
        raise BridgeError('Skope job ID mismatch')
    count = status.get('selected')
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        raise BridgeError('Skope selected QID count missing or invalid')
    destination = _base_dir(data_root)
    # By design no dirs are written until source job is confirmed ready.
    destination.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink():
        raise BridgeError('Skope import destination became a symlink')
    stage = destination / job
    if stage.exists() or stage.is_symlink():
        receipt = stage / 'receipt.json'
        if not receipt.is_file():
            raise BridgeError('Existing import folder has no valid receipt; refusing overwrite')
        existing = json.loads(receipt.read_text(encoding='utf8'))
        if existing.get('source_job') != job or existing.get('contract') != CONTRACT:
            raise BridgeError('Existing Skope import receipt mismatch')
        saved = stage / 'results.zip'
        if not saved.is_file():
            raise BridgeError('Existing Skope import bytes changed')
        digest = hashlib.sha256()
        with saved.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != existing.get('result_zip', {}).get('sha256'):
            raise BridgeError('Existing Skope import bytes changed')
        return existing | {'already_imported': True}
    temp = Path(tempfile.mkdtemp(prefix='.incoming-', dir=destination))
    try:
        dl = client.download_zip(job, temp / 'results.zip')
        if dl['bytes'] > max_zip:
            raise BridgeError('Result ZIP exceeds configured import cap')
        audit = inspect_result(temp / 'results.zip', job, count)
        # Materialize only validated allowlisted members, so EncyK can use the
        # noncanonical inventory without importing or running any Skope code.
        # This is not a source evidence or Kristal promotion operation.
        materialized = {}
        with zipfile.ZipFile(temp / 'results.zip') as zf:
            for name in audit['zip_members']:
                if name == 'README.txt':
                    continue
                digest = hashlib.sha256()
                size = 0
                with zf.open(name) as reader, (temp / name).open('xb') as output:
                    while True:
                        block = reader.read(256 * 1024)
                        if not block:
                            break
                        size += len(block)
                        digest.update(block)
                        output.write(block)
                materialized[name] = {'bytes': size, 'sha256': digest.hexdigest()}
        campaign, campaign_error = client.optional_json('/api/author-campaign/status', {'job': job}) if audit['source_kind'] == 'author_campaign' else (None, None)
        receipt = {
            'contract': CONTRACT, 'producer': {'system': 'skope', 'api': client.base,
                'release': (client.json('/api/config') or {}).get('server_release')},
            'consumer': {'system': 'encyk', 'authority': 'noncanonical external intake'},
            'source_job': job, 'state': 'imported',
            'pulled_at': datetime.now(timezone.utc).isoformat(),
            'source_status': status, 'author_campaign_status': campaign,
            'author_campaign_status_warning': campaign_error,
            'result_zip': dl, 'inventory': {'count': audit['qid_count'], 'sha256': audit['selected_qids_sha256']},
            'source_kind': audit['source_kind'], 'source_manifest': audit['provenance'],
            'zip_entries': audit['zip_members'], 'materialized_files': materialized,
            'limitations': [
                'Skope QID results are selection evidence, not original Wikidata claims.',
                'Original source JSON evidence remains at its own D: location; no byte copying or authority claim is made here.',
                'This import does not freeze an EncyK scope, promote a canon or publish to Mediatheque.',
                'Any Skope evidence_path is a reported external pointer, not independently verified by EncyK.'
            ],
        }
        (temp / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.rename(temp, stage)
        return receipt
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def main(argv=None):
    ap = argparse.ArgumentParser(description='EncyK pulls verified, noncanonical Skope QID inventories over local HTTP')
    ap.add_argument('command', choices=['doctor', 'list', 'pull'])
    ap.add_argument('--job', help='32-character Skope job ID (required for pull)')
    ap.add_argument('--api', default='http://127.0.0.1:8767')
    ap.add_argument('--data-root', default=os.environ.get('ENCYK_DATA_ROOT', 'D:/EncyKlopedia'))
    args = ap.parse_args(argv)
    try:
        cli = SkopeClient(args.api)
        result = doctor(cli) if args.command == 'doctor' else list_jobs(cli) if args.command == 'list' else pull(cli, args.job, args.data_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (BridgeError, HTTPError, URLError, TimeoutError, OSError, zipfile.BadZipFile) as exc:
        print(json.dumps({'error': str(exc), 'command': args.command}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
