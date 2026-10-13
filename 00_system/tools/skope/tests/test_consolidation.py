"""Non-regression checks for one-repository Skope integration in EncyK."""
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from skope import db
from skope.scope import explore
from skope.export import bundle
from test_integration import make_index, REC

TOOL=Path(__file__).resolve().parents[1]
ROOT=TOOL.parents[2]

class OneRepoTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.index=Path(self.tmp.name)/'global.sqlite'
        make_index(self.index)

    def test_no_legacy_ingestion_or_separate_project(self):
        self.assertFalse((TOOL/'skope/ingest.py').exists())
        self.assertFalse((TOOL/'skope/config.py').exists())
        self.assertFalse((TOOL/'pyproject.toml').exists())
        self.assertTrue((ROOT/'Lancer_Skope.pyw').exists())
        self.assertTrue((ROOT/'harvest.ps1').exists())

    def test_index_never_modified_even_on_export(self):
        import hashlib
        before=hashlib.sha256(self.index.read_bytes()).hexdigest()
        with db.connect(self.index) as conn:
            self.assertEqual(db.meta(conn)['evidence_available'],'false')
            self.assertEqual(len(db.find(conn,REC['root'])),1)
            self.assertEqual(db.node(conn,REC['root'])['id'],REC['root'])
            proposal=bundle(conn,REC,'integration-test')
            edges=db.neighbors(conn,REC['root'])
            self.assertTrue(edges)
            self.assertTrue(all(e['statement_id'] is None for e in edges))
        self.assertEqual(before,hashlib.sha256(self.index.read_bytes()).hexdigest())
        with ZipFile(io.BytesIO(proposal)) as z:
            self.assertTrue(all('/../' not in name for name in z.namelist()))
            self.assertNotIn('wikidata-entities.jsonl', z.namelist())
            cfg=json.loads(z.read('staged/00_system/tools/scope-builder/config/scopes/integration-test.scope.json'))
            self.assertEqual(cfg['schema_version'],'encyklopedia-scope/v3')
            self.assertEqual(cfg['discovery']['follow_rules'],[])
            self.assertEqual(cfg['discovery']['reverse_root_relations'],{})
            self.assertFalse(cfg['discovery']['include_all_entity_relations_from_roots'])
            self.assertTrue(cfg['evidence']['preserve_full_entity_json'])

    def test_readonly_index_detects_bad_schema(self):
        path=Path(self.tmp.name)/'invalid.sqlite'
        with sqlite3.connect(path) as conn:conn.execute('CREATE TABLE entity(id INTEGER)')
        with self.assertRaises(ValueError):db.connect(path)

    def test_branch_selection_and_aggregated_provenance(self):
        with db.connect(self.index) as conn:
            report=explore(conn,REC)
            self.assertFalse(report['truncated'])
            self.assertEqual(report['profile'],'skope.encyk-preview/1.0')
            self.assertEqual(report['source_snapshot_digest'],'sha1:'+'a'*40)
            self.assertTrue(report['counts']['entities']>1)
            self.assertTrue(any('agrégé' in note for note in report['limitations']))

if __name__=='__main__':unittest.main()
