"""Independent Framework/Integration v11 qualification; uses fixture snapshots when provided."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'tools/kristal.py'
FW=os.environ.get('KRISTAL_FRAMEWORK_ROOT')
PACK=os.environ.get('KRISTAL_INTEGRATION_PACK_ROOT')

class FrameworkQualificationTests(unittest.TestCase):
    def test_pin_structure_and_contracts(self):
        pin=json.loads((ROOT/'contracts/v11-framework-pin.json').read_text())
        self.assertEqual(pin['version'],'11.0.0-draft.4')
        self.assertEqual(len(pin['files']),13)
        self.assertIn('tools/v11/interop_preflight.py',pin['files'])
        self.assertIn('schemas/v11/kristal-dictionary-catalog.schema.json',pin['files'])
        self.assertTrue(all(len(x)==64 for x in pin['files'].values()))

    @unittest.skipUnless(FW,'Set KRISTAL_FRAMEWORK_ROOT for real v11 qualification')
    def test_actual_framework_and_integration(self):
        snapshot=ROOT/'examples/demo-semantic-v11'
        inputs=[snapshot/'canon/domain/v11'/name for name in ['graph.json','registry.json','crosswalk.json','dictionaries/catalog.json']]
        before=[hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs]
        cmd=[sys.executable,str(CLI),'qualify-v11',str(snapshot),'--framework',FW,'--locales','fr,fr-CA']
        if PACK:cmd+=['--integration-pack',PACK]
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        obj=json.loads(r.stdout)
        self.assertTrue(obj['valid'] and obj['read_only'] and obj['reference_coverage_match'])
        if PACK:self.assertEqual(obj['integration_pack'],'coverage-and-check-matched')
        self.assertEqual(before,[hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs])

    @unittest.skipUnless(FW,'Set KRISTAL_FRAMEWORK_ROOT for tamper test')
    def test_framework_pin_detects_schema_change(self):
        from scripts.qualify_framework_v11 import verify_pin,QualificationError
        with tempfile.TemporaryDirectory() as temp:
            source=Path(FW)
            copy=Path(temp)/'framework'
            shutil.copytree(source,copy)
            verify_pin(copy)
            target=copy/'schemas/v11/kristal-dictionary-catalog.schema.json'
            target.write_bytes(target.read_bytes()+b' ')
            with self.assertRaisesRegex(QualificationError,'Framework pin drift'):
                verify_pin(copy)

if __name__=='__main__':unittest.main()
