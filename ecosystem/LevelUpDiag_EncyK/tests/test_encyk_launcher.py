"""Startup tests for LevelUpDiag EncyK standalone GUI without a Tk display."""
import importlib.machinery
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
loader=importlib.machinery.SourceFileLoader('test_levelupdiag_encyk_launcher',str(ROOT/'LEVELUPDIAG_ENCYK.pyw'))
spec=importlib.util.spec_from_loader(loader.name,loader)
module=importlib.util.module_from_spec(spec)
loader.exec_module(module)

class LauncherTests(unittest.TestCase):
    def test_full_distribution_is_complete(self):
        self.assertEqual(module.missing_runtime(ROOT), [])
    def test_addon_only_installation_is_detected(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)
            (f/'LEVELUPDIAG_ENCYK.pyw').write_text('')
            missing=module.missing_runtime(f)
            self.assertIn('levelupdiag.py',missing)
            self.assertIn('levelupdiag_core/cli.py',missing)
    def test_uses_python_exe_from_path(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'python.exe';p.touch()
            with patch.object(module.shutil,'which',side_effect=lambda s: str(p) if s=='python' else None):
                self.assertEqual(module.default_python(),str(p))
    def test_avoids_pythonw_when_sibling_exists(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'python.exe';p.touch()
            with patch.object(module.shutil,'which',return_value=None),patch.object(module.sys,'executable',str(p.with_name('pythonw.exe'))):
                self.assertEqual(module.default_python(),str(p))

if __name__=='__main__':unittest.main()
