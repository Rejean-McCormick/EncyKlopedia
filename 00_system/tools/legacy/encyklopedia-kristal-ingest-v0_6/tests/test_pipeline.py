from __future__ import annotations
import json, sqlite3, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
TOOL=HERE.parent
SCRIPTS=TOOL/'scripts'
CFG=TOOL/'config/harvest.default.json'

SCHEMA='''
CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE entity(id INTEGER PRIMARY KEY,wid TEXT UNIQUE,kind TEXT,label_fr TEXT,label_en TEXT,label_mul TEXT,description_fr TEXT,description_en TEXT);
CREATE TABLE name(entity_id INTEGER,lang TEXT,name_kind INTEGER,value TEXT,norm TEXT,PRIMARY KEY(entity_id,lang,name_kind,value));
CREATE TABLE claim_presence(subject_id INTEGER,property_id INTEGER,datatype TEXT,statement_count INTEGER,preferred_count INTEGER,normal_count INTEGER,deprecated_count INTEGER,PRIMARY KEY(subject_id,property_id));
CREATE TABLE entity_edge(subject_id INTEGER,property_id INTEGER,target_id INTEGER,statement_count INTEGER,best_rank INTEGER,PRIMARY KEY(subject_id,property_id,target_id));
CREATE TABLE chronology(subject_id INTEGER,property_id INTEGER,year INTEGER,precision INTEGER,PRIMARY KEY(subject_id,property_id,year,precision));
'''

def q(n): return n

def build_root(base:Path):
    (base/'10_sources/seeds/active/intellectual-registry').mkdir(parents=True)
    (base/'30_working/wikidata').mkdir(parents=True)
    (base/'30_working/registry').mkdir(parents=True)
    (base/'00_system/tools/encyklopedia-kristal-ingest/config').mkdir(parents=True)
    (base/'20_ingest/snapshots/encyklopedia').mkdir(parents=True)
    (base/'20_ingest/handoffs/kristal').mkdir(parents=True)
    (base/'50_mediatheque/catalog/candidates/wikidata').mkdir(parents=True)
    (base/'MANIFEST.json').write_text('{}')
    (base/'00_system/tools/encyklopedia-kristal-ingest/config/harvest.default.json').write_bytes(CFG.read_bytes())
    reg={'schema_version':'test/v1','records':[{'key':'alice','display_name':'Alice','representation_kind':'historical_person','chronology':{'birth_year':1900},'isced_f_domains':['0223'],'tags':['philosophy']},{'key':'bob','display_name':'Bob','representation_kind':'historical_person','chronology':{'birth_year':1890},'isced_f_domains':['0232'],'tags':[]}]}
    (base/'10_sources/seeds/active/intellectual-registry/intellectuals.seed.json').write_text(json.dumps(reg),encoding='utf-8')
    qmap={'alice':{'qid':'Q1','confidence':'high'},'bob':{'qid':'Q2','confidence':'high'}}
    (base/'30_working/registry/qid-map.local.json').write_text(json.dumps(qmap),encoding='utf-8')
    db=base/'30_working/wikidata/wikidata.compact.sqlite'; c=sqlite3.connect(db); c.executescript(SCHEMA)
    c.executemany('INSERT INTO meta VALUES(?,?)',[('complete','1'),('schema_version','test-index/v1'),('dump_file','test.json.bz2'),('dump_sha1','abc'),('processed_entities','99')])
    ents=[
      (1,'Q1','item','Alice','Alice',None,'philosophe','philosopher'),(2,'Q2','item','Bob','Bob',None,'auteur','author'),
      (10,'Q10','item','Livre A','Book A',None,'livre','book'),(20,'Q20','item','Stoïcisme','Stoicism',None,'courant','movement'),
      (30,'Q30','item','Philosophie','Philosophy',None,'domaine','field'),(40,'Q40','item','Livre B','Book B',None,'traité','treatise'),
      (1000000050,'P50','property','auteur','author',None,None,None),(1000000800,'P800','property','œuvre notable','notable work',None,None,None)
    ]
    c.executemany('INSERT INTO entity VALUES(?,?,?,?,?,?,?,?)',ents)
    names=[(1,'fr',0,'Alice','alice'),(2,'fr',0,'Bob','bob'),(10,'fr',0,'Livre A','livre a'),(20,'fr',0,'Stoïcisme','stoicisme'),(30,'fr',0,'Philosophie','philosophie'),(40,'fr',0,'Livre B','livre b')]
    c.executemany('INSERT INTO name VALUES(?,?,?,?,?)',names)
    # Alice: P800 work, P135 movement, P101 field, P737 influenced by Bob
    edges=[(1,800,10,1,1),(1,135,20,1,1),(1,101,30,1,1),(1,737,2,1,1),(10,50,1,1,1),(40,50,2,1,1)]
    c.executemany('INSERT INTO entity_edge VALUES(?,?,?,?,?)',edges)
    pres=[(1,800,'wikibase-item',1,0,1,0),(1,135,'wikibase-item',1,0,1,0),(1,101,'wikibase-item',1,0,1,0),(1,737,'wikibase-item',1,0,1,0),(2,569,'time',1,0,1,0),(10,50,'wikibase-item',1,0,1,0),(10,577,'time',1,0,1,0),(40,50,'wikibase-item',1,0,1,0)]
    c.executemany('INSERT INTO claim_presence VALUES(?,?,?,?,?,?,?)',pres); c.execute('INSERT INTO chronology VALUES(?,?,?,?)',(2,569,1890,9)); c.commit(); c.close(); return db

def run(script,*args):
    cp=subprocess.run([sys.executable,str(SCRIPTS/script),*map(str,args)],capture_output=True,text=True)
    assert cp.returncode==0, cp.stdout+'\n'+cp.stderr
    return cp

def test_extract_and_handoff():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); build_root(root); run_dir=root/'30_working/encyklopedia-harvest/runs/test'; run_dir.mkdir(parents=True)
        run('02_extract_people.py','--root',root,'--run-dir',run_dir)
        run('03_extract_works.py','--root',root,'--run-dir',run_dir)
        run('04_extract_intellectual_context.py','--root',root,'--run-dir',run_dir)
        run('05_publish_mediatheque_candidates.py','--root',root,'--run-dir',run_dir,'--snapshot-name','test')
        (run_dir/'run-manifest.json').write_text('{}')
        run('06_build_source_snapshot.py','--root',root,'--run-dir',run_dir)
        run('07_prepare_daat_handoff.py','--root',root)
        people=[json.loads(x) for x in (run_dir/'people.jsonl').read_text().splitlines()]
        works=[json.loads(x) for x in (run_dir/'works.jsonl').read_text().splitlines()]
        currents=[json.loads(x) for x in (run_dir/'currents.jsonl').read_text().splitlines()]
        assert len(people)==2
        assert {x['wid'] for x in works}=={'Q10','Q40'}
        assert currents[0]['wid']=='Q20'
        latest=json.loads((root/'20_ingest/handoffs/kristal/latest.json').read_text())
        handoff=root/latest['path']/'daat-handoff.json'
        assert handoff.exists()
        h=json.loads(handoff.read_text())
        assert h['status']=='ready_for_daat_mapping'
        assert not (root/'40_kristal').exists()
