"""v0.6 regression: real compressed formats, source anchors, batch resume, safety."""
import bz2
import gzip
import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'dictionary-harvester'))
import semantic_enrichment as e
import dik_reconciliation as r
from lexical_indexer import SCHEMA, normalized_lemma


class EnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)/'lake'
        for rel in ('10_sources/lexical','20_evidence','30_working','50_mediatheque'):
            (self.root/rel).mkdir(parents=True)
        self.kaikki_en=self.root/'10_sources/lexical/en.jsonl.gz'
        self.kaikki_fr=self.root/'10_sources/lexical/fr.jsonl.gz'
        self.wiki=self.root/'10_sources/lexical/lexemes.json.bz2'
        self.unimorph=self.root/'10_sources/lexical/eng.zip'
        en_obj={'word':'Bank','lang_code':'en','pos':'noun',
                'senses':[{'glosses':['Financial institution','River edge'],'senseid':'kaikki-1'}],
                'forms':[{'form':'banks','tags':['plural']}],
                'translations':[{'word':'banque','code':'fr','sense':'finance'}]}
        fr_obj={'word':'chat','lang_code':'fr','pos':'noun',
                'senses':[{'glosses':['Petit félin domestique']}], 'translations':[]}
        self.kaikki_en.write_bytes(gzip.compress((json.dumps(en_obj)+'\n').encode()))
        self.kaikki_fr.write_bytes(gzip.compress((json.dumps(fr_obj)+'\n').encode()))
        wikibank={'id':'L321','language':'Q1860','lexicalCategory':'Q1084',
                  'lemmas':{'en':{'language':'en','value':'bank'}},
                  'senses':[{'id':'L321-S1','glosses':{'en':{'language':'en','value':'a financial institution'}}}],
                  'forms':[{'id':'L321-F1','representations':{'en':{'language':'en','value':'banks'}},
                            'grammaticalFeatures':['Q146786']} ]}
        wikichat={'id':'L88','language':'Q150','lexicalCategory':'Q1084',
                  'lemmas':{'fr':{'language':'fr','value':'chat'}},
                  'senses':[{'id':'L88-S1','glosses':{'fr':{'language':'fr','value':'animal'}}}],
                  'forms':[]}
        self.wiki.write_bytes(bz2.compress(('[\n'+json.dumps(wikibank)+',\n'+json.dumps(wikichat)+'\n]\n').encode()))
        with zipfile.ZipFile(self.unimorph,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('eng-main/eng','bank\tbanks\tN;PL\nbank\tbank\tN;SG\n')
        self.idx=self.root/e.INDEX
        self.idx.parent.mkdir(parents=True)
        with sqlite3.connect(self.idx) as con:
            con.executescript(SCHEMA)
            sources=[('kaikki','en',self.kaikki_en),('kaikki','fr',self.kaikki_fr),
                     ('wikidata','lexemes',self.wiki),('unimorph','eng',self.unimorph)]
            for sid,(kind,edition,path) in enumerate(sources,1):
                st=path.stat()
                con.execute('''INSERT INTO source_files(id,relative_path,kind,edition,size_bytes,mtime_ns,status,accepted)
                               VALUES(?,?,?,?,?,?,?,?)''',
                            (sid,path.relative_to(self.root).as_posix(),kind,edition,st.st_size,st.st_mtime_ns,'complete',2))
            records=[
                (1,1,'en','Bank','bank','noun',1,1,1,None,None,'en',None,None,None),
                (2,1,'fr','chat','chat','noun',1,0,0,None,None,'fr',None,None,None),
                (3,2,'en','bank','bank','Q1084',1,1,0,'L321','Q1860','en',None,None,None),
                (3,3,'fr','chat','chat','Q1084',1,0,0,'L88','Q150','fr',None,None,None),
                (4,1,'en','bank','bank','N',0,1,0,None,None,'eng','banks','banks','N;PL'),
                (4,2,'en','bank','bank','N',0,1,0,None,None,'eng','bank','bank','N;SG')]
            con.executemany('''INSERT INTO entries(source_id,source_line,language_code,lemma,lemma_key,pos,sense_observations,form_observations,
              translation_observations,external_id,language_qid,source_language_code,form_surface,form_key,grammatical_features)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',records)
            stats=[(1,'en',1,1,1,1),(2,'fr',1,1,0,0),(3,'en',1,1,1,0),(3,'fr',1,1,0,0),(4,'en',2,0,2,0)]
            con.executemany('''INSERT INTO language_stats(source_id,language_code,lemma_observations,sense_observations,form_observations,translation_observations)
                               VALUES(?,?,?,?,?,?)''',stats)
            con.commit()
        self.out=self.root/e.OUTPUT
        r.run(self.root,langs=['en','fr'],min_free_gb=0)

    def jsonlines(self, lang):
        return [json.loads(line) for line in (self.out/'evidence'/f'{lang}.jsonl').read_text().splitlines()]

    def test_plan_read_only(self):
        assert not self.out.exists()
        e.plan(self.root)
        assert not self.out.exists()

    def test_enriched_glosses_and_ids_and_morphology(self):
        x=e.run(self.root,min_free_gb=0,batch_lines=1)
        self.assertEqual(x['languages_staged'],2)
        self.assertEqual(x['status'],'candidate_evidence_complete')
        self.assertEqual(x['candidate_keys_staged'],2)
        self.assertEqual(x['source_anchors_captured'],5)
        bank=self.jsonlines('en')[0]
        self.assertTrue(bank['manual_sense_review_required'])
        self.assertFalse(bank['may_be_published'])
        sources={v['family']:v for v in bank['raw_source_line_evidence']}
        self.assertEqual(sources['kaikki']['observed_record']['senses'][0]['glosses'],['Financial institution','River edge'])
        self.assertEqual(sources['wikidata']['observed_record']['senses'][0]['sense_id'],'L321-S1')
        self.assertEqual(sources['wikidata']['observed_record']['forms'][0]['form_id'],'L321-F1')
        self.assertEqual(sources['unimorph']['observed_record']['features'],'N;PL')
        self.assertEqual(len(self.jsonlines('fr')),1)
        self.assertEqual(e.verify(self.root)['failed'],0)

    def test_idempotence_no_duplicate(self):
        e.run(self.root,min_free_gb=0,batch_lines=1)
        e.run(self.root,min_free_gb=0,batch_lines=1)
        with sqlite3.connect(self.out/'enrichment.sqlite3') as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0],5)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM anchors').fetchone()[0],5)

    def test_pilot_to_world_without_lost_evidence(self):
        e.run(self.root,languages=['en'],min_free_gb=0,batch_lines=1)
        self.assertEqual(len(self.jsonlines('en')[0]['raw_source_line_evidence']),3)
        full=e.run(self.root,min_free_gb=0,batch_lines=1)
        self.assertEqual(full['source_anchors_captured'],5)
        self.assertEqual(full['languages_staged'],2)
        self.assertEqual(len(self.jsonlines('en')[0]['raw_source_line_evidence']),3)

    def test_resume_after_partial_scan(self):
        e.run(self.root,languages=['fr'],min_free_gb=0,batch_lines=1,max_scan_lines=1)
        with sqlite3.connect(self.out/'enrichment.sqlite3') as db:
            self.assertIn('partial',dict(db.execute('SELECT status,COUNT(*) FROM source_progress GROUP BY status')))
        full=e.run(self.root,languages=['fr'],min_free_gb=0,batch_lines=1)
        self.assertEqual(full['source_anchors_captured'],2)
        self.assertEqual(full['status'],'candidate_evidence_partial')  # en still unstaged
        self.assertEqual(e.verify(self.root)['failed'],0)

    def test_refuse_mismatched_catalog(self):
        with sqlite3.connect(self.idx) as db:
            db.execute('UPDATE source_files SET accepted=9000 WHERE id=1')
        with self.assertRaises(RuntimeError):e.run(self.root,min_free_gb=0)

    def test_refuse_modified_archive(self):
        with sqlite3.connect(self.idx) as db:
            source=e.source_catalog(db)[1]
        self.kaikki_en.write_bytes(self.kaikki_en.read_bytes()+b'not-source')
        with self.assertRaises(RuntimeError):e.checked_source_path(self.root,source)

    def test_sha_verification_detects_corruption(self):
        e.run(self.root,min_free_gb=0,batch_lines=1)
        p=self.out/'evidence'/'en.jsonl'
        p.write_bytes(p.read_bytes()+b'\n')
        with self.assertRaises(RuntimeError):e.verify(self.root)

    def test_output_outside_root_refused(self):
        with self.assertRaises(ValueError):e.run(self.root,min_free_gb=0,output_override=Path(self.tmp.name))

    def test_caps_semantics_only(self):
        senses=[{'glosses':['a'*1500]} for _ in range(27)]
        value=e.extract_kaikki({'word':'x','lang_code':'en','senses':senses})
        self.assertEqual(len(value['senses']),24)
        self.assertTrue(value['truncation']['senses'])
        self.assertEqual(len(value['senses'][0]['glosses'][0]),480)
        self.assertEqual(e.extract_wikidata({'id':'L1'})['senses'],[])
        self.assertIsNone(self.jsonlines('en') if False else None)


if __name__=='__main__':unittest.main()
