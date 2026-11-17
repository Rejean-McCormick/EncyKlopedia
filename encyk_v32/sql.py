"""Transactions, schéma local de travail et connexions source strictement RO."""
from __future__ import annotations
from contextlib import contextmanager, closing
from pathlib import Path
import sqlite3

DDL='''
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS branches(branch_id TEXT PRIMARY KEY, title TEXT NOT NULL,
 source_path TEXT NOT NULL, source_version TEXT, status TEXT NOT NULL DEFAULT 'AVAILABLE');
CREATE TABLE IF NOT EXISTS concepts(concept_id TEXT PRIMARY KEY,label_fr TEXT,label_en TEXT,
  description TEXT,broader_json TEXT,related_json TEXT,source_uri TEXT);
CREATE TABLE IF NOT EXISTS branch_concepts(branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,
 PRIMARY KEY(branch_id,concept_id));
CREATE INDEX IF NOT EXISTS idx_branch_concept ON branch_concepts(concept_id,branch_id);
CREATE TABLE IF NOT EXISTS concept_aliases(concept_id TEXT NOT NULL,alias TEXT NOT NULL,lang TEXT NOT NULL,
 PRIMARY KEY(concept_id,alias,lang));
CREATE TABLE IF NOT EXISTS fallback_cursors(branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,
 alias TEXT NOT NULL,last_title TEXT NOT NULL DEFAULT '',completed INTEGER NOT NULL DEFAULT 0,
 updated_utc TEXT NOT NULL,PRIMARY KEY(branch_id,concept_id,alias));
CREATE TABLE IF NOT EXISTS mappings(concept_id TEXT NOT NULL,qid TEXT NOT NULL,
  status TEXT NOT NULL, source TEXT NOT NULL,branch_id TEXT NOT NULL,
  PRIMARY KEY(concept_id,qid,source,branch_id));
CREATE INDEX IF NOT EXISTS idx_mapping_branch ON mappings(branch_id,status);
CREATE TABLE IF NOT EXISTS subjects(subject_key TEXT PRIMARY KEY,qid TEXT,
  preferred_label TEXT NOT NULL DEFAULT '',kind TEXT NOT NULL DEFAULT 'WIKIDATA_SUBJECT');
CREATE TABLE IF NOT EXISTS candidates(candidate_id TEXT PRIMARY KEY,branch_id TEXT NOT NULL,
 concept_id TEXT NOT NULL,subject_key TEXT NOT NULL,page_id INTEGER NOT NULL,
 title TEXT NOT NULL,revision_id TEXT NOT NULL DEFAULT '',priority INTEGER NOT NULL DEFAULT 0,
 state TEXT NOT NULL DEFAULT 'PENDING',decision_reason TEXT NOT NULL DEFAULT '',created_utc TEXT NOT NULL,
  UNIQUE(branch_id,concept_id,page_id));
CREATE INDEX IF NOT EXISTS idx_candidates_queue ON candidates(state,priority DESC,candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidates_branch ON candidates(branch_id,state,priority DESC);
CREATE TABLE IF NOT EXISTS candidate_routes(route_id TEXT PRIMARY KEY,candidate_id TEXT NOT NULL,
 origin TEXT NOT NULL,anchor_qid TEXT,subject_qid TEXT,property_path TEXT NOT NULL,
 evidence_note TEXT NOT NULL DEFAULT '');
CREATE INDEX IF NOT EXISTS idx_routes_candidate ON candidate_routes(candidate_id);
CREATE TABLE IF NOT EXISTS graph_cursors(branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,anchor_qid TEXT NOT NULL,
 property_id TEXT NOT NULL,direction TEXT NOT NULL,last_id INTEGER NOT NULL DEFAULT 0,
 completed INTEGER NOT NULL DEFAULT 0,updated_utc TEXT NOT NULL,
 PRIMARY KEY(branch_id,concept_id,anchor_qid,property_id,direction));
CREATE TABLE IF NOT EXISTS jobs(job_id TEXT PRIMARY KEY,kind TEXT NOT NULL,
 status TEXT NOT NULL,pack_path TEXT NOT NULL,pack_sha256 TEXT NOT NULL,
 count INTEGER NOT NULL,created_utc TEXT NOT NULL,completed_utc TEXT, return_sha256 TEXT);
CREATE INDEX IF NOT EXISTS idx_jobs_open ON jobs(status,created_utc);
CREATE TABLE IF NOT EXISTS job_items(job_id TEXT NOT NULL,candidate_id TEXT NOT NULL,
 PRIMARY KEY(job_id,candidate_id));
CREATE INDEX IF NOT EXISTS idx_job_items_candidate ON job_items(candidate_id);
CREATE TABLE IF NOT EXISTS lanes(lane INTEGER PRIMARY KEY,job_id TEXT UNIQUE,
 FOREIGN KEY(job_id) REFERENCES jobs(job_id));
CREATE TABLE IF NOT EXISTS decisions(candidate_id TEXT PRIMARY KEY,job_id TEXT NOT NULL,
 decision TEXT NOT NULL,justification TEXT NOT NULL,created_utc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS article_sources(page_id INTEGER NOT NULL,revision_id TEXT NOT NULL,
 title TEXT NOT NULL,sha256 TEXT NOT NULL,source_path TEXT NOT NULL,
 PRIMARY KEY(page_id,revision_id));
CREATE TABLE IF NOT EXISTS proposals(proposal_id TEXT PRIMARY KEY, subject_key TEXT NOT NULL,
 page_id INTEGER NOT NULL,revision_id TEXT NOT NULL,statement TEXT NOT NULL,predicate TEXT NOT NULL,
 object_json TEXT NOT NULL,source_quote TEXT NOT NULL,source_locator TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'DRAFT',source_job TEXT NOT NULL,created_utc TEXT NOT NULL,
  UNIQUE(subject_key, page_id, revision_id, predicate, object_json));
CREATE INDEX IF NOT EXISTS idx_proposals_subject ON proposals(subject_key,status);
CREATE TABLE IF NOT EXISTS proposal_concepts(proposal_id TEXT NOT NULL,concept_id TEXT NOT NULL,
 PRIMARY KEY(proposal_id,concept_id));
CREATE TABLE IF NOT EXISTS proposal_citations(proposal_id TEXT NOT NULL,page_id INTEGER NOT NULL,
 revision_id TEXT NOT NULL,quote TEXT NOT NULL,locator TEXT NOT NULL,
 PRIMARY KEY(proposal_id,page_id,revision_id,quote));
CREATE TABLE IF NOT EXISTS receipts(receipt_id INTEGER PRIMARY KEY AUTOINCREMENT,
 created_utc TEXT NOT NULL,filename TEXT NOT NULL,file_sha256 TEXT NOT NULL,
 job_id TEXT,status TEXT NOT NULL,detail TEXT NOT NULL,
 UNIQUE(file_sha256,job_id));
CREATE TABLE IF NOT EXISTS kristal_islands(island_key TEXT PRIMARY KEY, root TEXT NOT NULL,
 state_index TEXT NOT NULL,model TEXT NOT NULL,source TEXT NOT NULL,scan_utc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS island_branch_links(island_key TEXT NOT NULL,branch_id TEXT NOT NULL,
 kind TEXT NOT NULL,PRIMARY KEY(island_key,branch_id,kind));
CREATE TABLE IF NOT EXISTS events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,
 created_utc TEXT NOT NULL,kind TEXT NOT NULL,details TEXT NOT NULL);
'''

SCHEMA = 'encyk.local-manager.v32/2'
OLD_SCHEMA = 'encyk.local-manager.v32/1'

EXTRA_DDL = """
CREATE TABLE IF NOT EXISTS active_items(candidate_id TEXT PRIMARY KEY, job_id TEXT NOT NULL,
 FOREIGN KEY(candidate_id) REFERENCES candidates(candidate_id), FOREIGN KEY(job_id) REFERENCES jobs(job_id));
CREATE TABLE IF NOT EXISTS return_archives(file_sha256 TEXT PRIMARY KEY, path TEXT NOT NULL, created_utc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS proposal_occurrences(proposal_id TEXT NOT NULL, job_id TEXT NOT NULL,
 return_sha256 TEXT NOT NULL, ordinal INTEGER NOT NULL, payload_json TEXT NOT NULL,
 PRIMARY KEY(job_id,return_sha256,ordinal));
CREATE TABLE IF NOT EXISTS import_errors(job_id TEXT NOT NULL,return_sha256 TEXT NOT NULL,
 ordinal INTEGER NOT NULL,error TEXT NOT NULL,payload_json TEXT NOT NULL,
 PRIMARY KEY(job_id,return_sha256,ordinal));
CREATE TABLE IF NOT EXISTS proposal_replacements(old_id TEXT PRIMARY KEY,new_id TEXT NOT NULL,
 job_id TEXT NOT NULL,return_sha256 TEXT NOT NULL,created_utc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS decision_history(candidate_id TEXT NOT NULL,job_id TEXT NOT NULL,
 decision TEXT NOT NULL,justification TEXT NOT NULL,created_utc TEXT NOT NULL,
 PRIMARY KEY(candidate_id,job_id));
CREATE TABLE IF NOT EXISTS source_results(job_id TEXT NOT NULL,page_id INTEGER NOT NULL,
 revision_id TEXT NOT NULL,profile TEXT NOT NULL,text_sha256 TEXT NOT NULL,
 status TEXT NOT NULL,coverage_json TEXT NOT NULL,concepts_json TEXT NOT NULL,subjects_json TEXT NOT NULL,
 PRIMARY KEY(job_id,page_id));
CREATE INDEX IF NOT EXISTS idx_source_reuse ON source_results(page_id,revision_id,profile,text_sha256,status);
CREATE TABLE IF NOT EXISTS candidate_extractions(candidate_id TEXT NOT NULL,job_id TEXT NOT NULL,page_id INTEGER NOT NULL,
 relation TEXT NOT NULL,PRIMARY KEY(candidate_id,job_id,page_id));
CREATE TABLE IF NOT EXISTS candidate_failures(candidate_id TEXT PRIMARY KEY,attempts INTEGER NOT NULL,
 reason TEXT NOT NULL,next_retry_utc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS island_locations(island_key TEXT NOT NULL,root TEXT NOT NULL,state_index TEXT NOT NULL,
 source TEXT NOT NULL,scan_utc TEXT NOT NULL,PRIMARY KEY(island_key,root));
"""


def _statements(db, script):
    # These schemas contain no triggers or semicolons inside literals.
    for statement in script.split(';'):
        if statement.strip(): db.execute(statement)


def open_work(path):
    from .locking import writer_lock
    path = Path(path)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError('Chemin de base de travail invalide')
    path.parent.mkdir(parents=True,exist_ok=True)
    # Fast read path: opening a qualified database does not require a writer lock.
    old = None
    if path.exists():
        with read_source(path) as check:
            if not has_table(check,'meta'):
                raise ValueError('Base SQLite préexistante étrangère au gestionnaire EncyK V32')
            row=check.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
            old = row[0] if row else None
            if old not in (OLD_SCHEMA, SCHEMA):
                raise ValueError('Schéma SQLite local incompatible : aucun changement appliqué')
    c=sqlite3.connect(str(path),timeout=60)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA busy_timeout=60000')
    c.execute('PRAGMA foreign_keys=ON')
    c.execute('PRAGMA synchronous=FULL')
    try:
        if old != SCHEMA:
            with writer_lock(path,id(c)):
                c.execute('PRAGMA journal_mode=WAL')
                # Recheck after acquiring the lock, in case another opener initialized it.
                current=c.execute("SELECT value FROM meta WHERE key='schema'").fetchone() if has_table(c,'meta') else None
                if current and current[0] == SCHEMA: return c
                if current:
                    import os
                    backup=Path(str(path)+'.before-v32-2.sqlite')
                    if not backup.exists():
                        temp=Path(str(backup)+'.tmp')
                        with closing(sqlite3.connect(str(temp))) as target: c.backup(target)
                        os.replace(temp,backup)
                with c:
                    c.execute('BEGIN IMMEDIATE')
                    _statements(c,DDL)
                    c.execute('ALTER TABLE proposals RENAME TO proposals_v1')
                    c.execute("""CREATE TABLE proposals(proposal_id TEXT PRIMARY KEY,subject_key TEXT NOT NULL,
                      page_id INTEGER NOT NULL,revision_id TEXT NOT NULL,statement TEXT NOT NULL,predicate TEXT NOT NULL,
                      object_json TEXT NOT NULL,source_quote TEXT NOT NULL,source_locator TEXT NOT NULL,
                      status TEXT NOT NULL DEFAULT 'DRAFT',source_job TEXT NOT NULL,created_utc TEXT NOT NULL,
                      context_json TEXT NOT NULL DEFAULT '{}',payload_json TEXT NOT NULL DEFAULT '{}',
                      supersedes TEXT REFERENCES proposals(proposal_id))""")
                    c.execute("""INSERT INTO proposals(proposal_id,subject_key,page_id,revision_id,statement,predicate,
                      object_json,source_quote,source_locator,status,source_job,created_utc)
                      SELECT proposal_id,subject_key,page_id,revision_id,statement,predicate,object_json,
                      source_quote,source_locator,status,source_job,created_utc FROM proposals_v1""")
                    c.execute('DROP TABLE proposals_v1')
                    c.execute('CREATE INDEX idx_proposals_subject ON proposals(subject_key,status)')
                    _statements(c,EXTRA_DDL)
                    c.execute('INSERT OR IGNORE INTO decision_history SELECT * FROM decisions')
                    # A v1 database already containing duplicate active jobs needs explicit repair.
                    c.execute("""INSERT INTO active_items SELECT ji.candidate_id,ji.job_id FROM job_items ji
                      JOIN jobs j ON j.job_id=ji.job_id WHERE j.status IN ('READY','SENT')""")
                    c.execute("INSERT OR REPLACE INTO meta VALUES('schema',?)",(SCHEMA,))
                    for lane in range(1,11):
                        c.execute('INSERT OR IGNORE INTO lanes(lane,job_id) VALUES (?,NULL)',(lane,))
        return c
    except Exception:
        c.close()
        raise

@contextmanager
def read_source(path):
    p=Path(path)
    if not p.is_file(): raise FileNotFoundError('Index source absent : '+str(p))
    c=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True,timeout=30)
    c.row_factory=sqlite3.Row
    try:
        c.execute('PRAGMA query_only=ON')
        yield c
    finally:c.close()

def has_table(c,name):
    return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None
