"""13-repo offline preflight positive/negative tests."""
from __future__ import annotations
import importlib.util,json,tempfile,unittest
from pathlib import Path
PILOT=Path(__file__).resolve().parents[1]/'tools/unesco_pilot/repo_preflight.py'
s=importlib.util.spec_from_file_location('repo_preflight',PILOT)
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)

class Tests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);self.root=Path(d.name)
        # Keep this test portable in an isolated EncyKlopedia checkout.
        # A separate live --root preflight verifies the 13 real peer folders.
        src=Path(__file__).resolve().parents[1]/'integrations'/'unesco-mt1-10'/'handoff.json'
        template=json.loads(src.read_text(encoding='utf8'))
        for name in r.RELATIVE_REPOS:
            target=self.root/name/'integrations'/'unesco-mt1-10'/'handoff.json'
            target.parent.mkdir(parents=True,exist_ok=True)
            d=dict(template,repo=name,component_role='test_role')
            target.write_text(json.dumps(d),encoding='utf8')

    def test_thirteen_present_and_public_blocked(self):
        result=r.inspect(self.root,snapshot_layout=True)
        self.assertTrue(result['installation_contracts_valid'])
        self.assertEqual(result['repos_present'],13)
        self.assertFalse(result['ready_for_publication'])
        self.assertFalse(result['language_14_qualified'])

    def test_absent_one_repo_fails(self):
        (self.root/'Spek'/'integrations'/'unesco-mt1-10'/'handoff.json').unlink()
        result=r.inspect(self.root,snapshot_layout=True)
        self.assertFalse(result['installation_contracts_valid'])
        self.assertEqual(result['repos_present'],12)

    def test_rogue_auto_upload_flag_fails(self):
        x=self.root/'kristal-public'/'integrations'/'unesco-mt1-10'/'handoff.json'
        content=json.loads(x.read_text());content['public_upload_authorized']=True
        x.write_text(json.dumps(content))
        result=r.inspect(self.root,snapshot_layout=True)
        self.assertFalse(result['installation_contracts_valid'])
        self.assertTrue(any('unsafe' in x for x in result['problems']))

    def test_one_kristal_per_language_rejected(self):
        x=self.root/'diK'/'integrations'/'unesco-mt1-10'/'handoff.json'
        content=json.loads(x.read_text());content['semantic_grain']['one_kristal_per_language']=True
        x.write_text(json.dumps(content))
        result=r.inspect(self.root,snapshot_layout=True)
        self.assertFalse(result['installation_contracts_valid'])

if __name__=='__main__':unittest.main()
