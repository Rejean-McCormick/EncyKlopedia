#!/usr/bin/env python3
"""EncyKlopedia v25: catalogue global, multibranches, indexe et reprenable.

Catalogue prive de candidats Wikipedia EN classes par concepts UNESCO.
N'ecrit JAMAIS dans la base Wikipedia source ni dans le Kristal canonique.
SQLite stdlib uniquement. Pas de parcours du dump XML ni scan de toutes les pages.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import csv
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import urllib.parse
import zipfile

VERSION = '25.0'
HERE = Path(__file__).resolve().parent
DEFAULT_BRANCH = HERE / 'v25_data' / 'branche_mt110.json'
DEFAULT_SOURCE = Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite')
DEFAULT_CATALOG = Path(r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite')
DEFAULT_OUTPUT = Path(r'D:\EncyKlopedia\30_working\catalogue_global_unesco_wikipedia_v25')
SCHEMA = 'encyklopedia.global-article-catalogue.v25/1'
BAD_CAT_START = ('wikipedia ', 'articles ', 'all wikipedia', 'use ', 'cs1 ', 'webarchive ', 'pages ',
                 'short description', 'good articles', 'featured articles', 'template ', 'maintenance ',
                 'tracking ', 'births ', 'deaths ', 'villages ', 'cities ', 'towns ', 'populated places ')

class Refusal(RuntimeError):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def blob(o):
    return (json.dumps(o, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def sha(x):
    return hashlib.sha256(x).hexdigest()


def read_json(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))


def safe_name(s):
    return bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}', s))


def wiki_title(s):
    return '_'.join(str(s).split())


def normalize(s):
    return ' '.join(str(s).replace('_', ' ').casefold().split())


def label(c, lang):
    vals = c.get('preferred_labels', {}).get(lang, [])
    return str(vals[0]) if vals else (str(c.get('unesco_id', '?')) if lang == 'en' else label(c, 'en'))


def topic_category(name):
    s = normalize(name)
    return (0 < len(s) < 256 and not s.startswith(BAD_CAT_START)
            and not any(term in ' ' + s + ' ' for term in (' wikidata ', ' wikipedia ')))


def label_variations(name):
    variants = [name]
    if name.startswith('Educational '):
        variants.append('Education ' + name[len('Educational '):])
    if name.endswith('y'):
        variants.append(name[:-1] + 'ies')
    elif not name.endswith('s'):
        variants.append(name + 's')
    return list(dict.fromkeys(variants))


def load_branch(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise Refusal('Manifeste de branche absent: ' + str(path))
    spec = read_json(path)
    if spec.get('schema') != 'encyklopedia.branch-manifest.v25/1':
        raise Refusal('Schema de branche incompatible: ' + str(path))
    bid, vocab = spec.get('branch_id'), spec.get('vocabulary')
    if not isinstance(bid, str) or not safe_name(bid) or not isinstance(vocab, str) or not safe_name(vocab):
        raise Refusal('Identifiant de branche / vocabulaire invalide')
    conf = spec.get('discovery', {})
    if not (isinstance(conf.get('auto_exact_category_roots'), bool)
            and 0 <= int(conf.get('auto_root_depth', -1)) <= 2
            and 0 <= int(conf.get('max_reviewed_root_depth', -1)) <= 5
            and 1 <= int(conf.get('max_category_tasks', 0)) <= 2_000_000
            and 20 <= int(conf.get('max_members_per_category', 0)) <= 5_000_000):
        raise Refusal('Bornes de decouverte invalides: ' + bid)
    srcs = {}
    for key in ('concepts_file', 'crosswalk_file', 'bridges_file'):
        rel = spec.get(key)
        if rel is None and key != 'concepts_file':
            continue
        if not isinstance(rel, str) or not rel or Path(rel).is_absolute() or '..' in Path(rel).parts:
            raise Refusal('Fichier de reference non relatif: ' + str(rel))
        p = path.parent / rel
        if not p.is_file():
            raise Refusal('Reference manquante: ' + str(p))
        srcs[key] = p
    raw = read_json(srcs['concepts_file'])
    concepts = raw.get('concepts')
    if not isinstance(concepts, list) or not concepts or len(concepts) > 50_000:
        raise Refusal('Liste des concepts absente ou invalide')
    ids = set()
    for c in concepts:
        cid = c.get('unesco_id')
        if not isinstance(cid, str) or not safe_name(cid) or cid in ids:
            raise Refusal('Concept duplique/invalide: ' + str(cid))
        ids.add(cid)
    qids = defaultdict(set)
    if 'crosswalk_file' in srcs:
        crosswalk = read_json(srcs['crosswalk_file'])
        for m in crosswalk.get('mappings', []):
            ext = m.get('external_ref', {})
            mt = re.fullmatch(r'wd-p3916-(concept\d+)', str(m.get('mapping_id', '')))
            if (mt and mt.group(1) in ids and m.get('status') == 'candidate'
                    and ext.get('system') == 'wikidata' and re.fullmatch(r'Q[1-9][0-9]*', str(ext.get('id', '')))):
                qids[mt.group(1)].add(ext['id'])
    bridges = []
    if 'bridges_file' in srcs:
        with srcs['bridges_file'].open(encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            required = {'concept_id', 'category_title', 'status', 'justification', 'depth_limit'}
            if not required <= set(reader.fieldnames or []):
                raise Refusal('Colonnes CSV des ponts manquantes')
            seen = set()
            for r in reader:
                cid, name, status = (str(r[k]).strip() for k in ('concept_id', 'category_title', 'status'))
                if cid not in ids or not topic_category(name) or (cid, name) in seen:
                    raise Refusal('Pont ambigu ou invalide: ' + cid + ' -> ' + name)
                seen.add((cid, name))
                if status not in ('ACTIVE_REVIEWED_AI', 'PROPOSED_NOT_ACTIVE'):
                    raise Refusal('Statut de pont non reconnu: ' + status)
                if status == 'ACTIVE_REVIEWED_AI':
                    reason = str(r['justification']).strip()
                    depth = int(r['depth_limit'])
                    if len(reason) < 15 or not 0 <= depth <= conf['max_reviewed_root_depth']:
                        raise Refusal('Pont non suffisamment qualifie: ' + name)
                    bridges.append((cid, name, reason, depth))
    signature = sha(blob({'manifest': sha(path.read_bytes()),
                          'references': {k: sha(p.read_bytes()) for k, p in sorted(srcs.items())}}))
    return {'path': path, 'spec': spec, 'id': bid, 'vocab': vocab, 'concepts': concepts,
            'qids': qids, 'bridges': bridges, 'signature': signature}


def source_ro(path):
    if not path.is_file():
        raise Refusal('Index SQL Wikipedia absent: ' + str(path))
    uri = path.resolve().as_uri() + '?mode=ro'
    c = sqlite3.connect(uri, uri=True, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute('PRAGMA query_only=ON')
    c.execute('PRAGMA busy_timeout=30000')
    c.execute('BEGIN')  # consistent read snapshot for the duration of this session
    return c


def source_fingerprint(c, path):
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    required = {'wiki_pages', 'wiki_qid', 'wiki_linktargets', 'wiki_categorylink_ids', 'ingest_state'}
    if required - tables:
        raise Refusal('Tables manquantes: ' + ', '.join(sorted(required - tables)))
    indexes = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    required_ix = {'idx_wiki_pages_title', 'idx_wiki_qid_qid', 'idx_wiki_lt_title',
                   'idx_wiki_catid_from', 'idx_wiki_catid_target'}
    if required_ix - indexes:
        raise Refusal('Index manquants, scan complet interdit: ' + ', '.join(sorted(required_ix - indexes)))
    stages = {r['stage']: {'completed': int(r['completed']), 'rows': int(r['rows_imported'])}
              for r in c.execute('SELECT stage,completed,rows_imported FROM ingest_state')}
    for name in ('page', 'page_props', 'linktarget', 'categorylinks'):
        if name not in stages or stages[name]['completed'] != 1:
            raise Refusal('Import de donnees non termine: ' + name)
    # Check that SQLite can use the target index and rowid pagination, without scanning the source.
    plan = ' '.join(str(r[3]) for r in c.execute(
        'EXPLAIN QUERY PLAN SELECT rowid FROM wiki_categorylink_ids INDEXED BY idx_wiki_catid_target '
        'WHERE target_id=? AND rowid>? ORDER BY rowid LIMIT 100', (1, 0)))
    if 'idx_wiki_catid_target' not in plan or 'TEMP B-TREE' in plan.upper():
        raise Refusal('Pagination indexee des categorylinks non disponible: ' + plan)
    st = path.stat()
    desc = {'path': str(path.resolve()), 'size_bytes': st.st_size, 'mtime_ns': st.st_mtime_ns,
            'ingest': stages, 'hash_scope': 'SQLITE_FILE_METADATA_AND_IMPORT_STAGES_NOT_FULL_CONTENT'}
    return desc, sha(blob(desc))


def cat_target(src, name):
    r = src.execute('SELECT target_id FROM wiki_linktargets WHERE ns=14 AND title=? LIMIT 1',
                    (wiki_title(name),)).fetchone()
    return int(r[0]) if r else None


def source_page(src, title):
    return src.execute('SELECT page_id,ns,title,redirect,latest_revision,content_bytes FROM wiki_pages '
                       'WHERE ns=0 AND title=? LIMIT 1', (wiki_title(title),)).fetchone()


def source_by_qid(src, qid):
    return src.execute('SELECT p.page_id,p.ns,p.title,p.redirect,p.latest_revision,p.content_bytes '
                       'FROM wiki_qid q JOIN wiki_pages p ON p.page_id=q.page_id '
                       'WHERE q.qid=? AND p.ns=0 LIMIT 20', (qid,))


def open_catalog(path):
    # Never attach/create tables inside an unrelated pre-existing SQLite database.
    if path.exists():
        if not path.is_file() or path.is_symlink():
            raise Refusal('Chemin de catalogue non regulier / symbolique')
        check = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            table = check.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'").fetchone()
            if not table:
                raise Refusal('Fichier SQLite preexistant etranger au catalogue v25')
            row = check.execute("SELECT value FROM meta WHERE key='schema'").fetchone()
            if not row or row[0] != SCHEMA:
                raise Refusal('Fichier SQLite de schema incompatible')
        finally:
            check.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=120)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA busy_timeout=120000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=NORMAL')
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA temp_store=FILE')
    db.execute('PRAGMA cache_size=-65536')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY,value TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS branches (
      branch_id TEXT PRIMARY KEY,vocabulary TEXT NOT NULL,branch_version TEXT NOT NULL,
      title_fr TEXT NOT NULL,config_sha TEXT NOT NULL,category_tasks INTEGER NOT NULL DEFAULT 0,
      max_category_tasks INTEGER NOT NULL,max_members_per_category INTEGER NOT NULL,
      added_utc TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS concepts (
      vocabulary TEXT NOT NULL,concept_id TEXT NOT NULL,label_fr TEXT NOT NULL,label_en TEXT NOT NULL,
      broader_json TEXT NOT NULL,related_json TEXT NOT NULL,
      PRIMARY KEY(vocabulary,concept_id));
    CREATE TABLE IF NOT EXISTS branch_concepts (
      branch_id TEXT NOT NULL,vocabulary TEXT NOT NULL,concept_id TEXT NOT NULL,
      PRIMARY KEY(branch_id,concept_id),
      FOREIGN KEY(branch_id) REFERENCES branches(branch_id),
      FOREIGN KEY(vocabulary,concept_id) REFERENCES concepts(vocabulary,concept_id));
    CREATE TABLE IF NOT EXISTS articles (
      wiki TEXT NOT NULL,page_id INTEGER NOT NULL,title TEXT NOT NULL,qid TEXT,
      revision_id TEXT,content_bytes INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(wiki,page_id));
    CREATE TABLE IF NOT EXISTS assignments (
      branch_id TEXT NOT NULL,wiki TEXT NOT NULL,page_id INTEGER NOT NULL,
      vocabulary TEXT NOT NULL,concept_id TEXT NOT NULL,score INTEGER NOT NULL,
      evidence_kind TEXT NOT NULL,evidence_origin TEXT NOT NULL,root_category TEXT NOT NULL,
      evidence_hits INTEGER NOT NULL DEFAULT 1,
      PRIMARY KEY(branch_id,wiki,page_id,concept_id),
      FOREIGN KEY(wiki,page_id) REFERENCES articles(wiki,page_id),
      FOREIGN KEY(branch_id,concept_id) REFERENCES branch_concepts(branch_id,concept_id));
    CREATE TABLE IF NOT EXISTS category_suggestions (
      branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,category_title TEXT NOT NULL,
      example_page_id INTEGER NOT NULL,lexical_score REAL NOT NULL,
      review_state TEXT NOT NULL DEFAULT 'TO_REVIEW',
      PRIMARY KEY(branch_id,concept_id,category_title));
    CREATE INDEX IF NOT EXISTS idx_suggestion_review ON category_suggestions(branch_id,lexical_score DESC);
    CREATE TABLE IF NOT EXISTS category_tasks (
      task_id INTEGER PRIMARY KEY AUTOINCREMENT,
      branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,
      root_category TEXT NOT NULL,category_title TEXT NOT NULL,target_id INTEGER NOT NULL,
      depth INTEGER NOT NULL,max_depth INTEGER NOT NULL,kind TEXT NOT NULL,
      last_rowid INTEGER NOT NULL DEFAULT 0,members_seen INTEGER NOT NULL DEFAULT 0,
      state TEXT NOT NULL DEFAULT 'PENDING',
      UNIQUE(branch_id,concept_id,root_category,target_id),
      FOREIGN KEY(branch_id,concept_id) REFERENCES branch_concepts(branch_id,concept_id));
    CREATE TABLE IF NOT EXISTS audit_events (
      event_id INTEGER PRIMARY KEY AUTOINCREMENT,branch_id TEXT NOT NULL,
      kind TEXT NOT NULL,description TEXT NOT NULL,created_utc TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS idx_assgn_concept ON assignments(branch_id,concept_id,score DESC,page_id);
    CREATE INDEX IF NOT EXISTS idx_assgn_article ON assignments(wiki,page_id,score DESC);
    CREATE INDEX IF NOT EXISTS idx_assgn_branch_article ON assignments(branch_id,page_id);
    CREATE INDEX IF NOT EXISTS idx_tasks_work ON category_tasks(state,task_id);
    CREATE INDEX IF NOT EXISTS idx_tasks_branch ON category_tasks(branch_id,state);
    ''')
    db.commit()
    return db


def meta(db, key):
    r = db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
    return r[0] if r else None


def tick(db):
    db.execute("UPDATE meta SET value=CAST(value AS INTEGER)+1 WHERE key='sequence'")


def bind_source(db, signature, info):
    old = meta(db, 'source_sha')
    if old is not None and old != signature:
        raise Refusal('La base Wikipedia a change depuis le debut du catalogue v25. '
                      'Refus de melanger deux snapshots: creer un nouveau catalogue versionne.')
    engine_schema = meta(db, 'schema')
    if engine_schema is not None and engine_schema != SCHEMA:
        raise Refusal('Catalogue existant de schema incompatible')
    with db:
        db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)', ('schema', SCHEMA))
        db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)', ('source_sha', signature))
        db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)', ('source_info', json.dumps(info, sort_keys=True)))
        db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)', ('sequence', '0'))
        db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)', ('created_utc', now()))


def add_article(db, p, qid=None):
    if int(p['ns']) != 0 or int(p['redirect']) != 0:
        return False
    db.execute('''INSERT INTO articles(wiki,page_id,title,qid,revision_id,content_bytes)
      VALUES('enwiki',?,?,?,?,?) ON CONFLICT(wiki,page_id) DO UPDATE SET
      qid=COALESCE(articles.qid,excluded.qid)''',
       (int(p['page_id']), str(p['title']).replace('_', ' '), qid,
        str(p['latest_revision'] or ''), int(p['content_bytes'] or 0)))
    return True


def associate(db, bid, vocab, cid, p, score, kind, detail, root=''):
    if not add_article(db, p):
        return
    db.execute('''INSERT INTO assignments
      (branch_id,wiki,page_id,vocabulary,concept_id,score,evidence_kind,evidence_origin,root_category)
      VALUES (?,'enwiki',?,?,?,?,?,?,?)
      ON CONFLICT(branch_id,wiki,page_id,concept_id) DO UPDATE SET
        evidence_hits=assignments.evidence_hits+1,
        score=MAX(assignments.score,excluded.score),
        evidence_kind=CASE WHEN excluded.score>assignments.score THEN excluded.evidence_kind ELSE assignments.evidence_kind END,
        evidence_origin=CASE WHEN excluded.score>assignments.score THEN excluded.evidence_origin ELSE assignments.evidence_origin END,
        root_category=CASE WHEN excluded.score>assignments.score THEN excluded.root_category ELSE assignments.root_category END''',
      (bid, int(p['page_id']), vocab, cid, score, kind, detail, root))


def enqueue(db, branch, cid, root, category, target, depth, max_depth, kind):
    bid = branch['id']
    limit, count = db.execute('SELECT max_category_tasks,category_tasks FROM branches WHERE branch_id=?', (bid,)).fetchone()
    existing = db.execute('SELECT 1 FROM category_tasks WHERE branch_id=? AND concept_id=? AND root_category=? AND target_id=?',
                          (bid, cid, root, target)).fetchone()
    if existing:
        return
    if count >= limit:
        db.execute('INSERT INTO audit_events(branch_id,kind,description,created_utc) VALUES(?,?,?,?)',
                   (bid, 'TASK_LIMIT', cid + ' ' + category, now()))
        return
    db.execute('''INSERT INTO category_tasks
      (branch_id,concept_id,root_category,category_title,target_id,depth,max_depth,kind)
      VALUES (?,?,?,?,?,?,?,?)''', (bid, cid, root, category, target, depth, max_depth, kind))
    db.execute('UPDATE branches SET category_tasks=category_tasks+1 WHERE branch_id=?', (bid,))


def suggest_anchor_categories(src, db, branch, cid, page_id, label_en):
    # Efficient source_page_id index; these are proposals, never active bridges.
    tks = set(re.findall(r'[a-z]{3,}', normalize(label_en))) - {
        'the', 'and', 'for', 'with', 'of', 'in', 'on', 'an', 'a', 'to'}
    if not tks:
        return
    for r in src.execute('''SELECT t.title FROM wiki_categorylink_ids c INDEXED BY idx_wiki_catid_from
                 JOIN wiki_linktargets t ON t.target_id=c.target_id AND t.ns=14
                 WHERE c.source_page_id=? LIMIT 35''', (page_id,)):
        cat = str(r[0]).replace('_', ' ')
        if not topic_category(cat):
            continue
        matched = len(tks & set(re.findall(r'[a-z]{3,}', normalize(cat))))
        if not matched:
            continue
        score = round(matched / len(tks), 3)
        db.execute('''INSERT OR IGNORE INTO category_suggestions
           (branch_id,concept_id,category_title,example_page_id,lexical_score)
           VALUES (?,?,?,?,?)''', (branch['id'], cid, cat, page_id, score))


def ensure_roots(src, db, branch):
    # Resumable: when task limits are increased, previously rejected roots can
    # be discovered again without replaying anchor assignments.
    spec = branch['spec']
    for c in branch['concepts']:
        cid = c['unesco_id']
        if spec['discovery']['auto_exact_category_roots']:
            for possible in label_variations(label(c, 'en')):
                if topic_category(possible):
                    target = cat_target(src, possible)
                    if target is not None:
                        enqueue(db, branch, cid, possible, possible, target, 0,
                                spec['discovery']['auto_root_depth'], 'AUTO_EXACT_LABEL_CANDIDATE')
    for cid, category, justification, depth in branch['bridges']:
        target = cat_target(src, category)
        if target is not None:
            enqueue(db, branch, cid, category, category, target, 0, depth,
                    'AI_REVIEWED_BRIDGE_CANDIDATE')


def seed_branch(src, db, branch):
    bid, vocab, spec = branch['id'], branch['vocab'], branch['spec']
    existing = db.execute('SELECT config_sha FROM branches WHERE branch_id=?', (bid,)).fetchone()
    if existing:
        if existing[0] != branch['signature']:
            raise Refusal('Branche deja enregistree avec un autre manifeste: ' + bid +
                          '. Utiliser un nouvel identifiant/version de branche; pas de mutation silencieuse.')
        with db:
            before = db.execute('SELECT category_tasks FROM branches WHERE branch_id=?', (bid,)).fetchone()[0]
            ensure_roots(src, db, branch)
            after = db.execute('SELECT category_tasks FROM branches WHERE branch_id=?', (bid,)).fetchone()[0]
            if after > before:
                tick(db)
        return {'branch_id': bid, 'seeded': False, 'concepts': len(branch['concepts']),
                'new_category_tasks': after-before}
    with db:
        db.execute('INSERT INTO branches(branch_id,vocabulary,branch_version,title_fr,config_sha,max_category_tasks,max_members_per_category,added_utc) '
                   'VALUES(?,?,?,?,?,?,?,?)', (bid, vocab, str(spec.get('branch_version', 'v1')),
                   str(spec.get('title_fr', bid)), branch['signature'],
                   spec['discovery']['max_category_tasks'], spec['discovery']['max_members_per_category'], now()))
        for c in branch['concepts']:
            cid = c['unesco_id']
            val = (vocab, cid, label(c, 'fr'), label(c, 'en'),
                   json.dumps(c.get('broader', []), ensure_ascii=False),
                   json.dumps(c.get('related', []), ensure_ascii=False))
            db.execute('INSERT OR IGNORE INTO concepts VALUES(?,?,?,?,?,?)', val)
            prev = db.execute('SELECT label_fr,label_en,broader_json FROM concepts WHERE vocabulary=? AND concept_id=?',
                              (vocab, cid)).fetchone()
            if (prev[0], prev[1], prev[2]) != (val[2], val[3], val[4]):
                raise Refusal('Identite de concept reutilisee avec autre definition: ' + cid)
            db.execute('INSERT INTO branch_concepts VALUES(?,?,?)', (bid, vocab, cid))
        # Seed only via indexed title/QID lookups. All remain candidates.
        for c in branch['concepts']:
            cid = c['unesco_id']
            anchors = set()
            for q in sorted(branch['qids'].get(cid, [])):
                for p in source_by_qid(src, q):
                    associate(db, bid, vocab, cid, p, 96, 'WIKIDATA_P3916_CANDIDATE', q)
                    if int(p['ns']) == 0 and not int(p['redirect']):
                        anchors.add(int(p['page_id']))
            name = label(c, 'en')
            p = source_page(src, name)
            if p:
                associate(db, bid, vocab, cid, p, 90, 'TITLE_EQUALITY_CANDIDATE', name)
                if int(p['ns']) == 0 and not int(p['redirect']):
                    anchors.add(int(p['page_id']))
            for page_id in sorted(anchors):
                suggest_anchor_categories(src, db, branch, cid, page_id, name)
        ensure_roots(src, db, branch)
        tick(db)
    return {'branch_id': bid, 'seeded': True, 'concepts': len(branch['concepts']),
            'category_tasks': db.execute('SELECT category_tasks FROM branches WHERE branch_id=?', (bid,)).fetchone()[0]}


def work_one_batch(src, db, branches, batch_size, branch_filter=None):
    # One bounded transaction = one durable resume point. Deterministic SQLite rowid keyset.
    db.execute('BEGIN IMMEDIATE')
    try:
        if branch_filter is None:
            task = db.execute("SELECT * FROM category_tasks WHERE state='PENDING' ORDER BY task_id LIMIT 1").fetchone()
        else:
            task = db.execute("SELECT * FROM category_tasks WHERE state='PENDING' AND branch_id=? "
                              "ORDER BY task_id LIMIT 1", (branch_filter,)).fetchone()
        if task is None:
            db.commit()
            return None
        branch = branches.get(task['branch_id'])
        if branch is None:
            raise Refusal('Manifeste de branche manquant pour une tache: ' + task['branch_id'])
        limit = db.execute('SELECT max_members_per_category FROM branches WHERE branch_id=?',
                           (task['branch_id'],)).fetchone()[0]
        remaining = limit - task['members_seen']
        if remaining <= 0:
            db.execute("UPDATE category_tasks SET state='CAPPED' WHERE task_id=?", (task['task_id'],))
            tick(db)
            db.commit()
            return {'category': task['category_title'], 'status': 'CAPPED', 'processed': 0}
        size = min(batch_size, remaining)
        rows = src.execute('''SELECT c.rowid AS cursor,c.source_page_id,c.type,
              p.page_id,p.ns,p.title,p.redirect,p.latest_revision,p.content_bytes,q.qid
          FROM wiki_categorylink_ids c INDEXED BY idx_wiki_catid_target
          LEFT JOIN wiki_pages p ON p.page_id=c.source_page_id
          LEFT JOIN wiki_qid q ON q.page_id=p.page_id
          WHERE c.target_id=? AND c.rowid>? ORDER BY c.rowid LIMIT ?''',
           (task['target_id'], task['last_rowid'], size)).fetchall()
        depth = int(task['depth'])
        if task['kind'].startswith('AI_REVIEWED'):
            confidence = 78 - 8*depth
        else:
            confidence = 64 - 8*depth
        for p in rows:
            if p['page_id'] is not None and int(p['ns']) == 0 and not int(p['redirect']):
                associate(db, task['branch_id'], branch['vocab'], task['concept_id'], p,
                          max(20, confidence), task['kind'], 'Category:' + task['category_title'],
                          task['root_category'])
                if p['qid']:
                    db.execute('UPDATE articles SET qid=COALESCE(qid,?) WHERE wiki=? AND page_id=?',
                               (p['qid'], 'enwiki', p['page_id']))
            elif p['page_id'] is not None and int(p['ns']) == 14 and depth < task['max_depth'] and str(p['type']).lower() == 'subcat':
                sub = str(p['title']).replace('_', ' ')
                if topic_category(sub):
                    target = cat_target(src, sub)
                    if target is not None:
                        enqueue(db, branch, task['concept_id'], task['root_category'], sub, target,
                                depth + 1, task['max_depth'], task['kind'])
        seen = int(task['members_seen']) + len(rows)
        if len(rows) < size:
            status = 'DONE'
        elif seen >= limit:
            status = 'CAPPED'
        else:
            status = 'PENDING'
        last = int(rows[-1]['cursor']) if rows else int(task['last_rowid'])
        db.execute('UPDATE category_tasks SET last_rowid=?,members_seen=?,state=? WHERE task_id=?',
                   (last, seen, status, task['task_id']))
        if status == 'CAPPED':
            db.execute('INSERT INTO audit_events(branch_id,kind,description,created_utc) VALUES(?,?,?,?)',
                       (task['branch_id'], 'CATEGORY_CAPPED', task['concept_id'] + ' ' + task['category_title'], now()))
        tick(db)
        db.commit()
        return {'branch_id': task['branch_id'], 'concept_id': task['concept_id'],
                'category': task['category_title'], 'processed': len(rows), 'status': status,
                'cursor': last}
    except Exception:
        db.rollback()
        raise


def escape(v):
    return html.escape(str(v), quote=True)


def csv_bytes(rows, fields):
    f = io.StringIO(newline='')
    w = csv.writer(f, lineterminator='\n')
    w.writerow(fields)
    for r in rows:
        vals = []
        for k in fields:
            v = r.get(k, '')
            if isinstance(v, (list, dict)):
                v = json.dumps(v, ensure_ascii=False)
            s = str(v) if v is not None else ''
            if s.lstrip().startswith(('=', '+', '-', '@')):
                s = "'" + s
            vals.append(s)
        w.writerow(vals)
    return ('\ufeff' + f.getvalue()).encode('utf-8')


CSS = '''body{font:16px/1.55 system-ui,Segoe UI,sans-serif;color:#27394b;background:#f5f7fb;margin:0}header{background:#19334d;color:white;padding:25px 5%}main{max-width:1150px;margin:25px auto;padding:0 18px}table{width:100%;border-collapse:collapse;background:white}th,td{border-bottom:1px solid #dbe3eb;padding:9px;text-align:left}th{background:#e8eef5}a{color:#126195}h1{margin:0}.muted{color:#62768a}.box{background:#fff;border:1px solid #dae1e8;border-radius:8px;padding:15px;margin:12px 0}code{overflow-wrap:anywhere}.status{color:#8f5b14}'''


def page(title, body):
    return ('<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" '
            'content="width=device-width,initial-scale=1"><title>' + escape(title) + '</title><style>' + CSS +
            '</style></head><body><header><h1>' + escape(title) +
            '</h1><p>Catalogue global UNESCO × Wikipédia · candidats · pas des articles publiés</p></header><main>' +
            body + '</main></body></html>').encode('utf-8')


def snapshot(db, path, out_root, sample_limit):
    seq = int(meta(db, 'sequence') or 0)
    final = out_root / 'snapshots' / f'{seq:010d}'
    if final.exists():
        result = verify_snapshot(final)
        save_latest(out_root, final)
        return result
    branches = [dict(x) for x in db.execute('SELECT * FROM branches ORDER BY branch_id')]
    stats = []
    files = {}
    all_concept_rows = []
    branch_index = ['<p class="box status">Classement documentaire en cours : les articles et scores sont des candidats, '
                    'les limites ne représentent pas la couverture entière de Wikipédia. Aucun Kristal canonique modifié.</p>',
                    f'<p>Identifiants d’articles uniques : <strong>{db.execute("SELECT count(*) FROM articles").fetchone()[0]}</strong></p>',
                    '<table><thead><tr><th>Branche UNESCO</th><th>Concepts</th><th>Rattachements</th><th>Catégories en attente</th></tr></thead><tbody>']
    for b in branches:
        bid = b['branch_id']
        cnt = db.execute('SELECT count(*) FROM branch_concepts WHERE branch_id=?', (bid,)).fetchone()[0]
        acount = db.execute('SELECT count(*) FROM assignments WHERE branch_id=?', (bid,)).fetchone()[0]
        tasks = {r['state']: r['n'] for r in db.execute(
            'SELECT state,count(*) n FROM category_tasks WHERE branch_id=? GROUP BY state', (bid,))}
        s = {'branch_id': bid, 'title_fr': b['title_fr'], 'concepts': cnt,
             'assignments': acount, 'category_tasks': tasks, 'category_tasks_total': b['category_tasks']}
        stats.append(s)
        safe_bid = urllib.parse.quote(bid, safe='')
        branch_index.append('<tr><td><a href="' + safe_bid + '.html">' + escape(b['title_fr']) +
                            '</a></td><td>' + str(cnt) + '</td><td>' + str(acount) +
                            '</td><td>' + str(tasks.get('PENDING', 0)) + '</td></tr>')
        concept_rows = [dict(r) for r in db.execute('''SELECT c.concept_id,c.label_fr,c.label_en,c.broader_json,
             count(a.page_id) AS total FROM branch_concepts bc
             JOIN concepts c ON c.vocabulary=bc.vocabulary AND c.concept_id=bc.concept_id
             LEFT JOIN assignments a ON a.branch_id=bc.branch_id AND a.concept_id=bc.concept_id
             WHERE bc.branch_id=? GROUP BY c.concept_id ORDER BY c.label_fr COLLATE NOCASE''', (bid,))]
        all_concept_rows.extend({'branch_id': bid, 'concept_id': r['concept_id'], 'label_fr': r['label_fr'],
                                 'label_en': r['label_en'], 'assignments': r['total'],
                                 'broader': r['broader_json']} for r in concept_rows)
        # Present UNESCO hierarchy as an editorial navigation, not a forced
        # assertion that an article belongs to the parent concept.
        index = {r['concept_id']: r for r in concept_rows}
        parents, children = {}, defaultdict(list)
        for r in concept_rows:
            local_parents = [x for x in json.loads(r['broader_json']) if x in index]
            parent_id = sorted(local_parents)[0] if local_parents else None
            parents[r['concept_id']] = parent_id
            children[parent_id].append(r['concept_id'])
        for child_ids in children.values():
            child_ids.sort(key=lambda cid: index[cid]['label_fr'].casefold())
        visited_nav = set()
        def nav_node(cid, stack):
            if cid in stack or cid in visited_nav:
                return ''
            visited_nav.add(cid)
            r = index[cid]
            inner = ''.join(nav_node(x, stack | {cid}) for x in children.get(cid, []))
            return ('<li><a href="#' + escape(cid) + '">' + escape(r['label_fr']) + '</a> '
                    '<span class="muted">(' + str(r['total']) + ')</span>' +
                    ('<ul>' + inner + '</ul>' if inner else '') + '</li>')
        tree = ''.join(nav_node(cid, set()) for cid in children.get(None, []))
        tree += ''.join(nav_node(cid, set()) for cid in sorted(index) if cid not in visited_nav)
        bbody = ['<p><a href="index.html">← Toutes les branches</a></p>',
                 '<p class="box">Une même page est unique dans le catalogue global; elle peut apparaître sous plusieurs concepts. '
                 'Les scores sont heuristiques, non des probabilités.</p>',
                 '<h2>Hiérarchie du thésaurus et couverture</h2><ul>' + tree + '</ul>',
                 '<h2>Articles candidats par concept</h2>',
                 '<table><thead><tr><th>Concept UNESCO</th><th>Articles candidats</th><th>Exemples (max. 5)</th></tr></thead><tbody>']
        for r in concept_rows:
            sampled = db.execute('''SELECT p.title,p.page_id,a.score FROM assignments a
                   JOIN articles p ON p.wiki=a.wiki AND p.page_id=a.page_id
                   WHERE a.branch_id=? AND a.concept_id=? ORDER BY a.score DESC,a.page_id LIMIT 5''',
                   (bid, r['concept_id'])).fetchall()
            examples = ', '.join('<a href="https://en.wikipedia.org/wiki/' +
                                 urllib.parse.quote(wiki_title(p['title']), safe='()_') + '">' +
                                 escape(p['title']) + '</a>' for p in sampled)
            bbody.append('<tr id="' + escape(r['concept_id']) + '"><td>' + escape(r['label_fr']) + ' <span class="muted">(' +
                         escape(r['concept_id']) + ')</span></td><td>' + str(r['total']) +
                         '</td><td>' + examples + '</td></tr>')
        bbody.append('</tbody></table>')
        files['reader_fr/' + bid + '.html'] = page(b['title_fr'], ''.join(bbody))
    branch_index.append('</tbody></table><p><a href="../CONCEPTS_ECHANTILLON_V25.csv">Index des concepts (CSV)</a> · '
                        '<a href="../ARTICLES_ECHANTILLON_V25.csv">Articles échantillons (CSV)</a> · '
                        '<a href="../RAPPORT_V25.json">Rapport</a></p>')
    files['reader_fr/index.html'] = page('EncyKlopedia — architecture mondiale (v25)', ''.join(branch_index))
    article_rows = [dict(r) for r in db.execute('SELECT wiki,page_id,title,qid,revision_id FROM articles ORDER BY page_id LIMIT ?',
                                                (sample_limit,))]
    assoc_rows = [dict(r) for r in db.execute('SELECT branch_id,page_id,concept_id,score,evidence_kind,evidence_origin '
                                              'FROM assignments ORDER BY branch_id,concept_id,score DESC LIMIT ?',
                                              (sample_limit,))]
    task_rows = [dict(r) for r in db.execute('SELECT branch_id,concept_id,category_title,depth,kind,state,members_seen '
                                            'FROM category_tasks ORDER BY task_id LIMIT ?', (sample_limit,))]
    suggestion_rows = [dict(r) for r in db.execute('SELECT branch_id,concept_id,category_title,example_page_id,lexical_score,review_state '
                         'FROM category_suggestions ORDER BY branch_id,lexical_score DESC LIMIT ?', (sample_limit,))]
    files.update({
        'PONTS_A_REVOIR_V25.csv': csv_bytes(suggestion_rows,
            ['branch_id','concept_id','category_title','example_page_id','lexical_score','review_state']),
        'ARTICLES_ECHANTILLON_V25.csv': csv_bytes(article_rows, ['wiki', 'page_id', 'title', 'qid', 'revision_id']),
        'RATTACHEMENTS_ECHANTILLON_V25.csv': csv_bytes(assoc_rows,
            ['branch_id', 'page_id', 'concept_id', 'score', 'evidence_kind', 'evidence_origin']),
        'CONCEPTS_ECHANTILLON_V25.csv': csv_bytes(all_concept_rows,
            ['branch_id', 'concept_id', 'label_fr', 'label_en', 'assignments', 'broader']),
        'CATEGORIES_ECHANTILLON_V25.csv': csv_bytes(task_rows,
            ['branch_id', 'concept_id', 'category_title', 'depth', 'kind', 'state', 'members_seen'])
    })
    report = {'format': SCHEMA, 'snapshot_sequence': seq, 'generated_utc': now(),
              'source': json.loads(meta(db, 'source_info')),
              'unique_articles': db.execute('SELECT count(*) FROM articles').fetchone()[0],
              'assignments': db.execute('SELECT count(*) FROM assignments').fetchone()[0],
              'category_bridges_to_review': db.execute('SELECT count(*) FROM category_suggestions').fetchone()[0],
              'branches': stats, 'editorial_status': 'DISCOVERY_CANDIDATES_NOT_REVIEWED',
              'coverage_claim': 'INDEXED_CATEGORY_EXPLORATION_NOT_EXHAUSTIVE_WIKIPEDIA_CLASSIFICATION',
              'score_interpretation': 'HEURISTIC_RANKING_NOT_PROBABILITY',
              'category_caps_require_review': any('CAPPED' in b['category_tasks'] for b in stats), 'sampling_limit': sample_limit,
              'raw_wikipedia_texts_imported': 0, 'source_sql_read_only': True,
              'canonical_admissions': 0, 'publication_authorized': False}
    files['RAPPORT_V25.json'] = blob(report)
    out_root.mkdir(parents=True, exist_ok=True)
    (out_root / 'snapshots').mkdir(parents=True, exist_ok=True)
    temp = Path(tempfile.mkdtemp(prefix='.v25_snapshot_', dir=out_root / 'snapshots'))
    try:
        for name, raw in files.items():
            p = temp / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
        with zipfile.ZipFile(temp / 'EXPORT_V25_POUR_CHATGPT.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
            for name in sorted(files):
                if not name.startswith('reader_fr/'):
                    z.write(temp / name, name)
        hashes = {p.relative_to(temp).as_posix(): sha(p.read_bytes()) for p in temp.rglob('*') if p.is_file()}
        (temp / 'MANIFEST_V25.json').write_bytes(blob({'version': VERSION, 'snapshot_sequence': seq,
                                                       'files_sha256': hashes, 'canonical_admissions': 0}))
        verify_snapshot(temp)
        temp.rename(final)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    save_latest(out_root, final)
    return verify_snapshot(final)


def save_latest(out_root, final):
    latest = out_root / 'LATEST.json'
    local_latest = out_root / '.LATEST.tmp'
    local_latest.write_bytes(blob({'snapshot': final.relative_to(out_root).as_posix(),
                                   'reader': (final / 'reader_fr' / 'index.html').as_posix(),
                                   'export': (final / 'EXPORT_V25_POUR_CHATGPT.zip').as_posix()}))
    os.replace(local_latest, latest)


def expand_limits(db, branch_id, new_members, new_tasks):
    """Modification explicite et tracable des budgets; ne change pas la taxonomie."""
    old = db.execute('SELECT max_members_per_category,max_category_tasks FROM branches WHERE branch_id=?',
                     (branch_id,)).fetchone()
    if old is None:
        raise Refusal('Branche non connue: ' + branch_id)
    if new_members < old[0] or new_tasks < old[1] or new_members > 5_000_000 or new_tasks > 2_000_000:
        raise Refusal('Extensions doivent etre superieures ou egales, dans les plafonds de securite')
    with db:
        db.execute('UPDATE branches SET max_members_per_category=?,max_category_tasks=? WHERE branch_id=?',
                   (new_members, new_tasks, branch_id))
        n = db.execute("UPDATE category_tasks SET state='PENDING' WHERE branch_id=? AND state='CAPPED' "
                       'AND members_seen<?', (branch_id, new_members)).rowcount
        db.execute('INSERT INTO audit_events(branch_id,kind,description,created_utc) VALUES (?,?,?,?)',
                   (branch_id, 'EXPLICIT_BUDGET_EXTENSION',
                    json.dumps({'before': list(old), 'after': [new_members,new_tasks],
                                'tasks_reopened': n}), now()))
        tick(db)
    return {'status': 'V25_BUDGETS_EXTENDED', 'branch_id': branch_id,
            'max_members_per_category': new_members, 'max_category_tasks': new_tasks,
            'capped_tasks_reopened': n}


def verify_snapshot(folder):
    if not folder.is_dir() or folder.is_symlink():
        raise Refusal('Snapshot introuvable')
    man = read_json(folder / 'MANIFEST_V25.json')
    files = man.get('files_sha256')
    if man.get('version') != VERSION or not isinstance(files, dict):
        raise Refusal('Manifest v25 invalide')
    names = {p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    if names != set(files) | {'MANIFEST_V25.json'}:
        raise Refusal('Snapshot incomplet ou altéré')
    for name, expected in files.items():
        parts = name.split('/')
        if any(x in ('', '.', '..') for x in parts) or not re.fullmatch(r'[a-f0-9]{64}', expected):
            raise Refusal('Manifest: chemin/empreinte invalide')
        if sha((folder / name).read_bytes()) != expected:
            raise Refusal('SHA-256 de sortie incorrect: ' + name)
    rpt = read_json(folder / 'RAPPORT_V25.json')
    if rpt.get('canonical_admissions') != 0 or rpt.get('publication_authorized') is not False:
        raise Refusal('Statut de publication non conforme')
    return {'status': 'V25_SNAPSHOT_OK', 'files_verified': len(files),
            'unique_articles': rpt['unique_articles'], 'assignments': rpt['assignments'],
            'reader': str(folder / 'reader_fr' / 'index.html'),
            'export': str(folder / 'EXPORT_V25_POUR_CHATGPT.zip')}



def export_semantic_batch(db, out_root, branch_id, after_page_id, batch_limit):
    """Transport deterministic small batches of article metadata, never raw text."""
    if not safe_name(branch_id) or after_page_id < 0 or not 1 <= batch_limit <= 5000:
        raise Refusal('Parametres export-batch invalides')
    if not db.execute('SELECT 1 FROM branches WHERE branch_id=?', (branch_id,)).fetchone():
        raise Refusal('Branche absente du catalogue: ' + branch_id)
    pageids = [int(x[0]) for x in db.execute(
        'SELECT DISTINCT page_id FROM assignments INDEXED BY idx_assgn_branch_article '
        'WHERE branch_id=? AND page_id>? ORDER BY page_id LIMIT ?',
        (branch_id, after_page_id, batch_limit)).fetchall()]
    if not pageids:
        return {'status': 'V25_BATCH_EMPTY', 'branch_id': branch_id, 'after_page_id': after_page_id}
    marker = ','.join('?' for _ in pageids)
    rows = [dict(x) for x in db.execute('SELECT wiki,page_id,title,qid,revision_id,content_bytes '
                                       "FROM articles WHERE wiki='enwiki' AND page_id IN (" + marker + ') '
                                       'ORDER BY page_id', pageids)]
    bypage = defaultdict(list)
    for a in db.execute('SELECT page_id,concept_id,score,evidence_kind,evidence_origin '
                        'FROM assignments WHERE branch_id=? AND page_id IN (' + marker + ') '
                        'ORDER BY page_id,score DESC,concept_id', [branch_id, *pageids]):
        bypage[a['page_id']].append(dict(a))
    contents = b''.join(json.dumps({'article_id': 'enwiki:' + str(a['page_id']), **a,
                                    'concept_assignments': bypage[a['page_id']],
                                    'status': 'CANDIDATE_NOT_CANONICAL_NOT_SEMANTICALLY_PROCESSED'},
                                   ensure_ascii=False, sort_keys=True).encode('utf-8') + b'\n'
                       for a in rows)
    seq = int(meta(db, 'sequence'))
    base = f'{branch_id}__s{seq:010d}__after{after_page_id}__to{pageids[-1]}'
    folder = out_root / 'batches'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (base + '.jsonl')
    manifest = folder / (base + '.manifest.json')
    spec = {'format': 'encyklopedia.semantic-batch-staging.v25/1', 'branch_id': branch_id,
            'from_page_id_exclusive': after_page_id, 'to_page_id_inclusive': pageids[-1],
            'records': len(rows), 'snapshot_sequence': seq, 'sha256': sha(contents),
            'article_texts_included': False, 'canonical_admissions': 0,
            'publication_authorized': False}
    data_m = blob(spec)
    if path.exists() or manifest.exists():
        if not path.is_file() or not manifest.is_file() or path.read_bytes() != contents or manifest.read_bytes() != data_m:
            raise Refusal('Lot export deja present mais different: ' + base)
    else:
        # Atomic file creation. Interrupted writes leave only a .partial that may be removed manually.
        partial = folder / (base + '.partial')
        if partial.exists():
            raise Refusal('Lot partiel ancien a inspecter: ' + str(partial))
        with partial.open('xb') as fp:
            fp.write(contents)
        os.replace(partial, path)
        tmp_manifest = folder / (base + '.manifest.partial')
        with tmp_manifest.open('xb') as fp:
            fp.write(data_m)
        os.replace(tmp_manifest, manifest)
    return {'status': 'V25_BATCH_EXPORTED', **spec, 'file': str(path),
            'next_after_page_id': pageids[-1], 'manifest': str(manifest)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=('preflight', 'run', 'report', 'verify', 'extend', 'export-batch'))
    ap.add_argument('--source-db', type=Path, default=DEFAULT_SOURCE)
    ap.add_argument('--catalogue-db', type=Path, default=DEFAULT_CATALOG)
    ap.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    ap.add_argument('--branch', type=Path, action='append')
    ap.add_argument('--max-batches', type=int, default=50)
    ap.add_argument('--extend-branch-id', type=str)
    ap.add_argument('--new-max-members', type=int)
    ap.add_argument('--new-max-tasks', type=int)
    ap.add_argument('--batch-size', type=int, default=1000)
    ap.add_argument('--sample-limit', type=int, default=300)
    ap.add_argument('--export-branch-id', type=str)
    ap.add_argument('--after-page-id', type=int, default=0)
    ap.add_argument('--batch-limit', type=int, default=1000)
    args = ap.parse_args(argv)
    if not (0 <= args.max_batches <= 100000 and 10 <= args.batch_size <= 5000
            and 10 <= args.sample_limit <= 10000):
        raise Refusal('Parametres hors limites')
    specs = [load_branch(p) for p in (args.branch or [DEFAULT_BRANCH])]
    if len({b['id'] for b in specs}) != len(specs):
        raise Refusal('Branche en double dans les arguments')
    if args.action == 'verify':
        latest = read_json(args.output_dir / 'LATEST.json')
        snap_path = (args.output_dir / latest['snapshot']).resolve()
        if args.output_dir.resolve() not in snap_path.parents:
            raise Refusal('Chemin de snapshot invalide')
        result = verify_snapshot(snap_path)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    src = source_ro(args.source_db)
    try:
        info, fp = source_fingerprint(src, args.source_db)
        if args.action == 'preflight':
            print(json.dumps({'status': 'V25_PREFLIGHT_OK', 'source': info, 'source_signature': fp,
                              'branches': [{'id': b['id'], 'concepts': len(b['concepts']),
                                            'reviewed_bridges': len(b['bridges'])} for b in specs],
                              'wiki_text_scanned': False, 'writes_performed': False},
                             ensure_ascii=False, indent=2)); return 0
        if args.catalogue_db.resolve() == args.source_db.resolve():
            raise Refusal('La base de catalogue ne doit jamais etre la base source Wikipedia')
        if args.action == 'export-batch' and not args.catalogue_db.is_file():
            raise Refusal('Catalogue v25 non encore construit')
        db = open_catalog(args.catalogue_db)
        try:
            bind_source(db, fp, info)
            if args.action == 'export-batch':
                if not args.export_branch_id:
                    raise Refusal('export-batch exige --export-branch-id')
                result = export_semantic_batch(db, args.output_dir, args.export_branch_id,
                                               args.after_page_id, args.batch_limit)
                print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
            if args.action == 'extend':
                if not args.extend_branch_id or args.new_max_members is None or args.new_max_tasks is None:
                    raise Refusal('extend exige --extend-branch-id --new-max-members --new-max-tasks')
                result = expand_limits(db, args.extend_branch_id, args.new_max_members, args.new_max_tasks)
                print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
            seeded = [seed_branch(src, db, b) for b in specs] if args.action == 'run' else []
            if args.action == 'run':
                pending = {r[0] for r in db.execute("SELECT DISTINCT branch_id FROM category_tasks WHERE state='PENDING'")}
                missing = pending - {b['id'] for b in specs}
                if missing:
                    raise Refusal('Branches avec travaux en cours: fournir aussi --branch pour ' + ', '.join(sorted(missing)))
            last = None
            total = 0
            if args.action == 'run':
                by_id = {b['id']: b for b in specs}
                for i in range(args.max_batches):
                    last = work_one_batch(src, db, by_id, args.batch_size)
                    if last is None:
                        break
                    total += last['processed']
                    if i == 0 or (i + 1) % 10 == 0:
                        print(json.dumps({'event': 'V25_BATCH_PROGRESS', 'batch': i + 1, **last},
                                         ensure_ascii=False), flush=True)
            _, final_source_sig = source_fingerprint(src, args.source_db)
            if final_source_sig != fp:
                raise Refusal('La source Wikipedia a change pendant la session; sortie non declaree fiable')
            result = snapshot(db, args.catalogue_db, args.output_dir, args.sample_limit)
            result.update({'status': 'V25_RUN_OK' if args.action == 'run' else 'V25_REPORT_OK',
                           'catalogue_db': str(args.catalogue_db), 'batches_requested': args.max_batches,
                           'members_examined_this_session': total, 'seeded': seeded,
                           'canonical_admissions': 0, 'publication_authorized': False})
            print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
        finally:
            db.close()
    finally:
        src.close()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (Refusal, sqlite3.Error, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as e:
        print(json.dumps({'status': 'V25_REFUS', 'reason': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)
