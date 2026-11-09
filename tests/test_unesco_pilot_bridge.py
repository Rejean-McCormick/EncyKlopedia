"""Local-only synthetic tests; no production SQLite, network, or GitHub access."""
from __future__ import annotations
import hashlib,importlib.util,json,sqlite3,tempfile,unittest
from pathlib import Path
from zipfile import ZipFile

PILOT=Path(__file__).resolve().parents[1]/'tools/unesco_pilot/local_wikipedia_bridge.py'
sp=importlib.util.spec_from_file_location('pilot',PILOT)
pilot=importlib.util.module_from_spec(sp);sp.loader.exec_module(pilot)


class PilotTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name)
        self.z=self.root/'pilot.zip';self.db=self.root/'enwiki.sqlite'
        self.write_source()
        c=sqlite3.connect(self.db)
        c.execute('CREATE TABLE wiki_qid (page_id INTEGER PRIMARY KEY,qid TEXT NOT NULL)')
        c.execute('CREATE INDEX idx_wiki_qid_qid ON wiki_qid(qid)')
        c.execute('CREATE TABLE wiki_pages (page_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT,is_redirect INTEGER,latest_rev INTEGER,length INTEGER)')
        c.execute("INSERT INTO wiki_qid VALUES (13,'Q100')")
        c.execute("INSERT INTO wiki_pages VALUES (13,0,'Education_policy',0,222,20)")
        c.execute("INSERT INTO wiki_qid VALUES (14,'Q100')")
        c.execute("INSERT INTO wiki_pages VALUES (14,1,'Talk:Education_policy',0,223,20)")
        c.commit();c.close()

    def write_source(self,tamper_hash=False,invalid_status=False):
        concepts=[{'unesco_id':'concept'+str(i),'source_uri':'http://vocabularies.unesco.org/thesaurus/concept'+str(i),
                   'preferred_labels':{'en':['Concept '+str(i)],'fr':['Notion '+str(i)]},
                   'broader':[], 'narrower':[], 'related':[]} for i in range(1,42)]
        candidates=[{'unesco_id':'concept'+str(i),'qid_candidate':'Q100' if i==1 else '',
                     'status':'NO_P3916_MAPPING' if i!=1 else 'INVALID' if invalid_status else 'SINGLE_P3916_CANDIDATE'} for i in range(1,42)]
        def dumps(x):return json.dumps(x).encode()
        cb=dumps({'concepts':concepts})
        source_hash='0'*64 if tamper_hash else hashlib.sha256(cb).hexdigest()
        scope={'grain':{'one_branch_kristal':True,'no_one_kristal_per_concept':True,'individual_articles_are_projections':True},
               'subject':{'unesco_branch_slug':'unesco-mt1-10','expected_seed_count':41},'source_sha256':source_hash}
        with ZipFile(self.z,'w') as z:
            z.writestr(pilot.SCOPE_FILE,dumps(scope))
            z.writestr(pilot.CONCEPT_FILE,cb)
            z.writestr(pilot.MAPPING_FILE,dumps({'mappings':candidates}))

    def test_41_14_no_articles_no_approval(self):
        x=pilot.build_manifest(self.z,self.db)
        self.assertEqual(len(x['records']),41)
        self.assertEqual(x['target_projection_count'],574)
        self.assertTrue(x['not_canonical']);self.assertTrue(x['not_publication'])
        self.assertEqual(x['article_count'],0)
        a=x['records'][0]
        self.assertEqual(a['wikipedia_en_inventory'][0]['latest_revision_id'],222)
        self.assertEqual(len(a['wikipedia_en_inventory']),1)
        self.assertFalse(a['wikidata']['canonical_exact_match'])
        self.assertIsNone(a['canonical_KQ'])
        self.assertEqual(a['language_channels']['fr']['label_status'],'source_label_present')
        self.assertEqual(a['language_channels']['de']['label_status'],'missing')
        self.assertEqual(a['article_projection_status'],'not_generated')

    def test_no_canon_writes_or_overwrites(self):
        result=pilot.build_manifest(self.z,self.db)
        target=self.root/'private'/'inventory.json'
        pilot.atomic_json_write(target,result)
        self.assertTrue(target.exists())
        with self.assertRaisesRegex(pilot.PilotError,'exists'):
            pilot.atomic_json_write(target,result)
        self.assertFalse((self.root/'canonical.json').exists())

    def test_refuse_output_inside_git(self):
        p=self.root/'git-repo';(p/'.git').mkdir(parents=True)
        with self.assertRaisesRegex(pilot.PilotError,'Git checkout'):
            pilot.atomic_json_write(p/'candidate.json',{})

    def test_refuse_bad_sha(self):
        self.write_source(tamper_hash=True)
        with self.assertRaisesRegex(pilot.PilotError,'SHA-256'):
            pilot.read_pilot_zip(self.z)

    def test_refuse_unapproved_status_mismatch(self):
        self.write_source(invalid_status=True)
        with self.assertRaisesRegex(pilot.PilotError,'Only explicit single'):
            pilot.read_pilot_zip(self.z)

    def test_refuse_missing_sqlite(self):
        with self.assertRaisesRegex(pilot.PilotError,'not found'):
            pilot.build_manifest(self.z,self.root/'missing.sqlite')
        self.assertFalse((self.root/'missing.sqlite').exists())

    def test_refuse_unknown_schema(self):
        c=sqlite3.connect(self.db)
        c.execute('DROP TABLE wiki_qid');c.execute('CREATE TABLE wiki_qid (fake_id INTEGER)');c.commit();c.close()
        with self.assertRaisesRegex(pilot.PilotError,'column absent'):
            pilot.build_manifest(self.z,self.db)

    def test_plan_prints_no_articles_and_does_not_write(self):
        self.assertEqual(pilot.main(['plan','--scope-zip',str(self.z),'--db',str(self.db)]),0)
        self.assertEqual(sorted(x.name for x in self.root.iterdir()),['enwiki.sqlite','pilot.zip'])

if __name__=='__main__':unittest.main()
