"""Batch results must be an explicit portable ZIP, not a dump nor a backup."""
import io
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.error import HTTPError
from zipfile import ZipFile
from http.server import ThreadingHTTPServer
from skope import massive
from skope.api import App
from test_integration import make_index,REC


class ResultExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        folder=Path(self.temp.name)/'30_working/wikidata';folder.mkdir(parents=True)
        self.db=folder/'wikidata.compact.sqlite';make_index(self.db)
        self.recipe={**REC,'max_entities':0,'direction':'in','allowed_properties':['P171'],
                     'convergence':{'threshold_percent':14.6,'min_support':8,'extra_depth':0,'include':[]}}

    def _complete(self):
        out=massive.start(self.db,self.recipe)
        for _ in range(100):
            r=massive.status(self.db,out['job'])
            if r['state'] not in ('queued','running'):break
            time.sleep(.02)
        self.assertEqual(r['state'],'completed',r)
        return r

    def test_zip_includes_qid_list_and_warnings(self):
        r=self._complete()
        path=massive.prepare_result_zip(self.db,r['job'])
        self.assertTrue(path.is_file())
        self.assertEqual(path, massive.prepare_result_zip(self.db,r['job']))
        with ZipFile(path) as z:
            self.assertEqual(set(z.namelist()),{'selected-qids.jsonl','recipe.json','summary.json','README.txt'})
            self.assertIsNone(z.testzip())
            report=json.loads(z.read('summary.json'))
            lines=z.read('selected-qids.jsonl').splitlines()
            self.assertEqual(len(lines),r['selected'])
            self.assertFalse(report['geographic_filter_applied'])
            self.assertFalse(report['external_convergence_applied'])
            self.assertFalse(report['contains_source_wikidata_json'])
            self.assertEqual(report['selected_qids'],r['selected'])
        self.assertFalse((self.db.parent.parent/'skope-large-scopes'/r['job']/'other-backup.zip').exists())

    def test_reject_non_completed_job_and_invalid_job_id(self):
        with self.assertRaises(ValueError):massive.prepare_result_zip(self.db,'/etc/passwd')
        parent=self.db.parent.parent/'skope-large-scopes';parent.mkdir()
        folder=parent/('a'*32)
        folder.mkdir()
        from skope.scope import validate_recipe
        (folder/'recipe.json').write_text(json.dumps(validate_recipe(self.recipe)))
        import sqlite3
        with sqlite3.connect(folder/'state.sqlite') as db:
            db.execute('CREATE TABLE status(state TEXT, selected INTEGER, expanded INTEGER,pending INTEGER,created_at REAL,updated_at REAL,message TEXT)')
            db.execute("INSERT INTO status VALUES ('paused',1,1,0,1,1,'paused')")
        with self.assertRaises(ValueError):massive.prepare_result_zip(self.db,'a'*32)

    def test_http_stream_and_origin_checks(self):
        r=self._complete()
        cls=type('ResultApp',(App,),{'db_path':str(self.db),'starting_recipe':None,'arketype_guidance':None,'target_kristal':None})
        srv=ThreadingHTTPServer(('127.0.0.1',0),cls)
        worker=threading.Thread(target=srv.serve_forever,daemon=True);worker.start()
        self.addCleanup(srv.server_close);self.addCleanup(srv.shutdown)
        base='http://127.0.0.1:'+str(srv.server_port)
        with urlopen(base+'/api/large/result.zip?job='+r['job'],timeout=10) as resp:
            self.assertEqual(resp.status,200)
            self.assertEqual(resp.headers['Content-Type'],'application/zip')
            payload=resp.read()
        with ZipFile(io.BytesIO(payload)) as z:
            self.assertIn('selected-qids.jsonl',z.namelist())
        with urlopen(base+'/results.js',timeout=5) as resp:
            self.assertEqual(resp.status,200)
        with self.assertRaises(HTTPError) as err:
            urlopen(Request(base+'/api/large/copy',data=json.dumps({'job':r['job']}).encode(),
                headers={'Content-Type':'application/json','Origin':'http://attacker.example:5432'}),timeout=5)
        self.assertEqual(err.exception.code,403)

if __name__=='__main__':unittest.main()
