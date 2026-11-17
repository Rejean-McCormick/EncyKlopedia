"""Tests synthétiques du centre EncyKlopedia v31.3 (aucune base réelle)."""
from __future__ import annotations

import importlib.machinery
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import encyk_global_v313 as glob

SCRIPT = Path(__file__).with_name('CENTRE_PILOTAGE_ENCYK_V313.pyw')
loader=importlib.machinery.SourceFileLoader('encyk_pilotage_v313',str(SCRIPT))
spec=importlib.util.spec_from_loader(loader.name,loader)
app=importlib.util.module_from_spec(spec)
loader.exec_module(app)


class TestCentrePilotage(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        root=Path(t.name)
        self.paths={k:root/(k+'.sqlite') for k in glob.DEFAULT_PATHS}
        self.reports=root/'rapports'
        self.branch='unesco.mt1.10'
        def init(name, script):
            c=sqlite3.connect(self.paths[name])
            try:c.executescript(script);c.commit()
            finally:c.close()
        init('station','''
            CREATE TABLE jobs(id TEXT,kind TEXT,status TEXT);
            INSERT INTO jobs VALUES('u1','v28','DONE');
            INSERT INTO jobs VALUES('u2','v28','READY');
            INSERT INTO jobs VALUES('k1','v27','DONE');
            CREATE TABLE v311_job_routes(job_id TEXT,branch_id TEXT);
            CREATE TABLE lanes(lane INTEGER,job_id TEXT);
            INSERT INTO lanes VALUES(0,'u2');
            CREATE TABLE receipts(id TEXT);
            INSERT INTO receipts VALUES('receipt');
            CREATE TABLE review_index(branch_id TEXT,concept_id TEXT,page_id INTEGER,
                candidate_id TEXT,title TEXT,state TEXT,priority INTEGER,seed_count INTEGER,
                link_evidence INTEGER,category_evidence INTEGER,subcategory_evidence INTEGER,
                task_id TEXT,evidence_sha256 TEXT,last_seen_utc TEXT);
            INSERT INTO review_index VALUES('unesco.mt1.10','C1',1,'id1','A','DECIDED',70,1,1,0,0,'u1',
                'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','2026-11-14');
            INSERT INTO review_index VALUES('unesco.mt1.10','C2',2,'id2','B','HOLD',40,1,1,0,0,'u1',
                'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb','2026-11-14');
        ''')
        init('catalogue','''
            CREATE TABLE articles(page_id INTEGER);
            INSERT INTO articles VALUES(1);
            CREATE TABLE branch_concepts(branch_id TEXT,vocabulary TEXT,concept_id TEXT);
            INSERT INTO branch_concepts VALUES('unesco.mt1.10','u','C1');
            INSERT INTO branch_concepts VALUES('unesco.mt1.10','u','C2');
            CREATE TABLE concepts(vocabulary TEXT,concept_id TEXT,label_fr TEXT,label_en TEXT);
            INSERT INTO concepts VALUES('u','C1','Éducation','Education');
            INSERT INTO concepts VALUES('u','C2','Compétences','Skills');
            CREATE TABLE assignments(branch_id TEXT,wiki TEXT,concept_id TEXT,page_id INTEGER);
            INSERT INTO assignments VALUES('unesco.mt1.10','enwiki','C1',1);
            CREATE TABLE reviewed_article_links_v28(branch_id TEXT,concept_id TEXT,page_id INTEGER,
                candidate_id TEXT,evidence_sha256 TEXT,decision TEXT);
            INSERT INTO reviewed_article_links_v28 VALUES('unesco.mt1.10','C1',1,'id1',
                'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','APPROVE');
        ''')
        init('decouverte','''
            CREATE TABLE candidates(branch_id TEXT,concept_id TEXT,page_id INTEGER,title TEXT,first_seen TEXT);
            INSERT INTO candidates VALUES('unesco.mt1.10','C1',1,'A','2026-11-14');
            INSERT INTO candidates VALUES('unesco.mt1.10','C2',2,'B','2026-11-14');
            INSERT INTO candidates VALUES('unesco.mt1.10','C2',3,'C','2026-11-14');
            CREATE TABLE seed_queue(branch_id TEXT,state TEXT);
            INSERT INTO seed_queue VALUES('unesco.mt1.10','DONE');
        ''')
        init('kristal','''
            CREATE TABLE claims(claim_key TEXT,statement_en TEXT,source_status TEXT);
            INSERT INTO claims VALUES('private1','SECRET_PRIVATE_SOURCE_QUOTE','PRIVATE');
            CREATE TABLE citations(claim_key TEXT,source_quote TEXT);
            INSERT INTO citations VALUES('private1','SECRET_PRIVATE_SOURCE_QUOTE');
            CREATE TABLE article_visits(page_id INTEGER);
            INSERT INTO article_visits VALUES(1);
            CREATE TABLE delta_imports(pack_id TEXT,payload_json TEXT);
            INSERT INTO delta_imports VALUES('p1','SECRET_PRIVATE_SOURCE_QUOTE');
        ''')
        init('packs','''
            CREATE TABLE packs(pack_id TEXT);
            INSERT INTO packs VALUES('p1');
            CREATE TABLE queue(page_id INTEGER,state TEXT);
            INSERT INTO queue VALUES(1,'DONE');
            CREATE TABLE source_epoch_history(id INTEGER);
        ''')
        self.before={k:v.read_bytes() for k,v in self.paths.items()}

    def test_collect_global_and_branch(self):
        result,concepts,actions,samples,discovered=app.collect(self.paths,self.branch)
        self.assertEqual(result['global']['station']['jobs_total'],3)
        self.assertEqual(result['global']['station']['jobs_ready'],1)
        self.assertEqual(result['global']['station']['revue_etats']['HOLD'],1)
        self.assertEqual(result['global']['kristal_prive']['claims'],1)
        self.assertEqual(result['global']['kristal_prive']['citations'],1)
        self.assertEqual(result['global']['packs_kristal']['packs_prepares'],1)
        self.assertEqual(result['branche']['rapprochement']['paires_decouvertes_absentes_station_et_catalogue'],1)
        self.assertEqual(result['branche']['rapprochement']['concepts_configures_sans_approve'],1)
        self.assertIsNone(result['global']['achevement_reel_pct'])
        self.assertIsNone(result['branche']['achevement_reel_pct'])
        self.assertEqual(len(concepts),2)
        self.assertEqual(len(discovered),3)
        for k,p in self.paths.items():self.assertEqual(p.read_bytes(),self.before[k])

    def test_export_works_and_keeps_private_text_out(self):
        result,concepts,actions,samples,discovered=app.collect(self.paths,self.branch)
        reports=app.export_reports(self.reports,result,concepts,actions,samples,discovered)
        self.assertEqual(len(reports),5)
        self.assertTrue(all(p.is_file() for p in reports))
        summary=json.loads(reports[0].read_text(encoding='utf-8'))
        self.assertEqual(summary['global']['kristal_prive']['claims'],1)
        self.assertNotIn('SECRET_PRIVATE_SOURCE_QUOTE',reports[0].read_text(encoding='utf-8'))
        self.assertNotIn('SECRET_PRIVATE_SOURCE_QUOTE',''.join(p.read_text(encoding='utf-8-sig') for p in reports if p.suffix=='.csv'))
        for k,p in self.paths.items():self.assertEqual(p.read_bytes(),self.before[k])

    def test_missing_private_database_is_not_zero(self):
        self.paths['kristal'].unlink()
        result,*_=app.collect(self.paths,self.branch)
        self.assertFalse(result['global']['sources']['kristal']['available'])
        self.assertNotIn('claims',result['global']['kristal_prive'])
        self.assertTrue(any('SOURCE_ABSENTE:kristal' in x for x in result['global']['alertes']))

    def test_invalid_export_into_production_db_folder(self):
        result,concepts,actions,samples,discovered=app.collect(self.paths,self.branch)
        self.assertRaises(ValueError,app.export_reports,self.paths['station'].parent,result,
                          concepts,actions,samples,discovered)

    def test_sqlite_ro_rejects_update(self):
        with glob.open_ro(self.paths['station']) as con:
            with self.assertRaises(sqlite3.OperationalError):con.execute('UPDATE jobs SET status=?', ('DONE',))
        self.assertEqual(self.paths['station'].read_bytes(),self.before['station'])


if __name__ == '__main__':unittest.main()
