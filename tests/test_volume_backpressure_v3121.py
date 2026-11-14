"""EncyKlopedia v31.2.1: global multi-branch backpressure is non-destructive."""
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import csv
import io
import sqlite3
import tempfile
import unittest
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
MODDIR = ROOT / 'tools' / 'unesco_pilot'
sys.path.insert(0, str(MODDIR))
SPEC = importlib.util.spec_from_file_location('station_v3121', MODDIR / 'poste_chatgpt_v30.py')
station = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(station)
import routage_branches_v311


class MultibranchBackpressureTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        d = Path(t.name)
        self.work = d / 'poste'
        self.v28 = d / 'v28'
        self.v28.mkdir()
        self.v27 = d / 'v27'
        self.cat = d / 'catalogue.sqlite'
        self.s = station.Station(ROOT, self.work, self.v27, self.v28, self.cat)
        self.addCleanup(self.s.db.close)
        self.branch = {'id': 'legacy.test', 'signature': 'testsig', 'concepts': [{'unesco_id': 'c1'}]}
        self.cid = 'c1_id_1'
        def build_candidate(_con, row, label):
            return {'candidate_id': self.cid, 'branch_id': row['branch_id'],
                    'concept_id': row['concept_id'], 'concept_en': label,
                    'page_id': row['page_id'], 'title': row['title'],
                    'priority': 71, 'seed_count': 1, 'links': 1, 'shared': 0, 'subs': 0,
                    'evidence_sha256': 'a' * 64, 'examples': 'source verified in this fixture'}
        def meta(con, key):
            r = con.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
            return r[0] if r else None
        v25 = SimpleNamespace(DEFAULT_BRANCH=Path('unused.json'),
                              load_branch=lambda _: self.branch,
                              label=lambda _c, _lang: 'Educational research', meta=meta)
        engine = SimpleNamespace(v25=v25, build_candidate=build_candidate,
                                 candidate_id=lambda _b, _c, _p: self.cid)
        self.s._v28_engine = lambda: engine
        with closing(sqlite3.connect(self.v28 / 'DECOUVERTE_ARTICLES_RELIES_V28.sqlite')) as con, con:
            con.executescript('''CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT);
                CREATE TABLE candidates(branch_id TEXT,concept_id TEXT,page_id INTEGER,title TEXT);
                ''')
            con.execute('INSERT INTO meta VALUES(?,?)', ('catalogue_sequence', '5'))
            con.execute('INSERT INTO candidates VALUES(?,?,?,?)', (self.branch['id'], 'c1', 1, 'Research example'))
        with self.s.db:
            self.s.db.execute('''INSERT INTO review_index(candidate_id,branch_id,concept_id,page_id,title,
                priority,seed_count,link_evidence,category_evidence,subcategory_evidence,state,last_seen_utc)
                VALUES(?,?,?,?,?,?,?,?,?,?,'PENDING',?)''',
                (self.cid,self.branch['id'],'c1',1,'Research example',71,1,1,0,0,station.now()))

    def add_jobs(self, count, routed):
        with self.s.db:
            for i in range(count):
                jid = f'historical_{i:03}' if not routed else f'branch_{i:03}'
                self.s.db.execute('''INSERT INTO jobs(id,kind,key,count,status,source_path,source_sha256,
                    bundle_path,bundle_sha256,created_utc) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                    (jid,'v28',jid,110,'WAITING',f'original/{jid}.csv','1'*64,
                     f'original/{jid}.zip','2'*64,station.now()))
                if routed:
                    self.s.db.execute('''INSERT INTO v311_job_routes(job_id,branch_id,manifest_path,
                        stage_path,work_path,branch_signature) VALUES(?,?,?,?,?,?)''',
                        (jid,'secondary.test','unchanged.json','unchanged.sqlite','unchanged','unchanged'))

    def test_full_global_buffer_creates_no_legacy_job(self):
        self.add_jobs(20, routed=True)
        before = [tuple(r) for r in self.s.db.execute('SELECT id,status,source_sha256 FROM jobs ORDER BY id')]
        with patch.object(routage_branches_v311,'live',return_value=[object()]):
            self.assertEqual(self.s._prepare_v28(),0)
        after = [tuple(r) for r in self.s.db.execute('SELECT id,status,source_sha256 FROM jobs ORDER BY id')]
        self.assertEqual(before, after)
        self.assertEqual(self.s.db.execute('SELECT state FROM review_index WHERE candidate_id=?', (self.cid,)).fetchone()[0],'PENDING')

    def test_only_one_available_slot_is_consumed(self):
        self.add_jobs(19, routed=True)
        before = {r['id']:r['source_sha256'] for r in self.s.db.execute('SELECT id,source_sha256 FROM jobs')}
        with patch.object(routage_branches_v311,'live',return_value=[object()]):
            self.assertEqual(self.s._prepare_v28(),1)
        self.assertEqual(self.s._open_review_count(),20)
        for jid,digest in before.items():
            self.assertEqual(self.s._row(jid)['source_sha256'], digest)
        fresh = self.s.db.execute("SELECT * FROM jobs WHERE kind='v28' AND id LIKE 'v28_%'").fetchone()
        self.assertIsNotNone(fresh)
        self.assertEqual(fresh['count'],1)
        with Path(fresh['source_path']).open(encoding='utf-8-sig',newline='') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]['candidate_id'], self.cid)
        self.assertEqual(rows[0]['evidence_sha256'], 'a' * 64)
        self.assertEqual(self.s.db.execute('SELECT state FROM review_index WHERE candidate_id=?', (self.cid,)).fetchone()[0],'QUEUED')

    def test_legacy_quota_does_not_bypass_secondary_share(self):
        self.add_jobs(10, routed=False)
        with patch.object(routage_branches_v311,'live',return_value=[object()]):
            self.assertEqual(self.s._prepare_v28(),0)
        self.assertEqual(self.s._open_review_count(),10)
        self.assertEqual(self.s.db.execute('SELECT state FROM review_index WHERE candidate_id=?',(self.cid,)).fetchone()[0],'PENDING')

    def test_no_extra_branches_keeps_historic_path(self):
        with patch.object(routage_branches_v311,'live',return_value=[]):
            self.assertEqual(self.s._prepare_v28(),1)
        self.assertEqual(self.s._open_review_count(),1)


if __name__ == '__main__':
    unittest.main()
