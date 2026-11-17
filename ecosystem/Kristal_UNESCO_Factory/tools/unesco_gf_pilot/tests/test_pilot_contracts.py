import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[4] # overlay root when extracted
PILOT=Path(__file__).resolve().parents[1]
SA=Path(r'C:\mycode\SemantiK_Architect\SemantiK_Architect')
if not (SA/'src'/'semantik_architect').is_dir():
    SA=Path('/mnt/data/work_overlay/semantik') if Path('/mnt/data/work_overlay/semantik').exists() else SA
sys.path[:0]=[str(PILOT)]
import pilot

class Leaf:
    kind='claim'
    key='concept10.fr.statement'

class PilotContracts(unittest.TestCase):
    def setUp(self):
        self.concept={'unesco_id':'concept10','source_uri':'http://vocabularies.unesco.org/thesaurus/concept10',
                      'status':'source_only_not_canonical','microthesaurus_ids':['mt1.1'],
                      'preferred_labels':{'fr':['Éducation'],'en':['Education']}}
        self.micro={'id':'mt1.1','uri':'http://example.org/mt1.1','label_fr':'Sciences', 'label_en':'Science'}

    def test_gf_path_from_wordbench(self):
        self.assertIn('Grammatical-Framework',str(pilot.DEFAULT_GF))
        self.assertEqual(str(pilot.DEFAULT_GF).replace('\\','/').split('/')[-1],'gf.exe')
        self.assertEqual(str(pilot.DEFAULT_WORDBENCH).replace('\\','/').split('/')[-1],'GF_Wordbench')

    def test_request_with_real_semantik_validator(self):
        import importlib
        if str(SA/'src') not in sys.path:sys.path.insert(0,str(SA/'src'))
        Request=importlib.import_module('semantik_architect.domain.communication.request').CommunicationRequest
        Validator=importlib.import_module('semantik_architect.application.validation.request_validation').RequestValidator
        for lang in ('fr','en'):
            for kind,part in (('claim','statement'),('scope','scope')):
                leaf=Leaf();leaf.kind=kind;leaf.key=f'concept10.{lang}.{part}'
                req=pilot.make_request(self.concept,self.micro,lang,leaf)
                Validator().validate(Request.from_dict(req))
                self.assertEqual(req['context']['target_language'],lang)
                self.assertEqual(req['semantic_graph']['statements'][0]['source_refs'][0],self.concept['source_uri'])

    def test_candidate_plans_without_claiming_real_gf(self):
        if str(SA/'src') not in sys.path:sys.path.insert(0,str(SA/'src'))
        from semantik_architect.conformance.candidate import CandidateConformance
        with tempfile.TemporaryDirectory() as temp:
            leaf=Leaf();req=pilot.make_request(self.concept,self.micro,'fr',leaf)
            cand=pilot.create_candidate(Path(temp),'fr',{leaf.key:req})
            # Only plan tests. The dummy cannot produce actual GF output.
            (cand/'grammar.pgf').write_bytes(b'UNCOMPILABLE_TEST_ONLY')
            pilot.create_lock(cand,'fr')
            app=CandidateConformance(cand,'unesco-pilot-fr-1')
            plan=app.plan(req)
            self.assertEqual(plan.units[0].operation_id,'clause.transitive_event')
            self.assertEqual(len(plan.units),1)

    def test_fails_without_gf_but_writes_archive(self):
        if str(SA/'src') not in sys.path:sys.path.insert(0,str(SA/'src'))
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);run=root/'RUN-test'; factory=Path(__file__).resolve().parents[3]
            if not (factory/'vendor/spek').is_dir():
                factory=Path('/mnt/data/work_overlay/factory')
            if not factory.is_dir(): self.skipTest('Only source test environment available')
            (run/'01_INVENTAIRE').mkdir(parents=True)
            (run/'01_INVENTAIRE'/'concepts.jsonl').write_text(json.dumps(self.concept)+'\n',encoding='utf-8')
            import csv
            with (run/'01_INVENTAIRE'/'groupes.csv').open('w',encoding='utf-8',newline='') as f:
                w=csv.DictWriter(f,fieldnames=['type','id','uri','label_fr','label_en']);w.writeheader();w.writerow({'type':'microthesaurus',**self.micro})
            if str(factory) not in sys.path:sys.path.insert(0,str(factory))
            from discourse_factory import instance_for
            for lang in ('fr','en'):
                p=run/'07_DISCOURS'/'instances'/lang/'concept10.json'
                p.parent.mkdir(parents=True)
                p.write_text(json.dumps(instance_for(self.concept,lang,False)),encoding='utf-8')
            zip_file=pilot.run_pilot(run,factory,SA,root/'out',gf_executable=str(root/'not-here.exe'))
            result=json.loads(zip_file.with_suffix('').joinpath('report.json').read_text(encoding='utf-8'))
            self.assertFalse(result['publication_authorized'])
            self.assertEqual(result['status'],'BLOCKED_OR_PARTIAL')
            self.assertTrue(zip_file.is_file())

if __name__=='__main__':unittest.main()
