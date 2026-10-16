"""Loopback integration tests; no Skope imports and no D: disk access."""
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from zipfile import ZipFile, ZIP_DEFLATED
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / 'skope_bridge.py'
spec = importlib.util.spec_from_file_location('encyk_skope_bridge', FILE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
JOB = 'b669d969d01f4840bec0a4dc9c6ca945'


def zip_bytes(qids=('Q1', 'Q4', 'Q12'), job=JOB, bad=None):
    buff = io.BytesIO()
    with ZipFile(buff, 'w', ZIP_DEFLATED) as z:
        z.writestr('recipe.json', json.dumps({'root': 'Q1', 'direction': 'in', 'allowed_properties': ['P279']}))
        z.writestr('summary.json', json.dumps({'state': 'completed', 'job': job, 'selected_qids': len(qids), 'contains_source_wikidata_json': False}))
        z.writestr('selected-qids.jsonl', ''.join(json.dumps({'wikidata_qid': q}) + '\n' for q in qids))
        if bad:
            z.writestr(bad, 'ATTACK')
    return buff.getvalue()


class Handler(BaseHTTPRequestHandler):
    zip_body = zip_bytes()
    state = 'completed'
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/large/result.zip':
            body = self.zip_body
            ctype = 'application/zip'
        else:
            ctype = 'application/json'
            data = {
                '/api/config': {'server_release': '0.14.1'},
                '/api/meta': {'complete': '1', 'entity_count': '121780373'},
                '/api/large/latest': {'job': JOB, 'state': self.state, 'selected': 3},
                '/api/large/status': {'job': JOB, 'state': self.state, 'selected': 3},
                '/api/author-campaign/latest': None,
                '/api/extract/latest': None,
            }.get(parsed.path, {'error': 'not_found'})
            if data == {'error': 'not_found'}:
                self.send_response(404);self.end_headers();return
            body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):pass


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.client = bridge.SkopeClient('http://127.0.0.1:' + str(cls.server.server_port))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=3)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        Handler.zip_body = zip_bytes()
        Handler.state = 'completed'

    def test_loopback_required(self):
        for uri in ('http://example.org:8767', 'https://127.0.0.1:8767', 'http://127.0.0.1:8767/api', 'http://localhost:8767/path', 'http://user@localhost:8767'):
            with self.subTest(uri=uri), self.assertRaises(bridge.BridgeError):bridge.SkopeClient(uri)

    def test_doctor_is_read_only(self):
        data = bridge.doctor(self.client)
        self.assertEqual(data['skope_config']['server_release'], '0.14.1')
        self.assertEqual(data['latest_large_job']['job'], JOB)
        self.assertFalse((Path(self.tmp.name) / '20_evidence').exists())

    def test_pull_completed_zip_and_idempotence(self):
        receipt = bridge.pull(self.client, JOB, self.tmp.name)
        self.assertEqual(receipt['inventory']['count'], 3)
        self.assertEqual(receipt['source_kind'], 'qid_inventory')
        dest = Path(self.tmp.name) / '20_evidence/external-intake/skope' / JOB
        self.assertTrue((dest / 'results.zip').exists())
        self.assertTrue((dest / 'selected-qids.jsonl').exists())
        self.assertTrue((dest / 'recipe.json').exists())
        self.assertEqual(json.loads((dest / 'receipt.json').read_text())['contract'], bridge.CONTRACT)
        result = bridge.pull(self.client, JOB, self.tmp.name)
        self.assertTrue(result['already_imported'])
        self.assertEqual(len(list(dest.parent.iterdir())), 1)
        self.assertFalse((Path(self.tmp.name) / '40_kristal').exists())

    def test_reject_incomplete_job(self):
        Handler.state = 'limit_reached'
        with self.assertRaisesRegex(bridge.BridgeError, 'completed'):
            bridge.pull(self.client, JOB, self.tmp.name)
        self.assertFalse((Path(self.tmp.name) / '20_evidence').exists())

    def test_traversal_and_unsorted_qids_rejected(self):
        for body in (zip_bytes(bad='../escape'), zip_bytes(qids=('Q4', 'Q1', 'Q12')), zip_bytes(qids=('Q1', 'Q1', 'Q12'))):
            Handler.zip_body = body
            with self.assertRaises(bridge.BridgeError):
                bridge.pull(self.client, JOB, self.tmp.name)
            parent = Path(self.tmp.name) / '20_evidence/external-intake/skope'
            if parent.exists():self.assertEqual(list(parent.iterdir()), [])

    def test_reject_corrupt_existing_import(self):
        receipt = bridge.pull(self.client, JOB, self.tmp.name)
        dest = Path(self.tmp.name)/'20_evidence/external-intake/skope'/JOB
        (dest/'results.zip').write_bytes(b'corrupt')
        with self.assertRaisesRegex(bridge.BridgeError, 'changed'):
            bridge.pull(self.client, JOB, self.tmp.name)

    def test_real_completed_skope_archive_if_uploaded(self):
        actual = Path('/mnt/data/skope-b669d969-results.zip')
        if not actual.exists():self.skipTest('user-supplied Skope result ZIP not mounted')
        result=bridge.inspect_result(actual, JOB, 16299)
        self.assertEqual(result['qid_count'], 16299)
        self.assertEqual(result['source_kind'], 'qid_inventory')


if __name__ == '__main__':unittest.main()

class AuthorJobTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.client = bridge.SkopeClient('http://127.0.0.1:' + str(cls.server.server_port))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=3)

    def test_author_campaign_zip_with_provenance(self):
        raw = io.BytesIO()
        with ZipFile(raw, 'w', ZIP_DEFLATED) as z:
            z.writestr('recipe.json', json.dumps({'kind': 'skope.recognised-authors/1.0', 'profile_id': 'catho-recognised-authors'}))
            z.writestr('selected-qids.jsonl', '{"wikidata_qid":"Q101"}\n{"wikidata_qid":"Q300"}\n{"wikidata_qid":"Q999"}\n')
            z.writestr('provenance-manifest.json', json.dumps({'format': 'skope.recognised-authors/1.0', 'unique_qids': 3, 'people_matched': 2, 'people_unresolved': 1}))
            z.writestr('matched-people.jsonl', '{"wikidata_qid":"Q101"}\n')
            z.writestr('unresolved-people.jsonl', '{"name":"Unknown","candidate_qids":[]}\n')
            z.writestr('author-work-links.jsonl', '{"author_qid":"Q101","work_qid":"Q300"}\n')
        Handler.zip_body = raw.getvalue()
        Handler.state = 'completed'
        try:
            with tempfile.TemporaryDirectory() as root:
                r = bridge.pull(self.client, JOB, root)
                self.assertEqual(r['source_kind'], 'author_campaign')
                self.assertEqual(r['inventory']['count'], 3)
                self.assertEqual(r['source_manifest']['people_unresolved'], 1)
                self.assertEqual(r['source_manifest']['people_matched'], 2)
                self.assertTrue((Path(root) / '20_evidence/external-intake/skope' / JOB / 'unresolved-people.jsonl').exists())
        finally:
            Handler.zip_body = zip_bytes()
