"""Deterministic radial / per-branch / convergence scope selection."""
from collections import defaultdict,deque
from math import ceil
import re
from .db import node,neighbors,induced_edges,meta
from .geography import validate_geography,annotate_geography

PREVIEW_NODE_BUDGET=10000  # borne RAM / HTTP ; pas le plafond du scope

def validate_recipe(recipe):
    if not isinstance(recipe,dict):raise ValueError('recipe must be JSON object')
    root=recipe.get('root','')
    if not isinstance(root,str) or not root.startswith('Q') or not root[1:].isdigit():raise ValueError('root must be a QID')
    default=int(recipe.get('default_depth',2))
    if default<0 or default>8:raise ValueError('default_depth must be in 0..8')
    branches=recipe.get('branches',{})
    if not isinstance(branches,dict) or len(branches)>500:raise ValueError('invalid branches')
    for k,v in branches.items():
        if not re.fullmatch(r'P[0-9]+:(in|out)',k) or not isinstance(v,int) or v<0 or v>8:raise ValueError('invalid branch override')
    pids=recipe.get('allowed_properties',[])
    if not isinstance(pids,list) or any(not isinstance(p,str) or not p.startswith('P') or not p[1:].isdigit() for p in pids):raise ValueError('invalid allowed_properties')
    direction=recipe.get('direction','both')
    if direction not in ('in','out','both'):raise ValueError('invalid direction')
    conv=recipe.get('convergence',{})
    if not isinstance(conv,dict):raise ValueError('invalid convergence')
    pct=float(conv.get('threshold_percent',1))
    if not 0<pct<=100:raise ValueError('threshold_percent must be > 0 and <= 100')
    support=int(conv.get('min_support',2))
    if support<1 or support>10000:raise ValueError('min_support must be 1..10000')
    extra=int(conv.get('extra_depth',1))
    if extra<0 or extra>6:raise ValueError('extra_depth must be 0..6')
    budget=int(recipe.get('max_entities',1000))
    if budget<0 or budget>9_000_000_000_000_000_000:raise ValueError('max_entities must be >= 0 (0 = unlimited)')
    included=conv.get('include',[])
    if not isinstance(included,list) or any(not isinstance(x,str) or not x.startswith('Q') or not x[1:].isdigit() for x in included):raise ValueError('invalid convergence.include')
    return {'root':root,'default_depth':default,'branches':branches,'allowed_properties':pids,
       'direction':direction,'convergence':{'threshold_percent':pct,'min_support':support,
       'extra_depth':extra,'include':sorted(set(included))},'max_entities':budget,
       'geography':validate_geography(recipe.get('geography'))}

def branches_for_root(conn,root,direction='both',allow=None):
    if not node(conn,root):raise ValueError('root QID not found in local database')
    groups={}
    seen_by_branch=defaultdict(set)
    for r in neighbors(conn,root,direction,allow):
        if not node(conn,r['neighbor']):continue
        k=r['pid']+':'+r['direction']
        if k not in groups:
            prop=node(conn,r['pid'])
            groups[k]={'key':k,'pid':r['pid'],'property_label':prop['label'] if prop else r['pid'],'direction':r['direction'],'first_hop_count':0,'examples':[]}
        if r['neighbor'] in seen_by_branch[k]:continue
        seen_by_branch[k].add(r['neighbor'])
        groups[k]['first_hop_count']+=1
        if len(groups[k]['examples'])<6:groups[k]['examples'].append(node(conn,r['neighbor']))
    return sorted(groups.values(),key=lambda x:(-x['first_hop_count'],x['key']))

def explore(conn,recipe):
    r=validate_recipe(recipe)
    root=r['root']; pids=set(r['allowed_properties']) if r['allowed_properties'] else None
    if not node(conn,root):raise ValueError(f'root {root} not present in local database')
    selected={root}; why=defaultdict(set);why[root].add('root')
    # Tout scope (y compris illimité) reste borné pour la réponse HTTP de prévisualisation.
    goal=r['max_entities']
    limit=PREVIEW_NODE_BUDGET if goal==0 else min(goal,PREVIEW_NODE_BUDGET)
    trunc=False
    # First-hop edges define branches. Keep branch provenance throughout traversal.
    frontier=deque()
    for br in branches_for_root(conn,root,r['direction'],pids):
        depth=int(r['branches'].get(br['key'],r['default_depth']))
        if depth==0:continue
        for edge in neighbors(conn,root,br['direction'],{br['pid']}):
            nid=edge['neighbor']
            if not node(conn,nid):continue
            if nid not in selected and len(selected)>=limit:trunc=True;continue
            selected.add(nid);why[nid].add('branch:'+br['key']+':1')
            frontier.append((nid,br['key'],1,depth))
    visited=set()
    while frontier:
        current,branch,level,maximum=frontier.popleft()
        key=(current,branch,level)
        if key in visited:continue
        visited.add(key)
        if level>=maximum:continue
        for edge in neighbors(conn,current,r['direction'],pids):
            nid=edge['neighbor']
            if not node(conn,nid):continue
            if nid not in selected and len(selected)>=limit:trunc=True;continue
            selected.add(nid);why[nid].add('branch:'+branch+':'+str(level+1))
            frontier.append((nid,branch,level+1,maximum))
    # Convergence considers distinct internal subjects attached to each external candidate.
    # No recursive convergence waves in v0.1. Explicit approval through include list.
    supports=defaultdict(set); links=defaultdict(set)
    for inside in sorted(selected):
        for edge in neighbors(conn,inside,r['direction'],pids):
            outside=edge['neighbor']
            if outside in selected or not node(conn,outside):continue
            supports[outside].add(inside)
            links[outside].add(edge['pid']+':'+edge['direction'])
    threshold=max(r['convergence']['min_support'],ceil(len(selected)*r['convergence']['threshold_percent']/100))
    candidates=[]
    for outside,origins in supports.items():
        count=len(origins)
        if count>=threshold:
            candidates.append({'id':outside,'label':node(conn,outside)['label'],'support':count,
             'ratio_percent':round(100*count/len(selected),3),'from':sorted(origins), 'relations':sorted(links[outside]),
             'accepted':outside in r['convergence']['include']})
    candidates.sort(key=lambda c:(-c['support'],c['id']))
    for c in candidates:
        if not c['accepted']:continue
        start=c['id']
        if start not in selected and len(selected)>=limit:trunc=True;continue
        selected.add(start);why[start].add('convergence:'+str(c['support']))
        wave=deque([(start,0)]);seen={start}
        while wave:
            current,depth=wave.popleft()
            if depth>=r['convergence']['extra_depth']:continue
            for edge in neighbors(conn,current,r['direction'],pids):
                nid=edge['neighbor']
                if not node(conn,nid) or nid in seen:continue
                if nid not in selected and len(selected)>=limit:trunc=True;continue
                seen.add(nid);selected.add(nid);why[nid].add('convergence-expansion:'+start+':'+str(depth+1));wave.append((nid,depth+1))
    base_nodes=[dict(node(conn,i),reasons=sorted(why[i])) for i in sorted(selected)]
    display_nodes,geo_counts=annotate_geography(conn,base_nodes,r['geography'])
    edges=induced_edges(conn,set(n['id'] for n in display_nodes))
    return {'profile':'skope.encyk-preview/1.0','root':root,'recipe':r,
       'source_snapshot_digest':meta(conn).get('source_snapshot_digest','unknown'),
       'nodes':display_nodes,'edges':edges,'geography_coverage':geo_counts,
       'candidates':candidates,'counts':{'entities':len(display_nodes),'relations':len(edges),'candidates':len(candidates)},
       'truncated':trunc, 'preview_budget':limit, 'requested_max_entities':goal,
       'preview_only':goal==0 or goal>PREVIEW_NODE_BUDGET,
       'status':'working_non_canonical',
       'limitations':['Sélection de travail non validée','Une absence de lien géographique ne signifie PAS absence du taxon dans la région','L’index EncyK est agrégé et n’inclut pas les déclarations source complètes','Convergence en une vague seulement; acceptation explicite requise']}
