#!/usr/bin/env python3
"""Reconstruct a resumable, private Wikimedia multistream page->byte-offset index.

The source is read-only. This *separate* derived SQLite stores every observed
page id and the start offset of its independent bzip2 member. The original
Wikimedia SQL index, Kristal and Mediatheque are never written to.

This reader assumes pages-articles-MULTISTREAM.xml.bz2 (concatenated independent
bzip2 members), NOT a generic single-member bzip2 archive. On malformed input
it fails closed and retains the last fully committed member checkpoint.
"""
from __future__ import annotations

import bz2
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys

VERSION = 'koa.wikipedia-multistream-local-offsets/1.0'
DEFAULT_XML = Path(r'D:\EncyKlopedia\10_sources\wikipedia\enwiki\2026-10\enwiki-latest-pages-articles-multistream.xml.bz2')
DEFAULT_SIDECAR = Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_multistream_offsets_v20.sqlite')
BATCH_BYTES = 256 * 1024
MAX_UNCOMPRESSED_MEMBER = 256 * 1024 * 1024
MAX_COMPRESSED_MEMBER = 128 * 1024 * 1024
PAGE = re.compile(rb'<page(?:\s[^>]*)?>.*?</page>', re.DOTALL)
ID = re.compile(rb'<id>(\d+)</id>')
NS = re.compile(rb'<ns>(\d+)</ns>')


def utc():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def signature(p: Path):
    """Metadata and sampled head/tail digest: NOT a full-file attestation."""
    p = p.resolve(strict=True)
    if not p.is_file():
        raise ValueError('Source XML absente ou non régulière : '+str(p))
    st = p.stat()
    if st.st_size < 64:
        raise ValueError('Archive XML suspecte : '+str(p))
    h = hashlib.sha256()
    with p.open('rb') as f:
        h.update(f.read(1024 * 1024))
        f.seek(max(0, st.st_size - 1024 * 1024))
        h.update(f.read(1024 * 1024))
    return {'path':str(p), 'bytes':st.st_size, 'mtime_ns':st.st_mtime_ns,
            'head_tail_sha256':h.hexdigest(), 'hash_scope':'FIRST_AND_LAST_MIB_ONLY'}


def emit(**data):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def single_member(f, offset):
    """Return (decompressed_member, next_compressed_offset), with output caps.

    BZ2Decompressor may leave unused bytes from the next member; put them back
    before returning so a crash/restart at the checkpoint is byte-identical.
    """
    f.seek(offset)
    head = f.read(4)
    if len(head) != 4 or head[:3] != b'BZh' or head[3:4] not in b'123456789':
        raise ValueError(f'En-tête BZip2 multistream invalide à offset={offset}')
    f.seek(offset)
    dec=bz2.BZ2Decompressor()
    chunks=[]; total=0; consumed=0
    while not dec.eof:
        if dec.needs_input:
            remaining = MAX_COMPRESSED_MEMBER - consumed
            if remaining <= 0:
                raise ValueError(f'Membre compressé trop grand à offset={offset}; index partiel conservé')
            block=f.read(min(BATCH_BYTES,remaining))
            if not block:
                raise ValueError(f'Membre BZip2 tronqué à offset={offset}; index partiel conservé')
            consumed += len(block)
        else:
            block=b''
        try:
            part=dec.decompress(block,max_length=4 * 1024 * 1024)
        except (OSError,EOFError) as exc:
            raise ValueError(f'Membre BZip2 corrompu à offset={offset}: {exc}') from exc
        if part:
            chunks.append(part);total+=len(part)
        if total > MAX_UNCOMPRESSED_MEMBER:
            raise ValueError(f'Membre trop gros (>256 MiB) à offset={offset}; refus sûr')
    back=len(dec.unused_data)
    if back:
        f.seek(-back,1)
    ending=f.tell()
    if ending<=offset:
        raise ValueError('Index compressé sans progression')
    return b''.join(chunks), ending


def page_ids(raw: bytes):
    result=[]
    seen=set()
    matched=0
    for m in PAGE.finditer(raw):
        matched+=1
        # The outer <page> ID is before <revision>; we never read revision IDs.
        prefix=raw[m.start():min(m.end(),m.start()+4096)].split(b'<revision',1)[0]
        pid=ID.search(prefix)
        ns=NS.search(prefix)
        if not pid or not ns:
            raise ValueError('Page XML sans id ou ns avant 4 Ko de métadonnées')
        page_id=int(pid.group(1))
        if page_id<=0 or page_id in seen:
            raise ValueError('ID de page dupliqué ou invalide dans un flux')
        seen.add(page_id)
        # The pages-articles archive also contains template pages; retain only
        # namespace 0 because the v19 atlas explicitly selects ns=0.
        if ns.group(1)==b'0':
            result.append(page_id)
    if raw.count(b'<page>') != matched:
        # Treat incomplete page elements as corruption; never skip them silently.
        raise ValueError('Flux avec page XML incomplète, extraction interrompue')
    return result


def connect(sidecar: Path, srcsig: dict):
    if sidecar.resolve() == Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite').resolve() or sidecar.name.lower() == 'wikipedia_en.sqlite':
        raise ValueError('Refus d’écrire dans la base Wikipédia SQL existante')
    if sidecar.exists():
        with sqlite3.connect(sidecar) as chk:
            names={x[0] for x in chk.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if 'v20_meta' not in names or 'page_offsets' not in names or 'streams' not in names:
                raise ValueError('SQLite existant non reconnu comme index V20 : '+str(sidecar))
            state={k:json.loads(v) for k,v in chk.execute('SELECT name,value FROM v20_meta')}
            if state.get('format') != VERSION or state.get('xml_signature') != srcsig:
                raise ValueError('Index V20 associé à une source XML différente ou modifiée; refuser le mélange')
    else:
        sidecar.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(sidecar,timeout=120)
    conn.execute('PRAGMA busy_timeout=120000')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=FULL')
    conn.executescript('''
      CREATE TABLE IF NOT EXISTS v20_meta(name TEXT PRIMARY KEY, value TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS streams(offset INTEGER PRIMARY KEY, ending INTEGER NOT NULL,
        ns0_pages INTEGER NOT NULL, expanded_bytes INTEGER NOT NULL);
      CREATE TABLE IF NOT EXISTS page_offsets(page_id INTEGER PRIMARY KEY, offset INTEGER NOT NULL);
    ''')
    def put(name,value):
        conn.execute('INSERT OR REPLACE INTO v20_meta(name,value) VALUES (?,?)',
                     (name,json.dumps(value,ensure_ascii=False,sort_keys=True)))
    with conn:
        if conn.execute("SELECT 1 FROM v20_meta WHERE name='format'").fetchone() is None:
            put('format',VERSION);put('xml_signature',srcsig)
            put('checkpoint',0);put('complete',False)
            put('streams_indexed',0);put('page_ids_indexed',0)
    return conn


def state(conn):
    return {k:json.loads(v) for k,v in conn.execute('SELECT name,value FROM v20_meta')}


def offsets(conn, wanted: set[int]):
    result={}
    for pid in wanted:
        r=conn.execute('SELECT offset FROM page_offsets WHERE page_id=?',(pid,)).fetchone()
        if r:result[pid]=int(r[0])
    return result


def ensure_offsets(xml:Path, sidecar:Path, wanted:set[int], max_streams:int=0,
                   progress_every:int=500):
    """Advance until all wanted page ids are found OR EOF; resume is atomic.

    max_streams=0 means no artificial limit; a nonzero value enables bounded
    troubleshooting or testing. Returns status even if incomplete.
    """
    if max_streams<0 or progress_every<1:
        raise ValueError('Limites de scan invalides')
    sig=signature(xml)
    with connect(sidecar,sig) as con:
        st=state(con)
        found=offsets(con,wanted)
        if len(found)==len(wanted):
            return {'status':'OFFSETS_READY','offsets':found,
                    'complete':st['complete'],'checkpoint':st['checkpoint'],
                    'streams_indexed':st['streams_indexed'],'page_ids_indexed':st['page_ids_indexed'],
                    'xml_signature':sig}
        if st['complete']:
            return {'status':'PAGES_ABSENTES_DU_DUMP','offsets':found,
                    'missing':sorted(wanted-set(found)), 'complete':True,
                    'checkpoint':st['checkpoint'],'xml_signature':sig}
        start=st['checkpoint']; session=0
        with xml.open('rb') as f:
            f.seek(start)
            while start<sig['bytes']:
                raw, end=single_member(f,start)
                ids=page_ids(raw)
                # One transaction per entire bzip2 member: checkpoint and rows
                # can never disagree even if the process is interrupted.
                with con:
                    con.executemany('INSERT INTO page_offsets(page_id,offset) VALUES(?,?)',
                                    ((pid,start) for pid in ids))
                    con.execute('INSERT INTO streams(offset,ending,ns0_pages,expanded_bytes) VALUES(?,?,?,?)',
                                (start,end,len(ids),len(raw)))
                    con.execute('UPDATE v20_meta SET value=? WHERE name=?',(json.dumps(end),'checkpoint'))
                    con.execute('UPDATE v20_meta SET value=? WHERE name=?',
                                (json.dumps(st['streams_indexed']+session+1),'streams_indexed'))
                    con.execute('UPDATE v20_meta SET value=? WHERE name=?',
                                (json.dumps(st['page_ids_indexed']+len(ids)), 'page_ids_indexed'))
                st['page_ids_indexed']+=len(ids)
                session+=1
                newly_wanted=wanted-set(found)
                if newly_wanted:
                    for pid in ids:
                        if pid in newly_wanted:
                            found[pid]=start
                start=end
                if session%progress_every==0:
                    emit(event='V20_INDEX_PROGRESS',compressed_offset=start,
                         compressed_bytes=sig['bytes'],pct=round(start*100/sig['bytes'],2),
                         streams_this_session=session,ids_total=st['page_ids_indexed'],
                         wanted_found=len(found),wanted_total=len(wanted))
                if len(found)==len(wanted):break
                if max_streams and session>=max_streams:break
            if start==sig['bytes']:
                with con:
                    con.execute('UPDATE v20_meta SET value=? WHERE name=?',('true','complete'))
        st=state(con)
        ready=len(found)==len(wanted)
        return {'status':('OFFSETS_READY' if ready else 'INDEX_PAUSED' if not st['complete']
                          else 'PAGES_ABSENTES_DU_DUMP'),
                'offsets':found,'missing':sorted(wanted-set(found)),
                'complete':st['complete'],'checkpoint':st['checkpoint'],
                'streams_indexed':st['streams_indexed'],'page_ids_indexed':st['page_ids_indexed'],
                'xml_signature':sig}


def audit_index(xml:Path,sidecar:Path):
    srcsig=signature(xml)
    if not sidecar.is_file():return {'status':'INDEX_V20_NON_CREE','xml_signature':srcsig}
    with sqlite3.connect(f'file:{sidecar.resolve().as_posix()}?mode=ro',uri=True) as c:
        state0={k:json.loads(v) for k,v in c.execute('SELECT name,value FROM v20_meta')}
        if state0.get('format')!=VERSION or state0.get('xml_signature')!=srcsig:
            raise ValueError('Empreinte ou version de l’index V20 non conforme')
        streamcount=c.execute('SELECT COUNT(*) FROM streams').fetchone()[0]
        pagecount=c.execute('SELECT COUNT(*) FROM page_offsets').fetchone()[0]
        if streamcount!=state0['streams_indexed'] or pagecount!=state0['page_ids_indexed']:
            raise ValueError('Compteurs de l’index V20 incohérents')
        return {'status':'INDEX_V20_VALID','complete':state0['complete'],
                'checkpoint':state0['checkpoint'], 'streams':streamcount,
                'pages':pagecount, 'xml_signature':srcsig}
