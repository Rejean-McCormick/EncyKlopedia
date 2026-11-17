#!/usr/bin/env python3
"""Index byte spans of Wikipedia pages in an existing uncompressed XML dump.

Only an independent derived SQLite file is written. Sources and pre-existing
Wikimedia SQL/graph indexes are never opened writable. The checkpoint is always
an XML </page> boundary committed in the same transaction as its page rows.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import os
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import sqlite3
import sys

VERSION = 'koa.wikipedia-direct-xml-offsets/1.0'
DEFAULT_XML = Path(r'D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml')
DEFAULT_DB = Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.sqlite')
DEFAULT_CATALOGUE = Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.source-candidate.json')
OPEN = b'<page>'
CLOSE = b'</page>'
TITLE = re.compile(rb'<title>(.*?)</title>', re.DOTALL)
NS = re.compile(rb'<ns>(\d+)</ns>')
ID = re.compile(rb'<id>(\d+)</id>')
REV = re.compile(rb'<revision\b[^>]*>\s*<id>(\d+)</id>', re.DOTALL)
REDIRECT = re.compile(rb'<redirect(?:\s|/|>)')
MAX_PAGE_BYTES = 256 * 1024 * 1024
DEFAULT_CHUNK = 8 * 1024 * 1024


def emit(**kwargs):
    print(json.dumps(kwargs, ensure_ascii=False), flush=True)


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def signature(p: Path):
    p = p.resolve(strict=True)
    st = p.stat()
    if not p.is_file() or st.st_size < 128:
        raise ValueError('XML absent ou trop petit: ' + str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        h.update(f.read(1024 * 1024))
        f.seek(max(0, st.st_size - 1024 * 1024))
        h.update(f.read(1024 * 1024))
    return {'path': str(p), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns,
            'head_tail_sha256': h.hexdigest(), 'hash_scope': 'FIRST_AND_LAST_MIB_ONLY'}


def check_xml(p: Path):
    with p.open('rb') as f:
        header = f.read(1024 * 1024)
        if b'<mediawiki' not in header or b'<page>' not in header:
            raise ValueError('Fichier non reconnu comme dump Wikipedia XML non compresse')
        f.seek(max(0, p.stat().st_size - 1024 * 1024))
        if b'</mediawiki>' not in f.read():
            raise ValueError('Fin XML </mediawiki> absente: source potentiellement incomplete')


def validate_paths(xml: Path, db: Path):
    if not xml.is_file():
        raise ValueError('Source XML introuvable: ' + str(xml))
    if xml.suffix.lower() != '.xml':
        raise ValueError('La source doit être le XML DECOMPRESSE (.xml)')
    if db.resolve() == xml.resolve() or db.name.lower() in ('wikipedia_en.sqlite', 'wikipedia_en_multistream_offsets_v20.sqlite'):
        raise ValueError('Refus de remplacer une source ou un index preexistant')
    check_xml(xml)
    return signature(xml)


def scan_pages(f, start: int, *, chunk_bytes: int = DEFAULT_CHUNK, max_page_bytes: int = MAX_PAGE_BYTES):
    """Yield (offset, ending, page_xml), bounded to one page + a read chunk.

    No repeated slicing of the remaining chunk for every page; we consume it
    with a cursor and compact it only after searching the whole chunk.
    """
    if chunk_bytes < 16 or max_page_bytes < 128:
        raise ValueError('Tailles des tampons invalides')
    f.seek(start)
    buf = b''
    origin = start
    eof = False
    while True:
        if not eof:
            data = f.read(chunk_bytes)
            if data:
                buf += data
            else:
                eof = True
        cursor = 0
        need_more = False
        while True:
            opener = buf.find(OPEN, cursor)
            if opener < 0:
                # Keep enough bytes to recognize an opening tag across chunks.
                keep = 0 if eof else min(len(OPEN) - 1, len(buf) - cursor)
                drop = len(buf) - keep
                origin += drop
                buf = buf[drop:]
                break
            closer = buf.find(CLOSE, opener + len(OPEN))
            if closer < 0:
                if eof:
                    raise ValueError('Derniere page XML tronquee a offset=' + str(origin + opener))
                origin += opener
                buf = buf[opener:]
                if len(buf) > max_page_bytes:
                    raise ValueError('Page XML trop volumineuse, index arrete sans perte du checkpoint')
                need_more = True
                break
            ending = closer + len(CLOSE)
            if ending - opener > max_page_bytes:
                raise ValueError('Page XML depasse la limite par page')
            yield origin + opener, origin + ending, buf[opener:ending]
            cursor = ending
        if eof:
            break
        if not need_more and not buf:
            # Avoid retaining past pages, even after large chunks.
            pass


def page_meta(raw: bytes):
    # The top-level page ID appears before <revision>, never confuse revision IDs.
    head = raw[:min(len(raw), 16384)].split(b'<revision', 1)[0]
    title = TITLE.search(head)
    ns = NS.search(head)
    pid = ID.search(head)
    if not title or not ns or not pid:
        raise ValueError('Page XML sans <title>, <ns> ou <id> avant sa revision')
    page_id = int(pid.group(1))
    if page_id < 1:
        raise ValueError('Identifiant Wikimedia invalide')
    label = html.unescape(title.group(1).decode('utf-8', errors='strict'))
    # Standard single-revision Wikimedia pages-articles XML.
    rev = REV.search(raw, len(head))
    if rev is None:
        rev = REV.search(raw)
    return (page_id, int(ns.group(1)), label,
            rev.group(1).decode('ascii') if rev else '',
            1 if REDIRECT.search(head) else 0)


def connect(db: Path, sig: dict):
    if db.exists():
        c = sqlite3.connect(db, timeout=120)
        try:
            tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'v21_meta', 'pages'}.issubset(tables):
                raise ValueError('Base SQLite preexistante non reconnue comme index V21: ' + str(db))
            old = {k: json.loads(v) for k,v in c.execute('SELECT name,value FROM v21_meta')}
            if old.get('format') != VERSION or old.get('source_signature') != sig:
                raise ValueError('Index V21 lie a un autre XML : refuser de melanger les sources')
        except BaseException:
            c.close()
            raise
        return c
    db.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(db, timeout=120)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=FULL')
    c.execute('PRAGMA busy_timeout=120000')
    with c:
        c.execute('CREATE TABLE v21_meta (name TEXT PRIMARY KEY, value TEXT NOT NULL)')
        c.execute('''CREATE TABLE pages (
            page_id INTEGER PRIMARY KEY,
            byte_offset INTEGER NOT NULL CHECK(byte_offset >= 0),
            byte_length INTEGER NOT NULL CHECK(byte_length > 0),
            namespace INTEGER NOT NULL,
            title TEXT NOT NULL,
            revision_id TEXT NOT NULL,
            is_redirect INTEGER NOT NULL CHECK(is_redirect IN (0,1))
        )''')
        for name, val in [('format', VERSION), ('source_signature', sig),
                           ('checkpoint', 0), ('pages_indexed', 0), ('complete', False),
                           ('created_utc', utc())]:
            c.execute('INSERT INTO v21_meta(name,value) VALUES(?,?)',
                      (name, json.dumps(val, ensure_ascii=False, sort_keys=True)))
    return c


def state(c):
    return {k: json.loads(v) for k, v in c.execute('SELECT name,value FROM v21_meta')}


def setmeta(c, name, value):
    c.execute('UPDATE v21_meta SET value=? WHERE name=?',
              (json.dumps(value, ensure_ascii=False, sort_keys=True), name))


def _build_unlocked(xml: Path, db: Path, *, batch_pages=10000, progress_pages=100000,
          max_pages=0, chunk_bytes=DEFAULT_CHUNK):
    if batch_pages < 1 or progress_pages < 1 or max_pages < 0:
        raise ValueError('Parametres invalides')
    sig = validate_paths(xml, db)
    with connect(db, sig) as c:
        st = state(c)
        if st['complete']:
            return {'status': 'V21_INDEX_DEJA_COMPLET', 'index': str(db),
                    'pages_indexed': st['pages_indexed'], 'checkpoint': st['checkpoint'],
                    'source_bytes': sig['bytes']}
        start = int(st['checkpoint'])
        rows=[]; session_pages=0; last_progress=int(st['pages_indexed'])
        next_checkpoint=start
        def flush():
            nonlocal rows
            if not rows: return
            with c:
                c.executemany('''INSERT INTO pages(page_id,byte_offset,byte_length,namespace,title,revision_id,is_redirect)
                    VALUES(?,?,?,?,?,?,?)''', rows)
                setmeta(c, 'checkpoint', next_checkpoint)
                setmeta(c, 'pages_indexed', st['pages_indexed'] + session_pages)
            rows=[]
        try:
            with xml.open('rb') as f:
                for begin, end, raw in scan_pages(f, start, chunk_bytes=chunk_bytes):
                    pid, ns, title, rid, redirect = page_meta(raw)
                    rows.append((pid,begin,end-begin,ns,title,rid,redirect))
                    next_checkpoint=end
                    session_pages += 1
                    if len(rows) >= batch_pages:
                        flush()
                    count=st['pages_indexed']+session_pages
                    if count-last_progress >= progress_pages:
                        if rows:flush()
                        emit(event='V21_INDEX_PROGRESS', pct=round(next_checkpoint*100/sig['bytes'],2),
                             xml_offset=next_checkpoint, xml_bytes=sig['bytes'],
                             pages_indexed=count, pages_this_session=session_pages,
                             database=str(db))
                        last_progress=count
                    if max_pages and session_pages >= max_pages:
                        flush()
                        return {'status':'V21_INDEX_PARTIEL_REPRENABLE', 'checkpoint':next_checkpoint,
                                'pages_indexed':st['pages_indexed']+session_pages,
                                'source_bytes':sig['bytes'],'index':str(db)}
            flush()
            # Mark EOF only after seeing a valid closing XML root.
            check_xml(xml)
            with c:
                setmeta(c, 'complete', True)
                setmeta(c, 'checkpoint', sig['bytes'])
                setmeta(c, 'finished_utc', utc())
            return {'status':'V21_INDEX_COMPLET','pages_indexed':st['pages_indexed']+session_pages,
                    'checkpoint':sig['bytes'],'source_bytes':sig['bytes'],'index':str(db),
                    'read_only_sources':True,'canonical_unchanged':True}
        except (KeyboardInterrupt, SystemExit):
            # No uncommitted pages/checkpoint allowed. Complete batches are safe.
            raise


@contextmanager
def writer_lock(db: Path):
    """Cross-process OS lock; automatically released by OS even on hard kill.

    The tiny .writer.lock file is a derived operational marker, not a signal
    that a completed build exists. Only the held lock controls exclusivity.
    """
    db.parent.mkdir(parents=True, exist_ok=True)
    lockfile=Path(str(db)+'.writer.lock')
    with lockfile.open('a+b') as f:
        f.seek(0,2)
        if f.tell()==0:
            f.write(b'\0');f.flush()
        f.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError('Un autre indexeur V21 utilise deja cette base; ne pas en lancer deux') from exc
        try:yield
        finally:
            f.seek(0)
            if os.name=='nt':msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(f,fcntl.LOCK_UN)

def build(xml: Path, db: Path, *, batch_pages=10000, progress_pages=100000,
          max_pages=0, chunk_bytes=DEFAULT_CHUNK):
    with writer_lock(db):
        return _build_unlocked(xml,db,batch_pages=batch_pages,
                               progress_pages=progress_pages,
                               max_pages=max_pages,chunk_bytes=chunk_bytes)


def ro_connect(db: Path):
    if not db.is_file():
        raise ValueError('Index V21 introuvable: '+str(db))
    c = sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True,timeout=30)
    c.execute('PRAGMA query_only=ON')
    return c


def audit(xml: Path, db: Path, *, samples=12, require_complete=False):
    sig=validate_paths(xml,db)
    with ro_connect(db) as c:
        st=state(c)
        if st.get('format')!=VERSION or st.get('source_signature')!=sig:
            raise ValueError('Identite de source XML / index V21 invalide')
        found=c.execute('SELECT COUNT(*) FROM pages').fetchone()[0]
        if found != st['pages_indexed']:
            raise ValueError('Compteurs incoherents entre l index et le checkpoint')
        if require_complete and not st['complete']:
            raise ValueError('Index V21 incomplet; relancer le lanceur principal')
        if st['complete'] and st['checkpoint']!=sig['bytes']:
            raise ValueError('Checkpoint final different de la longueur XML')
        if not 0<=st['checkpoint']<=sig['bytes']:
            raise ValueError('Checkpoint XML hors limites')
        verified=0
        if found:
            # Logically spaced rows, without expensive random-row SQL scans.
            selected=[0, found//2, found-1]
            selected.extend(int(i*(found-1)/(max(samples-1,1))) for i in range(samples))
            # Indexed ordering by byte_offset would force a scan/sort: use page_id
            # percentile approximation via primary-key range on the real distribution.
            extrema=c.execute('SELECT MIN(page_id),MAX(page_id) FROM pages').fetchone()
            targets=[int(extrema[0] + (extrema[1]-extrema[0])*i/max(1,samples-1)) for i in range(samples)]
            ids={}
            for q in targets:
                row=c.execute('SELECT page_id,byte_offset,byte_length FROM pages WHERE page_id>=? ORDER BY page_id LIMIT 1',(q,)).fetchone()
                if row:ids[row[0]]=row
            for row in (c.execute('SELECT page_id,byte_offset,byte_length FROM pages ORDER BY page_id LIMIT 1').fetchone(),
                        c.execute('SELECT page_id,byte_offset,byte_length FROM pages ORDER BY page_id DESC LIMIT 1').fetchone()):
                ids[row[0]]=row
            with xml.open('rb') as f:
                for pid, pos, length in ids.values():
                    f.seek(pos);raw=f.read(length)
                    if len(raw)!=length or not raw.startswith(OPEN) or not raw.endswith(CLOSE) or page_meta(raw)[0]!=pid:
                        raise ValueError('Entree index non conforme a l XML: '+str(pid))
                    verified+=1
        return {'status':'V21_INDEX_INTEGRITE_VERIFIEE','index':str(db),
                'pages_indexed':found,'complete':st['complete'],
                'checkpoint':st['checkpoint'],'source_bytes':sig['bytes'],
                'sampled_pages_verified':verified,'no_canonical_changes':True}


def read_one(f, row, wanted: int):
    pid, pos, length, ns, title, revision_id, redirect=row
    if int(pid)!=wanted or pos<0 or length<1 or length>MAX_PAGE_BYTES:
        raise ValueError('Entree d index V21 invalide')
    f.seek(pos)
    raw=f.read(length)
    if len(raw)!=length or not raw.startswith(OPEN) or not raw.endswith(CLOSE):
        raise ValueError('Source XML et offset non conformes')
    got_id, got_ns, got_title, got_rev, got_redir = page_meta(raw)
    if (got_id,got_ns,got_title,got_rev,got_redir)!=(pid,ns,title,revision_id,redirect):
        raise ValueError('Metadonnees du XML differentes de l index V21')
    return raw


def export_source_candidate(xml:Path, db:Path, output:Path):
    result=audit(xml,db,require_complete=True)
    document={
        'format':'koa.wikipedia-local-documentary-source-candidate/1.0',
        'status':'PREPARATION_MEDIATHEQUE_NON_IMPORTEE_NON_APPROUVEE',
        'source_kind':'WIKIPEDIA_EN_XML_SNAPSHOT',
        'source_identifier_candidate':'enwiki-2026-10-pages-articles-multistream',
        'xml_representation':signature(xml),
        'derived_direct_index':{'path':str(db),'format':VERSION,
                                'page_records':result['pages_indexed']},
        'source_and_index_are_not_canonical_KS':True,
        'imported_to_mediatheque':False,
        'wikipedia_license_note':'Verify current licensing, revision attribution, and provenance before reusing texts',
    }
    content=(json.dumps(document,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
    if output.exists():
        if output.read_bytes()!=content:
            raise ValueError('Catalogue candidat preexistant different: choisir un --output distinct')
        status='V21_CATALOGUE_CANDIDAT_DEJA_PRESENT'
    else:
        output.parent.mkdir(parents=True,exist_ok=True)
        tmp=Path(str(output)+'.tmp')
        if tmp.exists():raise ValueError('Ancien fichier .tmp de catalogue: examen manuel requis')
        try:
            with tmp.open('xb') as f:f.write(content)
            tmp.replace(output)
        finally:
            if tmp.exists():tmp.unlink()
        status='V21_CATALOGUE_CANDIDAT_PRET'
    return {'status':status,'output':str(output),
            'pages':result['pages_indexed'],'mediatheque_imported':False,
            'canon_unchanged':True}


def parse(argv=None):
    p=argparse.ArgumentParser(description='Wikimedia XML decompresse -> index direct V21 SQLite (derive)')
    sub=p.add_subparsers(dest='action',required=True)
    for command in ('preflight','index','audit','status','lookup','catalogue'):
        a=sub.add_parser(command)
        a.add_argument('--xml', default=str(DEFAULT_XML))
        a.add_argument('--db', default=str(DEFAULT_DB))
        if command=='index':
            a.add_argument('--batch-pages',type=int,default=10000)
            a.add_argument('--progress-pages',type=int,default=100000)
            a.add_argument('--max-pages',type=int,default=0)
        if command=='audit':a.add_argument('--require-complete',action='store_true')
        if command=='lookup':a.add_argument('--page-id',required=True,type=int)
        if command=='catalogue':a.add_argument('--output',default=str(DEFAULT_CATALOGUE))
    return p.parse_args(argv)


def main(argv=None):
    try:
        a=parse(argv); xml=Path(a.xml); db=Path(a.db)
        if a.action=='preflight':
            s=validate_paths(xml,db)
            output={'status':'V21_XML_PRET','source':s,'index':str(db),
                    'index_existing':db.exists(),'source_read_only':True}
        elif a.action=='index':
            output=build(xml,db,batch_pages=a.batch_pages,
                         progress_pages=a.progress_pages,max_pages=a.max_pages)
        elif a.action in ('audit','status'):output=audit(xml,db,require_complete= a.action=='audit' and a.require_complete)
        elif a.action=='catalogue':output=export_source_candidate(xml,db,Path(a.output))
        else:
            audit(xml,db)
            with ro_connect(db) as c:
                row=c.execute('SELECT page_id,byte_offset,byte_length,namespace,title,revision_id,is_redirect FROM pages WHERE page_id=?',(a.page_id,)).fetchone()
            if row is None:raise ValueError('Page non encore indexee ou inexistante: '+str(a.page_id))
            with xml.open('rb') as f:read_one(f,row,a.page_id)
            output={'status':'V21_PAGE_ACCESS_DIRECT_VERIFIE','page_id':a.page_id,
                    'title':row[4],'byte_offset':row[1],'byte_length':row[2],
                    'revision_id':row[5]}
        emit(**output)
        return 0 if output['status'] not in ('V21_INDEX_PARTIEL_REPRENABLE',) else 3
    except KeyboardInterrupt:
        emit(status='V21_INTERRUPTION_PROPRE',reprise='Relancer exactement la commande index')
        return 130
    except (OSError,ValueError,sqlite3.DatabaseError,UnicodeError) as exc:
        emit(status='V21_ECHEC_SANS_ECRITURE_SOURCE',error=str(exc))
        return 2

if __name__=='__main__':sys.exit(main())
