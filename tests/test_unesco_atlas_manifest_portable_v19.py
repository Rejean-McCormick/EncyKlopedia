"""Regression: v19 install works with only the repository-local SHA manifest."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


VERIFY_REL = Path('EncyKlopedia/EncyKlopedia/tools/unesco_pilot/verifier_overlay_atlas_v19.py')
MANIFEST = 'MANIFEST_OVERLAY_UNESCO_ATLAS_V19_20261109.json'


class ManifestPortableV19Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.verifier = self.root / VERIFY_REL
        self.verifier.parent.mkdir(parents=True)
        shutil.copyfile(Path(__file__).resolve().parents[1] / 'tools/unesco_pilot/verifier_overlay_atlas_v19.py', self.verifier)
        self.file = self.root / 'EncyKlopedia/EncyKlopedia/atlas_example.txt'
        self.file.write_bytes(b'first version')
        content = self.file.read_bytes()
        self.manifest = self.verifier.parent / MANIFEST
        self.manifest.write_text(json.dumps({'files': {'EncyKlopedia/EncyKlopedia/atlas_example.txt': {
            'bytes': len(content), 'sha256': hashlib.sha256(content).hexdigest(),
        }}}), encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def run_verifier(self):
        return subprocess.run([sys.executable, str(self.verifier), str(self.root)],
                              capture_output=True, text=True, timeout=20)

    def test_local_manifest_without_root_manifest(self):
        self.assertFalse((self.root / MANIFEST).exists())
        run = self.run_verifier()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['status'], 'OVERLAY_UNESCO_ATLAS_V19_VALID')
        self.assertEqual(result['manifest_location'], str(self.manifest))

    def test_tampered_file_is_rejected(self):
        self.file.write_bytes(b'changed version')
        run = self.run_verifier()
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)['status'], 'OVERLAY_INTEGRITY_FAILED')

    def test_manifest_missing_is_error_not_skipped(self):
        self.manifest.unlink()
        run = self.run_verifier()
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)['status'], 'OVERLAY_INTEGRITY_FAILED')

    def test_legacy_root_manifest_is_supported(self):
        self.manifest.replace(self.root / MANIFEST)
        run = self.run_verifier()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
