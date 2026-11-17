"""Regression tests for safe v10 read-surface and non-destructive migration audit."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / 'tools/kristal.py'
AUDIT = ROOT / 'scripts/audit_workspace_migration.py'
spec = importlib.util.spec_from_file_location('kit_migration_audit', AUDIT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class V10AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='kit-v10-alignment-'))
        self.ws = self.tmp / 'demo'
        self.run_cli('init', self.ws, '--title', 'Demo')
        p = self.ws / 'canon/domain/core.json'
        p.write_text('{"example":true}\n', encoding='utf-8')
        self.run_cli('register-artifact', self.ws, '--file', 'canon/domain/core.json',
                     '--artifact-id', 'urn:kristal:demo:core', '--contract-id', 'demo.core')
        self.run_cli('build-v9', self.ws)
        self.run_cli('build-ai', self.ws)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cli(self, *args, check=True):
        r = subprocess.run([sys.executable, str(TOOL), *map(str, args)],
                           capture_output=True, text=True, timeout=45)
        if check:
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def read_surface(self, require=True):
        args = ['read-surface', self.ws, '--compact']
        if require:
            args.append('--require-ready')
        r = self.run_cli(*args, check=False)
        return r, json.loads(r.stdout)

    def test_read_surface_is_deterministic_and_matches_actual_bytes(self):
        one, a = self.read_surface()
        two, b = self.read_surface()
        self.assertEqual(one.returncode, 0)
        self.assertEqual(a, b)
        self.assertEqual(a['file_count'], len(a['files']))
        self.assertEqual(a['total_bytes'], sum(x['size'] for x in a['files']))
        self.assertEqual(a['target_root'], 'kristals/demo')
        self.assertFalse(any(x['path'].startswith(('tools/', 'build/', 'release/', 'hosting/')) for x in a['files']))

    def test_wrong_size_with_correct_hash_must_not_be_ready(self):
        p = self.ws / 'ai/INDEX.json'
        idx = json.loads(p.read_text())
        idx['files'][0]['size'] += 1
        p.write_text(json.dumps(idx))
        r, surface = self.read_surface()
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(surface['ready'])
        self.assertTrue(any('size mismatch' in x for x in surface['errors']))

    def test_traversal_and_unlisted_tool_paths_fail_closed(self):
        for bad in ('../../private.json', 'tools/kristal.py', '/etc/passwd'):
            with self.subTest(bad=bad):
                self.run_cli('build-ai', self.ws)
                index = self.ws / 'ai/INDEX.json'
                doc = json.loads(index.read_text())
                doc['files'].append({'path': bad, 'role': 'overview',
                    'media_type': 'application/json', 'size': 1, 'sha256': 'sha256:' + '0'*64})
                index.write_text(json.dumps(doc))
                result, obj = self.read_surface()
                self.assertEqual(result.returncode, 1)
                self.assertFalse(obj['ready'])
                self.assertTrue(any('Unsafe AI index path' in x for x in obj['errors']))
                self.assertNotIn(bad, [f['path'] for f in obj['files']])

    def test_duplicate_index_path_fails_closed(self):
        p = self.ws / 'ai/INDEX.json'
        doc = json.loads(p.read_text())
        doc['files'].append(dict(doc['files'][0]))
        p.write_text(json.dumps(doc))
        result, surface = self.read_surface()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(surface['ready'])
        self.assertTrue(any('Duplicate AI index path' in x for x in surface['errors']))

    def test_disabled_ai_does_not_make_stale_ai_ready(self):
        ws = self.ws / 'kristal.workspace.json'
        doc = json.loads(ws.read_text())
        doc['portable_ai']['enabled'] = False
        ws.write_text(json.dumps(doc))
        (self.ws / 'canon/domain/core.json').write_text('{"example":false}\n')
        result, surface = self.read_surface()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(surface['ready'])
        self.assertTrue(any('digest mismatch' in x for x in surface['errors']))

    def test_migration_audit_comparison_on_separate_copies(self):
        copy = self.tmp / 'after'
        shutil.copytree(self.ws, copy)
        canonical_before = (self.ws / 'canon/state.index.json').read_bytes()
        report = module.audit(self.ws, copy)
        self.assertEqual(report['result'], 'PRESERVED')
        self.assertTrue(report['canonical_bytes_unchanged'])
        self.assertEqual(canonical_before, (self.ws / 'canon/state.index.json').read_bytes())
        (copy / 'canon/domain/core.json').write_text('{}\n')
        bad = module.audit(self.ws, copy)
        self.assertEqual(bad['result'], 'BLOCKED')
        self.assertTrue(any('canonical bytes' in x for x in bad['differences']))

    def test_migration_audit_no_built_snapshot_does_not_claim_full_pass(self):
        copy = self.tmp / 'after'
        shutil.copytree(self.ws, copy)
        for base in (self.ws, copy):
            (base / 'build/v9/state-snapshot.json').unlink()
            (base / 'state/state-snapshot.json').unlink()
        result = module.audit(self.ws, copy)
        self.assertEqual(result['result'], 'NOT_FULLY_QUALIFIED')
        self.assertTrue(result['v9_commitment_comparison'].startswith('NOT_EVALUATED'))

    def test_wrong_role_and_manifest_escape_fail_closed(self):
        idx_path = self.ws / 'ai/INDEX.json'
        doc = json.loads(idx_path.read_text())
        doc['files'][0]['role'] = 'overview'
        idx_path.write_text(json.dumps(doc))
        result, surface = self.read_surface()
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any('role mismatch' in x for x in surface['errors']))
        self.run_cli('build-ai', self.ws)
        manifest_path = self.ws / 'AI_MANIFEST.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['index'] = '../../private.json'
        manifest_path.write_text(json.dumps(manifest))
        result, surface = self.read_surface()
        self.assertEqual(result.returncode, 1)
        self.assertTrue(any('must reference ai/INDEX.json' in x for x in surface['errors']))

    def test_external_materialization_locator_is_not_downloaded(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('kristal_reader', TOOL)
        kt = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(kt)
        idx = json.loads((self.ws / 'canon/state.index.json').read_text())
        ref = kt._canonical_ref_map(self.ws, idx)['urn:kristal:demo:core']
        mat = {
            'schema_version':'9.0', 'artifact_type':'kristal_materialization_manifest',
            'materialization_id':'urn:kristal:materialization:demo:external',
            'source':ref, 'profile':'demo.remote/1',
            'segments':[{'segment_key':'remote', 'blob':{
                'media_type':'application/octet-stream', 'digest':'sha256:'+'a'*64,
                'size':500, 'locator':'https://example.invalid/no-fetch'}}],
            'reconstructability':{'lossless':True}
        }
        path=self.tmp/'external.json';path.write_text(json.dumps(mat))
        self.run_cli('register-materialization',self.ws,'--manifest',path)
        self.run_cli('build-v9',self.ws)
        self.run_cli('build-ai',self.ws)
        _, surface=self.read_surface()
        self.assertTrue(surface['ready'])
        self.assertTrue(any(obj['availability']=='external' for obj in surface['materialization_objects']))
        self.assertFalse(any('https://example.invalid' in x['path'] for x in surface['files']))

if __name__ == '__main__':
    unittest.main()
