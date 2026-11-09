import pathlib,sys,tempfile,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'tools/unesco_pilot'))
from lot2_preflight import preflight,NEW_TOOLS
class TestLot2(unittest.TestCase):
 def test_missing_repos_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   data=preflight(pathlib.Path(d),runtime_root=pathlib.Path(d))
   self.assertFalse(data['lot1_contracts_valid'])
   self.assertFalse(data['lot2_tools_present'])
   self.assertEqual(data['repositories_expected'],13)
   self.assertFalse(data['publication_authorized'])
 def test_required_tools_are_exactly_expected(self):
  self.assertEqual(len(NEW_TOOLS),8)
if __name__=='__main__':unittest.main()
