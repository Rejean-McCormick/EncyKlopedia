#!/usr/bin/env python3
"""DIK-LEX-1 v0.7: massive evidence triage and append-only NON-NORMATIVE review notes.

Inputs: lexical index v1, candidate reconciliation v0.5, source-anchored v0.6 evidence.
All inputs are read-only. Output is a separate D: data-lake folder.
No accepted matches, KS fabrications, KQ/KP, canonical dictionaries or publication.
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

from lexical_indexer import valid_lake, exclusive_lock, atomic_csv, atomic_json, utc
from semantic_enrichment import (INDEX, SQLITE_V05, OUTPUT as V06_OUTPUT,
                                  connect_ro, fixture_checks, safe_lang_filename)
from dik_reconciliation import OUTPUT as V05_OUTPUT
from quality_audit import db_fingerprint

PROFILE = 'encyklopedia.dik-lex1-qualification/candidate-v0.7'
OUTPUT = Path('30_working/lexical/harvester/dik-qualification-v1')
V06_DB = V06_OUTPUT / 'enrichment.sqlite3'
V05_DB = V05_OUTPUT / 'reconciliation.sqlite3'
CHOICES = {'needs_more_evidence', 'defer', 'reject_lexical_candidate', 'escalate_ambiguity', 'escalate_rights'}
LICENSE_CHOICES = {'needs_legal_review', 'source_license_claim_recorded', 'hold', 'needs_attribution_review'}
SCHEMA = '''
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS candidates (
 candidate_id TEXT PRIMARY KEY, language TEXT NOT NULL, lemma_key TEXT NOT NULL,
 tier TEXT NOT NULL, priority INTEGER NOT NULL,
 signals_json TEXT NOT NULL, summary_json TEXT NOT NULL,
 reviewed_by_machine INTEGER NOT NULL DEFAULT 0,
 CHECK(reviewed_by_machine=0));
CREATE INDEX IF NOT EXISTS ix_qualification_language ON candidates(language, priority, lemma_key);
CREATE INDEX IF NOT EXISTS ix_qualification_tier ON candidates(tier, language);
CREATE TABLE IF NOT EXISTS completed_languages (
 language TEXT PRIMARY KEY, candidates INTEGER NOT NULL,
 evidence_lines INTEGER NOT NULL, source_sha256 TEXT NOT NULL,
 export_sha256 TEXT NOT NULL, export_bytes INTEGER NOT NULL, export_records INTEGER NOT NULL,
 tier_counts_json TEXT NOT NULL, completed_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS review_events (
 seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
 candidate_id TEXT NOT NULL, reviewer_id TEXT NOT NULL, disposition TEXT NOT NULL,
 rationale TEXT NOT NULL, created_at TEXT NOT NULL,
 previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
 CHECK(disposition IN ('needs_more_evidence','defer','reject_lexical_candidate','escalate_ambiguity','escalate_rights')));
CREATE INDEX IF NOT EXISTS ix_review_events_candidate ON review_events(candidate_id, seq);
CREATE TABLE IF NOT EXISTS license_events (
 seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
 source_id INTEGER NOT NULL, reviewer_id TEXT NOT NULL, disposition TEXT NOT NULL,
 rationale TEXT NOT NULL, reference_url TEXT, created_at TEXT NOT NULL,
 previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL,
 CHECK(disposition IN ('needs_legal_review','source_license_claim_recorded','hold','needs_attribution_review')));
CREATE INDEX IF NOT EXISTS ix_license_events_source ON license_events(source_id, seq);
CREATE TRIGGER IF NOT EXISTS review_no_update BEFORE UPDATE ON review_events BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER IF NOT EXISTS review_no_delete BEFORE DELETE ON review_events BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER IF NOT EXISTS license_no_update BEFORE UPDATE ON license_events BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER IF NOT EXISTS license_no_delete BEFORE DELETE ON license_events BEGIN SELECT RAISE(ABORT,'append-only'); END;
'''


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha_file(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for b in iter(lambda: stream.read(2 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def fingerprint(index, recon, enrichment):
    idx = fixture_checks(index, recon)
    rmeta = enrichment.execute("SELECT v FROM meta WHERE k='index_fingerprint'").fetchone()
    if not rmeta or rmeta[0] != idx:
        raise RuntimeError('v0.6 ne pointe pas sur le catalogue v0.5/index-v1 attendu')
    return idx


def open_state(dbfile, fp):
    dbfile.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(dbfile, timeout=60)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA busy_timeout=60000')
    db.execute('PRAGMA synchronous=NORMAL')
    db.execute('PRAGMA cache_size=-65536')
    db.executescript(SCHEMA)
    old = db.execute('SELECT value FROM meta WHERE key=?', ('index_fingerprint',)).fetchone()
    ver = db.execute('SELECT value FROM meta WHERE key=?', ('profile',)).fetchone()
    if (old and old[0] != fp) or (ver and ver[0] != PROFILE):
        db.close()
        raise RuntimeError('Sortie v0.7 liée à une autre capture : nouveau dossier requis')
    with db:
        db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)', ('index_fingerprint', fp))
        db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)', ('profile', PROFILE))
    return db


def triage(doc, v05):
    """Classification de priorité d'examen, JAMAIS un diagnostic d'équivalence."""
    anchors = doc.get('raw_source_line_evidence') or []
    seen = [v for v in anchors if v.get('status') == 'observed']
    available = {v.get('family') for v in seen}
    nfc_variant_count = int(v05[2] or 0)
    pos_var = bool(v05[0])
    lexeme_var = bool(v05[1])
    glosses = []
    sense_ids = []
    lexeme_ids = set()
    pos_tags = set()
    sources = set()
    source_anchor_samples = []
    has_truncation = False
    for v in seen:
        sid = v.get('source_id')
        if isinstance(sid, int):
            sources.add(sid)
            if len(source_anchor_samples) < 12:
                source_anchor_samples.append({'source_id':sid, 'line':v.get('source_line'),
                    'family':v.get('family'), 'member':v.get('source_member'),
                    'path':v.get('source_relative_path')})
        data = v.get('observed_record') or {}
        fam = v.get('family')
        if fam == 'kaikki':
            if data.get('pos'): pos_tags.add('kaikki:'+str(data['pos'])[:100])
            for s in data.get('senses',[])[:24]:
                if not isinstance(s,dict): continue
                for g in (s.get('glosses') or s.get('raw_glosses') or [])[:2]:
                    if isinstance(g,str) and g and len(glosses)<8:glosses.append(g[:240])
        elif fam == 'wikidata':
            lex = data.get('lexeme_id')
            if lex:lexeme_ids.add(str(lex))
            if data.get('lexical_category_qid'):
                pos_tags.add('wikidata:'+str(data['lexical_category_qid'])[:80])
            for s in data.get('senses',[])[:24]:
                if not isinstance(s,dict):continue
                if s.get('sense_id') and len(sense_ids)<12:sense_ids.append(str(s['sense_id'])[:100])
                for g in (s.get('glosses') or [])[:2]:
                    value = g.get('value') if isinstance(g,dict) else None
                    if value and len(glosses)<8:glosses.append(str(value)[:240])
        elif fam == 'unimorph':
            # Traits N/V ne sont pas assimilés aux POS Kaikki ni aux QID Wikidata.
            feature = data.get('features')
            if feature:pos_tags.add('unimorph:'+str(feature).split(';')[0][:50])
        if any((data.get('truncation') or {}).values()):has_truncation=True
    signals = []
    if len(seen) != doc.get('anchors_total') or doc.get('evidence_captured') != doc.get('anchors_total'):
        signals.append('missing_or_invalid_sample_anchors')
    if lexeme_var or len(lexeme_ids)>1:
        signals.append('multiple_external_lexemes_same_graphy')
    if pos_var:
        signals.append('heterogeneous_pos_labels_require_mapping')
    if nfc_variant_count > 1:
        signals.append('distinct_NFC_spellings_collapsed_by_search_key')
    if has_truncation:
        signals.append('evidence_fields_truncated_v06')
    if len(glosses)>1:signals.append('multiple_glosses_require_sense_disambiguation')
    if not glosses and not sense_ids:signals.append('no_gloss_or_external_sense_id')
    if len(available)<2:signals.append('source_family_evidence_incomplete')
    # Explicitly do NOT infer contradiction from divergent glosses or labels.
    if 'missing_or_invalid_sample_anchors' in signals or 'source_family_evidence_incomplete' in signals:
        tier,priority='source_evidence_incomplete',1
    elif lexeme_var or nfc_variant_count>1:
        tier,priority='possible_lexeme_or_normalization_ambiguity',2
    elif pos_var:
        tier,priority='pos_mapping_review',3
    elif glosses and sense_ids:
        tier,priority='sense_comparison_queue',4
    elif glosses or sense_ids:
        tier,priority='limited_sense_evidence',5
    else:
        tier,priority='lemma_morphology_only',6
    summary = {'profile':PROFILE,'candidate_id':doc['candidate_id'],
        'language':doc['language'],'search_key':doc['search_key'],
        'tier':tier,'priority':priority,'signals':signals,
        'family_count':len(available),'families':sorted(available),
        'anchor_count':len(anchors),'observed_anchor_count':len(seen),
        'source_ids':sorted(sources),'source_anchor_sample':source_anchor_samples,
        'pos_tags_sample':sorted(pos_tags)[:12],
        'external_lexeme_ids_sample':sorted(lexeme_ids)[:12],
        'external_sense_ids_sample':sense_ids[:12],
        'glosses_sample':glosses[:8],
        'v05_nfc_variant_count_lower_bound':nfc_variant_count,
        'source_license_gate':'blocked_pending_review',
        'semantic_relationship':None,'semantic_equivalence_approved':False,
        'review_status':'unreviewed_candidate','may_be_published':False,
        'evidence_sampling':'v0.5 anchors only, capped v0.6 source fields',
        'limitations':['not_all_senses','no_automatic_exactMatch','not_a_normative_dik_review_decision']}
    return tier,priority,signals,summary


def materialize_sources(index, outdir):
    rows=[]
    for sid,path,kind,edition,status,n_good,n_rejected,sha_v in index.execute('''
       SELECT id,relative_path,kind,edition,status,accepted,rejected,source_sha256_verified
       FROM source_files ORDER BY id'''):
        rows.append({'source_id':sid,'family':kind,'edition':edition,'source_path':path,
          'index_status':status,'accepted_lines':n_good,'rejected_lines':n_rejected,
          'publisher_sha256_verified':bool(sha_v),'license_claim':'UNKNOWN',
          'license_review_status':'PENDING_MANUAL_REVIEW',
          'attribution_and_reuse_review':'REQUIRED',
          'may_be_redistributed':False,'may_be_published':False})
    atomic_csv(outdir/'source_license_review_queue.csv',list(rows[0]) if rows else [],rows)
    return len(rows)


def process_language(recon, enrich, db, lang, outdir, *, batch_size=1000, min_free_gb=3.0):
    src = enrich.execute('SELECT sha256,records,evidence_records FROM exports WHERE language=?',(lang,)).fetchone()
    if not src:raise RuntimeError(f'Export v0.6 absent: {lang}')
    source_hash, source_n, n_evidence = src
    rec=recon.execute('SELECT cross_family_keys FROM completed_languages WHERE language=?',(lang,)).fetchone()
    if not rec or rec[0] != source_n:
        raise RuntimeError(f'Désaccord v0.5/v0.6 pour {lang}: {rec} vs {source_n}')
    prev=db.execute('SELECT source_sha256,export_sha256,export_bytes,export_records FROM completed_languages WHERE language=?',(lang,)).fetchone()
    output_file=outdir/'review_queue'/safe_lang_filename(lang) if source_n else None
    if prev and prev[0]==source_hash and (source_n==0 or (output_file and output_file.is_file() and output_file.stat().st_size==prev[2])):
        # SHA-256 was verified at first staging. Run `verify` for an independent
        # full reread on reruns; size-only fast resume is not proof of integrity.
        return 'skipped'
    if prev and prev[0]!=source_hash:
        raise RuntimeError(f'Empreinte v0.6 modifiée depuis qualification: {lang}. Nouvelle capture requise.')
    if min_free_gb and shutil.disk_usage(outdir).free < min_free_gb*1024**3:
        raise RuntimeError('Espace D: libre insuffisant; checkpoints précédents préservés')
    if source_n==0:
        if source_hash!='no-candidates':raise RuntimeError('Empreinte d’export vide invalide')
        with db:
            db.execute('INSERT OR REPLACE INTO completed_languages VALUES (?,?,?,?,?,?,?,?,?)',
                       (lang,0,0,source_hash,'no-candidates',0,0,'{}',utc()))
        return 'empty'
    input_file=outdir.parent/(V06_OUTPUT.relative_to(OUTPUT.parent))/'evidence'/safe_lang_filename(lang)
    # outdir.parent is harvester ; construction relative explicite pour garantir la racine D:.
    if not input_file.is_file():raise FileNotFoundError(str(input_file))
    output_file.parent.mkdir(parents=True,exist_ok=True)
    partial=output_file.with_name(output_file.name+f'.partial-{os.getpid()}')
    digest=hashlib.sha256();incoming=hashlib.sha256();count=0;ev_lines=0;out_bytes=0;tiers=Counter()
    stream=recon.execute('''SELECT candidate_id,lemma_key,has_multiple_pos_labels,
       has_distinct_external_lexemes,nfc_variant_count_lower_bound
       FROM candidates WHERE language=? ORDER BY lemma_key''',(lang,))
    db.execute('BEGIN IMMEDIATE')
    try:
        db.execute('DELETE FROM candidates WHERE language=?',(lang,))
        batch=[]
        with input_file.open('rb') as reader, partial.open('wb') as writer:
            for raw in reader:
                incoming.update(raw)
                try:
                    doc=json.loads(raw)
                except (json.JSONDecodeError,UnicodeDecodeError) as exc:
                    raise RuntimeError(f'JSONL v0.6 corrompu ({lang}, ligne {count+1}): {exc}') from exc
                item=next(stream,None)
                if item is None or (doc.get('candidate_id'),doc.get('search_key'),doc.get('language'))!=(item[0],item[1],lang):
                    raise RuntimeError(f'Ordre ou identifiant candidat incohérent dans {lang}, ligne {count+1}')
                tier,priority,signals,summary=triage(doc,(item[2],item[3],item[4]))
                b=(canonical(summary)+'\n').encode('utf-8')
                writer.write(b);digest.update(b);out_bytes+=len(b)
                count+=1;ev_lines+=len(doc.get('raw_source_line_evidence') or [])
                tiers[tier]+=1
                batch.append((item[0],lang,item[1],tier,priority,canonical(signals),canonical(summary),0))
                if len(batch)>=batch_size:
                    db.executemany('INSERT INTO candidates VALUES (?,?,?,?,?,?,?,?)',batch)
                    batch.clear()
                if count%250000==0:
                    print(f'REVIEW|{lang}|{count}/{source_n}',flush=True)
            if batch:db.executemany('INSERT INTO candidates VALUES (?,?,?,?,?,?,?,?)',batch)
        if next(stream,None) is not None or count != source_n or ev_lines != n_evidence or incoming.hexdigest()!=source_hash:
            raise RuntimeError(f'Contrôle v0.6 SHA256/nombre de lignes échoué : {lang}')
        db.execute('INSERT OR REPLACE INTO completed_languages VALUES (?,?,?,?,?,?,?,?,?)',
                   (lang,count,ev_lines,source_hash,digest.hexdigest(),out_bytes,count,canonical(dict(tiers)),utc()))
        db.commit()
        os.replace(partial,output_file)
        return 'qualified'
    except BaseException:
        db.rollback()
        raise
    finally:
        if partial.exists():partial.unlink()


def manifest(root,index,rec,enrich,db,outdir,fp,total):
    staged=db.execute('SELECT COUNT(*) FROM completed_languages').fetchone()[0]
    candidates=db.execute('SELECT COALESCE(SUM(candidates),0) FROM completed_languages').fetchone()[0]
    categories=dict(db.execute('SELECT tier,COUNT(*) FROM candidates GROUP BY tier'))
    n_review=db.execute('SELECT COUNT(*) FROM review_events').fetchone()[0]
    n_lic=db.execute('SELECT COUNT(*) FROM license_events').fetchone()[0]
    complete=staged==total and candidates==rec.execute('SELECT COUNT(*) FROM candidates').fetchone()[0]
    status='qualification_candidates_complete' if complete else 'qualification_candidates_partial'
    result={'profile':PROFILE,'generated_at':utc(),'status':status,'data_root':str(root),
         'upstream_catalog_fingerprint':fp,'language_codes_total':total,'language_codes_staged':staged,
         'candidate_keys_qualified':candidates,'triage_categories':categories,
         'license_sources_pending_manual_review':index.execute('SELECT COUNT(*) FROM source_files').fetchone()[0],
         'non_normative_review_annotations':n_review,'non_normative_license_annotations':n_lic,
         'read_only_inputs':[str(root/INDEX),str(root/V05_DB),str(root/V06_DB),str(root/V06_OUTPUT/'evidence')],
         'output_sqlite':str(outdir/'qualification.sqlite3'),
         'output_shards':str(outdir/'review_queue'),
         'automatic_accepted_matches':0,'valid_KS_evidence_links_created':0,
         'source_official_hashes_confirmed_by_this_tool':False,
         'license_approved_by_this_tool':False,'KQ_KP_created':0,
         'normative_diK_import':False,'published':False,
         'semantic_matching':'none; heuristic flags only, requires distinct sense-level review'}
    atomic_json(outdir/'latest.json',result)
    atomic_json(outdir/'dik-qualification-handoff.candidate.json',{
         'profile':'encyklopedia.to-dik.qualification-queue/candidate-v0.7','status':status,
         'candidate_database':result['output_sqlite'],'candidate_shards':result['output_shards'],
         'source_license_queue':str(outdir/'source_license_review_queue.csv'),
         'evidence_database':str(root/V06_DB),'review_events_table':'review_events',
         'decision_scope':'local_triage_only_not_dik_review-decision/1.0-candidate',
         'requires_authorized_reviewer':True,'requires_KS_evidence_for_normative_acceptance':True,
         'license_review_required':True,'crosswalk_review_required':True,
         'may_be_published':False,'approved_semantic_equivalences':0})
    hdr=['language,candidates,review_sha256,review_bytes,source_v06_sha256,completed_at']
    for lang,n,e,h,oh,size,rc,tiers,dt in db.execute('SELECT * FROM completed_languages ORDER BY language'):
        hdr.append(','.join([lang,str(n),oh,str(size),h,dt]))
    (outdir/'languages_qualified.csv').write_text('\n'.join(hdr)+'\n',encoding='utf-8')
    report=['# EncyKlopedia → diK — Qualification candidate v0.7','',
      f'**État : {status}** — {staged:,}/{total:,} codes linguistiques.','',
      f'- Graphies candidates traitées : {candidates:,}',
      f'- Files de priorité : {categories}',
      f'- Annotations humaines locales (non normatives) : {n_review}',
      f'- Sources à revoir pour droits et licences : {result["license_sources_pending_manual_review"]}',
      '', '## Gouvernance et limites', '',
      '- Aucune fusion de sens, aucun exactMatch, aucun KQ/KP et aucune publication.',
      '- Les POS Kaikki/UniMorph/Wikidata ne sont pas normalisés entre ontologies.',
      '- Plusieurs gloses ne démontrent ni contradiction ni équivalence sémantique.',
      '- Les preuves source restent limitées aux ancrages v0.5 enrichis en v0.6.',
      '- Les notes de revue sont une file locale append-only, PAS des décisions diK ratifiées.',
      '- Les licences et l’attribution sont bloquées par défaut, sans droit d’usage supposé.',
      '- Une acceptation diK exige identités cible, décision autorisée et preuves KS.',
      '', '## Fichiers', '',
      '- qualification.sqlite3 : index dérivé des catégories et journal local append-only.',
      '- review_queue/<lang>.jsonl : qualification candidate et provenance résumée, vérifiable.',
      '- source_license_review_queue.csv : 210 sources à qualifier explicitement.',
      '- dik-qualification-handoff.candidate.json : pointeur candidat non normatif.']
    (outdir/'RAPPORT_QUALIFICATION.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    return result


def plan(root):
    root=valid_lake(root)
    with closing(connect_ro(root/INDEX)) as idx,closing(connect_ro(root/V05_DB)) as rec,closing(connect_ro(root/V06_DB)) as enrich:
        fp=fingerprint(idx,rec,enrich)
        print(json.dumps({'profile':PROFILE,'data_root':str(root),'index_fingerprint':fp,
          'languages_v05':rec.execute('SELECT COUNT(*) FROM completed_languages').fetchone()[0],
          'candidates_v05':rec.execute('SELECT COUNT(*) FROM candidates').fetchone()[0],
          'languages_v06':enrich.execute('SELECT COUNT(*) FROM exports').fetchone()[0],
          'evidence_records_v06':enrich.execute('SELECT COUNT(*) FROM evidence').fetchone()[0],
          'output':str(root/OUTPUT),'no_network':True,'no_canonical_write':True,
          'classification_does_not_approve_semantics':True},ensure_ascii=False,indent=2))


def run(root, *, languages=None,min_free_gb=3.0,batch_size=1000,max_languages=None):
    root=valid_lake(root);outdir=root/OUTPUT
    if min_free_gb<0 or batch_size<1:raise ValueError('Paramètres incorrects')
    if min_free_gb and shutil.disk_usage(root).free<min_free_gb*1024**3:
        raise RuntimeError('Espace insuffisant sur D:')
    with closing(connect_ro(root/INDEX)) as idx,closing(connect_ro(root/V05_DB)) as rec,closing(connect_ro(root/V06_DB)) as enrich:
        fp=fingerprint(idx,rec,enrich)
        known=[v[0] for v in rec.execute('SELECT language FROM completed_languages ORDER BY language')]
        chosen=sorted(set(languages)) if languages else known
        if not languages and enrich.execute('SELECT COUNT(*) FROM exports').fetchone()[0]!=len(known):
            raise RuntimeError('v0.6 non exportée pour toutes les langues : terminer v0.6 avant traitement mondial')
        if not set(chosen).issubset(known):raise ValueError('Langue non présente dans la v0.5')
        if max_languages is not None:chosen=chosen[:max_languages]
        outdir.mkdir(parents=True,exist_ok=True)
        with exclusive_lock(outdir/'qualification.lock'):
            with closing(open_state(outdir/'qualification.sqlite3',fp)) as db:
                for i,lang in enumerate(chosen,1):
                    state=process_language(rec,enrich,db,lang,outdir,batch_size=batch_size,min_free_gb=min_free_gb)
                    if state!='skipped' or i%100==0:print(f'QUALIFY|{i}|{len(chosen)}|{lang}|{state}',flush=True)
                    if i%250==0 or i==len(chosen):
                        if min_free_gb and shutil.disk_usage(root).free<min_free_gb*1024**3:
                            raise RuntimeError('Espace D: bas : checkpoint conservé')
                if fingerprint(idx,rec,enrich)!=fp:raise RuntimeError('Index modifié en cours de traitement')
                materialize_sources(idx,outdir)
                result=manifest(root,idx,rec,enrich,db,outdir,fp,len(known))
                print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
                return result


def verify(root):
    root=valid_lake(root);outdir=root/OUTPUT
    with closing(connect_ro(outdir/'qualification.sqlite3')) as db,closing(connect_ro(root/V06_DB)) as enrich:
        issues=[];passed=0
        for lang,n,ev,src_sha,out_sha,sz,count,tiers,at in db.execute('SELECT * FROM completed_languages ORDER BY language'):
            indexed=db.execute('SELECT COUNT(*) FROM candidates WHERE language=?',(lang,)).fetchone()[0]
            if indexed != n:
                issues.append((lang,'sqlite_candidate_count_mismatch'));continue
            upstream=enrich.execute('SELECT sha256,records,evidence_records FROM exports WHERE language=?',(lang,)).fetchone()
            if not upstream or upstream!=(src_sha,n,ev):
                issues.append((lang,'upstream_v06_mismatch'));continue
            if n==0:
                if out_sha!='no-candidates' or count!=0:issues.append((lang,'empty_mismatch'))
                else:passed+=1
                continue
            f=outdir/'review_queue'/safe_lang_filename(lang)
            if not f.is_file() or f.stat().st_size != sz or sha_file(f)!=out_sha:
                issues.append((lang,'local_sha256_mismatch'));continue
            with f.open('rb') as stream:lines=sum(1 for _ in stream)
            if lines!=count or count!=n:issues.append((lang,'record_count_mismatch'))
            else:passed+=1
            if (passed+len(issues))%300==0:print(f'VERIFY|{passed+len(issues)}|passed={passed}|failed={len(issues)}',flush=True)
        for table in ('review_events','license_events'):
            previous='0'*64
            for row in db.execute(f'SELECT * FROM {table} ORDER BY seq'):
                seq,event_id,subject,reviewer,choice,reason,*last = row
                if table=='review_events':date,prev,h=last;extra=None
                else:extra,date,prev,h=last
                payload={'id':event_id,'subject':subject,'reviewer':reviewer,'disposition':choice,
                         'rationale':reason,'reference_url':extra,'created_at':date,'previous_hash':previous}
                if prev!=previous or hashlib.sha256(canonical(payload).encode()).hexdigest()!=h:
                    issues.append((table,f'journal broken at {seq}'));break
                previous=h
        result={'profile':'encyklopedia.dik-lex1-qualification-verify/0.7',
                'checked_languages':passed+len([x for x in issues if x[0] not in ('review_events','license_events')]),
                'passed':passed,'failed':len(issues),'issues':issues[:40],
                'publisher_hashes_verified':False,'semantic_equivalences_approved':0}
        print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
        if issues:raise RuntimeError('Vérification v0.7 échouée')
        return result


def append_event(root, *, kind, subject, reviewer, disposition, rationale, reference_url=None):
    root=valid_lake(root)
    if kind not in ('review','license'):raise ValueError('Type d’annotation inconnu')
    allowed=CHOICES if kind=='review' else LICENSE_CHOICES
    if disposition not in allowed:raise ValueError('Disposition interdite : pas d’acceptation normative ici')
    if not 2<=len(reviewer.strip())<=100 or not 8<=len(rationale.strip())<=3000:
        raise ValueError('Réviseur (2+ chars) et justification (8+ chars) obligatoires')
    if reference_url and (len(reference_url)>500 or not reference_url.startswith('https://')):
        raise ValueError('Référence autorisée : https:// seulement')
    outdir=root/OUTPUT
    if not (outdir/'qualification.sqlite3').is_file():
        raise RuntimeError('Qualifier un pilote ou le monde avant d’annoter les candidats ou licences')
    with exclusive_lock(outdir/'qualification.lock'):
        with closing(sqlite3.connect(outdir/'qualification.sqlite3',timeout=60)) as db:
            existing=db.execute('SELECT value FROM meta WHERE key=?',('profile',)).fetchone()
            if not existing or existing[0]!=PROFILE:
                raise RuntimeError('Catalogue de qualification v0.7 non reconnu')
            recorded=db.execute('SELECT value FROM meta WHERE key=?',('index_fingerprint',)).fetchone()
            with closing(connect_ro(root/INDEX)) as source_catalog:
                if not recorded or db_fingerprint(source_catalog)!=recorded[0]:
                    raise RuntimeError('Le catalogue index-v1 a changé; ne pas annoter une ancienne qualification')
            db.executescript(SCHEMA)
            if kind=='review':
                if not db.execute('SELECT 1 FROM candidates WHERE candidate_id=?',(subject,)).fetchone():
                    raise ValueError('Candidat introuvable dans le catalogue v0.7')
                table='review_events'
            else:
                sid=int(subject)
                with closing(connect_ro(root/INDEX)) as src:
                    if not src.execute('SELECT 1 FROM source_files WHERE id=?',(sid,)).fetchone():
                        raise ValueError('Source inconnue')
                subject=sid;table='license_events'
            prev=db.execute(f'SELECT event_hash FROM {table} ORDER BY seq DESC LIMIT 1').fetchone()
            old_hash=prev[0] if prev else '0'*64
            date=utc()
            event_id='local-'+hashlib.sha256(os.urandom(32)).hexdigest()[:28]
            payload={'id':event_id,'subject':subject,'reviewer':reviewer.strip(),
              'disposition':disposition,'rationale':rationale.strip(),
              'reference_url':reference_url if kind=='license' else None,
              'created_at':date,'previous_hash':old_hash}
            hash_value=hashlib.sha256(canonical(payload).encode()).hexdigest()
            with db:
                if kind=='review':
                    db.execute('INSERT INTO review_events(event_id,candidate_id,reviewer_id,disposition,rationale,created_at,previous_hash,event_hash) VALUES (?,?,?,?,?,?,?,?)',
                         (event_id,subject,reviewer.strip(),disposition,rationale.strip(),date,old_hash,hash_value))
                else:
                    db.execute('INSERT INTO license_events(event_id,source_id,reviewer_id,disposition,rationale,reference_url,created_at,previous_hash,event_hash) VALUES (?,?,?,?,?,?,?,?,?)',
                         (event_id,subject,reviewer.strip(),disposition,rationale.strip(),reference_url,date,old_hash,hash_value))
    return {'event_id':event_id,'hash':hash_value,'status':'local_review_note_only','normative_dik_acceptance':False}


def main(argv=None):
    p=argparse.ArgumentParser(description='DIK-LEX-1 v0.7 — qualification candidate massive')
    p.add_argument('command',choices=('plan','run','verify','note','license-note'))
    p.add_argument('--data-root',default=os.environ.get('ENCYK_DATA_ROOT',r'D:\EncyKlopedia' if os.name=='nt' else None))
    p.add_argument('--languages',help='fr,en')
    p.add_argument('--min-free-gb',type=float,default=3.0)
    p.add_argument('--batch-size',type=int,default=1000)
    p.add_argument('--max-languages',type=int,help=argparse.SUPPRESS)
    p.add_argument('--candidate-id')
    p.add_argument('--source-id',type=int)
    p.add_argument('--reviewer')
    p.add_argument('--disposition')
    p.add_argument('--reason')
    p.add_argument('--reference-url')
    a=p.parse_args(argv)
    if not a.data_root:p.error('Préciser --data-root')
    root=Path(a.data_root)
    if a.command=='plan':plan(root)
    elif a.command=='run':run(root,languages=[s.strip().lower() for s in a.languages.split(',')] if a.languages else None,
                           min_free_gb=a.min_free_gb,batch_size=a.batch_size,max_languages=a.max_languages)
    elif a.command=='verify':verify(root)
    else:
        if not a.reviewer or not a.reason or not a.disposition:p.error('Annotation incomplète')
        kind='review' if a.command=='note' else 'license'
        subject=a.candidate_id if kind=='review' else a.source_id
        if subject is None:p.error('Candidat ou source absent')
        print(json.dumps(append_event(root,kind=kind,subject=subject,reviewer=a.reviewer,
                             disposition=a.disposition,rationale=a.reason,reference_url=a.reference_url),ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except KeyboardInterrupt:print('Interrompu; derniers checkpoints par langue conservés.',file=sys.stderr);sys.exit(130)
    except Exception as exc:print(f'[QUALIFICATION] {type(exc).__name__}: {exc}',file=sys.stderr);sys.exit(2)
