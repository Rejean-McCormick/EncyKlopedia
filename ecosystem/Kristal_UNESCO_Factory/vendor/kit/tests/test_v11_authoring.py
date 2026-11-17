"""v11 opt-in regression tests: legacy unchanged, strict KQ/KP, audited migration."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'tools/kristal.py'

def jwrite(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

class V11Authoring(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='kristal-v11-kit-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'workspace'
        self.run_ok('init',self.root,'--title','V11 Test')

    def call(self,*args):
        return subprocess.run([sys.executable,str(CLI),*map(str,args)],text=True,capture_output=True)

    def run_ok(self,*args):
        result=self.call(*args)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        return result.stdout

    def fixture(self):
        root=self.root
        base=root/'canon/domain/v11'
        ns='test:project'
        registry={'schema_version':'11.0','artifact_type':'kristal_identity_registry','namespace_id':ns,
           'registry_id':'test-registry','identities':[
            {'id':'KQ1001','kind':'entity','status':'stable'},
            {'id':'KQ1002','kind':'entity','status':'stable'},
            {'id':'KP2001','kind':'property','status':'stable'},
            {'id':'KA3001','kind':'assertion','status':'stable'},
            {'id':'KS4001','kind':'source','status':'stable'}]}
        graph={'schema_version':'11.0','artifact_type':'kristal_semantic_graph',
           'namespace_id':ns,'graph_id':'example-graph','entities':['KQ1001','KQ1002'],
           'properties':['KP2001'],'sources':['KS4001'],
           'assertions':[{'id':'KA3001','subject':'KQ1001','predicate':'KP2001','object':{'kind':'entity','id':'KQ1002'},'sources':['KS4001']}]}
        crosswalk={'schema_version':'11.0','artifact_type':'kristal_external_crosswalk','crosswalk_id':'test-crosswalk',
           'mappings':[{'mapping_id':'m1','local_ref':{'namespace_id':ns,'id':'KQ1001'},
           'external_ref':{'system':'wikidata','id':'Q8018'},'relation':'exactMatch','status':'accepted',
           'review':{'method':'human','decision_id':'d1','evidence_refs':['KS4001']}}]}
        fr={'namespace_id':ns,'semantic_id':'KQ1001','external_id':'Q8018','language':'fr',
           'preferred_term':"Augustin d'Hippone",'aliases':[], 'source_snapshot':'2026-demo'}
        layer=base/'dictionaries/wikidata-fr.jsonl';layer.parent.mkdir(parents=True,exist_ok=True)
        layer.write_text(json.dumps(fr,ensure_ascii=False)+'\n',encoding='utf8')
        catalog={'schema_version':'11.0','artifact_type':'kristal_dictionary_catalog','catalog_id':'test-catalog','namespace_id':ns,
        'languages':[{'tag':'fr','fallbacks':[],'layers':[{'kind':'wikidata','layer_id':'wikidata-fr','priority':100,
        'path':'wikidata-fr.jsonl','sha256':hashlib.sha256(layer.read_bytes()).hexdigest(),'source_snapshot':'2026-demo'}]},
        {'tag':'fr-CA','fallbacks':['fr'],'layers':[]}]}
        paths={'graph':base/'graph.json','registry':base/'registry.json',
               'crosswalk':base/'crosswalk.json','catalog':base/'dictionaries/catalog.json'}
        for k,v in zip(('graph','registry','crosswalk','catalog'),(graph,registry,crosswalk,catalog)):
            jwrite(paths[k],v)
        for k,p in paths.items():
            rel=p.relative_to(root).as_posix()
            self.run_ok('register-artifact',root,'--file',rel,'--artifact-id','urn:test:'+k,'--contract-id','test.'+k)
        args=['enable-v11',root]
        for k,p in paths.items():args+=['--'+k,p.relative_to(root).as_posix()]
        self.run_ok(*args)
        return paths

    def test_opt_in_and_build_preserves_legacy_contracts(self):
        self.fixture()
        self.run_ok('check-v11',self.root)
        self.run_ok('check',self.root)
        self.run_ok('build-v9',self.root)
        state=json.loads((self.root/'build/v9/state-snapshot.json').read_text())
        self.assertEqual(state['schema_version'],'9.0')
        self.assertTrue((self.root/'tools/kristal_v11_core.py').is_file())
        r=self.call('check',self.root)
        self.assertIn('Framework v11 identity profile',r.stdout)
        report=json.loads(self.run_ok('coverage-v11',self.root,'--locales','fr,fr-CA'))
        self.assertEqual(report['locales'][0]['KQ']['direct'],1)
        self.assertEqual(report['locales'][0]['KP']['missing'],1)
        self.assertEqual(report['locales'][1]['KQ']['fallback'],1)
        self.assertEqual(report['locales'][1]['KQ']['direct'],0)

    def test_fail_closed_when_graph_uses_a_word_as_predicate_or_label(self):
        paths=self.fixture()
        graph=json.loads(paths['graph'].read_text());graph['assertions'][0]['predicate']='position_documentee'
        jwrite(paths['graph'],graph)
        self.assertNotEqual(self.call('build-v9',self.root).returncode,0)
        graph['assertions'][0]['predicate']='KP2001';graph['label']='Merci'
        jwrite(paths['graph'],graph)
        self.assertNotEqual(self.call('check',self.root).returncode,0)

    def test_crosswalk_unverified_wikidata_label_fails(self):
        paths=self.fixture()
        cw=json.loads(paths['crosswalk'].read_text());cw['mappings'][0]['status']='candidate';cw['mappings'][0].pop('review')
        jwrite(paths['crosswalk'],cw)
        r=self.call('check',self.root)
        self.assertNotEqual(r.returncode,0)
        self.assertIn('Wikidata label without accepted exact',r.stdout+r.stderr)

    def test_dictionary_hash_fails_closed(self):
        self.fixture()
        p=self.root/'canon/domain/v11/dictionaries/wikidata-fr.jsonl'
        p.write_text(p.read_text()+' \n')
        self.assertNotEqual(self.call('build-v9',self.root).returncode,0)

    def plan_fixture(self,approved=True):
        paths=self.fixture()
        graph=json.loads(paths['graph'].read_text()); graph['assertions'][0]['predicate']='lie_a'
        source=self.root/'docs/legacy-shaped-draft.json';jwrite(source,graph)
        dg=hashlib.sha256(source.read_bytes()).hexdigest()
        plan={'schema_version':'11.0','artifact_type':'kristal_dik_conversion_plan','namespace_id':'test:project',
          'plan_id':'plan-1','catalog_id':'test-catalog','crosswalk_id':'test-crosswalk',
          'source':{'artifact_id':'demo-staged','sha256':dg,'declared_version':'legacy-v11-shaped'},
          'operations':[{'operation_id':'op1','source_path':'/assertions/0/predicate',
              'original_value':'lie_a','semantic_role':'property','target_id':'KP2001',
              'decision':({'status':'approved','decision_id':'d1','reviewer':'human','reason':'verified predicate','evidence_refs':['KS4001']} if approved else {'status':'pending'})}]}
        role={'format':'kristal.identity-role-map/11.0','source_sha256':dg,
          'roles':[{'path':'/assertions/0/predicate','role':'property'}],
          'review':{'decision_id':'role-1','reviewer':'human','reason':'verified predicate location','evidence_refs':['KS4001']}}
        jwrite(self.root/'docs/plan.json',plan);jwrite(self.root/'docs/roles.json',role)
        return source,plan,paths

    def test_migrate_only_reviewed_identity_fields_and_never_overwrite_source(self):
        source,plan,_=self.plan_fixture()
        original=source.read_bytes()
        self.run_ok('check-v11-plan',self.root,'--source','docs/legacy-shaped-draft.json','--plan','docs/plan.json','--roles','docs/roles.json')
        self.run_ok('apply-v11-plan',self.root,'--source','docs/legacy-shaped-draft.json','--plan','docs/plan.json',
            '--roles','docs/roles.json','--output','canon/domain/v11/converted.json',
            '--artifact-id','urn:test:converted','--contract-id','test.converted')
        self.assertEqual(source.read_bytes(),original)
        obj=json.loads((self.root/'canon/domain/v11/converted.json').read_text())
        self.assertEqual(obj['assertions'][0]['predicate'],'KP2001')
        self.assertEqual(len(json.loads((self.root/'canon/state.index.json').read_text())['canonical_artifacts']),5)
        self.assertNotEqual(self.call('apply-v11-plan',self.root,'--source','docs/legacy-shaped-draft.json','--plan','docs/plan.json',
            '--roles','docs/roles.json','--output','canon/domain/v11/converted.json',
            '--artifact-id','urn:test:converted2','--contract-id','test.converted').returncode,0)
        self.run_ok('build-v9',self.root)
        self.run_ok('select-v11-graph',self.root,'--graph','canon/domain/v11/converted.json')
        self.run_ok('check-v11',self.root)
        self.assertEqual(json.loads((self.root/'.kristal/v11/authoring.json').read_text())['graph'],
                         'canon/domain/v11/converted.json')
        self.assertTrue(list((self.root/'.kristal/v11/history').glob('*.json')))

    def test_pending_or_hash_drift_cannot_apply(self):
        source,_,_=self.plan_fixture(approved=False)
        result=self.call('check-v11-plan',self.root,'--source','docs/legacy-shaped-draft.json','--plan','docs/plan.json')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        args=['apply-v11-plan',self.root,'--source','docs/legacy-shaped-draft.json','--plan','docs/plan.json',
              '--roles','docs/roles.json','--output','canon/domain/v11/converted.json',
              '--artifact-id','urn:test:converted','--contract-id','test.converted']
        self.assertNotEqual(self.call(*args).returncode,0)
        self.assertFalse((self.root/'canon/domain/v11/converted.json').exists())
        plan=json.loads((self.root/'docs/plan.json').read_text())
        plan['operations'][0]['decision']={'status':'approved','reviewer':'human','reason':'approved','decision_id':'one','evidence_refs':['KS4001']}
        jwrite(self.root/'docs/plan.json',plan)
        source.write_text(source.read_text()+'\n')
        self.assertNotEqual(self.call(*args).returncode,0)
        self.assertFalse((self.root/'canon/domain/v11/converted.json').exists())

    def test_citation_text_cannot_be_targeted_by_reviewed_roles(self):
        source,plan,paths=self.plan_fixture()
        content=json.loads(source.read_text())
        content['citation']='Texte de citation conservé'
        jwrite(source,content)
        dg=hashlib.sha256(source.read_bytes()).hexdigest()
        plan['source']['sha256']=dg
        plan['operations'][0]['source_path']='/citation'
        plan['operations'][0]['original_value']='Texte de citation conservé'
        jwrite(self.root/'docs/plan.json',plan)
        roles=json.loads((self.root/'docs/roles.json').read_text())
        roles['source_sha256']=dg
        roles['roles']=[{'path':'/citation','role':'property'}]
        jwrite(self.root/'docs/roles.json',roles)
        r=self.call('apply-v11-plan',self.root,'--source','docs/legacy-shaped-draft.json',
          '--plan','docs/plan.json','--roles','docs/roles.json',
          '--output','canon/domain/v11/converted.json','--artifact-id','urn:test:bad','--contract-id','test.bad')
        self.assertNotEqual(r.returncode,0)
        self.assertFalse((self.root/'canon/domain/v11/converted.json').exists())
        self.assertEqual(json.loads(source.read_text())['citation'],'Texte de citation conservé')

    def test_default_legacy_workspaces_remain_valid(self):
        self.run_ok('check',self.root)
        self.assertFalse((self.root/'.kristal/v11/authoring.json').exists())
        self.assertNotEqual(self.call('check-v11',self.root).returncode,0)

if __name__=='__main__':unittest.main()
