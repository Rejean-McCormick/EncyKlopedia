"""Tests sans ecriture dans le workspace source; copies temporaires seulement."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[1]
SCRIPT=REPO/'tools/unesco_pilot/overlay_probatoire_v23.py'
SPEC=importlib.util.spec_from_file_location('overlay_probatoire_v23',SCRIPT)
V23=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(V23)
SOURCE=Path(os.environ.get('UNESCO_V22_TEST_SOURCE',str(V23.DEFAULT_WORK/V23.STAGE22)))

@unittest.skipUnless(SOURCE.is_dir(), 'Archive v22 absente : specifier UNESCO_V22_TEST_SOURCE')
class V23Test(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='test_unesco_v23_')
        self.work=Path(self.tmp.name)
        shutil.copytree(SOURCE,self.work/V23.STAGE22)

    def tearDown(self):self.tmp.cleanup()

    def test_preflight(self):
        result=V23.process(self.work,SCRIPT,'preflight')
        self.assertEqual(result['reviews'],44)
        self.assertEqual(result['41_concepts_preserved'],41)
        self.assertEqual(result['canonical_admissions'],0)

    def test_apply_and_verify(self):
        self.assertEqual(V23.process(self.work,SCRIPT,'apply')['files_verified'],52)
        self.assertEqual(V23.process(self.work,SCRIPT,'verify')['status'],'V23_CONTROLE_OK')
        report=json.loads((self.work/V23.STAGE23/'RAPPORT_V23.json').read_text('utf8'))
        self.assertEqual(report['editorial_ai_approved'],44)
        self.assertEqual(report['mapping_holds_external'],4)
        self.assertEqual(report['canonical_admissions'],0)
        self.assertFalse(report['publication_authorized'])

    def test_idempotent(self):
        V23.process(self.work,SCRIPT,'apply')
        self.assertEqual(V23.process(self.work,SCRIPT,'apply')['status'],'V23_DEJA_INSTALLE_INTEGRE')

    def test_refuse_corruption_even_forged_manifest(self):
        V23.process(self.work,SCRIPT,'apply')
        out=self.work/V23.STAGE23
        f=out/'reader_fr/concept10.html'
        f.write_text(f.read_text('utf8')+'<!-- altération -->',encoding='utf8')
        man=out/'MANIFESTE_V23.json'; data=json.loads(man.read_text('utf8'))
        data['files_sha256']['reader_fr/concept10.html']=V23.sha(f.read_bytes())
        man.write_bytes(V23.serialize(data))
        with self.assertRaises(V23.Refusal):V23.process(self.work,SCRIPT,'apply')

    def test_refuse_corrupted_source_v22(self):
        f=self.work/V23.STAGE22/'RAPPORT_V22.json'
        f.write_text(f.read_text('utf8')+' ',encoding='utf8')
        with self.assertRaises(V23.Refusal):V23.process(self.work,SCRIPT,'preflight')

    def test_four_external_anchors_have_no_internal_kq(self):
        V23.process(self.work,SCRIPT,'apply')
        data=json.loads((self.work/V23.STAGE23/'REVUES_44_V23.json').read_text('utf8'))['records']
        held=[r for r in data if r['mapping_state']=='ANCRE_EXTERNE_SEULE_SANS_KQ']
        self.assertEqual(len(held),4)
        self.assertTrue(all(x['provisional_kq_id'] is None and x['effective_unesco_id'] is None for x in held))
        self.assertEqual(len({x['proposal_id'] for x in data}),44)

    def test_capture_mock_returns_true_hash_and_no_admission(self):
        V23.process(self.work,SCRIPT,'apply')
        old=V23.fetch_one
        try:
            def fake_fetch(source):
                if source['source_id']!='UIS-417': return source['source_id'],{'status':'NOT_CAPTURED','error':'offline'},None
                raw=b'<!doctype html><html><body>EXAMPLE SYNTHETIC</body></html>'
                return 'UIS-417',{'status':'CAPTURE_HTTP_SUCCESS_NOT_FACT_CHECKED','filename':'UIS-417.html','sha256':V23.sha(raw)},raw
            V23.fetch_one=fake_fetch
            result=V23.capture(self.work,SCRIPT)
        finally:V23.fetch_one=old
        self.assertEqual(result['success_raw_captures'],1)
        self.assertEqual(result['canonical_admissions'],0)
        archive=Path(result['dest'])
        ledger=json.loads((archive/'REGISTRE_CAPTURES.json').read_text('utf8'))
        self.assertEqual(V23.sha((archive/'UIS-417.html').read_bytes()),ledger['files_sha256']['UIS-417.html'])
        self.assertFalse(ledger['publication_authorized'])

if __name__=='__main__':unittest.main()
