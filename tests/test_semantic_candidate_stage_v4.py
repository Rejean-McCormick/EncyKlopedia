"""Synthetic, offline end-to-end tests for the candidate (not canonical) stage."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('semantic_candidate_stage_v4',ROOT/'tools/unesco_pilot/semantic_candidate_stage_v4.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

class StageTest(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.work=Path(t.name)/'private_work';self.work.mkdir()
        self.xml=self.work/'wikipedia_extract';self.xml.mkdir()
        self.records=[];self.entries=[]
        for i in range(1,42):
            cid=f'concept{i}'
            self.records.append({'unesco_id':cid,'unesco_uri':f'https://unesco.test/{cid}',
                'unesco_preferred_labels':{'en':[f'Topic {i}']},'wikidata':{
                     'qid':f'Q{i+100}' if i<=36 else None,'canonical_exact_match':False},
                'skos':{'broader':[],'related':[],'narrower':[]},'wikipedia_en_inventory':[]})
            self.entries.append({'unesco_id':cid,'unesco_source_uri':f'https://unesco.test/{cid}',
                'wikipedia_en':[]})
        self.records[9]['skos']['related']=['concept11','concept501']
        for cid,pid,body,title in [('concept10',42,b'An evidence candidate with some text','Example'),
                                   ('concept11',43,b'#REDIRECT [[Example]]\n','Pointer')]:
            index=int(cid.replace('concept',''))-1
            bodyfile=self.xml/f'page-{pid}.wikitext.txt';bodyfile.write_bytes(body)
            d=hashlib.sha256(body).hexdigest()
            self.records[index]['wikipedia_en_inventory']=[{'page_id':pid,'title':title,'latest_revision_id':9}]
            self.entries[index]['wikipedia_en']=[{'page_id':pid,
               'wikipedia_page_metadata':{'page_id':pid,'title':title,'latest_revision_id':9},
               'local_text':{'revision_id':'9','text_sha256':d,'title_agrees':True,'revision_agrees':True,
                   'ai_context_eligible':True,'source_integrity_status':'CANDIDATE_MATCHED'}}]
        self.inventory={'profile':'encyklopedia.unesco-local-wikipedia-handoff/1.0','branch':'unesco-mt1-10',
                        'not_canonical':True,'not_publication':True,'approval_status':'BLOCKED',
                        'records':self.records}
        self.report={'branch':'unesco-mt1-10','status':'PRIVATE_RESEARCH_PREPARED_NOT_PUBLISHED',
                     'concepts_discovered':41,'articles_generated':0,'public_release_authorized':False}
        self.queue={'branch':'unesco-mt1-10','one_branch_kristal':True,'projection_queue_size':574,
                    'generated_articles':0,'public_release_authorized':False,
                    'jobs':[{'unesco_id':f'concept{i}','locale':locale} for i in range(1,42) for locale in m.LOCALES]}
        self.xm={'profile':'encyklopedia.unesco-enwiki-text-evidence/1.0','private':True,
                 'public_upload_authorized':False,'source_inventory_sha256':'',
                 'pages':[{'page_id':pid,'title':title,'revision_id':'9',
                           'relative_path':f'page-{pid}.wikitext.txt',
                           'sha256':digest(self.xml/f'page-{pid}.wikitext.txt'),
                           'inventory_title_agrees':True,'inventory_revision_agrees':True}
                          for pid,title in [(42,'Example'),(43,'Pointer')]]}
        self.dossier={'profile':'skope.unesco-mt1-10-local-source-dossier/1.0',
                      'branch':'unesco-mt1-10','private':True,'not_canonical':True,
                      'public_upload_authorized':False,'entries':self.entries}
        self.flush()
    def flush(self):
        dump(self.work/'RAPPORT_AUTO.json',self.report)
        dump(self.work/'inventory.json',self.inventory)
        dump(self.work/'projection_queue_14_langues.json',self.queue)
        self.xm['source_inventory_sha256']=digest(self.work/'inventory.json')
        dump(self.xml/'manifest.json',self.xm)
        self.dossier['inventory_sha256']=digest(self.work/'inventory.json')
        self.dossier['xml_manifest_sha256']=digest(self.xml/'manifest.json')
        dump(self.work/'skope_dossier.json',self.dossier)
    def test_full_stage_and_redirect_quarantine(self):
        out=self.work/'semantic_stage_v4'
        x=m.write_stage(self.work,out)
        self.assertEqual(x['concept_count'],41)
        self.assertEqual(x['candidate_qids'],36)
        self.assertEqual(x['wikipedia_substantive_contexts'],1)
        self.assertEqual(x['wikipedia_redirect_pages'],1)
        self.assertEqual(x['skos_observed_edge_count'],2)
        self.assertEqual(x['cross_branch_link_count'],1)
        self.assertEqual(x['projection_slots'],574)
        self.assertFalse(x['public_release_authorized'])
        c=m.load(out/'cards'/'concept11.json')
        self.assertEqual(c['wikipedia_en'][0]['source_status'],'REDIRECT_NOT_ARTICLE')
        self.assertFalse(c['wikipedia_en'][0]['candidate_context_usable'])
        self.assertIsNone(c['wikipedia_en'][0]['local_private_path'])
        self.assertEqual(len(list((out/'cards').glob('concept*.json'))),41)
        self.assertEqual(len(list((out/'ai_tasks').glob('concept*.json'))),41)
        self.assertIsNone(m.load(out/'cards'/'concept10.json')['canonical_KQ'])
        self.assertTrue(m.write_stage(self.work,out)['reused'])
    def test_reject_modified_stage_on_resume(self):
        out=self.work/'semantic_stage_v4';m.write_stage(self.work,out)
        (out/'cards'/'concept10.json').write_text('{}',encoding='utf8')
        with self.assertRaises(m.StageError):m.write_stage(self.work,out)
    def test_reject_tampered_wikipedia(self):
        (self.xml/'page-42.wikitext.txt').write_bytes(b'different')
        with self.assertRaisesRegex(m.StageError,'SHA-256'):m.build(self.work)
    def test_reject_cross_snapshot_dossier(self):
        self.dossier['inventory_sha256']='0'*64;dump(self.work/'skope_dossier.json',self.dossier)
        with self.assertRaisesRegex(m.StageError,'bound'):m.build(self.work)
    def test_reject_public_claim(self):
        self.report['public_release_authorized']=True;self.flush()
        with self.assertRaisesRegex(m.StageError,'unsafe|Unsafe'):m.build(self.work)
    def test_reject_canonical_crosswalk_claim(self):
        self.records[0]['wikidata']['canonical_exact_match']=True;self.flush()
        with self.assertRaisesRegex(m.StageError,'exactMatch'):m.build(self.work)
    def test_reject_queue_replacement(self):
        self.queue['jobs']=self.queue['jobs'][:-1];self.flush()
        with self.assertRaises(m.StageError):m.build(self.work)
    def test_output_must_not_be_git_or_outside_work(self):
        with self.assertRaises(m.StageError):m.write_stage(self.work,self.work.parent/'bad')
        (self.work/'.git').mkdir()
        with self.assertRaisesRegex(m.StageError,'Git'):m.write_stage(self.work,self.work/'stage')

if __name__=='__main__':unittest.main()
