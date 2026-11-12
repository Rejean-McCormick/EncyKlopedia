#!/usr/bin/env python3
"""Intégration incrémentale des ponts v26 dans le catalogue v25 existant.

Ne change pas le manifeste de branche figé v25 et ne touche pas à la base
Wikipédia en écriture. Les ponts sont des candidats d'architecture d'articles,
PAS des connaissances canoniques ni des articles publiés.

Utilisation: python -I integrer_ponts_revus_v26.py preflight|apply|verify
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import sys

# Python -I ne place pas le dossier du script sur sys.path :
# charger uniquement notre module voisin explicitement.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogue_global_v25 as v25

ROOT = Path(__file__).resolve().parent
DEFAULT_CSV = ROOT / 'v26_data' / 'PONTS_REVUS_V26_c1126b2f88bb.csv'
DEFAULT_BRANCH = ROOT / 'v25_data' / 'branche_mt110.json'
REVIEW_SCHEMA = 'encyklopedia.reviewed-bridge-import.v26/1'


def read_bridges(path, branch):
    if not path.is_file():
        raise v25.Refusal('CSV de décisions v26 absent: ' + str(path))
    data = path.read_bytes()
    try:
        raw = data.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(raw, newline=''))
        wanted = {'concept_id','category_title','status','justification','depth_limit','decision'}
        if set(reader.fieldnames or []) != wanted:
            raise v25.Refusal('Colonnes CSV incompatibles avec le contrat v26')
        concepts = {c['unesco_id'] for c in branch['concepts']}
        seen = set()
        seen_includes = set()
        includes = []
        counts = {'INCLUDE':0,'EXCLUDE':0,'HOLD':0}
        for number, r in enumerate(reader, 2):
            cid = r['concept_id'].strip()
            title = ' '.join(r['category_title'].replace('_',' ').split())
            status = r['status'].strip()
            decision = r['decision'].strip()
            reason = r['justification'].strip()
            depth = int(r['depth_limit'].strip())
            if cid not in concepts or not title or len(title)>255:
                raise v25.Refusal(f'Concept ou categorie invalide ligne {number}: {cid} -> {title}')
            # Les décisions HOLD/EXCLUDE peuvent contenir des variantes historiques
            # (casse différente) : elles ne sont pas activées dans v25.
            key = (cid, title)
            if key in seen:
                raise v25.Refusal(f'Categorie / concept en double ligne {number}: {cid} -> {title}')
            seen.add(key)
            if decision not in counts or (status == 'ACTIVE_REVIEWED_AI') != (decision == 'INCLUDE'):
                raise v25.Refusal(f'Decision/statut incoherent ligne {number}')
            if status not in ('ACTIVE_REVIEWED_AI', 'PROPOSED_NOT_ACTIVE'):
                raise v25.Refusal(f'Statut inconnu ligne {number}')
            if not 0 <= depth <= int(branch['spec']['discovery']['max_reviewed_root_depth']):
                raise v25.Refusal(f'Profondeur invalide ligne {number}')
            if decision == 'INCLUDE':
                active_key = (cid, v25.normalize(title))
                if active_key in seen_includes or not v25.topic_category(title):
                    raise v25.Refusal(f'Pont actif ambigu ligne {number}: {cid} -> {title}')
                seen_includes.add(active_key)
                if len(reason) < 20 or depth != 0:
                    raise v25.Refusal(f'Justification ou profondeur active invalide ligne {number}')
                includes.append({'concept_id':cid,'category_title':title,
                                 'reason':reason,'depth':depth})
            counts[decision] += 1
    except (UnicodeError, csv.Error) as exc:
        raise v25.Refusal('CSV v26 illisible: ' + str(exc)) from exc
    if not includes or not (counts['INCLUDE'] + counts['EXCLUDE'] + counts['HOLD']):
        raise v25.Refusal('Aucun pont actif dans le fichier de décisions')
    return {'sha256':hashlib.sha256(data).hexdigest(),'counts':counts,
            'reviewed':sum(counts.values()),'included':includes}


def read_catalogue_ro(path):
    if not path.is_file() or path.is_symlink():
        raise v25.Refusal('Catalogue v25 existant requis: aucune base vide ne sera creee')
    db = sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=60)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    return db


def verify_catalogue(db, branch, source_sha):
    if v25.meta(db,'schema')!=v25.SCHEMA:
        raise v25.Refusal('Schema du catalogue v25 incompatible')
    if v25.meta(db,'source_sha')!=source_sha:
        raise v25.Refusal('Source Wikipedia differente de celle du catalogue v25')
    row=db.execute('SELECT vocabulary,config_sha,max_category_tasks,category_tasks '
                   'FROM branches WHERE branch_id=?', (branch['id'],)).fetchone()
    if not row:
        raise v25.Refusal('Branche absente du catalogue; creer la branche avec v25 d\'abord')
    if row['vocabulary']!=branch['vocab'] or row['config_sha']!=branch['signature']:
        raise v25.Refusal('Configuration v25 modifiee: import refuse, aucune mutation silencieuse')
    n=db.execute('SELECT count(*) FROM branch_concepts WHERE branch_id=?',(branch['id'],)).fetchone()[0]
    if n!=len(branch['concepts']):
        raise v25.Refusal('Incoherence des concepts deja inscrits dans le catalogue')
    return row


def existing_reviewed(db):
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='reviewed_bridges_v26'").fetchone():
        return {(r['branch_id'],r['concept_id'],v25.normalize(r['category_title'])):dict(r)
                for r in db.execute('SELECT * FROM reviewed_bridges_v26')}
    return {}


def validate_plan(src, db, branch, review, source_sha):
    row=verify_catalogue(db,branch,source_sha)
    prior=existing_reviewed(db)
    rows=[]
    for r in review['included']:
        tid=v25.cat_target(src,r['category_title'])
        if not tid or tid < 1:
            raise v25.Refusal('Categorie v26 active sans linktarget sur le dump courant: '+r['category_title'])
        entry=(branch['id'],r['concept_id'],v25.normalize(r['category_title']))
        if entry in prior:
            old=prior[entry]
            if (old['category_title']!=r['category_title'] or old['target_id']!=tid
                or old['justification']!=r['reason'] or old['depth_limit']!=r['depth']):
                raise v25.Refusal('Pont deja audite avec une autre definition: '+r['category_title'])
        current=db.execute('''SELECT task_id FROM category_tasks WHERE branch_id=? AND concept_id=?
                              AND root_category=? AND target_id=? LIMIT 1''',
                           (branch['id'],r['concept_id'],r['category_title'],tid)).fetchone()
        rows.append({**r,'target_id':tid,'existing_task':int(current['task_id']) if current else None,
                     'existing_review':entry in prior})
    n_new_tasks=sum(1 for r in rows if r['existing_task'] is None)
    if int(row['category_tasks']) + n_new_tasks > int(row['max_category_tasks']):
        raise v25.Refusal('Budget de taches depasse: reduire les ponts ou augmenter explicitement la limite v25')
    return rows


def create_ledger(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS reviewed_bridge_imports_v26 (
      branch_id TEXT NOT NULL, csv_sha256 TEXT NOT NULL, schema_name TEXT NOT NULL,
      reviewed_count INTEGER NOT NULL, active_count INTEGER NOT NULL,
      imported_utc TEXT NOT NULL,
      PRIMARY KEY (branch_id, csv_sha256));
    CREATE TABLE IF NOT EXISTS reviewed_bridges_v26 (
      branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,category_title TEXT NOT NULL,
      target_id INTEGER NOT NULL,depth_limit INTEGER NOT NULL,
      justification TEXT NOT NULL,source_csv_sha256 TEXT NOT NULL,
      imported_utc TEXT NOT NULL,
      PRIMARY KEY (branch_id,concept_id,category_title));
    ''')
    db.commit()


def apply_rows(db, branch, review, rows):
    bid=branch['id']
    create_ledger(db)
    new_reviews=0
    new_tasks=0
    db.execute('BEGIN IMMEDIATE')
    try:
        imported=db.execute('SELECT reviewed_count,active_count FROM reviewed_bridge_imports_v26 '
                            'WHERE branch_id=? AND csv_sha256=?',(bid,review['sha256'])).fetchone()
        if imported and (int(imported['reviewed_count'])!=review['reviewed'] or
                         int(imported['active_count'])!=len(rows)):
            raise v25.Refusal('Le registre d\'import contient un bilan incoherent')
        if not imported:
            db.execute('INSERT INTO reviewed_bridge_imports_v26 VALUES(?,?,?,?,?,?)',
                       (bid,review['sha256'],REVIEW_SCHEMA,review['reviewed'],len(rows),v25.now()))
        for r in rows:
            if not r['existing_review']:
                db.execute('''INSERT INTO reviewed_bridges_v26
                   (branch_id,concept_id,category_title,target_id,depth_limit,
                    justification,source_csv_sha256,imported_utc)
                   VALUES(?,?,?,?,?,?,?,?)''',
                   (bid,r['concept_id'],r['category_title'],r['target_id'],r['depth'],
                    r['reason'],review['sha256'],v25.now()))
                new_reviews+=1
            if r['existing_task'] is None:
                v25.enqueue(db,branch,r['concept_id'],r['category_title'],r['category_title'],
                            r['target_id'],0,r['depth'],'AI_REVIEWED_BRIDGE_CANDIDATE')
                new_tasks+=1
        if not imported:
            db.execute('INSERT INTO audit_events(branch_id,kind,description,created_utc) VALUES(?,?,?,?)',
                       (bid,'V26_EXPLICIT_REVIEWED_BRIDGE_IMPORT',json.dumps({
                           'csv_sha256':review['sha256'],'decisions':review['reviewed'],
                           'approved':len(rows),'new_tasks':new_tasks},sort_keys=True),v25.now()))
        if new_reviews or new_tasks or not imported:
            v25.tick(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {'new_reviewed_bridges':new_reviews,'new_tasks':new_tasks}


def brief(db, bid):
    sql='''SELECT count(*) AS total FROM reviewed_bridges_v26 WHERE branch_id=?'''
    has_review=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='reviewed_bridges_v26'").fetchone()
    reviewed=int(db.execute(sql,(bid,)).fetchone()[0]) if has_review else 0
    return {'unique_articles':int(db.execute('SELECT count(*) FROM articles').fetchone()[0]),
            'assignments':int(db.execute('SELECT count(*) FROM assignments').fetchone()[0]),
            'active_bridges_in_ledger':reviewed,
            'tasks_pending':int(db.execute("SELECT count(*) FROM category_tasks WHERE branch_id=? AND state='PENDING'",(bid,)).fetchone()[0]),
            'tasks_capped':int(db.execute("SELECT count(*) FROM category_tasks WHERE branch_id=? AND state='CAPPED'",(bid,)).fetchone()[0]),
            'sequence':int(v25.meta(db,'sequence') or 0)}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=('preflight','apply','verify'))
    ap.add_argument('--source-db',type=Path,default=v25.DEFAULT_SOURCE)
    ap.add_argument('--catalogue-db',type=Path,default=v25.DEFAULT_CATALOG)
    ap.add_argument('--output-dir',type=Path,default=v25.DEFAULT_OUTPUT)
    ap.add_argument('--branch',type=Path,default=DEFAULT_BRANCH)
    ap.add_argument('--reviewed-bridges',type=Path,default=DEFAULT_CSV)
    ap.add_argument('--max-batches',type=int,default=5000)
    ap.add_argument('--batch-size',type=int,default=2000)
    ap.add_argument('--sample-limit',type=int,default=300)
    a=ap.parse_args(argv)
    if not (0 <= a.max_batches <= 100000 and 10 <= a.batch_size <= 5000
            and 10 <= a.sample_limit <= 10000):
        raise v25.Refusal('Parametres d\'execution hors limites')
    if a.source_db.resolve()==a.catalogue_db.resolve():
        raise v25.Refusal('La base source Wikipedia et le catalogue doivent etre distincts')
    if a.action=='verify':
        db=read_catalogue_ro(a.catalogue_db)
        try:
            branch=v25.load_branch(a.branch)
            review=read_bridges(a.reviewed_bridges,branch)
            if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='reviewed_bridge_imports_v26'").fetchone():
                raise v25.Refusal('Aucun registre de ponts v26 importe')
            entry=db.execute('SELECT reviewed_count,active_count FROM reviewed_bridge_imports_v26 '
                             'WHERE branch_id=? AND csv_sha256=?',(branch['id'],review['sha256'])).fetchone()
            if not entry or tuple(entry)!=(review['reviewed'],len(review['included'])):
                raise v25.Refusal('Import v26 absent ou incomplet pour ce fichier de decisions')
            for r in review['included']:
                existing=db.execute('SELECT target_id,depth_limit,justification FROM reviewed_bridges_v26 '
                                    'WHERE branch_id=? AND concept_id=? AND category_title=?',
                                    (branch['id'],r['concept_id'],r['category_title'])).fetchone()
                if not existing or int(existing['depth_limit'])!=r['depth'] or existing['justification']!=r['reason']:
                    raise v25.Refusal('Pont v26 manquant ou different: '+r['category_title'])
                task=db.execute('SELECT 1 FROM category_tasks WHERE branch_id=? AND concept_id=? '
                                'AND root_category=? AND target_id=?',
                                (branch['id'],r['concept_id'],r['category_title'],existing['target_id'])).fetchone()
                if not task:
                    raise v25.Refusal('Tache manquante pour le pont: '+r['category_title'])
            snap=v25.read_json(a.output_dir/'LATEST.json')
            folder=(a.output_dir/snap['snapshot']).resolve()
            if a.output_dir.resolve() not in folder.parents:
                raise v25.Refusal('Chemin LATEST sort de son repertoire')
            verified=v25.verify_snapshot(folder)
            report=v25.read_json(folder/'RAPPORT_V25.json')
            if report.get('snapshot_sequence')!=int(v25.meta(db,'sequence') or 0):
                raise v25.Refusal('Le dernier snapshot ne correspond pas a la base catalogue courante')
            result={'status':'V26_BRIDGES_VERIFY_OK',**brief(db,branch['id']),
                    'snapshot':verified,'canonical_admissions':0,'publication_authorized':False}
            print(json.dumps(result,ensure_ascii=False,indent=2));return 0
        finally:db.close()
    branch=v25.load_branch(a.branch)
    review=read_bridges(a.reviewed_bridges,branch)
    src=v25.source_ro(a.source_db)
    try:
        source_info,source_sha=v25.source_fingerprint(src,a.source_db)
        if a.action=='preflight':
            db=read_catalogue_ro(a.catalogue_db)
        else:
            # Do not create a new v25 database if the original is missing.
            if not a.catalogue_db.is_file() or a.catalogue_db.is_symlink():
                raise v25.Refusal('Catalogue original absent: import incremental impossible')
            db=v25.open_catalog(a.catalogue_db)
        try:
            plan=validate_plan(src,db,branch,review,source_sha)
            baseline=brief(db,branch['id'])
            if a.action=='preflight':
                result={'status':'V26_BRIDGES_PREFLIGHT_OK','branch_id':branch['id'],
                        'decisions_reviewed':review['reviewed'],'selected':len(plan),
                        'already_registered':sum(r['existing_review'] for r in plan),
                        'existing_tasks':sum(r['existing_task'] is not None for r in plan),
                        'tasks_to_add':sum(r['existing_task'] is None for r in plan),
                        'review_sha256':review['sha256'],'before':baseline,
                        'source_sql_read_only':True,'canonical_admissions':0}
                print(json.dumps(result,ensure_ascii=False,indent=2));return 0
            result_apply=apply_rows(db,branch,review,plan)
            examined=0
            batches=0
            for i in range(a.max_batches):
                work=v25.work_one_batch(src,db,{branch['id']:branch},a.batch_size,branch_filter=branch['id'])
                if work is None:break
                batches+=1
                examined+=int(work['processed'])
                if i==0 or (i+1)%25==0:
                    print(json.dumps({'event':'V26_BRIDGE_PROGRESS','batch':i+1,**work},ensure_ascii=False),flush=True)
            _,last_sig=v25.source_fingerprint(src,a.source_db)
            if last_sig!=source_sha:
                raise v25.Refusal('La base source Wikipedia a change pendant la session')
            snapshot=v25.snapshot(db,a.catalogue_db,a.output_dir,a.sample_limit)
            after=brief(db,branch['id'])
            if after['unique_articles']<baseline['unique_articles'] or after['assignments']<baseline['assignments']:
                raise v25.Refusal('Regression de la couverture de catalogue detectee')
            result={'status':'V26_BRIDGES_APPLIED_OK','branch_id':branch['id'],
                    'decisions_reviewed':review['reviewed'],'bridges_approved':len(plan),
                    **result_apply,'batches_processed':batches,'members_examined':examined,
                    'before':baseline,'after':after,'net_new_articles':after['unique_articles']-baseline['unique_articles'],
                    'net_new_assignments':after['assignments']-baseline['assignments'],
                    'source_sql_read_only':True,'canonical_admissions':0,'publication_authorized':False,
                    'reader':snapshot['reader'],'export':snapshot['export']}
            print(json.dumps(result,ensure_ascii=False,indent=2));return 0
        finally:db.close()
    finally:src.close()


if __name__=='__main__':
    try:sys.exit(main())
    except (v25.Refusal,sqlite3.Error,OSError,ValueError,TypeError,KeyError,UnicodeError,json.JSONDecodeError) as e:
        print(json.dumps({'status':'V26_BRIDGES_REFUS','reason':str(e)},ensure_ascii=False),file=sys.stderr)
        sys.exit(2)
