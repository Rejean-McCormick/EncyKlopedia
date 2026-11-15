"""V31.7 tests : new 4,000-row UNESCO packs, immutable sources, historical compatibility."""
from contextlib import closing
import csv
import hashlib
import importlib.util
import io
from pathlib import Path
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/'tools'/'unesco_pilot'
sys.path.insert(0,str(PILOT))
SPEC=importlib.util.spec_from_file_location('poste_chatgpt_v30',PILOT/'poste_chatgpt_v30.py')
station=importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name]=station
SPEC.loader.exec_module(station)

class UNESCO4000Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        p=Path(tmp.name);repo=p/'repo';repo.mkdir()
        v27=p/'v27';v27.mkdir()
        v28=p/'v28';v28.mkdir()
        cat=p/'cat.sqlite'
        self.st=station.Station(repo,p/'work',v27,v28,cat)
        self.addCleanup(self.st.db.close)
        self.branch={'id':'unesco.mt1.10.test','signature':'abc123','concepts':[{'unesco_id':'u1'}]}
        m=SimpleNamespace(
            FORMAT='TEST_V28',
            v25=SimpleNamespace(DEFAULT_BRANCH=Path('placeholder'),
                load_branch=lambda x:self.branch,
                label=lambda c,l:'Educational policy',
                meta=lambda db,k:(db.execute('SELECT value FROM meta WHERE key=?',(k,)).fetchone() or [None])[0]),
            build_candidate=lambda db,r,label:dict(candidate_id='candidate_'+str(r['page_id']),branch_id=r['branch_id'],
                 concept_id=r['concept_id'],concept_en=label,page_id=r['page_id'],title=r['title'],
                 priority=88,seed_count=1,links=1,shared=0,subs=0,
                 evidence_sha256=hashlib.sha256(str(r['page_id']).encode()).hexdigest(),
                 examples='Prouvé par WIKILINK'))
        self.st._v28_engine=lambda:m
        stage=v28/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        with closing(sqlite3.connect(stage)) as db,db:
            db.executescript('''CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);
              CREATE TABLE candidates(branch_id TEXT,concept_id TEXT,page_id INTEGER,title TEXT);''')
            db.executemany('INSERT INTO meta VALUES(?,?)', [('catalogue_sequence','99'),('schema','TEST_V28'),('branch_signature','abc123')])
            db.executemany('INSERT INTO candidates VALUES(?,?,?,?)',
                ((self.branch['id'],'u1',i,f'School {i}') for i in range(1,4126)))
        with self.st.db:
            self.st.db.executemany('''INSERT INTO review_index(candidate_id,branch_id,concept_id,page_id,title,priority,
              seed_count,link_evidence,category_evidence,subcategory_evidence,last_seen_utc)
              VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
              ((f'candidate_{i}',self.branch['id'],'u1',i,f'School {i}',88,1,1,0,0,station.now()) for i in range(1,4126)))

    def test_4000_then_remainder_without_deleting_candidates(self):
        self.assertEqual(station.REVIEW_SIZE,4000)
        self.assertEqual(station.REVIEW_BUDGET,16000)
        self.assertEqual(self.st._prepare_v28(),2)
        jobs=[dict(r) for r in self.st.db.execute("SELECT * FROM jobs WHERE kind='v28' ORDER BY count DESC")]
        self.assertEqual([j['count'] for j in jobs],[4000,125])
        ids=set()
        for j in jobs:
            raw=Path(j['source_path']).read_bytes()
            self.assertEqual(station.sha(raw),j['source_sha256'])
            with zipfile.ZipFile(j['bundle_path']) as z:
                self.assertEqual(z.read('REVUE_'+j['id']+'.csv'),raw)
                self.assertIn(b'candidate_id,decision,justification',z.read('PROMPT_CHATGPT.txt'))
            rows=station.read_baseline(raw)
            ids.update(r['candidate_id'] for r in rows)
            self.assertEqual(len({r['evidence_sha256'] for r in rows}),len(rows))
        self.assertEqual(len(ids),4125)
        self.assertEqual(self.st.db.execute("SELECT count(*) FROM review_index WHERE state='QUEUED'").fetchone()[0],4125)
        self.assertEqual(self.st._prepare_v28(),0)
        # Return must be valid with strictly 3 columns, all 4,000 identifiers.
        big=jobs[0];original=Path(big['source_path']).read_bytes()
        result=io.StringIO(newline='');w=csv.writer(result);w.writerow(['candidate_id','decision','justification'])
        for row in station.read_baseline(original):w.writerow([row['candidate_id'],'HOLD','Contexte insuffisant : revoir ultérieurement'])
        merged,count=self.st.merge_review(big,result.getvalue().encode('utf-8'))
        self.assertEqual(count['HOLD'],4000)
        self.assertEqual(len(station.read_baseline(merged)),4000)
        self.assertEqual(original,Path(big['source_path']).read_bytes())

    def test_880_existing_reply_compatible_and_stats_honest(self):
        ids=[f'old_{i}' for i in range(880)]
        rows=[dict(candidate_id=x,branch_id='un',concept_id='c',concept_en='Education',page_id=i,title='Old',priority=3,
            seed_count=1,link_evidence=1,category_evidence=0,subcategory_evidence=0,
            evidence_sha256=hashlib.sha256(x.encode()).hexdigest(),examples='link',decision='HOLD',justification='') for i,x in enumerate(ids)]
        p=self.st.work/'old.csv';p.write_bytes(station.csv_bytes(rows))
        job={'source_path':str(p),'source_sha256':station.sha_path(p)}
        reply=io.StringIO(newline='');w=csv.writer(reply);w.writerow(['candidate_id','decision','justification'])
        for x in ids:w.writerow([x,'REJECT','Lien documentaire accessoire'])
        merged,counts=self.st.merge_review(job,reply.getvalue().encode('utf-8'))
        self.assertEqual(counts['REJECT'],880)
        self.assertEqual(len(station.read_baseline(merged)),880)
        with self.st.db:
            self.st.db.execute('''INSERT INTO jobs(id,kind,key,count,status,source_path,source_sha256,bundle_path,bundle_sha256,created_utc)
            VALUES(?,?,?,?,?,?,?,?,?,?)''',('historic','v28','historic',880,'WAITING',str(p),station.sha_path(p),str(p),station.sha_path(p),station.now()))
        telemetry=self.st.volume_v315()
        self.assertEqual(telemetry['unesco_par_taille']['volume_650_880'],1)
        self.assertEqual(telemetry['contrat']['unesco_cible'],4000)

if __name__=='__main__':unittest.main(verbosity=2)
