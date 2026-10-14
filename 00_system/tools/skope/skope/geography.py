"""Geographic *scope intent* over an aggregated, read-only EncyK index.

Index links are discovery signals, never verified occurrences. Absence of a
signal is NOT evidence of absence. No GBIF/POWO observations are invented.
"""
from collections import defaultdict
import re
from .db import _eid, _wid

DEFAULT = {'focus':'north-america','priority':'canada','mode':'annotate',
           'region_qid':'Q49','priority_qid':'Q16',
           'evidence_properties':['P9714','P183','P2341']}
PROPERTIES={9714:'taxon_range',183:'endemic_to',2341:'indigenous_to'}
GEO_LINKS={17,131,30}  # country, administrative parent, continent
NA_COUNTRIES={'Q30','Q96','Q223'}  # USA, Mexico, Greenland (not an exhaustive inventory)


def validate_geography(spec):
    if spec is None:return {'mode':'off'}
    if not isinstance(spec,dict):raise ValueError('geography must be object')
    if not spec or spec.get('mode','off')=='off':return {'mode':'off'}
    if set(spec)-set(DEFAULT):raise ValueError('unsupported geography option')
    focus=spec.get('focus','north-america');priority=spec.get('priority','canada')
    mode=spec.get('mode','annotate')
    if focus not in ('north-america','custom') or priority not in ('canada','custom'):
        raise ValueError('geography: invalid focus/priority')
    if mode not in ('annotate','documented_only'):
        raise ValueError('geography.mode must be annotate or documented_only')
    region_qid=spec.get('region_qid','Q49');priority_qid=spec.get('priority_qid','Q16')
    if not all(isinstance(q,str) and re.fullmatch(r'Q[1-9][0-9]*',q) for q in (region_qid,priority_qid)):
        raise ValueError('geography: invalid geographic QID')
    if region_qid==priority_qid:raise ValueError('region_qid and priority_qid must differ')
    if (focus=='north-america') != (region_qid=='Q49') or (priority=='canada') != (priority_qid=='Q16'):
        raise ValueError('geography: incompatible QIDs and labels')
    values=spec.get('evidence_properties',['P9714','P183','P2341'])
    if not isinstance(values,list) or len(values)>3 or len(set(values))!=len(values) or any(v not in ('P9714','P183','P2341') for v in values):
        raise ValueError('geography.evidence_properties invalid')
    if not values:raise ValueError('geography.evidence_properties required')
    return {**DEFAULT,'mode':mode,'focus':focus,'priority':priority,'region_qid':region_qid,'priority_qid':priority_qid,'evidence_properties':values}


def _edges_from(conn,ids,prop_ids):
    """Subject-ID-first indexed reads, never scan all entity_edge rows."""
    output=[]
    numbers=sorted(ids)
    for at in range(0,len(numbers),250):
        chunk=numbers[at:at+250]
        s=','.join('?' for _ in chunk);p=','.join('?' for _ in prop_ids)
        output.extend(conn.execute(
            f'SELECT subject_id,property_id,target_id FROM entity_edge WHERE subject_id IN ({s}) AND property_id IN ({p})',
            [*chunk,*prop_ids]).fetchall())
    return output


def _area_class(conn,location,memo,region_qid,priority_qid):
    """Bounds geographic hierarchy to 2 indexed hops for evidence annotation.

    P17 / P131 / P30 links describe the geographic place (not the taxon).
    A nearby place does not imply a taxon is present there.
    """
    if location in memo:return memo[location]
    if location==priority_qid:memo[location]='priority';return 'priority'
    if location==region_qid or (region_qid=='Q49' and location in NA_COUNTRIES):
        memo[location]='region';return 'region'
    todo=[(location,0)];seen={location}
    outcome='other'
    while todo:
        current,depth=todo.pop(0)
        if depth>=2:continue
        eid=_eid(current)
        if eid is None:continue
        # All reads constrained by subject_id and bounded depth. Avoid trusting
        # transitive taxonomy or P171 as a geographic hierarchy.
        rs=conn.execute('SELECT property_id,target_id FROM entity_edge WHERE subject_id=? AND property_id IN (17,131,30) LIMIT 80',(eid,)).fetchall()
        for row in rs:
            q=_wid(row['target_id'])
            if q==priority_qid:outcome='priority';todo.clear();break
            if q==region_qid or (region_qid=='Q49' and q in NA_COUNTRIES):outcome='region'
            if q not in seen:
                seen.add(q);todo.append((q,depth+1))
        if outcome=='canada':break
    memo[location]=outcome
    return outcome


def annotate_geography(conn,nodes,spec):
    """Return sorted annotated nodes + coverage summary, without modifying DB.

    Classifies links on the *taxon* to a geographic Wikidata item.
    Does not infer naturalized/native status from P9714 alone.
    """
    geo=validate_geography(spec)
    if geo['mode']=='off':return nodes,None
    eid_map={_eid(n['id']):n['id'] for n in nodes}
    props=sorted(int(v[1:]) for v in geo['evidence_properties'])
    rows=_edges_from(conn,list(eid_map),props)
    evidence=defaultdict(list)
    memo={}
    for row in rows:
        q=eid_map.get(row['subject_id'])
        if not q:continue
        location=_wid(row['target_id'])
        classification=_area_class(conn,location,memo,geo['region_qid'],geo['priority_qid'])
        evidence[q].append({'property':'P'+str(row['property_id']),
                            'relation':PROPERTIES.get(row['property_id'],'other'),
                            'location_qid':location,'area_match':classification})
    groups=defaultdict(int);rank={'priority':0,'region':1,'outside_only':2,'unknown':3}
    tagged=[]
    for n in nodes:
        signals=sorted(evidence.get(n['id'],[]),key=lambda x:(x['property'],x['location_qid']))
        matches={sig['area_match'] for sig in signals}
        if 'priority' in matches:category='priority'
        elif 'region' in matches:category='region'
        elif signals:category='outside_only'
        else:category='unknown'
        groups[category]+=1
        tagged.append({**n,'geography':{'category':category,
            'evidence':signals,'evidence_count':len(signals),
            'interpretation':'index_links_only_not_proof_of_occurrence'}})
    considered=len(tagged)
    if geo['mode']=='documented_only':
        tagged=[n for n in tagged if n['geography']['category'] in ('priority','region') or 'root' in n.get('reasons',[])]
    # Canada-first presentation, without changing exploration/truncation logic.
    tagged.sort(key=lambda n:(rank[n['geography']['category']],n['id']))
    return tagged,{'mode':geo['mode'],'focus':geo['region_qid'],'priority':geo['priority_qid'],
       'priority_documented':groups['priority'],
       'region_other_documented':groups['region'],
       'other_area_only':groups['outside_only'],
       'no_geographic_evidence':groups['unknown'],
       'pre_filter_entities':considered,'shown_entities':len(tagged),
       'evidence_properties':geo['evidence_properties'],
       'certainty':'index_aggregated_unverified',
       'warnings':['Wikidata geography is incomplete: undocumented ≠ absent',
                   'Region focus is evaluated AFTER taxonomy graph traversal: cannot guarantee completeness when truncated',
                   'Subregions follow geographic P17/P131/P30 up to 2 hops; no implied species presence',
                   'Prioritization does not replace geographic occurrence data (GBIF/Canadian flora inventories)']}
