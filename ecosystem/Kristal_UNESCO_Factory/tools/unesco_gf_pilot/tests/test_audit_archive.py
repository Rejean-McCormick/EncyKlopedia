"""Checks that the archive auditor fails closed on malformed/tampered inputs."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

MODULE = Path(__file__).resolve().parents[1] / 'audit_archive.py'
spec = importlib.util.spec_from_file_location('unesco_archive_auditor', MODULE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AuditArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'pilot.zip'

    def test_missing_report_fails_closed(self):
        with zipfile.ZipFile(self.path, 'w') as z:
            z.writestr('README_STATUT.txt', 'PRIVATE')
        result = module.audit(self.path)
        self.assertEqual(result['status'], 'EVIDENCE_INCONSISTENT')
        self.assertTrue(any('Fichier absent' in x for x in result['errors']))

    def test_path_traversal_rejected(self):
        with zipfile.ZipFile(self.path, 'w') as z:
            z.writestr('../outside.txt', 'oops')
        with self.assertRaises(ValueError):
            module.audit(self.path)

    def test_duplicate_entry_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(self.path, 'w') as z:
                z.writestr('report.json', '{}')
                z.writestr('report.json', '{}')
        with self.assertRaises(ValueError):
            module.audit(self.path)

    def test_malformed_report_fails_closed(self):
        with zipfile.ZipFile(self.path, 'w') as z:
            z.writestr('report.json', '{this is bad}')
        result = module.audit(self.path)
        self.assertEqual(result['status'], 'EVIDENCE_INCONSISTENT')
        self.assertTrue(any('JSON invalide' in x for x in result['errors']))


if __name__ == '__main__':
    unittest.main()
