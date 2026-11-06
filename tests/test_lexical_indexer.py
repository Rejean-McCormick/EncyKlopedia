"""No external network; test candidate indexer against synthetic zipped, bz2 and gz fixtures."""
import bz2
import gzip
import importlib.util
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('lexidx',ROOT/'tools/dictionary-harvester/lexical_indexer.py')
indexer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(indexer)

class IndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='ency-lexical-test-')
        self.root=Path(self.tmp.name)
        for d in ['10_sources/lexical','20_evidence','30_working','50_mediatheque']:
            (self.root/d).mkdir(parents=True,exist_ok=True)
        self.kaikki=self.root/'10_sources/lexical/wiktionary/kaikki/raw-editions/en'
        self.kaikki.mkdir(parents=True)
        self.gz=self.kaikki/'raw-wiktextract-data.jsonl.gz'
        with gzip.open(self.gz,'wt',encoding='utf-8') as f:
            f.write(json.dumps({'word':'chat','lang_code':'fr','pos':'noun','senses':[{'glosses':['cat']}], 'forms':[{'form':'chats'}], 'translations':[{'word':'cat'}]})+'\n')
            f.write('invalid json\n')
            f.write(json.dumps({'word':'dog','lang_code':'en','senses':[{},{}]})+'\n')
        self.zipdir=self.root/'10_sources/lexical/unimorph/repos'
        self.zipdir.mkdir(parents=True)
        self.zip=self.zipdir/'fra.zip'
        with zipfile.ZipFile(self.zip,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('fra-main/README.md','Documentation')
            z.writestr('fra-main/fra','aller\tvais\tV;IND;PRS;1;SG\naller\tva\tV;IND;PRS;3;SG\n')
        self.wddir=self.root/'10_sources/lexical/wikidata/lexemes/dumps/current'
        self.wddir.mkdir(parents=True)
        self.wd=self.wddir/'latest-lexemes.json.bz2'
        lexeme={'id':'L123','type':'lexeme','lemmas':{'fr':{'language':'fr','value':'maison'}},'lexicalCategory':'Q1084','language':'Q150','forms':[{},{}], 'senses':[{}]}
        with bz2.open(self.wd,'wt',encoding='utf-8') as f:
            f.write('[\n'+json.dumps(lexeme)+',\n]\n')
        self.db=self.root/'30_working/lexical/harvester/index-v1/lexical.sqlite3'
    def tearDown(self):self.tmp.cleanup()
    def runindex(self,limit=None):
        result=indexer.main(['run','--data-root',str(self.root),'--min-free-gb','0']+(['--max-lines-per-source',str(limit)] if limit else []))
        return result
    def test_valid_data_root(self):self.assertEqual(indexer.valid_lake(self.root),self.root)
    def test_discovery_covers_three_types(self):
        self.assertEqual({x['kind'] for x in indexer.source_candidates(self.root)}, {'kaikki','wikidata','unimorph'})
        self.assertEqual(len(indexer.source_candidates(self.root)),3)
    def test_unimorph_main_file_only(self):
        with zipfile.ZipFile(self.zip) as z:self.assertEqual(indexer.unimorph_member(z,'fra').filename,'fra-main/fra')
    def test_normalize_wiktextract(self):
        self.assertEqual(indexer.parse_kaikki(json.dumps({'word':'CHAT','lang_code':'fr-CA','senses':[{}]}))[:5],('fr-ca','CHAT','chat','',1))
        self.assertIsNone(indexer.parse_kaikki('{}'))
    def test_normalize_wikidata(self):
        obj={'id':'L3','lemmas':{'en':{'value':'house'}},'language':'Q1860','forms':[1,2], 'senses':[1]}
        self.assertEqual(indexer.parse_wikidata(json.dumps(obj))[7],'L3')
        self.assertEqual(indexer.parse_wikidata(json.dumps(obj))[5],2)
    def test_morph(self):
        self.assertEqual(indexer.parse_morph('aller\tvais\tV;PRS;1','fra')[0],'fr')
        self.assertEqual(indexer.parse_morph('aller\tvais\tV;PRS;1','fra')[10],'vais')
        self.assertIsNone(indexer.parse_morph('x\ty','fra'))
    def test_full_index(self):
        self.assertEqual(self.runindex(),0)
        con=sqlite3.connect(self.db)
        self.assertEqual(con.execute('SELECT COUNT(*) FROM entries').fetchone()[0],5)
        self.assertEqual(con.execute('SELECT SUM(rejected) FROM source_files').fetchone()[0],3) # invalid JSON, WD brackets
        self.assertEqual(con.execute('SELECT COUNT(*) FROM source_files WHERE status="complete"').fetchone()[0],3)
        self.assertEqual(con.execute('SELECT SUM(form_observations) FROM entries').fetchone()[0],5)
        con.close()
        rep=json.loads((self.db.parent/'latest.json').read_text('utf-8'))
        self.assertEqual(rep['number_of_source_files'],3)
        self.assertFalse(rep['canonical_dictionary'])
        self.assertFalse(rep['published'])
        self.assertFalse(rep['source_licenses_reviewed'])
        self.assertEqual(rep['number_of_observed_language_codes'],2)
    def test_idempotent(self):
        self.runindex();self.runindex()
        con=sqlite3.connect(self.db)
        self.assertEqual(con.execute('SELECT COUNT(*) FROM entries').fetchone()[0],5)
        con.close()
    def test_resume_partial(self):
        self.runindex(limit=1)
        con=sqlite3.connect(self.db)
        self.assertEqual(con.execute('SELECT COUNT(*) FROM entries').fetchone()[0],2) # Kaikki first + WD bracket => 0 + UniMorph 1
        self.assertEqual(con.execute('SELECT COUNT(*) FROM source_files WHERE status="partial"').fetchone()[0],3)
        con.close()
        self.runindex()
        con=sqlite3.connect(self.db)
        self.assertEqual(con.execute('SELECT COUNT(*) FROM entries').fetchone()[0],5)
        con.close()
    def test_stale_source_not_silently_overwritten(self):
        self.runindex()
        with gzip.open(self.gz,'at') as f:f.write(json.dumps({'word':'z','lang_code':'en'})+'\n')
        self.runindex()
        con=sqlite3.connect(self.db)
        self.assertEqual(con.execute('SELECT COUNT(*) FROM entries').fetchone()[0],5)
        self.assertEqual(con.execute("SELECT status FROM source_files WHERE kind='kaikki'").fetchone()[0],'stale')
        con.close()
    def test_malformed_zip_no_data(self):
        with zipfile.ZipFile(self.zipdir/'epo.zip','w') as z:z.writestr('epo-main/README.md','empty')
        self.runindex()
        con=sqlite3.connect(self.db)
        self.assertEqual(con.execute("SELECT status FROM source_files WHERE edition='epo'").fetchone()[0],'no_data')
        con.close()
    def test_no_fake_approval_or_crosswalk(self):
        self.runindex()
        handoff=json.loads((self.db.parent/'dik-source-handoff.candidate.json').read_text('utf-8'))
        self.assertFalse(handoff['may_be_published'])
        self.assertEqual(handoff['status'],'unreviewed_candidate')
    def test_raw_files_untouched(self):
        before=(self.gz.read_bytes(),self.zip.read_bytes(),self.wd.read_bytes())
        self.runindex()
        self.assertEqual(before,(self.gz.read_bytes(),self.zip.read_bytes(),self.wd.read_bytes()))
    def test_code_validation(self):
        self.assertEqual(indexer.code('pt_BR'),'pt-br')
        self.assertEqual(indexer.code('fra'),'fr')
        self.assertEqual(indexer.code('deu'),'de')
        self.assertEqual(indexer.code('bad/iso'),'und')
        self.assertEqual(indexer.normalized_lemma('  ÉTÉ  '),('ÉTÉ','été'))
    def test_lookup(self):
        self.runindex()
        self.assertEqual(indexer.main(['lookup','--data-root',str(self.root),'--query','chat','--language','fr']),0)
        self.assertEqual(indexer.main(['lookup','--data-root',str(self.root),'--query','vais','--language','fr','--match','form']),0)
    def test_no_root_refuses_missing(self):
        with tempfile.TemporaryDirectory() as dir:
            with self.assertRaises(ValueError): indexer.valid_lake(Path(dir))

if __name__=='__main__':unittest.main()
