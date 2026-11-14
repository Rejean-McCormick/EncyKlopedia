"""Non-destructive clipboard/preload regression suite; real Windows clipboard is not touched."""
from pathlib import Path
import hashlib
import importlib.util
import os
import sqlite3
import struct
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'/'unesco_pilot'))
from poste_chatgpt_v30 import Station, sha_path
from presse_papiers_windows_v3161 import clipboard_payloads

class PrechargementV3161Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.station=Station(ROOT,root/'work',root/'v27',root/'v28',root/'cat.sqlite')
        self.addCleanup(self.close_station)
        self.base=root
        self.data=root/'packs';self.data.mkdir()

    def close_station(self):
        self.station.stop_preload()
        self.station.db.close()

    def add_task(self,num,lane=None):
        jid=f'v27_PACK_V27_TEST{num:03d}'
        path=self.data/f'PACK_V27_TEST{num:03d}.zip'
        # The warmup is agnostic to internal ZIP structure; production bundle()
        # verifies the exact original ZIP SHA before allowing its transfer.
        path.write_bytes(b'PK\x03\x04'+bytes([num%256])*64)
        h=sha_path(path)
        with self.station.db:
            self.station.db.execute('''INSERT INTO jobs(
              id,kind,key,count,status,source_path,source_sha256,bundle_path,bundle_sha256,created_utc
              ) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                (jid,'v27',f'PACK_V27_TEST{num:03d}',1,'READY',str(path),h,str(path),h,'2026-11-14T00:00:00Z'))
            if lane is not None:
                self.station.db.execute('UPDATE lanes SET job_id=? WHERE lane=?',(jid,lane))
        return jid,path

    def wait_for(self,condition,timeout=3):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            if condition():return
            time.sleep(.02)
        self.fail('preload not completed in time')

    def test_prepares_all_ten_lanes_without_rewriting_tasks(self):
        ids=[self.add_task(i+1,i+1)[0] for i in range(10)]
        jobs_before=[tuple(r) for r in self.station.db.execute('SELECT id,status,source_sha256,bundle_sha256 FROM jobs ORDER BY id')]
        self.station.start_preload()
        self.wait_for(lambda:self.station.preload_status()['ready']==10)
        state=self.station.snapshot()
        self.assertEqual(state['preload']['total'],10)
        self.assertTrue(all(state['preload']['jobs'][j]=='READY' for j in ids))
        self.assertEqual(jobs_before,[tuple(r) for r in self.station.db.execute('SELECT id,status,source_sha256,bundle_sha256 FROM jobs ORDER BY id')])
        self.assertEqual(len(self.station._warm_entries),10)
        self.assertEqual(len(list((self.base/'work').glob('review_context_cache/*'))),0)

    def test_transfer_reuses_prepared_result_and_invalidates_tampered_original(self):
        jid,path=self.add_task(1,1)
        original=self.station.bundle
        calls=[]
        def count_bundle(j):calls.append(j);return original(j)
        self.station.bundle=count_bundle
        self.station.warm_current_lanes()
        self.assertEqual(calls,[jid])
        self.assertEqual(self.station.transfer_path(jid),path)
        self.assertEqual(self.station.transfer_path(jid),path)
        self.assertEqual(calls,[jid])
        # Modify without changing length and restore modification time to verify SHA guard.
        before=path.stat()
        path.write_bytes(b'PK\x03\x04'+b'X'*64)
        os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns))
        with self.assertRaisesRegex(ValueError,'Paquet source absent ou modifié'):
            self.station.transfer_path(jid)
        self.assertEqual(calls,[jid,jid])

    def test_already_ready_lane_does_not_wait_for_other_lane_enrichment(self):
        a,_=self.add_task(1,1)
        b,_=self.add_task(2,2)
        self.station.transfer_path(a)
        original=self.station.bundle
        entered=threading.Event();release=threading.Event();errors=[]
        def slow_bundle(jid):
            if jid==b:
                entered.set()
                if not release.wait(2):raise RuntimeError('test timeout')
            return original(jid)
        self.station.bundle=slow_bundle
        def run():
            try:self.station.transfer_path(b)
            except Exception as ex:errors.append(ex)
        th=threading.Thread(target=run);th.start()
        try:
            self.assertTrue(entered.wait(1),'Second task did not start')
            before=time.perf_counter();p=self.station.transfer_path(a)
            self.assertLess(time.perf_counter()-before,.2,'Ready lane blocked by a different preparation')
            self.assertTrue(p.is_file())
        finally:
            release.set();th.join(timeout=3)
        self.assertFalse(errors)

    def test_newly_assigned_lane_triggers_warmup_without_recreating_jobs(self):
        a,_=self.add_task(1,1)
        b,_=self.add_task(2)
        with self.station.db:self.station.db.execute("UPDATE jobs SET status='WAITING' WHERE id=?",(b,))
        self.station.start_preload()
        self.wait_for(lambda:self.station.preload_status()['jobs'].get(a)=='READY')
        with self.station.lock:
            with self.station.db:
                self.station.db.execute("UPDATE jobs SET status='DONE' WHERE id=?",(a,))
                self.station._fill_lanes()
        self.wait_for(lambda:self.station.preload_status()['jobs'].get(b)=='READY')
        self.assertEqual(self.station._row(a)['status'],'DONE')
        self.assertEqual(self.station._row(b)['status'],'READY')

    def test_unesco_preload_reuses_enrichment_until_provenance_changes(self):
        import zipfile
        jid='v28_test_review_123'
        source=self.base/'revue.csv';source.write_bytes(b'candidate_id,decision,justification\n')
        original=self.base/'revue_orig.zip'
        with zipfile.ZipFile(original,'w') as z:z.writestr('REVUE.csv',source.read_bytes())
        prepared=self.base/'revue_enrichie.zip'
        with self.station.db:
            self.station.db.execute("""INSERT INTO jobs(
                id,kind,key,count,status,source_path,source_sha256,bundle_path,bundle_sha256,created_utc
                ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (jid,'v28',jid,880,'READY',str(source),sha_path(source),
                 str(original),sha_path(original),'2026-11-14T00:00:00Z'))
            self.station.db.execute('UPDATE lanes SET job_id=? WHERE lane=1',(jid,))
        version=[1];builds=[]
        self.station._review_inputs=lambda _id:{'version':version[0]}
        def generate(j):
            builds.append(version[0])
            if sha_path(source)!=self.station.task(j)['source_sha256']:
                raise ValueError('Preuve originale modifiée')
            with zipfile.ZipFile(prepared,'w') as z:
                z.writestr('CONTEXTES_DOCUMENTAIRES_V28.jsonl','{"version":'+str(version[0])+'}\n')
            return prepared
        self.station.bundle=generate
        self.station.warm_current_lanes()
        self.assertEqual(self.station.transfer_path(jid),prepared)
        self.assertEqual(self.station.transfer_path(jid),prepared)
        self.assertEqual(builds,[1])
        version[0]=2
        self.assertEqual(self.station.transfer_path(jid),prepared)
        self.assertEqual(builds,[1,2])
        self.assertEqual(source.read_bytes(),b'candidate_id,decision,justification\n')
        with zipfile.ZipFile(original) as z:self.assertEqual(z.read('REVUE.csv'),source.read_bytes())

    def test_native_clipboard_payload_is_verbatim_unicode_and_file_drop(self):
        f=self.base/'fichier.zip';f.write_bytes(b'test zip')
        text='École / UNESCO : revue à examiner ✨'
        raw_text,raw_file=clipboard_payloads(text,f)
        self.assertEqual(raw_text[:-2].decode('utf-16-le'),text)
        self.assertEqual(raw_text[-2:],b'\0\0')
        self.assertEqual(struct.unpack('<IiiII',raw_file[:20]),(20,0,0,0,1))
        self.assertEqual(raw_file[20:].decode('utf-16-le'),str(f.resolve())+'\0\0')
        self.assertEqual(f.read_bytes(),b'test zip')

if __name__=='__main__': unittest.main()
