"""V31.2 - Mode volume, protection des tâches historiques et intégrité."""
from pathlib import Path
import ast
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
SRC=(ROOT/'tools/unesco_pilot/poste_chatgpt_v30.py').read_text(encoding='utf-8')
class VolumeConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree=ast.parse(SRC)
        cls.values={}
        for node in tree.body:
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
                if node.targets[0].id in {'REVIEW_SIZE','MIN_REVIEW_SIZE','MAX_REVIEW_SIZE','REVIEW_BUDGET','QUEUE_BUFFER'}:
                    cls.values[node.targets[0].id]=ast.literal_eval(node.value)
    def test_unesco_880_and_budget(self):
        self.assertEqual(self.values['REVIEW_SIZE'],880)
        self.assertEqual(self.values['MAX_REVIEW_SIZE'],880)
        self.assertEqual(self.values['MIN_REVIEW_SIZE'],650)
        self.assertGreaterEqual(self.values['REVIEW_BUDGET'],3000)
    def test_production_kristal_parameters(self):
        for item in ["'-MaxArticles','24'","'-TargetWords','80000'","'-TargetBytes','12582912'"]:
            self.assertIn(item,SRC)
    def test_identifiers_and_existing_jobs_remain(self):
        self.assertIn("state='PENDING'",SRC)
        self.assertIn("state='QUEUED'",SRC)
        self.assertIn("if queued>=QUEUE_BUFFER:return 0",SRC)
        self.assertIn("if queued>=s.QUEUE_BUFFER:return 0",(ROOT/'tools/unesco_pilot/routage_branches_v311.py').read_text(encoding='utf-8'))
    def test_retains_decision_fields(self):
        self.assertIn("FIELDS=['candidate_id'",SRC)
        self.assertIn("set(hdr)=={'candidate_id','decision','justification'}",SRC)
if __name__=='__main__':unittest.main()
