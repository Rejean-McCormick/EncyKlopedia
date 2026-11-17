"""Tests du triage conservateur des trois index UNESCO (données synthétiques)."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sqlite3
import unittest

import encyk_triage_v314 as triage
import encyk_global_v313 as monitor


class TriageTests(unittest.TestCase):
    def setUp(self):
        t=TemporaryDirectory();self.addCleanup(t.cleanup)
        d=Path(t.name)
        self.paths={k:d/(k+'.sqlite') for k in ('station','catalogue','decouverte')}
        self.output=d/'resultats'
        schemas={
          'catalogue': '''
             CREATE TABLE branch_concepts(branch_id TEXT,vocabulary TEXT,concept_id TEXT);
             INSERT INTO branch_concepts VALUES('unesco.mt1.10','UNESCO','C1');
             INSERT INTO branch_concepts VALUES('unesco.mt1.10','UNESCO','C2');
             CREATE TABLE concepts(vocabulary TEXT,concept_id TEXT,label_fr TEXT,label_en TEXT);
             INSERT INTO concepts VALUES('UNESCO','C1','Politique éducative','Education policy');
             INSERT INTO concepts VALUES('UNESCO','C2','Pédagogie','Pedagogy');
             CREATE TABLE assignments(branch_id TEXT,wiki TEXT,concept_id TEXT,page_id INTEGER);
             INSERT INTO assignments VALUES('unesco.mt1.10','enwiki','C1',200);
             CREATE TABLE reviewed_article_links_v28(branch_id TEXT,concept_id TEXT,page_id INTEGER,
                candidate_id TEXT,evidence_sha256 TEXT,decision TEXT);
             INSERT INTO reviewed_article_links_v28 VALUES('unesco.mt1.10','C1',100,'id100','abc','APPROVE');
             INSERT INTO reviewed_article_links_v28 VALUES('unesco.mt1.10','C1',101,'id101','catalogue_sha','REJECT');
          ''',
          'decouverte': '''
             CREATE TABLE candidates(branch_id TEXT,concept_id TEXT,page_id INTEGER,title TEXT);
             INSERT INTO candidates VALUES('unesco.mt1.10','C1',100,'Déjà approuvé');
             INSERT INTO candidates VALUES('unesco.mt1.10','C1',101,'Empreinte à comparer');
             INSERT INTO candidates VALUES('unesco.mt1.10','C1',200,'Affectation historique');
             INSERT INTO candidates VALUES('unesco.mt1.10','C2',300,'Nouveau sujet');
             INSERT INTO candidates VALUES('une.autre','C2',555,'Autre branche ignorée');
          ''',
          'station': '''
             CREATE TABLE review_index(branch_id TEXT,concept_id TEXT,page_id INTEGER,
                candidate_id TEXT,state TEXT,evidence_sha256 TEXT,title TEXT);
             INSERT INTO review_index VALUES('unesco.mt1.10','C1',100,'id100','DECIDED','abc','Déjà approuvé');
             INSERT INTO review_index VALUES('unesco.mt1.10','C1',101,'id_different','HOLD','station_sha','A vérifier');
          '''
        }
        for k,script in schemas.items():
            with sqlite3.connect(self.paths[k]) as con:con.executescript(script)
        self.before={k:p.read_bytes() for k,p in self.paths.items()}

    def test_classify_missing_without_fabricating_identifiers(self):
        r=triage.analyse(self.paths)
        c=r['comptages']
        self.assertTrue(c['comparaison_complete'])
        self.assertEqual(c['paires_decouvertes'],4)
        self.assertEqual(c['absents_station_et_registre_decisions'],2)
        self.assertEqual(c['absents_mais_affectation_historique'],1)
        self.assertEqual(c['absents_sans_affectation_historique'],1)
        self.assertEqual(c['empreintes_divergentes'],1)
        self.assertEqual(c['identifiants_divergents'],1)
        self.assertEqual(c['hold_station'],1)
        self.assertEqual(c['concepts_configures_sans_approve'],1)
        self.assertIsNone(r['achevement_reel_pct'])
        self.assertEqual(len(r['candidats_ecarts']),2)
        self.assertTrue(all(not x['candidate_id'] and not x['evidence_sha256'] for x in r['candidats_ecarts']))
        for k,p in self.paths.items():self.assertEqual(self.before[k],p.read_bytes())

    def test_export_isolation_and_json_private_free(self):
        r=triage.analyse(self.paths)
        files=triage.exporter(self.output,r,lambda p,b:p.parent.mkdir(exist_ok=True,parents=True) or p.write_bytes(b))
        self.assertEqual(len(files),3)
        saved=json.loads(files[0].read_text())
        self.assertEqual(saved['comptages']['absents_station_et_registre_decisions'],2)
        self.assertNotIn('SECRET_',files[0].read_text())
        for k,p in self.paths.items():self.assertEqual(self.before[k],p.read_bytes())
        with self.assertRaises(ValueError):triage.exporter(self.paths['station'].parent,r,lambda p,b:p.write_bytes(b))

    def test_missing_sql_source_never_claims_zero_issues(self):
        self.paths['catalogue'].unlink()
        r=triage.analyse(self.paths)
        self.assertFalse(r['comptages']['comparaison_complete'])
        self.assertNotIn('absents_station_et_registre_decisions',r['comptages'])

    def test_sqlite_query_only(self):
        with monitor.open_ro(self.paths['station']) as con:
            with self.assertRaises(sqlite3.OperationalError):con.execute('DELETE FROM review_index')


if __name__=='__main__':unittest.main()
