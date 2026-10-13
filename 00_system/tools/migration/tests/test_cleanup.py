import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'cleanup.py'
spec=importlib.util.spec_from_file_location('enc_cleanup',p);cl=importlib.util.module_from_spec(spec);spec.loader.exec_module(cl)
class CleanupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'repo';self.root.mkdir()
        self.manifest=self.root/'manifest.json';self.file=self.root/'legacy.txt';self.file.write_text('old')
        self.sha=hashlib.sha256(b'old').hexdigest()
        self.manifest.write_text(json.dumps({'format':cl.FORMAT,'files':[{'path':'legacy.txt','sha256':self.sha,'reason':'test'}]}))
    def test_safe_deletion(self):
        self.assertEqual(cl.candidates(self.root,self.manifest)[0]['status'],'eligible')
        self.assertEqual(cl.delete_selected(self.root,self.manifest,['legacy.txt']),['legacy.txt'])
        self.assertFalse(self.file.exists())
    def test_changed_file_is_never_removed(self):
        self.file.write_text('new')
        self.assertEqual(cl.candidates(self.root,self.manifest)[0]['status'],'modified_keep')
        with self.assertRaises(ValueError):cl.delete_selected(self.root,self.manifest,['legacy.txt'])
        self.assertTrue(self.file.exists())
    def test_escape_rejected(self):
        for path in ['../outside','/tmp/elsewhere','C:/windows/win.ini','../a','a\\..\\b']:
            self.manifest.write_text(json.dumps({'format':cl.FORMAT,'files':[{'path':path,'sha256':self.sha}]}))
            with self.assertRaises(ValueError):cl.candidates(self.root,self.manifest)
    def test_symlink_rejected(self):
        link=self.root/'other';link.symlink_to(self.file)
        self.manifest.write_text(json.dumps({'format':cl.FORMAT,'files':[{'path':'other','sha256':self.sha}]}))
        self.assertEqual(cl.candidates(self.root,self.manifest)[0]['status'],'blocked_symlink')
if __name__=='__main__':unittest.main()
