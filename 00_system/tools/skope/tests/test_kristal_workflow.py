"""Workflow EncyK -> Skope -> proposition ciblant un Kristal, sans écriture."""
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from skope.arketype import load_guidance
from skope.project import (BOTANY_GUIDE,default_guidance,read_kristal,
                           find_kristals,safe_target,seed_search)
from skope.export import bundle
from test_integration import make_index, REC
from skope.db import connect

class KristalWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.kristal=self.root/'Kristal-Botany';self.kristal.mkdir()
        self.src=self.kristal/'kristal.workspace.json'
        self.src.write_text(json.dumps({'format':'kristal.local-workspace/3.2.0','slug':'kristal-botany',
             'title':'Kristal-Botany','state_ref':'urn:kristal:state:botany',
             'target':{'state_architecture':'kristal.state/9.0'},'state_scope':{'domain':'botany'}}),encoding='utf8')
        self.index=self.root/'index.sqlite';make_index(self.index)
    def test_discover_readonly_and_auto_arketype_botany(self):
        before=self.src.read_bytes()
        items=find_kristals(self.root)
        self.assertEqual(len(items),1)
        self.assertEqual(items[0][1]['domain'],'botany')
        self.assertEqual(default_guidance(items[0][1]),BOTANY_GUIDE)
        guide=load_guidance(default_guidance(items[0][1]))
        self.assertEqual(guide['profile_id'],'PRF-03')
        self.assertFalse(guide['publication_authorized'])
        self.assertEqual(seed_search(items[0][1]),'Embryophyta')
        self.assertEqual(before,self.src.read_bytes())
    def test_export_binding_without_local_path_or_canonical_write(self):
        target=safe_target(read_kristal(self.kristal))
        data_before=self.index.read_bytes()
        with connect(self.index) as db:
            output=bundle(db,REC,'kristal-botany-demo',load_guidance(BOTANY_GUIDE),target)
        with ZipFile(io.BytesIO(output)) as z:
            self.assertIn('review/target-kristal.json',z.namelist())
            self.assertIn('review/arketype.scope-guidance.json',z.namelist())
            t=json.loads(z.read('review/target-kristal.json'))
            self.assertFalse(t['canonical_write_authorized'])
            self.assertFalse(t['publication_authorized'])
            m=json.loads(z.read('manifest.json'))
            self.assertEqual(m['target_kristal']['state_ref'],'urn:kristal:state:botany')
            self.assertNotIn('\\',z.read('review/target-kristal.json').decode())
            self.assertNotIn(str(self.root),str(m))
        self.assertEqual(data_before,self.index.read_bytes())
    def test_no_auto_assignment_for_other_domains(self):
        self.assertIsNone(default_guidance({'slug':'kristal-ecology','domain':'ecology'}))
    def test_reject_wrong_project(self):
        other=self.root/'other';other.mkdir()
        with self.assertRaises(ValueError):read_kristal(other)
    def test_no_code_or_archive_touching_d(self):
        path=Path(__file__).resolve().parents[4]/'Lancer_Skope.pyw'
        self.assertTrue(path.exists())

if __name__=='__main__':unittest.main()
