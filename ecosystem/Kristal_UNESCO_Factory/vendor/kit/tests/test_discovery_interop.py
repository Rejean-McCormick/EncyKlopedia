"""Regression checks for the read-only consumer preflight command."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'tools/kristal.py'


def run(*args):
    return subprocess.run([sys.executable, str(CLI), *map(str, args)], capture_output=True, text=True)


class InteropAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='kit-audit-'))
        self.ws = self.tmp / 'demo'
        p = run('init', self.ws, '--title', 'Interop')
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def audit(self, strict=False):
        p = run('audit-discovery', self.ws, '--compact', *(['--require-fresh'] if strict else []))
        return p, json.loads(p.stdout)

    def test_fresh_has_no_authorization_and_is_read_only(self):
        before = {f: (self.ws / f).read_bytes() for f in (
            'canon/state.index.json', 'kristal.workspace.json', 'kristal.discovery.json',
            'derived/reader-profile.json', 'derived/reader-inventory.json')}
        p, d = self.audit(strict=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(d['format'], 'kristal.discovery-audit/1.0')
        self.assertEqual(d['status'], 'fresh')
        self.assertTrue(d['usable_as_reader_hint'])
        self.assertIn('no_access_or_publication_grant', d['authorization'])
        self.assertEqual(d['tracked_file_count'], 0)
        for name, data in before.items():
            self.assertEqual((self.ws / name).read_bytes(), data)

    def test_legacy_absent_falls_back_to_generic(self):
        for rel in ('kristal.discovery.json', 'derived/reader-profile.json', 'derived/reader-inventory.json'):
            (self.ws / rel).unlink()
        p, d = self.audit()
        self.assertEqual(p.returncode, 0)
        self.assertEqual(d['status'], 'absent')
        self.assertFalse(d['usable_as_reader_hint'])
        p, _ = self.audit(strict=True)
        self.assertEqual(p.returncode, 2)

    def test_incomplete_is_not_usable(self):
        (self.ws / 'derived/reader-profile.json').unlink()
        p, d = self.audit(strict=True)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(d['status'], 'incomplete')

    def test_source_mutation_is_stale_not_authorized(self):
        # Canonical index changes without updating discovery.
        file = self.ws / 'canon/domain/a.json'
        file.write_text('{"a":1}\n')
        p = run('register-artifact', self.ws, '--file', 'canon/domain/a.json', '--artifact-id', 'urn:a', '--contract-id', 'a')
        self.assertEqual(p.returncode, 0, p.stderr + p.stdout)
        p, d = self.audit(strict=True)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(d['status'], 'stale')
        self.assertFalse(d['usable_as_reader_hint'])
        p = run('build-discovery', self.ws)
        self.assertEqual(p.returncode, 0, p.stderr)
        p, d = self.audit(strict=True)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(d['status'], 'fresh')
        self.assertEqual(d['tracked_file_count'], 1)

    def test_edited_digest_or_identity_fails_closed(self):
        inv = self.ws / 'derived/reader-inventory.json'
        obj = json.loads(inv.read_text())
        obj['source_fingerprint'] = 'sha256:' + '0' * 64
        inv.write_text(json.dumps(obj))
        p, d = self.audit(strict=True)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(d['status'], 'invalid')
        self.assertIn('invalid_discovery_or_inputs', d['issues'])

    def test_symlinked_profile_rejected(self):
        f = self.ws / 'derived/reader-profile.json'
        target = self.tmp / 'outside.json'
        target.write_bytes(f.read_bytes())
        f.unlink()
        try:
            f.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks not available')
        p, d = self.audit(strict=True)
        self.assertEqual(p.returncode, 2)
        self.assertEqual(d['status'], 'invalid')
        self.assertIn('symlinked_discovery_path', d['issues'])

    def test_no_remote_or_side_effect_when_working_dir_missing(self):
        ws = self.tmp / 'nonexistent'
        p = run('audit-discovery', ws, '--compact', '--require-fresh')
        self.assertEqual(p.returncode, 2)
        self.assertEqual(json.loads(p.stdout)['status'], 'absent')
        self.assertFalse(ws.exists())


if __name__ == '__main__':
    unittest.main()
