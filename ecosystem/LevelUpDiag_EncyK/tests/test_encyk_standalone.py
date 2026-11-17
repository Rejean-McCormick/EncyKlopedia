"""Regression tests for independent EncyK target profile; no real Wikidata access."""
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from levelupdiag_core.config import ConfigError,load_config
from levelupdiag_core.manifest import load_manifest
from levels._encyk_common import checked_api,api_json
from levels.encyk_parity import compare

class FakeSkope(BaseHTTPRequestHandler):
    def do_GET(self):
        data={'/api/meta':{'complete':'1'},
              '/api/config':{'target_kristal':{'slug':'kristal-botany'}},
              '/api/extract/profiles':[{'id':'botany-canada-full-wikidata'}]}
        if self.path=='/api/redirect':
            self.send_response(301)
            self.send_header('Location','https://example.com')
            self.end_headers();return
        self.send_response(200 if self.path in data else 404)
        self.send_header('Content-Type','application/json');self.end_headers()
        self.wfile.write(json.dumps(data.get(self.path,{'error':'not_found'})).encode())
    def do_POST(self):
        length=int(self.headers.get('Content-Length','0'))
        body=json.loads(self.rfile.read(length))
        assert self.path=='/api/extract/preflight'
        assert body['profile']=='botany-canada-full-wikidata'
        self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
        self.wfile.write(json.dumps({'ready':False,'source':{'random_access_ready':False,'fast_backend':'bz2-stdlib'}}).encode())
    def log_message(self,*args): pass

class StandaloneEncyK(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.target=Path(self.tmp.name)/'EncyK';self.target.mkdir()
        (self.target/'MANIFEST.json').write_text('{"contracts":{"skope_pull":"encyk.skope-pull/1.0"}}')
        (self.target/'VERSION').write_text('0.14.0')
        bridge=self.target/'00_system/integrations/skope_bridge.py'
        bridge.parent.mkdir(parents=True)
        bridge.write_text('# test bridge')
        self.profile=patch.dict(os.environ,{})
        self.profile.start();self.addCleanup(self.profile.stop)

    def test_manifest_enables_encyk_only(self):
        m=load_manifest(ROOT)
        self.assertEqual(len(m['levels']),15)
        self.assertIn('bridge',m['campaigns'])
        self.assertTrue(all('orgo' not in l['module'] for l in m['levels']))
        self.assertIn('reader',m['campaigns'])

    def test_dedicated_single_manifest_without_profile(self):
        m=load_manifest(ROOT)
        self.assertIn('EncyK',m['suite_name'])
        self.assertEqual(m['suite_version'],'1.2.0')

    def test_external_target_and_report_under_levelup(self):
        cfg=load_config(ROOT,str(self.target))
        self.assertEqual(Path(cfg['_target_root']),self.target)
        self.assertEqual(Path(cfg['_control_root']),ROOT/'.levelupdiag/encyk')
        self.assertFalse(cfg['execution']['allow_target_mutation'])
        self.assertFalse(cfg['execution']['allow_network'])

    def test_refuse_nested_and_unrecognized_target(self):
        for path in (ROOT,ROOT.parent,Path(self.tmp.name)):
            with self.assertRaises(ConfigError):load_config(ROOT,str(path))

    def test_refuse_target_mutation_and_report_escape(self):
        import levelupdiag_core.config as c
        original=c.read_json
        def inject_bad(p):
            j=original(p)
            if p.name=='levelupdiag.config.json':
                j['execution']['allow_target_mutation']=True
            return j
        with patch('levelupdiag_core.config.read_json',side_effect=inject_bad):
            with self.assertRaises(ConfigError):load_config(ROOT,str(self.target))
        def inject_escape(p):
            j=original(p)
            if p.name=='levelupdiag.config.json':j['control_dir']='../D'
            return j
        with patch('levelupdiag_core.config.read_json',side_effect=inject_escape):
            with self.assertRaises(ConfigError):load_config(ROOT,str(self.target))

    def test_loopback_only(self):
        cfg={'encyk':{'skope_api':'https://127.0.0.1:8767'}}
        with self.assertRaises(ValueError):checked_api(cfg)
        cfg['encyk']['skope_api']='http://example.com'
        with self.assertRaises(ValueError):checked_api(cfg)

    def test_server_backend_mismatch(self):
        local={'random_access_ready':True}
        mismatch={'up':True,'preflight':{'source':{'random_access_ready':False,'fast_backend':'bz2-stdlib'}}}
        self.assertEqual(compare(local,mismatch)[0],'FAIL')
        mismatch['preflight']['source'].update({'random_access_ready':True,'fast_backend':'indexed_bzip2'})
        self.assertEqual(compare(local,mismatch)[0],'PASS')
        self.assertEqual(compare(local,{'up':False})[0],'BLOCKED')

    def test_fake_skope_api_readonly(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),FakeSkope)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        cfg={'encyk':{'skope_api':'http://127.0.0.1:'+str(server.server_port),
                      'skope_connection_timeout_seconds':1.5}}
        self.assertEqual(api_json(cfg,'/api/meta')['complete'],'1')
        self.assertEqual(api_json(cfg,'/api/extract/preflight',{'profile':'botany-canada-full-wikidata'})['source']['fast_backend'],'bz2-stdlib')
        with self.assertRaises(ValueError):api_json(cfg,'/api/redirect')

    def test_cli_doctor_never_creates_target_files(self):
        before=sorted(p.name for p in self.target.iterdir())
        env=os.environ.copy()
        cp=subprocess.run([sys.executable,'-B',str(ROOT/'levelupdiag.py'),'--target',str(self.target),'doctor'],
                          cwd=ROOT,env=env,text=True,capture_output=True,timeout=10)
        self.assertEqual(cp.returncode,0,cp.stderr)
        self.assertEqual(before,sorted(p.name for p in self.target.iterdir()))

if __name__=='__main__':unittest.main()
