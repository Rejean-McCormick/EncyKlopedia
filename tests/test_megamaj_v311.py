from contextlib import closing
"""Non-régression V31.1 : classification QID, multi-branches, provenance SQL."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import hashlib
import importlib.util
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile
import types

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'tools'/'unesco_pilot'
sys.path.insert(0,str(TOOLS))
import qualification_globale_v31 as qualify
import routage_branches_v311 as route
import poste_chatgpt_v30 as station
# L'export de sources V31 ne contenait pas le pont V26; les tests ciblés
# ne sollicitent pas son implémentation et l'installation native le fournit.
try:
    import integrer_ponts_revus_v26
except ModuleNotFoundError:
    sys.modules['integrer_ponts_revus_v26']=types.ModuleType('integrer_ponts_revus_v26')
import decouverte_relationnelle_v311 as sql_discovery
import decouvrir_articles_relies_v28 as v28


class ClassifierTests(unittest.TestCase):
    def test_education_is_not_deleted_as_stopword(self):
        self.assertIn('educat',qualify.tokens('Education and educational policies'))
        branch={'b':{'concepts':{'c':qualify.tokens('Education policy')},'qids':{}}}
        kind,rows=qualify.classify('Education policy',['Education policy'],branch)
        self.assertEqual(rows[0]['concept_id_suggested'],'c')
        self.assertGreater(rows[0]['score'],40)
    def test_qid_match_is_a_proposal_not_an_approval(self):
        branch={'b':{'concepts':{'c':qualify.tokens('Teaching methods')},'qids':{'Q123':{'c'}}}}
        _,rows=qualify.classify('Other title',[],branch,qid='Q123')
        self.assertEqual(rows[0]['branch_id'],'b')
        self.assertIn('classification_non_validee',rows[0]['reason'])
    def test_crosswalk_requires_provisional_qid_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            concepts={'concepts':[{'unesco_id':'concept1','preferred_labels':{'en':['Teaching methods']}}]}
            (root/'concepts_demo.json').write_text(json.dumps(concepts))
            manifest={'schema':'encyklopedia.branch-manifest.v25/1','branch_id':'demo','vocabulary':'unesco',
                      'concepts_file':'concepts_demo.json','crosswalk_file':'x.json'}
            (root/'branche_demo.json').write_text(json.dumps(manifest))
            (root/'x.json').write_text(json.dumps({'mappings':[{'mapping_id':'wd-p3916-concept1',
                'status':'candidate','external_ref':{'system':'wikidata','id':'Q123'}}]}))
            branch=qualify.definitions(root)['demo']
            self.assertEqual(branch['qids']['Q123'],{'concept1'})

class MultibranchStationTests(unittest.TestCase):
    def setUp(self):
        self.tm=tempfile.TemporaryDirectory();self.addCleanup(self.tm.cleanup)
        self.base=Path(self.tm.name);self.repo=self.base/'repo'
        self.manifests=self.repo/'tools'/'unesco_pilot'/'v25_data';self.manifests.mkdir(parents=True)
        for b in ('legacy','other'):(self.manifests/f'branche_{b}.json').write_text('{}')
        self.v28=self.base/'v28';self.v28.mkdir()
        self.v27=self.base/'v27';(self.v27/'packs').mkdir(parents=True)
        self.cat=self.base/'cat.sqlite'
        with closing(sqlite3.connect(self.cat)) as db, db:
            db.executescript('''CREATE TABLE branches(branch_id TEXT);
                CREATE TABLE assignments(branch_id TEXT,wiki TEXT,page_id INTEGER,concept_id TEXT);
                CREATE TABLE articles(wiki TEXT,page_id INTEGER);
                CREATE TABLE reviewed_article_links_v28(branch_id TEXT,concept_id TEXT,page_id INTEGER);''')
            db.execute("INSERT INTO branches VALUES('other')")
        self.st=station.Station(self.repo,self.base/'post',self.v27,self.v28,self.cat)
        work=self.v28/'branches'/route.folder('other');work.mkdir(parents=True)
        self.stage=work/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        with closing(sqlite3.connect(self.stage)) as db, db:
            db.executescript('''CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);
               CREATE TABLE candidates(branch_id TEXT,concept_id TEXT,page_id INTEGER,title TEXT);
               CREATE TABLE evidence(branch_id TEXT,concept_id TEXT,page_id INTEGER,seed_page_id INTEGER,kind TEXT);''')
            db.executemany('INSERT INTO meta VALUES(?,?)', [('schema','TEST'),('branch_signature','sig'),
                ('branch_id','other'),('catalogue_sequence','45')])
            db.executemany('INSERT INTO candidates VALUES(?,?,?,?)',
                           (('other','concept1',i,f'School {i}') for i in range(1,351)))
            db.executemany('INSERT INTO evidence VALUES(?,?,?,?,?)',
                           (('other','concept1',i,999,'WIKILINK') for i in range(1,351)))
        self.legacy={'id':'legacy','signature':'legacy-signature','concepts':[{'unesco_id':'concept1'}]}
        self.other={'id':'other','signature':'sig','concepts':[{'unesco_id':'concept1'}]}
        def load(file):return self.legacy if 'legacy' in str(file) else self.other
        def build(_work,src,label):
            pid=int(src['page_id']);cid=f'other:concept1:{pid}'
            return {'candidate_id':cid,'branch_id':'other','concept_id':'concept1',
                    'concept_en':label,'page_id':pid,'title':src['title'],'priority':50,
                    'seed_count':1,'links':1,'shared':0,'subs':0,
                    'evidence_sha256':f'{pid:064x}','examples':'verified link'}
        v25=SimpleNamespace(DEFAULT_BRANCH=self.manifests/'branche_legacy.json',load_branch=load,
                            label=lambda c,lang:'Education policy',
                            meta=lambda db,key:(db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone() or [None])[0])
        self.engine=SimpleNamespace(v25=v25,FORMAT='TEST',candidate_id=lambda b,c,p:f'{b}:{c}:{p}',
                                   build_candidate=build)
        self.st._v28_engine=lambda:self.engine
        self.st._log=lambda message:None
        self.addCleanup(self.st.db.close)
    def test_deferral_is_not_rejection_and_exploration_is_reopenable(self):
        import ouvrir_exploration_v311 as explore
        self.assertEqual(self.st._refresh_review_index(),350)
        with self.st.db:self.st.db.execute("UPDATE review_index SET state='DEFERRED'")
        self.assertEqual(route.prepare(self.st,self.engine),0)
        result=explore.run(self.st.db_path if hasattr(self.st,'db_path') else self.st.work/'station_v30.sqlite',100,'other')
        self.assertEqual(result['reopened'],100)
        self.assertGreater(route.prepare(self.st,self.engine),0)
        self.assertGreater(self.st.db.execute("SELECT COUNT(*) FROM review_index WHERE state='QUEUED'").fetchone()[0],0)
        self.assertEqual(self.st.db.execute("SELECT COUNT(*) FROM review_index WHERE state='DECIDED'").fetchone()[0],0)

    def test_second_branch_packs_have_stable_routing_and_id_integrity(self):
        self.assertEqual(self.st._refresh_review_index(),350)
        self.assertEqual(self.st._prepare_v28(),0) # legacy stage absent
        self.assertEqual(route.prepare(self.st,self.engine),1)
        jobs=list(self.st.db.execute("SELECT * FROM jobs WHERE kind='v28'"))
        self.assertEqual(sum(x['count'] for x in jobs),350)
        self.assertEqual(sum(1 for x in jobs if x['count']>880),0)
        self.assertEqual(self.st.db.execute("SELECT COUNT(*) FROM review_index WHERE state='PENDING'").fetchone()[0],0)
        for job in jobs:
            resolved=route.job_route(self.st,job['id'])
            self.assertEqual(resolved['branch_id'],'other')
            self.assertEqual(Path(resolved['stage_path']),self.stage)
            with zipfile.ZipFile(job['bundle_path']) as z:
                names=z.namelist();self.assertEqual(sum(x.startswith('REVUE_') for x in names),1)
                rows=station.read_baseline(z.read('REVUE_'+job['id']+'.csv'))
                self.assertTrue(all(x['branch_id']=='other' for x in rows))
        with patch.object(route.subprocess,'run') as stub:
            stub.return_value=SimpleNamespace(returncode=0,stdout='{"status":"V28_APPLY_PREFLIGHT_OK"}')
            route.apply(self.st,self.engine,dict(jobs[0]),self.base/'reply.csv',True)
            opts=stub.call_args[0][0]
            self.assertIn('--branch',opts)
            self.assertIn('--dry-run',opts)
            self.assertEqual(opts[opts.index('--work')+1],str(self.stage.parent))

class RelationalEvidenceTests(unittest.TestCase):
    def test_complete_sql_discovery_creates_importable_v28_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);src=root/'wiki.sqlite';cat=root/'cat.sqlite';work=root/'discovery'
            with closing(sqlite3.connect(src)) as db, db:
                db.executescript('''CREATE TABLE wiki_pages(page_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT,
                  redirect INTEGER,latest_revision INTEGER,content_bytes INTEGER);
                  CREATE INDEX idx_page_title ON wiki_pages(ns,title);
                  CREATE TABLE wiki_linktargets(target_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT);
                  CREATE TABLE wiki_pagelinks(source_page_id INTEGER,target_id INTEGER);
                  CREATE TABLE wiki_categorylink_ids(source_page_id INTEGER,target_id INTEGER,type TEXT);
                  CREATE INDEX idx_wiki_catid_from ON wiki_categorylink_ids(source_page_id);
                  CREATE INDEX idx_wiki_catid_target ON wiki_categorylink_ids(target_id);''')
                db.executemany('INSERT INTO wiki_pages VALUES(?,?,?,?,?,?)',
                    [(1,0,'Educational_policy',0,11,100),(2,0,'Learning_methods',0,22,200)])
                db.execute("INSERT INTO wiki_linktargets VALUES(901,0,'Learning_methods')")
                db.execute('INSERT INTO wiki_pagelinks VALUES(1,901)')
            with closing(sqlite3.connect(cat)) as db, db:
                db.executescript('''CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);
                    CREATE TABLE articles(wiki TEXT,page_id INTEGER,title TEXT,revision_id INTEGER);
                    CREATE TABLE assignments(branch_id TEXT,wiki TEXT,page_id INTEGER,concept_id TEXT,score INTEGER);''')
                db.execute("INSERT INTO meta VALUES('sequence','1')")
                db.execute("INSERT INTO articles VALUES('enwiki',1,'Educational policy',11)")
                db.execute("INSERT INTO assignments VALUES('demo','enwiki',1,'concept1',80)")
            branch={'id':'demo','signature':'sig','concepts':[{'unesco_id':'concept1'}]}
            def checked(_src,_cat,_branch):
                con=sqlite3.connect(src.resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
                catcon=sqlite3.connect(cat.resolve().as_uri()+'?mode=ro',uri=True);catcon.row_factory=sqlite3.Row
                return con,catcon,'source_sig'
            source_before=hashlib.sha256(src.read_bytes()).digest()
            cat_before=hashlib.sha256(cat.read_bytes()).digest()
            with patch.object(v28.v25,'load_branch',return_value=branch),patch.object(v28,'checked_source',side_effect=checked),                 patch.object(v28.v25,'label',return_value='Educational policy'):
                report=sql_discovery.run(src,cat,root/'branch.json',work,max_seeds=20)
                self.assertEqual(report['new_evidence'],1)
                self.assertEqual(report['seeds_pending'],0)
                with closing(v28.v27.ro_sql(work/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite')) as db:
                    row=db.execute('SELECT * FROM candidates WHERE page_id=2').fetchone()
                    evidence=db.execute('SELECT kind,detail FROM evidence').fetchone()
                    self.assertEqual(evidence[0],'WIKILINK')
                    self.assertIn('Learning methods',evidence[1])
                    candidate=v28.build_candidate(db,row,'Educational policy')
                    self.assertEqual(candidate['page_id'],2)
                    self.assertEqual(len(candidate['evidence_sha256']),64)
            self.assertEqual(hashlib.sha256(src.read_bytes()).digest(),source_before)
            self.assertEqual(hashlib.sha256(cat.read_bytes()).digest(),cat_before)

class TargetResolutionTests(unittest.TestCase):
    def test_target_id_resolved_through_linktargets_and_source_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'wiki.sqlite'
            with closing(sqlite3.connect(src)) as db, db:
                db.executescript('''CREATE TABLE wiki_pages(page_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT,
                 redirect INTEGER,latest_revision INTEGER,content_bytes INTEGER);
                 CREATE INDEX idx_p_ns_title ON wiki_pages(ns,title);
                 CREATE TABLE wiki_linktargets(target_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT);
                 CREATE TABLE wiki_pagelinks(source_page_id INTEGER,target_id INTEGER);''')
                db.executemany('INSERT INTO wiki_pages VALUES(?,?,?,?,?,?)',
                   [(1,0,'Seed',0,11,100),(2,0,'Teaching_methods',0,22,200)])
                db.execute("INSERT INTO wiki_linktargets VALUES(900,0,'Teaching_methods')")
                db.execute('INSERT INTO wiki_pagelinks VALUES(1,900)')
            before=hashlib.sha256(src.read_bytes()).hexdigest()
            with closing(sqlite3.connect(src)) as db, db:
                db.row_factory=sqlite3.Row
                links=list(sql_discovery._targets(db,1,10))
                self.assertEqual(len(links),1)
                self.assertEqual(links[0]['page_id'],2)
                self.assertNotEqual(links[0]['page_id'],900)
            self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(),before)

if __name__=='__main__':unittest.main()
