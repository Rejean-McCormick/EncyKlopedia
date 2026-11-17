"""Release acceptance: the tool diagnoses EncyK and no other application."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from levelupdiag_core.config import ConfigError, load_config
from levelupdiag_core.manifest import load_manifest

ROOT = Path(__file__).resolve().parents[1]


class DedicatedEncyKRelease(unittest.TestCase):
    def test_single_configuration_and_manifest(self):
        self.assertTrue((ROOT/'levelupdiag.config.json').is_file())
        self.assertTrue((ROOT/'levelupdiag_manifest.json').is_file())
        self.assertFalse((ROOT/'levelupdiag.config.encyk.json').exists())
        self.assertFalse((ROOT/'levelupdiag_manifest.encyk.json').exists())
        doc = json.loads((ROOT/'levelupdiag_manifest.json').read_text(encoding='utf8'))
        self.assertEqual(doc['suite_version'],'1.2.0')
        self.assertEqual(len(doc['levels']),15)
        self.assertTrue(all('encyk' in x['module'] or x['module'].startswith('levels.n0') for x in doc['levels']))
        self.assertFalse(any(x['id']=='N15' for x in doc['levels']))

    def test_no_orgo_runtime_or_launchers(self):
        for name in ('RUN_ORGO.ps1','RUN_ORGO_UI.bat','levelupdiag_core/desktop_ui.py',
                     'levels/orgo_validation.py','levels/orgo_acceptance.py',
                     'browser','adapters','levelupdiag.config.orgo.example.json'):
            self.assertFalse((ROOT/name).exists(),name)
        self.assertTrue((ROOT/'LEVELUPDIAG_ENCYK.pyw').is_file())
        self.assertTrue((ROOT/'RUN_ENCYK.ps1').is_file())

    def test_profile_switch_is_not_supported(self):
        res=subprocess.run([sys.executable,'-B',str(ROOT/'levelupdiag.py'),'--profile','orgo','list'],
                           cwd=ROOT,text=True,capture_output=True,timeout=15)
        self.assertNotEqual(res.returncode,0)
        self.assertTrue('unrecognized arguments' in res.stderr or 'invalid choice' in res.stderr)
        good=subprocess.run([sys.executable,'-B',str(ROOT/'levelupdiag.py'),'list'],
                            cwd=ROOT,text=True,capture_output=True,timeout=15)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertIn('bridge:',good.stdout)
        self.assertNotIn('Playwright',good.stdout)

    def test_encyk_is_required_and_reports_stay_local(self):
        with tempfile.TemporaryDirectory() as base:
            root=Path(base)
            bad=root/'SomeOtherApp';bad.mkdir()
            (bad/'VERSION').write_text('1.0')
            with self.assertRaises(ConfigError):load_config(ROOT,str(bad))
            encyk=root/'EncyK';encyk.mkdir()
            (encyk/'VERSION').write_text('0.14.0')
            (encyk/'MANIFEST.json').write_text('{}')
            bridge=encyk/'00_system/integrations/skope_bridge.py';bridge.parent.mkdir(parents=True)
            bridge.write_text('')
            cfg=load_config(ROOT,str(encyk))
            self.assertEqual(cfg['_control_root'],str(ROOT/'.levelupdiag/encyk'))
            self.assertEqual(cfg['_target_root'],str(encyk))
            self.assertFalse(cfg['execution']['allow_target_mutation'])
            self.assertFalse(cfg['execution']['allow_network'])

    def test_skope_is_an_encyk_integration_only(self):
        manifest=load_manifest(ROOT)
        assert set(manifest['campaigns'])=={'reader','quick','repository','standard','bridge'}
        bridge=manifest['campaigns']['bridge']['levels']
        self.assertIn('N14',bridge)
        self.assertIn('N10',bridge)
        self.assertNotIn('N13',bridge)
        self.assertNotIn('N15',bridge)
        self.assertFalse((ROOT/'levels/encyk_skope_repo.py').exists())


if __name__=='__main__':unittest.main()
