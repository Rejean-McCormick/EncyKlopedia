"""Autotests sans Tk, avec bases SQLite synthétiques, lecture seule."""
import importlib.machinery
import importlib.util
import json
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
import sys

SCRIPT = Path(__file__).with_name('AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw')
loader=importlib.machinery.SourceFileLoader('encyk_auto',str(SCRIPT))
spec=importlib.util.spec_from_loader(loader.name,loader)
m=importlib.util.module_from_spec(spec)
loader.exec_module(m)


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d=Path(self.tmp.name)
        self.paths={k:d/(k+'.sqlite') for k in ('station','catalogue','decouverte')}
        self.out=d/'rapports'
        self.args=SimpleNamespace(branche='unesco.mt1.10',**self.paths)
        con=sqlite3.connect(self.paths['catalogue'])
        con.executescript('''
            CREATE TABLE branch_concepts(branch_id TEXT,vocabulary TEXT,concept_id TEXT);
            CREATE TABLE concepts(vocabulary TEXT,concept_id TEXT,label_fr TEXT,label_en TEXT);
            CREATE TABLE assignments(branch_id TEXT,wiki TEXT,concept_id TEXT,page_id INTEGER);
            CREATE TABLE reviewed_article_links_v28(branch_id TEXT,concept_id TEXT,page_id INTEGER,
                candidate_id TEXT,evidence_sha256 TEXT,decision TEXT);
            INSERT INTO branch_concepts VALUES('unesco.mt1.10','UNESCO','C1');
            INSERT INTO branch_concepts VALUES('unesco.mt1.10','UNESCO','C2');
            INSERT INTO concepts VALUES('UNESCO','C1','Politique éducative','Education policy');
            INSERT INTO concepts VALUES('UNESCO','C2','Pédagogie','Pedagogy');
            INSERT INTO assignments VALUES('unesco.mt1.10','enwiki','C1',100);
            INSERT INTO reviewed_article_links_v28 VALUES('unesco.mt1.10','C1',100,'cand100',
                 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','APPROVE');
            INSERT INTO reviewed_article_links_v28 VALUES('unesco.mt1.10','C1',101,'cand101',
                 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb','REJECT');
        ''')
        con.commit();con.close()
        con=sqlite3.connect(self.paths['decouverte'])
        con.executescript('''
            CREATE TABLE candidates(branch_id TEXT,concept_id TEXT,page_id INTEGER,title TEXT,first_seen TEXT);
            CREATE TABLE seed_queue(branch_id TEXT,state TEXT);
            INSERT INTO candidates VALUES('unesco.mt1.10','C1',100,'Article déjà approuvé','2026-11-13');
            INSERT INTO candidates VALUES('unesco.mt1.10','C1',101,'Article rejeté','2026-11-13');
            INSERT INTO candidates VALUES('unesco.mt1.10','C2',102,'Article HOLD','2026-11-13');
            INSERT INTO candidates VALUES('unesco.mt1.10','C2',103,'Article jamais suivi','2026-11-13');
            INSERT INTO seed_queue VALUES('unesco.mt1.10','DONE');
        ''')
        con.commit();con.close()
        con=sqlite3.connect(self.paths['station'])
        con.executescript('''
            CREATE TABLE review_index(branch_id TEXT,concept_id TEXT,page_id INTEGER,candidate_id TEXT,title TEXT,
                state TEXT,priority INTEGER,seed_count INTEGER,link_evidence INTEGER,category_evidence INTEGER,
                subcategory_evidence INTEGER,task_id TEXT,evidence_sha256 TEXT,last_seen_utc TEXT);
            CREATE TABLE jobs(id TEXT,kind TEXT,status TEXT);
            CREATE TABLE v311_job_routes(job_id TEXT,branch_id TEXT);
            INSERT INTO review_index VALUES('unesco.mt1.10','C1',100,'cand100','Article déjà approuvé',
                'DECIDED',70,1,1,1,0,'j0','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa','2026-11-14');
            INSERT INTO review_index VALUES('unesco.mt1.10','C2',102,'cand102','Article HOLD',
                'HOLD',50,1,1,0,0,'j1','cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc','2026-11-14');
            INSERT INTO jobs VALUES('j0','v28','DONE');
            INSERT INTO jobs VALUES('j1','v28','DONE');
        ''')
        con.commit();con.close()
        self.before={k:p.read_bytes() for k,p in self.paths.items()}

    def test_reconciliation_and_export(self):
        report,concepts,actions,paths,summary=m.run_automatic(self.args,self.out)
        self.assertEqual(report['rapprochement']['paires_decouvertes'],4)
        self.assertEqual(report['rapprochement']['paires_decouvertes_absentes_station_et_catalogue'],1)
        self.assertEqual(report['rapprochement']['paires_station_hold'],1)
        self.assertEqual(report['rapprochement']['concepts_configures_sans_approve'],1)
        self.assertEqual(report['rapprochement']['paires_decidees_catalogue'],2)
        self.assertIsNone(report['achevement_reel_pct'])
        self.assertEqual(len(concepts),2)
        self.assertTrue(any(r['type']=='DECOUVERT_NON_SUIVI' and r['page_id']==103 for r in actions))
        self.assertTrue(any(r['type']=='HOLD_A_REVOIR' and r['page_id']==102 for r in actions))
        self.assertEqual(len(paths),4)
        self.assertTrue(all(p.exists() and p.stat().st_size>20 for p in paths))
        self.assertEqual(report['evolution']['nouveaux_candidats_depuis_precedent'],None)
        for k,p in self.paths.items():self.assertEqual(p.read_bytes(),self.before[k],k)

    def test_diff_does_not_fake_saturation(self):
        r1,*_=m.run_automatic(self.args,self.out)
        r2,*_=m.run_automatic(self.args,self.out)
        self.assertEqual(r2['evolution']['nouveaux_candidats_depuis_precedent'],0)
        self.assertFalse(r2['evolution']['cycle_de_decouverte_nouveau_observe'])
        self.assertIsNone(r2['evolution']['saturation_exploratoire_demontree'])
        self.assertEqual(r2['audit_auto']['preuve_de_saturation'],'NON_DEMONTREE')
        with sqlite3.connect(self.paths['decouverte']) as con:
            con.execute("INSERT INTO candidates VALUES ('unesco.mt1.10','C2',104,'Nouveau','2026-11-14')")
            con.execute("INSERT INTO seed_queue VALUES ('unesco.mt1.10','DONE')")
        r3,*_=m.run_automatic(self.args,self.out)
        self.assertEqual(r3['evolution']['nouveaux_candidats_depuis_precedent'],1)
        self.assertTrue(r3['evolution']['cycle_de_decouverte_nouveau_observe'])
        self.assertEqual(r3['evolution']['variation_graines_done'],1)
        self.assertIsNone(r3['achevement_reel_pct'])

    def test_source_missing_is_explicit(self):
        self.paths['station'].unlink()
        report,*_=m.run_automatic(self.args,self.out)
        self.assertFalse(report['sources']['station']['available'])
        self.assertIsNone(report['achevement_reel_pct'])
        self.assertTrue(report['avertissements'])

if __name__=='__main__':unittest.main()
