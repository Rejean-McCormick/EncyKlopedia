#!/usr/bin/env python3
"""Production privee EncyKlopedia v27 : packs integraux -> deltas IA -> Kristal cumulatif.

Consomme le catalogue derive v25 et l'index d'offsets XML v21, tous deux en lecture seule.
Les donnees produites sont des CANDIDATS IA cumules; aucune admission canonique.
Python >=3.11, bibliotheque standard, aucun acces reseau.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

PACK_FORMAT = 'encyklopedia.wikipedia-fulltext-pack.v27/1'
DELTA_FORMAT = 'encyklopedia.kristal-ai-delta.v27/1'
WORK_FORMAT = 'encyklopedia.kristal-work-queue.v27/1'
STORE_FORMAT = 'encyklopedia.private-cumulative-kristal.v27/1'
V21_FORMAT = 'koa.wikipedia-direct-xml-offsets/1.0'
CAT_FORMAT = 'encyklopedia.global-article-catalogue.v25/1'
DEFAULT_CATALOGUE = Path(r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite')
DEFAULT_XML = Path(r'D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml')
DEFAULT_INDEX = Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.sqlite')
DEFAULT_WORK = Path(r'D:\EncyKlopedia\30_working\production_kristals_v27')
REF_RE = re.compile(r'^(enwiki:[1-9]\d*|unesco:concept[1-9]\d*|wikidata:Q[1-9]\d*)$')
PROP_RE = re.compile(r'^[a-z][a-z0-9_]{1,79}$')
CONCEPT_RE = re.compile(r'^concept[1-9]\d*$')
PACK_ID_RE = re.compile(r'^PACK_V27_(\d{6,})$')


class Refusal(ValueError):
    pass


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def encoded(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def hash_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def ro_sql(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise Refusal('Base source introuvable ou lien symbolique: ' + str(path))
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=60)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    db.execute('PRAGMA busy_timeout=60000')
    return db


def value(db, table, key):
    column = {'meta': 'key', 'v21_meta': 'name'}[table]
    r = db.execute(f'SELECT value FROM {table} WHERE {column}=?', (key,)).fetchone()
    return r[0] if r else None


def xml_signature(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise Refusal('Dump XML decompresse absent: ' + str(path))
    st = path.stat()
    if st.st_size < 128:
        raise Refusal('XML incomplet ou vide')
    h = hashlib.sha256()
    with path.open('rb') as f:
        h.update(f.read(1024 * 1024))
        f.seek(max(0, st.st_size - 1024 * 1024))
        h.update(f.read(1024 * 1024))
    return {'path': str(path.resolve()), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns,
            'head_tail_sha256': h.hexdigest(), 'hash_scope': 'FIRST_AND_LAST_MIB_ONLY'}


def validated_sources(catalogue, index, xml):
    """Do not need to read or reindex the SQL dump or scan the XML."""
    catalog = ro_sql(catalogue)
    ix = ro_sql(index)
    try:
        catalog.execute('BEGIN')
        ix.execute('BEGIN')
        cat_schema = value(catalog, 'meta', 'schema')
        if cat_schema != CAT_FORMAT:
            raise Refusal('Catalogue v25 incompatible: ' + str(cat_schema))
        sequence = value(catalog, 'meta', 'sequence')
        origin = value(catalog, 'meta', 'source_sha')
        if not origin or sequence is None:
            raise Refusal('Catalogue sans origine ou sequence')
        if not {'articles', 'assignments'} <= {r[0] for r in catalog.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
            raise Refusal('Tables articles / assignments absentes du catalogue')
        raw_ixformat = value(ix, 'v21_meta', 'format')
        if raw_ixformat is None or json.loads(raw_ixformat) != V21_FORMAT:
            raise Refusal('Index XML v21 incompatible')
        if json.loads(value(ix, 'v21_meta', 'complete') or 'false') is not True:
            raise Refusal('Index v21 incomplet, aucun nouveau parcours XML lance')
        sig = xml_signature(xml)
        if json.loads(value(ix, 'v21_meta', 'source_signature') or 'null') != sig:
            raise Refusal('Le fichier XML ne correspond pas a l index v21')
        return catalog, ix, {'catalog_source_sha': origin, 'catalog_sequence': int(sequence),
                             'xml_signature': sig}
    except BaseException:
        catalog.close()
        ix.close()
        raise


def state_db(path, schema, init_sql):
    path = Path(path)
    if path.exists():
        if not path.is_file() or path.is_symlink():
            raise Refusal('Base de travail non reguliere: ' + str(path))
        with closing(ro_sql(path)) as r:
            try:
                old = value(r, 'meta', 'schema')
            except sqlite3.DatabaseError as e:
                raise Refusal('Base preexistante etrangere') from e
            if old != schema:
                raise Refusal('Base preexistante avec un autre schema: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=120)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA busy_timeout=120000')
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript(init_sql)
    with db:
        db.execute('INSERT OR IGNORE INTO meta(key,value) VALUES(?,?)', ('schema', schema))
    return db


QUEUE_SQL = '''
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS queue(
 page_id INTEGER PRIMARY KEY,title TEXT NOT NULL,qid TEXT,catalog_revision TEXT,
 score INTEGER NOT NULL, state TEXT NOT NULL DEFAULT 'PENDING',pack_id TEXT,
 xml_revision TEXT, text_sha256 TEXT,error TEXT
);
CREATE INDEX IF NOT EXISTS idx_queue_pending ON queue(state,score DESC,page_id);
CREATE TABLE IF NOT EXISTS packs(
 pack_id TEXT PRIMARY KEY,zip_path TEXT NOT NULL,sha256 TEXT NOT NULL,
 article_count INTEGER NOT NULL,created_utc TEXT NOT NULL
);
'''


STORE_SQL = '''
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS delta_imports(
 delta_sha256 TEXT PRIMARY KEY,pack_sha256 TEXT NOT NULL,
 pack_id TEXT NOT NULL,imported_utc TEXT NOT NULL,payload_json TEXT NOT NULL,
 claims_in_delta INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS claims(
 claim_key TEXT PRIMARY KEY,subject_ref TEXT NOT NULL,predicate TEXT NOT NULL,
 object_type TEXT NOT NULL,object_value TEXT NOT NULL,statement_en TEXT NOT NULL,
 confidence TEXT NOT NULL,first_seen_utc TEXT NOT NULL,source_status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_claim_pred ON claims(subject_ref,predicate);
CREATE TABLE IF NOT EXISTS citations(
 claim_key TEXT NOT NULL,page_id INTEGER NOT NULL,revision_id TEXT NOT NULL,
 pack_sha256 TEXT NOT NULL,section_hint TEXT NOT NULL,source_quote TEXT NOT NULL,
 wikitext_sha256 TEXT NOT NULL, PRIMARY KEY(claim_key,page_id,revision_id,pack_sha256),
 FOREIGN KEY(claim_key) REFERENCES claims(claim_key)
);
CREATE TABLE IF NOT EXISTS claim_concepts(
 claim_key TEXT NOT NULL,concept_id TEXT NOT NULL,routing TEXT NOT NULL,
 PRIMARY KEY(claim_key,concept_id),FOREIGN KEY(claim_key) REFERENCES claims(claim_key)
);
CREATE TABLE IF NOT EXISTS claim_branches(
 claim_key TEXT NOT NULL,branch_id TEXT NOT NULL,
 PRIMARY KEY(claim_key,branch_id),FOREIGN KEY(claim_key) REFERENCES claims(claim_key)
);
CREATE TABLE IF NOT EXISTS article_visits(
 page_id INTEGER NOT NULL,revision_id TEXT NOT NULL,pack_sha256 TEXT NOT NULL,
 delta_sha256 TEXT NOT NULL,extracted_claims INTEGER NOT NULL,
 coverage TEXT NOT NULL,PRIMARY KEY(page_id,revision_id,delta_sha256)
);
CREATE TABLE IF NOT EXISTS text_variants(
 claim_key TEXT NOT NULL,statement_en TEXT NOT NULL,delta_sha256 TEXT NOT NULL,
 PRIMARY KEY(claim_key,statement_en),FOREIGN KEY(claim_key) REFERENCES claims(claim_key)
);
'''


def bind_work(queue, source):
    expected = {'catalog_source_sha': source['catalog_source_sha'],
                'xml_signature': source['xml_signature'], 'selection_scope': 'all-catalogue-branches'}
    with queue:
        for k, v in expected.items():
            serialized = json.dumps(v, ensure_ascii=False, sort_keys=True)
            old = value(queue, 'meta', k)
            if old is not None and old != serialized:
                raise Refusal('Source/portee modifiee depuis la construction des packs: ' + k)
            queue.execute('INSERT OR IGNORE INTO meta(key,value) VALUES(?,?)', (k, serialized))
        queue.execute('INSERT OR IGNORE INTO meta(key,value) VALUES(?,?)', ('pack_sequence', '0'))


def synchronize(catalogue, queue, sequence, chunk=2000):
    """Rescan the *small derived catalogue* once per new sequence, never the XML."""
    if int(value(queue, 'meta', 'catalog_sequence_synced') or -1) == sequence:
        return {'synchronized': True, 'added_this_sync': 0}
    target = value(queue, 'meta', 'sync_target')
    if target != str(sequence):
        with queue:
            queue.execute("INSERT INTO meta(key,value) VALUES('sync_target',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(sequence),))
            queue.execute("INSERT INTO meta(key,value) VALUES('sync_cursor','0') ON CONFLICT(key) DO UPDATE SET value='0'")
    cursor = int(value(queue, 'meta', 'sync_cursor') or '0')
    seen = 0
    while True:
        rows = list(catalogue.execute('''SELECT a.page_id,a.title,a.qid,a.revision_id,
              COALESCE((SELECT MAX(s.score) FROM assignments s WHERE s.wiki=a.wiki AND s.page_id=a.page_id),0) score
              FROM articles a WHERE a.wiki='enwiki' AND a.page_id>?
              AND EXISTS(SELECT 1 FROM assignments s WHERE s.wiki='enwiki' AND s.page_id=a.page_id)
              ORDER BY a.page_id LIMIT ?''', (cursor, chunk)))
        if not rows:
            with queue:
                queue.execute("INSERT INTO meta(key,value) VALUES('catalog_sequence_synced',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(sequence),))
                queue.execute("DELETE FROM meta WHERE key IN ('sync_cursor','sync_target')")
            return {'synchronized': True, 'added_this_sync': seen}
        with queue:
            queue.executemany('''INSERT INTO queue(page_id,title,qid,catalog_revision,score) VALUES(?,?,?,?,?)
              ON CONFLICT(page_id) DO UPDATE SET
              score=MAX(queue.score,excluded.score),
              title=excluded.title,qid=COALESCE(queue.qid,excluded.qid),
              catalog_revision=excluded.catalog_revision''',
              [(int(r['page_id']), r['title'], r['qid'], str(r['revision_id'] or ''), int(r['score'])) for r in rows])
            cursor = int(rows[-1]['page_id'])
            queue.execute("INSERT INTO meta(key,value) VALUES('sync_cursor',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(cursor),))
        seen += len(rows)
        if seen % 50000 < chunk:
            print(json.dumps({'event': 'V27_CATALOGUE_SYNC', 'articles_examined': seen,
                              'last_page_id': cursor}, ensure_ascii=False), flush=True)


def page_from_index(ix, xml_handle, page_id):
    row = ix.execute('SELECT page_id,byte_offset,byte_length,namespace,title,revision_id,is_redirect '
                     'FROM pages WHERE page_id=?', (page_id,)).fetchone()
    if row is None or int(row['namespace']) != 0 or int(row['is_redirect']):
        raise Refusal('Page XML absente, redirigee ou hors espace principal: ' + str(page_id))
    offset, length = int(row['byte_offset']), int(row['byte_length'])
    if offset < 0 or length <= 0:
        raise Refusal('Index v21 invalide pour ' + str(page_id))
    xml_handle.seek(offset)
    raw = xml_handle.read(length)
    if len(raw) != length or not raw.startswith(b'<page>') or not raw.endswith(b'</page>'):
        raise Refusal('Octets XML/offsets incorrects: ' + str(page_id))
    try:
        root = ET.fromstring(raw)
        pid = int(root.findtext('./id') or '0')
        ns = int(root.findtext('./ns') or '-1')
        title = root.findtext('./title') or ''
        revision = root.find('./revision')
        rev = revision.findtext('./id') if revision is not None else None
        wikitext = revision.findtext('./text') if revision is not None else None
    except (ValueError, ET.ParseError) as e:
        raise Refusal('Article XML mal forme: ' + str(page_id)) from e
    if (pid != page_id or ns != 0 or title != row['title'] or str(rev or '') != str(row['revision_id'])
            or root.find('./redirect') is not None or not wikitext or not wikitext.strip()):
        raise Refusal('Index v21 et page XML incoherents: ' + str(page_id))
    return wikitext.encode('utf-8'), str(rev), title


def all_assignments(cat, page_id):
    return [dict(r) for r in cat.execute('SELECT branch_id,vocabulary,concept_id,score,evidence_kind,evidence_origin '
                                        "FROM assignments WHERE wiki='enwiki' AND page_id=? "
                                        'ORDER BY score DESC,branch_id,concept_id', (page_id,))]


def pack_articles(queue, cat, ix, xml, max_articles, target_words, target_bytes):
    """Priority keyset scan; skip any number of missing pages without user multipass."""
    entries = []
    total_words = total_bytes = 0
    last_score = last_pid = None
    done = False
    with Path(xml).open('rb') as inp:
        while not done and len(entries) < max_articles:
            if last_score is None:
                rows = queue.execute("SELECT * FROM queue WHERE state='PENDING' "
                                     "ORDER BY score DESC,page_id LIMIT 128").fetchall()
            else:
                rows = queue.execute("SELECT * FROM queue WHERE state='PENDING' "
                                     "AND (score<? OR (score=? AND page_id>?)) "
                                     "ORDER BY score DESC,page_id LIMIT 128",
                                     (last_score,last_score,last_pid)).fetchall()
            if not rows:
                break
            for candidate in rows:
                last_score, last_pid = int(candidate['score']), int(candidate['page_id'])
                pid = last_pid
                try:
                    raw, revision, title = page_from_index(ix, inp, pid)
                except Refusal as e:
                    with queue:
                        queue.execute("UPDATE queue SET state='FAILED',error=? WHERE page_id=? AND state='PENDING'",
                                      (str(e), pid))
                    continue
                word_count = len(raw.decode('utf-8').split())
                if entries and (len(entries) >= max_articles or total_words + word_count > target_words or
                                total_bytes + len(raw) > target_bytes):
                    done = True
                    break
                assigns = all_assignments(cat, pid)
                if not assigns:
                    raise Refusal('Article sans rattachement au catalogue : ' + str(pid))
                entries.append({'page_id': pid, 'text': raw, 'revision_id': revision, 'xml_title': title,
                                'catalog_title': candidate['title'], 'catalog_revision': candidate['catalog_revision'],
                                'qid': candidate['qid'], 'assignments': assigns,
                                'word_count': word_count, 'score': candidate['score']})
                total_words += word_count
                total_bytes += len(raw)
                if len(entries) >= max_articles:
                    done = True
                    break
    return entries


def make_pack(entries, pack_id, source, work):
    files = {}
    article_manifest = []
    for item in entries:
        rel = f"articles/enwiki-{item['page_id']}.wikitext.txt"
        files[rel] = item['text']  # full source, never truncated
        article_manifest.append({
            'article_id': 'enwiki:' + str(item['page_id']), 'page_id': item['page_id'],
            'title': item['xml_title'], 'catalog_title': item['catalog_title'], 'qid': item['qid'],
            'revision_id': item['revision_id'], 'catalog_revision_id': item['catalog_revision'],
            'revision_mismatch_with_catalogue': item['revision_id'] != item['catalog_revision'],
            'text_path': rel, 'text_sha256': digest(item['text']), 'text_bytes': len(item['text']),
            'approx_words': item['word_count'], 'classifications_are_candidates': True,
            'assignments': item['assignments'],
            'source_revision_url': 'https://en.wikipedia.org/w/index.php?oldid=' + item['revision_id']})
    manifest = {'format': PACK_FORMAT, 'pack_id': pack_id, 'created_utc': utc(),
                'articles_count': len(article_manifest), 'source': source,
                'articles': article_manifest, 'raw_article_texts_complete': True,
                'overlarge_single_article_allowed_without_truncation': True,
                'semantic_analysis_may_be_selective': True, 'status': 'PRIVATE_RESEARCH',
                'wikipedia_license_note': 'Attribution and share-alike may apply; verify rights before publication.',
                'canonical_admissions': 0, 'publication_authorized': False}
    files['MANIFEST_PACK_V27.json'] = encoded(manifest)
    model = {'format': DELTA_FORMAT, 'pack_id': pack_id, 'pack_sha256': 'REMPLACER_PAR_SHA256_DU_ZIP',
             'producer': 'GPT-6 / ChatGPT', 'coverage_note': 'Analyse selective; omission de connaissances permise',
             'claims': [{'source_page_id': article_manifest[0]['page_id'],
                         'source_revision_id': article_manifest[0]['revision_id'],
                         'subject_ref': article_manifest[0]['article_id'],
                         'predicate': 'describes', 'object': {'type': 'text', 'value': 'REMPLACER'},
                         'statement_en': 'REMPLACER PAR UN FAIT SPECIFIQUE VERIFIABLE',
                         'unesco_concepts': [], 'source_locator': 'Introduction ou section du texte',
                         'source_quote': '', 'confidence': 'medium'}]}
    files['MODELE_DELTA_KRISTAL_V27.json'] = encoded(model)
    files['INSTRUCTIONS_CHATGPT.md'] = (f'''# Pack {pack_id} — EncyKlopedia v27\n\n'''
        '''Lis les articles anglais COMPLETS dans `articles/`. Ils contiennent du wikitext, references incluses.\n'''
        '''Choisis les connaissances encyclopediques pertinentes. Il n'est PAS necessaire de tout extraire.\n'''
        '''Genere un fichier JSON conforme au modele `MODELE_DELTA_KRISTAL_V27.json`.\n'''
        '''Remplace `pack_sha256` par l'empreinte SHA-256 du ZIP indiquee par le lanceur local.\n'''
        '''Ancre chaque connaissance au vrai page_id / revision_id de l'article du manifeste.\n'''
        '''`subject_ref` est un identifiant `enwiki:123`, `unesco:concept9` ou `wikidata:Q42`.\n'''
        '''`predicate` est un nom de relation en anglais et en snake_case (non canonique KP).\n'''
        '''`object` est `{"type":"text|entity|number|date|boolean","value":"..."}`.\n'''
        '''Indique la section dans `source_locator`, une citation courte optionnelle dans `source_quote`.\n'''
        '''Les references Wikipedia sont un CONTEXTE, pas une verification independante.\n'''
        '''Aucun KQ/KP/KA/KS canonique, aucune publication, aucune obligation d'exhaustivite.\n''').encode('utf-8')
    target = Path(work) / 'packs' / (pack_id + '.zip')
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise Refusal('Pack deja present: ' + str(target))
    fd, tmpname = tempfile.mkstemp(prefix='.v27_pack_', suffix='.partial', dir=target.parent)
    os.close(fd)
    tmp = Path(tmpname)
    try:
        with zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                             allowZip64=True) as z:
            for name, content in sorted(files.items()):
                z.writestr(name, content)
        verify_pack(tmp)
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()
    return target, digest(files['MANIFEST_PACK_V27.json'])


def verify_pack(path):
    if not Path(path).is_file():
        raise Refusal('Pack absent: ' + str(path))
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or 'MANIFEST_PACK_V27.json' not in names:
            raise Refusal('ZIP de pack duplique ou sans manifeste')
        m = json.loads(z.read('MANIFEST_PACK_V27.json'))
        if (m.get('format') != PACK_FORMAT or m.get('raw_article_texts_complete') is not True or
                m.get('canonical_admissions') != 0 or m.get('publication_authorized') is not False or
                not PACK_ID_RE.fullmatch(m.get('pack_id', ''))):
            raise Refusal('Manifeste de pack incompatible')
        allowed = {'MANIFEST_PACK_V27.json','MODELE_DELTA_KRISTAL_V27.json','INSTRUCTIONS_CHATGPT.md'}
        ids = set()
        for a in m.get('articles', []):
            pid = a['page_id']
            if not isinstance(pid, int) or pid <= 0 or pid in ids:
                raise Refusal('ID article absent/duplique')
            ids.add(pid)
            rel = f'articles/enwiki-{pid}.wikitext.txt'
            if a['text_path'] != rel or rel not in names:
                raise Refusal('Nom article ZIP non conforme')
            raw = z.read(rel)
            if len(raw) != a['text_bytes'] or digest(raw) != a['text_sha256'] or not raw.strip():
                raise Refusal('Article manquant/tronque/alteré: ' + str(pid))
            allowed.add(rel)
        if (len(ids) != m.get('articles_count') or not ids or set(names) != allowed):
            raise Refusal('Membres du ZIP inattendus')
        return m


def recover_orphans(queue, work, source):
    """Crash between ZIP creation and SQLite commit: recover by verified ZIP, never duplicate."""
    folder = Path(work) / 'packs'
    if not folder.is_dir():
        return 0
    recovered = 0
    for path in sorted(folder.glob('PACK_V27_*.zip')):
        if queue.execute('SELECT 1 FROM packs WHERE pack_id=?', (path.stem,)).fetchone():
            continue
        m = verify_pack(path)
        if m['pack_id'] != path.stem or m['source']['xml_signature'] != source['xml_signature'] or m['source']['catalog_source_sha'] != source['catalog_source_sha']:
            raise Refusal('Pack orphelin d une autre source : ' + str(path))
        members = m['articles']
        for a in members:
            r = queue.execute('SELECT state,pack_id FROM queue WHERE page_id=?', (a['page_id'],)).fetchone()
            if r is None or r['state'] not in ('PENDING', 'PACKED') or (r['state']=='PACKED' and r['pack_id']!=path.stem):
                raise Refusal('Pack orphelin incoherent avec la file: ' + str(path))
        with queue:
            queue.execute('INSERT INTO packs VALUES(?,?,?,?,?)',
                          (path.stem, str(path), hash_file(path), len(members), m['created_utc']))
            for a in members:
                queue.execute("UPDATE queue SET state='PACKED',pack_id=?,xml_revision=?,text_sha256=?,error=NULL WHERE page_id=?",
                              (path.stem, a['revision_id'], a['text_sha256'], a['page_id']))
            seq = int(PACK_ID_RE.fullmatch(path.stem).group(1))
            queue.execute("UPDATE meta SET value=? WHERE key='pack_sequence' AND CAST(value AS INTEGER)<?",
                          (str(seq), seq))
        recovered += 1
    return recovered


def check_private_work(work, sources=()):
    target=Path(work).resolve()
    for ancestor in (target, *target.parents):
        if (ancestor / '.git').exists():
            raise Refusal('Dossier de travail sous Git interdit: ' + str(target))
    for src in sources:
        resolved=Path(src).resolve()
        if target == resolved or target in resolved.parents:
            raise Refusal('Dossier de travail recouvre un fichier source: ' + str(src))
    return target


def produce(args):
    if not (1 <= args.max_articles <= 100 and 100 <= args.target_words <= 1_000_000
            and 65536 <= args.target_bytes <= 200_000_000 and 1 <= args.max_packs <= 1000):
        raise Refusal('Bornes de production invalides')
    check_private_work(args.work, (args.catalogue,args.index,args.xml))
    catalogue, ix, source = validated_sources(args.catalogue, args.index, args.xml)
    try:
        queue = state_db(args.work / 'FILE_PACKS_V27.sqlite', WORK_FORMAT, QUEUE_SQL)
        try:
            bind_work(queue, source)
            sync = synchronize(catalogue, queue, source['catalog_sequence'])
            recovered = recover_orphans(queue, args.work, source)
            outputs = []
            for _ in range(args.max_packs):
                entries = pack_articles(queue, catalogue, ix, args.xml, args.max_articles,
                                        args.target_words, args.target_bytes)
                if not entries:
                    break
                seq = int(value(queue,'meta','pack_sequence') or 0) + 1
                pack_id = 'PACK_V27_' + f'{seq:06d}'
                file, _ = make_pack(entries, pack_id, source, args.work)
                h = hash_file(file)
                with queue:
                    queue.execute('INSERT INTO packs VALUES(?,?,?,?,?)', (pack_id, str(file), h, len(entries), utc()))
                    for a in entries:
                        queue.execute("UPDATE queue SET state='PACKED',pack_id=?,xml_revision=?,text_sha256=? WHERE page_id=? AND state='PENDING'",
                                      (pack_id,a['revision_id'],digest(a['text']),a['page_id']))
                    queue.execute("UPDATE meta SET value=? WHERE key='pack_sequence'", (str(seq),))
                outputs.append({'pack_id': pack_id, 'path': str(file), 'sha256': h,
                                'articles': len(entries), 'words': sum(x['word_count'] for x in entries),
                                'uncompressed_text_bytes': sum(len(x['text']) for x in entries)})
                print(json.dumps({'event':'V27_PACK_READY', **outputs[-1]},ensure_ascii=False),flush=True)
            stats = {r['state']: r['n'] for r in queue.execute('SELECT state,count(*) n FROM queue GROUP BY state')}
            return {'status': 'V27_PACKS_READY', 'source_catalogue_sequence': source['catalog_sequence'],
                    'packets_created_this_run': len(outputs), 'packs': outputs,
                    'queue': stats, 'recoveries': recovered, 'catalogue_sync': sync,
                    'source_xml_read_only': True,'catalogue_read_only': True,
                    'source_articles_untruncated': True,'canonical_admissions':0}
        finally:
            queue.close()
    finally:
        catalogue.close()
        ix.close()


def claim_key(claim):
    norm = {'subject_ref': claim['subject_ref'], 'predicate': claim['predicate'],
            'object_type': claim['object']['type'],
            'object_value': ' '.join(claim['object']['value'].split())}
    return 'CAND-KA-' + digest(encoded(norm))[:32]


def validate_delta(pack_path, delta_path):
    manifest = verify_pack(pack_path)
    raw = Path(delta_path).read_bytes()
    if len(raw) > 50 * 1024 * 1024:
        raise Refusal('Delta excessivement volumineux (>50 MiB); scinder le retour IA')
    data = json.loads(raw.decode('utf-8-sig'))
    pack_sha = hash_file(pack_path)
    if data.get('format') != DELTA_FORMAT or data.get('pack_id') != manifest['pack_id'] or data.get('pack_sha256') != pack_sha:
        raise Refusal('Le delta ne correspond pas au ZIP source exact')
    if data.get('canonical_admissions', 0) not in (0, None) or data.get('publication_authorized', False) not in (False,None):
        raise Refusal('Delta pretendument canonique/public refuse')
    claims = data.get('claims')
    if not isinstance(claims, list) or len(claims) > 20000:
        raise Refusal('Liste des faits invalide ou anormalement grande')
    allowed = {a['page_id']: a for a in manifest['articles']}
    valid = []
    for i, c in enumerate(claims):
        if not isinstance(c,dict):
            raise Refusal('Fait non JSON: ' + str(i))
        pid = c.get('source_page_id')
        if type(pid) is not int or pid not in allowed or c.get('source_revision_id') != allowed[pid]['revision_id']:
            raise Refusal('Reference article/revision absente du pack: ' + str(i))
        if not isinstance(c.get('subject_ref'), str) or not REF_RE.fullmatch(c['subject_ref']):
            raise Refusal('subject_ref invalide: ' + str(i))
        if not isinstance(c.get('predicate'), str) or not PROP_RE.fullmatch(c['predicate']):
            raise Refusal('predicate invalide: ' + str(i))
        obj = c.get('object')
        if not isinstance(obj, dict) or obj.get('type') not in ('text','entity','number','date','boolean') or not isinstance(obj.get('value'),str) or not 1 <= len(obj['value'].strip()) <= 2000:
            raise Refusal('Objet invalide: ' + str(i))
        if obj['value'].strip().upper().startswith(('REMPLACER', 'REPLACE_', 'TODO')) or c.get('statement_en','').strip().upper().startswith(('REMPLACER', 'REPLACE_', 'TODO')):
            raise Refusal('Modele non rempli / valeur fictive: ' + str(i))
        if obj['type'] == 'entity' and not REF_RE.fullmatch(obj['value']):
            raise Refusal('Objet entite sans identifiant reconnu: ' + str(i))
        if not isinstance(c.get('statement_en'),str) or not 15 <= len(c['statement_en'].strip()) <= 5000:
            raise Refusal('Statement anglais invalide: ' + str(i))
        if c.get('confidence') not in ('high','medium','low'):
            raise Refusal('Confiance invalide: ' + str(i))
        if not isinstance(c.get('source_locator'),str) or not 1 <= len(c['source_locator'].strip()) <= 300:
            raise Refusal('Localisateur source absent: ' + str(i))
        quote = c.get('source_quote','')
        if not isinstance(quote,str) or len(quote)>500:
            raise Refusal('Source quote trop longue: ' + str(i))
        concepts = c.get('unesco_concepts', [])
        if not isinstance(concepts,list) or len(concepts)>40 or any(not isinstance(x,str) or not CONCEPT_RE.fullmatch(x) for x in concepts):
            raise Refusal('Concept UNESCO invalide: ' + str(i))
        valid.append(c)
    return manifest, data, raw, pack_sha, valid


def import_delta(args):
    if not args.pack or not args.delta:
        raise Refusal('Import exige --pack et --delta')
    manifest, data, raw, pack_sha, claims = validate_delta(args.pack, args.delta)
    work = args.work
    check_private_work(work)
    work.mkdir(parents=True, exist_ok=True)
    store = state_db(work/'KRISTAL_CUMULATIF_PRIVE_V27.sqlite', STORE_FORMAT, STORE_SQL)
    try:
        delta_sha = digest(raw)
        existing = store.execute('SELECT 1 FROM delta_imports WHERE delta_sha256=?', (delta_sha,)).fetchone()
        if existing:
            return {'status':'V27_DELTA_DEJA_CUMULE', 'delta_sha256':delta_sha,
                    'canonical_admissions':0,'new_claims':0}
        by_id = {a['page_id']: a for a in manifest['articles']}
        new_claims = new_citations = new_visits = variants = 0
        counts = {}
        with store:
            for c in claims:
                pid=c['source_page_id']; a=by_id[pid]
                counts[pid] = counts.get(pid,0) + 1
                key = claim_key(c)
                old = store.execute('SELECT statement_en FROM claims WHERE claim_key=?', (key,)).fetchone()
                if old is None:
                    store.execute('''INSERT INTO claims VALUES(?,?,?,?,?,?,?,?,?)''',
                                  (key,c['subject_ref'],c['predicate'],c['object']['type'],
                                   c['object']['value'],c['statement_en'].strip(),c['confidence'],
                                   utc(),'AI_REVIEWED_CANDIDATE_UNVERIFIED'))
                    new_claims += 1
                if old is not None and old['statement_en'] != c['statement_en'].strip():
                    variants += 1
                    store.execute('INSERT OR IGNORE INTO text_variants VALUES(?,?,?)',
                                  (key,c['statement_en'].strip(),delta_sha))
                before=store.total_changes
                store.execute('INSERT OR IGNORE INTO citations VALUES(?,?,?,?,?,?,?)',
                              (key,pid,a['revision_id'],pack_sha,c['source_locator'].strip(),
                               c.get('source_quote',''),a['text_sha256']))
                new_citations += store.total_changes-before
                for cid in set(c.get('unesco_concepts', [])):
                    in_catalogue = any(x['concept_id']==cid for x in a['assignments'])
                    routing = 'CATALOGUE_CANDIDATE' if in_catalogue else 'AI_SUGGESTED_UNVERIFIED'
                    store.execute('INSERT OR IGNORE INTO claim_concepts VALUES(?,?,?)', (key,cid,routing))
                for bid in {x['branch_id'] for x in a['assignments']}:
                    store.execute('INSERT OR IGNORE INTO claim_branches VALUES(?,?)', (key,bid))
            for pid, count in counts.items():
                before=store.total_changes
                store.execute('INSERT OR IGNORE INTO article_visits VALUES(?,?,?,?,?,?)',
                              (pid,by_id[pid]['revision_id'],pack_sha,delta_sha,count,'PARTIAL_OK_NOT_EXHAUSTIVE'))
                new_visits += store.total_changes-before
            store.execute('INSERT INTO delta_imports VALUES(?,?,?,?,?,?)',
                          (delta_sha,pack_sha,manifest['pack_id'],utc(),raw.decode('utf-8-sig'),len(claims)))
        return {'status': 'V27_KRISTAL_PRIVE_CUMULE', 'pack_id':manifest['pack_id'],
                'delta_sha256':delta_sha,'claims_in_delta':len(claims),'new_unique_claims':new_claims,
                'new_citations':new_citations,'article_visits':new_visits,
                'alternate_formulations_detected':variants,'canonical_admissions':0,
                'publication_authorized':False,'store':str(work/'KRISTAL_CUMULATIF_PRIVE_V27.sqlite')}
    finally:
        store.close()


def report(work):
    queue_path = work / 'FILE_PACKS_V27.sqlite'
    store_path = work / 'KRISTAL_CUMULATIF_PRIVE_V27.sqlite'
    info={'status':'V27_STATUS_OK','work':str(work),'canonical_admissions':0,
          'publication_authorized':False,'articles_untruncated':True,
          'knowledge_coverage_may_be_partial':True}
    if queue_path.exists():
        with closing(ro_sql(queue_path)) as q:
            info['queue']={r['state']:r['n'] for r in q.execute('SELECT state,count(*) n FROM queue GROUP BY state')}
            info['packs_created']=q.execute('SELECT count(*) FROM packs').fetchone()[0]
            info['catalog_sequence_synced']=value(q,'meta','catalog_sequence_synced')
    else:
        info['queue']='NOT_STARTED'
    if store_path.exists():
        with closing(ro_sql(store_path)) as s:
            for tbl,name in [('claims','unique_claims'),('citations','citations'),('delta_imports','deltas_imported'),
                             ('claim_branches','branch_links'),('article_visits','article_visits')]:
                info[name]=s.execute('SELECT count(*) FROM '+tbl).fetchone()[0]
            info['potential_multiple_values_same_subject_predicate']=s.execute(
                'SELECT count(*) FROM (SELECT 1 FROM claims GROUP BY subject_ref,predicate HAVING count(*)>1)').fetchone()[0]
    else:
        info['unique_claims']=0
        info['deltas_imported']=0
    return info


def export_store(work):
    check_private_work(work)
    path = work/'KRISTAL_CUMULATIF_PRIVE_V27.sqlite'
    if not path.is_file():
        raise Refusal('Kristal de travail non initialise: importer un delta')
    with closing(ro_sql(path)) as db:
        count = db.execute('SELECT count(*) FROM delta_imports').fetchone()[0]
        final = work/'exports'/f'SNAPSHOT_KRISTAL_V27_{count:08d}'
        if final.exists():
            verify_export(final)
            return {'status':'V27_EXPORT_DEJA_PRESENT','directory':str(final),
                    'claims':db.execute('SELECT count(*) FROM claims').fetchone()[0]}
        final.parent.mkdir(parents=True,exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix='.export_v27_',dir=final.parent))
        try:
            specs = {
                'CLAIMS.jsonl': '''SELECT c.claim_key,c.subject_ref,c.predicate,c.object_type,c.object_value,
                                     c.statement_en,c.confidence,c.source_status FROM claims c ORDER BY claim_key''',
                'CITATIONS.jsonl': '''SELECT claim_key,page_id,revision_id,pack_sha256,section_hint,source_quote,wikitext_sha256
                                      FROM citations ORDER BY claim_key,page_id,revision_id''',
                'CONCEPTS.jsonl': '''SELECT claim_key,concept_id,routing FROM claim_concepts ORDER BY claim_key,concept_id''',
                'BRANCHES.jsonl': '''SELECT claim_key,branch_id FROM claim_branches ORDER BY claim_key,branch_id''',
            }
            sha_files={}
            for name, query in specs.items():
                with (tmp/name).open('wb') as f:
                    for row in db.execute(query):
                        f.write((json.dumps(dict(row),ensure_ascii=False,sort_keys=True)+'\n').encode('utf-8'))
                sha_files[name] = hash_file(tmp/name)
            info={'format':STORE_FORMAT,'created_utc':utc(), 'imported_deltas':count,
                  'unique_claims':db.execute('SELECT count(*) FROM claims').fetchone()[0],
                  'files_sha256':sha_files, 'canonical_admissions':0,'publication_authorized':False,
                  'note':'Candidats IA cumules, non approuves par le Framework canonique'}
            (tmp/'MANIFEST_EXPORT_V27.json').write_bytes(encoded(info))
            os.replace(tmp,final)
        finally:
            if tmp.exists():
                import shutil
                shutil.rmtree(tmp)
        verify_export(final)
        return {'status':'V27_EXPORT_KRISTAL_PRIVE_OK','directory':str(final),
                'claims':info['unique_claims'],'imported_deltas':count,'canonical_admissions':0}


def verify_export(path):
    m=json.loads((Path(path)/'MANIFEST_EXPORT_V27.json').read_text(encoding='utf-8'))
    if m.get('format')!=STORE_FORMAT or m.get('canonical_admissions')!=0:
        raise Refusal('Export invalide')
    for name, expected in m['files_sha256'].items():
        if hash_file(Path(path)/name)!=expected:
            raise Refusal('Export altere: '+name)
    return m


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='action',required=True)
    for cmd in ('packs','import','status','export','verify-pack'):
        ap=sub.add_parser(cmd)
        ap.add_argument('--work',type=Path,default=DEFAULT_WORK)
        if cmd=='packs':
            ap.add_argument('--catalogue',type=Path,default=DEFAULT_CATALOGUE)
            ap.add_argument('--xml',type=Path,default=DEFAULT_XML)
            ap.add_argument('--index',type=Path,default=DEFAULT_INDEX)
            ap.add_argument('--max-packs',type=int,default=5)
            ap.add_argument('--max-articles',type=int,default=12)
            ap.add_argument('--target-words',type=int,default=35000)
            ap.add_argument('--target-bytes',type=int,default=6*1024*1024)
        if cmd in ('import','verify-pack'):
            ap.add_argument('--pack',type=Path,required=True)
        if cmd=='import':
            ap.add_argument('--delta',type=Path,required=True)
    args=p.parse_args(argv)
    try:
        if args.action=='packs':result=produce(args)
        elif args.action=='import':result=import_delta(args)
        elif args.action=='status':result=report(args.work)
        elif args.action=='export':result=export_store(args.work)
        else:
            m=verify_pack(args.pack)
            result={'status':'V27_PACK_VERIFIE','pack_id':m['pack_id'],
                    'articles_count':m['articles_count'],'sha256':hash_file(args.pack)}
        print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
        return 0
    except (Refusal,OSError,sqlite3.DatabaseError,ValueError,KeyError,zipfile.BadZipFile,UnicodeError) as e:
        print(json.dumps({'status':'V27_REFUS_SANS_CANONISATION','error':str(e)},ensure_ascii=False),file=sys.stderr,flush=True)
        return 2


if __name__=='__main__':
    sys.exit(main())
