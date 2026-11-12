import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import xml.sax.saxutils as sax
import zipfile

HERE = Path(__file__).resolve().parents[1] / 'tools' / 'unesco_pilot'
sys.path.insert(0, str(HERE))
import production_kristals_v27 as p


def sample_page(pid, title, rev, text):
    return (f'<page><title>{sax.escape(title)}</title><ns>0</ns><id>{pid}</id>'
            f'<revision><id>{rev}</id><text xml:space="preserve">{sax.escape(text)}</text></revision>'
            '</page>').encode('utf-8')


class V27Pipeline(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.work = self.root/'work'
        self.catalogue = self.root/'catalog.sqlite'
        self.index = self.root/'index.sqlite'
        self.xml = self.root/'enwiki.xml'
        self.orig = {}
        articles = [
            (11, 'Right_to_education', '9991', '== Lead ==\nEducation is a right.\n'+'Text data. '*100+'\n== Further reading ==\nIMPORTANT_LAST_PARAGRAPH'),
            (22, 'Teacher_policy', '9992', '== Schools ==\nTeacher policies vary.\n'+'Details. '*120+'\n== Notes ==\nTHE_END_MUST_BE_PRESENT'),
            (33, 'Educational_reform', '9993', '== History ==\n'+('Large passage and evidence. '*600)+'\n== Conclusion ==\nDON_NOT_TRUNCATE'),
        ]
        blob=b'<?xml version="1.0"?><mediawiki>'
        offsets=[]
        for pid,title,rev,txt in articles:
            content = sample_page(pid,title,rev,txt)
            offsets.append((pid, len(blob), len(content), 0, title, rev, 0))
            self.orig[pid]=txt.encode('utf-8')
            blob+=content
        blob+=b'</mediawiki>'
        self.xml.write_bytes(blob)
        signature=p.xml_signature(self.xml)
        con=sqlite3.connect(self.index)
        con.execute('CREATE TABLE v21_meta(name TEXT PRIMARY KEY,value TEXT NOT NULL)')
        con.execute('CREATE TABLE pages(page_id INTEGER PRIMARY KEY,byte_offset INTEGER,byte_length INTEGER,namespace INTEGER,title TEXT,revision_id TEXT,is_redirect INTEGER)')
        for key,val in [('format',p.V21_FORMAT),('complete',True),('source_signature',signature)]:
            con.execute('INSERT INTO v21_meta VALUES(?,?)',(key,json.dumps(val)))
        con.executemany('INSERT INTO pages VALUES(?,?,?,?,?,?,?)',offsets)
        con.commit();con.close()
        con=sqlite3.connect(self.catalogue)
        con.execute('CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)')
        for key,val in [('schema',p.CAT_FORMAT),('source_sha','SOURCE_SQL_SHA'),('sequence','33')]:
            con.execute('INSERT INTO meta VALUES(?,?)',(key,val))
        con.execute('''CREATE TABLE articles(wiki TEXT,page_id INTEGER,title TEXT,qid TEXT,revision_id TEXT,content_bytes INTEGER,PRIMARY KEY(wiki,page_id))''')
        con.execute('''CREATE TABLE assignments(branch_id TEXT,wiki TEXT,page_id INTEGER,vocabulary TEXT,concept_id TEXT,score INTEGER,evidence_kind TEXT,evidence_origin TEXT,root_category TEXT)''')
        con.execute('CREATE INDEX idx_assgn_article ON assignments(wiki,page_id,score DESC)')
        for pid,title,rev,txt in articles:
            con.execute('INSERT INTO articles VALUES(?,?,?,?,?,?)',('enwiki',pid,title,'Q'+str(pid),rev,len(txt)))
            con.execute('INSERT INTO assignments VALUES(?,?,?,?,?,?,?,?,?)',('unesco.mt1.10','enwiki',pid,'unesco','concept10',80,'AI_BRIDGE','Category:Education','Education'))
        # same article, different branch -> no duplication
        con.execute('INSERT INTO assignments VALUES(?,?,?,?,?,?,?,?,?)',('unesco.mt1.20','enwiki',11,'unesco','concept500',50,'ANOTHER','Another category','Another'))
        con.commit();con.close()

    def tearDown(self):
        self.temp.cleanup()

    def args(self, **kw):
        class A: pass
        a=A()
        for k,v in dict(catalogue=self.catalogue,index=self.index,xml=self.xml,work=self.work,
                        max_articles=2,target_words=1800,target_bytes=1200000,max_packs=1).items():
            setattr(a,k,kw.get(k,v))
        return a

    def make_delta(self, pack, *, source=None, obj='right', exact_sha=True, claim_count=1):
        with zipfile.ZipFile(pack) as z:
            man=json.loads(z.read('MANIFEST_PACK_V27.json'))
        article = source or man['articles'][0]
        claims=[]
        for x in range(claim_count):
            claims.append({'source_page_id':article['page_id'], 'source_revision_id':article['revision_id'],
                           'subject_ref':'enwiki:'+str(article['page_id']), 'predicate':'has_policy_aim',
                           'object':{'type':'text','value':obj+str(x)},
                           'statement_en':'This article describes a particular policy aim '+str(x)+'.',
                           'unesco_concepts':['concept10'], 'source_locator':'Lead', 'source_quote':'',
                           'confidence':'high'})
        data={'format':p.DELTA_FORMAT,'pack_id':man['pack_id'],
              'pack_sha256':p.hash_file(pack) if exact_sha else 'WRONG',
              'producer':'ChatGPT GPT-6','claims':claims,
              'coverage_note':'selective'}
        path=self.root/(man['pack_id']+'_'+obj+'.json')
        path.write_bytes(p.encoded(data))
        return path

    def test_integral_wikitext_tail_and_two_branches(self):
        result = p.produce(self.args(max_packs=3))
        self.assertEqual(result['packets_created_this_run'], 2)
        packs = result['packs']
        with zipfile.ZipFile(packs[0]['path']) as z:
            m=json.loads(z.read('MANIFEST_PACK_V27.json'))
            self.assertEqual(m['articles_count'], 2)
            self.assertEqual(len(m['articles'][0]['assignments']), 2)
            for a in m['articles']:
                self.assertEqual(z.read(a['text_path']),self.orig[a['page_id']])
        with zipfile.ZipFile(packs[1]['path']) as z:
            m=json.loads(z.read('MANIFEST_PACK_V27.json'))
            self.assertEqual(m['articles_count'],1)
            self.assertIn(b'DON_NOT_TRUNCATE',z.read(m['articles'][0]['text_path']))
        self.assertEqual(p.produce(self.args())['packets_created_this_run'],0)

    def test_big_article_own_pack_untruncated(self):
        result=p.produce(self.args(max_packs=3,target_words=100,target_bytes=65536))
        self.assertEqual(result['packets_created_this_run'],3)
        for info in result['packs']:
            m=p.verify_pack(info['path'])
            self.assertEqual(m['articles_count'],1)
        self.assertGreater(result['packs'][2]['words'],100)

    def test_import_idempotent_cumulative_conflicts_and_export(self):
        built=p.produce(self.args(max_packs=2))
        pack=Path(built['packs'][0]['path'])
        delta=self.make_delta(pack)
        class I: pass
        inp=I();inp.pack=pack;inp.delta=delta;inp.work=self.work
        result=p.import_delta(inp)
        self.assertEqual(result['new_unique_claims'],1)
        self.assertEqual(p.import_delta(inp)['status'],'V27_DELTA_DEJA_CUMULE')
        second=self.make_delta(pack,obj='different')
        inp.delta=second
        other=p.import_delta(inp)
        self.assertEqual(other['new_unique_claims'],1)
        rep=p.report(self.work)
        self.assertEqual(rep['unique_claims'],2)
        self.assertEqual(rep['deltas_imported'],2)
        self.assertEqual(rep['potential_multiple_values_same_subject_predicate'],1)
        exp=p.export_store(self.work)
        self.assertEqual(exp['claims'],2)
        self.assertEqual(p.export_store(self.work)['status'],'V27_EXPORT_DEJA_PRESENT')
        self.assertEqual(p.verify_export(exp['directory'])['canonical_admissions'],0)

    def test_reimport_other_pack_same_fact_deduplicates(self):
        built=p.produce(self.args(max_articles=1,max_packs=2))
        claims=[]
        for record in built['packs']:
            path=Path(record['path'])
            delta=self.make_delta(path,obj='common')
            class I: pass
            i=I();i.pack=path;i.delta=delta;i.work=self.work
            claims.append(p.import_delta(i)['new_unique_claims'])
        self.assertEqual(claims,[1,1])  # different source page entity => distinct fact
        self.assertEqual(p.report(self.work)['unique_claims'],2)

    def test_hash_tampered_or_wrong_revision_refused(self):
        built=p.produce(self.args(max_packs=1))
        pack=Path(built['packs'][0]['path'])
        delta=self.make_delta(pack,exact_sha=False)
        class I: pass
        i=I();i.pack=pack;i.delta=delta;i.work=self.work
        with self.assertRaises(p.Refusal):p.import_delta(i)
        good=self.make_delta(pack)
        obj=json.loads(good.read_text())
        obj['claims'][0]['source_revision_id']='123456wrong'
        good.write_bytes(p.encoded(obj))
        with self.assertRaises(p.Refusal):p.import_delta(i)
        self.assertFalse((self.work/'KRISTAL_CUMULATIF_PRIVE_V27.sqlite').exists())

    def test_text_alteration_detected(self):
        built=p.produce(self.args(max_packs=1))
        pack=Path(built['packs'][0]['path'])
        corrupt=self.root/'changed.zip'
        with zipfile.ZipFile(pack) as src,zipfile.ZipFile(corrupt,'w') as out:
            for name in src.namelist():
                raw=src.read(name)
                if name.startswith('articles/'):
                    raw+=b'ALTERED'
                out.writestr(name,raw)
        with self.assertRaises(p.Refusal):p.verify_pack(corrupt)

    def test_refuse_source_changed(self):
        p.produce(self.args(max_packs=1))
        ix=sqlite3.connect(self.index)
        ix.execute("UPDATE v21_meta SET value=? WHERE name='source_signature'",(json.dumps({'modified':True}),))
        ix.commit();ix.close()
        with self.assertRaises(p.Refusal):p.produce(self.args())

    def test_catalogue_incremental_sync_new_article(self):
        p.produce(self.args(max_packs=5))
        cat=sqlite3.connect(self.catalogue)
        cat.execute("INSERT INTO articles VALUES('enwiki',44,'Future_article','Q44','9994',0)")
        cat.execute("INSERT INTO assignments VALUES('unesco.mt1.10','enwiki',44,'unesco','concept9',80,'EXACT','Category:Policy','Policy')")
        cat.execute("UPDATE meta SET value='34' WHERE key='sequence'")
        cat.commit();cat.close()
        # queue sync detects newly available article; lack of XML offset quarantines it.
        result=p.produce(self.args(max_packs=1))
        self.assertEqual(result['packets_created_this_run'],0)
        self.assertEqual(result['queue']['FAILED'],1)
        self.assertEqual(result['queue']['PACKED'],3)

    def test_crash_recovery_orphan_pack(self):
        built=p.produce(self.args(max_packs=1))
        packid=built['packs'][0]['pack_id']
        state=self.work/'FILE_PACKS_V27.sqlite'
        db=sqlite3.connect(state)
        db.execute('DELETE FROM packs WHERE pack_id=?',(packid,))
        db.execute("UPDATE queue SET state='PENDING',pack_id=NULL WHERE pack_id=?",(packid,))
        db.commit();db.close()
        again=p.produce(self.args(max_packs=1))
        self.assertEqual(again['recoveries'],1)
        self.assertEqual(again['packs'][0]['pack_id'],'PACK_V27_000002')

    def test_same_fact_two_sources_one_claim_two_citations(self):
        built=p.produce(self.args(max_packs=1))
        pack=Path(built['packs'][0]['path'])
        with zipfile.ZipFile(pack) as z:
            man=json.loads(z.read('MANIFEST_PACK_V27.json'))
        self.assertEqual(len(man['articles']),2)
        facts=[]
        for a in man['articles']:
            facts.append({'source_page_id':a['page_id'], 'source_revision_id':a['revision_id'],
                          'subject_ref':'unesco:concept10', 'predicate':'concerns',
                          'object':{'type':'entity','value':'unesco:concept9'},
                          'statement_en':'The right to education is related to education policy.',
                          'unesco_concepts':['concept10'], 'source_locator':'Lead',
                          'source_quote':'', 'confidence':'medium'})
        delta=self.root/'twosources.json'
        delta.write_bytes(p.encoded({'format':p.DELTA_FORMAT,'pack_id':man['pack_id'],
                          'pack_sha256':p.hash_file(pack),'producer':'GPT-6',
                          'claims':facts,'coverage_note':'partial'}))
        class I:pass
        i=I();i.pack=pack;i.delta=delta;i.work=self.work
        out=p.import_delta(i)
        self.assertEqual(out['new_unique_claims'],1)
        self.assertEqual(out['new_citations'],2)
        self.assertEqual(p.report(self.work)['unique_claims'],1)

    def test_git_work_directory_refused(self):
        git=self.root/'project'
        (git/'.git').mkdir(parents=True)
        with self.assertRaises(p.Refusal):
            p.produce(self.args(work=git/'work'))

    def test_sync_15000_articles_synthetic(self):
        cat=sqlite3.connect(self.catalogue)
        rows=[('enwiki',pid,'Article_'+str(pid),None,str(pid),120) for pid in range(1000,16000)]
        cat.executemany('INSERT INTO articles VALUES(?,?,?,?,?,?)', rows)
        cat.executemany('INSERT INTO assignments VALUES(?,?,?,?,?,?,?,?,?)',
                        [('unesco.mt1.10','enwiki',pid,'unesco','concept9',75,'CATEGORY','Category:Policy','Policy')
                         for pid in range(1000,16000)])
        cat.commit();cat.close()
        with p.closing(p.ro_sql(self.catalogue)) as c:
            q=p.state_db(self.work/'FILE_PACKS_V27.sqlite',p.WORK_FORMAT,p.QUEUE_SQL)
            try:
                r=p.synchronize(c,q,33)
                self.assertTrue(r['synchronized'])
                self.assertEqual(r['added_this_sync'],15003)
                self.assertEqual(q.execute('SELECT count(*) FROM queue').fetchone()[0],15003)
                self.assertEqual(p.synchronize(c,q,33)['added_this_sync'],0)
            finally:q.close()

    def test_no_placeholder_import(self):
        built=p.produce(self.args(max_packs=1))
        pack=Path(built['packs'][0]['path'])
        delta=self.make_delta(pack)
        obj=json.loads(delta.read_text())
        obj['claims'][0]['object']['value']='REMPLACER'
        delta.write_bytes(p.encoded(obj))
        class I: pass
        i=I();i.pack=pack;i.delta=delta;i.work=self.work
        with self.assertRaises(p.Refusal):p.import_delta(i)


if __name__=='__main__':unittest.main()
