from contextlib import closing
"""Stats globales V31 : pas de taux de fin inventé, lecture seule."""
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'/'unesco_pilot'))
import statistiques_globales_v31 as m

class StatsTests(unittest.TestCase):
    def test_global_inventory_not_same_as_branch_completion(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td);source=base/'wiki.sqlite';qual=base/'qual.sqlite'
            with closing(sqlite3.connect(source)) as db, db:
                db.executescript('''CREATE TABLE wiki_pages(page_id INTEGER PRIMARY KEY,ns INTEGER,redirect INTEGER);
                  CREATE TABLE ingest_state(stage TEXT,completed INTEGER,rows_imported INTEGER);''')
                db.executemany('INSERT INTO wiki_pages VALUES(?,?,?)',[(1,0,0),(2,0,0),(3,0,1),(4,14,0)])
            with closing(sqlite3.connect(qual)) as db, db:
                db.executescript('''CREATE TABLE article_profiles(page_id INTEGER PRIMARY KEY,branch_candidates INTEGER,kind TEXT);
                  CREATE TABLE branch_suggestions(page_id INTEGER,branch_id TEXT,score INTEGER);
                  CREATE TABLE meta(key TEXT,value TEXT);''')
                db.executemany('INSERT INTO article_profiles VALUES(?,?,?)',[(1,1,'PERSONNE'),(2,0,'INDETERMINE')])
                db.execute('INSERT INTO branch_suggestions VALUES(?,?,?)',(1,'unesco.mt1.10',63))
            s0=source.read_bytes();q0=qual.read_bytes()
            rep=m.inspect({'source':source,'qualification':qual})
            self.assertEqual(rep['bases']['source']['pages_ns0'],3)
            self.assertEqual(rep['bases']['qualification']['profils'],2)
            self.assertEqual(rep['inventaire_ns0_traite_pct'],66.667)
            self.assertIsNone(rep['avancement_complet_des_branches'])
            self.assertEqual(source.read_bytes(),s0)
            self.assertEqual(qual.read_bytes(),q0)
            self.assertIn('TABLEAU',m.html_report(rep).upper()[:1300])

if __name__=='__main__':unittest.main(verbosity=2)
