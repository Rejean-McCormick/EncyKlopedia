"""Regression tests for verified, batch-resumable full Wikidata evidence extraction."""
import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from skope import extraction


class FullExtractionTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.profiles = self.root/'profiles';self.profiles.mkdir()
        self.index = self.root/'30_working/wikidata/wikidata.compact.sqlite'
        self.index.parent.mkdir(parents=True)
        self.index.write_bytes(b'not touched')
        self.invfolder = self.root/'30_working/skope-large-scopes'/('b'*32)
        self.invfolder.mkdir(parents=True)
        self.inv=(self.invfolder/'selected-qids.jsonl')
        self.inv.write_text(''.join(json.dumps({'wikidata_qid':'Q'+str(x)})+'\n' for x in [1,2,3]),encoding='utf8')
        (self.invfolder/'recipe.json').write_text(json.dumps({'max_entities':0,'root':'Q1','default_depth':4,'geography':{'mode':'annotate'}}))
        with sqlite3.connect(self.invfolder/'state.sqlite') as conn:
            conn.execute('CREATE TABLE status(state TEXT, selected INT, expanded INT,pending INT,created_at REAL,updated_at REAL,message TEXT)')
            conn.execute('INSERT INTO status VALUES(?,?,?,?,?,?,?)',('completed',3,3,0,0,time.time(),'Done'))
        self.dump=self.root/'10_sources/wikidata/dumps/current/mock.json.bz2';self.dump.parent.mkdir(parents=True)
        self.dump.write_bytes(b'mock source file')
        self.man=self.root/'20_evidence/manifests/wikidata-dump-verified.json';self.man.parent.mkdir(parents=True)
        self.sha='c'*40
        self.man.write_text(json.dumps({'sha1':self.sha,'file':self.dump.name,'bytes':self.dump.stat().st_size,'verified':True}))
        self.side=self.root/'30_working/wikidata-fast'/('sha1-'+self.sha)/'manifest.json';self.side.parent.mkdir(parents=True)
        self.side.write_text(json.dumps({'complete':True,'dump':{'sha1':self.sha,'bytes':self.dump.stat().st_size}}))
        self.spec={'format':'skope.extraction-profile/draft-1','profile_id':'botany-test','title':'Test',
            'target':{'write_to_canon':False},'selection':{'source_job':'b'*32,'expected_qids':3, 'preserve_exact_inventory':True,'rediscover_scope':False},
            'source':{'dump_path':str(self.dump),'verify_dump_identity_from_manifest':str(self.man),'existing_fast_index_root':str(self.side.parent.parent),
                      'allow_full_dump_scan':False,'auto_build_new_index':False,'abort_if_no_verified_random_access':True,'require_verified_source_identity':True},
            'extraction':{'mode':'full_source_entity_json','output_compression':'gzip-jsonl','batch_size':2,'workers':1},
            'output':{'evidence_root':str(self.root/'20_evidence/scope-snapshots/botany-test'),'working_root':str(self.root/'30_working/scopes/botany-test'),'scope_key':'botany-test','no_extra_backup_or_archive':True},
            'geography':{'priority_qid':'Q16','secondary_region_qid':'Q49','mode':'annotate_then_review'},
            'safety':{'no_kristal_canonical_modification':True,'minimum_free_space_gib':0.001}}
        (self.profiles/'botany-test.json').write_text(json.dumps(self.spec),encoding='utf8')
        self.path_patcher=patch.object(extraction,'PROFILES',self.profiles)
        self.path_patcher.start();self.addCleanup(self.path_patcher.stop)
        self.mod=extraction._module()
        self.access=patch.object(self.mod,'fast_access_status',return_value=(True,{'random_access_ready':True,'runtime_backend':{'backend':'fixture'}}))
        self.access.start();self.addCleanup(self.access.stop)
        self.fetcher=patch.object(self.mod,'fast_fetch_raw',side_effect=self.raw_records)
        self.fetcher.start();self.addCleanup(self.fetcher.stop)
    def raw_records(self, root, dump, qids, threads):
        return {x:json.dumps({'id':x,'claims':{'P171':[{'references':[{'snaks':{'P248':[{'snaktype':'value'}]}}],'qualifiers':{'P580':[]}}]},'labels':{'en':{'value':'tree'}}}).encode() for x in qids}
    def wait(self,job):
        for _ in range(250):
            s=extraction.status(self.index,job)
            if s['state'] not in ('queued','running','finalizing'):
                return s
            time.sleep(0.02)
        self.fail('Job not completed: '+str(s))
    def test_preflight_verified_and_no_canon(self):
        p=extraction.preflight(self.index,'botany-test')
        self.assertTrue(p['ready'],p['blockers']);self.assertEqual(p['total'],3)
        self.assertTrue(p['source']['random_access_ready'])
        self.assertFalse((self.root/'20_evidence/scope-snapshots/botany-test').exists())
        self.assertEqual(self.index.read_bytes(),b'not touched')
    def test_unverified_source_fails_closed(self):
        self.man.write_text(json.dumps({'sha1':self.sha,'file':self.dump.name,'bytes':self.dump.stat().st_size,'verified':False}))
        p=extraction.preflight(self.index,'botany-test')
        self.assertFalse(p['ready']);self.assertIn('verified',str(p['blockers']))
    def test_no_fast_index_fails_closed(self):
        self.side.unlink()
        p=extraction.preflight(self.index,'botany-test')
        self.assertFalse(p['ready']);self.assertTrue(any('fast-access' in m for m in p['blockers']))
    def test_explicit_confirmation(self):
        with self.assertRaisesRegex(ValueError,'confirmation'):
            extraction.start(self.index,'botany-test')
    def test_full_records_promoted_to_evidence(self):
        first=extraction.start(self.index,'botany-test',confirmed=True)
        result=self.wait(first['job'])
        self.assertEqual(result['state'],'completed',result['message'])
        self.assertEqual(result['processed'],3)
        folder=Path(result['evidence_path'])
        self.assertEqual(len(list(folder.glob('part-*.jsonl.gz'))),2)
        import gzip
        items=[]
        for f in sorted(folder.glob('part-*.jsonl.gz')):
            with gzip.open(f,'rt') as stream:items += [json.loads(x) for x in stream]
        self.assertEqual(len(items),3)
        self.assertEqual(items[0]['claims']['P171'][0]['references'][0]['snaks']['P248'][0]['snaktype'],'value')
        manifest=json.loads((folder/'snapshot-manifest.json').read_text())
        self.assertEqual(manifest['record_count'],3)
        self.assertFalse(manifest['kristal_canon_modified'])
        self.assertEqual(self.inv.read_text().count('wikidata_qid'),3)
        self.assertEqual(self.index.read_bytes(),b'not touched')
    def test_resume_when_batch_missing_source(self):
        orig=self.mod.fast_fetch_raw
        def intermittent(root,dump,qids,threads):
            if 'Q3' in qids:return {}
            return self.raw_records(root,dump,qids,threads)
        with patch.object(self.mod,'fast_fetch_raw',side_effect=intermittent):
            started=extraction.start(self.index,'botany-test',confirmed=True)
            failed=self.wait(started['job'])
        self.assertEqual(failed['state'],'missing_source_records')
        self.assertEqual(failed['processed'],2)
        recovered=extraction.start(self.index,'botany-test',resume=started['job'],confirmed=True)
        final=self.wait(recovered['job'])
        self.assertEqual(final['state'],'completed',final['message'])
        self.assertEqual(final['processed'],3)
        self.assertFalse((self.root/'30_working/skope-extractions'/started['job']/'chunks').exists())
    def test_http_preflight_and_explicit_confirmation(self):
        import threading
        from http.server import ThreadingHTTPServer
        from urllib.request import urlopen,Request
        from urllib.error import HTTPError
        from skope.api import App
        cls=type('ExtractApp',(App,),{'db_path':str(self.index),'starting_recipe':None,'arketype_guidance':None,'target_kristal':None})
        srv=ThreadingHTTPServer(('127.0.0.1',0),cls)
        worker=threading.Thread(target=srv.serve_forever,daemon=True);worker.start()
        self.addCleanup(srv.server_close);self.addCleanup(srv.shutdown)
        base='http://127.0.0.1:'+str(srv.server_port)
        with urlopen(base+'/api/extract/profiles') as response:
            found=json.load(response)
            self.assertEqual(len(found),1)
            self.assertEqual(found[0]['id'],'botany-test')
        with urlopen(base+'/extraction.js') as response:
            self.assertEqual(response.status,200)
            self.assertIn(b'extract-modal',response.read())
        data=json.dumps({'profile':'botany-test'}).encode()
        with urlopen(Request(base+'/api/extract/preflight',data=data,headers={'Content-Type':'application/json'})) as response:
            ready=json.load(response)
            self.assertTrue(ready['ready'])
            self.assertEqual(ready['total'],3)
        with self.assertRaises(HTTPError) as failure:
            urlopen(Request(base+'/api/extract/start',data=data,headers={'Content-Type':'application/json'}))
        self.assertEqual(failure.exception.code,400)
        with self.assertRaises(HTTPError) as attacker:
            urlopen(Request(base+'/api/extract/start',data=data,headers={'Origin':'http://evil.example','Content-Type':'application/json'}))
        self.assertEqual(attacker.exception.code,403)

    def test_recover_snapshot_after_server_stop_during_finalization(self):
        first=extraction.start(self.index,'botany-test',confirmed=True)
        finished=self.wait(first['job'])
        self.assertEqual(finished['state'],'completed')
        state_file=self.root/'30_working/skope-extractions'/first['job']/'state.json'
        state=json.loads(state_file.read_text())
        state['state']='finalizing'
        state_file.write_text(json.dumps(state))
        recovered=extraction.start(self.index,'botany-test',confirmed=True,resume=first['job'])
        self.assertEqual(recovered['state'],'completed')
        self.assertEqual(recovered['evidence_path'],finished['evidence_path'])

    def test_refuse_modified_inventory_recipe_on_resume(self):
        first=extraction.start(self.index,'botany-test',confirmed=True)
        self.assertEqual(self.wait(first['job'])['state'],'completed')
        state_file=self.root/'30_working/skope-extractions'/first['job']/'state.json'
        state=json.loads(state_file.read_text());state['state']='paused';state_file.write_text(json.dumps(state))
        (self.invfolder/'recipe.json').write_text('{"modified": true}')
        with self.assertRaisesRegex(ValueError,'changed'):
            extraction.start(self.index,'botany-test',confirmed=True,resume=first['job'])

    def test_inventory_fingerprint_changes_block(self):
        old=self.inv.read_bytes();self.inv.write_bytes(old+b'bad data')
        with self.assertRaises((ValueError,json.JSONDecodeError)):
            extraction.preflight(self.index,'botany-test')

if __name__=='__main__':unittest.main()
