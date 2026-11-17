"""Reader discovery: built bytes, Arketype hints, lifecycle and fail-safe behavior."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'tools/kristal.py'


def cli(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True)


class ReaderDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix='kit-reader-test-'))
        self.ws = self.temp / 'demo'
        p = cli('init', self.ws, '--title', 'Example')
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)

    def tearDown(self):
        shutil.rmtree(self.temp, ignore_errors=True)

    def run_ok(self, *args):
        p = cli(*args)
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        return p.stdout

    def data(self, name):
        return json.loads((self.ws / name).read_text())

    def test_created_discovery_is_noncanonical_generic(self):
        d = self.data('kristal.discovery.json')
        self.assertEqual(d['format'], 'kristal.discovery/1.0')
        self.assertEqual(d['reader']['profile'], 'kristal.reader/generic-v1')
        self.assertEqual(d['data_layout']['inventory_ref'], 'derived/reader-inventory.json')
        self.assertEqual(d['size']['tracked_local_bytes'], 0)
        self.assertEqual(d['size']['class'], 'tiny')
        self.assertEqual(self.data('derived/reader-inventory.json')['storage']['max_json_depth'], None)
        self.assertEqual(self.run_ok('check', self.ws).count('WARN:'), 0)

    def test_classify_against_local_arketype_catalog(self):
        # Self-contained test catalog: no external checkout is required.
        catalog = self.temp / 'arketype'; (catalog / 'inventaires').mkdir(parents=True)
        (catalog / 'catalogue.json').write_text(json.dumps({'version': '1.4.0', 'archetypes': [
            {'slug': 'diagnostic-causal', 'id': 'ARK-08'}, {'slug': 'modele-multiplexe', 'id': 'ARK-09'}]}))
        (catalog / 'inventaires/profils-usage.json').write_text(json.dumps({'profiles': [{
            'id': 'PRF-15', 'slug': 'diagnostic-vehicule', 'primary_archetype': 'diagnostic-causal',
            'supporting_archetypes': ['modele-multiplexe'], 'usage_family': 'diagnosis', 'domain': 'automotive'}]}))
        self.run_ok('classify', self.ws, '--arketype-dir', catalog, '--usage', 'PRF-15')
        d = self.data('kristal.discovery.json')
        self.assertEqual(d['classification']['primary_archetype'], 'ARK-08')
        self.assertEqual(d['classification']['primary_usage'], 'PRF-15')
        self.assertEqual(d['reader']['profile'], 'kristal.reader/causal-graph-v1')
        self.assertEqual(self.data('kristal.workspace.json')['classification']['supporting_archetypes'], ['ARK-09'])
        self.run_ok('check', self.ws)

    def test_stale_reader_metadata_warns_without_mutating_canon(self):
        before = (self.ws / 'canon/state.index.json').read_bytes()
        f = self.ws / 'canon/domain/test.json'
        f.write_text('{"x":1}\n')
        self.run_ok('register-artifact', self.ws, '--file', 'canon/domain/test.json',
                    '--artifact-id', 'urn:test:x', '--contract-id', 'test')
        output = self.run_ok('check', self.ws)
        self.assertIn('Stale or edited derived reader metadata', output)
        self.run_ok('build-discovery', self.ws)
        self.assertEqual(self.run_ok('check', self.ws).count('Stale or edited'), 0)
        inv = self.data('derived/reader-inventory.json')
        self.assertEqual(inv['cardinality']['canonical_artifacts'], 1)
        row = next(x for x in inv['files'] if x['path'] == 'canon/domain/test.json')
        self.assertEqual(row['size_bytes'], len(f.read_bytes()))
        self.assertNotEqual(before, (self.ws / 'canon/state.index.json').read_bytes())  # only register-artifact changed it
        after = (self.ws / 'canon/state.index.json').read_bytes()
        self.run_ok('build-discovery', self.ws)
        self.assertEqual(after, (self.ws / 'canon/state.index.json').read_bytes())
        self.assertEqual(self.run_ok('check', self.ws).count('Stale or edited'), 0)

    def test_build_does_not_change_logical_state_when_classification_changes(self):
        self.run_ok('build-v9', self.ws)
        before = self.data('build/v9/state-snapshot.json')['logical_commitment']
        self.run_ok('classify', self.ws, '--archetype', 'ARK-02', '--usage', 'PRF-06', '--organization', 'federation')
        self.run_ok('build-v9', self.ws)
        after = self.data('build/v9/state-snapshot.json')['logical_commitment']
        self.assertEqual(before, after)
        self.assertEqual(self.data('kristal.discovery.json')['data_layout']['organization'], 'federation')
        self.assertEqual(self.data('kristal.discovery.json')['reader']['profile'], 'kristal.reader/federated-resolution-v1')

    def test_bad_classification_rejected_and_old_workspace_allowed(self):
        before = (self.ws / 'kristal.workspace.json').read_bytes()
        p = cli('classify', self.ws, '--archetype', 'INVALID')
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(before, (self.ws / 'kristal.workspace.json').read_bytes())
        (self.ws / 'kristal.discovery.json').unlink()
        (self.ws / 'derived/reader-profile.json').unlink()
        (self.ws / 'derived/reader-inventory.json').unlink()
        self.run_ok('check', self.ws)

    def test_partial_discovery_fails_closed_and_read_surface_lists_metadata(self):
        (self.ws / 'derived/reader-profile.json').unlink()
        p = cli('check', self.ws)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('Incomplete reader discovery', p.stdout)
        self.run_ok('build-discovery', self.ws)
        surface = json.loads(self.run_ok('read-surface', self.ws, '--compact'))
        rows = {x['path']:x for x in surface['files']}
        self.assertEqual(rows['kristal.discovery.json']['role'], 'reader_discovery')
        self.assertEqual(rows['derived/reader-inventory.json']['role'], 'reader_inventory')
        self.assertEqual(rows['derived/reader-profile.json']['role'], 'reader_profile')

    def test_discovery_and_sidecar_cannot_be_registered_as_canon(self):
        for rel in ('kristal.discovery.json', 'derived/reader-profile.json'):
            p = cli('register-artifact', self.ws, '--file', rel,
                    '--artifact-id', 'blocked', '--contract-id', 'blocked')
            self.assertNotEqual(p.returncode, 0)
            self.assertIn('Refusing to register derived', p.stderr + p.stdout)
        self.assertEqual(self.data('canon/state.index.json')['canonical_artifacts'], [])

    def test_jsonl_reader_strategy_is_stream_with_unknown_record_bound(self):
        data = self.ws / 'canon/domain/events.jsonl'
        data.write_text('{"a":1}\n{"a":2}\n')
        self.run_ok('register-artifact', self.ws, '--file', 'canon/domain/events.jsonl',
                    '--artifact-id', 'urn:events', '--contract-id', 'events',
                    '--mode', 'precomputed', '--commitment-profile', 'test/v1',
                    '--digest', 'sha256:' + 'a' * 64)
        self.run_ok('build-discovery', self.ws)
        reader = self.data('derived/reader-profile.json')
        match = [r for r in reader['artifact_strategies'] if r['path'].endswith('events.jsonl')]
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]['suggested_mode'], 'document_stream_requires_record_bound')
        self.assertEqual(match[0]['suggested_parser_family'], 'simdjson')
        self.assertIsNone(self.data('derived/reader-inventory.json')['storage']['max_record_bytes'])

    def test_source_bytes_change_marks_stale_and_rebuild_is_deterministic(self):
        p = self.ws / 'canon/domain/data.json'; p.write_text('{"a":1}\n')
        self.run_ok('register-artifact', self.ws, '--file', 'canon/domain/data.json', '--artifact-id', 'a', '--contract-id', 'a')
        self.run_ok('build-discovery', self.ws)
        before = [(self.ws / x).read_bytes() for x in
                  ['kristal.discovery.json','derived/reader-inventory.json','derived/reader-profile.json']]
        self.run_ok('build-discovery', self.ws)
        after = [(self.ws / x).read_bytes() for x in
                 ['kristal.discovery.json','derived/reader-inventory.json','derived/reader-profile.json']]
        self.assertEqual(before, after)
        p.write_text('{"a":2}\n')
        self.assertIn('Stale or edited', self.run_ok('check', self.ws))
        self.run_ok('build-discovery', self.ws)
        self.assertNotEqual(before[0], (self.ws / 'kristal.discovery.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
