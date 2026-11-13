"""Validation of additive UNESCO v28 evidence, no production DB touched."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'tools'/'unesco_pilot'
spec=importlib.util.spec_from_file_location('encystation_context_test',TOOLS/'poste_chatgpt_v30.py')
stationmod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(stationmod)
import sys
sys.path.insert(0,str(TOOLS))
import production_kristals_v27 as v27
import catalogue_global_v25 as v25

class ExtraReviewEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.work=root/'work'
        self.work.mkdir()
        self.stage=root/'v28'/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        self.stage.parent.mkdir()
        with sqlite3.connect(self.stage) as con:
            con.executescript('''CREATE TABLE evidence(branch_id,concept_id,page_id,seed_page_id,kind,detail);
                CREATE TABLE seed_queue(branch_id,page_id,title);''')
            con.execute('INSERT INTO seed_queue VALUES(?,?,?)',('unesco.mt1.10',123,'Education in Paris'))
            con.execute('INSERT INTO evidence VALUES(?,?,?,?,?,?)',
                        ('unesco.mt1.10','concept8',456,123,'WIKILINK','[[Educational reform]]'))
        self.row={'candidate_id':'V28_context_test','branch_id':'unesco.mt1.10','concept_id':'concept8',
                  'concept_en':'Educational development','page_id':456,'title':'Educational reform',
                  'priority':55,'seed_count':1,'link_evidence':1,'category_evidence':0,
                  'subcategory_evidence':0,'evidence_sha256':'seedhash','examples':'Education in Paris:WIKILINK',
                  'decision':'HOLD','justification':''}
        self.source_raw=stationmod.csv_bytes([self.row])
        self.source=self.work/'source.csv'
        self.source.write_bytes(self.source_raw)
        self.bundle=self.work/'v28_context_test.zip'
        with zipfile.ZipFile(self.bundle,'w') as z:
            z.writestr('REVUE_v28_context_test.csv',self.source_raw)
            z.writestr('PROMPT_CHATGPT.txt','Revise all rows.')
        self.orig=self.bundle.read_bytes()
        self.station=stationmod.Station(ROOT,self.work,root/'v27',self.stage.parent,root/'cat.sqlite')
        self.addCleanup(self.station.db.close)
        with self.station.db:
            self.station.db.execute('''INSERT INTO jobs(id,kind,key,count,status,source_path,source_sha256,
                bundle_path,bundle_sha256,created_utc) VALUES(?,?,?,?,?,?,?,?,?,?)''',
                ('v28_context_test','v28','v28_context_test',1,'READY',str(self.source),
                stationmod.sha(self.source_raw),str(self.bundle),stationmod.sha(self.orig),stationmod.now()))
        self.old_xml=v27.DEFAULT_XML
        self.old_index=v27.DEFAULT_INDEX
        self.old_source=v25.DEFAULT_SOURCE
        self.addCleanup(self.restore_sources)
        v27.DEFAULT_XML=root/'absent.xml'
        v27.DEFAULT_INDEX=root/'absent.sqlite'
        v25.DEFAULT_SOURCE=root/'absent_source.sqlite'

    def restore_sources(self):
        v27.DEFAULT_XML=self.old_xml
        v27.DEFAULT_INDEX=self.old_index
        v25.DEFAULT_SOURCE=self.old_source

    def test_fallback_preserves_job_and_source(self):
        result=self.station.bundle('v28_context_test')
        self.assertNotEqual(result,self.bundle)
        self.assertEqual(self.bundle.read_bytes(),self.orig)
        self.assertEqual(self.source.read_bytes(),self.source_raw)
        with zipfile.ZipFile(result) as z:
            self.assertEqual(z.read('REVUE_v28_context_test.csv'),self.source_raw)
            manifest=json.loads(z.read('MANIFEST_CONTEXTE_V28.json'))
            context=json.loads(z.read('CONTEXTES_DOCUMENTAIRES_V28.jsonl').decode('utf-8'))
            self.assertEqual(manifest['nombre_candidats'],1)
            self.assertEqual(manifest['extraits_xml_valides'],0)
            self.assertIn('source absent',manifest['information_xml'])
            self.assertEqual(context['candidate_id'],self.row['candidate_id'])
            self.assertTrue(context['concept']['note_portee_en'])
            self.assertEqual(context['evidence'][0]['article_source'],'Education in Paris')
        self.assertEqual(self.station.bundle('v28_context_test'),result)
        self.assertEqual(self.station._row('v28_context_test')['bundle_sha256'],stationmod.sha(self.orig))

    def test_xml_index_produces_verified_excerpt_and_invalidates_cache(self):
        from xml.sax.saxutils import escape
        # First download while XML is missing; then make it available.
        first=self.station.bundle('v28_context_test')
        with zipfile.ZipFile(first) as z:
            self.assertEqual(json.loads(z.read('MANIFEST_CONTEXTE_V28.json'))['extraits_xml_valides'],0)
        xml=self.stage.parent/'fixture.xml'
        wikitext="'''Educational reform''' refers to changes to public educational institutions. [[Schools]] are included."
        payload=(f'<page><title>Educational reform</title><ns>0</ns><id>456</id>'
                 f'<revision><id>789</id><text>{escape(wikitext)}</text></revision></page>').encode('utf-8')
        xml.write_bytes(payload)
        idx=self.stage.parent/'fixture_index.sqlite'
        v27.DEFAULT_XML=xml;v27.DEFAULT_INDEX=idx
        sig=v27.xml_signature(xml)
        with sqlite3.connect(idx) as con:
            con.execute('CREATE TABLE v21_meta(name TEXT PRIMARY KEY,value TEXT)')
            con.execute('''CREATE TABLE pages(page_id INTEGER PRIMARY KEY,byte_offset INTEGER,byte_length INTEGER,
                         namespace INTEGER,title TEXT,revision_id TEXT,is_redirect INTEGER)''')
            con.executemany('INSERT INTO v21_meta VALUES(?,?)',
                            [('source_signature',json.dumps(sig)),('complete','true')])
            con.execute('INSERT INTO pages VALUES(?,?,?,?,?,?,?)',(456,0,len(payload),0,'Educational reform','789',0))
        second=self.station.bundle('v28_context_test')
        self.assertEqual(first,second)
        with zipfile.ZipFile(second) as z:
            manifest=json.loads(z.read('MANIFEST_CONTEXTE_V28.json'))
            context=json.loads(z.read('CONTEXTES_DOCUMENTAIRES_V28.jsonl').decode('utf-8'))
            self.assertEqual(manifest['extraits_xml_valides'],1)
            self.assertEqual(context['article']['etat'],'texte_source_verifie')
            self.assertIn('public educational institutions',context['article']['texte_intro'])
            self.assertEqual(context['article']['revision_id'],'789')
            self.assertEqual(z.read('REVUE_v28_context_test.csv'),self.source_raw)
        self.assertEqual(self.bundle.read_bytes(),self.orig)

if __name__=='__main__':unittest.main()
