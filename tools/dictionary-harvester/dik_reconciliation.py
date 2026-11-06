#!/usr/bin/env python3
"""EncyKlopedia -> diK LEX-1 candidate reconciliation, NOT canonical diK import.

Existing lexical index is always read-only. Candidate staging is resumable by
language, SQLite-backed and bounded per-lemma. No auto exactMatch, KQ/KP, GF,
publication or source-data mutation. Python standard library only.
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
import unicodedata
from collections import Counter
from bisect import bisect_right
from contextlib import closing
from pathlib import Path

from quality_audit import readonly_connection, db_fingerprint
from lexical_indexer import valid_lake, exclusive_lock, atomic_json, atomic_csv, utc

PROFILE = 'encyklopedia.dik-lex1-candidate-reconciliation/0.5'
OUTPUT = Path('30_working/lexical/harvester/dik-reconciliation-v1')
FAMILY_BITS = {'kaikki':1, 'unimorph':2, 'wikidata':4}
FAMILY_ORDER = ('kaikki','unimorph','wikidata')
SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS completed_languages(
 language TEXT PRIMARY KEY, observations INTEGER NOT NULL, lemma_keys INTEGER NOT NULL,
 cross_family_keys INTEGER NOT NULL, nfc_variant_collision_keys INTEGER NOT NULL,
 source_file_count INTEGER NOT NULL, completed_at TEXT NOT NULL,
 exported_sha256 TEXT, exported_records INTEGER);
CREATE TABLE IF NOT EXISTS candidates(
 language TEXT NOT NULL, lemma_key TEXT NOT NULL, candidate_id TEXT NOT NULL UNIQUE,
 observations INTEGER NOT NULL, families_mask INTEGER NOT NULL,
 source_file_count INTEGER NOT NULL, nfc_variant_count_lower_bound INTEGER NOT NULL,
 has_multiple_pos_labels INTEGER NOT NULL, has_distinct_external_lexemes INTEGER NOT NULL,
 sample_lemma_nfc TEXT NOT NULL, provenance_json TEXT NOT NULL,
 PRIMARY KEY(language,lemma_key));
CREATE INDEX IF NOT EXISTS idx_candidates_language ON candidates(language);
'''


def readonly_index(root: Path, index_path: Path | None = None):
    index_path = index_path or root / '30_working/lexical/harvester/index-v1/lexical.sqlite3'
    return readonly_connection(index_path), index_path


def source_catalog(db):
    src = {}
    for sid, path, kind, edition, state, count, rejected, verified in db.execute('''
        SELECT id,relative_path,kind,edition,status,accepted,rejected,source_sha256_verified
        FROM source_files ORDER BY id'''):
        if kind not in FAMILY_BITS:
            raise ValueError(f'Famille inconnue, arret protecteur: {kind}')
        src[sid] = {'source_id':sid,'relative_path':path,'family':kind,
                    'edition':edition,'index_status':state,'accepted':count,
                    'rejected':rejected,'sha256_official_verified':bool(verified),
                    'license_reviewed':False}
    members_present=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='source_members'").fetchone()
    if members_present:
        for sid,member,first,last in db.execute('SELECT source_id,member_path,start_line,end_line FROM source_members ORDER BY source_id,start_line'):
            if sid in src:
                src[sid].setdefault('_members',[]).append((first,last,member))
    return src


def source_member(src, absolute_line):
    members=src.get('_members',[])
    if not members:return (None,None)
    idx=bisect_right([x[0] for x in members],absolute_line)-1
    if idx<0:return (None,None)
    first,last,name=members[idx]
    if first<=absolute_line<=last:return (name,absolute_line-first+1)
    return (None,None)


def fingerprint_guard(db, wanted):
    actual=db_fingerprint(db)
    if actual != wanted:
        raise RuntimeError('Index source modifie : arret. Ne jamais fusionner deux captures.')


def stage_connection(path:Path, fingerprint:str):
    path.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(path, timeout=60)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=60000')
    conn.executescript(SCHEMA)
    old=conn.execute("SELECT v FROM meta WHERE k='index_fingerprint'").fetchone()
    if old and old[0]!=fingerprint:
        conn.close()
        raise RuntimeError('Index different: dossier de reconciliation protege; utiliser un nouveau dossier.')
    with conn:
        conn.execute("INSERT OR IGNORE INTO meta(k,v) VALUES ('index_fingerprint',?)",(fingerprint,))
        conn.execute("INSERT OR IGNORE INTO meta(k,v) VALUES ('profile',?)",(PROFILE,))
    return conn


def safe_lang_filename(language):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,39}',language):
        raise ValueError('Code de langue non sûr: '+language[:80])
    return language+'.jsonl'


def candidate_id(language, lemma_key):
    digest=hashlib.sha256(json.dumps([language,lemma_key],ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
    return 'lexcand-'+digest


def normalize_unicode(text):
    return unicodedata.normalize('NFC',text)


def work_languages(db):
    return dict(db.execute('SELECT language_code,SUM(lemma_observations) FROM language_stats GROUP BY language_code ORDER BY language_code'))


def process_language(index, staged, lang, sources, fingerprint, progress=None, min_free_gb=3.0, *, outdir):
    """Checkpoint once per language. Streaming key groups, bounded evidence samples.

    An 'observation' is one row, not a word or concept. Morph forms repeat lemmas
    legitimately. Candidate keys are NFKC/casefold search keys, NOT semantic IDs.
    """
    if staged.execute('SELECT 1 FROM completed_languages WHERE language=?',(lang,)).fetchone():
        export_language(staged, lang, outdir)
        return 'skipped'
    min_free=int(min_free_gb*1024**3)
    if shutil.disk_usage(outdir).free < min_free:
        raise RuntimeError(f'Espace libre insuffisant (minimum {min_free_gb} Gio)')
    rows=0;keys=0;cross=0;collisions=0
    prev=None
    batch=[]
    state=None

    def reset(key):
        return {'lemma_key':key,'observations':0,'mask':0,'sources':set(),
                'by_family':Counter(),'pos_values':set(),'pos_overflow':False,
                'nfc_values':set(),'nfc_overflow':False,'external_ids':set(),
                'external_overflow':False,'proofs':{x:[] for x in FAMILY_ORDER}}

    def flush(cur):
        nonlocal keys,cross,collisions
        if cur is None:return
        keys+=1
        if len(cur['nfc_values'])>1 or cur['nfc_overflow']:collisions+=1
        if cur['mask'].bit_count() < 2:return
        cross+=1
        proofs={k:v for k,v in cur['proofs'].items() if v}
        evidence={'status':'unreviewed_candidate','identity':None,'relationship':None,
            'language_code':lang,'lemma_search_key':cur['lemma_key'],
            'source_counts_by_family':dict(cur['by_family']),
            'nfc_examples':sorted(cur['nfc_values']),
            'pos_examples':sorted(cur['pos_values']),
            'external_lexeme_ids_sample':sorted(cur['external_ids']),
            'source_observations_sample':proofs,
            'samples_truncated':(cur['nfc_overflow'] or cur['pos_overflow'] or cur['external_overflow']),
            'source_license_reviewed':False,'official_source_hash_verified':False,
            'suggested_action':'manual_review_required',
            'warnings':['homographs_not_semantic_equivalence',
               'search_normalization_NFKC_casefold_not_identity',
               'not_canonical_dik_or_kristal']}
        batch.append((lang,cur['lemma_key'],candidate_id(lang,cur['lemma_key']),
                      cur['observations'],cur['mask'],len(cur['sources']),
                      len(cur['nfc_values']) + int(cur['nfc_overflow']),
                      int(len(cur['pos_values'])>1 or cur['pos_overflow']),
                      int(len(cur['external_ids'])>1 or cur['external_overflow']),
                      sorted(cur['nfc_values'])[0] if cur['nfc_values'] else '',
                      json.dumps(evidence,ensure_ascii=False,separators=(',',':'))))
        if len(batch)>=2000:
            staged.executemany('''INSERT INTO candidates(language,lemma_key,candidate_id,observations,
              families_mask,source_file_count,nfc_variant_count_lower_bound,
              has_multiple_pos_labels,has_distinct_external_lexemes,sample_lemma_nfc,provenance_json)
              VALUES(?,?,?,?,?,?,?,?,?,?,?)''',batch)
            batch.clear()

    query='''SELECT lemma_key,source_id,source_line,lemma,pos,external_id,language_qid,
             source_language_code,grammatical_features,form_surface
             FROM entries INDEXED BY idx_entries_language_lemma
             WHERE language_code=? ORDER BY lemma_key'''
    # Single transaction per language: interrupted language rolls back fully.
    try:
        staged.execute('BEGIN IMMEDIATE')
        for key,sid,line_no,raw,pos,eid,lqid,rawlang,features,form in index.execute(query,(lang,)):
            rows+=1
            if prev!=key:
                flush(state)
                prev=key
                state=reset(key)
            state['observations']+=1
            state['sources'].add(sid)
            src=sources[sid]
            fam=src['family']
            state['mask'] |= FAMILY_BITS[fam]
            state['by_family'][fam]+=1
            nfc=normalize_unicode(raw)
            if nfc not in state['nfc_values']:
                if len(state['nfc_values'])<6:state['nfc_values'].add(nfc)
                else:state['nfc_overflow']=True
            if pos and pos not in state['pos_values']:
                if len(state['pos_values'])<8:state['pos_values'].add(pos)
                else:state['pos_overflow']=True
            if eid and eid not in state['external_ids']:
                if len(state['external_ids'])<6:state['external_ids'].add(eid)
                else:state['external_overflow']=True
            if (len(state['proofs'][fam])<4 and
                not any(p['source_id']==sid for p in state['proofs'][fam])):
                member,member_line=source_member(src,line_no)
                state['proofs'][fam].append({
                  'source_id':sid,'source_file':src['relative_path'],
                  'source_line':line_no,'zip_member':member,'zip_member_line':member_line,
                  'source_lemma_nfc':nfc,
                  'source_language_code':rawlang,'source_pos':pos,
                  'wikidata_lexeme_id':eid,'wikidata_language_qid':lqid,
                  'morph_features_sample':features[:140] if features else None,
                  'form_sample':form[:100] if form else None})
            if progress and rows%250000==0:
                progress(rows)
            if rows%2_000_000==0 and shutil.disk_usage(outdir).free<min_free:
                raise RuntimeError('Espace disque bas : rollback de cette langue (checkpoints precedents sauves)')
        flush(state)
        if batch:
            staged.executemany('''INSERT INTO candidates(language,lemma_key,candidate_id,observations,
              families_mask,source_file_count,nfc_variant_count_lower_bound,
              has_multiple_pos_labels,has_distinct_external_lexemes,sample_lemma_nfc,provenance_json)
              VALUES(?,?,?,?,?,?,?,?,?,?,?)''',batch)
        expected=index.execute('SELECT COALESCE(SUM(lemma_observations),0) FROM language_stats WHERE language_code=?',(lang,)).fetchone()[0]
        if expected != rows:
            raise RuntimeError(f'Desaccord comptable {lang}: index={rows} inventaire={expected}')
        staged.execute('''INSERT INTO completed_languages(language,observations,lemma_keys,cross_family_keys,
          nfc_variant_collision_keys,source_file_count,completed_at)
          VALUES (?,?,?,?,?,?,?)''',(lang,rows,keys,cross,collisions,
              len({r[0] for r in index.execute('SELECT source_id FROM language_stats WHERE language_code=?',(lang,))}),utc()))
        staged.commit()
    except BaseException:
        staged.rollback()
        raise
    # Export is separately retryable if interrupted after successful SQLite commit.
    export_language(staged,lang,outdir)
    return 'processed'


def export_language(db, lang, outdir):
    item=db.execute('SELECT cross_family_keys,exported_sha256 FROM completed_languages WHERE language=?',(lang,)).fetchone()
    if not item:raise ValueError('Langue non auditee')
    count, knownhash=item
    folder=outdir/'candidates'
    path=folder/safe_lang_filename(lang)
    if count==0:
        with db:
            db.execute('UPDATE completed_languages SET exported_records=0,exported_sha256=? WHERE language=?',('no-candidates',lang))
        return None
    if knownhash and path.is_file():
        # Avoid hashing millions of bytes on each resume; recorded size checked in manifest.
        return path
    folder.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+f'.partial-{os.getpid()}')
    h=hashlib.sha256();n=0
    try:
        with temp.open('wb') as stream:
            for cid, lemma, mask, obs, evidence in db.execute('''
               SELECT candidate_id,lemma_key,families_mask,observations,provenance_json
               FROM candidates WHERE language=? ORDER BY lemma_key''',(lang,)):
                doc=json.loads(evidence)
                doc.update(candidate_id=cid,profile=PROFILE,observations=obs,
                           source_families=[x for x in FAMILY_ORDER if mask & FAMILY_BITS[x]])
                line=(json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8')
                stream.write(line);h.update(line);n+=1
        if n!=count:raise RuntimeError(f'Export incomplet {lang}: {n} != {count}')
        os.replace(temp,path)
        with db:
            db.execute('UPDATE completed_languages SET exported_sha256=?,exported_records=? WHERE language=?',(h.hexdigest(),n,lang))
    finally:
        if temp.exists():temp.unlink()
    return path


def report(root, outdir, index, staged, fp, total_langs, *, partial):
    stats=list(staged.execute('''SELECT language,observations,lemma_keys,cross_family_keys,
      nfc_variant_collision_keys,source_file_count,exported_sha256,exported_records
      FROM completed_languages ORDER BY language'''))
    counted=sum(r[1] for r in stats)
    cand=sum(r[3] for r in stats)
    issues=list(index.execute('''SELECT relative_path,kind,edition,status,accepted,rejected,
       source_sha256_verified FROM source_files ORDER BY relative_path'''))
    source_rows=[dict(zip(['path','family','edition','status','accepted','rejected','official_sha256_verified'],r))
                 for r in issues]
    lang_path=outdir/'languages_staged.csv'
    names=['language','observations','lemma_keys','cross_family_keys',
           'nfc_variant_collision_keys','source_files','jsonl_sha256','jsonl_records']
    atomic_csv(lang_path,names,[dict(zip(names,row)) for row in stats])
    license_rows=[(s['path'],s['family'],s['status'],s['official_sha256_verified'],
                   'not_reviewed','needs_official_license_evidence') for s in source_rows]
    source_names=['source_path','family','index_status','official_sha256_verified','license_status','action']
    atomic_csv(outdir/'source_license_review_queue.csv',source_names,[dict(zip(source_names,row)) for row in license_rows])
    reviewed=staged.execute('SELECT COUNT(*) FROM completed_languages').fetchone()[0]
    manifest={'profile':PROFILE,'generated_at':utc(),'data_root':str(root),'source_index_path':str(root/'30_working/lexical/harvester/index-v1/lexical.sqlite3'),
       'source_index_fingerprint':fp,'status':'candidate_complete' if not partial else 'candidate_partial',
       'languages_total':total_langs,'languages_staged':reviewed,'observations_staged':counted,
       'cross_family_candidate_keys':cand,'source_count':len(source_rows),
       'candidate_database':str(outdir/'reconciliation.sqlite3'),
       'jsonl_directory':str(outdir/'candidates'),'language_manifest':str(lang_path),
       'diK_integration':'review_queue_only_not_normative_export',
       'notices':['Aucun mapping KQ/KP, L/S/F exactMatch, GF, ou publication',
                  'Les observables ont des identifiants de lignes; ils ne portent pas les gloses et sens integres',
                  'Une cle NFKC/casefold est une recherche homographe; non une equivalence semantique',
                  'Les licences et empreintes de la source officielle ne sont pas approuvees',
                  'Les donnees dont une seule famille dispose restent dans index-v1, hors file de conciliation']}
    atomic_json(outdir/'latest.json',manifest)
    atomic_json(outdir/'dik-review-queue.candidate.json',{
       'profile':'encyklopedia.to-dik.lexical-review-queue/candidate-v0.5',
       'generated_at':manifest['generated_at'],
       'status':'unreviewed_candidate',
       'source_index_fingerprint':fp,
       'candidate_stage':str(outdir/'reconciliation.sqlite3'),
       'candidate_shards_directory':str(outdir/'candidates'),
       'language_shards_manifest':str(lang_path),
       'source_licensing_queue':str(outdir/'source_license_review_queue.csv'),
       'review_policy':['LEX-003','LEX-004','LEX-005','XW-001','XW-002','XW-003'],
       'requires_human_sense_review':True,
       'requires_source_license_review':True,
       'requires_official_source_hash_review':True,
       'requires_crosswalk_and_KS_evidence':True,
       'approved_matches':0,'approved_dictionaries':0,
       'canonical_kristal_ids_created':0,'may_be_published':False,
       'warning':'Candidate staging interface, NOT a normative diK 1.0 or Framework v11 import job.'})
    human=['# EncyKlopedia → diK : file de conciliation candidate','',
      '**NE PAS PUBLIER.** Aucun dictionnaire curaté ni identité Kristal ne sont produits.','',
      f'- Capture de source : `{fp}`',f'- Langues traitees : **{reviewed:,}/{total_langs:,}**',
      f'- Observations parcoures : **{counted:,}**',
      f'- Clés homographes entre familles : **{cand:,}**',
      f'- Sources documentees : **{len(source_rows)}**',
      '- Rapprochement par graphie NFKC/casefold, avec exemples NFC fideles et POS/provenance conserves.',
      '- Les fiches possedent des indications de lignes sources, pas les definitions/sens bruts.',
      '- La conciliation de sens, l alignement Q/P et le mapping grammatical GF necessitent des preuves et revue humaine.',
      '', '## Integration',
      'Importer les JSONL uniquement dans un espace de **candidats** de diK apres validation du contrat.',
      'Les JSONL ne sont **pas** des dictionnaires Framework v11 ni des imports normatifs diK.',
      'Voir `source_license_review_queue.csv` et `languages_staged.csv`.','']
    (outdir/'RAPPORT_RECONCILIATION.md').write_text('\n'.join(human),encoding='utf-8')
    return manifest


def run(root, *, langs=None, min_free_gb=3.0, output_override=None):
    root=valid_lake(root)
    outdir=output_override.resolve() if output_override else root/OUTPUT
    if root not in outdir.parents:raise ValueError('Sortie hors racine de donnees : refusee')
    outdir.mkdir(parents=True,exist_ok=True)
    index,indexpath=readonly_index(root)
    with closing(index):
        sources=source_catalog(index)
        known=work_languages(index)
        chosen=sorted(set(langs) if langs else known)
        absent=[x for x in chosen if x not in known]
        if absent:raise ValueError('Langue(s) absente(s): '+', '.join(absent[:12]))
        fp=db_fingerprint(index)
        print(f'INDEX|{len(sources)}|{len(known)}|{len(chosen)}|{fp[:16]}',flush=True)
        with exclusive_lock(outdir/'reconciliation.lock'):
            with closing(stage_connection(outdir/'reconciliation.sqlite3',fp)) as staged:
                baseline=index.execute('PRAGMA data_version').fetchone()[0]
                for i,lang in enumerate(chosen,1):
                    if index.execute('PRAGMA data_version').fetchone()[0]!=baseline:
                        raise RuntimeError('Index modifie depuis le lancement; arret.')
                    print(f'LANGUAGE|{i}|{len(chosen)}|{lang}',flush=True)
                    result=process_language(index,staged,lang,sources,fp,
                        progress=lambda n:print(f'  {lang}: {n:,} observations',flush=True),
                        min_free_gb=min_free_gb,outdir=outdir)
                    print(f'[{result.upper()}] {lang}',flush=True)
                    if i%50==0:
                        print(f'CHECKPOINT|{i}|{len(chosen)}',flush=True)
                fingerprint_guard(index,fp)
                staged_count=staged.execute('SELECT COUNT(*) FROM completed_languages').fetchone()[0]
                manifest=report(root,outdir,index,staged,fp,len(known),partial=staged_count<len(known))
                print(json.dumps(manifest,ensure_ascii=False,indent=2),flush=True)
                return manifest


def verify_exports(root):
    root=valid_lake(root)
    outdir=root/OUTPUT
    dbpath=outdir/'reconciliation.sqlite3'
    if not dbpath.is_file():raise FileNotFoundError('Aucune base candidate a verifier')
    passed=0;failed=[]
    with closing(sqlite3.connect(dbpath.as_uri()+'?mode=ro',uri=True,timeout=30)) as db:
        entries=db.execute('SELECT language,exported_sha256,exported_records FROM completed_languages ORDER BY language')
        for language,expected_sha,expected_count in entries:
            if expected_count==0:
                if expected_sha!='no-candidates':failed.append((language,'empty checksum mismatch'))
                passed+=1
                continue
            target=outdir/'candidates'/safe_lang_filename(language)
            if not target.is_file():
                failed.append((language,'missing jsonl'));continue
            count=0;h=hashlib.sha256()
            with target.open('rb') as f:
                for ln in f:
                    h.update(ln);count+=1
            if h.hexdigest()!=expected_sha or count!=expected_count:
                failed.append((language,'sha256 or line count mismatch'))
            else:passed+=1
            if (passed+len(failed))%50==0:
                print(f'VERIFY|{passed+len(failed)}|ok={passed}|failed={len(failed)}',flush=True)
    report={'profile':'encyklopedia.dik-lex1-verify/v0.5','checked':passed+len(failed),
            'passed':passed,'failed':len(failed),'issues':failed[:50]}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if failed:raise RuntimeError('Des fichiers candidats doivent etre regeneres; aucune source brute touchee')
    return report


def quick_plan(root):
    root=valid_lake(root)
    with closing(readonly_index(root)[0]) as index:
        known=work_languages(index)
        print(json.dumps({'profile':PROFILE,'data_root':str(root),
          'index_found':True,'source_files':index.execute('SELECT COUNT(*) FROM source_files').fetchone()[0],
          'languages':len(known),'source_status':dict(index.execute('SELECT status,COUNT(*) FROM source_files GROUP BY status')),
          'output':str(root/OUTPUT),'scopes':['fr,en','all'],
          'warning':'Paires de graphies candidates seulement, aucune correspondance semantique auto'},
           ensure_ascii=False,indent=2))


def main(argv=None):
    parser=argparse.ArgumentParser(description='Staging massif EncyKlopedia vers diK - candidats seulement')
    parser.add_argument('command',choices=['plan','run','status','verify'])
    parser.add_argument('--data-root',default=os.environ.get('ENCYK_DATA_ROOT',r'D:\EncyKlopedia' if os.name=='nt' else ''))
    parser.add_argument('--languages',default='',help='Liste separee par virgules; defaut: toutes les langues')
    parser.add_argument('--min-free-gb',type=float,default=3.0)
    args=parser.parse_args(argv)
    if not args.data_root:parser.error('Indiquer --data-root sur ce systeme')
    root=Path(args.data_root)
    try:
        if args.command=='plan':quick_plan(root)
        elif args.command=='verify':verify_exports(root)
        elif args.command=='status':
            p=root/OUTPUT/'latest.json'
            print(p.read_text(encoding='utf-8') if p.is_file() else 'Aucune conciliation terminee')
        else:
            if args.min_free_gb<0:raise ValueError('min-free-gb negatif')
            run(root,langs=[x.strip() for x in args.languages.split(',') if x.strip()] or None,
                min_free_gb=args.min_free_gb)
        return 0
    except (OSError,ValueError,RuntimeError,sqlite3.Error) as exc:
        print('ERREUR : '+str(exc),file=sys.stderr,flush=True)
        return 2

if __name__=='__main__':raise SystemExit(main())
