"""Regression tests of lexical quality v0.4: only synthetic data and stdlib."""
import csv
from contextlib import closing
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

LIB = Path(__file__).resolve().parents[1]/'tools'/'dictionary-harvester'
sys.path.insert(0,str(LIB))
import lexical_indexer as ix
import quality_audit as qa


class QualityFixture(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        for folder in ('10_sources/lexical/unimorph/repos','20_evidence','30_working','50_mediatheque'):
            (self.root/folder).mkdir(parents=True,exist_ok=True)
        self.db=self.root/ix.SUBDIR/'lexical.sqlite3'
        con=ix.connect(self.db)
        sources=[
            (1,'10_sources/lexical/wiktionary/kaikki/raw-editions/en/a.jsonl.gz','kaikki','en','complete',4),
            (2,'10_sources/lexical/unimorph/repos/eng.zip','unimorph','eng','complete',2),
            (3,'10_sources/lexical/wikidata/lexemes/dumps/current/latest-lexemes.json.bz2','wikidata','wikidata-lexemes','complete',2),
            (4,'10_sources/lexical/unimorph/repos/pib.zip','unimorph','pib','no_data',0),
            (5,'10_sources/lexical/unimorph/repos/sdh.zip','unimorph','sdh','no_data',0)]
        with con:
            con.executemany('''INSERT INTO source_files
                (id,relative_path,kind,edition,size_bytes,mtime_ns,status,cursor_lines,accepted,rejected)
                VALUES (?,?,?,?,?,123,?,0,?,0)''',[(i,p,k,e,10,status,n) for i,p,k,e,status,n in sources])
            entries=[
                (1,1,'en','hello','Hello'),
                (1,2,'en','house','House'),
                (1,3,'fr','chat','Chat'),
                (1,4,'en','home','home'),
                (2,1,'en','hello','hello'),
                (2,2,'en','hello','HELLO'),
                (3,1,'en','hello','hello'),
                (3,2,'fr','chat','chat')]
            con.executemany('''INSERT INTO entries (
                source_id,source_line,language_code,lemma_key,lemma,
                sense_observations,form_observations,translation_observations)
                VALUES (?,?,?,?,?,0,0,0)''',entries)
            for sid,lang,num in [(1,'en',3),(1,'fr',1),(2,'en',2),(3,'en',1),(3,'fr',1)]:
                con.execute('''INSERT INTO language_stats
                    (source_id,language_code,lemma_observations,sense_observations,
                    form_observations,translation_observations) VALUES (?,?,?,0,0,0)''',(sid,lang,num))
        con.close()
        dest=self.root/'10_sources/lexical/unimorph/repos'
        with zipfile.ZipFile(dest/'pib.zip','w') as z:
            z.writestr('pib-main/README.md','No forms provided')
            z.writestr('pib-main/pib','')
        with zipfile.ZipFile(dest/'sdh.zip','w') as z:
            z.writestr('sdh-main/sdh','xwardin\txwardin\tNFIN;V\n'+'xwardin\txwem\t1;IND;PROG;PRS;SG;V\n')

    def tearDown(self):self.tmp.cleanup()

    def test_per_language_exact_distinct_and_overlap(self):
        with closing(qa.readonly_connection(self.db)) as conn:
            families=qa.source_families(conn)
            stats,examples=qa.audit_language(conn,'en',families)
        self.assertEqual(stats['observation_rows'],6)
        self.assertEqual(stats['distinct_lemma_keys'],3)
        self.assertEqual(stats['repeated_lemma_keys'],1)
        self.assertEqual(stats['extra_observation_rows'],3)
        self.assertEqual(stats['repeated_inside_one_source_keys'],1)
        self.assertEqual(stats['shared_across_files_keys'],1)
        self.assertEqual(stats['shared_across_families_keys'],1)
        self.assertEqual(stats['kaikki_unimorph_keys'],1)
        self.assertEqual(stats['kaikki_wikidata_keys'],1)
        self.assertEqual(stats['unimorph_wikidata_keys'],1)
        self.assertEqual(len(examples),1)
        self.assertEqual(examples[0]['lemma_key'],'hello')
        self.assertEqual(examples[0]['family_count'],3)

    def test_pib_sdh_diagnostic(self):
        with closing(qa.readonly_connection(self.db)) as conn:
            results=qa.diagnostic_unimorph(self.root,conn)
        self.assertEqual(results[0]['code'],'pib')
        self.assertEqual(results[0]['classification'],'no_nonempty_paradigm')
        self.assertEqual(results[1]['classification'],'valid_rows_but_not_indexed')
        self.assertEqual(results[1]['sample_accepted'],2)

    def test_resume_partial_then_full_without_double_count(self):
        first=qa.perform_audit(self.root,languages=['en'],min_free_gb=0,quiet=True)
        interim=Path(json.loads((self.root/qa.QUALITY_SUBDIR/'latest.json').read_text())['report'])
        self.assertIn('PARTIEL',interim.read_text(encoding='utf-8'))
        self.assertFalse(first['complete'])
        self.assertEqual(first['languages_audited'],1)
        again=qa.perform_audit(self.root,languages=['en'],min_free_gb=0,quiet=True)
        self.assertEqual(again['languages_audited'],1)
        last=qa.perform_audit(self.root,min_free_gb=0,quiet=True)
        self.assertTrue(last['complete'])
        self.assertEqual(last['languages_audited'],2)
        totals=last['totals_for_audited_languages']
        self.assertEqual(totals['observation_rows'],8)
        self.assertEqual(totals['distinct_lemma_keys'],4)
        self.assertEqual(totals['extra_observation_rows'],4)
        run=Path(json.loads((self.root/qa.QUALITY_SUBDIR/'latest.json').read_text())['run_dir'])
        with (run/'languages_quality.csv').open('r',encoding='utf-8-sig') as f:
            table=list(csv.DictReader(f))
        self.assertEqual(len(table),2)
        self.assertTrue((run/'DIAGNOSTIC_PIB_SDH.md').is_file())
        self.assertIn('COMPLET', (run/'RAPPORT_QUALITE_LEXICALE.md').read_text(encoding='utf-8'))
        with (run/'overlap_examples.csv').open(encoding='utf-8-sig',newline='') as f:
            overlap=list(csv.DictReader(f))
        self.assertIn('source_paths_sample',overlap[0])

    def test_new_fingerprint_when_source_catalog_changes(self):
        a=qa.perform_audit(self.root,languages=['en'],min_free_gb=0,quiet=True)
        con=sqlite3.connect(self.db)
        with con:con.execute("UPDATE source_files SET size_bytes=size_bytes+1 WHERE edition='pib'")
        con.close()
        b=qa.perform_audit(self.root,languages=['en'],min_free_gb=0,quiet=True)
        self.assertNotEqual(a['source_catalog_fingerprint'],b['source_catalog_fingerprint'])
        self.assertEqual(b['languages_audited'],1)
        runs=list((self.root/qa.QUALITY_SUBDIR/'runs').iterdir())
        self.assertEqual(len(runs),2)

    def test_reject_unknown_language_without_changing_index(self):
        before=self.db.stat().st_size
        with self.assertRaisesRegex(ValueError,'absents'):
            qa.perform_audit(self.root,languages=['zz'],min_free_gb=0)
        self.assertEqual(self.db.stat().st_size,before)


if __name__=='__main__':unittest.main()
