from __future__ import annotations
import bz2, gzip, json, sqlite3, subprocess, sys, tempfile, unittest
from pathlib import Path

TOOL=Path(__file__).resolve().parents[1]
SCRIPTS=TOOL/'scripts'
PERF=TOOL.parent/'performance'/'scripts'

class ScopePipelineTest(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(); self.root=Path(self.td.name)/'EncyKlopedia'; self.root.mkdir(); (self.root/'MANIFEST.json').write_text('{}')
        for d in ['10_sources/seeds/active/intellectual-registry','10_sources/wikidata/dumps/current','20_ingest','30_working/scopes','50_mediatheque']:(self.root/d).mkdir(parents=True,exist_ok=True)
        prod=self.root/'00_system/tools/scope-builder'; (prod/'config/scopes').mkdir(parents=True,exist_ok=True); (prod/'config/property-groups.json').write_text((TOOL/'config/property-groups.json').read_text(),encoding='utf-8')
        contracts=self.root/'00_system/contracts'; contracts.mkdir(parents=True,exist_ok=True)
        source_contracts=TOOL.parents[1]/'contracts'
        (contracts/'knowledge-baseline.json').write_text((source_contracts/'knowledge-baseline.json').read_text(),encoding='utf-8')
        scope={'schema_version':'encyklopedia-scope/v3','scope_key':'test-scope','title':'Test','root_source':{'kind':'registry','path':'10_sources/seeds/active/intellectual-registry/test.seed.json'},'root_semantics':{'role':'person_root','kind':'person'},'requires_complete_global_index':False,'discovery':{'include_all_entity_relations_from_roots':True,'reverse_root_relations':{'P50':{'source_role':'work','relation_role':'authored_work'}},'root_relation_roles':{'P19':'place','P135':'movement','P800':'work'},'follow_rules':[{'name':'works_context','source_roles':['work'],'direction':'out','property_group':'work_context','default_target_role':'work_context'}],'raw_max_passes':4,'max_entities':1000,'max_edges':10000},'evidence':{'preserve_full_entity_json':True}}
        (prod/'config/scopes/test.scope.json').write_text(json.dumps(scope),encoding='utf-8')
        seed={'schema_version':'x','registry_key':'test','records':[{'key':'person','display_name':'Test Thinker','chronology':{'birth_year':100,'death_year':170},'representation_kind':'historical_person'}]}
        (self.root/'10_sources/seeds/active/intellectual-registry/test.seed.json').write_text(json.dumps(seed),encoding='utf-8'); self._dump()
    def tearDown(self):self.td.cleanup()
    def _dump(self):
        q1={'type':'item','id':'Q1','labels':{'en':{'language':'en','value':'Test Thinker'}},'descriptions':{},'aliases':{},'sitelinks':{'enwiki':{'site':'enwiki','title':'Test Thinker','badges':[]}},'claims':{
          'P31':[{'id':'Q1$human','type':'statement','rank':'normal','mainsnak':{'snaktype':'value','property':'P31','datatype':'wikibase-item','datavalue':{'type':'wikibase-entityid','value':{'entity-type':'item','numeric-id':5,'id':'Q5'}}},'qualifiers':{},'references':[]}],
          'P19':[{'id':'Q1$birthplace','type':'statement','rank':'normal','mainsnak':{'snaktype':'value','property':'P19','datatype':'wikibase-item','datavalue':{'type':'wikibase-entityid','value':{'entity-type':'item','numeric-id':2,'id':'Q2'}}},'qualifiers':{},'references':[]}],
          'P135':[{'id':'Q1$movement','type':'statement','rank':'normal','mainsnak':{'snaktype':'value','property':'P135','datatype':'wikibase-item','datavalue':{'type':'wikibase-entityid','value':{'entity-type':'item','numeric-id':4,'id':'Q4'}}},'qualifiers':{},'references':[]}],
          'P800':[{'id':'Q1$work','type':'statement','rank':'normal','mainsnak':{'snaktype':'value','property':'P800','datatype':'wikibase-item','datavalue':{'type':'wikibase-entityid','value':{'entity-type':'item','numeric-id':3,'id':'Q3'}}},'qualifiers':{},'references':[]}],
          'P569':[{'id':'Q1$birth','type':'statement','rank':'normal','mainsnak':{'snaktype':'value','property':'P569','datatype':'time','datavalue':{'type':'time','value':{'time':'+0100-01-01T00:00:00Z','timezone':0,'before':0,'after':0,'precision':9,'calendarmodel':'http://www.wikidata.org/entity/Q1985727'}}},'qualifiers':{'P580':[{'snaktype':'value','property':'P580','datatype':'time','datavalue':{'type':'time','value':{'time':'+0100-01-01T00:00:00Z','timezone':0,'before':0,'after':0,'precision':9,'calendarmodel':'http://www.wikidata.org/entity/Q1985727'}}}]},'references':[{'hash':'abc','snaks':{'P248':[{'snaktype':'value','property':'P248','datatype':'wikibase-item','datavalue':{'type':'wikibase-entityid','value':{'entity-type':'item','numeric-id':3,'id':'Q3'}}}]},'snaks-order':['P248']}]}],
          'P570':[{'id':'Q1$death','type':'statement','rank':'normal','mainsnak':{'snaktype':'value','property':'P570','datatype':'time','datavalue':{'type':'time','value':{'time':'+0170-01-01T00:00:00Z','timezone':0,'before':0,'after':0,'precision':9,'calendarmodel':'http://www.wikidata.org/entity/Q1985727'}}},'qualifiers':{},'references':[]}]
        }}
        q2={'type':'item','id':'Q2','labels':{'en':{'language':'en','value':'Test City'}},'descriptions':{},'aliases':{},'sitelinks':{},'claims':{}}
        q3={'type':'item','id':'Q3','labels':{'en':{'language':'en','value':'Test Book'}},'descriptions':{},'aliases':{},'sitelinks':{},'claims':{
          'P50':[{'id':'Q3$author','type':'statement','rank':'normal','mainsnak':{'snaktype':'value','property':'P50','datatype':'wikibase-item','datavalue':{'type':'wikibase-entityid','value':{'entity-type':'item','numeric-id':1,'id':'Q1'}}},'qualifiers':{},'references':[]}],
          'P407':[{'id':'Q3$lang','type':'statement','rank':'normal','mainsnak':{'snaktype':'value','property':'P407','datatype':'wikibase-item','datavalue':{'type':'wikibase-entityid','value':{'entity-type':'item','numeric-id':6,'id':'Q6'}}},'qualifiers':{},'references':[]}],
          'P1476':[{'id':'Q3$title','type':'statement','rank':'normal','mainsnak':{'snaktype':'value','property':'P1476','datatype':'monolingualtext','datavalue':{'type':'monolingualtext','value':{'text':'Liber Test','language':'la'}}},'qualifiers':{},'references':[]}],
          'P1938':[{'id':'Q3$gutenberg','type':'statement','rank':'normal','mainsnak':{'snaktype':'value','property':'P1938','datatype':'external-id','datavalue':{'type':'string','value':'1234'}},'qualifiers':{},'references':[]}]}}
        q4={'type':'item','id':'Q4','labels':{'en':{'language':'en','value':'Test Movement'}},'descriptions':{},'aliases':{},'sitelinks':{},'claims':{}}
        q5={'type':'item','id':'Q5','labels':{'en':{'language':'en','value':'human'}},'descriptions':{},'aliases':{},'sitelinks':{},'claims':{}}
        q6={'type':'item','id':'Q6','labels':{'en':{'language':'en','value':'Latin'}},'descriptions':{},'aliases':{},'sitelinks':{},'claims':{}}
        p=self.root/'10_sources/wikidata/dumps/current/test.json.bz2'
        with bz2.open(p,'wt',encoding='utf-8') as f:
            f.write('[\n'); ents=[q1,q2,q3,q4,q5,q6]
            for i,e in enumerate(ents):f.write(json.dumps(e,separators=(',',':'))+(',' if i<len(ents)-1 else '')+'\n')
            f.write(']\n')
    def run_script(self,name,*args):
        cmd=[sys.executable,str(SCRIPTS/name),'--root',str(self.root),*map(str,args)]; r=subprocess.run(cmd,capture_output=True,text=True)
        if r.returncode!=0:self.fail(f'{name} failed\nSTDOUT:{r.stdout}\nSTDERR:{r.stderr}')
        return r
    def test_direct_lossless_without_global_db(self):
        cfg=self.root/'00_system/tools/scope-builder/config/scopes/test.scope.json'
        self.run_script('01_resolve_roots.py','--scope',cfg,'--backend','raw')
        roots=json.loads((self.root/'30_working/scopes/test-scope/roots.resolved.json').read_text()); self.assertEqual(roots['person']['qid'],'Q1')
        self.run_script('02_discover_scope.py','--scope',cfg,'--backend','raw')
        self.run_script('03_freeze_scope.py','--scope',cfg)
        freeze=json.loads((self.root/'30_working/scopes/test-scope/scope.freeze.json').read_text()); self.assertIn('Q2',freeze['entity_ids']); self.assertIn('Q3',freeze['entity_ids']); self.assertIn('Q6',freeze['entity_ids'])
        self.run_script('04_extract_evidence.py','--scope',cfg)
        latest=json.loads((self.root/'30_working/scopes/test-scope/evidence.latest.json').read_text()); sid=latest['snapshot_id']; snap=self.root/'20_ingest/scope-snapshots/test-scope'/sid
        with gzip.open(snap/'entities.wikidata.jsonl.gz','rt',encoding='utf-8') as f:objs={o['id']:o for o in map(json.loads,f)}
        birth=objs['Q1']['claims']['P569'][0]; self.assertIn('P580',birth['qualifiers']); self.assertIn('P248',birth['references'][0]['snaks']); self.assertEqual(objs['Q3']['claims']['P1938'][0]['mainsnak']['datavalue']['value'],'1234')
        self.run_script('07_publish_referents.py','--scope',cfg)
        rlatest=json.loads((self.root/'20_ingest/referent-registries/test-scope/latest.json').read_text()); registry=json.loads((self.root/rlatest['path']).read_text())
        rk={x['ref']:x['kind'] for x in registry['referents']}; self.assertEqual(rk['wikidata:Q1'],'person'); self.assertEqual(rk['wikidata:Q3'],'work')
        self.run_script('07_publish_mediatheque.py','--scope',cfg); works=(self.root/'50_mediatheque/catalog/candidates/wikidata/test-scope'/f'{sid}.works.jsonl').read_text(); self.assertIn('P1938',works); self.assertIn('edition_identity',works)
        self.run_script('08_prepare_daat_handoff.py','--scope',cfg); self.assertFalse((self.root/'40_kristal').exists())
        handoff_latest=json.loads((self.root/'20_ingest/daat-handoff/test-scope/latest.json').read_text()); handoff=json.loads((self.root/handoff_latest['path']).read_text()); self.assertEqual(handoff['contract'],'encyklopedia.corpus-harvest-handoff/1.0.0'); self.assertTrue(any(x['role']=='referent_registry_candidate' for x in handoff['files'])); self.assertFalse(any(x['role']=='project_query_index' for x in handoff['files'])); self.assertFalse(handoff['interaction_kernel']['message_emitted'])
    def test_orchestrator_raw_end_to_end(self):
        cfg=self.root/'00_system/tools/scope-builder/config/scopes/test.scope.json'
        cmd=[sys.executable,str(SCRIPTS/'run_scope_pipeline.py'),'--root',str(self.root),'--scope',str(cfg),'--discovery-backend','raw','--through','handoff']
        r=subprocess.run(cmd,capture_output=True,text=True)
        if r.returncode!=0:self.fail(f'orchestrator failed\nSTDOUT:{r.stdout}\nSTDERR:{r.stderr}')
        latest=json.loads((self.root/'20_ingest/daat-handoff/test-scope/latest.json').read_text())
        self.assertTrue(latest.get('handoff_id'))
        self.assertFalse((self.root/'30_working/scopes/test-scope/index/test-scope.sqlite').exists())

    def test_fast_access_plain_dump(self):
        cfg=self.root/'00_system/tools/scope-builder/config/scopes/test.scope.json'
        bz=self.root/'10_sources/wikidata/dumps/current/test.json.bz2'; plain=bz.with_suffix('')
        with bz2.open(bz,'rb') as src, plain.open('wb') as dst: dst.write(src.read())
        bz.unlink()
        self.run_script('01_resolve_roots.py','--scope',cfg,'--backend','raw')
        cmd=[sys.executable,str(PERF/'build_fast_access.py'),'--root',str(self.root),'--initial-qid-capacity','1000','--reverse-properties','P50,P170']
        r=subprocess.run(cmd,capture_output=True,text=True)
        if r.returncode!=0:self.fail(f'fast index failed\nSTDOUT:{r.stdout}\nSTDERR:{r.stderr}')
        self.run_script('02_discover_scope.py','--scope',cfg,'--backend','fast')
        self.run_script('03_freeze_scope.py','--scope',cfg)
        self.run_script('04_extract_evidence.py','--scope',cfg)
        latest=json.loads((self.root/'30_working/scopes/test-scope/evidence.latest.json').read_text()); snap=self.root/latest['path']; man=json.loads((snap/'snapshot-manifest.json').read_text())
        self.assertEqual(man['extraction_mode'],'fast_random_access')
        stats=json.loads((self.root/'30_working/scopes/test-scope/discovery/stats.json').read_text())
        self.assertEqual(stats['discovery_backend']['backend'],'fast')

    def test_non_person_root_scope_is_supported(self):
        prod=self.root/'00_system/tools/scope-builder'
        seed={'schema_version':'x','registry_key':'work-root','records':[{'key':'book','display_name':'Test Book','qid':'Q3','representation_kind':'work'}]}
        (self.root/'10_sources/seeds/active/intellectual-registry/work-root.seed.json').write_text(json.dumps(seed),encoding='utf-8')
        scope={
            'schema_version':'encyklopedia-scope/v3','scope_key':'work-root','title':'Work Root',
            'root_source':{'kind':'registry','path':'10_sources/seeds/active/intellectual-registry/work-root.seed.json'},
            'root_semantics':{'role':'work_root','kind':'work'},
            'discovery':{
                'include_all_entity_relations_from_roots':True,
                'reverse_root_relations':{},
                'root_relation_roles':{'P50':'person','P407':'concept'},
                'follow_rules':[],'raw_max_passes':3,'max_entities':1000,'max_edges':10000
            },
            'evidence':{'preserve_full_entity_json':True}
        }
        cfg=prod/'config/scopes/work-root.scope.json'; cfg.write_text(json.dumps(scope),encoding='utf-8')
        self.run_script('01_resolve_roots.py','--scope',cfg,'--backend','raw')
        self.run_script('02_discover_scope.py','--scope',cfg,'--backend','raw')
        self.run_script('03_freeze_scope.py','--scope',cfg)
        freeze=json.loads((self.root/'30_working/scopes/work-root/scope.freeze.json').read_text())
        self.assertEqual(freeze['root_semantics'],{'role':'work_root','kind':'work'})
        self.assertIn('work_root',freeze['entity_roles']['Q3']['roles'])
        self.run_script('04_extract_evidence.py','--scope',cfg)
        self.run_script('07_publish_referents.py','--scope',cfg)
        latest=json.loads((self.root/'20_ingest/referent-registries/work-root/latest.json').read_text())
        registry=json.loads((self.root/latest['path']).read_text())
        q3=next(x for x in registry['referents'] if x['ref']=='wikidata:Q3')
        self.assertEqual(q3['kind'],'work')
        self.run_script('06_build_scope_index.py','--scope',cfg)
        db=self.root/'30_working/scopes/work-root/index/work-root.sqlite'; c=sqlite3.connect(db)
        roots=c.execute('SELECT wid,role FROM v_scope_roots').fetchall(); c.close()
        self.assertIn(('Q3','work_root'),roots)

    def test_optional_project_index_still_works(self):
        cfg=self.root/'00_system/tools/scope-builder/config/scopes/test.scope.json'
        self.run_script('01_resolve_roots.py','--scope',cfg,'--backend','raw'); self.run_script('02_discover_scope.py','--scope',cfg,'--backend','raw'); self.run_script('03_freeze_scope.py','--scope',cfg); self.run_script('04_extract_evidence.py','--scope',cfg); self.run_script('06_build_scope_index.py','--scope',cfg)
        db=self.root/'30_working/scopes/test-scope/index/test-scope.sqlite'; c=sqlite3.connect(db); c.row_factory=sqlite3.Row; birth=c.execute("SELECT * FROM statement WHERE subject_wid='Q1' AND property_id='P569'").fetchone(); self.assertIn('P580',birth['qualifiers_json']); self.assertIn('P248',birth['references_json']); c.close()

if __name__=='__main__':unittest.main()
