import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'dictionary-harvester'))
import dik_reconciliation as m
from lexical_indexer import SCHEMA


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'D'
        for s in ('10_sources/lexical','20_evidence','30_working','50_mediatheque'):
            (self.root/s).mkdir(parents=True,exist_ok=True)
        self.idx=self.root/'30_working/lexical/harvester/index-v1/lexical.sqlite3'
        self.idx.parent.mkdir(parents=True)
        con=sqlite3.connect(self.idx)
        con.executescript(SCHEMA)
        con.executemany('INSERT INTO source_files(id,relative_path,kind,edition,size_bytes,mtime_ns,status,accepted,rejected) VALUES(?,?,?,?,?,?,?,?,?)',[
            (1,'10_sources/lexical/kaikki.jsonl.gz','kaikki','en',400,10,'complete',4,0),
            (2,'10_sources/lexical/unimorph.zip','unimorph','eng',400,10,'complete',4,0),
            (3,'10_sources/lexical/wikidata.json.bz2','wikidata','lexemes',400,10,'complete',2,0)])
        records=[
            (1,1,'en','bank','bank','noun',1,0,0,None,None,'en',None,None,None),
            (1,2,'en','Apple','apple','noun',1,0,0,None,None,'en',None,None,None),
            (1,3,'fr','chat','chat','noun',1,0,0,None,None,'fr',None,None,None),
            (2,1,'en','bank','bank','N',0,1,0,None,None,'eng','banks','banks','N;PL'),
            (2,2,'en','bank','bank','N',0,1,0,None,None,'eng','bank','bank','N;SG'),
            (2,3,'fr','chien','chien','N',0,1,0,None,None,'fra','chiens','chiens','N;PL'),
            (3,1,'en','bank','bank','Q1084',1,4,0,'L321','Q1860','en',None,None,None),
            (3,2,'fr','chat','chat','Q1084',1,4,0,'L88','Q150','fr',None,None,None)]
        con.executemany('''INSERT INTO entries(source_id,source_line,language_code,lemma,lemma_key,pos,sense_observations,form_observations,translation_observations,external_id,language_qid,source_language_code,form_surface,form_key,grammatical_features) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',records)
        con.executemany('''INSERT INTO language_stats(source_id,language_code,lemma_observations,sense_observations,form_observations,translation_observations) VALUES(?,?,?,?,?,?)''',[(1,'en',2,2,0,0),(1,'fr',1,1,0,0),(2,'en',2,0,2,0),(2,'fr',1,0,1,0),(3,'en',1,1,4,0),(3,'fr',1,1,4,0)])
        con.commit();con.close()

    def test_pilot_candidate_counts(self):
        out=m.run(self.root,langs=['en','fr'],min_free_gb=0)
        self.assertEqual(out['cross_family_candidate_keys'],2)
        self.assertEqual(out['languages_staged'],2)
        self.assertEqual(out['languages_total'],2)
        rows=[json.loads(x) for x in (self.root/m.OUTPUT/'candidates/en.jsonl').read_text().splitlines()]
        self.assertEqual(len(rows),1)
        r=rows[0]
        self.assertEqual(r['source_families'],['kaikki','unimorph','wikidata'])
        self.assertEqual(r['observations'],4)
        self.assertIsNone(r['relationship'])
        self.assertEqual(r['source_observations_sample']['wikidata'][0]['wikidata_lexeme_id'],'L321')
        self.assertEqual(len(r['source_observations_sample']['unimorph']),1)
        self.assertEqual(len(r['source_observations_sample']['kaikki']),1)
        self.assertFalse(r['source_license_reviewed'])
        self.assertTrue((self.root/m.OUTPUT/'source_license_review_queue.csv').is_file())

    def test_resume_without_duplicate(self):
        first=m.run(self.root,langs=['en'],min_free_gb=0)
        second=m.run(self.root,langs=['fr'],min_free_gb=0)
        third=m.run(self.root,min_free_gb=0)
        self.assertEqual((first['languages_staged'],second['languages_staged'],third['languages_staged']),(1,2,2))
        with sqlite3.connect(self.root/m.OUTPUT/'reconciliation.sqlite3') as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0],2)

    def test_source_input_readonly(self):
        before=hashlib.sha256(self.idx.read_bytes()).digest()
        m.run(self.root,langs=['en'],min_free_gb=0)
        after=hashlib.sha256(self.idx.read_bytes()).digest()
        self.assertEqual(before,after)

    def test_signature_guard(self):
        m.run(self.root,langs=['en'],min_free_gb=0)
        with sqlite3.connect(self.idx) as db:
            db.execute("UPDATE source_files SET accepted=12 WHERE id=1")
        with self.assertRaises(RuntimeError):m.run(self.root,langs=['fr'],min_free_gb=0)

    def test_zero_candidate(self):
        with sqlite3.connect(self.idx) as db:
            db.execute("UPDATE entries SET lemma='Unique',lemma_key='unique' WHERE source_id=3 AND language_code='fr'")
        out=m.run(self.root,langs=['fr'],min_free_gb=0)
        self.assertEqual(out['cross_family_candidate_keys'],0)
        self.assertFalse((self.root/m.OUTPUT/'candidates/fr.jsonl').exists())

    def test_id_deterministic(self):
        self.assertEqual(m.candidate_id('en','bank'),m.candidate_id('en','bank'))
        self.assertNotEqual(m.candidate_id('en','bank'),m.candidate_id('fr','bank'))

    def test_unsafe_lang_rejected(self):
        with self.assertRaises(ValueError):m.safe_lang_filename('../foo')

    def test_requires_root(self):
        with self.assertRaises(ValueError):m.run(Path(self.tmp.name)/'missing',min_free_gb=0)

    def test_min_disk_guard(self):
        with self.assertRaises(RuntimeError):m.run(self.root,min_free_gb=999999)

    def test_export_verification(self):
        m.run(self.root,min_free_gb=0)
        report=m.verify_exports(self.root)
        self.assertEqual(report['failed'],0)
        self.assertEqual(report['passed'],2)
        out=self.root/m.OUTPUT/'candidates/en.jsonl'
        out.write_bytes(out.read_bytes()+b'\n')
        with self.assertRaises(RuntimeError):m.verify_exports(self.root)

    def test_review_queue_explicitly_unapproved(self):
        m.run(self.root,langs=['en'],min_free_gb=0)
        manifest=json.loads((self.root/m.OUTPUT/'dik-review-queue.candidate.json').read_text())
        self.assertFalse(manifest['may_be_published'])
        self.assertEqual(manifest['approved_matches'],0)
        self.assertTrue(manifest['requires_human_sense_review'])

    def test_report_labels_no_public(self):
        x=m.run(self.root,min_free_gb=0)
        self.assertEqual(x['diK_integration'],'review_queue_only_not_normative_export')
        self.assertIn('NE PAS PUBLIER',(self.root/m.OUTPUT/'RAPPORT_RECONCILIATION.md').read_text())

if __name__=='__main__':unittest.main()
