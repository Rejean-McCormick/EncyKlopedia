"""Tests offline du moteur v25, SQLite source simulee, jamais le D: utilisateur."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ENGINE = Path(__file__).resolve().parents[1] / 'tools' / 'unesco_pilot' / 'catalogue_global_v25.py'
sys.path.insert(0, str(ENGINE.parent))
import catalogue_global_v25 as m


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'wiki.sqlite'
        self.dest = self.root / 'catalogue.sqlite'
        self.out = self.root / 'out'
        con = sqlite3.connect(self.source)
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
        con.executemany('INSERT INTO ingest_state VALUES(?,1,20)',
                        [(s,) for s in ('page', 'page_props', 'linktarget', 'categorylinks')])
        con.executemany('INSERT INTO wiki_pages VALUES(?,?,?,?,?,?)',
                        [(1, 0, 'Educational_policy', 0, 101, 500),
                         (2, 0, 'Teacher_policy', 0, 102, 400),
                         (3, 14, 'Teacher_policy', 0, 103, 0),
                         (4, 0, 'Redirect', 1, 104, 2)] +
                        [(n, 0, 'Example_' + str(n), 0, 100 + n, 1000) for n in range(10, 50)])
        con.executemany('INSERT INTO wiki_linktargets VALUES(?,14,?)',
                        [(30, 'Educational_policy'), (31, 'Teacher_policy')])
        con.execute("INSERT INTO wiki_qid VALUES(1,'Q111')")
        con.execute("INSERT INTO wiki_qid VALUES(2,'Q222')")
        con.executemany('INSERT INTO wiki_categorylink_ids VALUES(?,?,?)',
                        [(n, 30, 'page') for n in range(10, 50)] +
                        [(2, 30, 'page'), (4, 30, 'page'), (3, 30, 'subcat')] +
                        [(1, 31, 'page'), (2, 31, 'page')])
        con.commit();con.close()
        self.concepts = self.root / 'concepts.json'
        self.concepts.write_text(json.dumps({'concepts': [
            {'unesco_id': 'concept9', 'preferred_labels': {'en': ['Educational policy'], 'fr': ['Politique educative']},
             'broader': [], 'related': []},
            {'unesco_id': 'concept17163', 'preferred_labels': {'en': ['Teacher policy'], 'fr': ['Politique enseignante']},
             'broader': [], 'related': []}
        ]}), encoding='utf-8')
        self.crosswalk = self.root / 'crosswalk.json'
        self.crosswalk.write_text(json.dumps({'mappings': [
            {'mapping_id': 'wd-p3916-concept9', 'status': 'candidate',
             'external_ref': {'system': 'wikidata', 'id': 'Q111'}},
            {'mapping_id': 'wd-p3916-concept17163', 'status': 'candidate',
             'external_ref': {'system': 'wikidata', 'id': 'Q222'}}
        ]}), encoding='utf-8')
        self.bridges = self.root / 'ponts.csv'
        self.bridges.write_text('concept_id,category_title,status,justification,depth_limit\n', encoding='utf-8')
        self.branch = self.create_branch('unesco.mt1.10.test')

    def create_branch(self, name):
        cfg = {'schema': 'encyklopedia.branch-manifest.v25/1', 'branch_id': name,
               'branch_version': '2026-11-test', 'vocabulary': 'unesco', 'title_fr': name,
               'concepts_file': 'concepts.json', 'crosswalk_file': 'crosswalk.json',
               'bridges_file': 'ponts.csv', 'discovery': {
                   'auto_exact_category_roots': True, 'auto_root_depth': 0,
                   'max_reviewed_root_depth': 2, 'max_category_tasks': 100,
                   'max_members_per_category': 30}}
        p = self.root / (name + '.json')
        p.write_text(json.dumps(cfg), encoding='utf-8')
        return p

    def invoke(self, action='run', *args, branches=None):
        cmd = [action, '--source-db', str(self.source), '--catalogue-db', str(self.dest),
               '--output-dir', str(self.out), '--batch-size', '10', '--sample-limit', '20',
               '--max-batches', '1', *args]
        for b in branches if branches is not None else [self.branch]:
            cmd.extend(['--branch', str(b)])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            rc = m.main(cmd)
        self.assertEqual(rc, 0)
        return output.getvalue()

    def test_source_preflight_requires_index_and_is_read_only(self):
        self.assertIn('V25_PREFLIGHT_OK', self.invoke('preflight'))
        self.assertFalse(self.dest.exists())
        con = sqlite3.connect(self.source)
        con.execute('DROP INDEX idx_wiki_catid_target');con.commit();con.close()
        with self.assertRaises(m.Refusal): self.invoke('preflight')

    def test_resume_idempotence_and_caps(self):
        self.assertIn('V25_RUN_OK', self.invoke())
        con = sqlite3.connect(self.dest)
        first_count = con.execute('SELECT count(*) FROM articles').fetchone()[0]
        cursor1 = con.execute('SELECT last_rowid FROM category_tasks WHERE category_title=?',
                              ('Educational policy',)).fetchone()
        # Only actual category titles in the source (with underscore but auto names use spaces).
        self.assertTrue(first_count >= 2)
        self.assertIsNotNone(cursor1)
        con.close()
        self.invoke('run', '--max-batches', '10')
        con = sqlite3.connect(self.dest)
        count = con.execute('SELECT count(*) FROM articles').fetchone()[0]
        self.assertGreater(count, first_count)
        self.assertEqual(con.execute('SELECT count(*) FROM articles WHERE page_id=4').fetchone()[0], 0)
        self.assertEqual(con.execute('SELECT count(*) FROM category_tasks WHERE state=?', ('CAPPED',)).fetchone()[0], 1)
        nassign = con.execute('SELECT count(*) FROM assignments').fetchone()[0]
        con.close()
        self.invoke('run', '--max-batches', '10')
        con = sqlite3.connect(self.dest)
        self.assertEqual(con.execute('SELECT count(*) FROM assignments').fetchone()[0], nassign)
        self.assertEqual(con.execute('SELECT count(*) FROM articles').fetchone()[0], count)
        self.assertEqual(con.execute('SELECT count(*) FROM branch_concepts').fetchone()[0], 2)
        con.close()

    def test_multi_branches_shared_articles_no_double_global_records(self):
        self.invoke('run', '--max-batches', '10')
        second = self.create_branch('unesco.mt1.11.test')
        self.invoke('run', '--max-batches', '10', branches=[self.branch, second])
        con = sqlite3.connect(self.dest)
        self.assertEqual(con.execute('SELECT count(*) FROM branches').fetchone()[0], 2)
        self.assertEqual(con.execute('SELECT count(*) FROM branch_concepts').fetchone()[0], 4)
        articles_count = con.execute('SELECT count(*) FROM articles').fetchone()[0]
        union_count = con.execute('SELECT count(DISTINCT page_id) FROM assignments').fetchone()[0]
        self.assertEqual(articles_count, union_count)
        self.assertEqual(con.execute('SELECT count(*) FROM assignments WHERE page_id=1').fetchone()[0], 4)
        con.close()
        self.assertIn('V25_SNAPSHOT_OK', self.invoke('verify', branches=[self.branch, second]))

    def test_source_drift_and_branch_edit_refused(self):
        self.invoke()
        con = sqlite3.connect(self.source)
        con.execute('UPDATE wiki_pages SET title=? WHERE page_id=2', ('Modified',))
        con.commit();con.close()
        with self.assertRaises(m.Refusal): self.invoke()

    def test_branch_modified_refused(self):
        self.invoke()
        cfg = json.loads(self.branch.read_text())
        cfg['branch_version'] = 'changed'
        self.branch.write_text(json.dumps(cfg))
        with self.assertRaises(m.Refusal): self.invoke()

    def test_output_integrity_and_candidate_status(self):
        self.invoke()
        latest = m.read_json(self.out / 'LATEST.json')
        snap = self.out / latest['snapshot']
        rep = m.read_json(snap / 'RAPPORT_V25.json')
        self.assertFalse(rep['publication_authorized'])
        self.assertEqual(rep['canonical_admissions'], 0)
        self.assertTrue((snap / 'EXPORT_V25_POUR_CHATGPT.zip').is_file())
        (snap / 'reader_fr' / 'index.html').write_text('altered', encoding='utf-8')
        with self.assertRaises(m.Refusal): self.invoke('verify')

    def test_extend_capped_task_resumes_at_saved_cursor(self):
        self.invoke('run', '--max-batches', '10')
        db = m.open_catalog(self.dest)
        old = db.execute("SELECT last_rowid,members_seen FROM category_tasks WHERE state='CAPPED'").fetchone()
        self.assertEqual(old['members_seen'], 30)
        ans = m.expand_limits(db, 'unesco.mt1.10.test', 80, 200)
        self.assertEqual(ans['capped_tasks_reopened'], 1)
        restored = db.execute("SELECT last_rowid,members_seen FROM category_tasks WHERE state='PENDING' AND category_title='Educational policy'").fetchone()
        self.assertEqual(old['last_rowid'], restored['last_rowid'])
        db.close()
        self.invoke('run', '--max-batches', '10')
        db = sqlite3.connect(self.dest)
        self.assertEqual(db.execute("SELECT members_seen FROM category_tasks WHERE category_title='Educational policy'").fetchone()[0], 43)
        self.assertEqual(db.execute("SELECT count(*) FROM articles WHERE page_id BETWEEN 10 AND 49").fetchone()[0], 40)
        db.close()

    def test_category_bridge_suggestions_are_review_only(self):
        self.invoke('run', '--max-batches', '10')
        con = sqlite3.connect(self.dest)
        found = con.execute('SELECT count(*) FROM category_suggestions').fetchone()[0]
        self.assertGreater(found, 0)
        self.assertEqual(con.execute("SELECT count(*) FROM category_suggestions WHERE review_state='TO_REVIEW'").fetchone()[0], found)
        con.close()
        latest = m.read_json(self.out / 'LATEST.json')
        p = self.out / latest['snapshot'] / 'PONTS_A_REVOIR_V25.csv'
        self.assertTrue(p.is_file())

    def test_semantic_batch_staging_is_paginated_and_immutable(self):
        self.invoke('run', '--max-batches', '10')
        db = m.open_catalog(self.dest)
        one = m.export_semantic_batch(db, self.out, 'unesco.mt1.10.test', 0, 5)
        self.assertEqual(one['records'], 5)
        self.assertFalse(json.loads(Path(one['file']).read_text().splitlines()[0])['status'] == 'CANONICAL')
        rows = [json.loads(line) for line in Path(one['file']).read_text().splitlines()]
        self.assertEqual(len({x['page_id'] for x in rows}), 5)
        self.assertGreaterEqual(len(rows[0]['concept_assignments']), 1)
        two = m.export_semantic_batch(db, self.out, 'unesco.mt1.10.test', one['next_after_page_id'], 5)
        self.assertLess(max(x['page_id'] for x in rows), two['next_after_page_id'])
        self.assertEqual(m.export_semantic_batch(db, self.out, 'unesco.mt1.10.test', 0, 5)['file'], one['file'])
        Path(one['file']).write_text('corrupted', encoding='utf-8')
        with self.assertRaises(m.Refusal):
            m.export_semantic_batch(db, self.out, 'unesco.mt1.10.test', 0, 5)
        db.close()

    def test_unrelated_catalogue_is_never_modified(self):
        x = sqlite3.connect(self.dest)
        x.execute('CREATE TABLE important(x)');x.commit();x.close()
        with self.assertRaises(m.Refusal): self.invoke()
        x = sqlite3.connect(self.dest)
        self.assertEqual(x.execute("SELECT count(*) FROM sqlite_master WHERE name='important'").fetchone()[0], 1)
        self.assertEqual(x.execute("SELECT count(*) FROM sqlite_master WHERE name='meta'").fetchone()[0], 0)
        x.close()

    def test_refuses_same_source_and_target(self):
        with self.assertRaises(m.Refusal):
            self.invoke('run', '--catalogue-db', str(self.source))

    def test_generator_partitions_according_to_provided_source_only(self):
        from generer_branches_unesco_v25 import run
        data = json.loads(self.concepts.read_text())
        data['concepts'][0]['microthesaurus_ids'] = ['mt1.10','mt1.11']
        data['concepts'][1]['microthesaurus_ids'] = ['mt1.10']
        self.concepts.write_text(json.dumps(data), encoding='utf-8')
        dest = self.root / 'generated_branches'
        result = run(self.concepts, dest, 'test2026')
        self.assertEqual(len(result['branches']), 2)
        self.assertTrue((dest/'branche_mt1_10.json').is_file())
        with self.assertRaises(ValueError): run(self.concepts, dest, 'test2026')

    def test_reviewed_bridge_requires_justification_and_is_separate(self):
        self.bridges.write_text('concept_id,category_title,status,justification,depth_limit\n'
                                'concept9,Teacher policy,ACTIVE_REVIEWED_AI,Classification humaine revue avec sources,1\n',
                                encoding='utf-8')
        b = m.load_branch(self.branch)
        self.assertEqual(len(b['bridges']), 1)
        self.invoke('run', '--max-batches', '10')
        con = sqlite3.connect(self.dest)
        self.assertGreater(con.execute("SELECT count(*) FROM category_tasks WHERE kind='AI_REVIEWED_BRIDGE_CANDIDATE'").fetchone()[0], 0)
        con.close()


if __name__ == '__main__':
    unittest.main()
