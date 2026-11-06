#!/usr/bin/env python3
"""EncyKlopedia candidate lexical inventory/index. Python stdlib only.

Reads *existing* source archives; never modifies or extracts source files.
Writes a resumable local SQLite candidate index to 30_working only.
Not a diK canonical dictionary, reviewed crosswalk, or publication authority.
"""
from __future__ import annotations

import argparse
import bz2
import csv
import gzip
import json
import lzma
import os
import re
import shutil
import sqlite3
import sys
import time
import unicodedata
import zipfile
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

VERSION = '0.3.0'
DATA_DEFAULT = Path(r'D:\EncyKlopedia') if os.name == 'nt' else None
SUBDIR = Path('30_working/lexical/harvester/index-v1')
LANG_RE = re.compile(r'^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$')
ALIASES = json.loads((Path(__file__).with_name('language-aliases.json')).read_text(encoding='utf-8'))['aliases']
LEXEME_RE = re.compile(r'^L[1-9][0-9]*$')
ALLOWED_KINDS = {'kaikki', 'unimorph', 'wikidata'}
SCHEMA = '''
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS source_files (
 id INTEGER PRIMARY KEY, relative_path TEXT NOT NULL UNIQUE, kind TEXT NOT NULL,
 edition TEXT NOT NULL, size_bytes INTEGER NOT NULL, mtime_ns INTEGER NOT NULL,
 status TEXT NOT NULL, cursor_lines INTEGER NOT NULL DEFAULT 0,
 accepted INTEGER NOT NULL DEFAULT 0, rejected INTEGER NOT NULL DEFAULT 0,
 started_at TEXT, finished_at TEXT, error TEXT,
 source_sha256_verified INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS entries (
 id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL REFERENCES source_files(id),
 source_line INTEGER NOT NULL, language_code TEXT NOT NULL,
 lemma TEXT NOT NULL, lemma_key TEXT NOT NULL, pos TEXT,source_language_code TEXT,
 form_surface TEXT,form_key TEXT,grammatical_features TEXT,
 sense_observations INTEGER NOT NULL, form_observations INTEGER NOT NULL,
 translation_observations INTEGER NOT NULL, external_id TEXT,
 language_qid TEXT
);
CREATE INDEX IF NOT EXISTS idx_entries_language_lemma ON entries(language_code,lemma_key);
CREATE INDEX IF NOT EXISTS idx_entries_source_line ON entries(source_id,source_line);
CREATE INDEX IF NOT EXISTS idx_entries_form ON entries(form_key,language_code);
CREATE TABLE IF NOT EXISTS language_stats (
 source_id INTEGER NOT NULL REFERENCES source_files(id), language_code TEXT NOT NULL,
 lemma_observations INTEGER NOT NULL, sense_observations INTEGER NOT NULL,
 form_observations INTEGER NOT NULL, translation_observations INTEGER NOT NULL,
 PRIMARY KEY(source_id,language_code)
);
CREATE TABLE IF NOT EXISTS source_members (
 source_id INTEGER NOT NULL REFERENCES source_files(id),
 member_path TEXT NOT NULL, member_format TEXT NOT NULL,
 start_line INTEGER NOT NULL, end_line INTEGER NOT NULL,
 PRIMARY KEY(source_id,member_path)
);
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
'''

def utc():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def valid_lake(root: Path):
    root = root.resolve()
    for rel in ('10_sources/lexical', '20_evidence', '30_working', '50_mediatheque'):
        if not (root / rel).is_dir():
            raise ValueError(f'Racine de donnees invalide (absent: {root / rel})')
    return root

def source_candidates(root: Path, kinds: set[str] | None = None):
    kinds = kinds or ALLOWED_KINDS
    source = root / '10_sources' / 'lexical'
    candidates = []
    if 'kaikki' in kinds:
        ed = source / 'wiktionary' / 'kaikki' / 'raw-editions'
        candidates += [('kaikki', p.parent.name, p) for p in ed.glob('*/*.jsonl.gz') if p.is_file()]
        legacy = source / 'wiktionary' / 'kaikki' / 'enwiktionary'
        candidates += [('kaikki', 'enwiktionary-legacy', p) for pat in ('**/*.jsonl','**/*.jsonl.gz') for p in legacy.glob(pat) if p.is_file()]
        captures = source / 'harvester' / 'raw'
        for p in captures.glob('kaikki-*/*/*'):
            if p.is_file() and (p.name.endswith('.jsonl.gz') or p.name.endswith('.jsonl')):
                candidates.append(('kaikki', p.parent.parent.name, p))
    if 'unimorph' in kinds:
        candidates += [('unimorph', p.stem, p) for p in (source / 'unimorph' / 'repos').glob('*.zip') if p.is_file() and re.fullmatch('[a-z]{3}',p.stem)]
    if 'wikidata' in kinds:
        candidates += [('wikidata', 'wikidata-lexemes', p) for p in (source/'wikidata'/'lexemes'/'dumps'/'current').glob('*.json.bz2') if p.is_file() and 'lexeme' in p.name]
    seen=set(); out=[]
    for kind,edition,p in sorted(candidates, key=lambda x: x[2].as_posix()):
        rp=p.resolve()
        if rp in seen: continue
        if root not in rp.parents: raise ValueError(f'Source hors D: / lien symbolique non autorise: {p}')
        seen.add(rp)
        st=rp.stat()
        out.append(dict(kind=kind,edition=edition,path=rp,relative=rp.relative_to(root).as_posix(),size=st.st_size,mtime=st.st_mtime_ns))
    return out

def normalized_lemma(text):
    text = unicodedata.normalize('NFKC',text).strip()
    return text[:300], text.casefold()[:300]

def code(text):
    if not isinstance(text,str): return 'und'
    text=text.strip().lower().replace('_','-')
    if len(text)>40 or not LANG_RE.fullmatch(text): return 'und'
    parts=text.split('-')
    parts[0]=ALIASES.get(parts[0],parts[0])
    return '-'.join(parts)

def counts(obj):
    senses=obj.get('senses')
    if not isinstance(senses,list): senses=[]
    forms=obj.get('forms')
    if not isinstance(forms,list): forms=[]
    translations=obj.get('translations')
    if not isinstance(translations,list): translations=[]
    return len(senses),len(forms),len(translations)

def parse_kaikki(line):
    obj=json.loads(line)
    if not isinstance(obj,dict): return None
    lemma=obj.get('word')
    if not isinstance(lemma,str) or not lemma.strip(): return None
    lemma,key=normalized_lemma(lemma)
    if not key: return None
    lang=code(obj.get('lang_code'))
    source_lang=obj.get('lang_code') if isinstance(obj.get('lang_code'),str) else None
    senses,forms,trans=counts(obj)
    pos=obj.get('pos')
    if not isinstance(pos,str): pos=None
    return (lang,lemma,key,(pos or '')[:80],senses,forms,trans,None,None,source_lang,None,None,None)

def parse_wikidata(line):
    line=line.strip()
    if not line or line in ('[',']'): return None
    if line.endswith(','): line=line[:-1]
    obj=json.loads(line)
    if not isinstance(obj,dict): return None
    eid=obj.get('id')
    if not isinstance(eid,str) or not LEXEME_RE.fullmatch(eid): return None
    lemmas=obj.get('lemmas')
    if not isinstance(lemmas,dict) or not lemmas: return None
    selected=sorted((k,v.get('value')) for k,v in lemmas.items() if isinstance(v,dict) and isinstance(v.get('value'),str) and v.get('value').strip())
    if not selected: return None
    lang, lemma=selected[0]
    lemma,key=normalized_lemma(lemma)
    if not key: return None
    forms=obj.get('forms')
    senses=obj.get('senses')
    pos=obj.get('lexicalCategory')
    qid=obj.get('language')
    return (code(lang),lemma,key,(pos or '')[:80] if isinstance(pos,str) else '',
            len(senses) if isinstance(senses,list) else 0,
            len(forms) if isinstance(forms,list) else 0,0,eid,
            qid if isinstance(qid,str) and re.fullmatch(r'Q[1-9][0-9]*',qid) else None,lang,None,None,None)

def parse_morph(line,language,delimiter='\t'):
    if delimiter == ',':
        row=next(csv.reader([line]))
    else:
        row=line.rstrip('\r\n').split('\t')
    if len(row)<3 or len(row)>6: return None
    lemma,form,features=row[:3]
    if not (lemma.strip() and form.strip() and features.strip()):return None
    lemma,key=normalized_lemma(lemma)
    if not key:return None
    surface, form_key=normalized_lemma(form)
    if not form_key:return None
    return (code(language),lemma,key,features.split(';',1)[0][:80],0,1,0,None,None,language,surface,form_key,features[:250])

def unimorph_member(zf, language):
    """Backwards-compatible exact canonical selection (v0.2 policy)."""
    choices=[x for x in zf.infolist() if not x.is_dir() and Path(x.filename).name in (language,language+'.tsv')]
    if not choices:return None
    choices.sort(key=lambda x:(Path(x.filename).name!=language,len(x.filename)))
    candidate=choices[0]
    if candidate.file_size > 16*1024**3:
        raise ValueError('Archive ZIP: paradigme trop volumineux pour cette politique')
    return candidate


def unimorph_members(zf, language):
    """Select data-bearing members without counting train/dev/test or auxiliaries twice.

    v0.3 only expands selection when there is no canonical bare-code member.
    For ckb, two distinct orthographies are retained as observations (not uniques).
    """
    primary=unimorph_member(zf,language)
    if primary is not None:
        return [(primary,'tsv')]
    result=[]
    for x in zf.infolist():
        if x.is_dir():continue
        path=x.filename.replace('\\','/')
        parts=path.split('/')
        if path.startswith('/') or '..' in parts:continue
        filename=parts[-1]
        lower=filename.lower()
        fmt=None
        if language=='slk' and lower=='slk.xz':fmt='xz'
        elif language=='fin' and lower in ('fin.1','fin.2'):fmt='tsv'
        elif language=='ckb' and lower in ('ckb-arab-large.tsv','ckb-latn-large.tsv'):fmt='tsv'
        elif lower==language+'.csv':fmt='csv'
        elif re.fullmatch(re.escape(language)+r'-[a-z0-9-]+',lower):fmt='tsv'
        if fmt:
            if x.file_size>16*1024**3:raise ValueError('ZIP: membre depasse 16 Gio')
            result.append((x,fmt))
    return sorted(result,key=lambda t:t[0].filename)


def iter_member_lines(info):
    """Return (internal_member, format, text) without extracting or writing source files."""
    path=info['path']; kind=info['kind']
    if kind=='kaikki':
        opener = gzip.open if path.name.endswith('.gz') else open
        with opener(path,'rt',encoding='utf-8',errors='replace') as stream:
            for line in stream:yield '', 'jsonl', line
    elif kind=='wikidata':
        with bz2.open(path,'rt',encoding='utf-8',errors='replace') as stream:
            for line in stream:yield '', 'jsonl', line
    else:
        with zipfile.ZipFile(path) as zf:
            for member,fmt in unimorph_members(zf,info['edition']):
                with zf.open(member) as raw:
                    if fmt=='xz':
                        with lzma.LZMAFile(raw) as decoded:
                            size=0
                            for row in decoded:
                                size+=len(row)
                                if size>16*1024**3:raise ValueError('XZ: decompression depasse 16 Gio')
                                yield member.filename,fmt,row.decode('utf-8','replace')
                    else:
                        for row in raw:
                            yield member.filename,fmt,row.decode('utf-8','replace')


def iter_lines(info):
    """Legacy convenience wrapper for integrations reading textual lines."""
    for _member,_fmt,line in iter_member_lines(info):yield line


def supported_repair_candidate(info):
    if info['kind']!='unimorph':return False
    with zipfile.ZipFile(info['path']) as zf:
        return bool(unimorph_members(zf,info['edition']))


def connect(dbpath: Path):
    dbpath.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(dbpath,timeout=30)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=NORMAL')
    con.execute('PRAGMA busy_timeout=30000')
    con.executescript(SCHEMA)
    ver=con.execute("SELECT value FROM metadata WHERE key='schema'").fetchone()
    if ver and ver[0]!='1': raise ValueError('Version SQLite incompatible')
    con.execute("INSERT OR IGNORE INTO metadata(key,value) VALUES ('schema','1')")
    con.commit()
    return con

def ensure_source(con, info,refresh=False,repair_no_data=False):
    existing=con.execute('SELECT id,size_bytes,mtime_ns,status,cursor_lines FROM source_files WHERE relative_path=?',(info['relative'],)).fetchone()
    if existing:
        sid,size,mtime,status,cursor=existing
        if (size,mtime)!=(info['size'],info['mtime']):
            if not refresh:
                with con:con.execute("UPDATE source_files SET status='stale',error='Source size/mtime changed: run --refresh-changed to rebuild derived rows' WHERE id=?",(sid,))
                return sid,'changed'
            with con:
                con.execute('DELETE FROM source_members WHERE source_id=?',(sid,))
                con.execute('DELETE FROM language_stats WHERE source_id=?',(sid,))
                con.execute('DELETE FROM entries WHERE source_id=?',(sid,))
                con.execute('DELETE FROM source_files WHERE id=?',(sid,))
        elif status == 'stale':
            if not refresh:return sid,'changed'
            with con:
                con.execute('DELETE FROM source_members WHERE source_id=?',(sid,))
                con.execute('DELETE FROM language_stats WHERE source_id=?',(sid,))
                con.execute('DELETE FROM entries WHERE source_id=?',(sid,))
                con.execute('DELETE FROM source_files WHERE id=?',(sid,))
        elif status=='no_data' and repair_no_data:
            with con:
                con.execute('DELETE FROM source_members WHERE source_id=?',(sid,))
                con.execute('DELETE FROM language_stats WHERE source_id=?',(sid,))
                con.execute('DELETE FROM entries WHERE source_id=?',(sid,))
                con.execute('UPDATE source_files SET status=?,cursor_lines=0,accepted=0,rejected=0,error=NULL,started_at=?,finished_at=NULL WHERE id=?',('processing',utc(),sid))
            return sid,'repair'
        elif status in ('complete','no_data'):
            return sid,'skip'
        else:
            return sid,'resume'
    with con:
        cur=con.execute('INSERT INTO source_files(relative_path,kind,edition,size_bytes,mtime_ns,status,started_at) VALUES (?,?,?,?,?,?,?)',
                        (info['relative'],info['kind'],info['edition'],info['size'],info['mtime'],'processing',utc()))
    return cur.lastrowid,'new'

def commit_batch(con, sid, buffer, delta, new_cursor):
    if not buffer and not delta['rejected'] and not delta['accepted'] and new_cursor==delta['old_cursor']:
        return
    aggregates=defaultdict(lambda:[0,0,0,0])
    for row in buffer:
        agg=aggregates[row[2]]
        agg[0]+=1
        agg[1]+=row[6]
        agg[2]+=row[7]
        agg[3]+=row[8]
    with con:
        if buffer:
            con.executemany('INSERT INTO entries(source_id,source_line,language_code,lemma,lemma_key,pos,sense_observations,form_observations,translation_observations,external_id,language_qid,source_language_code,form_surface,form_key,grammatical_features) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',buffer)
            con.executemany('''INSERT INTO language_stats(source_id,language_code,lemma_observations,sense_observations,form_observations,translation_observations) VALUES(?,?,?,?,?,?)
                ON CONFLICT(source_id,language_code) DO UPDATE SET
                lemma_observations=lemma_observations+excluded.lemma_observations,
                sense_observations=sense_observations+excluded.sense_observations,
                form_observations=form_observations+excluded.form_observations,
                translation_observations=translation_observations+excluded.translation_observations''',
                [(sid, lang,*values) for lang,values in aggregates.items()])
        con.execute('''UPDATE source_files SET cursor_lines=?,accepted=accepted+?,rejected=rejected+?,status='processing',error=NULL
            WHERE id=?''',(new_cursor,delta['accepted'],delta['rejected'],sid))

def run_one(con,info,*, batch_size=2500, max_lines=None, refresh=False, repair_no_data=False, min_free_gb=0.0, quiet=False):
    sid, mode=ensure_source(con,info,refresh=refresh,repair_no_data=repair_no_data)
    if mode in ('skip','changed'):
        if not quiet:print(f'[{mode.upper()}] {info["relative"]}',flush=True)
        return mode
    old=con.execute('SELECT cursor_lines FROM source_files WHERE id=?',(sid,)).fetchone()[0]
    if not quiet:print(f'[{mode.upper()}] {info["relative"]} (reprise a la ligne {old})',flush=True)
    buffer=[];delta=dict(accepted=0,rejected=0,old_cursor=old)
    cursor=old
    try:
        stream=iter_member_lines(info)
        current_member=None
        member_first_line=None
        last_member_cursor=None
        for idx,(member,fmt,line) in enumerate(stream, start=1):
            if idx<=old: continue
            if member and member!=current_member:
                if current_member is not None:
                    with con:con.execute('UPDATE source_members SET end_line=? WHERE source_id=? AND member_path=?',(idx-1,sid,current_member))
                current_member=member
                member_first_line=idx
                with con:con.execute('''INSERT INTO source_members(source_id,member_path,member_format,start_line,end_line)
                    VALUES(?,?,?,?,?) ON CONFLICT(source_id,member_path) DO UPDATE SET
                    member_format=excluded.member_format,
                    end_line=MAX(source_members.end_line,excluded.end_line)''' ,(sid,member,fmt,idx,idx))
            if max_lines is not None and idx>max_lines:break
            cursor=idx
            try:
                if len(line)>8_000_000:raise ValueError('ligne hors limite')
                if info['kind']=='kaikki': parsed=parse_kaikki(line)
                elif info['kind']=='wikidata': parsed=parse_wikidata(line)
                else: parsed=parse_morph(line,info['edition'],delimiter=',' if fmt=='csv' else '\t')
                if parsed:
                    buffer.append((sid,idx,*parsed))
                    delta['accepted']+=1
                else: delta['rejected']+=1
            except (ValueError,TypeError,UnicodeError,json.JSONDecodeError,csv.Error):
                delta['rejected']+=1
            if idx%batch_size==0:
                commit_batch(con,sid,buffer,delta,cursor)
                if current_member is not None:
                    with con:con.execute('UPDATE source_members SET end_line=? WHERE source_id=? AND member_path=?',(cursor,sid,current_member))
                buffer=[];delta=dict(accepted=0,rejected=0,old_cursor=cursor)
                if min_free_gb and idx%100_000==0 and shutil.disk_usage(info['path']).free < min_free_gb*1024**3:
                    raise RuntimeError('Espace disque faible durant le traitement; dernier checkpoint conserve')
                if not quiet and idx%250_000==0:print(f'  {info["edition"]}: {idx:,} lignes lues',flush=True)
        commit_batch(con,sid,buffer,delta,cursor)
        if current_member is not None:
            with con:con.execute('UPDATE source_members SET end_line=? WHERE source_id=? AND member_path=?',(cursor,sid,current_member))
        endstat=info['path'].stat()
        if endstat.st_size!=info['size'] or endstat.st_mtime_ns!=info['mtime']:
            raise RuntimeError('Source modifiee durant le traitement')
        if max_lines is not None and cursor>=max_lines:
            status='partial'
        else:
            count=con.execute('SELECT accepted FROM source_files WHERE id=?',(sid,)).fetchone()[0]
            status='complete' if count else 'no_data'
        with con:con.execute('UPDATE source_files SET status=?,finished_at=? WHERE id=?',(status,utc(),sid))
        if not quiet:print(f'[{status.upper()}] {info["edition"]}',flush=True)
        return status
    except (Exception,KeyboardInterrupt) as exc:
        # Existing chunk commits survive interruption; uncommitted buffer is deliberately discarded.
        with con:con.execute('UPDATE source_files SET status=?,error=?,finished_at=? WHERE id=?',('error',str(exc)[:600],utc(),sid))
        if not quiet:print(f'[ERROR] {info["relative"]}: {exc}',file=sys.stderr,flush=True)
        if isinstance(exc,KeyboardInterrupt):raise
        return 'error'

def rows_dict(con,query,params=()):
    cursor=con.execute(query,params)
    fields=[x[0] for x in cursor.description]
    for row in cursor:
        yield dict(zip(fields,row))

def atomic_json(path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.partial-'+str(os.getpid()))
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2)
        f.write('\n')
    os.replace(tmp,path)

def atomic_csv(path, headers, records):
    tmp=path.with_name(path.name+'.partial-'+str(os.getpid()))
    with tmp.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=headers)
        writer.writeheader()
        for row in records:writer.writerow(row)
    os.replace(tmp,path)

def report(con,root,workdir):
    workdir.mkdir(parents=True,exist_ok=True)
    stats=list(rows_dict(con,'''SELECT l.language_code,
        SUM(l.lemma_observations) lemma_observations,
        SUM(l.sense_observations) sense_observations,
        SUM(l.form_observations) form_observations,
        SUM(l.translation_observations) translation_observations,
        COUNT(DISTINCT s.id) source_files
        FROM language_stats l JOIN source_files s ON s.id=l.source_id
        GROUP BY l.language_code ORDER BY l.language_code'''))
    source_data=list(rows_dict(con,'''SELECT relative_path,kind,edition,size_bytes,status,cursor_lines,accepted,rejected,
        COALESCE(error,'') error FROM source_files ORDER BY relative_path'''))
    for item in source_data:item['sha256_verified']=False
    members=list(rows_dict(con,'''SELECT s.edition,s.relative_path,m.member_path,m.member_format,
        m.start_line,m.end_line FROM source_members m JOIN source_files s ON s.id=m.source_id
        ORDER BY s.relative_path,m.start_line'''))
    totals={key:sum(int(row[key]) for row in stats) for key in ('lemma_observations','sense_observations','form_observations','translation_observations')}
    snapshot={
       'profile':'encyklopedia.lexical-source-index/candidate-v1','generated_at':utc(),
       'data_root':str(root),'database':str(workdir/'lexical.sqlite3'),
       'number_of_source_files':len(source_data),'number_of_observed_language_codes':len(stats),
       'sources_by_status':dict(Counter(row['status'] for row in source_data)),
       'totals':totals,'deduplication':'No cross-source or cross-edition semantic deduplication; counts are observations, not unique lemmas',
       'source_sha256_verified':False,'source_licenses_reviewed':False,
       'language_code_mapping':'ISO-639 alpha3 to alpha2 candidate aliases; source_language_code retained',
       'canonical_dictionary':False,'wikidata_exactmatch_created':False,'published':False,
       'integration_to_dik':'candidate handoff only; no writes to diK registry or Kristal identity graph',
       'languages_report':str(workdir/'languages.csv'),
       'sources_report':str(workdir/'sources.csv'),
       'source_members_report':str(workdir/'source_members.csv'),
       'human_report':str(workdir/'RAPPORT_LEXICAL.md')
    }
    headers_l=['language_code','lemma_observations','sense_observations','form_observations','translation_observations','source_files']
    headers_s=['relative_path','kind','edition','size_bytes','status','cursor_lines','accepted','rejected','error','sha256_verified']
    atomic_csv(workdir/'languages.csv',headers_l,stats)
    atomic_csv(workdir/'sources.csv',headers_s,source_data)
    atomic_csv(workdir/'source_members.csv',['edition','relative_path','member_path','member_format','start_line','end_line'],members)
    report_lines=[
        '# Inventaire lexical EncyKlopedia — index candidat',
        '',
        f'Généré : {snapshot["generated_at"]}',
        '',
        f'Archives sources recensées : **{len(source_data)}**',
        f'Codes de langues observés : **{len(stats)}** (normalisation candidate alpha3 → alpha2)',
        '',
        'Les chiffres ci-dessous sont des **observations** et non des lemmes uniques ou des contenus approuvés.',
        '',
        '| Mesure | Total |', '|---|---:|',
    ]
    report_lines.extend([f'| {name} | {count:,} |' for name,count in totals.items()])
    report_lines.extend(['','## État des sources','', '| État | Fichiers |', '|---|---:|'])
    report_lines.extend([f'| {name} | {num} |' for name,num in sorted(snapshot['sources_by_status'].items())])
    report_lines.extend(['','## Langues ayant le plus d’observations','',
                         '| Code | Lemmes observés | Sens observés | Formes observées | Traductions observées |',
                         '|---|---:|---:|---:|---:|'])
    for x in sorted(stats,key=lambda row:row['lemma_observations'],reverse=True)[:30]:
        report_lines.append(f'| {x["language_code"]} | {x["lemma_observations"]:,} | {x["sense_observations"]:,} | {x["form_observations"]:,} | {x["translation_observations"]:,} |')
    report_lines.extend(['','## Gouvernance','',
                         '- Données brutes sur `10_sources/lexical` : conservées, lecture seule.',
                         '- Index de travail sur `30_working/lexical/harvester/index-v1` : dérivé, non canonique.',
                         '- Données non révisées, droits et licences non validés.',
                         '- Pas de création de KQ/KP ni de correspondance `exactMatch`.',
                         '- Les fichiers de statut `partial`, `error`, `stale` ne sont pas une couverture complète.',
                         '- La provenance interne des ZIP UniMorph réparés est conservée dans `source_members.csv`.',
                         '- Un fichier UniMorph `no_data` n’équivaut pas à une langue couverte.',
                         ''])
    report_file=workdir/'RAPPORT_LEXICAL.md'
    temp_report=report_file.with_name(report_file.name+'.partial-'+str(os.getpid()))
    temp_report.write_text('\n'.join(report_lines),encoding='utf-8')
    os.replace(temp_report,report_file)
    atomic_json(workdir/'latest.json',snapshot)
    atomic_json(workdir/'dik-source-handoff.candidate.json', {
        'profile':'encyklopedia.to-dik.lexical-candidate-handoff/0.1',
        'generated_at':snapshot['generated_at'],'data_root':str(root),
        'source_index_database':str(workdir/'lexical.sqlite3'),
        'language_stats_file':str(workdir/'languages.csv'),
        'source_stats_file':str(workdir/'sources.csv'),
        'status':'unreviewed_candidate','requires_license_review':True,
        'requires_identity_crosswalk_review':True,
        'may_be_published':False,
        'warning':'This document is not a normative diK/Framework v11 export.'})
    return snapshot

@contextmanager
def exclusive_lock(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(path,os.O_RDWR|os.O_CREAT,0o600)
    try:
        os.lseek(fd,0,os.SEEK_SET)
        if os.read(fd,1)!=b'1':
            os.lseek(fd,0,os.SEEK_SET);os.write(fd,b'1');os.ftruncate(fd,1)
        os.lseek(fd,0,os.SEEK_SET)
        if os.name=='nt':
            import msvcrt
            try:msvcrt.locking(fd,msvcrt.LK_NBLCK,1)
            except OSError:raise RuntimeError('Indexation deja active (verrou Windows)')
        else:
            import fcntl
            try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise RuntimeError('Indexation deja active (verrou)')
        yield
    finally:
        if os.name=='nt':
            import msvcrt
            try:os.lseek(fd,0,os.SEEK_SET);msvcrt.locking(fd,msvcrt.LK_UNLCK,1)
            except OSError:pass
        os.close(fd)

def main(argv=None):
    parser=argparse.ArgumentParser(description='Index lexical candidate: code C:, archives D:, index SQLite D:')
    parser.add_argument('command',choices=['plan','run','repair','status','lookup'])
    parser.add_argument('--data-root',default=os.environ.get('ENCYK_DATA_ROOT',str(DATA_DEFAULT) if DATA_DEFAULT else None))
    parser.add_argument('--only',default='kaikki,unimorph,wikidata',help='Comma-separated source types')
    parser.add_argument('--refresh-changed',action='store_true',help='Rebuild DERIVED entries for sources whose size/mtime changed')
    parser.add_argument('--max-lines-per-source',type=int,help='Pilot only: limit rows scanned per input file (marks partial)')
    parser.add_argument('--min-free-gb',type=float,default=5.0,help='Stop if free space below this threshold')
    parser.add_argument('--query',help='Lemma to lookup (status lookup only)')
    parser.add_argument('--language',help='Language code for lookup, e.g. fr')
    parser.add_argument('--match',choices=['lemma','form'],default='lemma',help='Search lemma or UniMorph inflected form')
    parser.add_argument('--limit',type=int,default=20,help='Max lookup results (1..200)')
    args=parser.parse_args(argv)
    if not args.data_root:parser.error('Indiquer --data-root ou ENCYK_DATA_ROOT')
    root=valid_lake(Path(args.data_root))
    kinds={x.strip() for x in args.only.split(',') if x.strip()}
    if args.command=='repair':kinds={'unimorph'}
    if not kinds or not kinds <= ALLOWED_KINDS:parser.error('Valeur --only invalide')
    workdir=root/SUBDIR
    dbpath=workdir/'lexical.sqlite3'
    if args.command=='plan':
        files=source_candidates(root,kinds)
        sizes=Counter(x['kind'] for x in files)
        print(json.dumps({'data_root':str(root),'source_files':len(files),'by_kind':dict(sizes),
            'bytes_compressed':sum(x['size'] for x in files),'write_area':str(workdir),
            'raw_sources_untouched':True,'no_network':True,'run_command':'run',
            'note':'ZIP UniMorph sans paradigme exploitable restent no_data; comptages = observations non uniques.'},ensure_ascii=False,indent=2))
        return 0
    if args.command in ('status','lookup') and not dbpath.is_file():
        print('Aucun index encore cree. Executer: run')
        return 0 if args.command=='status' else 1
    if args.command=='lookup':
        if not args.query:parser.error('--query requis pour lookup')
        if not 1<=args.limit<=200:parser.error('--limit de 1 a 200')
        con=sqlite3.connect(f'file:{dbpath.as_posix()}?mode=ro',uri=True)
        lemma,key=normalized_lemma(args.query)
        lang=code(args.language) if args.language else None
        sql='''SELECT s.kind,s.edition,s.relative_path,e.source_line,e.language_code,e.lemma,e.pos,
                  e.sense_observations,e.form_observations,e.translation_observations,e.external_id,e.source_language_code
                  FROM entries e JOIN source_files s ON s.id=e.source_id
                  WHERE e.lemma_key=?'''
        params=[key]
        if lang:sql+=' AND e.language_code=?';params.append(lang)
        sql+=' ORDER BY e.language_code,e.id LIMIT ?';params.append(args.limit)
        results=list(rows_dict(con,sql,params))
        print(json.dumps({'matches':results,'count':len(results),'canonical':False},ensure_ascii=False,indent=2))
        con.close()
        return 0
    if args.command=='status':
        con=sqlite3.connect(f'file:{dbpath.as_posix()}?mode=ro',uri=True)
        data=dict(Counter(x[0] for x in con.execute('SELECT status FROM source_files')))
        total=con.execute('SELECT COALESCE(SUM(accepted),0) FROM source_files').fetchone()[0]
        print(json.dumps({'data_root':str(root),'database':str(dbpath),'source_statuses':data,
            'accepted_observations':total,'reports':str(workdir/'latest.json'),
            'notes':'Partial and error sources can be resumed by run; no publication'},ensure_ascii=False,indent=2))
        con.close();return 0
    if args.max_lines_per_source is not None and args.max_lines_per_source < 1:parser.error('--max-lines-per-source doit etre positif')
    if not 0 <= args.min_free_gb <= 100000:parser.error('--min-free-gb invalide')
    files=source_candidates(root,kinds)
    if not files:raise RuntimeError('Aucune archive supportee trouvee; aucune ecriture')
    if args.command=='repair' and not dbpath.is_file():
        raise RuntimeError('Index existant introuvable : ne pas executer une reparation sans index initial.')
    if shutil.disk_usage(root).free < args.min_free_gb*1024**3:
        raise RuntimeError(f'Libre insuffisant sur D: (< {args.min_free_gb:g} Gio). Rien ne sera modifie.')
    with exclusive_lock(workdir/'lexical-index.lock'):
        con=connect(dbpath)
        try:
            runresults=Counter()
            if args.command=='repair':
                existing={relative:status for relative,status in con.execute('SELECT relative_path,status FROM source_files')}
                files=[info for info in files if existing.get(info['relative']) in ('no_data','error','partial')]
                print(f'[REPARATION] {len(files)} source(s) UniMorph inachevee(s) detectee(s), analyse selective.',flush=True)
            for idx,info in enumerate(files,start=1):
                if args.command=='repair':
                    try:
                        recognized=supported_repair_candidate(info)
                    except (OSError,zipfile.BadZipFile,ValueError) as exc:
                        print(f'[ARCHIVE_NON_LISIBLE] {info["edition"]}: {exc}',file=sys.stderr,flush=True)
                        runresults['error']+=1
                        continue
                    if not recognized:
                        print(f'[NO_DATA_CONFIRME] {info["edition"]}: aucun paradigme reconnu; archive intacte',flush=True)
                        runresults['no_data_confirmed']+=1
                        continue
                if shutil.disk_usage(root).free < args.min_free_gb*1024**3:
                    print('ESPACE DISQUE FAIBLE: arret sans perte des fichiers sources',file=sys.stderr)
                    break
                print(f'({idx}/{len(files)})',end=' ',flush=True)
                mode=run_one(con,info,max_lines=args.max_lines_per_source,refresh=args.refresh_changed,
                             repair_no_data=(args.command=='repair'),min_free_gb=args.min_free_gb)
                runresults[mode]+=1
            snapshot=report(con,root,workdir)
            print(json.dumps({'run_results':dict(runresults),'catalog':snapshot},ensure_ascii=False,indent=2))
            return 1 if runresults['error'] or runresults['changed'] else 0
        finally:con.close()

if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:
        print('Interrompu. Dernier checkpoint conserve; relancer exactement la commande.',file=sys.stderr)
        sys.exit(130)
    except Exception as exc:
        print(f'[indexer] {type(exc).__name__}: {exc}',file=sys.stderr)
        sys.exit(2)
