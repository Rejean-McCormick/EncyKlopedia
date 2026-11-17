"""Standalone Spek connectors and language-channel boundary regression tests."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from spek.core import ValidationError, compile_inputs, digest
from spek.bridge import bridge_import, fetch_konstellation, safe_navigation
from spek.ai_phrases import import_ai
from spek.document import project_document
from spek.render import article_html

ROOT=Path(__file__).resolve().parent.parent
DIR=ROOT/'examples'/'bridge'

def data(p):return json.loads(p.read_text(encoding='utf-8'))

class StandaloneBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.article=data(ROOT/'examples'/'article.json')
        cls.real=data(ROOT/'examples'/'realizations.json')
        cls.layout=[data(p) for p in sorted((ROOT/'layouts').glob('*.json'))]
        cls.k=data(DIR/'konstellation-resultset.json')
        cls.kmap=data(DIR/'konstellation-mapping.json')
        cls.ext=data(DIR/'external-system-exchange.json')
        cls.extmap=data(DIR/'external-system-mapping.json')

    def bridged(self,kind='konstellation'):
        return bridge_import(kind,self.k if kind=='konstellation' else self.ext,
                             self.article,self.kmap if kind=='konstellation' else self.extmap)

    def test_konstellation_resultset_has_real_0_2_schema(self):
        try:import jsonschema
        except ImportError:self.skipTest('jsonschema not installed for optional upstream contract validation')
        import zipfile
        snapshot=ROOT.parent.parent/'upstream'/'Konstellation_Code_snapshot.zip'
        if snapshot.exists():
            with zipfile.ZipFile(snapshot) as z:
                schema=json.loads(z.read('contracts/result-set.schema.json'))
            jsonschema.validate(self.k,schema)
        else:
            # Self-contained checkout: validate the required ResultSet contract
            # subset; upstream full-schema conformance was tested separately.
            self.assertEqual(self.k['schemaVersion'],'0.2')
            self.assertEqual(self.k['evaluation'],'complete')
            self.assertIsNone(self.k['nextCursor'])
            self.assertEqual(self.k['total']['kind'],'exact')
            for row in self.k['rows']:
                self.assertTrue(row['witnessesComplete'])
                for witness in row['witnesses']:
                    self.assertIn(witness['kind'], ('assertion','absence_in_view','derivation'))

    def test_konstellation_bridge_builds_with_scope_and_pins(self):
        src=self.bridged()
        self.assertEqual(src['source']['reader_policy_ref'],'demo:reader-policy:v1')
        self.assertEqual(src['source']['origin'],'external_projection')
        self.assertEqual(src['units'][0]['external_ref'],'a.u.result.claim')
        model=compile_inputs(src,self.real,self.layout)
        self.assertTrue(model.demo)
        self.assertFalse(model.source_verified)
        self.assertTrue(project_document(model,'en').sections[0].items('claim')[0].navigation_url)

    def test_generic_exchange_not_konstellation_dependent(self):
        s=self.bridged('exchange')
        self.assertEqual(s['source']['external_system'],'external-demo-system')
        self.assertEqual(s['source']['reader_policy_ref'],'demo:reader-policy:v1')
        model=compile_inputs(s,self.real,self.layout)
        self.assertIn('other.example.org',article_html(model,'en'))
        self.assertIn('View in source system',article_html(model,'en'))

    def test_policy_mismatch_refused(self):
        k=copy.deepcopy(self.k)
        k['context']['readerPolicyRef']='public-or-other-policy'
        with self.assertRaisesRegex(ValidationError,'policy differs'):
            bridge_import('konstellation',k,self.article,self.kmap)

    def test_dataset_mismatch_refused(self):
        k=copy.deepcopy(self.k);k['context']['datasetRef']='other'
        with self.assertRaises(ValidationError):bridge_import('konstellation',k,self.article,self.kmap)

    def test_incomplete_result_refused(self):
        for field,value in [('nextCursor','next'),('evaluation','partial')]:
            k=copy.deepcopy(self.k);k[field]=value
            with self.subTest(field=field),self.assertRaises(ValidationError):
                bridge_import('konstellation',k,self.article,self.kmap)
        k=copy.deepcopy(self.k);k['rows'][0]['witnessesComplete']=False
        with self.assertRaises(ValidationError):bridge_import('konstellation',k,self.article,self.kmap)

    def test_missing_assertion_and_unpinned_mutation_refused(self):
        k=copy.deepcopy(self.k);k['assertions'][0]['payload']['unexpected']='changed'
        with self.assertRaisesRegex(ValidationError,'payload changed'):
            bridge_import('konstellation',k,self.article,self.kmap)
        k=copy.deepcopy(self.k);k['rows'][0]['witnesses'][0]['assertionRefs'].append('a.not.present')
        with self.assertRaisesRegex(ValidationError,'missing'):
            bridge_import('konstellation',k,self.article,self.kmap)

    def test_mapped_claims_required_all(self):
        m=copy.deepcopy(self.kmap)
        del m['unit_bindings']['u.result.claim']
        with self.assertRaisesRegex(ValidationError,'Every template unit'):
            bridge_import('konstellation',self.k,self.article,m)

    def test_no_external_authority_escalation(self):
        model=compile_inputs(self.bridged(),self.real,self.layout)
        with self.assertRaisesRegex(ValidationError,'pinned v9'):
            compile_inputs(self.bridged(),self.real,self.layout,production=True)
        self.assertEqual(model.source['source']['scientific_review'],'not_submitted')

    def test_other_system_requires_local_preview_export(self):
        k=copy.deepcopy(self.ext);k['context']['export_status']='granted_to_publish'
        with self.assertRaisesRegex(ValidationError,'not approved'):
            bridge_import('exchange',k,self.article,self.extmap)

    def test_external_source_binding_hash_refused(self):
        k=copy.deepcopy(self.ext);k['sources'][0]['payload']['locator']='tampered'
        with self.assertRaisesRegex(ValidationError,'Source changed'):
            bridge_import('exchange',k,self.article,self.extmap)

    def test_navigation_javascript_rejected_and_escaped(self):
        with self.assertRaises(ValidationError):safe_navigation('javascript:alert({id})','a.foo')
        with self.assertRaises(ValidationError):safe_navigation('https://user:pass@site.test/?focus={id}','a.foo')
        self.assertEqual(safe_navigation('https://example.org/?focus={id}','a.x:y'),
                         'https://example.org/?focus=a.x%3Ay')
        src=self.bridged();src['units'][0]['navigation_url']='javascript:alert(1)'
        with self.assertRaisesRegex(ValidationError,'Unsafe navigation'):
            compile_inputs(src,self.real,self.layout)

    def test_unambiguous_ai_import(self):
        ai=data(DIR/'ai-preconstructed-example.json')
        base=data(DIR/'realizations-without-example-claim.json')
        merged=import_ai(ai,base)
        node=merged['entries']['u.result.claim']['en']
        self.assertEqual(node['channel'],'ai_preconstructed')
        self.assertNotIn('runtime_set_id',node)
        self.assertEqual(node['status'],'fixture')
        model=compile_inputs(self.bridged('exchange'),merged,self.layout)
        proj=project_document(model,'en')
        claim=proj.sections[0].items('claim')[0]
        self.assertEqual(claim.realization_channel,'ai_preconstructed')
        self.assertEqual(claim.realization_runtime_set_id,'')
        self.assertEqual(claim.realization_model_id,'illustrative-placeholder-no-model-invoked')

    def test_ai_cannot_claim_semantik_runtime_or_qualification(self):
        bundle=import_ai(data(DIR/'ai-preconstructed-example.json'))
        node=bundle['entries']['u.result.claim']['en']
        with self.assertRaises(ValidationError):import_ai({'format':'spek.ai-phrases/0.1',
              'phrases':[dict(data(DIR/'ai-preconstructed-example.json')['phrases'][0],runtime_set_id='fake')]})
        real=copy.deepcopy(self.real)
        real['entries']['u.result.claim']['en']=dict(node,status='qualified',runtime_set_id='fake')
        with self.assertRaisesRegex(ValidationError,'cannot claim GF'):
            compile_inputs(self.article,real,self.layout)

    def test_ai_review_requires_explicit_reference(self):
        x=data(DIR/'ai-preconstructed-example.json')
        x['phrases'][0]['human_review']={'status':'approved'}
        with self.assertRaisesRegex(ValidationError,'reference required'):
            import_ai(x)
        x['phrases'][0]['human_review']={'status':'approved','review_ref':'local-human-review:pending-authentication'}
        out=import_ai(x)
        self.assertEqual(out['entries']['u.result.claim']['fr']['status'],'reviewed')

    def test_import_does_not_overwrite_existing_semantik_phrase(self):
        with self.assertRaisesRegex(ValidationError,'Duplicate realization'):
            import_ai(data(DIR/'ai-preconstructed-example.json'),self.real)

    def test_cli_roundtrip_konstellation_and_ai_without_services(self):
        with tempfile.TemporaryDirectory() as t:
            a=Path(t)/'source.json';r=Path(t)/'realizations.json';d=Path(t)/'dist'
            call=lambda *params:subprocess.run([sys.executable,'-m','spek',*map(str,params)],cwd=ROOT,
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            p=call('bridge-import','--adapter','konstellation','--input',DIR/'konstellation-resultset.json',
                   '--template',ROOT/'examples'/'article.json','--mapping',DIR/'konstellation-mapping.json','--out',a)
            self.assertEqual(p.returncode,0,p.stderr)
            p=call('import-ai','--input',DIR/'ai-preconstructed-example.json',
                   '--base',DIR/'realizations-without-example-claim.json','--out',r)
            self.assertEqual(p.returncode,0,p.stderr)
            p=call('build','--source',a,'--realizations',r,'--out',d,'--formats','html,tex')
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertIn('source-navigation',(d/'en'/'index.html').read_text())
            self.assertEqual(call('verify-site',d).returncode,0)

if __name__=='__main__':unittest.main()
