from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from contextlib import closing
from zipfile import ZipFile
import csv
import io
import json
import os
import sqlite3
import sys
import unittest
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from encyk_v32.sql import open_work
from encyk_v32.sources import import_unesco,discover,discover_fallback
from encyk_v32.pipeline import make_wave,import_for_job,jobs_overview
from encyk_v32.federation import scan_islands,describe_island,admit_proposals
from encyk_v32.config import Settings


class UnifiedTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        d=Path(self.temp.name)
        unesco=d/'UNESCO_Kristals'
        for mid,concept,qid in [('mt1.05','concept2','Q11'),('mt1.10','concept3','Q12')]:
            slug='unesco-'+mid.replace('.','-')
            root=unesco/'branches'/slug
            p=root/'canon/domain';p.mkdir(parents=True,exist_ok=True)
            doc={'unesco_microthesaurus':mid,'source_scheme_modified':'2026-08-31',
                 'concepts':[{'unesco_id':concept,'preferred_labels':{'en':['Education'], 'fr':['Éducation']},
                              'scope_notes':{'en':['Educational topic']},'broader':[],'related':[],
                              'source_uri':'http://vocabularies.unesco.org/thesaurus/'+concept}]}
            (p/'unesco-source.json').write_text(json.dumps(doc))
            (root/'canon'/'state.index.json').write_text(json.dumps({'format':'kristal.authoring-state-index/2.0.0',
                    'canonical_artifacts':[{'artifact_id':'urn:kristal:'+slug+':unesco-source',
                                           'path':'canon/domain/unesco-source.json'}]}))
            m=root/'derived';m.mkdir(parents=True,exist_ok=True)
            (m/'wikidata-p3916-candidates.json').write_text(json.dumps({'mappings':[{'unesco_id':concept,
                   'qid_candidate':qid,'status':'SINGLE_P3916_CANDIDATE'}]}))
        self.xml=d/'wiki.xml';self.direct=d/'direct.sqlite';self.wiki=d/'wiki.sqlite';self.graph=d/'wd.sqlite'
        self.pages={1:('Article Q11','Founded in 1961. The school established a library.','11','Q11'),
                    2:('Article Q12','Education expanded in 2001. The teachers studied history.','12','Q12'),
                    3:('Other college','The university opened a new campus in 2003.','13','Q13')}
        a=sqlite3.connect(self.wiki)
        a.executescript('CREATE TABLE wiki_pages(page_id INTEGER PRIMARY KEY,ns INTEGER,title TEXT,redirect INTEGER,latest_revision INTEGER,content_bytes INTEGER);'
                        'CREATE TABLE wiki_qid(page_id INTEGER PRIMARY KEY,qid TEXT); CREATE INDEX idx_wiki_qid_qid ON wiki_qid(qid);')
        b=sqlite3.connect(self.direct)
        b.executescript('CREATE TABLE pages(page_id INTEGER PRIMARY KEY,byte_offset INTEGER,byte_length INTEGER,namespace INTEGER,title TEXT,revision_id TEXT,is_redirect INTEGER);')
        with self.xml.open('wb') as f:
            for pid,(title,text,rev,qid) in self.pages.items():
                root=ET.Element('page')
                ET.SubElement(root,'title').text=title;ET.SubElement(root,'ns').text='0';ET.SubElement(root,'id').text=str(pid)
                rr=ET.SubElement(root,'revision');ET.SubElement(rr,'id').text=rev;ET.SubElement(rr,'text').text=text
                raw=ET.tostring(root,encoding='utf-8')
                raw=raw.replace(b'<page>',b'<page>').replace(b'</page>',b'</page>')
                offset=f.tell();f.write(raw)
                b.execute('INSERT INTO pages VALUES (?,?,?,?,?,?,?)',(pid,offset,len(raw),0,title,rev,0))
                a.execute('INSERT INTO wiki_pages VALUES (?,?,?,?,?,?)',(pid,0,title.replace(' ','_'),0,int(rev),len(text)))
                a.execute('INSERT INTO wiki_qid VALUES(?,?)',(pid,qid))
        a.commit();a.close();b.commit();b.close()
        g=sqlite3.connect(self.graph)
        g.executescript('CREATE TABLE entity(id INTEGER);CREATE TABLE name(id INTEGER);CREATE TABLE meta(key TEXT,value TEXT);'
                        'CREATE TABLE entity_edge(subject_id INTEGER,property_id INTEGER,target_id INTEGER,best_rank INTEGER,statement_count INTEGER);'
                        'CREATE INDEX ixwdout ON entity_edge(subject_id,property_id,target_id);'
                        'CREATE INDEX ixwdin ON entity_edge(target_id,property_id,subject_id);'
                        "INSERT INTO meta VALUES ('complete','1');")
        g.execute('INSERT INTO entity_edge VALUES (?,?,?,?,?)',(13,1_000_000_031,11,1,1));g.commit();g.close()
        self.settings=Settings(unesco_root=str(unesco),wikipedia_sql=str(self.wiki),
             wikidata_sql=str(self.graph),wikipedia_xml=str(self.xml),wikipedia_direct_index=str(self.direct),
             work_root=str(d/'work'),kristal_roots=[str(unesco)],select_pack_size=3,enrich_pack_articles=3)
        self.db=open_work(self.settings.db_path);self.addCleanup(self.db.close)

    def test_two_passes_and_graph(self):
        self.assertEqual(import_unesco(self.db,self.settings.unesco_root)['branches'],2)
        rep=discover(self.db,self.settings,graph_enabled=True,max_pairs=100)
        self.assertEqual(rep['total_candidates'],3)
        # Idempotence: direct route and completed graph not replayed as work.
        again=discover(self.db,self.settings,graph_enabled=True,max_pairs=100)
        self.assertEqual(again['total_candidates'],3)
        jobs=make_wave(self.db,self.settings,kind='select')
        self.assertEqual(len(jobs),1)
        jid=jobs[0]['job_id']
        with ZipFile(jobs[0]['path']) as z:
            a=[json.loads(line) for line in z.read('candidates.jsonl').splitlines()]
            self.assertTrue(all(x['source_context'] is not None for x in a))
            self.assertEqual(len(a),3)
        ret=Path(self.temp.name)/'selection.zip'
        buf=io.StringIO();writer=csv.writer(buf);writer.writerow(['candidate_id','decision','justification'])
        for row in a:writer.writerow([row['candidate_id'],'SELECT','Pertinence documentaire clairement identifiable'])
        with ZipFile(ret,'w') as z:z.writestr('selection_decisions.csv',buf.getvalue())
        imported=import_for_job(self.db,ret,jid)
        self.assertEqual(imported['decided'],3)
        self.assertEqual(import_for_job(self.db,ret,jid)['status'],'ALREADY_IMPORTED')
        selected=self.db.execute("SELECT COUNT(*) FROM candidates WHERE state='SELECTED'").fetchone()[0]
        self.assertEqual(selected,3)
        enrichment=make_wave(self.db,self.settings,kind='enrich')
        self.assertEqual(len(enrichment),1)
        self.assertEqual(enrichment[0]['count'],3)
        ejid=enrichment[0]['job_id']
        with ZipFile(enrichment[0]['path']) as z:
            articles=[json.loads(line) for line in z.read('articles.jsonl').splitlines()]
            self.assertEqual(len(articles),3)
        coverage=[{'page_id':x['page_id'],'note':'Article examiné dans son ensemble'} for x in articles]
        facts=[]
        for x in articles:
            pid=x['page_id'];text=self.pages[pid][1]
            facts.append({'page_id':pid,'revision_id':x['revision_id'],'subject_key':x['subjects'][0],
                          'predicate':'describes','object':{'type':'text','value':text},
                          'statement':'The article documents an institutional or educational event: '+text,
                          'source_quote':text,'source_locator':'Introduction','concept_ids':x['concept_ids']})
        result={'format':'encyk.enrichment-delta.v32/1','job_id':ejid,'facts':facts,
                'source_coverage':coverage,'canonical_admissions':0,'publication_authorized':False}
        eret=Path(self.temp.name)/'enrichment.zip'
        with ZipFile(eret,'w') as z:z.writestr('kristal_delta.json',json.dumps(result))
        imported=import_for_job(self.db,eret,ejid)
        self.assertEqual(imported['new_proposals'],3)
        self.assertEqual(self.db.execute('SELECT count(*) FROM proposals').fetchone()[0],3)
        self.assertEqual(import_for_job(self.db,eret,ejid)['status'],'ALREADY_IMPORTED')
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM candidates WHERE state='ENRICHED'").fetchone()[0],3)
        self.assertEqual(self.db.execute('SELECT count(*) FROM lanes WHERE job_id IS NOT NULL').fetchone()[0],0)

    def test_partial_return_and_no_default_vote(self):
        import_unesco(self.db,self.settings.unesco_root)
        discover(self.db,self.settings,graph_enabled=False)
        job=make_wave(self.db,self.settings,kind='select')[0]
        with ZipFile(job['path']) as z:items=[json.loads(x) for x in z.read('candidates.jsonl').splitlines()]
        buf='candidate_id,decision,justification\n'+items[0]['candidate_id']+',HOLD,Texte disponible insuffisant\n'
        ret=Path(self.temp.name)/'partial.zip'
        with ZipFile(ret,'w') as z:z.writestr('selection_decisions.csv',buf)
        r=import_for_job(self.db,ret,job['job_id'])
        self.assertEqual(r['status'],'PARTIAL')
        self.assertEqual(r['unanswered_requeued'],1)
        self.assertEqual(self.db.execute("SELECT count(*) FROM candidates WHERE state='PENDING'").fetchone()[0],1)
        self.assertEqual(self.db.execute("SELECT count(*) FROM candidates WHERE state='HOLD'").fetchone()[0],1)

    def test_refuse_forged_quote_and_atomicity(self):
        import_unesco(self.db,self.settings.unesco_root)
        discover(self.db,self.settings,graph_enabled=False)
        job=make_wave(self.db,self.settings,kind='select')[0]
        with ZipFile(job['path']) as z:items=[json.loads(x) for x in z.read('candidates.jsonl').splitlines()]
        buf='candidate_id,decision,justification\n'+''.join(x['candidate_id']+',SELECT,Correspondance substantielle étayée\n' for x in items)
        ret=Path(self.temp.name)/'sel.zip'
        with ZipFile(ret,'w') as z:z.writestr('selection_decisions.csv',buf)
        import_for_job(self.db,ret,job['job_id'])
        job=make_wave(self.db,self.settings,kind='enrich')[0]
        with ZipFile(job['path']) as z:article=json.loads(z.read('articles.jsonl').splitlines()[0])
        delta={'format':'encyk.enrichment-delta.v32/1','job_id':job['job_id'],
            'source_coverage':[{'page_id':k,'note':'Lu'} for k in (1,2)],
            'facts':[{'page_id':article['page_id'],'revision_id':article['revision_id'],
                      'subject_key':article['subjects'][0], 'predicate':'states',
                      'object':{'type':'text','value':'X'},'statement':'Statement based on a fabricated quote',
                      'source_quote':'Citation fabriquée dans une révision',
                      'source_locator':'History','concept_ids':article['concept_ids']}],
            'canonical_admissions':0,'publication_authorized':False}
        ret=Path(self.temp.name)/'bad.zip'
        with ZipFile(ret,'w') as z:z.writestr('kristal_delta.json',json.dumps(delta))
        with self.assertRaises(ValueError):import_for_job(self.db,ret,job['job_id'])
        self.assertEqual(self.db.execute('SELECT count(*) FROM proposals').fetchone()[0],0)

    def test_fallback_for_unmapped_concept_and_resume(self):
        root=Path(self.settings.unesco_root)/'branches'/'unesco-mt2-01'
        (root/'canon/domain').mkdir(parents=True,exist_ok=True)
        (root/'derived').mkdir(parents=True,exist_ok=True)
        source={'unesco_microthesaurus':'mt2.01','concepts':[{'unesco_id':'concept99',
                  'preferred_labels':{'en':['Other college'],'fr':['Autre collège']},
                  'alternate_labels':{},'broader':[],'related':[]}]}
        (root/'canon/domain/unesco-source.json').write_text(json.dumps(source))
        (root/'derived/wikidata-p3916-candidates.json').write_text(json.dumps({'mappings':[
                    {'unesco_id':'concept99','qid_candidate':'','status':'NO_P3916_MAPPING'}]}))
        import_unesco(self.db,self.settings.unesco_root)
        first=discover_fallback(self.db,self.settings,branch='unesco.mt2.01',max_pages=1)
        self.assertEqual(first['pages_examined'],1)
        second=discover_fallback(self.db,self.settings,branch='unesco.mt2.01',max_pages=2)
        self.assertEqual(second['pages_examined'] if 'pages_examined' in second else 0,0)
        found=self.db.execute("SELECT * FROM candidates WHERE branch_id='unesco.mt2.01'").fetchall()
        self.assertEqual(len(found),1)
        self.assertEqual(found[0]['title'],'Other college')

    def test_refuse_unrelated_existing_sqlite(self):
        other=Path(self.temp.name)/'other.sqlite'
        with sqlite3.connect(other) as db:db.execute('CREATE TABLE foreign_data(k TEXT)')
        original=other.read_bytes()
        with self.assertRaises(ValueError):open_work(other)
        self.assertEqual(other.read_bytes(),original)

    def test_federation_is_readonly_and_admission_closed(self):
        before={p:p.read_bytes() for p in Path(self.settings.unesco_root).rglob('canon/state.index.json')}
        data=scan_islands(self.db,self.settings.kristal_roots)
        self.assertEqual(data['readable'],2)
        k=self.db.execute('SELECT island_key FROM kristal_islands LIMIT 1').fetchone()[0]
        detail=describe_island(self.db,k)
        self.assertTrue(detail['read_only'])
        self.assertTrue(detail['canonical_artifacts'][0]['available'])
        with self.assertRaises(RuntimeError):admit_proposals()
        self.assertEqual(before,{p:p.read_bytes() for p in before})

if __name__=='__main__':unittest.main()
