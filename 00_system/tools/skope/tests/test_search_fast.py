"""SQL regressions for production-scale Skope searches, using compact index fixture."""
import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from skope import db
from test_integration import make_index

class FastSearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'wikidata.sqlite'
        make_index(self.path)

    def test_qid_lookup_skips_search_names(self):
        with db.connect(self.path) as conn:
            sql=[]
            conn.set_trace_callback(sql.append)
            hits=db.find(conn,'  q900000000  ')
            self.assertEqual([h['id'] for h in hits],['Q900000000'])
            self.assertFalse(any('idx_name_norm' in s or 'norm >' in s or 'norm =' in s for s in sql),sql)
            self.assertEqual(db.find(conn,'Q7777777777'),[])
            self.assertFalse(any('FROM name INDEXED BY idx_name_norm' in s for s in sql))

    def test_name_and_alias_search_via_index_and_prefix(self):
        with db.connect(self.path) as conn:
            rows=db.find(conn,'Embryophyta')
            self.assertEqual(rows[0]['id'],'Q900000000')
            self.assertEqual(db.find(conn,'Plantes terrestres')[0]['id'],'Q900000000')
            self.assertEqual(db.find(conn,'Embryoph')[0]['id'],'Q900000000')
            self.assertEqual(db.find(conn,'%%%'),[])  # caractère joker seul : pas de recherche globale
            self.assertEqual(db.find(conn,'Plantes%')[0]['id'],'Q900000000') # normalisé en préfixe littéral

    def test_name_index_is_required_and_never_rebuilt(self):
        with sqlite3.connect(self.path) as conn:
            conn.execute('DROP INDEX idx_name_norm')
        with db.connect(self.path) as conn:
            with self.assertRaisesRegex(ValueError,'idx_name_norm'):
                db.find(conn,'Embryophyta')
            self.assertEqual(db.find(conn,'Q900000000')[0]['label'],'Embryophyta')
        with sqlite3.connect(self.path) as conn:
            self.assertFalse(conn.execute("SELECT 1 FROM sqlite_master WHERE name='idx_name_norm'").fetchone())

    def test_index_plan_does_not_scan_or_sort_entity_table(self):
        with db.connect(self.path) as conn:
            key=db._norm('Embryophyta')
            plan=conn.execute('EXPLAIN QUERY PLAN SELECT entity_id FROM name INDEXED BY idx_name_norm WHERE norm>=? AND norm<? LIMIT ?', (key,key+'\uffff',180)).fetchall()
            description=' '.join(str(x[3]) for x in plan).lower()
            self.assertIn('idx_name_norm',description)
            self.assertNotIn('temp b-tree',description)
            self.assertNotIn('scan',description)

if __name__=='__main__':unittest.main()
