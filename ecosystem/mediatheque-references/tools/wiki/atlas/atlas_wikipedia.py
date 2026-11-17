#!/usr/bin/env python3
"""Atlas UNESCO Educational Policy of the *documentary* Wikipedia EN link graph.

Read-only SQLite consumer of mediatheque-references' independently imported
Wikimedia SQL dump. No KQ/KP/KA/KS, no Wikipedia API, no git operations.
Only bounded neighbourhood expansion; never a full-table scan.
"""
from __future__ import annotations

import argparse
import bz2
import csv
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import heapq
import io
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

DEFAULT_DB = Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite')
DEFAULT_WORK = Path(r'D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41')
DEFAULT_OUT = DEFAULT_WORK / 'atlas_documentaire_v19'
DEFAULT_INVENTORY = DEFAULT_WORK / 'inventory.json'
DEFAULT_CACHE = DEFAULT_WORK / 'wikipedia_extract'
DEFAULT_IDMAP = Path(r'C:\mycode\EncyKlopedia\UNESCO_Workbench\reference\v11_identity_map.json')
DEFAULT_XML_DIR = Path(r'D:\EncyKlopedia\10_sources\wikipedia\enwiki\2026-10')
FORMAT = 'koa.unesco-wikipedia-documentary-atlas/1.0'
ZIP_FORMAT = 'koa.unesco-wikipedia-chatgpt-research-batch/1.0'
MAX_PAGE_LIMIT = 2500
MAX_CANDIDATES = 60000
STOP = {'the','and','of','in','to','with','for','a','an','on','or','by','at','from',
        'education','educational','policy','policies','school','schools','learning',
        'study','rights','right','system','systems'}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(obj) -> bytes:
    return (json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')


def title_norm(s: str) -> str:
    return ' '.join(str(s).replace('_', ' ').split()).casefold()


def terms(s: str) -> set[str]:
    return {x for x in re.findall(r'[a-z]{3,}', str(s).lower()) if x not in STOP}


def csv_bytes(rows: list[dict], fields: list[str]) -> bytes:
    buff = io.StringIO(newline='')
    w = csv.DictWriter(buff, fieldnames=fields, extrasaction='ignore', lineterminator='\n')
    w.writeheader()
    for row in rows:
        safe={}
        for k in fields:
            val=row.get(k,'')
            if isinstance(val,str) and val.lstrip().startswith(('=','+','-','@')):
                val="'"+val
            safe[k]=val
        w.writerow(safe)
    return buff.getvalue().encode('utf-8-sig')


def open_ro(db: Path):
    if not db.is_file():
        raise ValueError(f'Base SQLite absente : {db}')
    # sqlite uses a URI to prevent accidental creation or writes.
    con = sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True, timeout=12)
    con.execute('PRAGMA query_only=ON')
    con.execute('PRAGMA busy_timeout=12000')
    con.row_factory = sqlite3.Row
    return con


def preflight(con, require_import_complete=True):
    needed = {'wiki_pages', 'wiki_qid', 'wiki_linktargets', 'wiki_pagelinks',
              'wiki_externallinks', 'wiki_categorylink_ids', 'ingest_state'}
    tables = {x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = sorted(needed - tables)
    if missing:
        raise ValueError('Tables import Wikipédia manquantes : ' + ', '.join(missing))
    indexes = {x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='index'")}
    # A missing index would trigger scans over hundreds of millions of rows.
    required = {'idx_wiki_pages_title', 'idx_wiki_pagelinks_from', 'idx_wiki_lt_title'}
    if required - indexes:
        raise ValueError('Indices SQLite indispensables absents : ' + ', '.join(sorted(required-indexes))
                         + '. Ne pas parcourir des milliards de lignes sans index.')
    states = {r['stage']: {'completed': bool(r['completed']), 'rows': r['rows_imported']}
              for r in con.execute('SELECT stage,completed,rows_imported FROM ingest_state')}
    if require_import_complete:
        for stage in ('page','page_props','linktarget','externallinks','pagelinks','categorylinks'):
            if stage not in states or not states[stage]['completed']:
                raise ValueError('Import SQL incomplet : '+stage)
    return {'index_names':sorted(indexes), 'ingest_state':states,
            'qid_index_ready':'idx_wiki_qid_qid' in indexes,
            'external_index_ready':'idx_wiki_external_from' in indexes,
            'category_index_ready':'idx_wiki_catid_from' in indexes}


def load_inventory(path: Path):
    raw = json.loads(path.read_text(encoding='utf-8-sig'))
    if raw.get('branch') != 'unesco-mt1-10':
        raise ValueError('Inventaire non associé à la branche UNESCO unesco-mt1-10')
    records = raw.get('records')
    if not isinstance(records, list) or len(records) != 41:
        raise ValueError('Inventaire UNESCO : attendu exactement 41 concepts')
    if len({r['unesco_id'] for r in records}) != 41:
        raise ValueError('Identifiants UNESCO dupliqués')
    return records


def page_row(row):
    if row is None: return None
    return {'page_id':int(row['page_id']), 'title':str(row['title']).replace('_',' '),
            'revision_id':str(row['latest_revision'] or ''), 'redirect':bool(row['redirect']),
            'ns':int(row['ns']), 'qid':'', 'source':'wikipedia_sql_index'}


def by_page_id(con, pid):
    r = con.execute('SELECT page_id,title,latest_revision,redirect,ns FROM wiki_pages '
                    'WHERE page_id=? AND ns=0', (pid,)).fetchone()
    return page_row(r)


def by_title(con, title):
    title = str(title).strip().replace(' ', '_')
    r = con.execute('SELECT page_id,title,latest_revision,redirect,ns FROM wiki_pages '
                    'WHERE ns=0 AND title=? LIMIT 1', (title,)).fetchone()
    return page_row(r)


def seed_pages(con, records, indexes):
    seeds = {}
    unresolved = []
    for rec in records:
        concept = rec['unesco_id']
        q = (rec.get('wikidata') or {}).get('qid')
        hits = []
        if q and indexes['qid_index_ready']:
            for r in con.execute('''SELECT p.page_id,p.title,p.latest_revision,p.redirect,p.ns
                      FROM wiki_qid q JOIN wiki_pages p ON q.page_id=p.page_id
                      WHERE q.qid=? AND p.ns=0 LIMIT 8''', (q,)):
                hits.append((page_row(r),'QID_CANDIDAT_NON_CANONIQUE'))
        for w in rec.get('wikipedia_en_inventory') or []:
            if isinstance(w, dict):
                pid = w.get('page_id') or w.get('pageid')
                if str(pid).isdigit():
                    x = by_page_id(con, int(pid))
                    if x: hits.append((x,'INVENTAIRE_WIKIPEDIA_EXISTANT'))
        if not hits:
            for label in (rec.get('unesco_preferred_labels') or {}).get('en', [])[:3]:
                x = by_title(con,label)
                if x: hits.append((x,'EGALITE_TITRE_NON_APPROUVEE'))
        for x,reason in hits:
            pid = x['page_id']
            if pid not in seeds:
                seeds[pid] = {'page':x, 'concepts':set(), 'reasons':set()}
            seeds[pid]['concepts'].add(concept)
            seeds[pid]['reasons'].add(reason)
        if not hits:
            unresolved.append({'unesco_id':concept,
               'label_en': ' / '.join((rec.get('unesco_preferred_labels') or {}).get('en',[])),
               'qid_candidate':q or '', 'status':'NO_LOCAL_PAGE_MATCH_NOT_CANONICAL'})
    return seeds,unresolved


def score_title(title, known_terms):
    text = title_norm(title)
    common = len(terms(title) & known_terms)
    boost = (9 if 'education' in text else 0) + (4 if 'school' in text else 0)
    if 'policy' in text or 'curriculum' in text: boost += 5
    return min(35, common*6+boost)


def crawl(con,seeds,records, max_pages=450,max_links=180,depth=2,max_candidates=20000):
    known = set()
    for r in records:
        for lab in (r.get('unesco_preferred_labels') or {}).get('en', []):
            known |= terms(lab)
    nodes={}; edges=[]; expanded=set(); heap=[]
    for sid, datum in seeds.items():
        p=datum['page']; p.update({'depth':0,'score':1000.0,
            'root_concepts':','.join(sorted(datum['concepts'])),
            'origin':','.join(sorted(datum['reasons']))})
        nodes[sid]=p;heapq.heappush(heap,(-p['score'],sid))
    while heap and len(expanded)<max_pages:
        priority,sid=heapq.heappop(heap)
        if sid in expanded or sid not in nodes: continue
        source=nodes[sid]
        expanded.add(sid)
        if source['depth']>=depth: continue
        rows=con.execute('''SELECT pl.target_id, lt.ns AS target_ns, lt.title AS target_title,
                                  p.page_id, p.latest_revision, p.redirect
                         FROM wiki_pagelinks pl
                         JOIN wiki_linktargets lt ON pl.target_id=lt.target_id
                         LEFT JOIN wiki_pages p ON p.ns=lt.ns AND p.title=lt.title
                         WHERE pl.source_page_id=? LIMIT ?''',(sid,max_links+1)).fetchall()
        truncated=len(rows)>max_links
        for r in rows[:max_links]:
            if r['target_ns']!=0 or r['page_id'] is None: continue
            tid=int(r['page_id']); newdepth=source['depth']+1
            if len(nodes)>=max_candidates and tid not in nodes: continue
            text=str(r['target_title']).replace('_',' ')
            proposed=round(70-22*newdepth+score_title(text,known)+
                           min(10,math.log1p(float(source['score']))),3)
            if r['redirect']: proposed-=9
            if tid not in nodes:
                nodes[tid]={'page_id':tid,'title':text,'revision_id':str(r['latest_revision'] or ''),
                            'redirect':bool(r['redirect']),'ns':0,'qid':'','depth':newdepth,
                            'score':proposed,'root_concepts':'','origin':'WIKIPEDIA_PAGELINK_OBSERVE'}
                heapq.heappush(heap,(-proposed,tid))
            elif proposed>nodes[tid]['score'] and tid not in seeds:
                nodes[tid]['score']=proposed
                if newdepth<nodes[tid]['depth']:nodes[tid]['depth']=newdepth
                heapq.heappush(heap,(-proposed,tid))
            edges.append({'source_page_id':sid,'target_page_id':tid,'target_title':text,
                          'source_depth':source['depth'],'edge_kind':'WIKIPEDIA_INTERNAL_LINK_OBSERVED',
                          'authority':'DOCUMENT_DISCOVERY_NOT_SEMANTIC_ASSERTION'})
        source['outgoing_limit_reached']=bool(truncated)
    # Don't make claims about inbound links; no index on target_id is guaranteed.
    return nodes,edges,expanded


def enrich_nodes(con,nodes,indexes):
    selected=list(nodes.keys())
    for k in range(0,len(selected),400):
        block=selected[k:k+400]
        if not block: continue
        marks=','.join('?'*len(block))
        for r in con.execute('SELECT page_id,qid FROM wiki_qid WHERE page_id IN ('+marks+')', block):
            nodes[int(r['page_id'])]['qid']=str(r['qid'])


def extras(con,nodes,expanded,indexes,per_page=30):
    cats=[]; extern=[]
    for pid in sorted(expanded):
        if pid not in nodes:continue
        if indexes['category_index_ready']:
            rows=con.execute('''SELECT t.title, c.type FROM wiki_categorylink_ids c
                JOIN wiki_linktargets t ON t.target_id=c.target_id AND t.ns=14
                WHERE c.source_page_id=? LIMIT ?''',(pid,per_page+1)).fetchall()
            for r in rows[:per_page]:
                cats.append({'page_id':pid,'category':str(r['title']).replace('_',' '),
                             'kind':'CATEGORY_MEMBERSHIP_OBSERVED'})
        if indexes['external_index_ready']:
            rows=con.execute('SELECT target_url FROM wiki_externallinks WHERE source_page_id=? LIMIT ?',
                             (pid,per_page+1)).fetchall()
            for r in rows[:per_page]:
                url=str(r['target_url'])
                extern.append({'page_id':pid,'url':url,
                               'kind':'EXTERNAL_LINK_UNVERIFIED_NOT_CITATION'})
    return cats,extern


def read_provisional_identity_map(path:Path, records:list[dict]):
    if not path.is_file():
        return {}, {'status':'NOT_AVAILABLE_NO_PROVISIONAL_IDENTITIES_INFERRED'}
    doc=json.loads(path.read_text(encoding='utf-8-sig'))
    q=(doc.get('by_kind') or {}).get('Q')
    if not isinstance(q,dict):raise ValueError('Carte du Workbench sans section Q')
    allowed={'unesco-skos:'+r['unesco_id'] for r in records}
    if not allowed.issubset(q):
        raise ValueError('Carte des identités KQ provisoires incomplète')
    ids={k.replace('unesco-skos:','',1):v for k,v in q.items() if k in allowed}
    if len(ids)!=41 or len(set(ids.values()))!=41 or any(not re.fullmatch(r'KQ[1-9]\d*',v) for v in ids.values()):
        raise ValueError('Identifiants KQ provisoires invalides ou dupliqués')
    registry=path.with_name('v11_registry.json')
    meta={'status':'WORKBENCH_PROVISIONAL_MAP_READ_ONLY',
          'identity_map_path':str(path),'identity_map_sha256':sha(path.read_bytes()),
          'provisional_kq_count':len(ids)}
    if registry.is_file():
        r=json.loads(registry.read_text(encoding='utf-8-sig'))
        approved={x['id'] for x in r.get('identities',[]) if x.get('status') not in ('provisional','candidate')}
        if approved.intersection(ids.values()):
            raise ValueError('La carte contient des identités non provisoires; revue explicite exigée')
        meta['registry_namespace']=r.get('namespace_id')
        meta['namespace_language_bound_candidate']=(':en:' in str(r.get('namespace_id','')))
        meta['registry_path']=str(registry)
    return ids,meta


def fs_signature(path:Path):
    s=path.stat()
    return {'bytes':s.st_size,'mtime_ns':s.st_mtime_ns,'path':str(path)}


def write_new(target:Path,files:dict[str,bytes], metadata:dict):
    if target.exists():
        raise FileExistsError('Sortie déjà présente : '+str(target)+' ; utiliser AUDIT ou un nouveau --out')
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.atlas_tmp_',dir=target.parent) as td:
        root=Path(td)
        hashes={}
        for name,data in sorted(files.items()):
            dest=root/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(data)
            hashes[name]={'sha256':sha(data),'bytes':len(data)}
        metadata['files']=hashes
        (root/'manifest.json').write_bytes(json_bytes(metadata))
        root.rename(target)


def audit(target:Path):
    doc=json.loads((target/'manifest.json').read_text(encoding='utf-8'))
    for name,meta in doc['files'].items():
        f=target/name
        if not f.is_file() or sha(f.read_bytes())!=meta['sha256']:
            raise ValueError('Fichier atlas modifié ou absent : '+name)
    return {'status':'ATLAS_INTEGRITY_VERIFIED','files_verified':len(doc['files']),
            'branch':doc['branch'],'atlas_path':str(target)}


def build(args):
    if args.max_pages<1 or args.max_pages>MAX_PAGE_LIMIT:
        raise ValueError('max-pages hors limites (1..2500)')
    if args.max_links<1 or args.max_links>1200:
        raise ValueError('max-links hors limites (1..1200)')
    if args.max_candidates < 100 or args.max_candidates > MAX_CANDIDATES:
        raise ValueError('max-candidates hors limites (100..60000)')
    if args.max_side_links < 0 or args.max_side_links > 120:
        raise ValueError('max-side-links hors limites (0..120)')
    if args.shortlist < 1 or args.shortlist > 10000:
        raise ValueError('shortlist hors limites (1..10000)')
    if args.depth not in (1,2):
        raise ValueError('depth doit valoir 1 ou 2 ; pas de graphe mondial illimité')
    db=Path(args.db);inventory=Path(args.inventory); out=Path(args.out)
    if out.exists():
        status=audit(out)
        meta=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
        if meta.get('db_signature')!=fs_signature(db) or meta.get('inventory_sha256')!=sha(inventory.read_bytes()):
            raise ValueError('Source modifiée depuis cet atlas : utiliser un nouveau --out')
        idpath=Path(args.identity_map)
        previous=meta.get('identity_reuse',{}).get('identity_map_sha256')
        current=sha(idpath.read_bytes()) if idpath.is_file() else None
        if previous!=current:
            raise ValueError('Carte d’identité Workbench modifiée depuis cet atlas : nouveau --out requis')
        print(json.dumps(dict(status, operation='REPRISE_IDENTIQUE'),ensure_ascii=False,indent=2));return
    records=load_inventory(inventory)
    ids,identity_meta=read_provisional_identity_map(Path(args.identity_map),records)
    with closing(open_ro(db)) as con:
        index=preflight(con)
        seeds,unresolved=seed_pages(con,records,index)
        if not seeds: raise ValueError('Aucune page trouvée : vérifier la base, les QID et les index SQL')
        nodes,edges,expanded=crawl(con,seeds,records,args.max_pages,args.max_links,args.depth,args.max_candidates)
        enrich_nodes(con,nodes,index)
        cats,extern=extras(con,nodes,expanded,index,args.max_side_links)
    ordered=sorted(nodes.values(),key=lambda r:(-r['score'],r['page_id']))
    for i,n in enumerate(ordered):
        n['rank']=i+1; n['expanded']=n['page_id'] in expanded
        n['wikipedia_url']='https://en.wikipedia.org/wiki/'+urllib.parse.quote(n['title'].replace(' ','_'),safe='():_,')
        n['research_status']='SEED_NON_CANONICAL' if n['page_id'] in seeds else 'CANDIDATE_DISCOVERY_ONLY'
    priorities=[]
    eligible_seeds=[p for p in ordered if p['page_id'] in seeds and not p['redirect']]
    # One manageable first ZIP, always include concept10 and concept9 when found.
    chosen=[]
    for concept in ('concept10','concept9'):
        for p in eligible_seeds:
            if concept in p['root_concepts'].split(',') and p['page_id'] not in chosen:
                chosen.append(p['page_id'])
    for p in eligible_seeds:
        if p['page_id'] not in chosen and len(chosen)<25:
            chosen.append(p['page_id'])
    first_batch=set(chosen[:25])
    for p in ordered[:args.shortlist]:
        if p['redirect']:continue
        priorities.append({'selected':'1' if p['page_id'] in first_batch else '0',
                           'page_id':p['page_id'],'title':p['title'],'rank':p['rank'],
                           'score':p['score'],'revision_id':p['revision_id'],
                           'qid':p['qid'],'rationale':p['origin'],
                           'review_status':'NON_EXAMINEE'})
    anchors=[{'unesco_id':r['unesco_id'],
              'preferred_label_en':(r.get('unesco_preferred_labels') or {}).get('en',[]),
              'wikidata_qid_candidate':(r.get('wikidata') or {}).get('qid'),
              'wikidata_is_exactmatch_approved':False,
              'wikipedia_seed_page_ids':sorted(x for x,datum in seeds.items() if r['unesco_id'] in datum['concepts']),
              'canonical_KQ':None,'existing_provisional_KQ':ids.get(r['unesco_id']),
              'semantic_location':'UNESCO_BRANCH_ANCHOR',
              'change_policy':'APPEND_OR_REVISE_ONLY_NO_ID_RENUMBERING'} for r in records]
    filemap={
      'graphe_documentaire.json':json_bytes({'format':'koa.wikipedia-documentary-neighborhood/1.0',
             'branch':'unesco-mt1-10','graph_kind':'OBSERVED_LINKS_NOT_SEMANTIC_KNOWLEDGE',
             'nodes':[{'page_id':r['page_id'],'title':r['title'],'qid':r['qid'],
                       'rank':r['rank'],'depth':r['depth'],'score':r['score'],
                       'redirect':r['redirect']} for r in ordered],
             'edges':edges}),
      'pages.csv':csv_bytes(ordered,['rank','page_id','title','qid','revision_id','redirect','depth','score',
                    'root_concepts','origin','expanded','outgoing_limit_reached','research_status','wikipedia_url']),
      'liens_internes.csv':csv_bytes(edges,['source_page_id','target_page_id','target_title','source_depth','edge_kind','authority']),
      'liens_externes.csv':csv_bytes(extern,['page_id','url','kind']),
      'categories.csv':csv_bytes(cats,['page_id','category','kind']),
      'pages_prioritaires_a_selectionner.csv':csv_bytes(priorities,
           ['selected','page_id','title','rank','score','revision_id','qid','rationale','review_status']),
      'sans_page_identifiee.csv':csv_bytes(unresolved,['unesco_id','label_en','qid_candidate','status']),
      'ancrages_kristal_stables.json':json_bytes({'format':'koa.unesco-stable-documentary-anchors/1.0',
            'branch':'unesco-mt1-10','knowledge_architecture':'ONE_KRISTAL_PER_UNESCO_BRANCH',
            'anchors':anchors,'existing_identity_map':identity_meta,
            'new_wikipedia_pages_are_sources_not_new_canonical_KQ':True}),
      'README_ATLAS.md':("# Atlas documentaire UNESCO / Wikipédia EN\n\n"
        "Ce dossier est un sous-graphe **borné**, issu de la base SQL locale. Il ne représente pas tout Wikipédia.\n\n"
        "- `pages.csv` : pages trouvées/classées; score = heuristique de découverte, pas autorité scientifique.\n"
        "- `liens_internes.csv` : liens observés, ni relations SKOS ni preuves KS.\n"
        "- `liens_externes.csv` : URL observées, pas forcément citations.\n"
        "- `pages_prioritaires_a_selectionner.csv` : sélectionner `1` pour un futur ZIP de lecture.\n"
        "- `ancrages_kristal_stables.json` : 41 points d'ancrage, sans création de KQ.\n"
        "- Le modèle n'utilise jamais de recherche globale sans index, ni de validation canonique.\n"
        "- Textes Wikipédia : attribution, révision et licence CC BY-SA; sources externes à vérifier.\n").encode('utf-8')}
    meta={'format':FORMAT,'branch':'unesco-mt1-10','created_utc':datetime.now(timezone.utc).isoformat(),
          'status':'PRIVATE_DOCUMENT_GRAPH_READY_FOR_CHATGPT_SELECTION',
          'db_signature':fs_signature(db),'inventory_sha256':sha(inventory.read_bytes()),
          'identity_reuse':identity_meta,
          'concept_anchors':41,'qid_candidates':sum(bool((r.get('wikidata') or {}).get('qid')) for r in records),
          'seed_pages':len(seeds),'unresolved_anchors':len(unresolved),
          'discovered_pages':len(nodes),'expanded_pages':len(expanded),'outbound_edges_observed':len(edges),
          'categories_observed':len(cats),'external_links_observed':len(extern),
          'bounds':{'depth':args.depth,'max_pages':args.max_pages,'max_links_per_expansion':args.max_links,
                    'max_candidates':args.max_candidates},
          'inbound_links_coverage':'NOT_COMPUTED_INDEX_ON_TARGET_ID_NOT_ASSUMED',
          'no_sqlite_writes':True,'no_approved_KQ_KP_KA_KS':True,'no_git_push':True,
          'no_articles_generated':True,'sources':'WIKIPEDIA_SQL_DUMPS_LOCAL_ONLY'}
    write_new(out,filemap,meta)
    print(json.dumps({'status':meta['status'],'out':str(out),'seed_pages':len(seeds),
                      'discovered_pages':len(nodes),'expanded_pages':len(expanded),
                      'outbound_edges_observed':len(edges),'unresolved_anchors':len(unresolved)},
                     ensure_ascii=False,indent=2))


def load_selection(atlas:Path, selection:Path|None,limit:int):
    allowed={}
    with (atlas/'pages.csv').open('r',encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):allowed[int(r['page_id'])]=r
    src=selection or (atlas/'pages_prioritaires_a_selectionner.csv')
    picked=[]
    with src.open('r',encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if str(r.get('selected','')).strip().lower() not in ('1','yes','oui','true','y'):continue
            pid=int(r['page_id'])
            if pid not in allowed:raise ValueError('Page choisie hors atlas : '+str(pid))
            if allowed[pid]['redirect'].lower() in ('true','1'):continue
            if pid not in picked:picked.append(pid)
            if len(picked)>limit:raise ValueError('Lot trop grand (maximum '+str(limit)+')')
    if not picked:raise ValueError('Aucune page non-redirection sélectionnée')
    return picked,allowed


def read_cache(cache:Path, ids:set[int]):
    result={}
    mf=cache/'manifest.json'
    if not mf.is_file():return result
    m=json.loads(mf.read_text(encoding='utf-8'))
    for r in m.get('pages',[]):
        pid=int(r['page_id'])
        if pid not in ids:continue
        name=r['relative_path']
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Chemin d’extraction dangereux')
        f=(cache/name).resolve()
        if not f.is_relative_to(cache.resolve()):raise ValueError('Fichier de cache hors racine')
        text=f.read_bytes()
        if sha(text)!=r['sha256']:
            raise ValueError('Empreinte d’extraction non conforme : '+str(pid))
        if re.match(rb'\s*#REDIRECT\b',text,re.I):continue
        result[pid]={'text':text,'revision_id':str(r.get('revision_id','')),
                     'source':'LOCAL_PRIOR_TARGETED_XML_EXTRACTION','sha256':sha(text)}
    return result


def index_offsets(idx:Path,target_ids:set[int]):
    """Read official multistream index `byte_offset:page_id:title`, even when bzip2 compressed.

    Only store target offsets; memory does not scale with total index rows.
    """
    offsets={}
    opener=bz2.open if idx.name.endswith('.bz2') else open
    with opener(idx,'rt',encoding='utf-8',errors='replace') as f:
        for line in f:
            parts=line.rstrip('\n').split(':',2)
            if len(parts)<3:continue
            if parts[1].isdigit() and int(parts[1]) in target_ids and parts[0].isdigit():
                offsets[int(parts[1])]=int(parts[0])
    return offsets


def decompress_one_bzip2_stream(xml:Path,offset:int,compressed_cap=64*1024*1024,
                                 text_cap=128*1024*1024):
    chunks=[]; total=0;read=0;d=bz2.BZ2Decompressor()
    with xml.open('rb') as f:
        f.seek(offset)
        while not d.eof:
            block=f.read(min(256*1024,compressed_cap-read))
            if not block:raise ValueError('Flux multistream incomplet ou plafond atteint')
            read+=len(block)
            part=d.decompress(block,max_length=4*1024*1024)
            if part:chunks.append(part);total+=len(part)
            if total>text_cap:raise ValueError('Flux multistream trop volumineux')
            while not d.needs_input and not d.eof:
                part=d.decompress(b'',max_length=4*1024*1024)
                if part:chunks.append(part);total+=len(part)
                if total>text_cap:raise ValueError('Flux multistream trop volumineux')
            if read>=compressed_cap and not d.eof:raise ValueError('Plafond flux compressé atteint')
    return b''.join(chunks)


def from_multistream(xml:Path,index:Path,ids:set[int],sql_meta:dict[int,dict]):
    if not xml.is_file() or not index.is_file():
        return {}, {i:'INDEX_OR_XML_NOT_FOUND' for i in ids}
    offs=index_offsets(index,ids)
    result={};missing={i:'PAGE_NOT_IN_MULTISTREAM_INDEX' for i in ids if i not in offs}
    per_offset={}
    for pid,off in offs.items():per_offset.setdefault(off,set()).add(pid)
    for off,wanted in per_offset.items():
        try:
            raw=decompress_one_bzip2_stream(xml,off)
            for found in re.finditer(rb'<page>.*?</page>',raw,flags=re.DOTALL):
                page=ET.fromstring(found.group())
                id_raw=page.findtext('./id')
                if not id_raw or not id_raw.isdigit() or int(id_raw) not in wanted:continue
                pid=int(id_raw)
                if page.find('redirect') is not None:
                    missing[pid]='REDIRECT_NOT_SUBSTANTIVE';continue
                if page.findtext('./ns')!='0':
                    missing[pid]='NON_ARTICLE_NAMESPACE';continue
                rev=page.find('./revision')
                if rev is None:missing[pid]='REVISION_MISSING';continue
                text=rev.findtext('./text') or ''
                if not text.strip():missing[pid]='EMPTY_PAGE';continue
                rev_id=rev.findtext('./id') or ''
                sql_rev=sql_meta[pid]['revision_id']
                result[pid]={'text':text.encode('utf-8'),'revision_id':rev_id,
                             'source':'LOCAL_MULTISTREAM_INDEXED_XML',
                             'revision_mismatch_with_SQL':bool(sql_rev and rev_id!=sql_rev)}
                missing.pop(pid,None)
            for pid in wanted:
                if pid not in result and pid not in missing:missing[pid]='NOT_IN_DECOMPRESSED_STREAM'
        except (OSError,ValueError,ET.ParseError) as exc:
            for pid in wanted:missing[pid]='EXTRACTION_FAILED_'+type(exc).__name__
    return result,missing


def find_xml_index(xml_dir:Path):
    indices=sorted(xml_dir.glob('*pages-articles-multistream-index.txt*'))
    xmls=sorted(p for p in xml_dir.glob('*pages-articles-multistream.xml.bz2') if 'index' not in p.name)
    return (xmls[0] if xmls else None,indices[0] if indices else None)


def build_pack(args):
    atlas=Path(args.atlas)
    audit(atlas)
    if args.limit < 1 or args.limit > 100:
        raise ValueError('Nombre de pages du lot hors limites (1..100)')
    picked,allowed=load_selection(atlas,Path(args.selection) if args.selection else None,args.limit)
    cache=Path(args.cache)
    texts=read_cache(cache,set(picked))
    missing=set(picked)-set(texts)
    xml=Path(args.xml) if args.xml else None
    idx=Path(args.multistream_index) if args.multistream_index else None
    if args.try_multistream and (xml is None or idx is None):
        auto_xml,auto_idx=find_xml_index(Path(args.xml_dir))
        xml=xml or auto_xml;idx=idx or auto_idx
    details={}
    if missing and args.try_multistream and xml and idx:
        got,details=from_multistream(xml,idx,missing,{i:allowed[i] for i in missing})
        texts.update(got)
    elif missing:details={i:'XML_MULTISTREAM_INDEX_NOT_SUPPLIED' for i in missing}
    out=Path(args.output) if args.output else atlas.parent/(atlas.name+'_LOT_001_CHATGPT.zip')
    if out.exists():
        try:
            with zipfile.ZipFile(out) as existing:
                old=json.loads(existing.read('LOT_MANIFEST.json'))
                if old.get('atlas_manifest_sha256') == sha((atlas/'manifest.json').read_bytes()) and \
                   [int(x['page_id']) for x in old.get('items',[])] == picked:
                    print(json.dumps({'status':'LOT_DEJA_PRESENT_REPRISE','lot_zip':str(out),
                         'selected':len(picked),'text_available':old['texts_available'],
                         'text_missing':old['texts_missing']},ensure_ascii=False,indent=2))
                    return
        except (KeyError,zipfile.BadZipFile,ValueError):pass
        raise FileExistsError('Lot déjà présent mais différent : '+str(out)+' ; choisir un nouveau --output')
    metadata=[]; zfiles={}
    for pid in picked:
        src=allowed[pid]
        if pid in texts and len(texts[pid]['text']) > 5 * 1024 * 1024:
            texts.pop(pid)
            details[pid]='TEXT_EXCEEDS_5_MIB_LIMIT'
        status='TEXT_EXTRACTED' if pid in texts else 'TEXT_UNAVAILABLE'
        rev=src.get('revision_id','')
        item={'page_id':pid,'title':src['title'],'qid':src.get('qid',''),
              'atlas_rank':src.get('rank'),'atlas_revision_id':rev,
              'status':status,'discovery_is_not_semantic_evidence':True}
        if pid in texts:
            data=texts[pid]['text']
            name=f'articles/page-{pid}.wikitext.txt'
            zfiles[name]=data
            item.update({'text_relative_path':name,'text_sha256':sha(data),
                         'text_revision_id':texts[pid]['revision_id'],
                         'local_source':texts[pid]['source'],
                         'revision_mismatch_with_SQL':
                           bool(rev and texts[pid]['revision_id'] and rev!=texts[pid]['revision_id'])})
        else:item['reason']=details.get(pid,'NO_TEXT')
        metadata.append(item)
    for name in ['ancrages_kristal_stables.json','liens_internes.csv','pages_prioritaires_a_selectionner.csv']:
        zfiles['atlas/'+name]=(atlas/name).read_bytes()
    batch={'format':ZIP_FORMAT,'branch':'unesco-mt1-10','atlas_manifest_sha256':sha((atlas/'manifest.json').read_bytes()),
           'items':metadata,'selected_pages':len(picked),'texts_available':len(texts),
           'texts_missing':len(picked)-len(texts),'no_KQ_KP_KA_KS_approved':True,
           'wikipedia_license_notice':'Wikipedia text requires CC BY-SA attribution and revision traceability; investigate exceptions.',
           'purpose':'CHATGPT_PRIVATE_RESEARCH_NOT_PUBLICATION'}
    batch_manifest=json_bytes(batch)
    zfiles['LOT_MANIFEST.json']=batch_manifest
    zfiles['MODELE_PROPOSITIONS_CHATGPT.json']=json_bytes({
        'format':'koa.unesco-documentary-proposals/1.0',
        'branch':'unesco-mt1-10','batch_manifest_sha256':sha(batch_manifest),
        'proposals':[],
        '_instructions':'ChatGPT remplit proposals avec candidate_id, unesco_id, source_page_id, '
                        'source_revision_id, source_locator et statement. '
                        'Aucune proposition ne devient KA/KS ou vérité approuvée.'})
    zfiles['LISEZ_MOI_CHATGPT.md']=(
        '# Lot Wikipédia EN / Educational Policy\n\n'
        'La sélection et les liens sont des pistes de recherche, non des preuves canoniques. '
        'Le texte est une source de contexte à examiner. Les liens externes ne sont pas '
        'automatiquement des citations.\n\n'
        'Retour attendu : compléter `MODELE_PROPOSITIONS_CHATGPT.json` avec des assertions '
        'candidates et un localisateur de section précis, puis utiliser le récepteur '
        '`recevoir_lots_atlas_v19.py intake` pour un dépôt privé append-only. '
        'Les 41 ancrages UNESCO restent stables. Aucun KQ/KP/KA/KS n’est créé.\n').encode('utf-8')
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.atlas_lot_',suffix='.zip',dir=out.parent,delete=False) as tmp:
        tmp_path=Path(tmp.name)
    try:
        with zipfile.ZipFile(tmp_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for name,data in sorted(zfiles.items()):z.writestr(name,data)
        tmp_path.rename(out)
    finally:
        if tmp_path.exists():tmp_path.unlink()
    print(json.dumps({'status':'PRIVATE_CHATGPT_RESEARCH_LOT_READY','lot_zip':str(out),
                      'selected':len(picked),'text_available':len(texts),
                      'text_missing':len(picked)-len(texts),
                      'xml_multistream_available':bool(xml and idx),'no_canonical_changes':True},
                     ensure_ascii=False,indent=2))


def make_index_zip(args):
    atlas=Path(args.atlas);audit(atlas)
    out=Path(args.output) if args.output else atlas.parent/(atlas.name+'_INDEX_POUR_CHATGPT.zip')
    if out.exists():
        try:
            with zipfile.ZipFile(out) as existing:
                if sha(existing.read('manifest.json'))==sha((atlas/'manifest.json').read_bytes()):
                    print(json.dumps({'status':'INDEX_ZIP_DEJA_PRESENT','zip':str(out)},ensure_ascii=False,indent=2))
                    return
        except (KeyError,zipfile.BadZipFile,ValueError):pass
        raise FileExistsError('ZIP existant différent : '+str(out))
    files=['manifest.json','graphe_documentaire.json','pages.csv','liens_internes.csv','liens_externes.csv','categories.csv',
           'pages_prioritaires_a_selectionner.csv','sans_page_identifiee.csv','ancrages_kristal_stables.json','README_ATLAS.md']
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.atlas_idx_',suffix='.zip',dir=out.parent,delete=False) as tmp:
        temp=Path(tmp.name)
    try:
        with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for f in files:z.write(atlas/f,arcname=f)
        temp.rename(out)
    finally:
        if temp.exists():temp.unlink()
    print(json.dumps({'status':'ATLAS_GRAPH_ZIP_READY','zip':str(out),'files':len(files)},
                     ensure_ascii=False,indent=2))


def parse(argv=None):
    p=argparse.ArgumentParser(description='Atlas documentaire hors ligne UNESCO — lecture seule SQLite')
    sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('build');a.add_argument('--db',default=str(DEFAULT_DB));
    a.add_argument('--inventory',default=str(DEFAULT_INVENTORY));a.add_argument('--out',default=str(DEFAULT_OUT))
    a.add_argument('--max-pages',type=int,default=450);a.add_argument('--depth',type=int,default=2)
    a.add_argument('--max-links',type=int,default=180);a.add_argument('--max-candidates',type=int,default=20000)
    a.add_argument('--max-side-links',type=int,default=30);a.add_argument('--shortlist',type=int,default=250)
    a.add_argument('--identity-map',default=str(DEFAULT_IDMAP))
    a=sub.add_parser('audit');a.add_argument('--atlas',default=str(DEFAULT_OUT))
    a=sub.add_parser('index-zip');a.add_argument('--atlas',default=str(DEFAULT_OUT));a.add_argument('--output')
    a=sub.add_parser('pack');a.add_argument('--atlas',default=str(DEFAULT_OUT));a.add_argument('--selection')
    a.add_argument('--limit',type=int,default=25);a.add_argument('--cache',default=str(DEFAULT_CACHE))
    a.add_argument('--output');a.add_argument('--xml-dir',default=str(DEFAULT_XML_DIR));a.add_argument('--xml')
    a.add_argument('--multistream-index');a.add_argument('--try-multistream',action='store_true')
    return p.parse_args(argv)


def main(argv=None):
    try:
        args=parse(argv)
        if args.action=='build':build(args)
        elif args.action=='audit':print(json.dumps(audit(Path(args.atlas)),ensure_ascii=False,indent=2))
        elif args.action=='index-zip':make_index_zip(args)
        elif args.action=='pack':build_pack(args)
        return 0
    except (OSError,ValueError,KeyError,sqlite3.DatabaseError) as exc:
        print(json.dumps({'status':'ERREUR_SANS_ECRITURE_CANONIQUE','error':str(exc)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
