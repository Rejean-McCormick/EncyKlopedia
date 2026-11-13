from contextlib import closing
"""V31: tests d'inventaire exhaustif, multibranche, reprise, station native et stats."""
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
ROOTTOOLS=ROOT/'tools'/'unesco_pilot'
sys.path.insert(0,str(ROOTTOOLS))
import qualification_globale_v31 as q
import priorisation_native_v31 as prior

SPEC=importlib.util.spec_from_file_location('station30v31',ROOTTOOLS/'poste_chatgpt_v30.py')
s=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(s)

class GlobalClassificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        d=Path(self.tmp.name);self.d=d
        self.src=d/'source.sqlite';self.cache=d/'cache.sqlite';self.branches=d/'branches'
        self.branches.mkdir()
        con=sqlite3.connect(self.src)
        con.executescript('''CREATE TABLE wiki_pages(page_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT,redirect INTEGER,latest_revision INTEGER);
          CREATE TABLE wiki_categorylinks(source_page_id INTEGER,category TEXT,type TEXT);
          CREATE INDEX idx_wiki_cat_from ON wiki_categorylinks(source_page_id);
          CREATE TABLE wiki_pagelinks(source_page_id INTEGER,target_id INTEGER);
          CREATE INDEX idx_wiki_pagelinks_from ON wiki_pagelinks(source_page_id);
          CREATE TABLE wiki_linktargets(target_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT);
          CREATE TABLE wiki_qid(page_id INTEGER PRIMARY KEY,qid TEXT);''')
        con.executemany('INSERT INTO wiki_pages VALUES(?,?,?,?,?)',[(1,0,'University_of_Example',0,100),
              (2,0,'Example_City',0,200),(3,0,'Teaching_method',0,300),
              (4,0,'Redirect',1,400),(5,14,'Non_article',0,500),(6,0,'Unknown',0,600)])
        con.executemany('INSERT INTO wiki_categorylinks VALUES(?,?,?)',[(1,'Educational_institutions','page'),
              (2,'Cities_in_France','page'),(3,'Teaching_methods','page')])
        con.executemany('INSERT INTO wiki_linktargets VALUES(?,?,?)',[(501,0,'Teaching_methods'),(502,0,'Example_City')])
        con.executemany('INSERT INTO wiki_pagelinks VALUES(?,?)',[(1,501),(2,502)])
        con.execute("INSERT INTO wiki_qid VALUES(1,'Q123')")
        con.commit();con.close()
        self.new_branch('education','educational','University education','Teaching methods')
        self.new_branch('geography','geography','Geography','Cities')

    def new_branch(self,name,title,*labels):
        (self.branches/f'concepts_{name}.json').write_text(json.dumps({'concepts':[
            {'unesco_id':f'{name}_{i}', 'preferred_labels':{'en':[lab]}} for i,lab in enumerate(labels)]}),encoding='utf-8')
        (self.branches/f'branche_{name}.json').write_text(json.dumps({
          'schema':'encyklopedia.branch-manifest.v25/1','branch_id':name,'title_fr':title,
          'vocabulary':'unesco','concepts_file':f'concepts_{name}.json'}),encoding='utf-8')

    def test_every_main_namespace_page_preserved_and_resume_multibranch(self):
        first=q.execute(self.src,self.cache,self.branches,batch_size=2,max_articles=2,categories_limit=5)
        self.assertEqual(first['totals']['profiles'],2)
        second=q.execute(self.src,self.cache,self.branches,batch_size=2,max_articles=50,categories_limit=5)
        self.assertEqual(second['totals']['profiles'],5) # ns14 ignored, redirects still kept
        self.assertTrue(second['source_exhausted'])
        third=q.execute(self.src,self.cache,self.branches,batch_size=2,max_articles=50,categories_limit=5)
        self.assertEqual(third['totals']['profiles'],5)
        with closing(sqlite3.connect(self.cache)) as con, con:
            self.assertEqual(con.execute('SELECT redirect FROM article_profiles WHERE page_id=4').fetchone()[0],1)
            self.assertEqual(con.execute('SELECT branch_candidates FROM article_profiles WHERE page_id=6').fetchone()[0],0)
            self.assertEqual(con.execute('SELECT qid,liens_vus FROM article_profiles WHERE page_id=1').fetchone(),('Q123',1))
            self.assertGreater(con.execute('SELECT COUNT(*) FROM branch_suggestions').fetchone()[0],0)
            self.assertIn('education',[r[0] for r in con.execute('SELECT DISTINCT branch_id FROM branch_suggestions')])
        self.assertEqual(first['source'],str(self.src))

    def test_read_only_source_and_manifest_drift(self):
        before=self.src.read_bytes();q.execute(self.src,self.cache,self.branches,batch_size=10,max_articles=10)
        self.assertEqual(before,self.src.read_bytes())
        self.new_branch('new','new','Novel subject')
        result=q.execute(self.src,self.cache,self.branches,batch_size=10,max_articles=10)
        self.assertEqual(result['batch']['reclassified_profiles'],5)
        self.assertEqual(result['totals']['branch_count'],3)
        self.assertEqual(before,self.src.read_bytes())

    def test_selector_preserves_all_unselected(self):
        rows=[{'candidate_id':str(i),'priority':200-i} for i in range(1000)]
        out=prior.select(rows,300)
        self.assertEqual(len(out),300)
        self.assertEqual(len(set(r['candidate_id'] for r in out)),300)
        self.assertEqual([r['candidate_id'] for r in out[:225]],[str(i) for i in range(225)])
        self.assertTrue(any(int(r['candidate_id'])>500 for r in out[225:]))
        self.assertTrue(prior.score({'title':'Educational_policy','links':2,'seed_count':2},'Educational policy')>
                        prior.score({'title':'City','shared':1},'Educational policy'))

class NativeStationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        d=Path(self.tmp.name);self.d=d
        self.repo=d/'repo';self.repo.mkdir()
        self.work=d/'poste_chatgpt_v30';self.v28=d/'v28';self.v27=d/'v27';self.v28.mkdir();(self.v27/'packs').mkdir(parents=True)
        self.cat=d/'cat.sqlite';self.stage=self.v28/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        with closing(sqlite3.connect(self.cat)) as c, c:
            c.executescript('''CREATE TABLE articles(wiki TEXT,page_id INTEGER);
               CREATE TABLE assignments(branch_id TEXT,wiki TEXT,page_id INTEGER,concept_id TEXT);
               CREATE TABLE reviewed_article_links_v28(branch_id TEXT,concept_id TEXT,page_id INTEGER);''')
        self.station=s.Station(self.repo,self.work,self.v27,self.v28,self.cat)
        self.branch={'id':'unesco.mt1.10.test','signature':'sig','concepts':[{'unesco_id':'concept1'}]}
        def candidate_id(bid,cid,pid):return f'candidate_{pid}'
        def build_candidate(db,row,label):
            pid=int(row['page_id'])
            return {'candidate_id':candidate_id(None,None,pid),'branch_id':row['branch_id'],'concept_id':row['concept_id'],
              'concept_en':label,'page_id':pid,'title':row['title'],'priority':37,'seed_count':1,'links':1,
              'shared':0,'subs':0,'evidence_sha256':f'{pid:064x}','examples':'seed->article'}
        v25=SimpleNamespace(DEFAULT_BRANCH=Path('unused.json'),load_branch=lambda _:self.branch,
            label=lambda _c,lang:'Educational policy',meta=lambda db,key:db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone()[0])
        engine=SimpleNamespace(FORMAT='TEST_SCHEMA_V28',v25=v25,candidate_id=candidate_id,build_candidate=build_candidate)
        self.station._v28_engine=lambda:engine
        with closing(sqlite3.connect(self.stage)) as c, c:
            c.executescript('''CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);
             CREATE TABLE candidates(branch_id TEXT,concept_id TEXT,page_id INTEGER,title TEXT);
             CREATE TABLE evidence(branch_id TEXT,concept_id TEXT,page_id INTEGER,seed_page_id INTEGER,kind TEXT);
             ''')
            c.executemany('INSERT INTO meta VALUES(?,?)',[('schema',engine.FORMAT),('branch_signature','sig'),('catalogue_sequence','47')])
            c.executemany('INSERT INTO candidates VALUES(?,?,?,?)',
                ((self.branch['id'],'concept1',i,f'Example school {i}') for i in range(1,1801)))
            c.executemany('INSERT INTO evidence VALUES(?,?,?,?,?)',
                ((self.branch['id'],'concept1',i,9001,'WIKILINK') for i in range(1,1801)))

    def tearDown(self):self.station.db.close()

    def test_880_candidate_native_packs_and_no_duplicate_ids(self):
        self.assertEqual(self.station._refresh_review_index(),1800)
        n=self.station._prepare_v28()
        self.assertEqual(n,3)
        jobs=list(self.station.db.execute('SELECT * FROM jobs ORDER BY created_utc,id'))
        self.assertEqual(sum(j['count'] for j in jobs),1800)
        self.assertEqual(sorted(j['count'] for j in jobs),[40,880,880])
        self.assertEqual(self.station.db.execute("SELECT COUNT(*) FROM review_index WHERE state='PENDING'").fetchone()[0],0)
        for job in jobs:
            with zipfile.ZipFile(job['bundle_path']) as z:
                raw=z.read('REVUE_'+job['id']+'.csv')
                rows=s.read_baseline(raw)
                self.assertEqual(len(rows),job['count'])
                self.assertEqual({r['evidence_sha256'] for r in rows}.__len__(),len(rows))
        # Index refresh cannot requeue already-dispatched candidates.
        self.assertEqual(self.station._refresh_review_index(),0)
        self.assertEqual(self.station._prepare_v28(),0)

if __name__=='__main__':unittest.main(verbosity=2)
