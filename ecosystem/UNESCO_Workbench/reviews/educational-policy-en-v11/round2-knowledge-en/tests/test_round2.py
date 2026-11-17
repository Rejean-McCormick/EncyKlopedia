import csv
import tempfile
import unittest
from pathlib import Path
import importlib.util

P = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ep_gate', P/'validate_round2.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class Round2Tests(unittest.TestCase):
    def test_unchanged_research_package(self):
        issues, summary = gate.validate()
        self.assertEqual(issues, [])
        self.assertEqual(summary['claim_proposals'], 19)
    def test_reject_identity_approval_in_pack(self):
        with tempfile.TemporaryDirectory() as d:
            t=Path(d)
            for n in ['41_identity_recommendations_en.csv','source_register_en.json','19_ka_ks_research_proposals_en.jsonl','right-to-education.en.md']:
                (t/n).write_bytes((P/n).read_bytes())
            p=t/'41_identity_recommendations_en.csv'
            with p.open(encoding='utf-8-sig', newline='') as f: rows=list(csv.DictReader(f));fields=list(rows[0])
            rows[0]['editorial_decision']='approve_exact'
            with p.open('w',encoding='utf-8-sig',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
            errs,_=gate.validate(t)
            self.assertTrue(any('approval found' in e for e in errs))
    def test_missing_source_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            t=Path(d)
            for n in ['41_identity_recommendations_en.csv','source_register_en.json','19_ka_ks_research_proposals_en.jsonl','right-to-education.en.md']:
                (t/n).write_bytes((P/n).read_bytes())
            p=t/'source_register_en.json'
            import json
            obj=json.loads(p.read_text(encoding='utf-8'));obj['sources'].pop();p.write_text(json.dumps(obj),encoding='utf-8')
            errs,_=gate.validate(t)
            self.assertTrue(any('expected 6' in e for e in errs))
if __name__=='__main__':unittest.main()
