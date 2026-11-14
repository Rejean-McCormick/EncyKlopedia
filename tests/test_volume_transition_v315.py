"""v31.5: persistent-queue telemetry and conservative global backpressure."""
import importlib.util
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
TOOL=ROOT/'tools'/'unesco_pilot'
sys.path.insert(0,str(TOOL))
spec=importlib.util.spec_from_file_location('station_v315',TOOL/'poste_chatgpt_v30.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
import routage_branches_v311 as branches

class VolumeTransitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        base=Path(self.tmp.name)
        self.s=module.Station(ROOT,base/'station',base/'v27',base/'v28',base/'catalogue.sqlite')
        self.addCleanup(self.s.db.close)
        self.branch={'id':'unesco.mt1.10','concepts':[{'unesco_id':'ed'}]}
        self.cid='candidate-001'
        class V25:
            DEFAULT_BRANCH=Path('unused.json')
            load_branch=lambda _,_path:self.branch
            label=lambda _,_c,_lang:'Educational policy'
            meta=lambda _,_con,_key:'36'
        def build(_,row,_label):
            return {'candidate_id':self.cid,'branch_id':row['branch_id'],
                    'concept_id':row['concept_id'],'page_id':row['page_id'],'title':row['title'],
                    'concept_en':'Educational policy','priority':71,'seed_count':1,'links':1,'shared':0,'subs':0,
                    'evidence_sha256':'b'*64,'examples':'Verified link metadata'}
        self.s._v28_engine=lambda: SimpleNamespace(v25=V25(),build_candidate=build)
        stage=self.s.v28/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        self.s.v28.mkdir(exist_ok=True)
        with sqlite3.connect(stage) as db:
            db.execute('CREATE TABLE candidates(branch_id TEXT,concept_id TEXT,page_id INTEGER,title TEXT)')
            db.execute('INSERT INTO candidates VALUES(?,?,?,?)',(self.branch['id'],'ed',11,'Test school'))
        with self.s.db:
            self.s.db.execute('''INSERT INTO review_index(candidate_id,branch_id,concept_id,page_id,
               title,priority,seed_count,link_evidence,category_evidence,subcategory_evidence,
               state,last_seen_utc) VALUES(?,?,?,?,?,?,?,?,?,?,'PENDING',?)''',
               (self.cid,self.branch['id'],'ed',11,'Test school',71,1,1,0,0,module.now()))
    def job(self,jid,kind='v28',n=110,status='READY',route=False,finished=None,sent=None):
        with self.s.db:
            self.s.db.execute('''INSERT INTO jobs(id,kind,key,count,status,source_path,source_sha256,
                bundle_path,bundle_sha256,created_utc,sent_utc,finished_utc)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                (jid,kind,jid,n,status,'historic/source.csv','7'*64,'historic/bundle.zip','8'*64,
                 module.now(),sent,finished))
            if route:
                self.s.db.execute('''INSERT INTO v311_job_routes(job_id,branch_id,manifest_path,stage_path,work_path,branch_signature)
                    VALUES(?,?,?,?,?,?)''',(jid,'second.branch','historic.json','historic.db','historic','old-signature'))
    def test_four_ready_are_identified_by_kind_and_size(self):
        self.job('u_small',n=110)
        self.job('u_large',n=880,status='SENT')
        self.job('k_small',kind='v27',n=2)
        self.job('k_large',kind='v27',n=24)
        start=datetime(2026,11,14,12,0,tzinfo=timezone.utc)
        self.job('u_done',n=880,status='DONE',sent=start.isoformat(),finished=(start+timedelta(minutes=25)).isoformat())
        before=[tuple(x) for x in self.s.db.execute('SELECT id,status,source_sha256 FROM jobs ORDER BY id')]
        diag=self.s.snapshot()['volume_v315']
        self.assertEqual(diag['ready_par_type'],{'v28':1,'v27':2})
        self.assertEqual(diag['unesco_par_taille']['petits_300_ou_moins'],1)
        self.assertEqual(diag['unesco_par_taille']['volume_650_880'],1)
        self.assertEqual(diag['kristal_ouverts'],2)
        self.assertEqual(diag['delai_transfert_import_minutes']['mediane'],25.0)
        self.assertEqual(diag['delai_par_format_minutes']['unesco_650_880']['mediane'],25.0)
        self.assertEqual(before,[tuple(x) for x in self.s.db.execute('SELECT id,status,source_sha256 FROM jobs ORDER BY id')])
    def test_full_secondary_buffer_never_adds_legacy_pack(self):
        for i in range(module.QUEUE_BUFFER):self.job(f'b{i:03}',route=True)
        with patch.object(branches,'live',return_value=[{'branch':{'id':'second.branch'}}]):
            self.assertEqual(self.s._prepare_v28(),0)
            self.assertEqual(self.s._prepare_v28(allow_fallback=True),0)
        self.assertEqual(self.s._open_review_count(),module.QUEUE_BUFFER)
        self.assertEqual(self.s.db.execute("SELECT state FROM review_index WHERE candidate_id=?",(self.cid,)).fetchone()[0],'PENDING')
    def test_fallback_uses_one_spare_slot_without_touching_old_work(self):
        for i in range(module.QUEUE_BUFFER-1):self.job(f'b{i:03}',route=True)
        old={r['id']:r['source_sha256'] for r in self.s.db.execute('SELECT * FROM jobs')}
        with patch.object(branches,'live',return_value=[{'branch':{'id':'second.branch'}}]):
            self.assertEqual(self.s._prepare_v28(allow_fallback=True),1)
        self.assertEqual(self.s._open_review_count(),module.QUEUE_BUFFER)
        self.assertEqual(self.s.db.execute("SELECT state FROM review_index WHERE candidate_id=?",(self.cid,)).fetchone()[0],'QUEUED')
        for jid,digest in old.items():self.assertEqual(self.s._row(jid)['source_sha256'],digest)
        fresh=self.s.db.execute("SELECT * FROM jobs WHERE id LIKE 'v28_%' AND kind='v28'").fetchone()
        self.assertEqual(fresh['count'],1)
        self.assertTrue(Path(fresh['bundle_path']).is_file())
    def test_first_pass_reserves_space_for_secondary_branch(self):
        for i in range(module.QUEUE_BUFFER//2):self.job(f'legacy{i:03}')
        with patch.object(branches,'live',return_value=[{'branch':{'id':'second.branch'}}]):
            self.assertEqual(self.s._prepare_v28(),0)
        self.assertEqual(self.s._open_review_count(),module.QUEUE_BUFFER//2)
    def test_consolidated_transfer_is_non_destructive_and_keeps_nested_zips(self):
        self.job('small_a',n=110)
        self.job('small_b',n=300)
        self.job('large_c',n=880)
        sample={}
        for jid in ('small_a','small_b'):
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w') as z:z.writestr('REVUE_'+jid+'.csv','candidate_id,decision,justification\n')
            p=self.s.work/(jid+'.zip');p.write_bytes(out.getvalue());sample[jid]=p.read_bytes()
        self.s.bundle=lambda jid:self.s.work/(jid+'.zip')
        before=[tuple(r) for r in self.s.db.execute('SELECT id,status,source_sha256,bundle_sha256 FROM jobs ORDER BY id')]
        name,raw=self.s.dispatch_small_v315()
        self.assertTrue(name.startswith('TRANSFERT_MULTI_V28_'))
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertEqual(z.testzip(),None)
            manifest=json.loads(z.read('MANIFEST_TRANSFERT_MULTI_V315.json'))
            self.assertEqual(manifest['count'],410)
            self.assertEqual(len(manifest['tasks']),2)
            for jid,content in sample.items():self.assertEqual(z.read('PACKS/'+jid+'.zip'),content)
            msg=z.read('INSTRUCTIONS_TRANSFERT_MULTI_V315.txt').decode()
            self.assertIn('DECISIONS_small_a.csv',msg)
            self.assertIn('DECISIONS_small_b.csv',msg)
        after=[tuple(r) for r in self.s.db.execute('SELECT id,status,source_sha256,bundle_sha256 FROM jobs ORDER BY id')]
        self.assertEqual(before,after)

    def test_consolidated_transfer_requires_two_unsent_small_jobs(self):
        self.job('small_a',n=110)
        self.job('small_b',n=110,status='SENT')
        self.assertFalse(self.s.volume_v315()['transfert_groupe']['possible'])
        with self.assertRaisesRegex(ValueError,'Au moins deux'):
            self.s.dispatch_small_v315()

    def test_zero_sent_timestamp_does_not_invent_ai_duration(self):
        self.job('unknown',status='DONE',n=880)
        self.assertIsNone(self.s.volume_v315()['delai_transfert_import_minutes']['mediane'])

if __name__=='__main__':unittest.main()
