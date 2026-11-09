"""V17 full-path regression using synthetic statuses and the genuine Workbench.
Never reads D: and never writes to git/production directories.
"""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO.parents[1]
sys.path.insert(0,str(REPO/'tools/unesco_pilot'))
from final_product_pipeline_v17 import execute,PipelineError,verify_output
WB=ROOT/'EncyKlopedia/UNESCO_Workbench/candidates/educational-policy-en-v11/unesco-mt1-10'

def outcsv(path,header,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=header);w.writeheader();w.writerows(rows)

def prepare_fake(work):
    data=json.loads((WB/'derived/v11/identity-review.en.json').read_text(encoding='utf8'))['concepts']
    nodes=[{'unesco_id':x['unesco_id'],'label_en':x['english_label'],
        'qid_candidate_unapproved':x.get('wikidata_qid_candidate') or ''} for x in data]
    ids=[n['unesco_id'] for n in nodes]
    graph={'branch':'unesco-mt1-10','canonical_graph_built':False,'claims_approved_as_KA':0,
      'nodes':nodes,'candidate_statements':[
        {'proposal_ref':f'P{i+1}','unesco_id':ids[i%41],'editorial_selected_en':f'Synthetic editorial text {i+1}',
         'evidence_status':'NOT_ATTESTED'} for i in range(85)],
      'skos_internal_observations':[
        {'source':ids[i%41],'target':ids[(i+1)%41],'relation':'related','ref':f'R{i}'} for i in range(61)]}
    stage14=work/'semantic_stage_v14_editorial';stage14.mkdir()
    raw=(json.dumps(graph,ensure_ascii=False)+'\n').encode()
    (stage14/'KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json').write_bytes(raw)
    report={'branch':'unesco-mt1-10','editorial_claims_selected':85,
       'private_english_concept_previews':41,'canonical_kristal_built':False}
    (stage14/'RAPPORT_EDITIONS_V14.json').write_text(json.dumps(report))
    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in stage14.iterdir()}
    (stage14/'MANIFESTE_EDITORIAL_V14.json').write_text(json.dumps({'files_sha256':files}))
    stage15=work/'semantic_stage_v15_workspace';stage15.mkdir()
    (stage15/'RAPPORT_V15.json').write_text(json.dumps({'branch':'unesco-mt1-10',
        'kit_standard_check_passed':True,'canonical_KQ_KP_KA_KS_created':0}))
    (stage15/'MANIFESTE_V15.json').write_text(json.dumps({'input_sha256':{
        'semantic_stage_v14_editorial/'+name:hashlib.sha256((stage14/name).read_bytes()).hexdigest()
        for name in ('RAPPORT_EDITIONS_V14.json','KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json','MANIFESTE_EDITORIAL_V14.json')
    }}))
    stage11=work/'semantic_stage_v11_global';stage11.mkdir()
    (stage11/'MANIFESTE_PASSE_GLOBALE.json').write_text('{}')
    for name,count in [('DECISIONS_41_IDENTITES_EDITABLE.csv',41),('DECISIONS_85_PROPOSITIONS_EDITABLE.csv',85),
        ('DECISIONS_61_RELATIONS_EDITABLE.csv',61),('DECISIONS_4_SOURCES_CONCEPT10_EDITABLE.csv',4)]:
        outcsv(stage11/name,['ref','decision'],[{'ref':str(i),'decision':'PENDING'} for i in range(count)])
    outcsv(stage11/'FILE_81_SOURCES_A_ATTESTER.csv',['reference_id','source_status'],
       [{'reference_id':f'S{i}','source_status':'NOT_ATTESTED'} for i in range(81)])
    outcsv(stage11/'PROJECTIONS_574_NON_GENEREES.csv',
       ['unesco_id','locale','article_generated','publication_authorized'],
       [{'unesco_id':id,'locale':lang,'article_generated':'NO','publication_authorized':'NO'}
        for id in ids for lang in ('en','fr','es','de','nl','sv','da','no','nn','fi','et','af','it','pt')])

@unittest.skipUnless(WB.is_dir(),'Workbench non fourni')
class TestIntegratedPipeline(unittest.TestCase):
 def test_one_pass_resume_and_fail_closed(self):
    with tempfile.TemporaryDirectory() as td:
      work=Path(td);prepare_fake(work)
      one=execute(work,ROOT,WB)
      self.assertEqual(one['operation'],'NOUVEAU_PRODUIT_PRIVE')
      path=Path(one['output'])
      self.assertEqual(len(list((path/'reader_en').glob('concept*.html'))),41)
      self.assertTrue((path/'workbench_v11_candidat_prive/.kristal/v11/authoring.json').is_file())
      self.assertEqual(execute(work,ROOT,WB)['operation'],'DEJA_PRESENT_INTACT')
      self.assertFalse(json.loads((path/'GATES_PRODUIT_FINAL_V17.json').read_text())['final_product_publishable'])
      with self.assertRaises(PipelineError):execute(work,ROOT,WB,require_final=True)
      (path/'reader_en/concept10.html').write_text('tampered')
      with self.assertRaises(PipelineError):execute(work,ROOT,WB,check_only=True)
 def test_reject_fake_human_approval(self):
    with tempfile.TemporaryDirectory() as td:
      work=Path(td);prepare_fake(work)
      target=work/'semantic_stage_v11_global/DECISIONS_41_IDENTITES_EDITABLE.csv'
      target.write_text(target.read_text().replace('PENDING','APPROVE',1))
      with self.assertRaises(PipelineError):execute(work,ROOT,WB)
 def test_v15_pinned_source_blocks_rehashing_v14(self):
    with tempfile.TemporaryDirectory() as td:
      work=Path(td);prepare_fake(work)
      graph=work/'semantic_stage_v14_editorial/KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json'
      obj=json.loads(graph.read_text());obj['candidate_statements'][0]['editorial_selected_en']='Untrusted edit'
      graph.write_text(json.dumps(obj))
      m=work/'semantic_stage_v14_editorial/MANIFESTE_EDITORIAL_V14.json'
      manifest=json.loads(m.read_text());manifest['files_sha256']['KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json']=hashlib.sha256(graph.read_bytes()).hexdigest()
      m.write_text(json.dumps(manifest))
      with self.assertRaises(PipelineError):execute(work,ROOT,WB)
 def test_require_final_fails_without_creating_product(self):
    with tempfile.TemporaryDirectory() as td:
      work=Path(td);prepare_fake(work)
      with self.assertRaises(PipelineError):execute(work,ROOT,WB,require_final=True)
      self.assertFalse((work/'semantic_stage_v17_integrated_product').exists())
if __name__=='__main__':unittest.main()
