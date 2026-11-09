import importlib.util
from pathlib import Path
import json
import sys
import tempfile
import unittest

TOOLS=Path(__file__).resolve().parents[1]/'tools/unesco_pilot'
sys.path.insert(0,str(TOOLS))
spec=importlib.util.spec_from_file_location('unesco_workspace_readiness_v15',TOOLS/'workspace_readiness_v15.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

class V15BasicSafetyTests(unittest.TestCase):
    def test_source_file_limits(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(mod.Stage15Error):mod.read_json(Path(d)/'absent')
    def test_bad_output_name_refused_before_writing(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(mod.Stage15Error):mod.run_pipeline(Path(d),Path(d),output_name='../canon')
    def test_git_folder_is_never_private_work(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'.git').mkdir()
            with self.assertRaises(mod.Stage15Error):mod.ensure_work(p)
    def test_no_symlink_private_work(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);x=p/'link'
            try:x.symlink_to(p,target_is_directory=True)
            except OSError:self.skipTest('symlink forbidden on this system')
            with self.assertRaises(mod.Stage15Error):mod.ensure_work(x)
    def test_reader_rejects_malformed_csv(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'file.csv';p.write_text('a,b\n1\n',encoding='utf8')
            with self.assertRaises(mod.Stage15Error):mod.read_csv(p)

if __name__=='__main__':unittest.main()
