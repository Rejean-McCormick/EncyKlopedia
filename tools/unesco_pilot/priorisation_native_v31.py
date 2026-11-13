#!/usr/bin/env python3
"""Choix DIRECT de candidats UNESCO v28 par pertinence et exploration.

Ne change jamais candidate_id, evidence_sha256, le score du CSV source ou une tâche figée.
Une faible priorité n'est jamais une décision REJECT.
"""
from __future__ import annotations
import hashlib
import re
import unicodedata

GENERAL={'city','county','municipality','village','town','province','state','country',
         'district','region','capital','legislature','government','rights','people',
         'language','justice','social','law','legislation','wisdom','reason','violence',
         'university','college'}
STOP={'the','of','and','for','in','on','a','an','to','with','de','la','les','en','du','des'}

def terms(s):
    s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode('ascii').lower()
    return {t for t in re.split(r'[^a-z0-9]+',s) if len(t)>2 and t not in STOP}

def score(raw,label):
    """Score de planification calculé sur les indices déjà présents en station."""
    links=int(raw.get('links',raw.get('link_evidence',0)) or 0)
    cats=int(raw.get('shared',raw.get('category_evidence',0)) or 0)
    sub=int(raw.get('subs',raw.get('subcategory_evidence',0)) or 0)
    seeds=int(raw.get('seed_count',0) or 0)
    title=terms(raw.get('title','')); concept=terms(label)
    overlap=len(title & concept)
    score=3 + min(37,13*links) + min(18,4*seeds) + min(8,2*cats) + min(5,sub)
    score+=min(26,13*overlap)
    if title and title<=GENERAL and not overlap:score-=24
    if links==0 and not overlap:score-=12
    if sub and not links:score-=3
    return max(0,min(100,score))

def _hash(row):
    return int.from_bytes(hashlib.sha256(str(row['candidate_id']).encode()).digest()[:8], 'big')

def select(rows,limit=300,explore=0.25):
    """Sélection ordonnée dans un pool classé : 75% forts, 25% stratifiés.

    Les autres candidats restent PENDING; aucun effacement ni refus implicite.
    """
    if not rows:return []
    take=min(limit,len(rows));topn=int(round(take*(1-explore)))
    result=list(rows[:topn]);remaining=rows[topn:]
    count=take-len(result)
    if count:
        # Echantillonner dans plusieurs tranches du reste, sans privilégier
        # uniquement les scores les plus faibles ni les plus élevés.
        picked=set()
        for i in range(3):
            lo=len(remaining)*i//3;hi=len(remaining)*(i+1)//3
            group=sorted(remaining[lo:hi],key=lambda r:(_hash(r),str(r['candidate_id'])))
            quota=count//3+(1 if i<count%3 else 0)
            for r in group[:quota]:
                cid=r['candidate_id']
                if cid not in picked:picked.add(cid);result.append(r)
        if len(result)<take:
            for r in remaining:
                if r['candidate_id'] not in picked:
                    picked.add(r['candidate_id']);result.append(r)
                    if len(result)>=take:break
    return result[:take]
