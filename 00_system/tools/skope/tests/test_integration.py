import hashlib
import io
import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from skope import db
from skope.scope import explore
from skope.export import bundle,proposal
from skope.arketype import load_guidance

BASE=Path(__file__).resolve().parents[1]
FIX=BASE/'fixtures/demo.wikidata.jsonl'
REC=json.loads((BASE/'fixtures/demo.recipe.json').read_text())

def make_index(path,complete='1'):
    c=sqlite3.connect(path)
    c.executescript('''CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE entity(id INTEGER PRIMARY KEY,wid TEXT,kind TEXT,label_fr TEXT,label_en TEXT,label_mul TEXT,description_fr TEXT,description_en TEXT);
CREATE TABLE name(entity_id INTEGER,lang TEXT,name_kind INTEGER,value TEXT,norm TEXT);
CREATE INDEX idx_name_norm ON name(norm);
CREATE TABLE entity_edge(subject_id INTEGER,property_id INTEGER,target_id INTEGER,statement_count INTEGER,best_rank INTEGER);
CREATE INDEX edge_from ON entity_edge(subject_id);CREATE INDEX edge_to ON entity_edge(target_id);
''')
    c.executemany('INSERT INTO meta VALUES (?,?)', [('complete',complete),('lossless','0'),('dump_sha1','a'*40),('dump_file','synthetic.jsonl'),('processed_entities','16')])
    from collections import defaultdict
    ids={}
    items=[json.loads(line) for line in FIX.read_text().splitlines() if line.strip()]
    for e in items:
        q=e['id'];idx=db._eid(q);ids[q]=idx
        label=lambda key,lang:(e.get(key,{}).get(lang) or {}).get('value')
        c.execute('INSERT INTO entity VALUES (?,?,?,?,?,?,?,?)',(idx,q,e.get('type','item'),label('labels','fr'),label('labels','en'),None,label('descriptions','fr'),label('descriptions','en')))
        for lang,lab in (e.get('labels') or {}).items():
            v=lab.get('value','')
            if v:c.execute('INSERT INTO name VALUES (?,?,?,?,?)',(idx,lang,0,v,v.casefold()))
        for lang,aliases in (e.get('aliases') or {}).items():
            for alias in aliases:
                v=alias.get('value','') if isinstance(alias,dict) else ''
                if v:c.execute('INSERT INTO name VALUES (?,?,?,?,?)',(idx,lang,1,v,db._norm(v)))
    for e in items:
        for p,claims in (e.get('claims') or {}).items():
            counts=defaultdict(lambda:[0,1])
            for st in claims:
                value=((st.get('mainsnak') or {}).get('datavalue') or {}).get('value')
                target=value.get('id') if isinstance(value,dict) else None
                if target and target in ids:
                    counts[target][0]+=1
                    counts[target][1]=max(counts[target][1],{'deprecated':0,'normal':1,'preferred':2}.get(st.get('rank'),1))
            for target,(num,rank) in counts.items():
                c.execute('INSERT INTO entity_edge VALUES (?,?,?,?,?)',(ids[e['id']],int(p[1:]),ids[target],num,rank))
    c.commit();c.close()

class SkopeIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'encyk.sqlite';make_index(self.path)
    def test_readonly_encyk_index(self):
        with db.connect(self.path) as con:
            self.assertEqual(db.meta(con)['adapter'],'skope-encyk-readonly/1.0')
            self.assertEqual(db.node(con,REC['root'])['id'],REC['root'])
            self.assertEqual(len(db.find(con,'Q900000000')),1)
            self.assertTrue(db.neighbors(con,REC['root'],'out'))
            self.assertIsNone(db.neighbors(con,REC['root'],'out')[0]['statement_id'])
        with self.assertRaises(ValueError):db.connect(self.path,readonly=False)
    def test_encryption_scope_convergence_and_proposal(self):
        with db.connect(self.path) as con:
            preview=explore(con,REC)
            self.assertEqual(preview['source_snapshot_digest'],'sha1:'+'a'*40)
            self.assertEqual(preview['profile'],'skope.encyk-preview/1.0')
            self.assertIn('Q900000011',{c['id'] for c in preview['candidates']})
            report,regpath,registry,cfgpath,config,manifest=proposal(con,REC,'scope-test')
            self.assertEqual(len(registry['records']),len(report['nodes']))
            self.assertEqual(config['schema_version'],'encyklopedia-scope/v3')
            self.assertEqual(config['discovery']['reverse_root_relations'],{})
            self.assertFalse(config['discovery']['include_all_entity_relations_from_roots'])
            self.assertFalse(manifest['raw_source_json_included'])
            data=bundle(con,REC,'scope-test')
            self.assertEqual(data,bundle(con,REC,'scope-test'))
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertIn('staged/'+regpath,z.namelist())
            self.assertIn('staged/'+cfgpath,z.namelist())
            self.assertNotIn('30_working/wikidata-entities.jsonl',z.namelist())
            self.assertTrue(json.loads(z.read('manifest.json'))['status'].startswith('working'))
    def test_truncated_rejected(self):
        with db.connect(self.path) as con:
            rec=dict(REC,max_entities=1)
            self.assertTrue(explore(con,rec)['truncated'])
            with self.assertRaises(ValueError):bundle(con,rec)
    def test_incomplete_index_rejected(self):
        bad=Path(self.tmp.name)/'bad.sqlite';make_index(bad,'0')
        with self.assertRaises(ValueError):db.connect(bad)
    def test_arketype_no_authority(self):
        x={'format':'arketype.scope-guidance/1.0','status':'draft_requires_review',
           'profile_slug':'demo','structure':{},'dimensions':{},'inclusions':[],
           'exclusions':[],'coverage_questions':[],'limitations':[],
           'publication_authorized':False,'activation_authorized':False}
        p=Path(self.tmp.name)/'arketype.json';p.write_text(json.dumps(x))
        self.assertEqual(load_guidance(p),x)
        x['activation_authorized']=True;p.write_text(json.dumps(x))
        with self.assertRaises(ValueError):load_guidance(p)

if __name__=='__main__': unittest.main()
