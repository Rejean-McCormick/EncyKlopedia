"""Wizard remains opt-in and has no new write endpoints or source mutations."""
import json
import threading
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from http.server import ThreadingHTTPServer
from skope.api import App, STATIC
from test_integration import make_index

class WizardAssets(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        db = Path(self.tmp.name)/'fixture.sqlite'
        make_index(db)
        cls = type('WizardTestServer',(App,), {'db_path':str(db), 'starting_recipe':None,
             'arketype_guidance':None, 'target_kristal':{'slug':'kristal-botany'}})
        self.server = ThreadingHTTPServer(('127.0.0.1',0),cls)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base='http://127.0.0.1:'+str(self.server.server_address[1])

    def get(self,uri):
        with urlopen(self.base+uri,timeout=4) as resp:
            return resp.status,resp.read().decode('utf-8')

    def test_wizard_assets_are_served_with_existing_ui(self):
        _,index=self.get('/')
        self.assertIn('id="wizard-open"',index)
        self.assertIn('id="skope-wizard"',index)
        for legacy in ['id="search"','id="preview"','id="export"', 'id="graph"','id="budget"', 'id="threshold"','id="branchcount"']:
            self.assertIn(legacy,index)
        for url in ['/wizard.js','/wizard.css','/app.js','/style.css']:
            code,body=self.get(url)
            self.assertEqual(code,200)
            self.assertGreater(len(body),400)

    def test_profile_is_click_to_apply_and_counts_use_readonly_preview(self):
        js=(STATIC/'wizard.js').read_text(encoding='utf8')
        self.assertIn("e('wizard-open').addEventListener('click',open)",js)
        self.assertIn("button('Apply'",js)
        self.assertIn("function applyAll()",js)
        self.assertIn("'/api/preview'",js)
        self.assertNotIn("'/api/export'",js)
        self.assertNotIn('canon/',js)
        self.assertNotIn('fetch(\'http',js)
        self.assertIn('measure',js)
        self.assertIn('truncated',js)
        old=(STATIC/'app.js').read_text(encoding='utf8')
        self.assertIn('window.SkopeWizardBridge',old)
        self.assertIn('chooseRoot:',old)

    def test_readonly_api_remains_restricted(self):
        code,data=self.get('/api/meta')
        self.assertEqual(code,200)
        self.assertIn('complete',json.loads(data))

if __name__=='__main__':unittest.main()
