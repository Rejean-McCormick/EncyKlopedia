import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS=Path(__file__).resolve().parents[1]/'tools'/'unesco_pilot'
sys.path.insert(0,str(TOOLS))
import cumulative_preflight as p
from repo_preflight import RELATIVE_REPOS


class TestCumulative(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.payload=self.root/'one-file.txt'
        self.payload.write_text('local additive test',encoding='utf8')
        manifest={'format':'koa.unesco-mt1-10-cumulative-integrity/1.0',
                  'branch':'unesco-mt1-10','lots':[1,2,3],
                  'repositories_expected':13,
                  'file_sha256':{'one-file.txt':hashlib.sha256(self.payload.read_bytes()).hexdigest()}}
        (self.root/p.MANIFEST).write_text(json.dumps(manifest),encoding='utf8')
        # Real package coordination files are copied byte-for-byte from the
        # overlay test checkout; no real GitHub repo or local D: data involved.
        stage=Path(__file__).resolve().parents[1]
        from repo_preflight import LOCALES
        for repo,rel in RELATIVE_REPOS.items():
            x=self.root/rel/'integrations'/'unesco-mt1-10'/'lot3-status.json'
            x.parent.mkdir(parents=True,exist_ok=True)
            status={'format':p.STATUS,'repo':repo,'local_relative_path':rel,
                    'branch':'unesco-mt1-10','unesco_seed_concepts':41,
                    'target_locales':list(LOCALES),'status':'LOCAL_PRIVATE_RESEARCH_AND_PROJECTIONS_ONLY',
                    'semantic_grain':{'one_branch_kristal':True,'articles_are_projections':True,
                                      'one_kristal_per_locale':False,'one_kristal_per_concept':False}}
            for flag in ('automatic_exact_match','automatic_canonical_minting','ai_training_as_source_KS',
                         'wikipedia_content_license_cleared','verified_14_language_runtimes',
                         'github_publication_enabled','independent_release_approval_verified'):
                status[flag]=False
            x.write_text(json.dumps(status),encoding='utf8')

    def test_manifest_and_statuses_pass_but_not_publication(self):
        r=p.check(self.root)
        self.assertTrue(r['installation_contracts_valid'],r['problems'])
        self.assertEqual(r['repositories_status_valid'],13)
        self.assertFalse(r['public_release_authorized'])
        self.assertFalse(r['canonical_assertions_qualified_by_preflight'])

    def test_modified_package_file_fails(self):
        self.payload.write_text('change',encoding='utf8')
        r=p.check(self.root)
        self.assertFalse(r['installation_contracts_valid'])
        self.assertTrue(any('SHA mismatch' in x for x in r['problems']))

    def test_public_upload_enabled_in_one_repo_fails(self):
        x=self.root/RELATIVE_REPOS['Spek']/'integrations'/'unesco-mt1-10'/'lot3-status.json'
        d=json.loads(x.read_text('utf8'));d['github_publication_enabled']=True
        x.write_text(json.dumps(d),encoding='utf8')
        self.assertFalse(p.check(self.root)['installation_contracts_valid'])

if __name__=='__main__':unittest.main()
