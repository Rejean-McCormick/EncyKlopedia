"""Tests hors-ligne du pont explicite v26 -> catalogue v25 existant."""
from __future__ import annotations
import contextlib
import csv
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE/'tools'/'unesco_pilot'))
import catalogue_global_v25 as v25
import integrer_ponts_revus_v26 as bridge


class BridgeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'wiki.sqlite'
        self.catalogue=self.root/'catalogue.sqlite'
        self.output=self.root/'out'
        self.csv=bridge.DEFAULT_CSV
        self.branch=bridge.DEFAULT_BRANCH
        includes=bridge.read_bridges(self.csv,v25.load_branch(self.branch))['included']
        self.includes=includes
        con=sqlite3.connect(self.source)
        con.executescript('''
          CREATE TABLE wiki_pages(page_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT,redirect INTEGER,
                                  latest_revision INTEGER,content_bytes INTEGER);
          CREATE TABLE wiki_qid(page_id INTEGER PRIMARY KEY,qid TEXT NOT NULL);
          CREATE TABLE wiki_linktargets(target_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT);
          CREATE TABLE wiki_categorylink_ids(source_page_id INTEGER,target_id INTEGER,type TEXT);
          CREATE TABLE ingest_state(stage TEXT PRIMARY KEY,completed INTEGER,rows_imported INTEGER);
          CREATE INDEX idx_wiki_pages_title ON wiki_pages(ns,title);
          CREATE INDEX idx_wiki_qid_qid ON wiki_qid(qid);
          CREATE INDEX idx_wiki_lt_title ON wiki_linktargets(ns,title);
          CREATE INDEX idx_wiki_catid_from ON wiki_categorylink_ids(source_page_id);
          CREATE INDEX idx_wiki_catid_target ON wiki_categorylink_ids(target_id);
        ''')
        con.executemany('INSERT INTO ingest_state VALUES(?,1,999)',
                        [(n,) for n in ['page','page_props','linktarget','categorylinks']])
        con.execute("INSERT INTO wiki_pages VALUES(1,0,'Educational_policy',0,101,999)")
        con.execute("INSERT INTO wiki_pages VALUES(2,0,'Other_education_subject',0,102,700)")
        con.execute("INSERT INTO wiki_pages VALUES(3,0,'Redirect_to_other',1,103,10)")
        con.execute("INSERT INTO wiki_pages VALUES(4,14,'Subcategory_example',0,104,10)")
        con.execute("INSERT INTO wiki_linktargets VALUES(100,14,'Educational_policy')")
        # Ce jeu synthétique contient toutes les catégories actives du vrai CSV.
        unique_names=list(dict.fromkeys(r['category_title'] for r in includes))
        for i,title in enumerate(unique_names, 101):
            con.execute('INSERT INTO wiki_linktargets VALUES(?,14,?)',(i,v25.wiki_title(title)))
            con.execute('INSERT INTO wiki_categorylink_ids VALUES(?,?,?)',(2,i,'page'))
            con.execute('INSERT INTO wiki_categorylink_ids VALUES(?,?,?)',(3,i,'page'))
        con.execute('INSERT INTO wiki_categorylink_ids VALUES(2,100,"page")')
        con.commit();con.close()
        self.invoke(v25.main,'run',v25=True,extra=['--max-batches','1'])

    def invoke(self,fn,action,v25=False,extra=None,expect=0):
        args=[action,'--source-db',str(self.source),'--catalogue-db',str(self.catalogue),
              '--output-dir',str(self.output),'--branch',str(self.branch),
              '--max-batches','100','--batch-size','10']
        if not v25:args.extend(['--reviewed-bridges',str(self.csv)])
        if extra:args.extend(extra)
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            code=fn(args)
        self.assertEqual(code,expect)
        return out.getvalue()

    def count(self,what):
        with sqlite3.connect(self.catalogue) as c:
            return c.execute('SELECT count(*) FROM '+what).fetchone()[0]

    def test_isolated_python_cli_preflight_apply_verify(self):
        script=HERE/'tools'/'unesco_pilot'/'integrer_ponts_revus_v26.py'
        base=[sys.executable,'-I',str(script),
              '--source-db',str(self.source),'--catalogue-db',str(self.catalogue),
              '--output-dir',str(self.output),'--branch',str(self.branch),
              '--reviewed-bridges',str(self.csv), '--max-batches','100','--batch-size','10']
        for action in ('preflight','apply','verify'):
            r=subprocess.run([*base[:3],action,*base[3:]],capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,msg=f'{action}: {r.stdout} {r.stderr}')
            self.assertIn({'preflight':'V26_BRIDGES_PREFLIGHT_OK',
                           'apply':'V26_BRIDGES_APPLIED_OK',
                           'verify':'V26_BRIDGES_VERIFY_OK'}[action],r.stdout)

    def test_preflight_does_not_change_catalogue(self):
        before=self.catalogue.read_bytes()
        result=self.invoke(bridge.main,'preflight')
        self.assertIn('"selected": 28',result)
        self.assertIn('"decisions_reviewed": 423',result)
        self.assertEqual(self.catalogue.read_bytes(),before)

    def test_apply_28_no_loss_and_idempotent(self):
        article_before=self.count('articles')
        prior=self.count('assignments')
        prior_snapshots=list((self.output/'snapshots').iterdir())
        result=self.invoke(bridge.main,'apply')
        self.assertIn('V26_BRIDGES_APPLIED_OK',result)
        self.assertEqual(self.count('reviewed_bridges_v26'),28)
        self.assertGreaterEqual(self.count('assignments'),prior)
        self.assertGreaterEqual(self.count('articles'),article_before)
        self.assertEqual(self.count('articles'),article_before) # single article in many categories
        self.assertTrue(all(p.is_dir() for p in prior_snapshots))
        latest=json.loads((self.output/'LATEST.json').read_text())
        snap=self.output/latest['snapshot']
        rep=v25.read_json(snap/'RAPPORT_V25.json')
        self.assertIsInstance(rep['snapshot_sequence'],int)
        self.assertEqual(rep['canonical_admissions'],0)
        self.assertEqual(rep['category_caps_require_review'],False)
        count_tasks=self.count('category_tasks')
        count_assgn=self.count('assignments')
        self.invoke(bridge.main,'apply')
        self.assertEqual(self.count('category_tasks'),count_tasks)
        self.assertEqual(self.count('assignments'),count_assgn)
        self.assertEqual(self.count('reviewed_bridge_imports_v26'),1)
        self.assertIn('V26_BRIDGES_VERIFY_OK',self.invoke(bridge.main,'verify'))

    def test_resume_with_zero_then_run(self):
        self.invoke(bridge.main,'apply',extra=['--max-batches','0'])
        with sqlite3.connect(self.catalogue) as c:
            pending=c.execute("SELECT count(*) FROM category_tasks WHERE state='PENDING'").fetchone()[0]
        self.assertGreater(pending,0)
        self.invoke(bridge.main,'apply')
        with sqlite3.connect(self.catalogue) as c:
            self.assertEqual(c.execute("SELECT count(*) FROM category_tasks WHERE state='PENDING'").fetchone()[0],0)

    def test_refuse_unexpected_source_version(self):
        with sqlite3.connect(self.source) as db:
            db.execute("INSERT INTO wiki_pages VALUES(500,0,'Changed',0,500,1)")
        db=sqlite3.connect(self.catalogue)
        old=db.execute('SELECT count(*) FROM category_tasks').fetchone()[0];db.close()
        with self.assertRaises(v25.Refusal):self.invoke(bridge.main,'preflight')
        self.assertEqual(self.count('category_tasks'),old)

    def test_refuse_missing_source_category_before_write(self):
        old_count=self.count('category_tasks')
        with sqlite3.connect(self.source) as db:
            db.execute("DELETE FROM wiki_linktargets WHERE title=?", (v25.wiki_title(self.includes[0]['category_title']),))
        with self.assertRaises(v25.Refusal):self.invoke(bridge.main,'preflight')
        self.assertEqual(self.count('category_tasks'),old_count)

    def test_refuse_mutated_manifest_signature(self):
        with sqlite3.connect(self.catalogue) as db:
            db.execute("UPDATE branches SET config_sha='unexpected' WHERE branch_id='unesco.mt1.10'")
        with self.assertRaises(v25.Refusal):self.invoke(bridge.main,'preflight')

    def test_reject_changed_reviewed_bridge_without_deleting_original(self):
        self.invoke(bridge.main,'apply',extra=['--max-batches','0'])
        original_count=self.count('reviewed_bridges_v26')
        with self.csv.open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        row=next(r for r in rows if r['decision']=='INCLUDE')
        row['justification']='Justification contradictoire apres approbation; ne pas ecraser un pont existant.'
        alt=self.root/'changed.csv'
        with alt.open('w',encoding='utf-8',newline='') as fp:
            w=csv.DictWriter(fp,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
        with self.assertRaises(v25.Refusal):self.invoke(bridge.main,'apply',extra=['--reviewed-bridges',str(alt)])
        self.assertEqual(self.count('reviewed_bridges_v26'),original_count)

    def test_two_branches_do_not_get_unrelated_work(self):
        # A task for another branch should not be needed to run the MT1.10 integration.
        with sqlite3.connect(self.catalogue) as db:
            db.execute('INSERT INTO branches(branch_id,vocabulary,branch_version,title_fr,config_sha,max_category_tasks,max_members_per_category,added_utc) '
                       "VALUES ('other.test','unesco','test','Autre','test',10,100,'now')")
            db.execute("INSERT INTO category_tasks(branch_id,concept_id,root_category,category_title,target_id,depth,max_depth,kind) "
                       "VALUES('other.test','unknown','Some', 'Some',100,0,0,'AUTO_EXACT_LABEL_CANDIDATE')")
        result=self.invoke(bridge.main,'apply')
        self.assertIn('V26_BRIDGES_APPLIED_OK',result)
        with sqlite3.connect(self.catalogue) as db:
            self.assertEqual(db.execute("SELECT state FROM category_tasks WHERE branch_id='other.test'").fetchone()[0],'PENDING')


if __name__=='__main__':unittest.main()
