"""Functional, non-destructive tests for v30. Run from repository root with unittest."""
import csv
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('station30',ROOT/'tools/unesco_pilot/poste_chatgpt_v30.py')
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)

class StationV30Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name)
        self.repo=ROOT;self.v27=base/'v27';self.v28=base/'v28';self.work=base/'work'
        (self.v27/'packs').mkdir(parents=True)
        self.v28.mkdir(parents=True)
        self.catalogue=base/'catalogue.sqlite'
        with sqlite3.connect(self.catalogue) as con:
            con.executescript('''CREATE TABLE articles(wiki TEXT,page_id INTEGER);
              CREATE TABLE assignments(branch_id TEXT,wiki TEXT,page_id INTEGER,concept_id TEXT);
              CREATE TABLE reviewed_article_links_v28(branch_id TEXT,concept_id TEXT,page_id INTEGER);
              ''')
        self.station=m.Station(self.repo,self.work,self.v27,self.v28,self.catalogue)
        self.commands=[]
        self.station._run=lambda script,opts:self.commands.append((script,opts)) or 'V27_ACTION_OK'

    def tearDown(self):self.station.db.close()

    def make_stage(self,n=2500):
        engine=self.station._v28_engine()
        branch=engine.v25.load_branch(engine.v25.DEFAULT_BRANCH)
        cid=branch['concepts'][0]['unesco_id']
        stage=self.v28/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        with sqlite3.connect(stage) as con:
            con.executescript(engine.INIT)
            con.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('schema',engine.FORMAT))
            con.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('branch_signature',branch['signature']))
            con.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('catalogue_sequence','36'))
            con.execute("INSERT INTO seed_queue VALUES(?,?,?,?,?,?,?)",
                 (branch['id'],99001,'Test seed','1','x','DONE',m.now()))
            con.executemany('INSERT INTO candidates VALUES(?,?,?,?,?,?)',
                ((branch['id'],cid,k,f'Test school {k}','100',m.now()) for k in range(1,n+1)))
            con.executemany('INSERT INTO evidence VALUES(?,?,?,?,?,?)',
                ((branch['id'],cid,k,99001,'WIKILINK',f'Test link to {k}') for k in range(1,n+1)))
        return branch,cid

    def wait_busy(self):
        for _ in range(100):
            if not self.station.busy:return
            time.sleep(.03)
        self.fail('Background operation did not finish')

    def test_pagination_beyond_3000_and_persistent_ten_lanes(self):
        self.make_stage(3155)
        self.station._prepare()
        stat=self.station.snapshot()
        self.assertGreater(stat['review_index'].get('PENDING',0),0)
        self.assertGreaterEqual(stat['review_index'].get('QUEUED',0),2000)
        self.assertEqual(len([s for s in stat['lanes'] if s['job']]),10)
        self.assertEqual(stat['jobs']['WAITING'],10)
        self.station.db.close()
        self.station=m.Station(self.repo,self.work,self.v27,self.v28,self.catalogue)
        self.assertEqual(len([s for s in self.station.snapshot()['lanes'] if s['job']]),10)
        # Mark all 20 as done, all candidates as HOLD, then index the next page.
        with self.station.db:
            self.station.db.execute("UPDATE jobs SET status='DONE' WHERE kind='v28'")
            self.station.db.execute("UPDATE review_index SET state='HOLD' WHERE state='QUEUED'")
        generated=self.station._prepare_v28()
        self.assertGreater(generated,0)  # automatic next page beyond top candidates
        self.assertEqual(self.station.snapshot()['review_index'].get('PENDING',0),0)

    def test_original_evidence_and_three_column_return(self):
        self.make_stage(4);self.station._prepare()
        job=dict(self.station.db.execute("SELECT * FROM jobs WHERE kind='v28' LIMIT 1").fetchone())
        rows=m.read_baseline(Path(job['source_path']).read_bytes())
        out=io.StringIO(newline='');w=csv.DictWriter(out,fieldnames=['candidate_id','decision','justification']);w.writeheader()
        w.writerow({'candidate_id':rows[0]['candidate_id'],'decision':'APPROVE',
                    'justification':'Établissement explicitement relié au concept UNESCO.'})
        for r in rows[1:]:w.writerow({'candidate_id':r['candidate_id'],'decision':'HOLD','justification':''})
        response=out.getvalue().encode()
        full,counts=self.station.merge_review(job,response)
        self.assertEqual((counts['APPROVE'],counts['HOLD']),(1,3))
        self.assertEqual(len(m.read_baseline(full)),4)
        illegal=[dict(r) for r in rows];illegal[0]['title']='Changed title'
        with self.assertRaisesRegex(ValueError,'Preuve source modifiée'):
            self.station.merge_review(job,m.csv_bytes(illegal))
        found,kind=self.station._resolve_return('DECISIONS_'+job['id']+'.csv',response)
        self.assertEqual((found['id'],kind),(job['id'],'v28'))
        z=io.BytesIO()
        with zipfile.ZipFile(z,'w') as f:f.writestr('DECISIONS_'+job['id']+'.csv',response)
        self.station.receive([('return.zip',z.getvalue())]);self.wait_busy()
        done=self.station.db.execute('SELECT status,review_approved,review_hold FROM jobs WHERE id=?',(job['id'],)).fetchone()
        self.assertEqual(tuple(done),('DONE',1,3));self.assertEqual(len(self.commands),2)
        self.assertTrue(any('-DryRun' in opts for _,opts in self.commands))

    def test_all_hold_requires_confirmation(self):
        self.make_stage(2);self.station._prepare()
        job=dict(self.station.db.execute("SELECT * FROM jobs WHERE kind='v28' LIMIT 1").fetchone())
        raw=b'candidate_id,decision,justification\n'
        self.station._import_one(job,'v28',raw)
        self.assertEqual(self.station._row(job['id'])['status'],'NEEDS_CONFIRMATION')
        self.assertEqual(self.commands,[])
        self.station.confirm_hold(job['id'])
        self.assertEqual(self.station._row(job['id'])['status'],'DONE')
        self.assertEqual(self.station.db.execute("SELECT count(*) FROM review_index WHERE state='HOLD'").fetchone()[0],2)

    def test_unsafe_zip_rejected(self):
        z=io.BytesIO()
        with zipfile.ZipFile(z,'w') as f:f.writestr('run.cmd',b'del C:\\*')
        with self.assertRaisesRegex(ValueError,'interdit'):
            m.extract_zip_files('return.zip',z.getvalue())
        z=io.BytesIO()
        with zipfile.ZipFile(z,'w') as f:f.writestr('../DECISIONS_blah.csv',b'x')
        with self.assertRaisesRegex(ValueError,'Chemin ZIP'):
            m.extract_zip_files('return.zip',z.getvalue())

    def test_import_error_remains_visible_and_retry(self):
        self.make_stage(2);self.station._prepare()
        job=dict(self.station.db.execute("SELECT * FROM jobs WHERE kind='v28' LIMIT 1").fetchone())
        self.station._run=lambda *_:(_ for _ in ()).throw(ValueError('Erreur moteur test'))
        first=m.read_baseline(Path(job['source_path']).read_bytes())[0]
        rows=m.read_baseline(Path(job['source_path']).read_bytes())
        raw=('candidate_id,decision,justification\n'+first['candidate_id']+',REJECT,Not relevant\n'+rows[1]['candidate_id']+',HOLD,\n').encode()
        with self.assertRaisesRegex(ValueError,'Erreur moteur test'):
            self.station._import_one(job,'v28',raw)
        self.assertEqual(self.station._row(job['id'])['status'],'ERROR')
        self.station.retry(job['id']);self.assertEqual(self.station._row(job['id'])['status'],'READY')

    def test_freeze_discovery_with_unresolved_reviews(self):
        self.make_stage(2);self.station._prepare()
        self.station._run=lambda script,opts:self.commands.append((script,opts)) or '"queue":{"PACKED":1134}'
        self.station._batch()
        self.assertFalse(any(script=='DECOUVRIR_ARTICLES_RELIES_V28.ps1' for script,_ in self.commands))

if __name__=='__main__':unittest.main(verbosity=2)

class OverlayUpdateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        d=Path(self.tmp.name);self.repo=d/'repo';self.repo.mkdir()
        (self.repo/'docs').mkdir()
        (self.repo/'docs/example.md').write_bytes(b'OLD')
        self.station=m.Station(self.repo,d/'work',d/'v27',d/'v28',d/'cat.sqlite')
    def tearDown(self):self.station.db.close()
    def archive(self,files,changes=None):
        info=[]
        for name,data in files.items():
            item={'path':name,'sha256':m.sha(data)}
            old=self.repo/name
            item['requires_sha256']=m.sha(old.read_bytes()) if old.exists() else None
            info.append(item)
        man={'format':'encyklopedia.safe-overlay.v30/1','description':'Test contrôlé', 'files':info}
        if changes:man.update(changes)
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('ENCYK_OVERLAY_MANIFEST_V30.json',m.json_text(man))
            for path,data in files.items():z.writestr(path,data)
        return buf.getvalue()
    def test_overlay_explicit_install_and_rollback(self):
        raw=self.archive({'docs/example.md':b'NEW','docs/new.md':b'ADDED'})
        preview=self.station.stage_update(raw)
        self.assertEqual((self.repo/'docs/example.md').read_bytes(),b'OLD')
        self.assertEqual(len(preview['files']),2)
        applied=self.station.apply_update(preview['id']);self.assertTrue(applied['restart_required'])
        self.assertEqual((self.repo/'docs/example.md').read_bytes(),b'NEW')
        self.assertEqual((self.repo/'docs/new.md').read_bytes(),b'ADDED')
        self.station.rollback_update(preview['id'])
        self.assertEqual((self.repo/'docs/example.md').read_bytes(),b'OLD')
        self.assertFalse((self.repo/'docs/new.md').exists())
    def test_overlay_integrity_and_path_guard(self):
        raw=self.archive({'docs/new.md':b'OK'})
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            entries={n:z.read(n) for n in z.namelist()}
        entries['docs/new.md']=b'TAMPER'
        bad=io.BytesIO()
        with zipfile.ZipFile(bad,'w') as z:
            for name,data in entries.items():z.writestr(name,data)
        with self.assertRaisesRegex(ValueError,'SHA incorrect'):
            self.station.stage_update(bad.getvalue())
        evil=self.archive({'../escaped.py':b'code'})
        with self.assertRaisesRegex(ValueError,'Chemin logiciel interdit'):
            self.station.stage_update(evil)
