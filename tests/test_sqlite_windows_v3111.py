"""V31.1.1 — fermetures explicites des connexions SQLite, y compris en refus.

La sortie d'un ``with sqlite3.connect(...)`` ne ferme PAS la connexion en CPython.
Sur Windows une connexion ouverte interdit le nettoyage du fichier temporaire.
"""
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'/'unesco_pilot'))
import preuves_xml_v31
import piloter_branches_v311


class _Observe(sqlite3.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._closed_explicitly = False

    def close(self):
        self._closed_explicitly = True
        return super().close()


class WindowsSQLiteHandleTests(unittest.TestCase):
    def _observe(self, action):
        native = sqlite3.connect
        opened = []

        def tracked(*args, **kwargs):
            kwargs.setdefault('factory', _Observe)
            db = native(*args, **kwargs)
            opened.append(db)
            return db

        try:
            with patch.object(sqlite3, 'connect', side_effect=tracked):
                action()
        finally:
            not_closed = [db for db in opened if not db._closed_explicitly]
            for db in not_closed:
                db.close()
        self.assertTrue(opened, 'Le test doit ouvrir au moins une connexion')
        self.assertEqual(not_closed, [], 'Connexions SQLite non fermées explicitement')

    def test_preuves_xml_read_targets_frees_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'stage.sqlite'
            with closing(sqlite3.connect(path)) as db, db:
                db.execute('CREATE TABLE candidates(page_id INTEGER)')
                db.executemany('INSERT INTO candidates VALUES (?)', [(1,), (2,)])
            self._observe(lambda: self.assertEqual(preuves_xml_v31.read_targets(path), {1,2}))

    def test_preuves_xml_read_targets_failure_frees_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'stage.sqlite'
            with closing(sqlite3.connect(path)) as db, db:
                db.execute('CREATE TABLE unrelated(x INTEGER)')
            def action():
                with self.assertRaisesRegex(ValueError, 'Table candidates'):
                    preuves_xml_v31.read_targets(path)
            self._observe(action)

    def test_pilote_jobs_read_frees_connection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'station.sqlite'
            with closing(sqlite3.connect(path)) as db, db:
                db.execute('CREATE TABLE jobs(kind TEXT,status TEXT)')
                db.execute("INSERT INTO jobs VALUES('v28','SENT')")
            self._observe(lambda: self.assertEqual(piloter_branches_v311.readable_jobs(path), 1))

if __name__ == '__main__':
    unittest.main(verbosity=2)
