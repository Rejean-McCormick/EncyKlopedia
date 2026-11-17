#!/usr/bin/env python3
"""Tests isolés de la sauvegarde SQLite résultats — sans aucune base utilisateur."""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
import json
import sqlite3
import tempfile
import unittest
import encyk_sauvegarde as b

class TestsResultats(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.home=Path(t.name)
        self.data=self.home/'Donnees'/'EncyKlopedia';self.data.mkdir(parents=True)
        self.out=self.home/'HorsProduction'/'Sauvegardes'
        self.dbpaths=[]
        for index,(role,rel,required) in enumerate(b.RESULTS+b.DERIVED_RESULTS):
            p=self.data/rel;p.parent.mkdir(parents=True,exist_ok=True)
            with closing(sqlite3.connect(p)) as c,c:
                c.execute('CREATE TABLE t(id INTEGER PRIMARY KEY,value TEXT)')
                c.execute('INSERT INTO t VALUES(?,?)',(index,f'valeur {index}'))
                if role=='STATION':
                    c.execute('CREATE TABLE jobs(status TEXT)');c.execute("INSERT INTO jobs VALUES('DONE')")
                if role=='KRISTAL_PRIVE':
                    c.execute('CREATE TABLE claims(id INT)');c.execute('INSERT INTO claims VALUES(1)')
                    c.execute('CREATE TABLE citations(id INT)');c.execute('INSERT INTO citations VALUES(1)')
                if role=='CATALOGUE_UNESCO':
                    c.execute('CREATE TABLE articles(id INT)');c.execute('INSERT INTO articles VALUES(1)')
                    c.execute('CREATE TABLE assignments(id INT)');c.execute('INSERT INTO assignments VALUES(1)')
            self.dbpaths.append((role,p))
        # Gros fichiers et fichiers de travail : même dans des répertoires voisins, jamais inclus.
        self.xml=self.data/'30_working'/'wikipedia_en_uncompressed'/'enwiki-big.xml'
        self.xml.parent.mkdir(parents=True);self.xml.write_text('source Wikipedia')
        self.pack=self.data/'30_working'/'production_kristals_v27'/'packs'/'PACK_V27_000280.zip'
        self.pack.parent.mkdir(parents=True);self.pack.write_bytes(b'PACK')
        self.delta=self.data/'30_working'/'production_kristals_v27'/'deltas'/'DELTA_V27.json'
        self.delta.parent.mkdir(parents=True);self.delta.write_bytes(b'DELTA')
        self.response=self.data/'30_working'/'poste_chatgpt_v30'/'returns'/'return.zip'
        self.response.parent.mkdir(parents=True);self.response.write_bytes(b'RETOUR')
        self.code=self.home/'Code'/'EncyKlopedia';self.code.mkdir(parents=True)
        (self.code/'program.py').write_text('code')
    def args(self,cmd='backup',closed=True,derived=False):
        return SimpleNamespace(command=cmd,data_root=self.data,destination=self.out,
                               station_fermee=closed,avec_index_derive=derived)
    def snapshot(self,derived=False):
        self.assertEqual(b.save(self.args(derived=derived)),0)
        folds=list(self.out.glob('ENCYK_RESULTATS_*'))
        self.assertEqual(len(folds),1)
        obj=json.loads((folds[0]/'MANIFEST_RESULTATS.json').read_text('utf-8'))
        return folds[0],obj
    def test_copies_only_whitelist_results(self):
        folder,obj=self.snapshot()
        self.assertEqual(len(obj['bases']),len(b.RESULTS))
        self.assertEqual(b.verify(folder)['databases'],len(b.RESULTS))
        self.assertFalse(obj['includes_wikipedia_sources'])
        self.assertFalse(obj['includes_packs_returns_or_deltas'])
        self.assertFalse(obj['includes_program_code'])
        for entry in obj['bases']:
            self.assertNotIn('inventaire_categories',entry['backup_path'])
            self.assertNotIn('packs',entry['backup_path'])
            self.assertNotIn('returns',entry['backup_path'])
            self.assertNotIn('deltas',entry['backup_path'])
            self.assertNotIn('wikipedia_en_uncompressed',entry['backup_path'])
            with closing(sqlite3.connect(folder/entry['backup_path'])) as c:
                self.assertEqual(c.execute('SELECT count(*) FROM t').fetchone()[0],1)
        self.assertEqual(obj['metrics_from_copies']['station_v30.sqlite']['taches_terminees'],1)
    def test_derived_is_explicit(self):
        folder,obj=self.snapshot(derived=True)
        self.assertEqual(len(obj['bases']),len(b.RESULTS)+len(b.DERIVED_RESULTS))

    def test_five_realistic_databases_two_optional_missing(self):
        for role,rel,_ in b.RESULTS:
            if role in ('QUALIFICATION_V31', 'PREUVES_XML_V31'):
                (self.data/rel).unlink()
        folder,obj=self.snapshot()
        self.assertEqual(len(obj['bases']),5)
        self.assertEqual({x['role'] for x in obj['missing_optional_databases']},
                         {'QUALIFICATION_V31','PREUVES_XML_V31'})
        self.assertEqual(b.verify(folder)['databases'],5)
    def test_sha_tamper_refused(self):
        folder,obj=self.snapshot()
        p=folder/obj['bases'][0]['backup_path']
        with p.open('ab') as f:f.write(b'TAMPER')
        with self.assertRaisesRegex(b.BackupError,'(Taille invalide|SHA-256 invalide)'):
            b.verify(folder)
    def test_missing_core_is_error(self):
        (self.data/b.RESULTS[0][1]).unlink()
        with self.assertRaisesRegex(b.BackupError,'indispensables'):
            b.save(self.args())
        self.assertFalse(self.out.exists())
    def test_preflight_no_copy(self):
        self.assertEqual(b.save(self.args('preflight')),0)
        self.assertFalse(self.out.exists())
    def test_station_must_be_closed(self):
        with self.assertRaisesRegex(b.BackupError,'Fermer la station'):
            b.save(self.args(closed=False))
    def test_inside_source_blocked(self):
        a=self.args();a.destination=self.data/'Backup'
        with self.assertRaisesRegex(b.BackupError,'Destination dangereuse'):
            b.save(a)
    def test_sqlite_wal_snapshot_includes_committed_data(self):
        p=self.data/b.RESULTS[0][1]
        conn=sqlite3.connect(p)
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute("INSERT INTO t VALUES (100,'en WAL')")
            conn.commit()
            dst=self.home/'copie.sqlite'
            b.sqlite_backup(p,dst)
            with closing(sqlite3.connect(dst)) as c:
                self.assertEqual(c.execute('SELECT count(*) FROM t').fetchone()[0],2)
        finally:
            conn.close()
    def test_no_extra_file_in_backup(self):
        folder,obj=self.snapshot()
        (folder/'resultats'/'fichier_imprevu.zip').write_bytes(b'foo')
        with self.assertRaisesRegex(b.BackupError,'Fichier supplementaire'):
            b.verify(folder)

    def test_wal_source_full_backup_is_standalone_without_shm(self):
        # Reproduit exactement l'erreur de la base decouverte en mode WAL.
        source=self.data/b.RESULTS[3][1]
        writer=sqlite3.connect(source)
        try:
            self.assertEqual(writer.execute('PRAGMA journal_mode=WAL').fetchone()[0],'wal')
            writer.execute('PRAGMA wal_autocheckpoint=0')
            writer.execute("INSERT INTO t VALUES(200, 'transaction en WAL')")
            writer.commit()
            self.assertTrue(Path(str(source)+'-wal').exists())
            folder,obj=self.snapshot()
            target=next(folder/item['backup_path'] for item in obj['bases']
                        if item['role']=='DECOUVERTE_UNESCO')
            self.assertFalse(Path(str(target)+'-shm').exists())
            self.assertFalse(Path(str(target)+'-wal').exists())
            with closing(sqlite3.connect(target.resolve().as_uri()+'?mode=ro&immutable=1',uri=True)) as c:
                self.assertEqual(c.execute('PRAGMA journal_mode').fetchone()[0],'delete')
                self.assertEqual(c.execute('SELECT COUNT(*) FROM t').fetchone()[0],2)
            before={str(p.relative_to(folder)):p.stat().st_size for p in folder.rglob('*') if p.is_file()}
            b.verify(folder)
            after={str(p.relative_to(folder)):p.stat().st_size for p in folder.rglob('*') if p.is_file()}
            self.assertEqual(before,after)  # verification strictement sans effets
        finally:
            writer.close()

    def test_strict_verifier_still_refuses_unexpected_sqlite_shm(self):
        folder,obj=self.snapshot()
        target=folder/obj['bases'][0]['backup_path']
        Path(str(target)+'-shm').write_bytes(b'Fichier sqlite supplementaire')
        with self.assertRaisesRegex(b.BackupError,'Fichier supplementaire non declare'):
            b.verify(folder)

    def test_verifier_refuses_wal_header_without_sidecar(self):
        # Un SQLite WAL avec un simple -shm retire ne doit pas etre declare autonome.
        folder,obj=self.snapshot()
        target=folder/obj['bases'][0]['backup_path']
        c=sqlite3.connect(target)
        try:
            self.assertEqual(c.execute('PRAGMA journal_mode=WAL').fetchone()[0],'wal')
            c.commit()
        finally:
            c.close()
        # Recalcul de la taille/empreinte pour tester le controle du mode,
        # sans toucher a la base source ni aux autres fichiers du manifeste.
        manifest_path=folder/'MANIFEST_RESULTATS.json'
        mf=json.loads(manifest_path.read_text('utf-8'))
        item=next(e for e in mf['bases'] if e['backup_path']==obj['bases'][0]['backup_path'])
        item['bytes']=target.stat().st_size
        item['sha256']=b.sha256(target)
        manifest_path.write_text(json.dumps(mf),encoding='utf-8')
        with self.assertRaisesRegex(b.BackupError,'Copie non autonome'):
            b.verify(folder)

if __name__=='__main__':
    unittest.main(verbosity=2)
