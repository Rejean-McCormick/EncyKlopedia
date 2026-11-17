"""diK interoperability and failure-atomic v11 registration (draft.3)."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import kristal_v11_core as v11
CLI=ROOT/'tools/kristal.py'
SAMPLE=ROOT/'examples/demo-semantic-v11'

class Interop(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='authoring-dik-')
        self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name)/'workspace'
        shutil.copytree(SAMPLE,self.project)
        self.canon=self.project/'canon/domain/v11'
        self.input=self.canon/'dictionaries/catalog.json'

    def cli(self,*args,ok=True):
        r=subprocess.run([sys.executable,str(CLI),*map(str,args)],text=True,capture_output=True)
        if ok:self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)
        return r

    def test_import_register_select_and_copy_isolation(self):
        graph=self.canon/'graph.json'; before=v11.digest(graph)
        old_index=v11.digest(self.project/'canon/state.index.json')
        result=json.loads(self.cli('import-dik-catalog',self.project,'--catalog',self.input,
                         '--revision','new-wikidata','--register','--artifact-id','urn:diK:1','--contract-id','test.dik').stdout)
        self.assertTrue(result['registered']);self.assertFalse(result['selected'])
        self.assertEqual(v11.digest(graph),before)
        self.assertNotEqual(v11.digest(self.project/'canon/state.index.json'),old_index)
        profile=v11.load_profile(self.project)
        self.assertEqual(profile['catalog'],'canon/domain/v11/dictionaries/catalog.json')
        selected=result['catalog']
        self.cli('select-v11-catalog',self.project,'--catalog',selected)
        self.assertEqual(v11.load_profile(self.project)['catalog'],selected)
        self.cli('check-v11',self.project)
        self.assertEqual(v11.digest(graph),before)
        self.assertTrue((self.project/'.kristal/v11/history').is_dir())
        self.assertNotEqual(self.cli('import-dik-catalog',self.project,'--catalog',self.input,
                          '--revision','new-wikidata',ok=False).returncode,0)

    def test_reject_unapproved_wikidata_label(self):
        import_dir=Path(self.tmp.name)/'foreign';shutil.copytree(self.input.parent,import_dir)
        shard=import_dir/'wikidata-fr.jsonl'
        line=json.loads(shard.read_text().splitlines()[0]);line['external_id']='Q9999'
        shard.write_text(json.dumps(line)+'\n')
        cat=import_dir/'catalog.json';obj=json.loads(cat.read_text());obj['languages'][0]['layers'][0]['sha256']=v11.digest(shard)
        cat.write_text(json.dumps(obj))
        self.assertNotEqual(self.cli('import-dik-catalog',self.project,'--catalog',cat,
                            '--revision','invalid',ok=False).returncode,0)
        self.assertFalse((self.canon/'dictionaries/dik-revisions/invalid').exists())

    def test_detect_wikidata_layer_hash_tampering(self):
        bad=Path(self.tmp.name)/'bad';shutil.copytree(self.input.parent,bad)
        (bad/'wikidata-fr.jsonl').write_bytes(b'changed')
        self.assertNotEqual(self.cli('import-dik-catalog',self.project,'--catalog',bad/'catalog.json',
                             '--revision','bad',ok=False).returncode,0)
        self.assertFalse((self.canon/'dictionaries/dik-revisions/bad').exists())

    def test_graph_registration_crash_before_index_rolls_back(self):
        state=self.project/'canon/state.index.json';old=v11.digest(state)
        rel='canon/domain/v11/new-crash.json';payload=b'{"hello":"world"}\n'
        with self.assertRaisesRegex(v11.V11Error,'INJECTED_CRASH_AFTER_ARTIFACT'):
            v11.register_artifact_recoverably(self.project,rel=rel,payload=payload,
              artifact_id='urn:test:crash1',contract_id='test.graph',fault='after_artifact')
        self.assertTrue((self.project/rel).is_file())
        self.assertEqual(v11.digest(state),old)
        self.assertTrue(any(x['status']=='pending' for x in v11.recover_v11(self.project)))
        with self.assertRaisesRegex(v11.V11Error,'pending v11 transaction'):
            v11.register_artifact_recoverably(self.project,rel='canon/domain/v11/other.json',payload=payload,
              artifact_id='urn:test:other',contract_id='test.graph')
        self.assertEqual(v11.recover_v11(self.project,mode='rollback')[0]['status'],'rolled_back')
        self.assertFalse((self.project/rel).exists());self.assertEqual(v11.digest(state),old)

    def test_crash_after_index_requires_finish_not_rollback(self):
        rel='canon/domain/v11/new-after-index.json';payload=b'{"graph":"new"}\n'
        with self.assertRaisesRegex(v11.V11Error,'INJECTED_CRASH_AFTER_INDEX'):
            v11.register_artifact_recoverably(self.project,rel=rel,payload=payload,
              artifact_id='urn:test:crash2',contract_id='test.graph',fault='after_index')
        with self.assertRaisesRegex(v11.V11Error,'rollback forbidden'):
            v11.recover_v11(self.project,mode='rollback')
        self.assertEqual(v11.recover_v11(self.project,mode='finish')[0]['status'],'complete')
        items=v11.read(self.project/'canon/state.index.json')['canonical_artifacts']
        self.assertTrue(any(x['artifact_id']=='urn:test:crash2' for x in items))
        self.assertEqual((self.project/rel).read_bytes(),payload)

    def test_recovery_refuses_tampered_output(self):
        rel='canon/domain/v11/new-tamper.json'
        with self.assertRaises(v11.V11Error):
            v11.register_artifact_recoverably(self.project,rel=rel,payload=b'{}\n',
              artifact_id='urn:test:tamper',contract_id='test.graph',fault='after_artifact')
        (self.project/rel).write_bytes(b'{"changed":true}')
        with self.assertRaisesRegex(v11.V11Error,'changed'):
            v11.recover_v11(self.project,mode='finish')

    def test_curated_layer_survives_new_import(self):
        # The curated French label is not replaced by new Wikidata source text.
        incoming=Path(self.tmp.name)/'incoming'
        shutil.copytree(self.input.parent,incoming)
        old_catalog=self.input
        obj=json.loads(old_catalog.read_text())
        curated={'schema_version':'11.0','artifact_type':'kristal_curated_dictionary',
          'namespace_id':'test:project','language':'fr',
          'entries':[{'semantic_id':'KQ1001','preferred_term':'Saint Augustin',
              'alternate_terms':[], 'review':{'decision_id':'d-curated','reviewer':'human','reason':'local preference'}}]}
        curated_file=self.input.parent/'curated-fr.json'
        curated_file.write_text(json.dumps(curated,ensure_ascii=False)+'\n',encoding='utf8')
        obj['languages'][0]['layers'].append({'kind':'curated','layer_id':'curated-fr',
            'priority':200,'path':'curated-fr.json','sha256':v11.digest(curated_file)})
        old_catalog.write_text(json.dumps(obj,ensure_ascii=False)+'\n',encoding='utf8')
        outcome=v11.build_dik_catalog_revision(self.project,incoming/'catalog.json','curation-preserved')
        proposed=json.loads((self.project/outcome['catalog']).read_text())
        layers=proposed['languages'][0]['layers']
        self.assertEqual({layer['kind'] for layer in layers},{'wikidata','curated'})
        self.assertEqual({layer['priority'] for layer in layers},{100,200})
        self.assertEqual(outcome['old_catalog_sha256'],v11.digest(old_catalog))
        self.assertEqual(v11.read(self.canon/'graph.json')['assertions'][0]['subject'],'KQ1001')

    def test_unregistered_catalog_cannot_be_selected(self):
        out=json.loads(self.cli('import-dik-catalog',self.project,'--catalog',self.input,'--revision','unregistered').stdout)
        self.assertFalse(out['registered'])
        self.assertNotEqual(self.cli('select-v11-catalog',self.project,'--catalog',out['catalog'],ok=False).returncode,0)

if __name__=='__main__':unittest.main()
