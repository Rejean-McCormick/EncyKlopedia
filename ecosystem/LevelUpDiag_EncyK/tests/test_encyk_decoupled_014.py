"""Standalone EncyK 0.14 + standalone Skope 0.14.x, bounded and read-only tests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

from levelupdiag_core.config import ConfigError, load_config
from levelupdiag_core.report import Report
from levels import encyk_bridge, encyk_topology, encyk_skope
from levels.n05_declared_validations import run as run_validators
from levels._encyk_common import bounded_json

ROOT=Path(__file__).resolve().parents[1]

def sample_repo(base):
    repo=base/'EncyK';repo.mkdir()
    (repo/'VERSION').write_text('0.14.0',encoding='utf8')
    (repo/'MANIFEST.json').write_text(json.dumps({'contracts':{'skope_pull':'encyk.skope-pull/1.0'}}),encoding='utf8')
    bridge=repo/'00_system/integrations/skope_bridge.py'
    bridge.parent.mkdir(parents=True)
    bridge.write_text('class SkopeClient:\n pass\ndef pull(): pass\ndef inspect_result(): pass\ndef list_jobs(): pass\n',encoding='utf8')
    return repo

def sample_report():
    return Report('N14','External bridge','read only','test','run')

class DecoupledArchitecture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.target=sample_repo(self.root)
        self.data=self.root/'volume';self.data.mkdir()
        self.cfg={'_target_root':str(self.target),'_tool_root':str(ROOT),
                  'encyk':{'data_root':str(self.data),'skope_repo_root':str(self.root/'Skope'),
                           'skope_api':'http://127.0.0.1:8767'}}

    def test_independent_target_detected_without_old_launcher(self):
        import os
        with patch.dict(os.environ,{}):
            cfg=load_config(ROOT,str(self.target))
        self.assertEqual(Path(cfg['_target_root']),self.target)
        self.assertFalse((self.target/'Lancer_Skope.pyw').exists())
        old=self.root/'OldEncyK';old.mkdir()
        (old/'Lancer_Skope.pyw').write_text('legacy',encoding='utf8')
        with patch.dict(os.environ,{}):
            with self.assertRaises(ConfigError):load_config(ROOT,str(old))

    def test_topology_requires_decoupling_and_external_bridge(self):
        report=sample_report();encyk_topology.run(self.cfg,report)
        findings={x['id']:x['verdict'] for x in report.findings}
        self.assertEqual(findings['encyk.code.skope_decoupled'],'PASS')
        self.assertEqual(findings['encyk.code.skope_pull_bridge'],'PASS')
        old=self.target/'00_system/tools/skope/skope/api.py';old.parent.mkdir(parents=True)
        old.write_text('integrated legacy',encoding='utf8')
        report=sample_report();encyk_topology.run(self.cfg,report)
        findings={x['id']:x['verdict'] for x in report.findings}
        self.assertEqual(findings['encyk.code.skope_decoupled'],'FAIL')

    def test_bridge_audits_contract_without_pulling_or_writing(self):
        before=sorted(str(p.relative_to(self.target)) for p in self.target.rglob('*') if p.is_file())
        report=sample_report();encyk_bridge.run(self.cfg,report)
        d={x['id']:x['verdict'] for x in report.findings}
        self.assertEqual(d['encyk.bridge.contract'],'PASS')
        self.assertEqual(d['encyk.bridge.no_embedded_skope'],'PASS')
        self.assertEqual(d['encyk.bridge.intake_area'],'WARN')
        self.assertEqual(before,sorted(str(p.relative_to(self.target)) for p in self.target.rglob('*') if p.is_file()))

    def test_bridge_inspects_receipt_metadata_and_not_zip_payload(self):
        stage=self.data/'20_evidence/external-intake/skope'/('a'*32);stage.mkdir(parents=True)
        (stage/'receipt.json').write_text(json.dumps({'contract':'encyk.skope-pull/1.0','source_job':stage.name,'source_kind':'qid_inventory'}),encoding='utf8')
        (stage/'results.zip').write_bytes(b'not parsed or downloaded')
        report=sample_report();encyk_bridge.run(self.cfg,report)
        x=next(x for x in report.findings if x['id']=='encyk.bridge.intake_receipts')
        self.assertEqual(x['verdict'],'PASS')
        self.assertEqual(x['evidence']['recent_count'],1)

    def test_encyk_validators_interpreter_placeholder_without_shell(self):
        cfg={'_target_root':str(self.target),'encyk':{},'execution':{'allow_target_mutation':False,'allow_network':False},
             'validators':[{'id':'safe','name':'Safe test','cwd':'.','command':['{python}','-B','-c','print(123)'],'mutates_target':False,'network':False}]}
        report=sample_report()
        run_validators(cfg,report)
        item=report.findings[-1]
        self.assertEqual(item['verdict'],'PASS',item)
        self.assertEqual(item['evidence']['argv'][1:3],['-B','-c'])

    def test_bad_receipt_not_mistaken_for_valid_import(self):
        stage=self.data/'20_evidence/external-intake/skope'/('b'*32);stage.mkdir(parents=True)
        (stage/'receipt.json').write_text(json.dumps({'contract':'not-encrypted','source_job':stage.name}),encoding='utf8')
        (stage/'results.zip').write_bytes(b'data')
        report=sample_report();encyk_bridge.run(self.cfg,report)
        self.assertEqual(report.findings[-1]['verdict'],'WARN')

class ReadOnlyAPI(BaseHTTPRequestHandler):
    methods=[]
    def do_GET(self):
        self.methods.append(('GET',self.path))
        responses={
            '/api/meta':{'complete':'1'},'/api/config':{'server_release':'0.14.1','target_kristal':None},
            '/api/extract/profiles':[], '/api/diagnostics/reader':{'python_executable':'python312', 'reader_importable':True},
            '/api/kristals':{'entries':[],'active':None},
            '/api/scope-profiles/catalog':{'profiles':[{'id':'catho'}]},
            '/api/large/latest':{'job':None},
        }
        body=json.dumps(responses.get(self.path,{})).encode('utf8')
        self.send_response(200 if self.path in responses else 404)
        self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers();self.wfile.write(body)
    def do_POST(self):
        self.methods.append(('POST',self.path));self.send_response(500);self.end_headers()
    def log_message(self,*args):pass

class SkopeAPITests(unittest.TestCase):
    def test_external_encyk_skope_bridge_api_only_get(self):
        ReadOnlyAPI.methods=[]
        svr=ThreadingHTTPServer(('127.0.0.1',0),ReadOnlyAPI)
        t=threading.Thread(target=svr.serve_forever,daemon=True);t.start()
        try:
            cfg={'encyk':{'skope_api':f'http://127.0.0.1:{svr.server_port}','skope_connection_timeout_seconds':2}}
            data=encyk_skope.collect(cfg,with_preflight=False)
            self.assertEqual(data['config']['server_release'],'0.14.1')
            self.assertTrue(all(method=='GET' for method,_ in ReadOnlyAPI.methods))
            report=sample_report();encyk_skope.run(cfg,report)
            fields={f['id']:f['verdict'] for f in report.findings}
            self.assertEqual(fields['encyk.skope.standalone_release'],'PASS')
        finally:
            svr.shutdown();svr.server_close();t.join(timeout=3)

if __name__=='__main__':unittest.main()
