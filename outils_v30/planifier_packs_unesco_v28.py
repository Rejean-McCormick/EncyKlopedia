#!/usr/bin/env python3
"""Planification de lots UNESCO v28 *avant* création/gel des tâches.

Ce module NE génère PAS de REVUE_v28_*.csv contractuel ni de ZIP soumis à v30.
Ce plan est un brouillon à consommer par le générateur d'origine, uniquement après
vérification des protections de tâches/preuves existantes. Aucune écriture SQLite.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
import math
import os
import sys
from pathlib import Path

# Réutilisation du modèle historique, compatible Python stdlib et sans nouvelles dépendances.
from priorisation_unesco_v28 import analyze_one, iter_inputs, read_pack, read_csv_bytes, jsonlines

CONFIG = Path(__file__).parent/'configuration_packs_adaptatifs_v30.json'


def config_valide(config):
    required = ('objectif_candidats', 'minimum_souhaite', 'maximum_candidats',
                'budget_caracteres_preuves', 'part_exploration', 'taille_minimale_contexte_estime')
    for key in required:
        if key not in config:
            raise ValueError('Configuration absente : '+key)
    low, target, high = (config[k] for k in ('minimum_souhaite','objectif_candidats','maximum_candidats'))
    if not all(type(v) is int for v in (low,target,high)) or not (1 <= low <= target <= high <= 500):
        raise ValueError('Tailles invalides : attendu 1 <= minimum <= objectif <= maximum <= 500')
    b = config['budget_caracteres_preuves']
    if type(b) is not int or b < 20000 or b > 30_000_000:
        raise ValueError('Budget document invalide (20 000 a 30 000 000 caracteres)')
    if not isinstance(config['part_exploration'],(float,int)) or not 0 <= config['part_exploration'] <= .5:
        raise ValueError('part_exploration doit etre entre 0 et 0,5')
    if type(config['taille_minimale_contexte_estime']) is not int or not 100 <= config['taille_minimale_contexte_estime'] <= 100_000:
        raise ValueError('taille_minimale_contexte_estime invalide')
    return config


def liser_entrees(path, is_csv, context_path=None):
    """Ne modifie jamais les fichiers sources. Identifiants uniques stricts."""
    output=[]
    if is_csv:
        if not path.is_file(): raise ValueError('CSV pre-generation introuvable : '+str(path))
        rows = read_csv_bytes(path.read_bytes())
        contextes={}
        if context_path:
            if not context_path.is_file():raise ValueError('JSONL des contextes introuvable : '+str(context_path))
            contextes_list=jsonlines(context_path.read_bytes())
            if len({x['candidate_id'] for x in contextes_list}) != len(contextes_list):
                raise ValueError('Doublons candidate_id dans les contextes')
            contextes={x['candidate_id']:x for x in contextes_list}
            if set(contextes) != {x.get('candidate_id') for x in rows}:
                raise ValueError('Le jeu de contextes ne correspond pas exactement au CSV')
        datasets=[(path.name, rows, contextes)]
    else:
        datasets=[]
        for file in iter_inputs(path):
            rows,ctx=read_pack(file)
            if ctx and set(ctx) != {r.get('candidate_id') for r in rows}:
                raise ValueError(f'{file}: contextes et CSV non concordants')
            datasets.append((file.name,rows,ctx))
        if not datasets: raise ValueError('Aucun pack source UNESCO v28 trouve')
    all_ids=set()
    for source,rows,ctx in datasets:
        for row in rows:
            cid=str(row.get('candidate_id') or '')
            if not cid:raise ValueError(f'{source}: identifiant vide')
            if cid in all_ids:raise ValueError(f'Identifiant present plusieurs fois : {cid}')
            all_ids.add(cid)
            context=ctx.get(cid,{})
            if context and context.get('candidate_id')!=cid:
                raise ValueError(f'Incoherence de contexte pour {cid}')
            if context and row.get('evidence_sha256') and context.get('resume_preuves_csv'):
                empreinte=(context.get('resume_preuves_csv') or {}).get('empreinte_preuves_originales')
                if empreinte and empreinte != row['evidence_sha256']:
                    raise ValueError(f'Empreinte des preuves divergente pour {cid}')
            output.append({'source':source,'row':row,'context':context,'candidate_id':cid})
    return output


def estimer_caracteres(item,config):
    # Estimation explicite, non une taille ZIP ni des tokens réels.
    row=item['row'];ctx=item['context']
    row_chars=len(json.dumps(row,ensure_ascii=False,sort_keys=True))
    if ctx:
        ctx_chars=len(json.dumps(ctx,ensure_ascii=False,sort_keys=True))
        # marge pour en-têtes, réponse, formatage et inflation UTF-8
        return max(300,row_chars+ctx_chars+250)
    # Mode CSV: estimation conservatrice si le contexte n'est pas fourni.
    hints=sum(len(str(v)) for k,v in row.items() if k not in {'candidate_id','title','concept_en'})
    return max(config['taille_minimale_contexte_estime'],row_chars+hints+250)


def hashstable(cid): return hashlib.sha256(cid.encode('utf-8')).hexdigest()


def prioriser(items,config,model):
    ranked=[]
    for item in items:
        score,signals,ft=analyze_one(item['row'],item['context'],model)
        clone=dict(item)
        clone['score']=round(100*score,4)
        clone['signaux']=signals
        clone['caracteres_estimes']=estimer_caracteres(item,config)
        ranked.append(clone)
    ranked.sort(key=lambda x:(-x['score'],x['candidate_id']))
    # Conserver une part exploratoire du bas du classement à chaque passage.
    exploration_share=float(config['part_exploration'])
    exploration_n=math.ceil(len(ranked)*exploration_share) if len(ranked)>1 else 0
    exploration = sorted(ranked[-exploration_n:],key=lambda x:(hashstable(x['candidate_id']),x['candidate_id'])) if exploration_n else []
    selected = ranked[:len(ranked)-exploration_n] if exploration_n else ranked
    for x in selected:x['couloir']='prioritaire'
    for x in exploration:x['couloir']='exploratoire'
    return selected,exploration


def planifier(items,config,model):
    """Tous les candidats sont conservés, lots <= objectif sauf besoin de lecture partielle.

    À ce stade l'objectif est une limite souple en nombre et le budget de preuves
    est une limite stricte estimative (sauf candidat indivisiblement surdimensionné).
    """
    high,low=prioriser(items,config,model)
    high=collections.deque(high);low=collections.deque(low)
    goal=config['objectif_candidats'];hard=config['maximum_candidats'];limit=config['budget_caracteres_preuves']
    explore_quota=round(goal*config['part_exploration'])
    packs=[];batch=0
    while high or low:
        batch+=1;group=[];size=0;explored=0
        # Intercalage : environ 25% du lot provient d'un échantillon stable du
        # bas du classement. Ne pas y confondre décision REJECT / information faible.
        while len(group)<min(goal,hard) and (high or low):
            # Essayer de remplir le quota exploratoire progressivement plutôt
            # que de réserver le fond de chaque lot aux derniers candidats.
            want_low=bool(low) and (not high or explored < explore_quota and (len(group)+1)*config['part_exploration'] > explored)
            options=[low,high] if want_low else [high,low]
            q=next((q for q in options if q),None)
            if q is None:break
            item=q[0]
            extra=item['caracteres_estimes']
            if group and size+extra>limit:
                # Chercher dans l'autre couloir un article qui tient encore.
                other=high if q is low else low
                if other and size+other[0]['caracteres_estimes'] <= limit:
                    q=other;item=q[0];extra=item['caracteres_estimes']
                else:break
            q.popleft();group.append(item)
            size+=extra
            if item['couloir']=='exploratoire':explored+=1
            if size>=limit:break
        assert group, 'La planification doit progresser au moins une ligne'
        packs.append({'numero':batch,'candidats':group,'caracteres_estimes':size,
                      'depasse_budget_indivisible':len(group)==1 and size>limit})
    flat=[item['candidate_id'] for pack in packs for item in pack['candidats']]
    expected=[item['candidate_id'] for item in items]
    assert len(flat)==len(expected) and set(flat)==set(expected) and len(set(flat))==len(flat)
    assert all(len(pack['candidats'])<=hard for pack in packs)
    return packs


def analyser(argv=None):
    p=argparse.ArgumentParser(description='Planificateur adaptatif UNESCO v28, AUDIT SEULEMENT')
    src=p.add_mutually_exclusive_group(required=True)
    src.add_argument('--csv',type=Path,help='CSV AVANT generation de taches')
    src.add_argument('--packs',type=Path,help='Packs existants (simulation uniquement, NE PAS regrouper les taches)')
    p.add_argument('--contextes',type=Path,help='JSONL des contextes correspondant au --csv')
    p.add_argument('--sortie',type=Path,required=True)
    p.add_argument('--configuration',type=Path,default=CONFIG)
    args=p.parse_args(argv)
    if args.contextes and not args.csv: p.error('--contextes exige --csv')
    config=config_valide(json.loads(args.configuration.read_text(encoding='utf-8-sig')))
    model=json.loads((Path(__file__).parent/'modele_priorisation_v28.json').read_text(encoding='utf-8-sig'))
    items=liser_entrees(args.csv or args.packs,bool(args.csv),args.contextes)
    packs=planifier(items,config,model)
    args.sortie.mkdir(parents=True,exist_ok=True)
    path=args.sortie/'PLAN_PACKS_UNESCO_V28.csv'
    columns=['lot_suggere','rang_dans_lot','candidate_id','source','concept_id','page_id','titre','score_priorite_indicatif',
             'couloir','caracteres_estimes','empreinte_preuves_originales','signaux']
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
        for pack in packs:
            for i,x in enumerate(pack['candidats'],1):
                r=x['row']
                w.writerow({'lot_suggere':pack['numero'],'rang_dans_lot':i,'candidate_id':x['candidate_id'],
                            'source':x['source'],'concept_id':r.get('concept_id',''),'page_id':r.get('page_id',''),
                            'titre':r.get('title',''),'score_priorite_indicatif':x['score'],
                            'couloir':x['couloir'],'caracteres_estimes':x['caracteres_estimes'],
                            'empreinte_preuves_originales':r.get('evidence_sha256',''),'signaux':x['signaux']})
    summary={'format':'encyklopedia.plan.packs-v28/1','mode':'PLAN_NON_APPLICABLE_DIRECTEMENT',
             'source':'CSV pre-generation (non gele)' if args.csv else 'ZIP existants (taches figees, simulation seulement)',
             'total_candidats':len(items),'total_lots_suggeres':len(packs),'configuration':config,
             'lots':[{'lot_suggere':x['numero'],'nb_candidats':len(x['candidats']),
                      'caracteres_estimes':x['caracteres_estimes'],
                      'exploration':sum(y['couloir']=='exploratoire' for y in x['candidats']),
                      'depasse_budget_indivisible':x['depasse_budget_indivisible']} for x in packs],
             'avertissements':[
                'NE PAS REMPLACER / REPACKER les ZIP de taches en cours : identifiants de batch, preuves et empreintes doivent rester inchanges.',
                'Objectif 300 propositions, maximum 500 paramétrable ; réductions possibles selon le volume des preuves ; minimum non garanti.',
                'Ce plan ne devient opérationnel pour les nouveaux lots qu’après branchement explicite au producteur v28 et respect des verrous.',
                'Nombre de caractères estimé, pas un nombre exact de tokens ou une garantie de capacité du modèle.',
                'Aucune décision APPROVE / REJECT produite et aucune base SQLite modifiée.'
             ]}
    (args.sortie/'PLAN_PACKS_UNESCO_V28.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    txt=['PLANIFICATION PACKS UNESCO V28 — SIMULATION / LECTURE SEULE',
         f'Candidats: {len(items)} | lots suggeres: {len(packs)}',
         f'Objectif: {config["objectif_candidats"]}, maximum: {config["maximum_candidats"]}, minimum souhaite: {config["minimum_souhaite"]}',
         f'Budget estimatif par lot: {config["budget_caracteres_preuves"]} caracteres',
         'AUCUN ZIP OU IDENTIFIANT DE TACHE MODIFIE. Le producteur v28 natif n est PAS encore branche.', '']
    for x in summary['lots']:
        txt.append(f'  Lot {x["lot_suggere"]:03}: {x["nb_candidats"]} candidats, {x["caracteres_estimes"]} caracteres estimes, {x["exploration"]} exploratoires')
    (args.sortie/'PLAN_PACKS_UNESCO_V28.txt').write_text('\n'.join(txt)+'\n',encoding='utf-8-sig')
    print('\n'.join(txt));print('FICHIERS :',args.sortie)
    return 0


if __name__=='__main__':sys.exit(analyser())
