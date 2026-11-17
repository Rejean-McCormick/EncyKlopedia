"""Diagnostic conservateur de suivi UNESCO, v31.4, bases SQL en lecture seule.

Classe les écarts entre découverte, catalogue et station sans changer la priorité
ou l'admissibilité éditoriale. Les absences d'index ne sont pas des pertes prouvées.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import io
import json
import sqlite3

import encyk_global_v313 as db

SCHEMA = 'encyklopedia.triage-documentaire.v31.4-readonly/1'


def _required(con: sqlite3.Connection | None, table: str, cols: set[str]):
    return con is not None and cols.issubset(db.columns(con, table))


def analyse(paths: dict, branch: str = 'unesco.mt1.10') -> dict:
    """Read-only reconciliation of branch `(concept_id,page_id)` pairs.

    The candidate identifier cannot be fabricated from a discovery row; it is
    included only where it already exists in the station or canonical ledger.
    """
    info = {'schema': SCHEMA, 'branch_id': branch,
            'created_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
            'achevement_reel_pct': None, 'saturation_demontree': None,
            'sources': {k: db.source_meta(Path(paths[k])) for k in ('catalogue','station','decouverte')},
            'comptages': {}, 'concepts': [], 'candidats_ecarts': [], 'alertes': [],
            'garde_fous': ['Aucune décision éditoriale automatique',
                          'Aucun candidat exclu du stock',
                          'Aucun travail ajouté à la station',
                          'Aucune empreinte réécrite',
                          'Aucune donnée privée Kristal interrogée']}
    missing = [k for k, val in info['sources'].items() if not val.get('available')]
    if missing:
        info['alertes'].append('SOURCES_ABSENTES:' + ','.join(missing))
        info['comptages']['comparaison_complete'] = False
        return info

    configured = {}
    assignments = set()
    ledger = {}
    discovered = {}
    index = {}
    problems = Counter()
    try:
        with db.open_ro(Path(paths['catalogue'])) as con:
            if not _required(con, 'branch_concepts', {'branch_id','concept_id'}):
                raise ValueError('catalogue.branch_concepts manquant')
            for row in con.execute('SELECT DISTINCT concept_id FROM branch_concepts WHERE branch_id=?', (branch,)):
                configured[str(row[0])] = str(row[0])
            if _required(con,'concepts',{'concept_id','vocabulary','label_fr','label_en'}) and _required(con,'branch_concepts',{'vocabulary'}):
                for r in con.execute('''SELECT b.concept_id,c.label_fr,c.label_en
                    FROM branch_concepts b LEFT JOIN concepts c
                    ON c.vocabulary=b.vocabulary AND c.concept_id=b.concept_id
                    WHERE b.branch_id=?''', (branch,)):
                    configured[str(r[0])] = str(r[1] or r[2] or r[0])
            if not _required(con,'assignments',{'branch_id','concept_id','page_id','wiki'}):
                raise ValueError('catalogue.assignments manquant')
            for r in con.execute('SELECT concept_id,page_id FROM assignments WHERE branch_id=? AND wiki=?', (branch,'enwiki')):
                assignments.add((str(r[0]),int(r[1])))
            if not _required(con,'reviewed_article_links_v28',{'branch_id','concept_id','page_id','candidate_id','evidence_sha256','decision'}):
                raise ValueError('catalogue.reviewed_article_links_v28 manquant')
            for r in con.execute('SELECT concept_id,page_id,candidate_id,evidence_sha256,decision FROM reviewed_article_links_v28 WHERE branch_id=?',(branch,)):
                key=(str(r[0]),int(r[1]));v=(r[2] or '', r[3] or '', str(r[4] or '').upper())
                if key in ledger and ledger[key] != v: problems['DUPLICAT_CONTRADICTOIRE_CATALOGUE']+=1
                ledger[key] = v
        with db.open_ro(Path(paths['decouverte'])) as con:
            if not _required(con,'candidates',{'branch_id','concept_id','page_id','title'}):
                raise ValueError('decouverte.candidates manquant')
            for r in con.execute('SELECT concept_id,page_id,title FROM candidates WHERE branch_id=?',(branch,)):
                key=(str(r[0]),int(r[1]));
                if key in discovered: problems['DUPLICAT_CANDIDAT_DECOUVERTE']+=1
                discovered[key] = str(r[2] or '')
        with db.open_ro(Path(paths['station'])) as con:
            if not _required(con,'review_index',{'branch_id','concept_id','page_id','candidate_id','state','evidence_sha256'}):
                raise ValueError('station.review_index manquant')
            extra = 'title' if 'title' in db.columns(con,'review_index') else "'' AS title"
            for r in con.execute(f'SELECT concept_id,page_id,candidate_id,state,evidence_sha256,{extra} FROM review_index WHERE branch_id=?',(branch,)):
                key=(str(r[0]),int(r[1]));v=(r[2] or '',str(r[3] or '').upper(),r[4] or '',r[5] or '')
                if key in index and index[key] != v: problems['DUPLICAT_CONTRADICTOIRE_STATION']+=1
                index[key] = v
    except (ValueError, sqlite3.Error, OSError) as ex:
        info['alertes'].append('COMPARAISON_INCOMPLETE:' + type(ex).__name__ + ':' + str(ex))
        info['comptages']['comparaison_complete'] = False
        return info

    discovery_keys=set(discovered); station_keys=set(index); ledger_keys=set(ledger)
    not_tracked = discovery_keys - (station_keys | ledger_keys)
    allocated = not_tracked & assignments
    unallocated = not_tracked - assignments
    has_hold = {k for k,(_,state,_,_) in index.items() if state=='HOLD'}
    missing_discovery = (station_keys | ledger_keys) - discovery_keys
    conflict_hash = set(); conflict_id = set()
    for k in station_keys & ledger_keys:
        sid,_,sh,_ = index[k]; lid,lh,_ = ledger[k]
        if sid and lid and sid!=lid: conflict_id.add(k)
        if sh and lh and sh.lower()!=lh.lower():conflict_hash.add(k)

    concept_counts=defaultdict(Counter)
    for keys, label in [(discovery_keys,'decouverts'), (assignments,'affectes'),
                        (ledger_keys,'decides_catalogue'),(has_hold,'hold'),
                        (not_tracked,'non_suivis'),(allocated,'non_suivis_deja_affectes'),
                        (unallocated,'non_suivis_sans_affectation')]:
        for k in keys:concept_counts[k[0]][label]+=1
    for k,(_,_,decision) in ledger.items():concept_counts[k[0]]['import_'+decision]+=1
    for c in sorted(set(configured)|set(concept_counts)):
        cc=concept_counts[c]
        approve=cc['import_APPROVE']
        notes=[]
        if c not in configured:notes.append('HORS_CONFIGURATION')
        if not approve:notes.append('SANS_APPROVE_V28')
        if not cc['decouverts']:notes.append('AUCUN_CANDIDAT_DECOUVERT')
        if cc['non_suivis']:notes.append('ECARTS_A_VERIFIER')
        if cc['hold']:notes.append('HOLD_A_CONSERVER')
        info['concepts'].append({'concept_id':c,'label_fr':configured.get(c,c),'configure':c in configured,
           'decouverts':cc['decouverts'],'affectes_historiques':cc['affectes'],
           'approve_v28':approve,'reject_v28':cc['import_REJECT'],
           'hold':cc['hold'],'non_suivis':cc['non_suivis'],
           'non_suivis_deja_affectes':cc['non_suivis_deja_affectes'],
           'non_suivis_sans_affectation':cc['non_suivis_sans_affectation'],
           'motifs':'|'.join(notes)})
    info['concepts'].sort(key=lambda c:(not c['configure'],c['approve_v28']>0,-c['non_suivis'], -c['hold'],c['concept_id']))
    for k in sorted(not_tracked):
        c,p=k
        status = 'ABSENT_DES_DEUX_INDEX_MAIS_AFFECTATION_HISTORIQUE' if k in assignments else 'ABSENT_DES_DEUX_INDEX_NON_AFFECTE'
        info['candidats_ecarts'].append({'categorie':status,'concept_id':c,
            'concept_fr':configured.get(c,c),'page_id':p,'titre':discovered[k],
            'candidate_id':'','evidence_sha256':'','revision_historique':'AUCUNE_CONCLUSION',
            'action_proposee':'Verifier reserve/generation et sources avant tout rearmement'})
    info['comptages']={
      'comparaison_complete':True,'paires_decouvertes':len(discovery_keys),
      'paires_station':len(station_keys),'paires_decisions_importees':len(ledger_keys),
      'absents_station_et_registre_decisions':len(not_tracked),
      'absents_mais_affectation_historique':len(allocated),
      'absents_sans_affectation_historique':len(unallocated),
      'paires_hors_decouverte_station_ou_catalogue':len(missing_discovery),
      'hold_station':len(has_hold),
      'empreintes_divergentes':len(conflict_hash),
      'identifiants_divergents':len(conflict_id),
      'concepts_configures':len(configured),
      'concepts_configures_sans_approve':sum(c['configure'] and not c['approve_v28'] for c in info['concepts']),
      'concepts_configures_sans_decouverte':sum(c['configure'] and not c['decouverts'] for c in info['concepts']),
      'anomalies_doublons':dict(problems)}
    if conflict_hash:info['alertes'].append(f'EMPREINTES_DIVERGENTES:{len(conflict_hash)} (ne pas corriger automatiquement)')
    if conflict_id:info['alertes'].append(f'IDS_DIVERGENTS:{len(conflict_id)} (ne pas reconstituer automatiquement)')
    info['alertes'].append('ABSENCE_DE_SUIVI_NON_EQUIVALENTE_A_PERTE_OU_EXCLUSION')
    info['alertes'].append('SOURCES_LUES_SEPAREMENT:COHERENCE_TEMPORELLE_NON_VERIFIEE')
    info['alertes'].append('SATURATION_ET_RAPPEL_NON_DEMONTRES')
    return info


def csv_bytes(rows: list[dict], cols: list[str]) -> bytes:
    output=io.StringIO(newline='')
    writer=csv.DictWriter(output,fieldnames=cols,lineterminator='\n',extrasaction='ignore')
    writer.writeheader();writer.writerows(rows)
    return ('\ufeff'+output.getvalue()).encode('utf-8')


def exporter(folder: Path, triage: dict, atomic_writer) -> list[Path]:
    """Writes reports outside database directories with the caller's atomic writer."""
    folder=Path(folder).expanduser().resolve()
    protected={Path(x['path']).resolve().parent for x in triage['sources'].values() if x.get('available')}
    if any(folder==parent or folder in parent.parents for parent in protected):
        raise ValueError('Dossier de rapports incompatible avec le répertoire de production')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    prefix='TRIAGE_UNESCO_V314_'+stamp
    summary=folder/(prefix+'.json');diffs=folder/(prefix+'_ECARTS.csv');concepts=folder/(prefix+'_CONCEPTS.csv')
    atomic_writer(summary,(json.dumps(triage,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    atomic_writer(diffs,csv_bytes(triage['candidats_ecarts'],[
        'categorie','concept_id','concept_fr','page_id','titre','candidate_id','evidence_sha256','revision_historique','action_proposee']))
    atomic_writer(concepts,csv_bytes(triage['concepts'],[
        'concept_id','label_fr','configure','decouverts','affectes_historiques','approve_v28','reject_v28','hold',
        'non_suivis','non_suivis_deja_affectes','non_suivis_sans_affectation','motifs']))
    return [summary,diffs,concepts]
