from contextlib import closing
"""Extraction XML ciblée V31, vérification de signature/révision/hachages."""
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'/'unesco_pilot'))
import preuves_xml_v31 as p
import contexte_revue_unesco_v28 as ctx

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        d=Path(self.tmp.name)
        self.xml=d/'wiki.xml';self.stage=d/'stage.sqlite';self.cache=d/'cache.sqlite';self.source=d/'source.sqlite'
        self.xml.write_text('''<mediawiki xmlns="http://www.mediawiki.org/xml/export-0.11/">
        <siteinfo><sitename>Wikipedia</sitename></siteinfo>
        <page><title>University of Example</title><ns>0</ns><id>1</id><revision><id>101</id><text xml:space="preserve">\nUniversity of Example is an [[educational institution]].\nIt provides university education and research for students. </text></revision></page>
        <page><title>Other</title><ns>0</ns><id>2</id><revision><id>202</id><text>Unrelated topics</text></revision></page>
        </mediawiki>''',encoding='utf-8')
        with closing(sqlite3.connect(self.stage)) as db, db:
            db.execute('CREATE TABLE candidates(page_id INTEGER)')
            db.executemany('INSERT INTO candidates VALUES(?)',[(1,),(2,)])
        with closing(sqlite3.connect(self.source)) as db, db:
            db.execute('CREATE TABLE wiki_pages(page_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT,latest_revision INTEGER)')
            db.executemany('INSERT INTO wiki_pages VALUES(?,?,?,?)',[(1,0,'University_of_Example',101),(2,0,'Other',999)])

    def test_extract_cache_and_revision_check(self):
        result=p.run(self.xml,self.stage,self.cache,text_chars=1000)
        self.assertEqual(result['new_excerpts'],2)
        self.assertEqual(p.run(self.xml,self.stage,self.cache)['new_excerpts'],0)
        with closing(sqlite3.connect(self.cache)) as db, db, closing(sqlite3.connect(self.source)) as source, source:
            db.row_factory=sqlite3.Row
            good=ctx._prepared_article_v31(db,source,1,['university','research'])
            bad=ctx._prepared_article_v31(db,source,2,['anything'])
            self.assertEqual(good['etat'],'texte_source_verifie')
            self.assertEqual(good['revision_id'],101)
            self.assertEqual(bad['etat'],'revision_xml_differente')
            db.execute("UPDATE prepared_pages SET wikitext='TAMPERED' WHERE page_id=1")
            db.commit()
            self.assertEqual(ctx._prepared_article_v31(db,source,1,['x'])['etat'],'cache_v31_empreinte_incoherente')

    def test_xml_source_drift_is_detected(self):
        p.run(self.xml,self.stage,self.cache)
        self.xml.write_text(self.xml.read_text()+'\n',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'changé'):
            p.run(self.xml,self.stage,self.cache)

if __name__=='__main__':unittest.main(verbosity=2)
