"""Pure offline fixture tests. NO access to D: or actual Wikimedia DB."""
import bz2
import csv
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
M_PATH=ROOT/'tools/wiki/atlas/atlas_wikipedia.py'
SPEC=importlib.util.spec_from_file_location('wiki_atlas_v19',M_PATH)
M=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def fixture(base):
    db=base/'wiki.sqlite';inv=base/'inventory.json';cache=base/'cache';cache.mkdir()
    with sqlite3.connect(db) as c:
        c.executescript('''
          CREATE TABLE wiki_pages(page_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT,redirect INTEGER,latest_revision INTEGER,content_bytes INTEGER);
          CREATE TABLE wiki_qid(page_id INTEGER PRIMARY KEY,qid TEXT);
          CREATE TABLE wiki_linktargets(target_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT);
          CREATE TABLE wiki_pagelinks(source_page_id INTEGER,target_id INTEGER);
          CREATE TABLE wiki_externallinks(link_id INTEGER PRIMARY KEY,source_page_id INTEGER,target_url TEXT,raw_domain_index TEXT);
          CREATE TABLE wiki_categorylink_ids(source_page_id INTEGER,target_id INTEGER,type TEXT);
          CREATE TABLE ingest_state(stage TEXT PRIMARY KEY,filename TEXT,source_bytes INTEGER,source_mtime_ns INTEGER,
                  committed_line INTEGER,rows_imported INTEGER,completed INTEGER,finished_at TEXT,sha256 TEXT,schema_json TEXT);
          CREATE INDEX idx_wiki_pages_title ON wiki_pages(ns,title);
          CREATE INDEX idx_wiki_pagelinks_from ON wiki_pagelinks(source_page_id);
          CREATE INDEX idx_wiki_lt_title ON wiki_linktargets(ns,title);
          CREATE INDEX idx_wiki_qid_qid ON wiki_qid(qid);
          CREATE INDEX idx_wiki_external_from ON wiki_externallinks(source_page_id);
          CREATE INDEX idx_wiki_catid_from ON wiki_categorylink_ids(source_page_id);
        ''')
        for i,s in enumerate(['Right_to_education','Educational_policy','Education_reform',
                             'Education_finance','Wikipedia','Illiteracy'],1):
            c.execute('INSERT INTO wiki_pages VALUES(?,?,?,?,?,?)',
                      (i,0,s,1 if i==6 else 0,101+i,1000))
        c.executemany('INSERT INTO wiki_qid VALUES(?,?)',[(1,'Q69370'),(2,'Q9999')])
        c.executemany('INSERT INTO wiki_linktargets VALUES(?,?,?)',
                      [(10,0,'Educational_policy'),(11,0,'Education_reform'),
                       (12,0,'Education_finance'),(13,0,'Wikipedia'),
                       (14,0,'Illiteracy'),(15,14,'Education_policy')])
        c.executemany('INSERT INTO wiki_pagelinks VALUES(?,?)',
                      [(1,10),(1,11),(1,13),(1,14),(2,12),(3,12)])
        c.execute('INSERT INTO wiki_categorylink_ids VALUES(?,?,?)',(1,15,'page'))
        c.execute('INSERT INTO wiki_externallinks VALUES(?,?,?,?)',
                  (99,1,'https://example.org/needs-validation','example.org'))
        for stage in ('page','page_props','linktarget','externallinks','pagelinks','categorylinks'):
            c.execute('INSERT INTO ingest_state VALUES(?,?,?,?,?,?,?,?,?,?)',
                      (stage,'fixture',0,0,0,10,1,'','',''))
    records=[]
    for i in range(41):
        uid='concept10' if i==0 else ('concept9' if i==1 else 'concept'+str(1000+i))
        label='Right to education' if i==0 else ('Educational policy' if i==1 else f'No matching concept {i}')
        records.append({'unesco_id':uid,'unesco_preferred_labels':{'en':[label]},
                        'wikidata':{'qid':'Q69370' if i==0 else ('Q9999' if i==1 else None)},
                        'wikipedia_en_inventory':[]})
    inv.write_text(json.dumps({'branch':'unesco-mt1-10','records':records}),encoding='utf8')
    txt=b'Right to education is a foundational right.\n== Scope ==\nExample section.'
    (cache/'page-1.wikitext.txt').write_bytes(txt)
    (cache/'manifest.json').write_text(json.dumps({'pages':[
        {'page_id':1,'relative_path':'page-1.wikitext.txt','sha256':M.sha(txt),'revision_id':'102'}]}))
    return db,inv,cache


class AtlasTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.db,self.inv,self.cache=fixture(self.root)
        self.out=self.root/'atlas'

    def build(self):
        r=M.main(['build','--db',str(self.db),'--inventory',str(self.inv),'--out',str(self.out),
                  '--max-pages','10','--max-links','10','--depth','2'])
        self.assertEqual(r,0)

    def test_full_atlas_ro_and_repeat(self):
        before=self.db.read_bytes();self.build()
        self.assertEqual(before,self.db.read_bytes())
        self.assertEqual(M.main(['audit','--atlas',str(self.out)]),0)
        m=json.loads((self.out/'manifest.json').read_text())
        self.assertEqual(m['concept_anchors'],41)
        self.assertEqual(m['seed_pages'],2)
        self.assertGreaterEqual(m['outbound_edges_observed'],3)
        self.assertEqual(m['no_approved_KQ_KP_KA_KS'],True)
        self.assertEqual(M.main(['build','--db',str(self.db),'--inventory',str(self.inv),'--out',str(self.out)]),0)
        self.assertEqual(before,self.db.read_bytes())
        with (self.out/'pages.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
        self.assertIn('Education reform',[p['title'] for p in rows])
        self.assertTrue((self.out/'categories.csv').read_bytes())

    def test_index_and_text_lot_and_intake(self):
        self.build()
        self.assertEqual(M.main(['index-zip','--atlas',str(self.out)]),0)
        self.assertEqual(M.main(['index-zip','--atlas',str(self.out)]),0)
        self.assertEqual(M.main(['pack','--atlas',str(self.out),'--cache',str(self.cache)]),0)
        zf=self.root/'atlas_LOT_001_CHATGPT.zip'
        with zipfile.ZipFile(zf) as z:
            m=json.loads(z.read('LOT_MANIFEST.json'))
            self.assertGreater(m['texts_available'],0)
            self.assertIn('articles/page-1.wikitext.txt',z.namelist())
            example=json.loads(z.read('MODELE_PROPOSITIONS_CHATGPT.json'))
            self.assertEqual(example['proposals'],[])
        self.assertEqual(M.main(['pack','--atlas',str(self.out),'--cache',str(self.cache)]),0)

    def test_missing_index_does_not_full_scan(self):
        self.build()
        self.assertEqual(M.main(['pack','--atlas',str(self.out),'--cache',str(self.root/'empty'),
                                 '--try-multistream','--xml-dir',str(self.root/'absent')]),0)
        with zipfile.ZipFile(self.root/'atlas_LOT_001_CHATGPT.zip') as z:
            m=json.loads(z.read('LOT_MANIFEST.json'))
            self.assertEqual(m['texts_available'],0)

    def test_missing_sql_index_blocked(self):
        with sqlite3.connect(self.db) as c:c.execute('DROP INDEX idx_wiki_pagelinks_from')
        self.assertEqual(M.main(['build','--db',str(self.db),'--inventory',str(self.inv),
                                 '--out',str(self.out)]),2)
        self.assertFalse(self.out.exists())

    def test_audit_tamper_blocked(self):
        self.build()
        with (self.out/'pages.csv').open('ab') as f:f.write(b'EXTRA')
        self.assertEqual(M.main(['audit','--atlas',str(self.out)]),2)

    def test_inventory_wrong_branch(self):
        raw=json.loads(self.inv.read_text());raw['branch']='other';self.inv.write_text(json.dumps(raw))
        self.assertEqual(M.main(['build','--db',str(self.db),'--inventory',str(self.inv),
                                 '--out',str(self.out)]),2)

    def test_indexed_multistream(self):
        page=b'<page><title>Education finance</title><ns>0</ns><id>4</id><revision><id>105</id><text>Funding article</text></revision></page>'
        s1=bz2.compress(b'<mediawiki><page><title>Other</title><ns>0</ns><id>555</id></page></mediawiki>')
        s2=bz2.compress(b'<mediawiki>'+page+b'</mediawiki>')
        xml=self.root/'enwiki-latest-pages-articles-multistream.xml.bz2';xml.write_bytes(s1+s2)
        idx=self.root/'enwiki-latest-pages-articles-multistream-index.txt.bz2'
        idx.write_bytes(bz2.compress((str(len(s1))+':4:Education finance\n').encode()))
        got,missing=M.from_multistream(xml,idx,{4},{4:{'revision_id':'105'}})
        self.assertEqual(got[4]['text'],b'Funding article')
        self.assertEqual(missing,{})

    def test_no_unlimited_depth(self):
        self.assertEqual(M.main(['build','--db',str(self.db),'--inventory',str(self.inv),
                                 '--out',str(self.out),'--depth','10']),2)


if __name__=='__main__':unittest.main()
