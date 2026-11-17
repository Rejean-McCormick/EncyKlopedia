#!/usr/bin/env python3
"""Diagnostic ENCYKLOPEDIA v31 : couverture de la branche, en lecture seule.

Ne fait AUCUNE écriture dans les bases ; ne relance pas la découverte ni les tâches.
Python 3.10+ ; standard library seulement.
"""
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

DEFAULT_STATION = Path(r'D:\EncyKlopedia\30_working\poste_chatgpt_v30\station_v30.sqlite')
DEFAULT_CATALOGUE = Path(r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite')
DEFAULT_DISCOVERY = Path(r'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28\DECOUVERTE_ARTICLES_RELIES_V28.sqlite')


def connect_ro(path):
    if not path.is_file():
        return None
    # sqlite read-only mode: respects SQLite's live WAL; never opens writable.
    connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA query_only=ON')
    return connection


@contextmanager
def open_readonly(path):
    con = connect_ro(path)
    try:
        yield con
    finally:
        if con is not None:
            con.close()


def has_table(con, name):
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def scalar(con, sql, args=()):
    return con.execute(sql, args).fetchone()[0]


def grouped(con, sql, args=()):
    return {str(r[0]): int(r[1]) for r in con.execute(sql, args)}


def pct(a, b):
    return round(a * 100.0 / b, 2) if isinstance(a, (int, float)) and b else None


def metadata(path):
    if not path.is_file():
        return {'available': False, 'path': str(path)}
    return {'available': True, 'path': str(path),
            'size_bytes': path.stat().st_size,
            'modified_utc': datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()}


def measure(a):
    result = {
        'schema': 'encyklopedia.audit-achievement.v31-readonly/1',
        'created_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'branch_id': a.branche,
        'sources': {name: metadata(path) for name, path in [('station', a.station), ('catalogue', a.catalogue), ('decouverte', a.decouverte)]},
        'catalogue': {}, 'decouverte': {}, 'station': {},
        'achevement_reel_pct': None,
        'avertissements': [],
        'commentaire': 'Aucun pourcentage global unique : le rappel et la saturation exploratoire exigent un audit et des campagnes répétées.'
    }
    w = result['avertissements']

    # The catalogue contains already catalogued pairs, v28-approved and rejected
    # pairs, and the branch's explicitly configured concepts. Avoid conflating them.
    with open_readonly(a.catalogue) as con:
        if con is None:
            w.append('Catalogue indisponible : concepts et décisions importées inconnus.')
        else:
            d = result['catalogue']
            if has_table(con, 'branch_concepts'):
                d['concepts_configures'] = scalar(con, 'SELECT COUNT(DISTINCT concept_id) FROM branch_concepts WHERE branch_id=?', (a.branche,))
            else:
                d['concepts_configures'] = None
                w.append('Table branch_concepts absente du catalogue.')
            if has_table(con, 'assignments'):
                d['affectations_paires'] = scalar(con, '''SELECT COUNT(*) FROM (
                    SELECT DISTINCT concept_id, page_id FROM assignments WHERE branch_id=? AND wiki='enwiki')''', (a.branche,))
                d['articles_distincts_affectes'] = scalar(con, '''SELECT COUNT(DISTINCT page_id)
                    FROM assignments WHERE branch_id=? AND wiki='enwiki' ''', (a.branche,))
                d['concepts_avec_affectation'] = scalar(con, '''SELECT COUNT(DISTINCT concept_id)
                    FROM assignments WHERE branch_id=? AND wiki='enwiki' ''', (a.branche,))
            else:
                w.append('Table assignments absente : couverture historique des concepts inconnue.')
            if has_table(con, 'reviewed_article_links_v28'):
                d['decisions_importees_v28'] = grouped(con, '''SELECT UPPER(decision), COUNT(*)
                    FROM reviewed_article_links_v28 WHERE branch_id=? GROUP BY UPPER(decision)''', (a.branche,))
                d['concepts_avec_approve_v28'] = scalar(con, '''SELECT COUNT(DISTINCT concept_id)
                    FROM reviewed_article_links_v28 WHERE branch_id=? AND UPPER(decision)='APPROVE' ''', (a.branche,))
                d['candidats_distincts_decides_v28'] = scalar(con, '''SELECT COUNT(DISTINCT candidate_id)
                    FROM reviewed_article_links_v28 WHERE branch_id=?''', (a.branche,))
                d['couverture_concepts_approve_v28_pct'] = pct(d['concepts_avec_approve_v28'], d['concepts_configures'])
            else:
                w.append('Table reviewed_article_links_v28 absente : APPROVE/REJECT importés inconnus.')

    # Discovery measurements: these are local stock metrics, NOT the global
    # number of Wikipedia pages that could be relevant to this branch.
    with open_readonly(a.decouverte) as con:
        if con is None:
            w.append('Base de découverte absente : stock connu et graines non mesurables.')
        else:
            d = result['decouverte']
            if has_table(con, 'candidates'):
                d['couples_candidats_distincts'] = scalar(con, '''SELECT COUNT(*) FROM (
                    SELECT DISTINCT concept_id,page_id FROM candidates WHERE branch_id=?)''', (a.branche,))
                d['pages_candidates_distinctes'] = scalar(con, '''SELECT COUNT(DISTINCT page_id)
                    FROM candidates WHERE branch_id=?''', (a.branche,))
            else:
                w.append('Table candidates absente de la découverte.')
            if has_table(con, 'seed_queue'):
                d['graines_par_etat'] = grouped(con, '''SELECT state,COUNT(*) FROM seed_queue
                    WHERE branch_id=? GROUP BY state''', (a.branche,))
                seeds = d['graines_par_etat']
                d['graines_connues_total'] = sum(seeds.values())
                d['graines_connues_terminees_pct'] = pct(seeds.get('DONE', 0), d['graines_connues_total'])
                d['graines_en_attente'] = seeds.get('PENDING', 0)
            else:
                w.append('Table seed_queue absente : saturation de la découverte impossible à apprécier.')

    # Station measurement: DECIDED and HOLD are reviews that reached DONE,
    # but HOLD is explicitly unresolved. DEFERRED, SKIPPED, STALE are NOT done.
    with open_readonly(a.station) as con:
        if con is None:
            w.append('Base station absente : aucune mesure du travail réellement importé.')
        else:
            d = result['station']
            if has_table(con, 'review_index'):
                d['candidats_par_etat'] = grouped(con, '''SELECT state,COUNT(*) FROM review_index
                    WHERE branch_id=? GROUP BY state''', (a.branche,))
                states = d['candidats_par_etat']
                total = sum(states.values())
                d['candidats_suivis'] = total
                d['revus_avec_import'] = states.get('DECIDED', 0) + states.get('HOLD', 0)
                d['decisions_tranchees'] = states.get('DECIDED', 0)
                d['en_attente_ou_a_revoir'] = total - d['decisions_tranchees']
                d['avancement_stock_station_revu_pct'] = pct(d['revus_avec_import'], total)
                d['avancement_stock_station_tranche_pct'] = pct(d['decisions_tranchees'], total)
                d['hold_importes_non_tranches'] = states.get('HOLD', 0)
            else:
                w.append('Table review_index absente : stock station inconnu.')
            if has_table(con, 'jobs') and has_table(con, 'v311_job_routes'):
                # Native legacy UNESCO jobs have no v311 route row.
                d['jobs_v28_par_etat'] = grouped(con, '''SELECT j.status,COUNT(*)
                    FROM jobs j LEFT JOIN v311_job_routes r ON r.job_id=j.id
                    WHERE j.kind='v28' AND COALESCE(r.branch_id,'unesco.mt1.10')=?
                    GROUP BY j.status''', (a.branche,))
                jobs = d['jobs_v28_par_etat']
                d['jobs_importes_pct_file_existante'] = pct(jobs.get('DONE', 0), sum(jobs.values()))
                d['jobs_unesco_ouverts'] = sum(jobs.get(s, 0) for s in ('WAITING','READY','SENT','ERROR','IMPORTING','NEEDS_CONFIRMATION'))
            else:
                w.append('Tables jobs/routes absentes : répartition des tâches par branche inconnue.')

    # Exhaustion cannot be proven from a snapshot; especially with queue freeze,
    # fresh seeds may be added only after a future discovery cycle.
    d = result['decouverte']
    s = result['station']
    result['criteres_de_cloture'] = {
        'pas_de_graines_pendantes_observees': (d.get('graines_en_attente') == 0) if 'graines_en_attente' in d else None,
        'pas_de_jobs_unesco_ouverts_observes': (s.get('jobs_unesco_ouverts') == 0) if 'jobs_unesco_ouverts' in s else None,
        'pas_de_candidats_non_tranches_station': (s.get('en_attente_ou_a_revoir') == 0) if 'en_attente_ou_a_revoir' in s else None,
        'saturation_exploratoire_demontree': None,
        'rappel_estime_sur_candidats_differes': None,
        'sources_coherentes_meme_generation': None,
    }
    if a.branche != 'unesco.mt1.10':
        w.append('Le fichier de découverte par défaut correspond à la branche historique ; renseigner --decouverte pour une autre branche.')
    w.extend([
        'Les trois bases sont interrogées séparément : une activité concurrente peut produire un état non atomique ; utiliser des snapshots SQLite cohérents si nécessaire.',
        'Le nombre de graines PENDING à zéro ne démontre pas l\'épuisement de la branche : de nouvelles graines peuvent apparaître après extension du catalogue.',
        'Le taux de revue de la station exclut des candidats déjà traités avant son index ; ce n\'est pas le pourcentage du monde Wikipédia.',
        'Les décisions HOLD restent non tranchées, et aucune donnée Kristal ne contribue aux totaux UNESCO.'
    ])
    return result



# ---------------------------------------------------------------------------
# Rapprochement automatisé v31.2 — strictement lecture seule pour les bases.
# Les fichiers produits sont uniquement dans le répertoire de rapports choisi.
# ---------------------------------------------------------------------------
import csv
import gzip
import hashlib
import os
import tempfile
from collections import defaultdict
from types import SimpleNamespace

AUTO_SCHEMA = 'encyklopedia.audit-couverture-auto.v31.2/1'
ACTION_STATES = {'HOLD', 'PENDING', 'DEFERRED', 'SKIPPED', 'STALE',
                 'QUEUED', 'ERROR', 'WAITING', 'READY', 'SENT',
                 'IMPORTING', 'NEEDS_CONFIRMATION'}


def sql_columns(con, table):
    if not has_table(con, table):
        return set()
    return {r['name'] for r in con.execute('PRAGMA table_info(' + table + ')')}


def key_of(concept_id, page_id):
    return (str(concept_id), int(page_id))


def key_json(k):
    return json.dumps([k[0], k[1]], ensure_ascii=False, separators=(',', ':'))


def safe_branch_filename(branch):
    return ''.join(c if c.isalnum() or c in '-_.' else '_' for c in branch)[:90]


def analyze_branch(args):
    """Return report and export rows. Does not mutate any SQLite database."""
    base = measure(args)
    branch = args.branche
    details = {}
    discovery = {}
    ledger = {}
    station_index = {}
    assignments = set()
    errors = []
    evidence_conflicts = []

    with open_readonly(args.catalogue) as con:
        if con is not None:
            if has_table(con, 'branch_concepts'):
                cols = sql_columns(con, 'concepts')
                if {'vocabulary', 'concept_id', 'label_fr', 'label_en'}.issubset(cols):
                    for r in con.execute('''SELECT b.concept_id,c.label_fr,c.label_en
                        FROM branch_concepts b LEFT JOIN concepts c
                        ON b.vocabulary=c.vocabulary AND b.concept_id=c.concept_id
                        WHERE b.branch_id=?''', (branch,)):
                        details[str(r['concept_id'])] = (r['label_fr'] or r['label_en'] or r['concept_id'])
                else:
                    for r in con.execute('SELECT DISTINCT concept_id FROM branch_concepts WHERE branch_id=?',(branch,)):
                        details[str(r[0])] = str(r[0])
            if has_table(con, 'assignments'):
                assignments = {key_of(r['concept_id'],r['page_id']) for r in con.execute(
                    "SELECT concept_id,page_id FROM assignments WHERE branch_id=? AND wiki='enwiki'",(branch,))}
            if has_table(con, 'reviewed_article_links_v28'):
                for r in con.execute('''SELECT concept_id,page_id,candidate_id,evidence_sha256,decision
                        FROM reviewed_article_links_v28 WHERE branch_id=?''',(branch,)):
                    k=key_of(r['concept_id'],r['page_id'])
                    ledger[k]={'candidate_id':r['candidate_id'], 'evidence_sha256':r['evidence_sha256'],
                               'decision':str(r['decision']).upper()}

    with open_readonly(args.decouverte) as con:
        if con is not None and has_table(con, 'candidates'):
            for r in con.execute('''SELECT concept_id,page_id,title,first_seen
                    FROM candidates WHERE branch_id=?''',(branch,)):
                discovery[key_of(r['concept_id'],r['page_id'])] = {
                    'title':r['title'], 'first_seen':r['first_seen']}

    with open_readonly(args.station) as con:
        if con is not None and has_table(con, 'review_index'):
            for r in con.execute('''SELECT concept_id,page_id,candidate_id,title,state,priority,
                    seed_count,link_evidence,category_evidence,subcategory_evidence,
                    task_id,evidence_sha256,last_seen_utc
                    FROM review_index WHERE branch_id=?''',(branch,)):
                k=key_of(r['concept_id'],r['page_id'])
                if k in station_index:
                    errors.append('Clé concept/page présente plusieurs fois en station : '+key_json(k))
                station_index[k] = {field:r[field] for field in r.keys()}

    discovered_keys=set(discovery)
    catalog_keys=set(ledger)
    station_keys=set(station_index)
    known_keys=discovered_keys | catalog_keys | station_keys
    not_tracked=discovered_keys - (catalog_keys | station_keys)
    import_without_discovery=catalog_keys-discovered_keys
    station_without_discovery=station_keys-discovered_keys
    waiting_keys={k for k,r in station_index.items() if str(r['state']).upper() not in ('DECIDED', 'HOLD')}
    holds_keys={k for k,r in station_index.items() if str(r['state']).upper()=='HOLD'}
    overlap_decided={k for k in station_keys & catalog_keys
                      if str(station_index[k]['state']).upper()=='DECIDED'}

    for k in station_keys & catalog_keys:
        stat_sha=station_index[k].get('evidence_sha256')
        led_sha=ledger[k].get('evidence_sha256')
        if stat_sha and led_sha and str(stat_sha).lower()!=str(led_sha).lower():
            evidence_conflicts.append(k)
        sid=station_index[k].get('candidate_id')
        lid=ledger[k].get('candidate_id')
        if sid and lid and sid!=lid:
            errors.append('Identifiants différents pour la même paire : '+key_json(k))

    by_concept=defaultdict(lambda: defaultdict(int))
    for c,_ in known_keys: by_concept[c]['known']+=1
    for c,_ in discovered_keys: by_concept[c]['discovery']+=1
    for c,_ in assignments: by_concept[c]['assignments']+=1
    for k,r in ledger.items():by_concept[k[0]]['import_'+r['decision']]+=1
    for k,r in station_index.items():by_concept[k[0]]['station_'+str(r['state']).upper()]+=1
    for c,_ in not_tracked:by_concept[c]['untracked']+=1
    for c,_ in waiting_keys:by_concept[c]['pending_review']+=1
    for c,_ in holds_keys:by_concept[c]['hold']+=1
    for c,_ in import_without_discovery:by_concept[c]['import_without_discovery']+=1

    concept_rows=[]
    for c in sorted(set(details) | set(by_concept)):
        counts=by_concept[c]
        reasons=[]
        if c not in details:reasons.append('CONCEPT_HORS_CONFIGURATION')
        if not counts['discovery']:reasons.append('AUCUN_CANDIDAT_DECOUVERT')
        if not counts['assignments']:reasons.append('AUCUNE_AFFECTATION')
        if not counts['import_APPROVE']:reasons.append('AUCUN_APPROVE_V28')
        if counts['hold']:reasons.append('HOLD_A_REVOIR')
        if counts['untracked']:reasons.append('CANDIDATS_NON_SUIVIS')
        concept_rows.append({
            'branch_id':branch,'concept_id':c,'label_fr':details.get(c,c),
            'configured':'oui' if c in details else 'non',
            'candidats_connus':counts['known'],
            'candidats_decouverts':counts['discovery'],
            'affectations_catalogue':counts['assignments'],
            'approve_importes':counts['import_APPROVE'],
            'reject_importes':counts['import_REJECT'],
            'hold_station':counts['hold'],
            'a_revoir_autres_etats':counts['pending_review'],
            'decided_station':counts['station_DECIDED'],
            'absents_station_et_catalogue':counts['untracked'],
            'decisions_hors_decouverte':counts['import_without_discovery'],
            'alertes':';'.join(reasons)})
    concept_rows.sort(key=lambda r:(r['configured']!='oui',r['approve_importes']>0,
                                    -r['absents_station_et_catalogue'],-r['hold_station'],r['concept_id']))

    actions=[]
    for k in sorted(known_keys):
        d=discovery.get(k,{})
        s=station_index.get(k,{})
        l=ledger.get(k,{})
        state=str(s.get('state','')).upper()
        types=[]
        if k in not_tracked:types.append('DECOUVERT_NON_SUIVI')
        if state=='HOLD':types.append('HOLD_A_REVOIR')
        elif state and state!='DECIDED':types.append('ETAT_STATION_'+state)
        if k in evidence_conflicts:types.append('EMPREINTE_DIVERGENTE')
        if k in import_without_discovery:types.append('IMPORT_HORS_DECOUVERTE')
        if not types:continue
        actions.append({
            'type':'|'.join(types),'branch_id':branch,'concept_id':k[0],
            'concept_fr':details.get(k[0],k[0]),'page_id':k[1],
            'candidate_id':s.get('candidate_id') or l.get('candidate_id') or '',
            'title':s.get('title') or d.get('title') or '',
            'etat_station':state,'decision_importee':l.get('decision',''),
            'priority':s.get('priority') if s.get('priority') is not None else '',
            'seed_count':s.get('seed_count') if s.get('seed_count') is not None else '',
            'liens':s.get('link_evidence') if s.get('link_evidence') is not None else '',
            'categories':s.get('category_evidence') if s.get('category_evidence') is not None else '',
            'sous_categories':s.get('subcategory_evidence') if s.get('subcategory_evidence') is not None else '',
            'evidence_sha256_station':s.get('evidence_sha256') or '',
            'evidence_sha256_catalogue':l.get('evidence_sha256') or '',
            'task_id':s.get('task_id') or ''})
    sort_priority={'EMPREINTE_DIVERGENTE':0,'HOLD_A_REVOIR':1,'DECOUVERT_NON_SUIVI':2}
    actions.sort(key=lambda r:(min((v for k,v in sort_priority.items() if k in r['type']),default=3),
                               -int(r['priority'] or 0),r['concept_id'],r['page_id']))

    # Échantillon déterministe, stratifié, pour audit humain des omissions.
    # Aucun résultat de ce prélèvement n'est interprété comme un verdict.
    strata={
        'REJECT_IMPORTE': {k for k,v in ledger.items() if v['decision']=='REJECT'},
        'HOLD_STATION': holds_keys,
        'DECOUVERT_NON_SUIVI': not_tracked,
        'ETAT_NON_TRANCHE_HORS_HOLD': waiting_keys,
    }
    samples=[]
    for stratum,keys_group in strata.items():
        ordered=sorted(keys_group,key=lambda k:hashlib.sha256(
            (stratum+'|'+k[0]+'|'+str(k[1])).encode('utf8')).hexdigest())
        # Interleave concepts so the sample does not collapse into one category.
        concepts_buckets=defaultdict(list)
        for k in ordered:concepts_buckets[k[0]].append(k)
        sampled=[]
        while len(sampled)<min(30,len(ordered)):
            did_one=False
            for c in sorted(concepts_buckets):
                if concepts_buckets[c]:
                    sampled.append(concepts_buckets[c].pop(0))
                    did_one=True
                    if len(sampled)>=30:break
            if not did_one:break
        for k in sampled:
            si=station_index.get(k,{})
            l=ledger.get(k,{})
            d=discovery.get(k,{})
            samples.append({
                'strate':stratum,'branch_id':branch,'concept_id':k[0],
                'concept_fr':details.get(k[0],k[0]),'page_id':k[1],
                'candidate_id':si.get('candidate_id') or l.get('candidate_id') or '',
                'title':si.get('title') or d.get('title') or '',
                'decision_initiale':l.get('decision') or si.get('state') or '',
                'controle_humain':'', 'note_humaine':''})

    base['schema']=AUTO_SCHEMA
    base['rapprochement']={
        'paires_union_connues':len(known_keys),
        'paires_decouvertes':len(discovered_keys),
        'paires_presentes_station':len(station_keys),
        'paires_decidees_catalogue':len(catalog_keys),
        'paires_decouvertes_absentes_station_et_catalogue':len(not_tracked),
        'paires_decouvertes_non_decidees_catalogue':len(discovered_keys-catalog_keys),
        'paires_decouvertes_avec_decision_catalogue':len(discovered_keys & catalog_keys),
        'paires_station_hors_decouverte':len(station_without_discovery),
        'decisions_catalogue_hors_decouverte':len(import_without_discovery),
        'paires_station_hold':len(holds_keys),
        'paires_station_autres_non_tranchees':len(waiting_keys),
        'paires_station_decided_et_importees_catalogue':len(overlap_decided),
        'empreintes_divergentes_station_catalogue':len(evidence_conflicts),
        'concepts_configures_sans_affectation':sum(1 for r in concept_rows if r['configured']=='oui' and r['affectations_catalogue']==0),
        'concepts_configures_sans_approve':sum(1 for r in concept_rows if r['configured']=='oui' and r['approve_importes']==0),
        'concepts_configures_sans_candidat_decouvert':sum(1 for r in concept_rows if r['configured']=='oui' and r['candidats_decouverts']==0),
        'lignes_a_revoir_exportables':len(actions),
    }
    base['audit_auto']={
        'indicateur_achevement_reel':None,
        'preuve_de_saturation':'NON_DEMONTREE',
        'controle_des_omissions':'NON_REALISE : requires independent document review',
        'gel_preuves_respecte':True,
        'nombre_concepts_detailles':len(concept_rows),
        'echantillon_controle_omissions':len(samples),
        'anomalies':errors[:30],
        'anomalies_supprimees_du_rapport':max(0,len(errors)-30),
        'avertissement':('Les écarts entre bases signalent un besoin de rapprochement, '
                         'pas un défaut de données certain. Aucune exclusion automatique.'),
        'top_actions':actions[:30],
    }
    if evidence_conflicts:
        base['avertissements'].append('ALERTE : empreintes divergentes pour '
                                     +str(len(evidence_conflicts))+' paires station/catalogue ; aucune correction automatique.')
    if not_tracked:
        base['avertissements'].append('Des candidats existent dans la découverte, mais pas dans les deux autres index interrogés ; vérifier la génération et la réserve avant conclusion.')
    base['avertissements'].append('Aucune égalité entre nombre de candidats connus et couverture totale de Wikipédia ne peut être inférée.')
    return base,concept_rows,actions,samples,discovered_keys


def write_atomic(path, content):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent,mode='wb',delete=False) as f:
        temp=Path(f.name)
        try:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:temp.replace(path)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise


def csv_export(rows, columns):
    from io import StringIO
    out=StringIO(newline='')
    writer=csv.DictWriter(out,fieldnames=columns,extrasaction='ignore',lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return ('\ufeff'+out.getvalue()).encode('utf-8')


def save_auto_report(folder, report, concepts, actions, samples, keys):
    """Writes only audit artifacts, never the SQLite source paths."""
    folder=Path(folder).expanduser().resolve()
    source_paths={Path(m['path']).resolve() for m in report['sources'].values() if m.get('available')}
    if folder in source_paths:
        raise ValueError('Dossier de rapport identique au chemin d’une base SQLite')
    folder.mkdir(parents=True,exist_ok=True)
    safe=safe_branch_filename(report['branch_id'])
    prefix='AUDIT_'+safe+'_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    state_path=folder/('ETAT_PRECEDENT_'+safe+'.json.gz')
    history_path=folder/('HISTORIQUE_'+safe+'.jsonl')
    old=None
    if state_path.is_file():
        try:
            with gzip.open(state_path,'rt',encoding='utf8') as f:old=json.load(f)
            if old.get('branch_id')!=report['branch_id']:old=None
        except (OSError,ValueError,TypeError):old=None
    current_serialized={key_json(k) for k in keys}
    evolution={'comparaison_disponible':old is not None,'nouveaux_candidats_depuis_precedent':None,
               'candidats_absents_depuis_precedent':None,'variation_graines_done':None,
               'cycle_de_decouverte_nouveau_observe':False,'saturation_exploratoire_demontree':None}
    if old:
        prev=set(old.get('candidate_keys',[]))
        evolution['nouveaux_candidats_depuis_precedent']=len(current_serialized-prev)
        evolution['candidats_absents_depuis_precedent']=len(prev-current_serialized)
        done_old=old.get('seed_done')
        done_now=report.get('decouverte',{}).get('graines_par_etat',{}).get('DONE')
        if isinstance(done_old,int) and isinstance(done_now,int):
            evolution['variation_graines_done']=done_now-done_old
            evolution['cycle_de_decouverte_nouveau_observe']=(done_now>done_old)
        if evolution['candidats_absents_depuis_precedent']:
            report['avertissements'].append('Des candidats ont disparu du dernier snapshot de découverte : inspecter les sources avant toute conclusion.')
    report['evolution']=evolution
    report['audit_auto']['fichiers_produits']=[prefix+'.json',prefix+'_CONCEPTS.csv',prefix+'_A_REVOIR.csv',prefix+'_ECHANTILLON_OMISSIONS.csv']
    report_path=folder/(prefix+'.json')
    concept_path=folder/(prefix+'_CONCEPTS.csv')
    actions_path=folder/(prefix+'_A_REVOIR.csv')
    sample_path=folder/(prefix+'_ECHANTILLON_OMISSIONS.csv')
    concept_cols=['branch_id','concept_id','label_fr','configured','candidats_connus',
                  'candidats_decouverts','affectations_catalogue','approve_importes','reject_importes',
                  'hold_station','a_revoir_autres_etats','decided_station',
                  'absents_station_et_catalogue','decisions_hors_decouverte','alertes']
    actions_cols=['type','branch_id','concept_id','concept_fr','page_id','candidate_id','title',
                  'etat_station','decision_importee','priority','seed_count','liens','categories',
                  'sous_categories','evidence_sha256_station','evidence_sha256_catalogue','task_id']
    write_atomic(concept_path,csv_export(concepts,concept_cols))
    write_atomic(actions_path,csv_export(actions,actions_cols))
    write_atomic(sample_path,csv_export(samples,['strate','branch_id','concept_id','concept_fr',
        'page_id','candidate_id','title','decision_initiale','controle_humain','note_humaine']))
    write_atomic(report_path,(json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
    prev_state={'branch_id':report['branch_id'],'created_utc':report['created_utc'],
                'candidate_keys':sorted(current_serialized),
                'seed_done':report.get('decouverte',{}).get('graines_par_etat',{}).get('DONE'),
                'source_catalogue_modified_utc':report['sources'].get('catalogue',{}).get('modified_utc')}
    write_atomic(state_path,gzip.compress(json.dumps(prev_state,ensure_ascii=False,separators=(',',':')).encode('utf8')))
    summary={'created_utc':report['created_utc'],'branch_id':report['branch_id'],
             'candidats_decouverts':len(keys),
             'candidats_absents_station_et_catalogue':report['rapprochement']['paires_decouvertes_absentes_station_et_catalogue'],
             'hold':report['rapprochement']['paires_station_hold'],
             'non_tranches_station':report['station'].get('en_attente_ou_a_revoir'),
             'nouveaux':evolution['nouveaux_candidats_depuis_precedent'],
             'graines_traitees':report.get('decouverte',{}).get('graines_par_etat',{}).get('DONE')}
    with history_path.open('a',encoding='utf-8',newline='\n') as f:
        f.write(json.dumps(summary,ensure_ascii=False)+'\n')
    return [report_path,concept_path,actions_path,sample_path],summary


def run_automatic(args,output_folder=None):
    report,concepts,actions,samples,keys=analyze_branch(args)
    paths,summary=save_auto_report(output_folder or (Path.home()/'Documents'/'EncyKlopedia_Audits'),
                                   report,concepts,actions,samples,keys)
    return report,concepts,actions,paths,summary


# ---------------------------------------------------------------------------
# Interface graphique Windows (Tkinter) — aucune dépendance externe.
# La fonction measure() ci-dessus est reprise à l'identique du diagnostic v31.
# ---------------------------------------------------------------------------
import queue
import threading
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

BG = '#F3F6FA'
WHITE = '#FFFFFF'
NAVY = '#152B45'
SLATE = '#4B5D73'
MUTED = '#63768A'
BLUE = '#2267AD'
TEAL = '#147A6D'
GREEN = '#168052'
AMBER = '#A36A16'
LINE = '#DCE4EC'
SUBTLE = '#EAF0F6'


def display_number(value):
    if value is None:
        return 'Non mesuré'
    if isinstance(value, bool):
        return 'Oui' if value else 'Non'
    if isinstance(value, int):
        return f'{value:,}'.replace(',', ' ')
    if isinstance(value, float):
        return f'{value:,.2f}'.replace(',', ' ').replace('.', ',')
    return str(value)


def display_percent(value):
    return 'Non mesuré' if value is None else f'{display_number(value)} %'


def state_text(value):
    if value is True:
        return 'Vérifié'
    if value is False:
        return 'Non satisfait'
    return 'À démontrer'


class MetricCard(tk.Frame):
    def __init__(self, parent, heading, accent=BLUE):
        super().__init__(parent, bg=WHITE, highlightbackground=LINE, highlightthickness=1)
        tk.Frame(self, bg=accent, height=4).pack(fill='x')
        inner=tk.Frame(self, bg=WHITE, padx=15, pady=10)
        inner.pack(fill='both', expand=True)
        self.heading=tk.Label(inner, text=heading, font=('Segoe UI', 10), fg=SLATE,
                              bg=WHITE, anchor='w', justify='left', wraplength=220)
        self.heading.pack(fill='x')
        self.value=tk.Label(inner, text='—', font=('Segoe UI Semibold', 24), fg=NAVY,
                            bg=WHITE, anchor='w')
        self.value.pack(fill='x', pady=(2,0))
        self.note=tk.Label(inner, text='En attente du diagnostic', font=('Segoe UI', 9),
                           fg=MUTED, bg=WHITE, anchor='w', justify='left', wraplength=220)
        self.note.pack(fill='x', pady=(2,0))

    def update_metric(self, value, note):
        self.value.configure(text=value)
        self.note.configure(text=note)


class ProgressMetric(tk.Frame):
    def __init__(self, parent, label, description, accent=BLUE):
        super().__init__(parent, bg=WHITE)
        top=tk.Frame(self, bg=WHITE)
        top.pack(fill='x')
        tk.Label(top, text=label, bg=WHITE, fg=NAVY, font=('Segoe UI Semibold', 10),
                 anchor='w').pack(side='left')
        self.percent=tk.Label(top, text='—', bg=WHITE, fg=accent,
                              font=('Segoe UI Semibold', 10))
        self.percent.pack(side='right')
        self.bar=ttk.Progressbar(self, mode='determinate', maximum=100, value=0,
                                style='Accent.Horizontal.TProgressbar')
        self.bar.pack(fill='x', pady=(5,3))
        tk.Label(self, text=description, bg=WHITE, fg=MUTED,
                 font=('Segoe UI', 9), anchor='w', justify='left', wraplength=450).pack(fill='x')

    def update_metric(self, value):
        self.percent.configure(text=display_percent(value))
        self.bar['value']=0 if value is None else max(0,min(100,float(value)))


class AuditUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('EncyKlopedia • Achèvement de la branche UNESCO • v31')
        self.geometry('1120x850')
        self.minsize(920,690)
        self.configure(bg=BG)
        self.report=None
        self.tasks=queue.Queue()
        self.busy=False
        self.paths={
            'station':tk.StringVar(value=str(DEFAULT_STATION)),
            'catalogue':tk.StringVar(value=str(DEFAULT_CATALOGUE)),
            'decouverte':tk.StringVar(value=str(DEFAULT_DISCOVERY))}
        self.branch=tk.StringVar(value='unesco.mt1.10')
        self.status=tk.StringVar(value='Prêt • aucune base ne sera modifiée')
        self._setup_styles()
        self._layout()
        self.after(100,self._poll_results)
        self.after(400,self.run_diagnostic)  # Analyse immédiate au double-clic Windows
        self.bind('<F5>', lambda _e:self.run_diagnostic())
        self.bind('<Control-s>', lambda _e:self.save_json())

    def _setup_styles(self):
        sty=ttk.Style(self)
        if 'clam' in sty.theme_names():
            sty.theme_use('clam')
        sty.configure('TNotebook', background=BG, borderwidth=0)
        sty.configure('TNotebook.Tab', padding=(18,10),font=('Segoe UI',10))
        sty.configure('TEntry', padding=(6,5))
        sty.configure('TButton',font=('Segoe UI',10),padding=(12,7))
        sty.configure('Primary.TButton',font=('Segoe UI Semibold',10),padding=(15,7),
                      foreground=WHITE,background=BLUE)
        sty.map('Primary.TButton',foreground=[('disabled','#DFE6ED'),('!disabled',WHITE)],
                background=[('active','#17558F'),('disabled','#9AACBC'),('!disabled',BLUE)])
        sty.configure('Accent.Horizontal.TProgressbar',background=TEAL,troughcolor=SUBTLE,
                      thickness=10,borderwidth=0)
        sty.configure('Audit.Treeview',font=('Segoe UI',10),rowheight=28,
                      background=WHITE,fieldbackground=WHITE,foreground=NAVY)
        sty.configure('Audit.Treeview.Heading',font=('Segoe UI Semibold',10))

    def _layout(self):
        header=tk.Frame(self,bg=NAVY,padx=26,pady=19)
        header.pack(fill='x')
        tk.Label(header,text='EncyKlopedia  /  AUDIT UNESCO V31',bg=NAVY,fg='#9ECDE9',
                 font=('Segoe UI Semibold',10),anchor='w').pack(fill='x')
        tk.Label(header,text='Achèvement réel de la première branche',bg=NAVY,fg=WHITE,
                 font=('Segoe UI Semibold',21),anchor='w').pack(fill='x',pady=(5,3))
        tk.Label(header,text='Diagnostic local, strictement en lecture seule • Aucune tâche créée • Aucune preuve modifiée',
                 bg=NAVY,fg='#D2E2F0',font=('Segoe UI',10),anchor='w').pack(fill='x')

        body=tk.Frame(self,bg=BG,padx=22,pady=15)
        body.pack(fill='both',expand=True)
        setup=tk.Frame(body,bg=WHITE,padx=17,pady=13,
                       highlightbackground=LINE,highlightthickness=1)
        setup.pack(fill='x',pady=(0,12))
        top=tk.Frame(setup,bg=WHITE)
        top.pack(fill='x',pady=(0,8))
        tk.Label(top,text='BRANCHE',font=('Segoe UI Semibold',10),bg=WHITE,fg=SLATE).pack(side='left',padx=(0,10))
        ttk.Entry(top,textvariable=self.branch,width=25).pack(side='left',padx=(0,12))
        self.run_button=ttk.Button(top,text='Analyser les bases  (F5)',style='Primary.TButton',command=self.run_diagnostic)
        self.run_button.pack(side='left')
        self.save_button=ttk.Button(top,text='Exporter le JSON  (Ctrl+S)',command=self.save_json,state='disabled')
        self.save_button.pack(side='left',padx=(9,0))
        self.copy_button=ttk.Button(top,text='Copier le bilan',command=self.copy_summary,state='disabled')
        self.copy_button.pack(side='left',padx=(9,0))
        labels={'station':'Station v30','catalogue':'Catalogue v25','decouverte':'Découverte v28'}
        for key in ('station','catalogue','decouverte'):
            line=tk.Frame(setup,bg=WHITE)
            line.pack(fill='x',pady=2)
            tk.Label(line,text=labels[key],font=('Segoe UI',9),bg=WHITE,fg=SLATE,
                     width=17,anchor='w').pack(side='left')
            ttk.Entry(line,textvariable=self.paths[key]).pack(side='left',fill='x',expand=True,padx=(2,8))
            ttk.Button(line,text='Parcourir…',command=lambda key=key:self.pick_db(key)).pack(side='right')
        note=tk.Label(setup,text='Chemins préremplis pour D:\\EncyKlopedia. Modifiables si nécessaire ; accès SQLite mode=ro.',
                      bg=WHITE,fg=MUTED,font=('Segoe UI',9),anchor='w')
        note.pack(fill='x',pady=(8,0))

        self.notebook=ttk.Notebook(body)
        self.notebook.pack(fill='both',expand=True)
        overview_page=tk.Frame(self.notebook,bg=BG)
        self.notebook.add(overview_page,text='Tableau de bord')
        overview_canvas=tk.Canvas(overview_page,bg=BG,highlightthickness=0)
        overview_scroll=ttk.Scrollbar(overview_page,orient='vertical',command=overview_canvas.yview)
        overview_canvas.configure(yscrollcommand=overview_scroll.set)
        overview_scroll.pack(side='right',fill='y')
        overview_canvas.pack(side='left',fill='both',expand=True)
        overview=tk.Frame(overview_canvas,bg=BG,padx=3,pady=12)
        canvas_item=overview_canvas.create_window((0,0),window=overview,anchor='nw')
        overview.bind('<Configure>',lambda _e:overview_canvas.configure(scrollregion=overview_canvas.bbox('all')))
        overview_canvas.bind('<Configure>',lambda e:overview_canvas.itemconfigure(canvas_item,width=e.width))
        overview_canvas.bind('<Enter>',lambda _e:overview_canvas.bind_all('<MouseWheel>',
                                lambda event: overview_canvas.yview_scroll(int(-event.delta/120),'units')))
        overview_canvas.bind('<Leave>',lambda _e:overview_canvas.unbind_all('<MouseWheel>'))
        self._build_overview(overview)
        self.details={}
        for key,name in [('catalogue','Catalogue'),('decouverte','Découverte'),('station','Station')]:
            page=tk.Frame(self.notebook,bg=WHITE,padx=14,pady=12)
            self.notebook.add(page,text=name)
            self.details[key]=self._build_detail(page)
        controls=tk.Frame(self.notebook,bg=WHITE,padx=14,pady=12)
        self.notebook.add(controls,text='Critères & alertes')
        self.warnings_view=ScrolledText(controls,wrap='word',font=('Segoe UI',10),state='disabled',
                                      bg=WHITE,fg=NAVY,relief='flat',padx=9,pady=9)
        self.warnings_view.pack(fill='both',expand=True)
        raw=tk.Frame(self.notebook,bg=WHITE,padx=14,pady=12)
        self.notebook.add(raw,text='Rapport JSON')
        self.json_view=ScrolledText(raw,wrap='none',font=('Consolas',10),state='disabled',
                                    bg='#F8FAFC',fg=NAVY,padx=9,pady=9)
        self.json_view.pack(fill='both',expand=True)
        footer=tk.Frame(self,bg=SUBTLE,padx=24,pady=8)
        footer.pack(fill='x',side='bottom')
        self.spinner=ttk.Progressbar(footer,mode='indeterminate',length=90)
        self.spinner.pack(side='right')
        tk.Label(footer,textvariable=self.status,bg=SUBTLE,fg=SLATE,
                 font=('Segoe UI',9),anchor='w').pack(side='left',fill='x',expand=True)

    def _build_overview(self,page):
        self.result_banner=tk.Frame(page,bg='#E8F0F9',padx=15,pady=11)
        self.result_banner.pack(fill='x',pady=(0,12))
        self.headline=tk.Label(self.result_banner,text='Achèvement réel : non mesuré',
                               font=('Segoe UI Semibold',15),fg=NAVY,bg='#E8F0F9',anchor='w')
        self.headline.pack(fill='x')
        self.explanation=tk.Label(self.result_banner,text='Lancer le diagnostic pour charger les indicateurs.',
                                  font=('Segoe UI',10),fg=SLATE,bg='#E8F0F9',
                                  anchor='w',justify='left',wraplength=950)
        self.explanation.pack(fill='x',pady=(3,0))
        cards=tk.Frame(page,bg=BG)
        cards.pack(fill='x',pady=(0,12))
        self.cards={}
        for i,(key,label,accent) in enumerate([
            ('tranche','Candidats du stock station tranchés',TEAL),
            ('concepts','Concepts UNESCO ayant un APPROVE',BLUE),
            ('holds','Rattachements non tranchés',AMBER),
            ('jobs','Tâches UNESCO ouvertes',SLATE)]):
            cards.grid_columnconfigure(i,weight=1,uniform='cards')
            card=MetricCard(cards,label,accent)
            card.grid(row=0,column=i,sticky='nsew',padx=(0 if i==0 else 5, 0 if i==3 else 5))
            self.cards[key]=card
        content=tk.Frame(page,bg=WHITE,highlightbackground=LINE,highlightthickness=1,padx=17,pady=12)
        content.pack(fill='both',expand=True)
        tk.Label(content,text='ÉTAT DU STOCK CONNU',font=('Segoe UI Semibold',11),
                 bg=WHITE,fg=NAVY,anchor='w').pack(fill='x',pady=(0,7))
        tk.Label(content,text='Chaque barre mesure une dimension différente ; aucune ne prouve à elle seule la saturation de Wikipédia.',
                 font=('Segoe UI',9),bg=WHITE,fg=MUTED,anchor='w',wraplength=890,justify='left').pack(fill='x',pady=(0,10))
        self.bars={}
        configs=[
            ('revus','Candidats examinés avec retour importé','Rapportés uniquement au stock suivi par la station.'),
            ('tranches','Décisions tranchées','Les HOLD restent non tranchés.'),
            ('concepts','Concepts avec APPROVE','Part des concepts configurés ayant au moins un APPROVE importé.'),
            ('graines','Graines connues traitées','Ne démontre pas qu’aucune nouvelle graine n’existe.'),
            ('jobs','Tâches UNESCO importées','Part des tâches enregistrées dans la station actuelle.')]
        for i,(key,label,description) in enumerate(configs):
            bar=ProgressMetric(content,label,description)
            bar.pack(fill='x',pady=(0,8 if i<len(configs)-1 else 0))
            self.bars[key]=bar

    def _build_detail(self,page):
        tk.Label(page,text='MESURES DE LA BASE • lecture seule',bg=WHITE,fg=NAVY,
                 font=('Segoe UI Semibold',11),anchor='w').pack(fill='x',pady=(0,12))
        tree=ttk.Treeview(page,columns=('metrique','valeur'),show='headings',style='Audit.Treeview')
        tree.heading('metrique',text='Métrique')
        tree.heading('valeur',text='Valeur')
        tree.column('metrique',anchor='w',width=500,stretch=True)
        tree.column('valeur',anchor='w',width=250,stretch=True)
        scroll=ttk.Scrollbar(page,orient='vertical',command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side='left',fill='both',expand=True)
        scroll.pack(side='right',fill='y')
        return tree

    def pick_db(self,key):
        current=Path(self.paths[key].get().strip())
        chosen=filedialog.askopenfilename(parent=self,title='Sélectionner la base SQLite',
                                          initialdir=str(current.parent),
                                          filetypes=[('Bases SQLite','*.sqlite *.db'),('Tous les fichiers','*.*')])
        if chosen:
            self.paths[key].set(chosen)

    def run_diagnostic(self):
        if self.busy:
            return
        branch=self.branch.get().strip()
        if not branch:
            messagebox.showwarning('Branche manquante','Renseigner un identifiant de branche.',parent=self)
            return
        args=SimpleNamespace(branche=branch,
                             station=Path(self.paths['station'].get().strip()),
                             catalogue=Path(self.paths['catalogue'].get().strip()),
                             decouverte=Path(self.paths['decouverte'].get().strip()))
        self.busy=True
        self.run_button.configure(state='disabled')
        self.spinner.start(12)
        self.status.set('Lecture des trois bases en cours… aucune écriture effectuée')
        def work():
            try:
                report=measure(args)
                self.tasks.put(('ok',report))
            except Exception as exc:
                self.tasks.put(('error',f'{type(exc).__name__} : {exc}'))
        threading.Thread(target=work,daemon=True).start()

    def _poll_results(self):
        try:
            kind,data=self.tasks.get_nowait()
        except queue.Empty:
            self.after(100,self._poll_results)
            return
        self.busy=False
        self.spinner.stop()
        self.run_button.configure(state='normal')
        if kind=='ok':
            self.report=data
            self._display_report(data)
            self.save_button.configure(state='normal')
            self.copy_button.configure(state='normal')
            self.status.set('Analyse terminée • '+data['created_utc']+' • bases ouvertes en lecture seule')
        else:
            self.status.set('Échec de l’analyse • aucune modification des bases')
            messagebox.showerror('Diagnostic impossible',data,parent=self)
        self.after(100,self._poll_results)

    def _display_report(self,r):
        c=r.get('catalogue',{});d=r.get('decouverte',{});s=r.get('station',{})
        self.headline.configure(text='Achèvement réel : indéterminé (non démontré)')
        self.explanation.configure(text=(
            'La revue du stock station et la saturation de la découverte sont deux choses différentes. '
            'Les pourcentages ci-dessous ne constituent pas un taux global d’achèvement de la branche.'))
        self.cards['tranche'].update_metric(display_percent(s.get('avancement_stock_station_tranche_pct')),
            f"{display_number(s.get('decisions_tranchees'))} sur {display_number(s.get('candidats_suivis'))} candidats")
        self.cards['concepts'].update_metric(display_percent(c.get('couverture_concepts_approve_v28_pct')),
            f"{display_number(c.get('concepts_avec_approve_v28'))} / {display_number(c.get('concepts_configures'))} concepts")
        self.cards['holds'].update_metric(display_number(s.get('hold_importes_non_tranches')),
            'HOLD importés, non résolus')
        self.cards['jobs'].update_metric(display_number(s.get('jobs_unesco_ouverts')),
            'Tâches connues encore ouvertes')
        for key,val in [
            ('revus',s.get('avancement_stock_station_revu_pct')),
            ('tranches',s.get('avancement_stock_station_tranche_pct')),
            ('concepts',c.get('couverture_concepts_approve_v28_pct')),
            ('graines',d.get('graines_connues_terminees_pct')),
            ('jobs',s.get('jobs_importes_pct_file_existante'))]:
            self.bars[key].update_metric(val)
        definitions={
            'catalogue':[
                ('concepts_configures','Concepts configurés'),
                ('affectations_paires','Paires concept–article affectées'),
                ('articles_distincts_affectes','Articles distincts affectés'),
                ('concepts_avec_affectation','Concepts ayant une affectation'),
                ('decisions_importees_v28','Décisions UNESCO v28 importées'),
                ('concepts_avec_approve_v28','Concepts avec APPROVE'),
                ('candidats_distincts_decides_v28','Candidats distincts du catalogue avec décision v28'),
                ('couverture_concepts_approve_v28_pct','Couverture APPROVE des concepts (%)')],
            'decouverte':[
                ('couples_candidats_distincts','Paires candidates concept–page'),
                ('pages_candidates_distinctes','Pages candidates distinctes'),
                ('graines_par_etat','Graines de découverte par état'),
                ('graines_connues_total','Graines connues'),
                ('graines_connues_terminees_pct','Graines connues terminées (%)'),
                ('graines_en_attente','Graines PENDING')],
            'station':[
                ('candidats_par_etat','Candidats par état'),
                ('candidats_suivis','Candidats suivis'),
                ('revus_avec_import','Revus avec import (DECIDED + HOLD)'),
                ('decisions_tranchees','Décisions tranchées (DECIDED)'),
                ('en_attente_ou_a_revoir','Non tranchés ou à revoir'),
                ('avancement_stock_station_revu_pct','Stock station revu (%)'),
                ('avancement_stock_station_tranche_pct','Stock station tranché (%)'),
                ('hold_importes_non_tranches','HOLD importés non tranchés'),
                ('jobs_v28_par_etat','Tâches UNESCO par état'),
                ('jobs_importes_pct_file_existante','Tâches terminées de la file existante (%)'),
                ('jobs_unesco_ouverts','Tâches UNESCO ouvertes')]
        }
        for area,tree in self.details.items():
            for item in tree.get_children():tree.delete(item)
            dat=r.get(area,{})
            for key,label in definitions[area]:
                if key not in dat:
                    continue
                val=dat[key]
                if isinstance(val,dict):
                    pid=tree.insert('', 'end', values=(label, f'{len(val)} états'))
                    for state,count in sorted(val.items()):
                        tree.insert('', 'end', values=(f'    ↳ {state}',display_number(count)))
                else:
                    formatted=display_percent(val) if key.endswith('_pct') else display_number(val)
                    tree.insert('', 'end', values=(label,formatted))
        constraints=r.get('criteres_de_cloture',{})
        text=['CRITÈRES DE CLÔTURE OBSERVABLES','='*45,'']
        names={
            'pas_de_graines_pendantes_observees':'Aucune graine PENDING observée',
            'pas_de_jobs_unesco_ouverts_observes':'Aucune tâche UNESCO ouverte observée',
            'pas_de_candidats_non_tranches_station':'Aucun candidat non tranché dans la station',
            'saturation_exploratoire_demontree':'Saturation exploratoire démontrée',
            'rappel_estime_sur_candidats_differes':'Rappel sur les candidats différés estimé',
            'sources_coherentes_meme_generation':'Sources cohérentes sur une même génération'}
        for key,value in constraints.items():
            text.append(f"{names.get(key,key)} : {state_text(value)}")
        text.extend(['','AVERTISSEMENTS','='*45,''])
        text.extend('• '+warning for warning in r.get('avertissements',[]))
        text.extend(['','SOURCES UTILISÉES','='*45,''])
        for key,meta in r.get('sources',{}).items():
            text.append(f"{key} : {'DISPONIBLE' if meta.get('available') else 'ABSENTE'}")
            text.append('  '+meta.get('path',''))
            if meta.get('modified_utc'):
                text.append('  Dernière modification : '+meta['modified_utc'])
        self._set_text(self.warnings_view,'\n'.join(text)+'\n')
        self._set_text(self.json_view,json.dumps(r,ensure_ascii=False,indent=2)+'\n')

    @staticmethod
    def _set_text(widget,content):
        widget.configure(state='normal')
        widget.delete('1.0','end')
        widget.insert('1.0',content)
        widget.configure(state='disabled')

    def save_json(self):
        if not self.report:
            return
        file=filedialog.asksaveasfilename(parent=self,title='Enregistrer le diagnostic JSON',
                                          initialfile='ACHEVEMENT_BRANCHE_1.json',
                                          defaultextension='.json',
                                          filetypes=[('Rapport JSON','*.json'),('Tous les fichiers','*.*')])
        if not file:
            return
        try:
            Path(file).write_text(json.dumps(self.report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        except OSError as exc:
            messagebox.showerror('Export impossible',str(exc),parent=self)
            return
        self.status.set('Rapport JSON enregistré : '+str(file))
        messagebox.showinfo('Export terminé','Le rapport JSON a été enregistré.\nLes bases SQLite n’ont pas été modifiées.',parent=self)

    def copy_summary(self):
        if not self.report:
            return
        c=self.report.get('catalogue',{});s=self.report.get('station',{});d=self.report.get('decouverte',{})
        lines=[
            f"EncyKlopedia — branche {self.report['branch_id']}",
            f"Stock station tranché : {display_percent(s.get('avancement_stock_station_tranche_pct'))} ({display_number(s.get('decisions_tranchees'))}/{display_number(s.get('candidats_suivis'))})",
            f"Concepts avec APPROVE : {display_number(c.get('concepts_avec_approve_v28'))}/{display_number(c.get('concepts_configures'))} ({display_percent(c.get('couverture_concepts_approve_v28_pct'))})",
            f"HOLD non tranchés : {display_number(s.get('hold_importes_non_tranches'))}",
            f"Graines connues traitées : {display_percent(d.get('graines_connues_terminees_pct'))}",
            f"Tâches UNESCO ouvertes : {display_number(s.get('jobs_unesco_ouverts'))}",
            'Achèvement réel de la branche : non démontré (saturation exploratoire inconnue).']
        self.clipboard_clear()
        self.clipboard_append('\n'.join(lines))
        self.update_idletasks()
        self.status.set('Bilan copié dans le presse-papiers')



class AuditAutoUI(AuditUI):
    """UI v31 enriched with concept coverage, cross-index gaps and refresh."""
    def __init__(self):
        self.auto_enabled=False
        self.auto_timer=None
        self.last_concepts=[]
        self.last_actions=[]
        self.last_paths=[]
        super().__init__()
        self.title('EncyKlopedia • Audit automatique de la branche UNESCO • v31.2')
        self.bind('<Control-r>', lambda _e:self.toggle_automatic())

    def _layout(self):
        super()._layout()
        self.auto_output=tk.StringVar(value=str(Path.home()/'Documents'/'EncyKlopedia_Audits'))
        self.interval=tk.StringVar(value='30')

        concept_tab=tk.Frame(self.notebook,bg=WHITE,padx=12,pady=10)
        self.notebook.add(concept_tab,text='41 concepts & alertes')
        tk.Label(concept_tab,text='Un concept sans APPROVE n’est pas forcément absent de Wikipédia.',
                 bg=WHITE,fg=SLATE,font=('Segoe UI',10)).pack(anchor='w',pady=(0,8))
        self.concepts_tree=self.make_tree(concept_tab,(
            ('concept_id','Concept',145),('label','Libellé',265),('discovered','Découverts',80),
            ('assignments','Affectés',75),('approved','APPROVE',82),('holds','HOLD',67),
            ('missing','Non suivis',90),('alerts','Alertes',390)))

        actions_tab=tk.Frame(self.notebook,bg=WHITE,padx=12,pady=10)
        self.notebook.add(actions_tab,text='Candidats à vérifier')
        self.action_label=tk.Label(actions_tab,text='Aucun rapprochement réalisé',font=('Segoe UI',10),
                                   bg=WHITE,fg=SLATE,justify='left')
        self.action_label.pack(anchor='w',pady=(0,8))
        self.actions_tree=self.make_tree(actions_tab,(
            ('type','Alerte',200),('concept','Concept',160),('page','Page ID',86),
            ('candidate','Candidat',240),('title','Article',260),('priority','Priorité',70)))

        panel=tk.Frame(self.notebook,bg=WHITE,padx=20,pady=17)
        self.notebook.add(panel,text='Automatisation & historique')
        tk.Label(panel,text='AUDIT AUTOMATIQUE EN LECTURE SEULE',bg=WHITE,fg=NAVY,
                 font=('Segoe UI Semibold',14)).pack(anchor='w',pady=(0,10))
        tk.Label(panel,text='Chaque analyse génère un JSON, le bilan des concepts et le CSV des candidats à vérifier. '
                          'Les fichiers sont enregistrés dans le dossier choisi, jamais dans les bases SQLite.',
                 bg=WHITE,fg=SLATE,font=('Segoe UI',10),wraplength=860,justify='left').pack(fill='x',pady=(0,16))
        directory=tk.Frame(panel,bg=WHITE)
        directory.pack(fill='x',pady=5)
        tk.Label(directory,text='Dossier des rapports',bg=WHITE,fg=SLATE,width=18,anchor='w').pack(side='left')
        ttk.Entry(directory,textvariable=self.auto_output).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(directory,text='Parcourir…',command=self.pick_output_folder).pack(side='left')
        intervalbar=tk.Frame(panel,bg=WHITE)
        intervalbar.pack(fill='x',pady=(14,9))
        tk.Label(intervalbar,text='Rafraîchissement',bg=WHITE,fg=SLATE,width=18,anchor='w').pack(side='left')
        ttk.Combobox(intervalbar,textvariable=self.interval,state='readonly',
                     values=['15','30','60','180'],width=7).pack(side='left',padx=(8,3))
        tk.Label(intervalbar,text='minutes (tant que la fenêtre reste ouverte)',bg=WHITE,fg=MUTED).pack(side='left')
        self.auto_button=ttk.Button(intervalbar,text='Activer le suivi périodique',command=self.toggle_automatic)
        self.auto_button.pack(side='right')
        self.auto_note=tk.StringVar(value='Suivi périodique désactivé. Une analyse est lancée automatiquement à l’ouverture.')
        tk.Label(panel,textvariable=self.auto_note,bg=WHITE,fg=TEAL,font=('Segoe UI',9),
                 justify='left').pack(anchor='w',pady=(0,14))
        tk.Label(panel,text='HISTORIQUE DES MESURES',bg=WHITE,fg=NAVY,
                 font=('Segoe UI Semibold',11)).pack(anchor='w',pady=(6,8))
        self.history_tree=self.make_tree(panel,(
            ('date','Date UTC',176),('discovered','Découverts',110),('new','Nouveaux',95),
            ('hold','HOLD',92),('untracked','Non suivis',110),('seed','Graines DONE',120)))
        tk.Label(panel,text='Aucun calcul ne déclare la branche terminée sans preuve indépendante de saturation '
                            'et audit des omissions. Les rapports répétés sans nouvelle exploration ne prouvent pas la saturation.',
                 bg=WHITE,fg=AMBER,font=('Segoe UI',9),wraplength=870,
                 justify='left').pack(fill='x',pady=(12,0))

    @staticmethod
    def make_tree(parent,columns):
        outer=tk.Frame(parent,bg=WHITE)
        outer.pack(fill='both',expand=True)
        fields=[k for k,_,_ in columns]
        tree=ttk.Treeview(outer,columns=fields,show='headings',style='Audit.Treeview')
        sx=ttk.Scrollbar(outer,orient='horizontal',command=tree.xview)
        sy=ttk.Scrollbar(outer,orient='vertical',command=tree.yview)
        tree.configure(xscrollcommand=sx.set,yscrollcommand=sy.set)
        for k,label,width in columns:
            tree.heading(k,text=label)
            tree.column(k,width=width,minwidth=60,stretch=(k in ('label','title','alerts')))
        tree.grid(row=0,column=0,sticky='nsew')
        sy.grid(row=0,column=1,sticky='ns')
        sx.grid(row=1,column=0,sticky='ew')
        outer.grid_columnconfigure(0,weight=1)
        outer.grid_rowconfigure(0,weight=1)
        return tree

    def pick_output_folder(self):
        dest=filedialog.askdirectory(parent=self,title='Choisir le dossier des rapports',
                                     initialdir=self.auto_output.get())
        if dest:self.auto_output.set(dest)

    def toggle_automatic(self):
        self.auto_enabled=not self.auto_enabled
        if not self.auto_enabled:
            if self.auto_timer is not None:
                try:self.after_cancel(self.auto_timer)
                except tk.TclError:pass
                self.auto_timer=None
            self.auto_button.configure(text='Activer le suivi périodique')
            self.auto_note.set('Suivi périodique désactivé.')
        else:
            self.auto_button.configure(text='Arrêter le suivi périodique')
            self._schedule_auto()

    def _schedule_auto(self):
        if self.auto_timer is not None:
            try:self.after_cancel(self.auto_timer)
            except tk.TclError:pass
            self.auto_timer=None
        if self.auto_enabled:
            minutes=int(self.interval.get())
            self.auto_note.set(f'Suivi actif : contrôle toutes les {minutes} minutes tant que la fenêtre est ouverte.')
            self.auto_timer=self.after(minutes*60*1000,self._scheduled_run)

    def _scheduled_run(self):
        self.auto_timer=None
        if not self.auto_enabled:return
        if self.busy:
            self.auto_timer=self.after(30*1000,self._scheduled_run)
            return
        self.run_diagnostic()

    def run_diagnostic(self):
        if self.busy:return
        branch=self.branch.get().strip()
        if not branch:
            messagebox.showwarning('Branche manquante','Renseigner un identifiant de branche.',parent=self)
            return
        folder=Path(self.auto_output.get().strip()).expanduser()
        if not str(folder).strip():
            messagebox.showwarning('Dossier manquant','Choisir le dossier de rapports.',parent=self)
            return
        args=SimpleNamespace(branche=branch,
                             station=Path(self.paths['station'].get().strip()),
                             catalogue=Path(self.paths['catalogue'].get().strip()),
                             decouverte=Path(self.paths['decouverte'].get().strip()))
        self.busy=True
        self.run_button.configure(state='disabled')
        self.spinner.start(12)
        self.status.set('Audit multibase en cours • lecture seule • aucun gel levé')
        def worker():
            try:
                result=run_automatic(args,folder)
                self.tasks.put(('auto_ok',result))
            except Exception as exc:
                self.tasks.put(('error',f'{type(exc).__name__} : {exc}'))
        threading.Thread(target=worker,daemon=True).start()

    def _poll_results(self):
        try:kind,data=self.tasks.get_nowait()
        except queue.Empty:
            self.after(100,self._poll_results)
            return
        self.busy=False
        self.spinner.stop()
        self.run_button.configure(state='normal')
        if kind=='auto_ok':
            report,concepts,actions,paths,summary=data
            self.report=report
            self.last_concepts=concepts
            self.last_actions=actions
            self.last_paths=paths
            self._display_report(report)
            self.save_button.configure(state='normal')
            self.copy_button.configure(state='normal')
            self.status.set('Audit enregistré • '+str(paths[0]))
        else:
            self.status.set('Échec de l’audit • aucune base modifiée')
            messagebox.showerror('Audit impossible',data,parent=self)
        if self.auto_enabled:self._schedule_auto()
        self.after(100,self._poll_results)

    def _display_report(self,report):
        super()._display_report(report)
        for item in self.concepts_tree.get_children():self.concepts_tree.delete(item)
        for r in self.last_concepts:
            vals=[r['concept_id'],r['label_fr'],r['candidats_decouverts'],
                  r['affectations_catalogue'],r['approve_importes'],r['hold_station'],
                  r['absents_station_et_catalogue'],r['alertes']]
            self.concepts_tree.insert('','end',values=vals)
        for item in self.actions_tree.get_children():self.actions_tree.delete(item)
        for r in self.last_actions[:500]:
            self.actions_tree.insert('','end',values=[r['type'],r['concept_fr'],r['page_id'],
                                      r['candidate_id'],r['title'],r['priority']])
        n=len(self.last_actions)
        self.action_label.configure(text=f'{n:,} lignes exportées dans le CSV intégral • les 500 premières sont affichées.'
                                    .replace(',',' '))
        rp=report.get('rapprochement',{})
        evolution=report.get('evolution',{})
        self.headline.configure(text='Achèvement réel : NON DÉMONTRÉ • audit multibase terminé')
        self.explanation.configure(text=(
            f"Candidats découverts non retrouvés en station ni au catalogue : {rp.get('paires_decouvertes_absentes_station_et_catalogue','?')}. "
            f"Concepts configurés sans APPROVE : {rp.get('concepts_configures_sans_approve','?')}. "
            f"Nouveaux candidats depuis la précédente analyse : {evolution.get('nouveaux_candidats_depuis_precedent','non comparable')}. "
            'Ceci ne mesure pas le rappel sur Wikipédia.'))
        self._reload_history()

    def _reload_history(self):
        for item in self.history_tree.get_children():self.history_tree.delete(item)
        p=Path(self.auto_output.get().strip())/('HISTORIQUE_'+safe_branch_filename(self.branch.get().strip())+'.jsonl')
        if not p.is_file():return
        try:
            with p.open(encoding='utf8') as f:
                rows=[json.loads(line) for line in f if line.strip()]
        except (OSError,ValueError):return
        for r in reversed(rows[-100:]):
            self.history_tree.insert('','end',values=[r.get('created_utc',''),
                r.get('candidats_decouverts',''),r.get('nouveaux') if r.get('nouveaux') is not None else '—',
                r.get('hold',''),r.get('candidats_absents_station_et_catalogue',''),
                r.get('graines_traitees','')])

    def copy_summary(self):
        super().copy_summary()
        if not self.report:return
        rp=self.report.get('rapprochement',{})
        self.clipboard_append('\nCandidats découverts absents station/catalogue : '
                              +str(rp.get('paires_decouvertes_absentes_station_et_catalogue','?')))
        self.clipboard_append('\nConcepts configurés sans APPROVE : '
                              +str(rp.get('concepts_configures_sans_approve','?')))
        self.clipboard_append('\nAudit automatique : saturation et rappel non démontrés.')


def main():
    import argparse
    parser=argparse.ArgumentParser(description='Audit EncyKlopedia v31.2 : CLI --once ou interface graphique')
    parser.add_argument('--once',action='store_true',help='exécuter un audit puis quitter (pour Planificateur de tâches Windows)')
    parser.add_argument('--branch','--branche',default='unesco.mt1.10',dest='branche')
    parser.add_argument('--station',type=Path,default=DEFAULT_STATION)
    parser.add_argument('--catalogue',type=Path,default=DEFAULT_CATALOGUE)
    parser.add_argument('--decouverte',type=Path,default=DEFAULT_DISCOVERY)
    parser.add_argument('--output','--sortie',type=Path,default=Path.home()/'Documents'/'EncyKlopedia_Audits')
    args=parser.parse_args()
    if args.once:
        try:
            report,concepts,actions,paths,summary=run_automatic(args,args.output)
            print('Audit terminé. Fichiers :',*[str(p) for p in paths],sep='\n')
        except Exception as exc:
            from traceback import format_exc
            args.output.mkdir(parents=True,exist_ok=True)
            (args.output/'DERNIERE_ERREUR_AUDIT.txt').write_text(format_exc(),encoding='utf8')
            raise SystemExit(1) from exc
    else:
        ui=AuditAutoUI()
        ui.mainloop()


if __name__ == '__main__':
    main()
