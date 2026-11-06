#!/usr/bin/env python3
"""EncyKlopedia DIK-LEX-1 v0.6: source-anchored semantic evidence, never automatic matching.

Input index + v0.5 reconciliation databases and original archives are READ-ONLY.
Output is isolated on the data disk. All results are unapproved candidates, not diK imports.
Only v0.5 sampled source-line anchors are enriched; this is NOT exhaustive sense extraction.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
from collections import Counter
from contextlib import closing
from pathlib import Path

from lexical_indexer import (valid_lake, exclusive_lock, atomic_json, atomic_csv, utc,
                             iter_member_lines, parse_kaikki, parse_wikidata, parse_morph)
from quality_audit import db_fingerprint, readonly_connection
from dik_reconciliation import OUTPUT as V05_OUTPUT, safe_lang_filename

PROFILE = 'encyklopedia.dik-lex1-anchored-evidence/candidate-v0.6'
OUTPUT = Path('30_working/lexical/harvester/dik-enrichment-v1')
INDEX = Path('30_working/lexical/harvester/index-v1/lexical.sqlite3')
SQLITE_V05 = V05_OUTPUT / 'reconciliation.sqlite3'
FAMILIES = ('kaikki', 'unimorph', 'wikidata')
MAX_SENSES = 24
MAX_FORMS = 24
MAX_TRANSLATIONS = 24
MAX_GLOSSES = 4
TEXT_LIMIT = 480
SCHEMA = '''
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS staged_languages(language TEXT PRIMARY KEY, candidate_count INTEGER NOT NULL, anchors_added INTEGER NOT NULL, staged_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS anchors(
  source_id INTEGER NOT NULL, source_line INTEGER NOT NULL,
  candidate_id TEXT NOT NULL, language TEXT NOT NULL, lemma_key TEXT NOT NULL,
  PRIMARY KEY(source_id,source_line,candidate_id));
CREATE INDEX IF NOT EXISTS ix_anchors_candidate ON anchors(candidate_id);
CREATE TABLE IF NOT EXISTS source_progress(
  source_id INTEGER PRIMARY KEY, status TEXT NOT NULL DEFAULT 'queued',
  cursor_line INTEGER NOT NULL DEFAULT 0, anchors_found INTEGER NOT NULL DEFAULT 0,
  anchors_missing INTEGER NOT NULL DEFAULT 0, errors INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL, detail TEXT);
CREATE TABLE IF NOT EXISTS evidence(
  source_id INTEGER NOT NULL, source_line INTEGER NOT NULL, candidate_id TEXT NOT NULL,
  language TEXT NOT NULL, family TEXT NOT NULL, status TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  PRIMARY KEY(source_id,source_line,candidate_id));
CREATE INDEX IF NOT EXISTS ix_evidence_candidate ON evidence(candidate_id);
CREATE INDEX IF NOT EXISTS ix_evidence_language_candidate ON evidence(language,candidate_id);
CREATE TABLE IF NOT EXISTS exports(
 language TEXT PRIMARY KEY, sha256 TEXT NOT NULL, records INTEGER NOT NULL,
 evidence_records INTEGER NOT NULL, exported_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS review_tiers(
 language TEXT NOT NULL, tier TEXT NOT NULL, candidates INTEGER NOT NULL,
 PRIMARY KEY(language,tier));
'''


def connect_ro(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f'Entrée absente : {path}')
    db = sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=30)
    db.execute('PRAGMA query_only=ON')
    db.execute('PRAGMA busy_timeout=30000')
    return db


def fixture_checks(index, recon):
    needed = {'entries', 'source_files', 'language_stats'}
    tabs = {r[0] for r in index.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not needed <= tabs:
        raise ValueError('Index lexical incomplet')
    if not {'candidates', 'completed_languages', 'meta'} <= {r[0] for r in recon.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
        raise ValueError('Conciliation v0.5 absente ou schéma inattendu')
    source_fp = db_fingerprint(index)
    expected = recon.execute("SELECT v FROM meta WHERE k='index_fingerprint'").fetchone()
    if not expected or expected[0] != source_fp:
        raise RuntimeError('Empreinte du catalogue index-v1 différente de la v0.5 : arrêt protecteur')
    return source_fp


def open_state(path, fingerprint):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=60)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA synchronous=NORMAL')
    db.execute('PRAGMA busy_timeout=60000')
    db.execute('PRAGMA cache_size=-65536')
    db.executescript(SCHEMA)
    old = db.execute("SELECT v FROM meta WHERE k='index_fingerprint'").fetchone()
    ver = db.execute("SELECT v FROM meta WHERE k='profile'").fetchone()
    if (old and old[0] != fingerprint) or (ver and ver[0] != PROFILE):
        db.close()
        raise RuntimeError('Enrichissement lié à une autre version des données; utiliser un nouveau dossier')
    with db:
        db.execute("INSERT OR IGNORE INTO meta(k,v) VALUES('index_fingerprint',?)", (fingerprint,))
        db.execute("INSERT OR IGNORE INTO meta(k,v) VALUES('profile',?)", (PROFILE,))
    return db


def candidate_languages(recon):
    return [r[0] for r in recon.execute('SELECT language FROM completed_languages ORDER BY language')]


def staged_count(db):
    return db.execute('SELECT COUNT(*) FROM staged_languages').fetchone()[0]


def stage_anchors(recon, db, langs, valid_source_ids, *, min_free_gb=3.0):
    """Stage source line references from v0.5; commit each language atomically.

    A pilot can be expanded to the whole world later: sources touched by new anchors
    are queued for a fresh scan. Existing evidence is retained and de-duplicated.
    """
    for n, lang in enumerate(langs, 1):
        if n%50==1 and min_free_gb and shutil.disk_usage(db.execute('PRAGMA database_list').fetchone()[2]).free < min_free_gb*1024**3:
            raise RuntimeError('Espace D: insuffisant pendant la préparation des ancrages (dernières langues conservées)')
        if db.execute('SELECT 1 FROM staged_languages WHERE language=?', (lang,)).fetchone():
            if n % 200 == 0: print(f'STAGE|{n}|{len(langs)}|existing', flush=True)
            continue
        count = 0
        added = 0
        touched = set()
        db.execute('BEGIN IMMEDIATE')
        try:
            cursor = recon.execute('SELECT candidate_id,lemma_key,provenance_json FROM candidates WHERE language=?', (lang,))
            for cid, key, doc in cursor:
                count += 1
                proofs = json.loads(doc).get('source_observations_sample') or {}
                for family in FAMILIES:
                    for obs in proofs.get(family, []):
                        sid, line = obs.get('source_id'), obs.get('source_line')
                        if not isinstance(sid, int) or sid not in valid_source_ids or not isinstance(line, int) or line < 1:
                            continue
                        before = db.total_changes
                        db.execute('INSERT OR IGNORE INTO anchors(source_id,source_line,candidate_id,language,lemma_key) VALUES (?,?,?,?,?)',
                                   (sid, line, cid, lang, key))
                        if db.total_changes > before:
                            added += 1
                            touched.add(sid)
            db.execute('INSERT INTO staged_languages(language,candidate_count,anchors_added,staged_at) VALUES (?,?,?,?)',
                       (lang, count, added, utc()))
            for sid in touched:
                db.execute('''INSERT INTO source_progress(source_id,status,cursor_line,updated_at)
                              VALUES (?,'queued',0,?) ON CONFLICT(source_id) DO UPDATE SET
                              status='queued',cursor_line=0,anchors_found=0,anchors_missing=0,errors=0,updated_at=excluded.updated_at,detail='anchors_added' ''',
                           (sid, utc()))
            db.commit()
        except BaseException:
            db.rollback()
            raise
        if count or n % 100 == 0:
            print(f'STAGE|{n}|{len(langs)}|{lang}|candidates={count}|anchors={added}', flush=True)


def clip(value, limit=TEXT_LIMIT):
    if isinstance(value, str):
        return value[:limit]
    return None


def string_list(value, max_len=MAX_GLOSSES):
    if isinstance(value, str):
        return [clip(value)] if value else []
    if isinstance(value, list):
        return [clip(v) for v in value[:max_len] if isinstance(v, str) and v]
    return []


def wikidata_mono(value, max_items=MAX_GLOSSES):
    if not isinstance(value, dict):
        return []
    out = []
    for lang, item in sorted(value.items())[:max_items]:
        if isinstance(item, dict) and isinstance(item.get('value'), str):
            out.append({'language': str(lang)[:40], 'value': clip(item['value'])})
    return out


def safe_tags(value, n=12):
    return [clip(v, 80) for v in value[:n] if isinstance(v, str)] if isinstance(value, list) else []


def extract_kaikki(obj):
    senses = obj.get('senses') if isinstance(obj.get('senses'), list) else []
    forms = obj.get('forms') if isinstance(obj.get('forms'), list) else []
    translations = obj.get('translations') if isinstance(obj.get('translations'), list) else []
    payload = {'word': clip(obj.get('word')), 'language_code':clip(obj.get('lang_code'),40),
               'pos':clip(obj.get('pos'),80), 'raw_sense_count':len(senses),
               'raw_form_count':len(forms), 'raw_translation_count':len(translations),
               'senses':[], 'forms':[], 'translations':[], 'ids_are_external':True}
    for s in senses[:MAX_SENSES]:
        if isinstance(s, dict):
            payload['senses'].append({'glosses':string_list(s.get('glosses')),
                'raw_glosses':string_list(s.get('raw_glosses')),
                'sense_id':clip(s.get('senseid') or s.get('id'),160),
                'tags':safe_tags(s.get('tags')),
                'topics':safe_tags(s.get('topics'))})
    for f in forms[:MAX_FORMS]:
        if isinstance(f, dict):
            payload['forms'].append({'form':clip(f.get('form')),'tags':safe_tags(f.get('tags'))})
    for t in translations[:MAX_TRANSLATIONS]:
        if isinstance(t, dict):
            payload['translations'].append({'word':clip(t.get('word')),
                'language_code':clip(t.get('code') or t.get('lang_code'),40),
                'sense_label':clip(t.get('sense'))})
    payload['truncation'] = {'senses':len(senses)>MAX_SENSES,'forms':len(forms)>MAX_FORMS,
                             'translations':len(translations)>MAX_TRANSLATIONS}
    return payload


def extract_wikidata(obj):
    senses = obj.get('senses') if isinstance(obj.get('senses'), list) else []
    forms = obj.get('forms') if isinstance(obj.get('forms'), list) else []
    payload = {'lexeme_id':clip(obj.get('id'),64),
               'language_qid':clip(obj.get('language'),64),
               'lexical_category_qid':clip(obj.get('lexicalCategory'),64),
               'lemmas':wikidata_mono(obj.get('lemmas'),32),
               'raw_sense_count':len(senses),'raw_form_count':len(forms),
               'senses':[],'forms':[],'ids_are_external':True}
    for s in senses[:MAX_SENSES]:
        if isinstance(s, dict):
            payload['senses'].append({'sense_id':clip(s.get('id'),100),
                                      'glosses':wikidata_mono(s.get('glosses'),12),
                                      'claim_properties_sample':list(sorted(s.get('claims',{})))[:12] if isinstance(s.get('claims'),dict) else []})
    for f in forms[:MAX_FORMS]:
        if isinstance(f, dict):
            payload['forms'].append({'form_id':clip(f.get('id'),100),
                                     'representations':wikidata_mono(f.get('representations'),12),
                                     'grammatical_feature_qids':safe_tags(f.get('grammaticalFeatures'),24)})
    payload['truncation'] = {'senses':len(senses)>MAX_SENSES, 'forms':len(forms)>MAX_FORMS,
                             'lemmas':len(obj.get('lemmas',{}))>32 if isinstance(obj.get('lemmas'),dict) else False}
    return payload


def extract_morph(line, fmt):
    if fmt == 'csv':
        row = next(csv.reader([line]))
    else:
        row = line.rstrip('\r\n').split('\t')
    if len(row)<3 or not all(isinstance(x,str) and x.strip() for x in row[:3]):
        raise ValueError('Paradigme UniMorph non reconnu')
    return {'lemma':clip(row[0]),'form':clip(row[1]),'features':clip(row[2],250),
            'additional_columns':[clip(v,250) for v in row[3:6]],
            'glosses_available':False,'sense_ids_available':False}


def parse_anchor(kind, line, fmt):
    if len(line)>8_000_000:
        raise ValueError('Ligne source trop longue (8 Mo)')
    if kind == 'kaikki':
        obj=json.loads(line)
        parsed=parse_kaikki(line)
        return parsed,extract_kaikki(obj)
    if kind == 'wikidata':
        obj=json.loads(line.rstrip().rstrip(','))
        parsed=parse_wikidata(line)
        return parsed,extract_wikidata(obj)
    if kind == 'unimorph':
        return None,extract_morph(line,fmt)
    raise ValueError('Famille inconnue: '+kind)


def source_catalog(index):
    result={}
    for r in index.execute('SELECT id,relative_path,kind,edition,size_bytes,mtime_ns,status FROM source_files ORDER BY id'):
        result[r[0]]={'id':r[0],'relative_path':r[1],'kind':r[2],'edition':r[3],
                       'size_bytes':r[4],'mtime_ns':r[5],'index_status':r[6]}
    return result


def checked_source_path(root, info):
    path=(root/info['relative_path']).resolve()
    if root not in path.parents or not path.is_file():
        raise FileNotFoundError(f'Source hors racine ou manquante : {info["relative_path"]}')
    st=path.stat()
    if st.st_size!=info['size_bytes'] or st.st_mtime_ns!=info['mtime_ns']:
        raise RuntimeError(f'Source modifiée depuis index-v1 : {info["relative_path"]}')
    return path


def process_source(db, root, info, *, batch_lines=25000, min_free_gb=3.0, max_scan_lines=None):
    sid=info['id']
    row=db.execute('SELECT status,cursor_line FROM source_progress WHERE source_id=?',(sid,)).fetchone()
    if not row or row[0]=='complete':return 'skipped'
    old=row[1]
    path=checked_source_path(root,info)
    cursor=db.execute('''SELECT source_line,candidate_id,language,lemma_key FROM anchors
                        WHERE source_id=? AND source_line>? ORDER BY source_line,candidate_id''',(sid,old))
    target=next(cursor,None)
    if not target:
        with db:db.execute("UPDATE source_progress SET status='complete',updated_at=? WHERE source_id=?",(utc(),sid))
        return 'complete'
    size=0;got=0;issues=0
    pending=[]
    last=old
    free_min=int(min_free_gb*1024**3)
    print(f'SCAN|{sid}|{info["kind"]}|{info["edition"]}|cursor={old}',flush=True)
    db.execute("UPDATE source_progress SET status='processing',updated_at=? WHERE source_id=?",(utc(),sid))
    db.commit()

    def checkpoint():
        nonlocal pending
        with db:
            if pending:
                db.executemany('''INSERT OR REPLACE INTO evidence(source_id,source_line,candidate_id,language,family,status,payload_json)
                                  VALUES(?,?,?,?,?,?,?)''',pending)
            db.execute('''UPDATE source_progress SET cursor_line=?,anchors_found=anchors_found+?,errors=errors+?,
                          updated_at=?,status='processing' WHERE source_id=?''',
                       (last,got,issues,utc(),sid))
            # Counters are per batch, so call-site resets them.
        pending=[]

    stream_info={'kind':info['kind'],'edition':info['edition'],'path':path}
    reached_limit=False
    scan_count=0
    try:
        batch_found=0;batch_errors=0
        for idx,(member,fmt,line) in enumerate(iter_member_lines(stream_info),1):
            if idx<=old:continue  # Gzip/XZ restart must replay to this offset.
            if target is None:break
            if max_scan_lines is not None and scan_count >= max_scan_lines:
                reached_limit=True;break
            scan_count+=1;last=idx
            if target[0]==idx:
                try:
                    parsed,payload=parse_anchor(info['kind'],line,fmt)
                    error=None
                except (ValueError,TypeError,json.JSONDecodeError,csv.Error,UnicodeError) as ex:
                    parsed=None;payload=None;error=str(ex)[:240]
                while target and target[0]==idx:
                    line_no,cid,lang,key=target
                    mismatch=False
                    if not error:
                        if info['kind']=='unimorph':
                            # Corpus variant: normalized lemma must equal the staged key.
                            from lexical_indexer import normalized_lemma
                            mismatch=normalized_lemma(payload['lemma'])[1]!=key
                        else:
                            mismatch=not parsed or (parsed[0],parsed[2])!=(lang,key)
                    status='parse_error' if error else 'anchor_mismatch' if mismatch else 'observed'
                    if status!='observed':batch_errors+=1
                    record={'profile':PROFILE,'candidate_id':cid,'language':lang,
                         'search_key':key,'source_id':sid,'source_line':idx,
                         'source_member':member or None,
                         'family':info['kind'],'source_relative_path':info['relative_path'],
                         'source_edition':info['edition'],'status':status,
                         'license_reviewed':False,'source_official_sha256_verified':False,
                         'semantic_relationship':None,'sense_alignment_approved':False,
                         'observed_record':payload if status=='observed' else None,
                         'error':error or ('lemma_or_language_changed' if mismatch else None)}
                    pending.append((sid,idx,cid,lang,info['kind'],status,
                                    json.dumps(record,ensure_ascii=False,separators=(',',':'))))
                    batch_found+=1
                    target=next(cursor,None)
            if scan_count % batch_lines == 0:
                got= batch_found; issues=batch_errors
                checkpoint()
                batch_found=0;batch_errors=0;got=0;issues=0
                if scan_count % (batch_lines*8)==0:
                    print(f'PROGRESS|{sid}|line={idx}|anchors={db.execute("SELECT anchors_found FROM source_progress WHERE source_id=?",(sid,)).fetchone()[0]}',flush=True)
                    if free_min and shutil.disk_usage(root).free < free_min:
                        raise RuntimeError('Espace D: libre insuffisant; les checkpoints sont préservés')
        got=batch_found;issues=batch_errors
        checkpoint()
        checked_source_path(root,info)
        if reached_limit:
            state='partial'
        elif target is not None:
            state='unresolved'
        else:state='complete'
        with db:
            db.execute('''UPDATE source_progress SET status=?,anchors_missing=?,updated_at=?,detail=? WHERE source_id=?''',
                       (state,db.execute('SELECT COUNT(*) FROM anchors WHERE source_id=? AND source_line>?',(sid,last)).fetchone()[0],utc(),
                        None if state=='complete' else ('scan_limit' if reached_limit else 'anchors_past_source_eof'),sid))
        print(f'SOURCE_DONE|{sid}|{state}|cursor={last}',flush=True)
        return state
    except BaseException as exc:
        # Batch transactions already committed. Discard uncommitted evidence.
        with db:
            db.execute('UPDATE source_progress SET status=?,updated_at=?,detail=? WHERE source_id=?',
                       ('error',utc(),f'{type(exc).__name__}: {exc}'[:350],sid))
        raise


def export_language(recon, state, lang, outdir):
    """Atomic JSONL export; only candidate ID plus limited, source-anchored evidence."""
    if not state.execute('SELECT 1 FROM staged_languages WHERE language=?',(lang,)).fetchone():
        return None
    count=recon.execute('SELECT COUNT(*) FROM candidates WHERE language=?',(lang,)).fetchone()[0]
    if count==0:
        with state:
            state.execute('INSERT OR REPLACE INTO exports(language,sha256,records,evidence_records,exported_at) VALUES(?,?,?,?,?)',
                          (lang,'no-candidates',0,0,utc()))
        return None
    path=outdir/'evidence'/safe_lang_filename(lang)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f'.partial-{os.getpid()}')
    digest=hashlib.sha256();n=0;ev_count=0;tiers=Counter()
    try:
        with tmp.open('wb') as f:
            for cid,key in recon.execute('SELECT candidate_id,lemma_key FROM candidates WHERE language=? ORDER BY lemma_key',(lang,)):
                evidences=[]
                for (doc,) in state.execute('SELECT payload_json FROM evidence WHERE candidate_id=? ORDER BY source_id,source_line',(cid,)):
                    evidences.append(json.loads(doc))
                ev_count+=len(evidences)
                total_anchors=state.execute('SELECT COUNT(*) FROM anchors WHERE candidate_id=?',(cid,)).fetchone()[0]
                observed=[v for v in evidences if v.get('status')=='observed']
                glosses=False;external_senses=False
                for source in observed:
                    content=source.get('observed_record') or {}
                    if source.get('family')=='kaikki':
                        glosses|=any(s.get('glosses') or s.get('raw_glosses') for s in content.get('senses',[]))
                    if source.get('family')=='wikidata':
                        external_senses|=any(s.get('sense_id') for s in content.get('senses',[]))
                if len(observed)!=total_anchors:
                    tier='incomplete_source_evidence'
                elif glosses and external_senses:
                    tier='glosses_plus_wikidata_sense_ids_for_review'
                elif glosses or external_senses:
                    tier='some_sense_evidence_for_review'
                else:
                    tier='morphology_or_lemma_only'
                tiers[tier]+=1
                row={'profile':PROFILE,'candidate_id':cid,'language':lang,
                     'search_key':key,'evidence_status':'sampled_unreviewed',
                     'raw_source_line_evidence':evidences,
                     'anchors_total':total_anchors,
                     'evidence_captured':len(evidences),
                     'review_tier':tier,'review_tier_is_semantic_decision':False,
                     'semantic_equivalence':None,'manual_sense_review_required':True,
                     'source_license_review_required':True,'may_be_published':False,
                     'limitations':['only_v05_provenance_sample_anchors','glosses_forms_translations_capped',
                                    'not_all_senses_or_lexemes','not_a_normative_dik_import']}
                line=(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
                f.write(line);digest.update(line);n+=1
        if n!=count:raise RuntimeError('Export count mismatch for '+lang)
        os.replace(tmp,path)
        with state:
            state.execute('INSERT OR REPLACE INTO exports(language,sha256,records,evidence_records,exported_at) VALUES(?,?,?,?,?)',
                          (lang,digest.hexdigest(),n,ev_count,utc()))
            state.execute('DELETE FROM review_tiers WHERE language=?',(lang,))
            state.executemany('INSERT INTO review_tiers(language,tier,candidates) VALUES(?,?,?)',
                              [(lang,tier,count) for tier,count in tiers.items()])
    finally:
        if tmp.exists():tmp.unlink()
    return path


def report(root, index, recon, db, outdir, fingerprint, total_langs):
    statuses=dict(db.execute('SELECT status,COUNT(*) FROM source_progress GROUP BY status'))
    n_staged=staged_count(db)
    n_candidates=db.execute('SELECT COALESCE(SUM(candidate_count),0) FROM staged_languages').fetchone()[0]
    n_anchors=db.execute('SELECT COUNT(*) FROM anchors').fetchone()[0]
    n_evidence=db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0]
    n_observed=db.execute("SELECT COUNT(*) FROM evidence WHERE status='observed'").fetchone()[0]
    exports_count=db.execute('SELECT COUNT(*) FROM exports').fetchone()[0]
    tier_counts=dict(db.execute('SELECT tier,SUM(candidates) FROM review_tiers GROUP BY tier'))
    complete=(n_staged==total_langs and all(s=='complete' for s in statuses) and exports_count==total_langs and n_observed==n_anchors)
    manifest={'profile':PROFILE,'generated_at':utc(),'data_root':str(root),
        'source_index_fingerprint':fingerprint,'status':'candidate_evidence_complete' if complete else 'candidate_evidence_partial',
        'languages_total':total_langs,'languages_staged':n_staged,'candidate_keys_staged':n_candidates,
        'source_anchors':n_anchors,'source_anchors_captured':n_evidence,'records_with_usable_evidence':n_observed,
        'source_anchors_unusable_or_missing':n_anchors-n_observed,
        'source_capture_statuses':statuses,'languages_exported':exports_count,
        'review_queue_triage_counts':tier_counts,
        'output_database':str(outdir/'enrichment.sqlite3'),
        'output_shards':str(outdir/'evidence'),
        'read_only_inputs':[str(root/INDEX),str(root/SQLITE_V05),str(root/'10_sources/lexical')],
        'source_license_reviewed':False,'source_official_sha256_verified':False,
        'approved_semantic_equivalences':0,'kq_kp_created':0,'published':False,
        'source_coverage':'v0.5 sampled provenance anchors only; NOT exhaustive senses or all single-family entries',
        'wikidata_L_S_F':'external IDs retained; no automatic mapping to canonical Kristal or GF'}
    atomic_json(outdir/'latest.json',manifest)
    atomic_json(outdir/'dik-enriched-handoff.candidate.json',{
        'profile':'encyklopedia.to-dik.enriched-evidence-candidate/0.6','generated_at':manifest['generated_at'],
        'status':'unreviewed_candidate','source_index_fingerprint':fingerprint,
        'enrichment_db':manifest['output_database'],'evidence_shards':manifest['output_shards'],
        'upstream_v05':str(root/V05_OUTPUT/'dik-review-queue.candidate.json'),
        'license_review_queue':str(root/V05_OUTPUT/'source_license_review_queue.csv'),
        'requires_human_sense_review':True,'requires_license_review':True,
        'requires_external_hash_review':True,'requires_identity_crosswalk_review':True,
        'approved_matches':0,'may_be_published':False,
        'warning':'NOT a normative diK/Framework v11 import; source-anchored evidence only.'})
    source_meta={r[0]:(r[1],r[2],r[3]) for r in index.execute('SELECT id,relative_path,kind,status FROM source_files')}
    rows=[]
    for sid,status,cursor,found,missing,errors,details in db.execute('''SELECT source_id,status,cursor_line,anchors_found,
                 anchors_missing,errors,detail FROM source_progress ORDER BY source_id'''):
        name,kind,idx_state=source_meta[sid]
        rows.append({'source_id':sid,'path':name,'kind':kind,'index_status':idx_state,
                     'capture_status':status,'cursor_line':cursor,'anchors_found':found,
                     'anchors_missing':missing,'errors':errors,'detail':details or ''})
    atomic_csv(outdir/'sources_enrichment.csv',list(rows[0]) if rows else
               ['source_id','path','kind','index_status','capture_status','cursor_line','anchors_found','anchors_missing','errors','detail'],rows)
    human=['# EncyKlopedia → diK — Enrichissement probatoire candidat v0.6','',
      '**NON CANONIQUE — NE PAS PUBLIER.**','','## État','',
      f'- Langues mises en file : {n_staged:,}/{total_langs:,}',f'- Graphies candidates : {n_candidates:,}',
      f'- Ancrages v0.5 : {n_anchors:,}',f'- Ancrages récupérés : {n_evidence:,}',
      f'- Enregistrements source utiles : {n_observed:,}',
      f'- Ancrages non utilisables ou manquants : {n_anchors-n_observed:,}',f'- Statuts des sources : {statuses}',
      f'- Tri de revue (signal, pas décision) : {tier_counts}',
      '', '## Limites méthodologiques','',
      '- Extraction ciblée sur les preuves échantillonnées en v0.5, et non sur tous les sens existants.',
      '- Les définitions, formes, traductions et gloses par entrée sont limitées en volume et marquées si tronquées.',
      '- Les unités L/S/F de Wikidata restent des identifiants EXTERNES ; les traits Q ne deviennent pas des traits GF.',
      '- La graphie commune et les POS ne prouvent PAS une équivalence de sens.',
      '- Tous les candidats sont en attente de revue humaine; licences et empreintes officielles non vérifiées.',
      '- Les données mono-source restent conservées dans index-v1, hors rapprochements de v0.5.',
      '', '## Sorties', '',
      '- enrichment.sqlite3 : ancrages et observations récupérées par source, transactionnelles et reprenables.',
      '- evidence/<lang>.jsonl : fiches candidates avec preuves limitées et SHA-256 par langue.',
      '- sources_enrichment.csv : suivi des sources et anomalies.',
      '- dik-enriched-handoff.candidate.json : transfert NON normatif vers espace de revue diK.', '']
    (outdir/'RAPPORT_ENRICHISSEMENT.md').write_text('\n'.join(human),encoding='utf-8')
    return manifest


def run(root, *, languages=None, batch_lines=25000, min_free_gb=3.0, max_scan_lines=None, output_override=None):
    root=valid_lake(root)
    if batch_lines < 1:raise ValueError('batch_lines doit être positif')
    outdir=output_override.resolve() if output_override else root/OUTPUT
    if root not in outdir.parents:raise ValueError('Sortie hors racine de données')
    if min_free_gb and shutil.disk_usage(root).free < min_free_gb*1024**3:
        raise RuntimeError('Espace disque disponible insuffisant')
    with closing(connect_ro(root/INDEX)) as index, closing(connect_ro(root/SQLITE_V05)) as recon:
        fp=fixture_checks(index,recon)
        known=candidate_languages(recon)
        chosen=sorted(set(languages)) if languages else known
        if not set(chosen)<=set(known):raise ValueError('Codes absents de la conciliation v0.5')
        sources=source_catalog(index)
        if not chosen:raise ValueError('Aucune langue à traiter')
        outdir.mkdir(parents=True,exist_ok=True)
        with exclusive_lock(outdir/'semantic-enrichment.lock'):
            with closing(open_state(outdir/'enrichment.sqlite3',fp)) as db:
                stage_anchors(recon,db,chosen,set(sources),min_free_gb=min_free_gb)
                requested=[r[0] for r in db.execute("SELECT source_id FROM source_progress WHERE status!='complete' ORDER BY source_id")]
                for num,sid in enumerate(requested,1):
                    info=sources[sid]
                    print(f'SOURCE|{num}|{len(requested)}|{info["kind"]}:{info["edition"]}',flush=True)
                    try:
                        process_source(db,root,info,batch_lines=batch_lines,min_free_gb=min_free_gb,max_scan_lines=max_scan_lines)
                    except Exception as exc:
                        print(f'[SOURCE_ERROR] {info["relative_path"]}: {type(exc).__name__}: {exc}',file=sys.stderr,flush=True)
                # Export staged languages: pilot outputs are reused by the worldwide run.
                to_export=[r[0] for r in db.execute('SELECT language FROM staged_languages ORDER BY language')]
                for j,lang in enumerate(to_export,1):
                    if j%50==1 and min_free_gb and shutil.disk_usage(outdir).free < min_free_gb*1024**3:
                        raise RuntimeError('Espace D: insuffisant pendant les exports; reprendre après libération d’espace')
                    # An unchanged, fully exported language can be skipped on normal reruns.
                    ex=db.execute('SELECT sha256 FROM exports WHERE language=?',(lang,)).fetchone()
                    if ex and lang not in chosen:
                        continue
                    export_language(recon,db,lang,outdir)
                    if j%100==0:print(f'EXPORT|{j}|{len(to_export)}',flush=True)
                if db_fingerprint(index)!=fp:
                    raise RuntimeError('Le catalogue index-v1 a changé durant la lecture')
                m=report(root,index,recon,db,outdir,fp,len(known))
                print(json.dumps(m,ensure_ascii=False,indent=2),flush=True)
                if max_scan_lines is None and any(s in ('error','unresolved','stale') for s in m['source_capture_statuses']):
                    raise RuntimeError('Certaines sources ont échoué; voir sources_enrichment.csv. Reprendre le traitement.')
                return m


def verify(root):
    root=valid_lake(root)
    outdir=root/OUTPUT
    path=outdir/'enrichment.sqlite3'
    with closing(connect_ro(path)) as db:
        passed=0;issues=[]
        for lang,h,n,ev,updated in db.execute('SELECT language,sha256,records,evidence_records,exported_at FROM exports ORDER BY language'):
            if n==0:
                if h!='no-candidates':issues.append((lang,'empty hash invalid'))
                else:passed+=1
                continue
            file=outdir/'evidence'/safe_lang_filename(lang)
            if not file.is_file():issues.append((lang,'shard absent'));continue
            dig=hashlib.sha256();lines=0
            with file.open('rb') as f:
                for line in f:dig.update(line);lines+=1
            if dig.hexdigest()!=h or lines!=n:issues.append((lang,'sha256/ligne incohérents'))
            else:passed+=1
            if (passed+len(issues))%250==0:print(f'VERIFY|{passed+len(issues)}|ok={passed}|failed={len(issues)}',flush=True)
        result={'profile':'encyklopedia.dik-lex1-enrichment-verify/0.6','checked':passed+len(issues),
                'passed':passed,'failed':len(issues),'issues':issues[:50],
                'warning':'Vérifie les exports LOCAUX, pas les SHA officiels des sources'}
        print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
        if issues:raise RuntimeError('Vérification échouée')
        return result


def plan(root):
    root=valid_lake(root)
    with closing(connect_ro(root/INDEX)) as idx,closing(connect_ro(root/SQLITE_V05)) as rec:
        fp=fixture_checks(idx,rec)
        sources=source_catalog(idx)
        print(json.dumps({'profile':PROFILE,'data_root':str(root),'index_fingerprint':fp,
             'languages_staged_v05':rec.execute('SELECT COUNT(*) FROM completed_languages').fetchone()[0],
             'candidate_keys_v05':rec.execute('SELECT COUNT(*) FROM candidates').fetchone()[0],
             'sources_indexed':len(sources),'output':str(root/OUTPUT),
             'strategy':'stream raw source only at v0.5 sampled line anchors',
             'source_changes_blocked':True,'no_network':True,'no_canonical_writes':True,
             'pilot':'--languages fr,en','world':'run without --languages'},ensure_ascii=False,indent=2))


def main(argv=None):
    p=argparse.ArgumentParser(description='DIK-LEX-1 v0.6 — enrichissement par preuves ancrées')
    p.add_argument('command',choices=['plan','run','verify'])
    p.add_argument('--data-root',default=os.environ.get('ENCYK_DATA_ROOT',r'D:\EncyKlopedia' if os.name=='nt' else None))
    p.add_argument('--languages',help='codes séparés par virgule: fr,en')
    p.add_argument('--batch-lines',type=int,default=25000)
    p.add_argument('--min-free-gb',type=float,default=3.0)
    p.add_argument('--max-scan-lines',type=int,help=argparse.SUPPRESS)
    args=p.parse_args(argv)
    if not args.data_root:p.error('Préciser --data-root')
    if args.command=='plan':plan(Path(args.data_root));return 0
    if args.command=='verify':verify(Path(args.data_root));return 0
    languages=[s.strip().lower() for s in args.languages.split(',') if s.strip()] if args.languages else None
    if args.min_free_gb < 0: p.error('min-free-gb invalide')
    run(Path(args.data_root),languages=languages,batch_lines=args.batch_lines,min_free_gb=args.min_free_gb,
        max_scan_lines=args.max_scan_lines)
    return 0


if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:
        print('Interrompu; les checkpoints déjà écrits sont conservés.',file=sys.stderr);sys.exit(130)
    except Exception as exc:
        print(f'[ENRICHISSEMENT] {type(exc).__name__}: {exc}',file=sys.stderr);sys.exit(2)
