import importlib.util,sys
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]/'tools/unesco_pilot'
sys.path.insert(0,str(ROOT))
s=importlib.util.spec_from_file_location('editorial_advance_v14',ROOT/'editorial_advance_v14.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Tests(unittest.TestCase):
 def test_private_output_name(self):self.assertEqual(m.OUT,'semantic_stage_v14_editorial')
 def test_hash_is_sha256(self):self.assertEqual(len(m.sha(b'hello')),64)
 def test_absent_repo_file_rejected(self):
  with self.assertRaises(m.AdvanceError):m.loader(Path('/tmp/absent-unesco-v14.py'),'absent')
if __name__=='__main__':unittest.main()
