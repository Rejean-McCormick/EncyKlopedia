"""Private, fail-closed UNESCO branch integration (stdlib, Windows-friendly).

No canonical Kristal write, source approval, publication or network call.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

BRANCH = 'unesco-mt1-10'
PROFILE = 'encyklopedia.unesco-research-view/1.0'
SOURCE_REL = 'candidates/educational-policy-en-v11/unesco-mt1-10/canon/domain/unesco-source.json'
MAP_REL = 'candidates/educational-policy-en-v11/unesco-mt1-10/.kristal/v11/identity-migration-map.json'
REGISTRY_REL = 'candidates/educational-policy-en-v11/unesco-mt1-10/canon/domain/v11/registry.json'
CROSSWALK_REL = 'candidates/educational-policy-en-v11/unesco-mt1-10/canon/domain/v11/crosswalk.json'
R2_REL = 'reviews/educational-policy-en-v11/round2-knowledge-en'
INTERNAL_INPUTS = {
    'source': (SOURCE_REL, 'reference/unesco_2026_educational_policy.json'),
    'identity': (MAP_REL, 'reference/v11_identity_map.json'),
    'registry': (REGISTRY_REL, 'reference/v11_registry.json'),
    'crosswalk': (CROSSWALK_REL, 'reference/v11_crosswalk.json'),
    'proposals': (R2_REL+'/19_ka_ks_research_proposals_en.jsonl', 'reference/r2_proposals.jsonl'),
    'sources': (R2_REL+'/source_register_en.json', 'reference/r2_sources.json'),
    'article': (R2_REL+'/right-to-education.en.md', 'reference/r2_article.en.md'),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique(values, message):
    if len(values) != len(set(values)):
        raise ValueError('duplicate '+message)


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def read_json(file: Path) -> Any:
    return json.loads(file.read_text(encoding='utf-8-sig'))


def paths_for(root: Path) -> dict[str, Path]:
    root = root.resolve()
    chosen = {}
    for role, (primary, fallback) in INTERNAL_INPUTS.items():
        a, b = root/primary, root/fallback
        chosen[role] = a if a.is_file() else b
        require(chosen[role].is_file(), f'missing {role}: {a} or {b}')
    chosen['ldh'] = root/'reference/ldh_2025_educational_policy.json'
    require(chosen['ldh'].is_file(), 'missing frozen LinkedDataHub historical reference')
    return chosen


def normalized(c: dict, r: str) -> set[tuple[str, str]]:
    return {(x['unesco_id'], y) for x in c for y in x.get(r, [])}


def comparison(latest: list[dict], legacy: dict) -> dict:
    old = legacy['branch_concepts']
    old_ids = {x['unesco_id'] for x in old}
    new_ids = {x['unesco_id'] for x in latest}
    out = {
        'scope': 'Educational policy (41 anchors), supplied snapshots only',
        'historical_rdf_snapshot_sha256': legacy['origin_sha256'],
        'historical_rdf_modified': legacy['source_date'],
        'historical_rdf_total_triples': legacy['triple_count_in_origin'],
        'historical_matched': len(old_ids & new_ids),
        'current_concepts': len(new_ids),
        'added_since_historical': sorted(new_ids-old_ids),
        'missing_from_current': sorted(old_ids-new_ids),
        'relations': {},
    }
    for relation in ('broader', 'narrower', 'related'):
        now, previous = normalized(latest,relation),normalized(old,relation)
        out['relations'][relation] = {'added': [list(pair) for pair in sorted(now-previous)],
                                      'removed': [list(pair) for pair in sorted(previous-now)]}
    return out


def label_for(c: dict) -> str:
    labels = c.get('preferred_labels', {}).get('en', [])
    require(len(labels) > 0 and isinstance(labels[0],str), 'missing English UNESCO label for '+str(c.get('unesco_id')))
    return labels[0]


def clean_markdown(text: str) -> str:
    text = re.sub(r'\[([^\]]+)\]\(https?://[^)]+\)',r'\1',text)
    text = re.sub(r'\*\*([^*]+)\*\*',r'\1',text)
    text = re.sub(r'(?<!\w)\*([^*]+)\*',r'\1',text)
    return re.sub(r'`([^`]+)`',r'\1',text).strip()


def parse_article(md: str) -> tuple[str,list[dict]]:
    sections=[];title='Right to education';heading='Research context';para=[]
    for raw in md.splitlines():
        line=raw.strip()
        if line.startswith('# '):
            title=line[2:].strip()
            continue
        if line.startswith('## '):
            if para:sections.append({'heading':heading,'body':clean_markdown('\n'.join(para))})
            heading=line[3:].strip();para=[];continue
        if line.startswith('### '):
            if para:sections.append({'heading':heading,'body':clean_markdown('\n'.join(para))})
            heading=line[4:].strip();para=[];continue
        if heading.startswith('Candidate claim concordance'):
            continue  # available in structured claim rows, not duplicated as prose
        if line and not line.startswith('*English-first encyclopedic'):
            para.append(line)
    if para:sections.append({'heading':heading,'body':clean_markdown('\n'.join(para))})
    sections=[s for s in sections if s['body'] and s['heading']!='Candidate claim concordance (not approved)']
    require(len(sections) >= 5, 'research draft lacks expected sections')
    return title,sections[:16]


def root_catalog(root: Path) -> list[dict]:
    path=root.parent/'UNESCO_Kristals/branches'
    rows=[]
    if path.is_dir():
        for d in sorted(path.iterdir()):
            if not d.is_dir() or not re.fullmatch(r'unesco-mt\d+-\d+', d.name):continue
            config=d/'kristal.workspace.json'
            if not config.is_file():continue
            data=read_json(config)
            rows.append({'id':d.name,'label':data.get('title',d.name),
                         'source_status':data.get('status','unknown'),
                         'enriched_research_available': d.name==BRANCH})
    return rows


def load(root: Path):
    selected=paths_for(root)
    src=read_json(selected['source']);identity=read_json(selected['identity'])
    registry=read_json(selected['registry']);crosswalk=read_json(selected['crosswalk'])
    legacy=read_json(selected['ldh'])
    installed_ttl=root.parent/'LinkedDataHub-UNESCO/demo/unesco-thesaurus/concept-schemes/unesco-thesaurus/unesco-thesaurus.ttl'
    if installed_ttl.is_file() and sha(installed_ttl.read_bytes()) != legacy['origin_sha256']:
        raise ValueError('LinkedDataHub RDF differs from frozen 2025 reference: regenerate/review before build')
    sources=read_json(selected['sources'])
    proposals=[json.loads(l) for l in selected['proposals'].read_text(encoding='utf-8-sig').splitlines() if l.strip()]
    article=selected['article'].read_text(encoding='utf-8-sig')
    require(legacy.get('format')=='encyklopedia.unesco-skos-reference/1.0','invalid historical SKOS format')
    concepts=src['concepts']
    concept_ids=[c['unesco_id'] for c in concepts]
    require(len(concepts)==41,'expected 41 UNESCO concepts; review source change before integration')
    unique(concept_ids,'concept IDs')
    qmap={k.partition(':')[2]:v for k,v in identity['by_kind']['Q'].items()}
    require(set(concept_ids)==set(qmap),'identity map/UNESCO mismatch')
    ids={row['id'] for row in registry['identities']}
    require(set(qmap.values()) <= ids,'identity missing from v11 registry')
    require(all(row['status']=='provisional' for row in registry['identities']),'unreviewed adapter refuses promoted identities')
    require(len(proposals)==19,'research proposal set changed: review explicitly')
    srows=sources['sources'] if isinstance(sources,dict) else sources
    require(isinstance(srows,list),'invalid source register')
    source_by_id={s['source_id']:s for s in srows}
    unique([s['source_id'] for s in srows],'source ids')
    require(len(source_by_id)==6,'expected six source documents')
    unique([p['proposal_id'] for p in proposals],'proposal ids')
    for p in proposals:
        require(p['source_id'] in source_by_id,'unresolved source for claim')
        require(p['subject_provisional_kq']==qmap['concept10'],'claim subject is not concept10')
        require(p.get('not_canon') is True and p.get('canonical_ka_id') is None and p.get('canonical_ks_id') is None and p.get('reviewer') is None and p.get('editorial_decision') is None,
                'promotion detected in research proposals: fail closed')
        require(p.get('source_capture_sha256') is None,'source capture changed; no silent qualification')
    for s in srows:
        require(s.get('capture_status')=='NOT_CAPTURED' and not s.get('reviewer') and not s.get('canonical_ks_id'),
                'captured/reviewed source requires independent qualified pipeline')
    mappings=crosswalk['mappings']
    require(all(m['status']=='candidate' for m in mappings),'external identity promoted without approval gate')
    unique([m['local_ref']['id'] for m in mappings],'Wikidata local references')
    require(all(m['local_ref']['id'] in ids for m in mappings),'crosswalk identity missing')
    return selected, concepts, qmap, mappings, proposals, srows, article, legacy


def make_view(root: Path) -> dict:
    chosen, concepts, qmap, crosswalk, proposals, sources, md, historical=load(root)
    by_kq={m['local_ref']['id']:m for m in crosswalk}
    source_references=[{'id':s['source_id'],'label':s['title'],'url':s['url'],
                        'locator':s['locator'],'capture_status':'NOT_CAPTURED','review_status':'pending'} for s in sources]
    require(all(ref['url'].startswith('https://') for ref in source_references),'source URLs require https')
    title, long_sections=parse_article(md)
    claim_rows=[{'id':p['proposal_id'],'statement':p['statement_en'],'section':p['section'],
                 'source_id':p['source_id'],'source_locator':p['source_locator'],
                 'status':'candidate_unreviewed'} for p in proposals]
    article_rows=[]
    for c in concepts:
        cid=c['unesco_id']; name=label_for(c); kq=qmap[cid]
        is_rte=cid=='concept10'
        summary=('Private research article based on nineteen unapproved atomic proposals and six uncaptured source references.'
                  if is_rte else 'UNESCO vocabulary anchor only; encyclopedic research not yet written or approved.')
        sections=long_sections if is_rte else ([{'heading':'UNESCO scope note (not an encyclopedic definition)',
                                                  'body':' '.join(c.get('scope_notes',{}).get('en',[]))}]
                                               if c.get('scope_notes',{}).get('en') else [])
        cross=by_kq.get(kq)
        article_rows.append({
            'id':'unesco:'+cid,
            'slug':re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-'),
            'semantic_id':kq,
            'identity_status':'provisional',
            'unesco_id':cid,'unesco_uri':c['source_uri'],
            'editorial_status':'research_candidate_unapproved' if is_rte else 'source_anchor_only',
            'wikidata_candidate': {'id':cross['external_ref']['id'],'status':'candidate','relation':'proposed_exact_match'} if cross else None,
            'skos_relations':{rel:c.get(rel,[]) for rel in ('broader','narrower','related')},
            'localized':{'en':{'title':name,'summary':summary,'sections':sections}},
            'source_refs':source_references if is_rte else [],
            'claim_proposals':claim_rows if is_rte else []
        })
    unique([a['slug'] for a in article_rows],'article slugs')
    rdf=comparison(concepts,historical)
    view={
        'profile':PROFILE,'mode':'private-research','qualified':False,'publication_enabled':False,
        'publication_id':'NONE_PRIVATE_RESEARCH_NOT_A_PUBLICATION','locales':['en'],
        'branch':{'id':BRANCH,'title':'Educational policy','owner':'UNESCO v11 candidate workspace',
                  'concept_count':len(article_rows),'language':'en'},
        'origin':{'unesco_source':'supplied Factory UNESCO source snapshot (2026-08-31 as declared)',
                  'historical_rdf':'LinkedDataHub supplied UNESCO 2025 RDF snapshot',
                  'wikidata':'candidate crosswalk only',
                  'semantic_status':'v11 provisional; not certified',
                  'research_status':'19 atomic proposals; six source URLs; zero captures and approvals',
                  'source_licenses_require_review':True},
        'rdf_comparison':rdf,
        'articles':article_rows,
        'root_catalog':root_catalog(root),
        'source_sha256':{role:sha(path.read_bytes()) for role,path in chosen.items()},
    }
    require(len(view['articles'])==41 and sum(bool(a['wikidata_candidate']) for a in article_rows)==36,
            'expected 36 provisional crosswalk matches')
    return view


def atomic_write(path:Path, data:bytes):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_bytes(data)
    temp.replace(path)


def output_paths(root:Path):
    base=root/'output/private/educational-policy-en'
    return base/'research-view.json',base/'build-report.json'


def build(root:Path)->dict:
    result=make_view(root)
    main,report=output_paths(root)
    encoded=(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
    d=result['rdf_comparison']
    summary={
        'format':'encyklopedia.unesco-total-report/1.0','status':'PRIVATE_RESEARCH_BUILT_UNQUALIFIED',
        'view_sha256':sha(encoded),'concept_count':len(result['articles']),
        'crosswalk_candidates':sum(a['wikidata_candidate'] is not None for a in result['articles']),
        'reviewed_crosswalks':0,'claims_proposed':19,'claims_approved':0,
        'sources_linked':6,'sources_captured':0,
        'legacy_concepts_matched':d['historical_matched'],
        'historical_only':d['missing_from_current'],
        'new_since_legacy':d['added_since_historical'],
        'scope':'educational-policy/en',
        'public_release':False,
        'files':{'research_view':str(main),'report':str(report)},
        'source_sha256':result['source_sha256'],
        'warnings':['The historical RDF snapshot is older than the 2026 Factory source.',
                    'Source capture, licensing, human review and canonical KA/KS authoring are incomplete.',
                    'No assertion or Wikidata exactMatch is approved.',
                    'The preview is loopback-only and must never be served as a qualified public publication.']
    }
    atomic_write(main,encoded)
    atomic_write(report,(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8'))
    return summary


def check(root:Path)->dict:
    main,report=output_paths(root)
    require(main.is_file() and report.is_file(),'run build before check')
    view,meta=read_json(main),read_json(report)
    require(sha(main.read_bytes())==meta['view_sha256'],'private view digest mismatch')
    require(view['profile']==PROFILE and view['mode']=='private-research' and view['qualified'] is False and view['publication_enabled'] is False,'invalid review/publication gate')
    require(len(view['articles'])==41 and sum(len(a['claim_proposals']) for a in view['articles'])==19,'invalid record counts')
    require(len([x for x in view['articles'] if x['editorial_status']=='research_candidate_unapproved'])==1,'invalid research status')
    return {'status':'PRIVATE_VIEW_INTEGRITY_OK_NO_PUBLICATION','sha256':meta['view_sha256'],'articles':41,'claims_approved':0}


def verify_historical_rdf(root:Path, ttl:Path)->dict:
    ref=read_json(root/'reference/ldh_2025_educational_policy.json')
    require(ttl.is_file(),f'not found: {ttl}')
    digest=sha(ttl.read_bytes())
    return {'file':str(ttl),'actual_sha256':digest,'expected_sha256':ref['origin_sha256'],
            'status':'REFERENCE_MATCH' if digest==ref['origin_sha256'] else 'REFERENCE_CHANGED_REVIEW_REQUIRED'}


def main(argv=None):
    p=argparse.ArgumentParser(description='Private UNESCO/Kristal/LinkedDataHub/EncyKlopedia integration')
    p.add_argument('action',choices=['build','check','rdf-check'])
    p.add_argument('--workbench',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--rdf',type=Path,default=None)
    args=p.parse_args(argv)
    try:
        if args.action=='build':res=build(args.workbench)
        elif args.action=='check':res=check(args.workbench)
        else:
            default=args.workbench.parent/'LinkedDataHub-UNESCO/demo/unesco-thesaurus/concept-schemes/unesco-thesaurus/unesco-thesaurus.ttl'
            res=verify_historical_rdf(args.workbench,args.rdf or default)
        print(json.dumps(res,ensure_ascii=False,indent=2))
        return 2 if res.get('status')=='REFERENCE_CHANGED_REVIEW_REQUIRED' else 0
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print('UNESCO_TOTAL_FAILED: '+str(exc),file=sys.stderr)
        return 1


if __name__=='__main__':raise SystemExit(main())
