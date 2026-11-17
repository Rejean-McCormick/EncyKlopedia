"""Read only: SQLite metadata, no COUNT scans, no dump decompression."""
import sqlite3
from ._encyk_common import data_root,add

def run(cfg,report):
    root=data_root(cfg)
    db=root/'30_working/wikidata/wikidata.compact.sqlite'
    dump_dir=root/'10_sources/wikidata/dumps/current'
    dumps=sorted(dump_dir.glob('*.json.bz2')) if dump_dir.is_dir() else []
    dump=dumps[0] if len(dumps)==1 else None
    manifests=root/'20_evidence/manifests/wikidata-dump-verified.json'
    if not db.is_file():
        add(report,'encyk.wikidata.index.present','BLOCKED','Compact SQLite not found.',{'path':str(db)});return
    add(report,'encyk.wikidata.index.present','PASS','Compact SQLite file is available.',{'bytes':db.stat().st_size})
    try:
        # mode=ro is SQLite-enforced; no PRAGMAs that write.
        uri=db.resolve().as_uri()+'?mode=ro'
        c=sqlite3.connect(uri,uri=True,timeout=2)
        c.row_factory=sqlite3.Row
        try:
            c.execute('PRAGMA query_only=ON')
            kv={r[0]:r[1] for r in c.execute('SELECT key,value FROM meta LIMIT 80')}
            tables={r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 128")}
            required={'entity','name','claim_presence','entity_edge','chronology'}
            missing=sorted(required-tables)
            add(report,'encyk.wikidata.index.complete','PASS' if kv.get('complete')=='1' and not missing else 'FAIL',
                'Index completion flag and required tables examined.',{'complete':kv.get('complete'),'processed_entities':kv.get('processed_entities'),'missing_tables':missing})
            add(report,'encyk.wikidata.index.strategy','PASS','Read-only index metadata available.',{'schema_version':kv.get('schema_version'),'index_strategy':kv.get('index_strategy')})
            # Single PK lookup. Never call entity count or global text search.
            qid=cfg.get('encyk',{}).get('required_qid','Q192154')
            if isinstance(qid,str) and qid.startswith('Q') and qid[1:].isdigit():
                # Schema varies; only use safe query if id is column.
                cols={r[1] for r in c.execute('PRAGMA table_info(entity)')}
                if 'qid' in cols:
                    found=c.execute('SELECT 1 FROM entity WHERE qid=? LIMIT 1',(qid,)).fetchone()
                    add(report,'encyk.wikidata.root_qid','PASS' if found else 'WARN','Configured QID lookup completed.',{'root_qid':qid,'found':bool(found)})
        finally:c.close()
    except (sqlite3.Error, OSError) as exc:
        add(report,'encyk.wikidata.sqlite.readonly','FAIL','Read-only SQLite metadata query failed.',{'error':type(exc).__name__+': '+str(exc)[:180]})
    add(report,'encyk.wikidata.dump.present','PASS' if dump and dump.is_file() else 'BLOCKED',
        'Existing compressed dump is present; it was not scanned.',{'exists':bool(dump and dump.is_file()),'candidate_count':len(dumps),'bytes':dump.stat().st_size if dump else None})
    add(report,'encyk.wikidata.manifest.present','PASS' if manifests.is_file() else 'WARN',
        'Existing source verification manifest is present.',{'exists':manifests.is_file()})
