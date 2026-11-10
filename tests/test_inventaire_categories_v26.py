import csv
import hashlib
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'tools'/'unesco_pilot'))
import inventaire_categories_v26 as v

class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.source=self.base/'wikipedia.sqlite'
        c=sqlite3.connect(self.source)
        c.executescript('''
          CREATE TABLE wiki_linktargets(target_id INTEGER PRIMARY KEY,ns INTEGER NOT NULL,title TEXT NOT NULL);
          CREATE INDEX idx_wiki_lt_title ON wiki_linktargets(ns,title);
          CREATE TABLE wiki_pages(page_id INTEGER PRIMARY KEY,ns INTEGER NOT NULL,title TEXT NOT NULL,
                                  redirect INTEGER,latest_revision INTEGER,content_bytes INTEGER);
          CREATE INDEX idx_wiki_pages_title ON wiki_pages(ns,title);
          CREATE TABLE wiki_categorylink_ids(source_page_id INTEGER NOT NULL,target_id INTEGER NOT NULL,type TEXT);
          CREATE INDEX idx_wiki_catid_target ON wiki_categorylink_ids(target_id);
          CREATE TABLE ingest_state(stage TEXT,completed INTEGER);
          INSERT INTO ingest_state VALUES ('page',1),('page_props',1),('linktarget',1),('categorylinks',1);
          INSERT INTO wiki_linktargets VALUES
             (101,14,'Educational_policy'),(102,14,'Curriculum_development'),
             (103,14,'School_reform'),(104,14,'Wikipedians_by_type'),(7,0,'Unrelated');
          INSERT INTO wiki_pages VALUES
             (1,0,'Education_reform',0,100,500),
             (2,0,'National_curriculum',0,101,400),
             (3,14,'School_curriculum',0,102,300),
             (4,0,'Curriculum_history',0,103,150),
             (5,14,'School_reform',0,104,200),
             (6,14,'Orphan_school_category',0,105,200);
          INSERT INTO wiki_categorylink_ids VALUES
             (1,101,'page'),(2,102,'page'),(3,102,'subcat'),(4,103,'page');
        ''')
        c.commit();c.close()
        self.out=self.base/'derived.sqlite'
        self.ref=self.base/'concepts.json'
        self.ref.write_text(json.dumps({'concepts':[
         {'unesco_id':'concept9','preferred_labels':{'en':['Educational policy'],'fr':['Politique educative']}},
         {'unesco_id':'concept7273','preferred_labels':{'en':['Curriculum development'],'fr':['Developpement des programmes']}},
         {'unesco_id':'concept7282','preferred_labels':{'en':['Educational reform'],'fr':['Reforme educative']}}]
        }),encoding='utf8')
        self.dest=self.base/'exports'
    def run_cli(self,cmd,*more):
        return v.main([cmd,'--source-db',str(self.source),'--inventory-db',str(self.out),
                       '--output-dir',str(self.dest),'--concepts',str(self.ref),*map(str,more)])
    def test_indexed_scan_resumption_and_complete(self):
        self.assertEqual(self.run_cli('scan','--max-rows','2','--batch-size','1'),0)
        c=sqlite3.connect(self.out)
        self.assertEqual(c.execute('select count(*) from categories').fetchone()[0],2)
        c.close()
        self.assertEqual(self.run_cli('scan','--max-rows','2','--batch-size','1'),0)
        self.assertEqual(self.run_cli('scan','--max-rows','100','--batch-size','2'),0)
        c=sqlite3.connect(self.out)
        rows=c.execute('select title,origin from categories order by title').fetchall()
        self.assertEqual(len(rows),6)
        self.assertEqual(dict(rows)['Orphan_school_category'],'CATEGORY_PAGE_ONLY')
        self.assertEqual(c.execute("select value from meta where key='done'").fetchone()[0],'1')
        c.close()
        self.assertEqual(self.run_cli('scan','--max-rows','10'),0)
    def test_export_sample_and_pseudo_orphan(self):
        self.assertEqual(self.run_cli('scan-export','--max-rows','100','--batch-size','2'),0)
        with ZipFile(self.dest/'EXPORT_INVENTAIRE_V26_POUR_CHATGPT.zip') as z:
            man=json.loads(z.read('MANIFEST_SHA256.json'))
            for name,digest in man['sha256'].items():
                self.assertEqual(hashlib.sha256(z.read(name)).hexdigest(),digest)
            rows=list(csv.DictReader(io.StringIO(z.read('CANDIDATS_UNESCO_V26.csv').decode('utf-8-sig'))))
            self.assertTrue(any(r['category_title']=='Educational policy' and r['concept_id']=='concept9' for r in rows))
            self.assertTrue(any('National curriculum' in r['example_articles'] for r in rows))
            self.assertTrue(any('School curriculum' in r['example_subcategories'] for r in rows))
            report=json.loads(z.read('RAPPORT_INVENTAIRE_V26.json'))
            self.assertTrue(report['inventory_complete'])
            self.assertEqual(report['raw_wikipedia_articles_included'],0)
    def test_refuse_symlink_inventory_destination(self):
        real=self.base/'real_destination.sqlite'
        sqlite3.connect(real).close()
        link=self.base/'inventory_link.sqlite'
        try:
            link.symlink_to(real)
        except (OSError,NotImplementedError):
            self.skipTest('La plateforme ne permet pas les liens symboliques')
        self.out=link
        self.assertEqual(self.run_cli('scan','--max-rows','3'),2)
        with sqlite3.connect(real) as db:
            tables=db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        self.assertEqual(tables,[])

    def test_refuse_changed_source_metadata(self):
        self.assertEqual(self.run_cli('scan','--max-rows','3'),0)
        c=sqlite3.connect(self.source)
        c.execute("INSERT INTO wiki_linktargets VALUES(110,14,'Teacher_policies')");c.commit();c.close()
        self.assertEqual(self.run_cli('scan','--max-rows','3'),2)
    def test_no_overwrite_existing_unrelated_sqlite(self):
        c=sqlite3.connect(self.out);c.execute('create table foreign_table(id)');c.close()
        self.assertEqual(self.run_cli('scan','--max-rows','3'),2)
    def test_bad_source_stages(self):
        c=sqlite3.connect(self.source);c.execute("UPDATE ingest_state SET completed=0 WHERE stage='categorylinks'");c.commit();c.close()
        self.assertEqual(self.run_cli('scan','--max-rows','3'),2)
    def test_targeted_probe_reusable_without_rescan(self):
        self.assertEqual(self.run_cli('scan','--max-rows','100'),0)
        q=self.base/'queries.json'
        q.write_text(json.dumps({'schema':'encyklopedia.category-probe-request.v26/1',
            'queries':[{'term':'School reform','max_results':25}], 'category_ids':[101]}))
        self.assertEqual(self.run_cli('probe','--queries-file',q),0)
        self.assertEqual(self.run_cli('probe','--queries-file',q),0)
        files=list(self.dest.glob('RESULTATS_REQUETES_V26_*.zip'))
        self.assertEqual(len(files),1)
        with ZipFile(files[0]) as z:
            rows=list(csv.DictReader(io.StringIO(z.read('RESULTATS_REQUETES_V26.csv').decode('utf-8-sig'))))
            self.assertTrue(any(r['category_title']=='School reform' for r in rows))
            self.assertTrue(any(r['category_title']=='Educational policy' for r in rows))

    def test_import_selections_only_produces_file(self):
        self.assertEqual(self.run_cli('scan','--max-rows','100'),0)
        c=sqlite3.connect(self.out)
        s=v.mv(c,'source_signature')
        c.close()
        decisions=self.base/'decision.json'
        decisions.write_text(json.dumps({'schema':'encyklopedia.category-review.v26/1',
          'source_signature':s,'unesco_sha256':hashlib.sha256(self.ref.read_bytes()).hexdigest(),
          'decisions':[{'concept_id':'concept9','category_id':101,'category_title':'Educational policy',
                       'decision':'INCLUDE','justification':'Relation semantique directe examinee par IA.','depth_limit':0}]}))
        self.assertEqual(self.run_cli('import-decisions','--decisions',decisions),0)
        rows=list(self.dest.glob('PONTS_REVUS_V26_*.csv'))
        self.assertEqual(len(rows),1)
        self.assertIn('ACTIVE_REVIEWED_AI',rows[0].read_text(encoding='utf-8-sig'))
        self.assertEqual(self.run_cli('import-decisions','--decisions',decisions),0)
    def test_orphan_category_cannot_be_activated_without_target(self):
        self.assertEqual(self.run_cli('scan','--max-rows','100'),0)
        c=sqlite3.connect(self.out)
        s=v.mv(c,'source_signature');c.close()
        decisions=self.base/'decision.json'
        decisions.write_text(json.dumps({'schema':'encyklopedia.category-review.v26/1',
          'source_signature':s,'unesco_sha256':hashlib.sha256(self.ref.read_bytes()).hexdigest(),
          'decisions':[{'concept_id':'concept9','category_id':-6,'category_title':'Orphan school category',
                       'decision':'INCLUDE','justification':'La categorie n\'a pas un target d\'adhesion.','depth_limit':0}]}))
        self.assertEqual(self.run_cli('import-decisions','--decisions',decisions),2)

if __name__=='__main__':unittest.main()
