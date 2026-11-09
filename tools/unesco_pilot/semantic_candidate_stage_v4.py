"""Stage one UNESCO mt1.10 research graph for a ONE-Kristal pilot.

Offline, read-only with respect to the finished UNESCO/Wikipedia research run.
Never creates KQ/KP/KA/KS, calls an AI, edits canonical workspaces or publishes.

It builds a reproducible reviewable 41-concept *candidate* graph and 41 AI
research task specifications that can later be submitted to a configured AI
engine and Kristalizer's independent AI proposal intake.

Important: an unreviewed Wikidata QID or a matching MediaWiki page is context,
NOT a canonical crosswalk or a factual source approval. A redirect does not
qualify as an autonomous encyclopedic text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

FORMAT='koa.unesco-mt1-10-semantic-stage/1.0'
AI_TASK_FORMAT='koa.unesco-mt1-10-ai-research-task/1.0'
LOCALES=('en','fr','es','de','nl','sv','da','no','nn','fi','et','af','it','pt')
READ_MAX=32_000_000
REDIRECT=re.compile(r'^\ufeff?\s*#\s*redirect\b\s*:?\s*\[\[',re.I)
CID=re.compile(r'^concept[1-9][0-9]*$')

class StageError(ValueError):pass

def sha_bytes(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def sha_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(65536),b''):h.update(chunk)
    return h.hexdigest()

def load(path:Path,*,max_bytes=READ_MAX):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>max_bytes:
        raise StageError(f'Missing/symlinked/oversized JSON: {path}')
    return json.loads(path.read_text(encoding='utf-8'))

def canonical_json(obj)->bytes:
    return (json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+'\n').encode('utf-8')

def write_json(path:Path,obj)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(canonical_json(obj))

def forbid_git(path:Path)->None:
    for parent in (path,*path.parents):
        if (parent/'.git').exists():
            raise StageError(f'Private output inside Git checkout: {path}')

def redirects(text:bytes)->bool:
    return bool(REDIRECT.match(text[:4096].decode('utf-8','replace')))

def check_inputs(work:Path):
    paths={'report':work/'RAPPORT_AUTO.json','inventory':work/'inventory.json',
           'dossier':work/'skope_dossier.json','queue':work/'projection_queue_14_langues.json',
           'xml_manifest':work/'wikipedia_extract'/'manifest.json'}
    hashes={k:sha_file(p) for k,p in paths.items() if p.is_file()}
    if len(hashes)!=len(paths):raise StageError('Run autopilot to completion first: some source files absent')
    report=load(paths['report']);inventory=load(paths['inventory']);dossier=load(paths['dossier'])
    queue=load(paths['queue']);xm=load(paths['xml_manifest'])
    if (report.get('branch')!='unesco-mt1-10' or report.get('status')!='PRIVATE_RESEARCH_PREPARED_NOT_PUBLISHED' or
        report.get('concepts_discovered')!=41 or report.get('public_release_authorized') is not False or
        report.get('articles_generated')!=0):raise StageError('Unsafe or unfinished autopilot report')
    if (inventory.get('profile')!='encyklopedia.unesco-local-wikipedia-handoff/1.0' or
        inventory.get('branch')!='unesco-mt1-10' or inventory.get('not_canonical') is not True or
        inventory.get('not_publication') is not True or inventory.get('approval_status')!='BLOCKED'):
        raise StageError('Unexpected inventory authority')
    if (dossier.get('profile')!='skope.unesco-mt1-10-local-source-dossier/1.0' or
        dossier.get('branch')!='unesco-mt1-10' or dossier.get('private') is not True or
        dossier.get('not_canonical') is not True or dossier.get('public_upload_authorized') is not False or
        dossier.get('inventory_sha256')!=hashes['inventory'] or
        dossier.get('xml_manifest_sha256')!=hashes['xml_manifest']):
        raise StageError('Dossier not bound to this research snapshot')
    if (xm.get('profile')!='encyklopedia.unesco-enwiki-text-evidence/1.0' or
        xm.get('private') is not True or xm.get('public_upload_authorized') is not False or
        xm.get('source_inventory_sha256')!=hashes['inventory']):
        raise StageError('XML manifest belongs to other inventory')
    if (queue.get('branch')!='unesco-mt1-10' or queue.get('one_branch_kristal') is not True or
        queue.get('projection_queue_size')!=574 or queue.get('public_release_authorized') is not False or
        queue.get('generated_articles')!=0):raise StageError('Projection queue not a private 41 x 14 plan')
    records=inventory.get('records');entries=dossier.get('entries')
    if not isinstance(records,list) or len(records)!=41 or not isinstance(entries,list) or len(entries)!=41:
        raise StageError('Expected 41 concepts in both inventory and dossier')
    rids=[x.get('unesco_id') for x in records]
    eids=[x.get('unesco_id') for x in entries]
    if (any(not isinstance(v,str) or not CID.fullmatch(v) for v in rids) or
        len(set(rids))!=41 or set(rids)!=set(eids) or len(set(eids))!=41 or 'concept10' not in rids):
        raise StageError('Mismatched, duplicate or missing UNESCO IDs')
    jobs=queue.get('jobs',[])
    if not isinstance(jobs,list) or len(jobs)!=574 or set((j.get('unesco_id'),j.get('locale')) for j in jobs)!=set((x,y) for x in rids for y in LOCALES):
        raise StageError('Expected exactly 41 x 14 unique project slots')
    return paths,hashes,report,records,entries,xm

def build(work:Path):
    paths,hashes,report,records,entries,xm=check_inputs(work)
    entry_index={e['unesco_id']:e for e in entries}
    file_pages={}
    for p in xm.get('pages',[]):
        pid=p.get('page_id');rel=p.get('relative_path')
        if type(pid) is not int or pid<1 or pid in file_pages:
            raise StageError('Bad or duplicated XML page id')
        if rel!=f'page-{pid}.wikitext.txt':raise StageError('Unexpected extracted text path')
        path=work/'wikipedia_extract'/rel
        if path.is_symlink() or not path.is_file() or path.stat().st_size>20_000_000:
            raise StageError('Missing/symlinked/oversized extracted text')
        data=path.read_bytes()
        if sha_bytes(data)!=p.get('sha256'):raise StageError('Extracted text SHA-256 changed')
        file_pages[pid]={'meta':p,'redirect':redirects(data),'bytes':len(data),'file':path}
    result={};tasks={};edges=[];external_links=0;safe_article_refs=0;redir_ids=set();no_qid=[]
    known={r['unesco_id'] for r in records}
    order=['concept10']+[r['unesco_id'] for r in records if r['unesco_id']!='concept10']
    for cid in order:
        rec=next(r for r in records if r['unesco_id']==cid)
        dos=entry_index[cid]
        if dos.get('unesco_source_uri')!=rec.get('unesco_uri'):
            raise StageError(f'UNESCO URI mismatch: {cid}')
        wd=rec.get('wikidata') or {}
        if wd.get('canonical_exact_match') is not False:
            raise StageError('Invented canonical exactMatch in inventory')
        qid=wd.get('qid')
        if qid is not None and (not isinstance(qid,str) or not re.fullmatch(r'Q[1-9][0-9]*',qid)):
            raise StageError(f'Bad candidate QID: {cid}')
        if not qid:no_qid.append(cid)
        skos=rec.get('skos') or {}
        rels=[]
        for relation in ('broader','narrower','related'):
            ids=skos.get(relation) or []
            if not isinstance(ids,list):raise StageError('SKOS IDs not list')
            for target in ids:
                if not isinstance(target,str) or not CID.fullmatch(target):
                    raise StageError('Unsafe SKOS target ID')
                link={'from_unesco_id':cid,'relation':relation,'to_unesco_id':target,
                      'to_branch_member':target in known,'authority':'UNESCO_SKOS_OBSERVED_NOT_KA'}
                rels.append(link);edges.append(link)
                if target not in known:external_links+=1
        refs=[]
        for link in dos.get('wikipedia_en',[]):
            pid=link.get('page_id')
            if pid not in file_pages:raise StageError('Skope page reference missing XML text')
            target=file_pages[pid];meta=target['meta']; local=link.get('local_text') or {}
            source_page=link.get('wikipedia_page_metadata') or {}
            if (str(meta.get('revision_id'))!=str(local.get('revision_id')) or
                meta.get('sha256')!=local.get('text_sha256') or
                source_page.get('page_id')!=pid):
                raise StageError('Dossier XML page identity mismatch')
            title_ok=meta.get('inventory_title_agrees') is True and local.get('title_agrees') is True
            rev_ok=meta.get('inventory_revision_agrees') is True and local.get('revision_agrees') is True
            allowed=bool(title_ok and rev_ok and local.get('ai_context_eligible') is True and
                         local.get('source_integrity_status')=='CANDIDATE_MATCHED' and
                         not target['redirect'])
            if target['redirect']:redir_ids.add(pid)
            if allowed:safe_article_refs+=1
            refs.append({'page_id':pid,'title':meta.get('title'),'revision_id':meta.get('revision_id'),
                         'sha256':meta.get('sha256'),'text_bytes':target['bytes'],
                         'is_redirect':target['redirect'],'candidate_context_usable':allowed,
                         'source_status':('REDIRECT_NOT_ARTICLE' if target['redirect'] else
                              'MATCHED_RESEARCH_CONTEXT' if allowed else 'UNUSABLE_IDENTITY_MISMATCH'),
                         'local_private_path':str(target['file']) if allowed else None,
                         'license_cleared':False})
        card={'format':'koa.unesco-mt1-10-semantic-review-card/1.0',
              'branch':'unesco-mt1-10','unesco_id':cid,'unesco_uri':rec.get('unesco_uri'),
              'labels':rec.get('unesco_preferred_labels'),'wikidata_qid_candidate':qid,
              'wikidata_mapping_status':'UNREVIEWED_EXTERNAL_CANDIDATE',
              'skos_links':rels,'wikipedia_en':refs,'candidate_knowledge_status':'SOURCE_OBSERVATIONS_ONLY',
              'canonical_KQ':None,'canonical_KP':[], 'canonical_KA':[], 'canonical_KS':[],
              'assertion_review_status':'NOT_STARTED','target_locales':list(LOCALES),
              'public_release_authorized':False,'one_branch_kristal':True}
        result[cid]=card
        tasks[cid]={'format':AI_TASK_FORMAT,'branch':'unesco-mt1-10','unesco_id':cid,
                    'priority':'PILOT_FIRST' if cid=='concept10' else 'AFTER_PILOT',
                    'prompt_language':'en', 'instruction':(
                        'Draft candidate policy-encyclopedia claims only. Include jurisdiction, time, '
                        'uncertainty and exact source locator wherever applicable. Distinguish observed '
                        'UNESCO SKOS from factual policy assertions. Model knowledge is not a KS; '
                        'Wikipedia text is unverified context only. Do not invent KQ/KP/KA/KS, '
                        'Wikidata exactMatches, RuntimeSet qualification, copyright clearance or publication.'),
                    'output_contract':'kristalizer.unesco-mt1-10-raw-ai-proposals/1.0',
                    'unesco_source_uri':rec.get('unesco_uri'),'labels':rec.get('unesco_preferred_labels'),
                    'candidate_wikidata_qid':qid,
                    'available_wikipedia_en_contexts':[x for x in refs if x['candidate_context_usable']],
                    'skos_observations':rels,'model_invocation_performed':False,'proposals_generated':0,
                    'publication_authorized':False}
    unique_edges=list({(x['from_unesco_id'],x['relation'],x['to_unesco_id']):x for x in edges}.values())
    staging={'format':FORMAT,'branch':'unesco-mt1-10','one_branch_kristal':True,
             'source_sha256':hashes, 'source_paths':{k:str(v) for k,v in paths.items()},
             'concept_count':41,'candidate_qids':41-len(no_qid),'missing_candidate_qids':no_qid,
             'skos_observed_edge_count':len(unique_edges),'cross_branch_link_count':external_links,
             'wikipedia_substantive_contexts':safe_article_refs,'wikipedia_redirect_pages':len(redir_ids),
             'wikipedia_redirect_page_ids':sorted(redir_ids),'languages_planned':list(LOCALES),
             'projection_slots':574,'articles_generated':0,'ai_model_calls':0,
             'canonical_assertions_approved':0,'canonical_kristal_built':False,
             'language_runtimes_qualified':False,'public_release_authorized':False,
             'status':'PRIVATE_CANDIDATE_STAGE_NOT_CANONICAL',
             'next':'Human/API AI research with provenance, Kristalizer review, Kit v11 canonical check and real RuntimeSets'}
    return order,result,tasks,unique_edges,staging

def write_stage(work:Path,out:Path):
    work=work.resolve();out=out.resolve()
    if out==work or work.is_relative_to(out) or not out.is_relative_to(work):
        raise StageError('Stage output must be a NEW child directory of the existing private work folder')
    forbid_git(out)
    order,cards,tasks,edges,report=build(work)
    # Idempotence: if completed and unchanged, reuse; any drift blocks overwriting.
    if out.exists():
        marker=out/'manifest.json'
        if marker.is_file():
            existing=load(marker)
            if existing==report and all((out/'cards'/(cid+'.json')).is_file() and
                                    (out/'ai_tasks'/(cid+'.json')).is_file() for cid in order):
                for cid in order:
                    if (out/'cards'/(cid+'.json')).read_bytes()!=canonical_json(cards[cid]) or \
                       (out/'ai_tasks'/(cid+'.json')).read_bytes()!=canonical_json(tasks[cid]):
                        raise StageError('Previously generated card or task altered; do not overwrite')
                if (out/'skos_candidate_edges.json').read_bytes()!=canonical_json({'edges':edges}):
                    raise StageError('Previously generated edge file altered')
                return dict(report, reused=True,output_path=str(out))
        raise StageError('Output already exists with different contents. Refuse overwrite.')
    if not out.parent.is_dir():raise StageError('Parent work directory absent')
    tmp=Path(tempfile.mkdtemp(prefix='.semantic_v4_',dir=out.parent))
    try:
        for cid in order:
            write_json(tmp/'cards'/(cid+'.json'),cards[cid])
            write_json(tmp/'ai_tasks'/(cid+'.json'),tasks[cid])
        write_json(tmp/'skos_candidate_edges.json',{'edges':edges})
        write_json(tmp/'manifest.json',report)
        (tmp/'LIRE_DABORD.txt').write_text(
            'ÉTAPE 4 — DOSSIER PRIVÉ DE CANDIDATS SÉMANTIQUES\n'
            '41 fiches UNESCO + observations SKOS et QID candidats + contextes Wikipédia EN.\n'
            'Un seul Kristal de branche. AUCUN KQ/KP/KA/KS canonique créé.\n'
            'Le dossier ai_tasks/ prépare les demandes à un moteur IA qui doit être connecté\n'
            'séparément, de manière autorisée et avec un vrai identifiant de génération.\n'
            'Le modèle et les assertions ne sont pas qualifiés ici.\n'
            'Aucun dépôt GitHub modifié. Ne pas publier ces dossiers bruts.\n',encoding='utf-8')
        os.rename(tmp,out)
    finally:
        if tmp.exists():shutil.rmtree(tmp)
    return dict(report,reused=False,output_path=str(out))

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,default=Path(r'D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41'))
    p.add_argument('--out',type=Path)
    a=p.parse_args(argv)
    try:
        output=a.out if a.out else a.work/'semantic_stage_v4'
        result=write_stage(a.work,output)
        print(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False))
        return 0
    except (StageError,OSError,ValueError,TypeError,KeyError) as e:
        print(json.dumps({'status':'BLOCKED','error':str(e),'public_release_authorized':False},ensure_ascii=False),file=sys.stderr)
        return 2
if __name__=='__main__':raise SystemExit(main())
