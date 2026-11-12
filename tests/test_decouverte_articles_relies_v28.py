"""Tests v28 hors ligne : source SQL/XML synthetique, pas de lecture du vrai D:."""
import contextlib
import csv
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import xml.sax.saxutils as sax

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'unesco_pilot'))
import catalogue_global_v25 as v25
import production_kristals_v27 as v27
import decouvrir_articles_relies_v28 as v28


def page(pid,title,revision,text):
    return (f'<page><title>{sax.escape(title.replace("_"," "))}</title><ns>0</ns><id>{pid}</id>'
            f'<revision><id>{revision}</id><text xml:space="preserve">{sax.escape(text)}</text></revision></page>').encode()


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/'sql.sqlite'
        self.catalogue=self.root/'catalogue.sqlite'
        self.index=self.root/'v21.sqlite'
        self.xml=self.root/'wiki.xml'
        self.work=self.root/'work'
        self.output=self.root/'snapshots'
        self.branch=self.root/'branch.json'
        self.root.joinpath('concepts.json').write_text(json.dumps({'concepts':[
            {'unesco_id':'concept10','preferred_labels':{'en':['Teacher policies'],'fr':['Politiques enseignantes']},'broader':[],'related':[]}
        ]}),encoding='utf-8')
        self.root.joinpath('crosswalk.json').write_text(json.dumps({'mappings':[]}),encoding='utf-8')
        self.root.joinpath('bridges.csv').write_text('concept_id,category_title,status,justification,depth_limit\n',encoding='utf-8')
        self.branch.write_text(json.dumps({'schema':'encyklopedia.branch-manifest.v25/1',
            'branch_id':'unesco.mt1.10.test','branch_version':'1','vocabulary':'unesco',
            'title_fr':'Politique enseignante', 'concepts_file':'concepts.json',
            'crosswalk_file':'crosswalk.json','bridges_file':'bridges.csv','discovery':{
              'auto_exact_category_roots':False,'auto_root_depth':0,'max_reviewed_root_depth':2,
              'max_category_tasks':100,'max_members_per_category':100}}),encoding='utf-8')
        contents={
          1:('Teacher_policies','== Introduction ==\nOverview [[Teacher_training]].\n== Notes ==\nLast section [[Teacher_evaluation]].'),
          2:('Teacher_training','Training of teachers.'),
          3:('Teacher_assessment','Assessment of teachers.'),
          4:('Teacher_innovation','Novel methods.'),
          5:('Teacher_evaluation','Evaluation of teachers.'),
          6:('Teacher_licensing','Licenses.'),
        }
        blob=b'<?xml version="1.0"?><mediawiki>'
        offsets=[]
        for pid,(title,txt) in contents.items():
            record=page(pid,title,1000+pid,txt)
            offsets.append((pid,len(blob),len(record),0,title.replace('_',' '),str(1000+pid),0))
            blob+=record
        blob+=b'</mediawiki>'
        self.xml.write_bytes(blob)
        ix=sqlite3.connect(self.index)
        ix.executescript('''CREATE TABLE v21_meta(name TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE pages(page_id INTEGER PRIMARY KEY,byte_offset INTEGER,byte_length INTEGER,
            namespace INTEGER,title TEXT,revision_id TEXT,is_redirect INTEGER);''')
        for key,val in [('format',v27.V21_FORMAT),('complete',True),('source_signature',v27.xml_signature(self.xml))]:
            ix.execute('INSERT INTO v21_meta VALUES(?,?)',(key,json.dumps(val)))
        ix.executemany('INSERT INTO pages VALUES(?,?,?,?,?,?,?)',offsets)
        ix.commit();ix.close()
        db=sqlite3.connect(self.source)
        db.executescript('''CREATE TABLE wiki_pages(page_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT,redirect INTEGER,latest_revision INTEGER,content_bytes INTEGER);
            CREATE TABLE wiki_qid(page_id INTEGER PRIMARY KEY,qid TEXT NOT NULL);
            CREATE TABLE wiki_linktargets(target_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT);
            CREATE TABLE wiki_categorylink_ids(source_page_id INTEGER,target_id INTEGER,type TEXT);
            CREATE TABLE ingest_state(stage TEXT PRIMARY KEY,completed INTEGER,rows_imported INTEGER);
            CREATE INDEX idx_wiki_pages_title ON wiki_pages(ns,title);
            CREATE INDEX idx_wiki_qid_qid ON wiki_qid(qid);
            CREATE INDEX idx_wiki_lt_title ON wiki_linktargets(ns,title);
            CREATE INDEX idx_wiki_catid_from ON wiki_categorylink_ids(source_page_id);
            CREATE INDEX idx_wiki_catid_target ON wiki_categorylink_ids(target_id);''')
        db.executemany('INSERT INTO wiki_pages VALUES(?,?,?,?,?,?)',[(pid,0,title,0,1000+pid,len(txt)) for pid,(title,txt) in contents.items()])
        db.executemany('INSERT INTO wiki_pages VALUES(?,?,?,?,?,?)',[(20,14,'Teacher_policy_models',0,1020,0),
                                                                     (21,14,'Teacher_innovation_models',0,1021,0)])
        db.executemany('INSERT INTO wiki_linktargets VALUES(?,14,?)',[(100,'Teacher_policy_models'),(101,'Teacher_innovation_models')])
        db.executemany('INSERT INTO wiki_categorylink_ids VALUES(?,?,?)',[(1,100,'page'),(3,100,'page'),
            (21,100,'subcat'),(4,101,'page'),(6,101,'page')])
        db.executemany('INSERT INTO ingest_state VALUES(?,1,50)',[(s,) for s in ('page','page_props','linktarget','categorylinks')])
        db.commit();db.close()
        br=v25.load_branch(self.branch)
        src=v25.source_ro(self.source)
        try:
            info,signature=v25.source_fingerprint(src,self.source)
            cat=v25.open_catalog(self.catalogue)
            try:
                v25.bind_source(cat,signature,info)
                v25.seed_branch(src,cat,br)
            finally:cat.close()
        finally:src.close()

    def args(self,action,**kw):
        class A:pass
        a=A()
        for key,val in dict(source_db=self.source,catalogue_db=self.catalogue,
            index=self.index,xml=self.xml,branch=self.branch,work=self.work,
            catalogue_output=self.output,max_seeds=10,max_links_per_seed=2,
            max_seed_categories=35,max_categories_per_concept=3,
            max_category_size=50,max_neighbors_per_category=5,max_subcategories=2,
            max_export=100,sample_limit=20,decisions=None,dry_run=False).items():
            setattr(a,key,kw.get(key,val))
        return a

    def test_preflight_no_mutation(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(v28.main(['preflight','--source-db',str(self.source),
                '--catalogue-db',str(self.catalogue),'--index',str(self.index),
                '--xml',str(self.xml),'--branch',str(self.branch)]),0)
        self.assertIn('V28_PREFLIGHT_OK',output.getvalue())
        self.assertFalse(self.work.exists())

    def test_wikilink_end_and_category_subcategory(self):
        res=v28.discover(self.args('discover'))
        self.assertEqual(res['seeds_processed_this_run'],1)
        self.assertEqual(res['seeds_pending'],0)
        db=sqlite3.connect(self.work/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite')
        evidence={(r[0],r[1]) for r in db.execute('SELECT page_id,kind FROM evidence')}
        self.assertIn((2,'WIKILINK'),evidence)
        self.assertIn((5,'WIKILINK'),evidence)  # at the very end of the source article
        self.assertIn((3,'SHARED_CATEGORY'),evidence)
        self.assertIn((4,'SUBCATEGORY'),evidence)
        self.assertEqual(v28.discover(self.args('discover'))['new_evidence'],0)
        db.close()

    def review(self,approved=(2,4),reason='Contenu directement lie a la politique des enseignants.'):
        res=v28.export(self.args('export'))
        path=Path(res['csv'])
        with path.open(encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f);rows=list(reader);fields=reader.fieldnames
        self.assertGreaterEqual(len(rows),4)
        for r in rows:
            if int(r['page_id']) in approved:
                r['decision']='APPROVE';r['justification']=reason
        reviewed=self.root/'decisions.csv'
        with reviewed.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
        return reviewed

    def test_apply_idempotent_and_v27_incremental(self):
        v28.discover(self.args('discover'))
        decisions=self.review()
        dry=v28.apply(self.args('apply',decisions=decisions,dry_run=True))
        self.assertEqual(dry['approved'],2)
        with sqlite3.connect(self.catalogue) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM articles').fetchone()[0],1)
        res=v28.apply(self.args('apply',decisions=decisions))
        self.assertEqual(res['new_articles'],2)
        self.assertEqual(res['new_assignments'],2)
        self.assertEqual(res['articles_after'],3)
        again=v28.apply(self.args('apply',decisions=decisions))
        self.assertEqual(again['new_articles'],0)
        self.assertEqual(again['new_approvals'],0)
        self.assertEqual(again['articles_after'],3)
        # The v27 pipeline sees the new v25 sequence without resetting previous packs.
        class B:pass
        b=B();b.catalogue=self.catalogue;b.index=self.index;b.xml=self.xml;b.work=self.root/'v27'
        b.max_articles=12;b.target_words=35000;b.target_bytes=6291456;b.max_packs=2
        vres=v27.produce(b)
        self.assertEqual(sum(p['articles'] for p in vres['packs']),3)
        self.assertEqual(v27.produce(b)['packets_created_this_run'],0)

    def test_tampering_and_decision_rewrite_refused(self):
        v28.discover(self.args('discover'))
        path=self.review(approved=(2,))
        with path.open(encoding='utf-8-sig',newline='') as f:
            rows=list(csv.DictReader(f))
        fields=rows[0].keys()
        rows[0]['evidence_sha256']='0'*64
        with path.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
        with self.assertRaises(v28.Refusal):v28.apply(self.args('apply',decisions=path))
        with sqlite3.connect(self.catalogue) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM articles').fetchone()[0],1)
        # Fresh review and approval cannot be reinterpreted on repeat.
        fresh=self.review(approved=(2,))
        v28.apply(self.args('apply',decisions=fresh))
        # Do not export approved candidates again. Modify the original already-reviewed CSV.
        res=v28.export(self.args('export'))
        with Path(res['csv']).open(encoding='utf-8-sig',newline='') as f:
            pending=list(csv.DictReader(f))
        self.assertNotIn(2,[int(x['page_id']) for x in pending])
        with fresh.open(encoding='utf-8-sig',newline='') as f:
            old_rows=list(csv.DictReader(f))
        for row in old_rows:
            if int(row['page_id'])==2:
                row['justification']='Nouvelle raison differente de la version importee.'
        with fresh.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=old_rows[0].keys())
            writer.writeheader();writer.writerows(old_rows)
        with self.assertRaises(v28.Refusal):v28.apply(self.args('apply',decisions=fresh))

    def test_hold_is_not_a_frozen_decision(self):
        v28.discover(self.args('discover'))
        hold=self.review(approved=())
        with sqlite3.connect(self.catalogue) as cat:
            before=cat.execute("SELECT value FROM meta WHERE key='sequence'").fetchone()[0]
        r=v28.apply(self.args('apply',decisions=hold))
        self.assertEqual(r['status'],'V28_APPLY_NO_ACTION')
        with sqlite3.connect(self.catalogue) as cat:
            after=cat.execute("SELECT value FROM meta WHERE key='sequence'").fetchone()[0]
        self.assertEqual(before,after)
        approved=self.review(approved=(2,))
        self.assertEqual(v28.apply(self.args('apply',decisions=approved))['new_articles'],1)

    def test_isolated_cli_and_review_zip_manifest(self):
        script=Path(v28.__file__)
        flags=['--source-db',str(self.source),'--catalogue-db',str(self.catalogue),
               '--index',str(self.index),'--xml',str(self.xml),'--branch',str(self.branch),
               '--work',str(self.work)]
        result=subprocess.run([sys.executable,'-I',str(script),'discover',*flags],
                              capture_output=True,text=True,check=True)
        self.assertIn('V28_DISCOVERY_OK',result.stdout)
        export=subprocess.run([sys.executable,'-I',str(script),'export',*flags,'--max-export','10'],
                              capture_output=True,text=True,check=True)
        import zipfile
        summary=json.loads(export.stdout)
        self.assertEqual(summary['status'],'V28_EXPORT_OK')
        with zipfile.ZipFile(summary['export_for_chatgpt']) as z:
            manifest=json.loads(z.read('MANIFEST_SHA256_V28.json'))
            for filename,checksum in manifest['sha256'].items():
                self.assertEqual(v28.digest(z.read(filename)),checksum)
        self.assertEqual(v28.status(self.args('status'))['seeds']['DONE'],1)

    def test_approved_pages_seed_new_linked_round(self):
        v28.discover(self.args('discover'))
        reviewed=self.review(approved=(2,4))
        v28.apply(self.args('apply',decisions=reviewed))
        result=v28.discover(self.args('discover'))
        self.assertEqual(result['seed_queue_new_or_changed'],2)
        self.assertEqual(result['seeds_processed_this_run'],2)
        self.assertEqual(result['seeds_pending'],0)
        self.assertEqual(v28.discover(self.args('discover'))['seeds_processed_this_run'],0)

    def test_resume_seed_queue_and_source_guard(self):
        first=v28.discover(self.args('discover',max_seeds=1,max_links_per_seed=3))
        self.assertEqual(first['seeds_pending'],0)
        self.assertEqual(first['seed_queue_new_or_changed'],1)
        self.assertEqual(v28.discover(self.args('discover',max_seeds=1))['seeds_processed_this_run'],0)
        # Explicit branch manifest edit must be refused.
        obj=json.loads(self.branch.read_text(encoding='utf-8'))
        obj['branch_version']='different'
        self.branch.write_text(json.dumps(obj),encoding='utf-8')
        with self.assertRaises(v25.Refusal):v28.discover(self.args('discover'))


    def change_xml_revision(self, pid, original, replacement):
        """Simulate SQL / XML revision drift while keeping v21 index consistent."""
        old=(f'<revision><id>{original}</id><text').encode('utf-8')
        new=(f'<revision><id>{replacement}</id><text').encode('utf-8')
        self.assertEqual(len(old),len(new))
        body=self.xml.read_bytes()
        self.assertEqual(body.count(old),1)
        self.xml.write_bytes(body.replace(old,new,1))
        with sqlite3.connect(self.index) as ix:
            ix.execute('UPDATE pages SET revision_id=? WHERE page_id=?',(str(replacement),pid))
            ix.execute('UPDATE v21_meta SET value=? WHERE name=?',
                       (json.dumps(v27.xml_signature(self.xml)),'source_signature'))

    def test_sql_xml_revision_mismatch_audited_without_refusal(self):
        self.change_xml_revision(1,1001,1991)
        with sqlite3.connect(self.catalogue) as c:
            before=c.execute('SELECT revision_id FROM articles WHERE page_id=1').fetchone()[0]
        res=v28.discover(self.args('discover'))
        self.assertEqual(res['seeds_processed_this_run'],1)
        self.assertEqual(res['revision_mismatches_this_run'],1)
        self.assertEqual(res['revision_mismatches_recorded'],1)
        self.assertEqual(res['seeds_pending'],0)
        result=v28.status(self.args('status'))
        self.assertEqual(result['revision_mismatch_examples'][0]['page_id'],1)
        self.assertEqual(result['revision_mismatch_examples'][0]['catalogue_revision'],'1001')
        self.assertEqual(result['revision_mismatch_examples'][0]['xml_revision'],'1991')
        with sqlite3.connect(self.catalogue) as c:
            self.assertEqual(c.execute('SELECT revision_id FROM articles WHERE page_id=1').fetchone()[0],before)
        self.assertEqual(v28.discover(self.args('discover'))['seeds_processed_this_run'],0)

    def test_resume_old_workspace_after_revision_mismatch(self):
        # Page 1 was already completed by the initial v28 deployment.
        self.change_xml_revision(5,1005,1995)
        first=v28.discover(self.args('discover',max_seeds=1))
        self.assertEqual(first['seeds_processed_this_run'],1)
        with sqlite3.connect(self.work/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite') as work:
            previous_evidence=work.execute('SELECT count(*) FROM evidence').fetchone()[0]
            work.execute('DROP TABLE seed_revision_mismatches')  # legacy v28 working schema
        br=v25.load_branch(self.branch)
        with sqlite3.connect(self.source) as src, sqlite3.connect(self.catalogue) as cat:
            src.row_factory=sqlite3.Row
            p=src.execute('SELECT * FROM wiki_pages WHERE page_id=5').fetchone()
            v25.associate(cat,br['id'],br['vocab'],'concept10',p,70,
                          'TEST','additional previously queued seed')
            v25.tick(cat)
        second=v28.discover(self.args('discover',max_seeds=2))
        self.assertEqual(second['seeds_processed_this_run'],1)
        self.assertEqual(second['revision_mismatches_this_run'],1)
        self.assertEqual(second['revision_mismatches_recorded'],1)
        self.assertEqual(second['seeds_pending'],0)
        with sqlite3.connect(self.work/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite') as work:
            self.assertEqual(work.execute("SELECT count(*) FROM seed_queue WHERE state='DONE'").fetchone()[0],2)
            self.assertGreaterEqual(work.execute('SELECT count(*) FROM evidence').fetchone()[0],previous_evidence)
            row=work.execute('SELECT catalogue_revision,xml_revision FROM seed_revision_mismatches WHERE page_id=5').fetchone()
            self.assertEqual(row,('1005','1995'))
        self.assertEqual(v28.discover(self.args('discover'))['seeds_processed_this_run'],0)

    def test_xml_v21_revision_mismatch_still_refused(self):
        # A mismatch between SQL catalogue and XML is allowed; a mismatch
        # BETWEEN the v21 index and XML is not allowed under any circumstances.
        old=b'<revision><id>1001</id><text'
        new=b'<revision><id>1991</id><text'
        self.xml.write_bytes(self.xml.read_bytes().replace(old,new,1))
        # Keep the v21 source signature current, but deliberately leave the
        # index row's revision_id at 1001 (incorrect for XML revision 1991).
        with sqlite3.connect(self.index) as ix:
            ix.execute('UPDATE v21_meta SET value=? WHERE name=?',
                       (json.dumps(v27.xml_signature(self.xml)),'source_signature'))
        with self.assertRaises((v28.Refusal,v27.Refusal)):
            v28.discover(self.args('discover'))
        state=v28.status(self.args('status'))
        self.assertEqual(state['seeds']['PENDING'],1)
        self.assertEqual(state['candidate_pairs'],0)


if __name__=='__main__':unittest.main()
