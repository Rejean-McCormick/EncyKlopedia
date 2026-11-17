"""v31.9 — diagnostic de capacité et découverte avant réexamen HOLD.

Synthetic only: temporary station DB, no production resources or real XML edited.
"""
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import sys

ROOT=Path(__file__).resolve().parents[1]
PILOT=ROOT/'tools'/'unesco_pilot'
sys.path.insert(0,str(PILOT))
spec=importlib.util.spec_from_file_location('station_v319_test',PILOT/'poste_chatgpt_v30.py')
station_mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(station_mod)
import routage_branches_v311

class PipelineV319Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        base=Path(self.temp.name)
        self.station=station_mod.Station(ROOT,base/'work',base/'v27',base/'v28',base/'cat.sqlite')
        self.addCleanup(self.station.db.close)

    def add_row(self,n,state='HOLD'):
        with self.station.db:
            self.station.db.execute('''INSERT INTO review_index(candidate_id,branch_id,concept_id,page_id,title,
                priority,seed_count,link_evidence,category_evidence,subcategory_evidence,state,
                task_id,evidence_sha256,last_seen_utc) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (f'V28_test_{n}','unesco.mt1.10','concept9',n,f'Test {n}',100-n,1,1,0,0,
                 state,'task-original' if state=='HOLD' else None,'old-frozen-proof' if state=='HOLD' else None,station_mod.now()))

    def add_open_job(self,status='READY'):
        with self.station.db:
            self.station.db.execute('''INSERT INTO jobs(id,kind,key,count,status,source_path,source_sha256,
                 bundle_path,bundle_sha256,created_utc) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                 ('v28_existing','v28','v28_existing',1,status,'frozen.csv','source-sha','frozen.zip','bundle-sha',station_mod.now()))

    def test_open_review_blocks_rearming_without_changes(self):
        self.add_row(1)
        self.add_open_job()
        with patch.object(self.station,'batch',side_effect=AssertionError('Must not run')):
            with self.assertRaisesRegex(ValueError,'Terminer les revues UNESCO ouvertes'):
                self.station.reopen_holds()
        row=self.station.db.execute('SELECT * FROM review_index WHERE page_id=1').fetchone()
        self.assertEqual((row['state'],row['task_id'],row['evidence_sha256']),
                         ('HOLD','task-original','old-frozen-proof'))
        self.assertEqual(self.station._row('v28_existing')['status'],'READY')

    def test_explicit_rearm_starts_discovery_before_packing(self):
        for i in range(1,4):self.add_row(i)
        actions=[]
        def spy_run(script,options):
            actions.append(script)
            if script=='PRODUIRE_KRISTALS_V27.ps1':return '"queue":{"PACKED":3}'
            return '"seeds_pending":0'
        self.station._run=spy_run
        self.station._prepare=lambda:actions.append('PREPARATION')
        self.station._v28_engine=lambda:None
        with patch.object(routage_branches_v311,'discover_other',return_value=[]):
            with patch.object(self.station,'batch',side_effect=lambda:self.station._batch()):
                result=self.station.reopen_holds(limit=2)
        self.assertEqual(result,{'reopened':2,'discovery_first':True})
        self.assertEqual(actions[:3],['PRODUIRE_KRISTALS_V27.ps1',
                                     'DECOUVRIR_ARTICLES_RELIES_V28.ps1','PREPARATION'])
        states=list(self.station.db.execute('SELECT state,task_id FROM review_index ORDER BY page_id'))
        self.assertEqual([r['state'] for r in states],['PENDING','PENDING','HOLD'])
        self.assertEqual([r['task_id'] for r in states],[None,None,'task-original'])

    def test_available_stock_is_not_discovery_scanned_count(self):
        for i,state in [(1,'PENDING'),(2,'DEFERRED'),(3,'HOLD'),(4,'DECIDED')]:self.add_row(i,state)
        diag=self.station.snapshot()['production_diagnostic']
        self.assertEqual(diag['unesco_preparable'],2)
        self.assertEqual((diag['unesco_pending'],diag['unesco_deferred'],diag['unesco_hold']),(1,1,1))
        self.assertEqual(diag['free_lanes'],10)
        self.assertEqual(diag['unesco_open'],0)
        self.assertFalse(diag['discovery_frozen'])
        self.add_open_job('SENT')
        diag=self.station.snapshot()['production_diagnostic']
        self.assertEqual(diag['unesco_open'],1)
        self.assertTrue(diag['discovery_frozen'])

    def test_fair_hold_rotation_retains_provenance_and_no_permanent_exclusion(self):
        self.add_row(1);self.add_row(2)
        with patch.object(self.station,'batch'):
            first=self.station.reopen_holds(limit=1)
            self.assertEqual(first['reopened'],1)
            r=self.station.db.execute('SELECT * FROM hold_reexaminations WHERE candidate_id=?',('V28_test_1',)).fetchone()
            self.assertEqual((r['attempts'],r['original_task_id'],r['original_evidence_sha256']),
                             (1,'task-original','old-frozen-proof'))
            # Simulate first result still HOLD; next click prioritizes another candidate.
            with self.station.db:
                self.station.db.execute("UPDATE review_index SET state='HOLD' WHERE page_id=1")
            self.station.reopen_holds(limit=1)
            self.assertEqual(self.station.db.execute('SELECT state FROM review_index WHERE page_id=2').fetchone()[0],'PENDING')
            # Once every HOLD has had a first pass, the first may be explicitly reopened again.
            with self.station.db:
                self.station.db.execute("UPDATE review_index SET state='HOLD' WHERE page_id=2")
            self.station.reopen_holds(limit=1)
            self.assertEqual(self.station.db.execute('SELECT state FROM review_index WHERE page_id=1').fetchone()[0],'PENDING')

    def test_rearm_no_hold_no_packs(self):
        with patch.object(self.station,'batch',side_effect=AssertionError('No batch needed')):
            self.assertEqual(self.station.reopen_holds(),{'reopened':0,'discovery_first':False})

    def test_ui_warns_and_disables_hold_during_freeze(self):
        js=(PILOT/'poste_chatgpt_v30.js').read_text(encoding='utf-8')
        html=(PILOT/'poste_chatgpt_v30.html').read_text(encoding='utf-8')
        self.assertIn('st.busy||st.v28_frozen||!',js)
        self.assertIn("st.jobs.WAITING||0",js)
        self.assertIn('production_diagnostic',js)
        self.assertIn('id="schedulingDiagnostic"',html)
        self.assertIn('Tâches non attribuées',html)

if __name__=='__main__':unittest.main(verbosity=2)
