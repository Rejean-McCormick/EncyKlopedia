"""v31.12 : reconstitue le blocage avec des candidats DEFERRED en réserve.

Aucune production ni base réelle requise : copies temporaires SQLite.
"""
from contextlib import closing
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

from test_unesco_4000_v317 import UNESCO4000Tests as _Fixture


class ReserveDeferredV3112(unittest.TestCase):
    def setUp(self):
        _Fixture.setUp(self)

    def _add_to_7023(self):
        stage=self.st.v28/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        with closing(sqlite3.connect(stage)) as db, db:
            db.executemany('INSERT INTO candidates VALUES(?,?,?,?)',
                ((self.branch['id'],'u1',i,f'School {i}') for i in range(4126,7024)))
        with self.st.db:
            self.st.db.executemany('''INSERT INTO review_index(candidate_id,branch_id,concept_id,page_id,title,priority,
              seed_count,link_evidence,category_evidence,subcategory_evidence,state,last_seen_utc)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
              ((f'candidate_{i}',self.branch['id'],'u1',i,f'School {i}',3,0,0,0,0,'DEFERRED','2026-11-15T00:00:00Z')
               for i in range(4126,7024)))

    def test_reserve_7023_deferred_produces_two_more_packs(self):
        self._add_to_7023()
        with self.st.db:
            self.st.db.execute("UPDATE review_index SET state='DEFERRED',priority=3,link_evidence=0 WHERE state='PENDING'")
        stage=self.st.v28/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        size_before=stage.stat().st_size
        self.assertEqual(self.st._prepare_v28(),2)
        counts=[r[0] for r in self.st.db.execute("SELECT count FROM jobs WHERE kind='v28' ORDER BY count DESC")]
        self.assertEqual(counts,[4000,3023])
        self.assertEqual(self.st.db.execute("SELECT count(*) FROM review_index WHERE state='DEFERRED'").fetchone()[0],0)
        self.assertEqual(self.st.db.execute("SELECT count(*) FROM review_index WHERE state='QUEUED'").fetchone()[0],7023)
        self.assertEqual(stage.stat().st_size,size_before)
        self.assertEqual(self.st._prepare_v28(),0)

    def test_mixed_queue_fills_remaining_capacity_without_ignoring_deferred(self):
        with self.st.db:
            self.st.db.execute("UPDATE review_index SET state='DEFERRED',priority=3 WHERE page_id>1000")
        self.assertEqual(self.st._prepare_v28(),2)
        self.assertEqual(self.st.db.execute("SELECT count(*) FROM review_index WHERE state='QUEUED'").fetchone()[0],4125)
        self.assertEqual(self.st.db.execute("SELECT count(*) FROM review_index WHERE state IN ('PENDING','DEFERRED')").fetchone()[0],0)

    def test_existing_open_unesco_review_freezes_discovery_not_packing(self):
        with self.st.db:
            self.st.db.execute("UPDATE review_index SET state='DEFERRED'")
            self.st.db.execute('''INSERT INTO jobs(id,kind,key,count,status,source_path,source_sha256,
                bundle_path,bundle_sha256,created_utc) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                ('review_existing','v28','existing',5,'SENT','old.csv','digest','old.zip','digest','2026-11-15T00:00:00Z'))
        called=[]
        self.st._run=lambda script,options:called.append(script) or '"queue":{"PACKED":1}'
        self.st._refresh_review_index=lambda:0
        self.st._prepare_v27=lambda:0
        self.st._batch()
        self.assertFalse(any('DECOUVRIR_' in cmd for cmd in called))
        self.assertEqual(self.st.db.execute("SELECT count(*) FROM jobs WHERE kind='v28' AND status IN ('SENT','READY','WAITING')").fetchone()[0],3)
        self.assertEqual(self.st.db.execute("SELECT count(*) FROM review_index WHERE state='QUEUED'").fetchone()[0],4125)


if __name__=='__main__':unittest.main()
