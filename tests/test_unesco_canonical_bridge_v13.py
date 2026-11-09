import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'tools'/'unesco_pilot'/'canonical_bridge_v13.py'
sys.path.insert(0,str(SCRIPT.parent))
spec=importlib.util.spec_from_file_location('unesco_canonical_bridge_v13',SCRIPT)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class BridgeTests(unittest.TestCase):
 def test_source_missing_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(mod.BridgeError):mod.build(Path(d),Path(d))
 def test_deterministic_hash(self):
  self.assertEqual(mod.sha(b'test'),'9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08')
 def test_no_write_on_check_only(self):
  with tempfile.TemporaryDirectory() as d:
   dest=Path(d)/'new'
   op,n=mod.publish_new_files(dest,{'RAPPORT.json':b'{}'},check_only=True)
   self.assertEqual(op,'VERIFICATION_SANS_ECRITURE')
   self.assertFalse(dest.exists())
 def test_output_changed_refused(self):
  with tempfile.TemporaryDirectory() as d:
   dest=Path(d)
   (dest/'RAPPORT.json').write_bytes(b'wrong')
   with self.assertRaises(mod.ReviewError):mod.publish_new_files(dest,{'RAPPORT.json':b'expected'},check_only=False)

if __name__=='__main__':unittest.main()
