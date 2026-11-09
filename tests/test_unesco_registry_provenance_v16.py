import importlib.util
from pathlib import Path
import tempfile
import json
import sys
import unittest

TOOLS=Path(__file__).resolve().parents[1]/'tools/unesco_pilot'
sys.path.insert(0,str(TOOLS))
spec=importlib.util.spec_from_file_location('rv16',TOOLS/'registry_provenance_v16.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class OrchestratorSafetyTests(unittest.TestCase):
    def test_new_output_name_restricted(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(m.V16Error):m.run(Path(d),Path(d),output_name='../canon')
    def test_no_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(m.V16Error):m.integrity(Path(d),'MANIFESTE_V15.json','files_sha256')
    def test_traversal_manifest_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'MANIFESTE_V15.json').write_bytes(m.jb({'files_sha256':{'../foo':'f'}}))
            with self.assertRaises(m.V16Error):m.integrity(p,'MANIFESTE_V15.json','files_sha256')
    def test_corrupt_output_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'x.txt').write_text('bad');(p/'MANIFESTE_V15.json').write_bytes(m.jb({'files_sha256':{'x.txt':'0'*64}}))
            with self.assertRaises(m.V16Error):m.integrity(p,'MANIFESTE_V15.json','files_sha256')
    def test_prior_inputs_are_pinned(self):
        with tempfile.TemporaryDirectory() as d:
            w=Path(d)/'w';r=Path(d)/'r';w.mkdir();r.mkdir()
            (w/'x.txt').write_bytes(b'OK')
            m.verify_v15_input_contract({'input_sha256':{'x.txt':m.sha(b'OK')}},w,r)
            (w/'x.txt').write_bytes(b'changed')
            with self.assertRaises(m.V16Error):m.verify_v15_input_contract({'input_sha256':{'x.txt':m.sha(b'OK')}},w,r)
    def test_prior_inputs_no_traversal(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(m.V16Error):m.verify_v15_input_contract({'input_sha256':{'../other':'0'*64}},Path(d),Path(d))
    def test_untracked_file_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'x.txt').write_text('good');(p/'extra.txt').write_text('unexpected')
            (p/'MANIFESTE_V15.json').write_bytes(m.jb({'files_sha256':{'x.txt':m.sha(b'good')}}))
            with self.assertRaises(m.V16Error):m.integrity(p,'MANIFESTE_V15.json','files_sha256')

if __name__=='__main__':unittest.main()
