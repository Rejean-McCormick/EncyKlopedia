#!/usr/bin/env python3
"""Raccordement multibranche natif de la station V30/V31.1.

Un espace de découverte v28 par manifeste réel, journalisation des routes
sur les tâches nouvelles, import par le moteur v28 officiel. Ne remplace ni
les IDs des propositions ni les preuves originales. La branche historique
reste sur son ancienne base et ses anciennes commandes.
"""
from __future__ import annotations
from contextlib import closing
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import subprocess
import sys
import zipfile


def folder(branch_id):
    return 'b_'+hashlib.sha256(branch_id.encode('utf-8')).hexdigest()[:16]


def all_branches(station,engine):
    root=station.repo/'tools'/'unesco_pilot'/'v25_data'
    if not root.is_dir():return []
    legacy=engine.v25.load_branch(engine.v25.DEFAULT_BRANCH)['id']
    out=[];seen={legacy}
    for file in sorted(root.rglob('branche_*.json')):
        branch=engine.v25.load_branch(file)
        bid=branch['id']
        if bid in seen:continue
        seen.add(bid)
        work=station.v28/'branches'/folder(bid)
        out.append({'branch':branch,'manifest':file,'work':work,
                    'stage':work/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'})
    return out


def live(station,engine):
    return [r for r in all_branches(station,engine) if r['stage'].is_file()]


def _catalogued(station,engine):
    if not station.catalogue.is_file():return set()
    from contextlib import closing
    import poste_chatgpt_v30 as s
    with closing(s.uri_ro(station.catalogue)) as db:
        return {r[0] for r in db.execute('SELECT branch_id FROM branches')}


def refresh(station,engine):
    """Intégrer les candidats de toutes les découvertes secondaires déjà disponibles."""
    import poste_chatgpt_v30 as s
    from priorisation_native_v31 import score
    added=0
    if not station.catalogue.is_file():return 0
    with closing(s.uri_ro(station.catalogue)) as cat:
        for route in live(station,engine):
            branch=route['branch'];bid=branch['id']
            with closing(s.uri_ro(route['stage'])) as work:
                if (engine.v25.meta(work,'schema')!=engine.FORMAT or
                    engine.v25.meta(work,'branch_signature')!=branch['signature'] or
                    engine.v25.meta(work,'branch_id')!=bid):
                    raise ValueError('Découverte multibranche incompatible : '+bid)
                labels={c['unesco_id']:engine.v25.label(c,'en') for c in branch['concepts']}
                classified={(c,int(p)) for c,p in cat.execute('SELECT concept_id,page_id FROM assignments WHERE branch_id=? AND wiki=?',(bid,'enwiki'))}
                if cat.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='reviewed_article_links_v28'").fetchone():
                    classified.update((c,int(p)) for c,p in cat.execute('SELECT concept_id,page_id FROM reviewed_article_links_v28 WHERE branch_id=?',(bid,)))
                query='''SELECT c.branch_id,c.concept_id,c.page_id,c.title,
                 COUNT(DISTINCT e.seed_page_id) seed_count,
                 SUM(CASE WHEN e.kind='WIKILINK' THEN 1 ELSE 0 END) links,
                 SUM(CASE WHEN e.kind='SHARED_CATEGORY' THEN 1 ELSE 0 END) shared,
                 SUM(CASE WHEN e.kind='SUBCATEGORY' THEN 1 ELSE 0 END) subs
                 FROM candidates c JOIN evidence e ON e.branch_id=c.branch_id
                 AND e.concept_id=c.concept_id AND e.page_id=c.page_id
                 WHERE c.branch_id=? GROUP BY c.branch_id,c.concept_id,c.page_id'''
                with station.db:
                    for raw in work.execute(query,(bid,)):
                        d=dict(raw);cid=d['concept_id'];pid=int(d['page_id'])
                        if (cid,pid) in classified or cid not in labels:continue
                        candidate_id=engine.candidate_id(bid,cid,pid)
                        rating=score(d,labels[cid])
                        cur=station.db.execute('''INSERT OR IGNORE INTO review_index(candidate_id,branch_id,concept_id,page_id,title,
                            priority,seed_count,link_evidence,category_evidence,subcategory_evidence,state,last_seen_utc)
                            VALUES(?,?,?,?,?,?,?,?,?,?,'PENDING',?)''',
                            (candidate_id,bid,cid,pid,d['title'],rating,d['seed_count'],d['links'],d['shared'],d['subs'],s.now()))
                        added+=cur.rowcount
                        station.db.execute('''UPDATE review_index SET title=?,priority=?,seed_count=?,link_evidence=?,
                            category_evidence=?,subcategory_evidence=?,last_seen_utc=?,
                            state=CASE WHEN ?<15 AND ?=0 THEN 'DEFERRED' ELSE 'PENDING' END
                            WHERE candidate_id=? AND state IN ('PENDING','DEFERRED') ''',
                            (d['title'],rating,d['seed_count'],d['links'],d['shared'],d['subs'],s.now(),
                             rating,d['links'],candidate_id))
    return added


def prepare(station,engine):
    """Packs par branche; jamais de mélange qui rendrait les imports ambigus."""
    import poste_chatgpt_v30 as s
    from priorisation_native_v31 import select
    sources=live(station,engine)
    if not sources:return 0
    queued=station._open_review_count();created=0
    if queued>=s.QUEUE_BUFFER:return 0
    while queued<s.QUEUE_BUFFER:
        progress=False
        for route in sources:
            if queued>=s.QUEUE_BUFFER:break
            branch=route['branch'];bid=branch['id']
            ranked=list(station.db.execute('''SELECT * FROM review_index WHERE state='PENDING' AND branch_id=?
                ORDER BY priority DESC,seed_count DESC,page_id ASC LIMIT ?''',(bid,max(6000,s.REVIEW_SIZE*15))))
            if not ranked:continue
            take=min(s.REVIEW_SIZE,s.MAX_REVIEW_SIZE)
            top=select(ranked,min(len(ranked),round(take*.75)),explore=.18)
            weak=list(station.db.execute('''SELECT * FROM review_index WHERE state='DEFERRED' AND branch_id=?
                ORDER BY priority DESC,page_id ASC LIMIT ?''',(bid,max(6000,s.REVIEW_SIZE*15))))
            chosen=top+select(weak,min(take-len(top),len(weak)),explore=1.0)
            if len(chosen)<take:
                seen={x['candidate_id'] for x in chosen}
                chosen.extend(x for x in ranked if x['candidate_id'] not in seen)
                chosen=chosen[:take]
            labels={c['unesco_id']:engine.v25.label(c,'en') for c in branch['concepts']}
            rows=[];complexity=0
            with closing(s.uri_ro(route['stage'])) as work:
                for item in chosen:
                    cost=1+min(3,(int(item['link_evidence'])+int(item['category_evidence'])+int(item['subcategory_evidence']))//8)
                    if len(rows)>=s.MIN_REVIEW_SIZE and complexity+cost>s.REVIEW_BUDGET:break
                    src=work.execute('SELECT * FROM candidates WHERE branch_id=? AND concept_id=? AND page_id=?',
                                     (bid,item['concept_id'],item['page_id'])).fetchone()
                    if src is None:
                        station.db.execute("UPDATE review_index SET state='STALE' WHERE candidate_id=? AND state='PENDING'",(item['candidate_id'],))
                        continue
                    cand=engine.build_candidate(work,src,labels[item['concept_id']])
                    if not cand or cand['candidate_id']!=item['candidate_id']:
                        raise ValueError('Empreinte ou candidat incohérent : '+item['candidate_id'])
                    rows.append({'candidate_id':cand['candidate_id'],'branch_id':cand['branch_id'],
                      'concept_id':cand['concept_id'],'concept_en':cand['concept_en'],'page_id':cand['page_id'],
                      'title':cand['title'],'priority':cand['priority'],'seed_count':cand['seed_count'],
                      'link_evidence':cand['links'],'category_evidence':cand['shared'],
                      'subcategory_evidence':cand['subs'],'evidence_sha256':cand['evidence_sha256'],
                      'examples':cand['examples'],'decision':'HOLD','justification':''})
                    complexity+=cost
                generation=str(engine.v25.meta(work,'catalogue_sequence') or '')
            if not rows:continue
            raw=s.csv_bytes(rows)
            jid='v28_'+s.sha(raw)[:14]+'_'+secrets.token_hex(4)
            basedir=station.work/'review_sources';basedir.mkdir(parents=True,exist_ok=True)
            srcpath=basedir/(jid+'.csv');bundle=station.work/'bundles'/(jid+'.zip')
            bundle.parent.mkdir(parents=True,exist_ok=True)
            srcpath.write_bytes(raw)
            info={'id':jid,'kind':'v28','count':len(rows),'bundle_path':str(bundle)}
            tmp=bundle.with_suffix('.tmp')
            with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
                z.writestr('REVUE_'+jid+'.csv',raw)
                z.writestr('INSTRUCTIONS_CHATGPT.txt',
                           'Revue UNESCO multibranche : conserver exactement candidate_id, decision, justification; '
                           'relire les preuves contextuelles. APPROVE seulement pour correspondance substantielle. '\
                           'Aucune admission canonique.\n')
                z.writestr('PROMPT_CHATGPT.txt',s.prompt(info))
            tmp.replace(bundle)
            with station.db:
                station.db.execute('''INSERT INTO jobs(id,kind,key,count,status,source_path,source_sha256,
                 bundle_path,bundle_sha256,created_utc,source_generation) VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                 (jid,'v28',jid,len(rows),'WAITING',str(srcpath),s.sha(raw),str(bundle),s.sha_path(bundle),s.now(),generation))
                station.db.execute('''INSERT INTO v311_job_routes(job_id,branch_id,manifest_path,stage_path,work_path,branch_signature)
                 VALUES(?,?,?,?,?,?)''',(jid,bid,str(route['manifest']),str(route['stage']),str(route['work']),branch['signature']))
                station.db.executemany('''UPDATE review_index SET state='QUEUED',task_id=?,evidence_sha256=?
                  WHERE candidate_id=? AND state IN ('PENDING','DEFERRED') ''',[(jid,x['evidence_sha256'],x['candidate_id']) for x in rows])
            queued+=1;created+=1;progress=True
        if not progress:break
    return created


def job_route(station,job_id):
    return station.db.execute('SELECT * FROM v311_job_routes WHERE job_id=?',(job_id,)).fetchone()


def apply(station,engine,job,decisions_file,dry_run):
    """Réutiliser strictement la validation/l'importation officielle v28."""
    route=job_route(station,job['id'])
    if route is None:
        return station._run('DECOUVRIR_ARTICLES_RELIES_V28.ps1',
            ['-Action','Apply','-DecisionsFile',str(decisions_file)]+(['-DryRun'] if dry_run else []))
    branch=engine.v25.load_branch(Path(route['manifest_path']))
    if branch['id']!=route['branch_id'] or branch['signature']!=route['branch_signature']:
        raise ValueError('Manifeste de branche de la tâche modifié')
    options=[sys.executable,str(station.repo/'tools'/'unesco_pilot'/'decouvrir_articles_relies_v28.py'),
             'apply','--branch',route['manifest_path'],'--work',route['work_path'],
             '--catalogue-db',str(station.catalogue),'--decisions',str(decisions_file)]
    if dry_run:options.append('--dry-run')
    proc=subprocess.run(options,cwd=station.repo,text=True,encoding='utf-8',errors='replace',
                        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=7200)
    for line in proc.stdout.splitlines()[-12:]:station._log(line[:550])
    if proc.returncode:raise ValueError('Import v28 multibranche refusé : '+proc.stdout[-1100:])
    return proc.stdout


def relational_discover(station,engine,manifest,work_dir,max_seeds=3000):
    """Run relational discovery while preserving v28 source integrity."""
    cmd=[sys.executable,str(station.repo/'tools'/'unesco_pilot'/'decouverte_relationnelle_v311.py'),
         '--branch',str(manifest),'--work',str(work_dir),
         '--catalogue-db',str(station.catalogue),'--max-seeds',str(max_seeds)]
    result=subprocess.run(cmd,cwd=station.repo,text=True,encoding='utf-8',errors='replace',
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=7200)
    for line in result.stdout.splitlines()[-7:]:station._log(line[:550])
    if result.returncode:raise ValueError('Découverte SQL relationnelle refusée : '+result.stdout[-1100:])
    return result.stdout


def discover_other(station,engine,max_seeds=3000):
    """Découvrir les branches nouvelles déjà enregistrées au catalogue v25."""
    enabled=_catalogued(station,engine)
    produced=[]
    for route in all_branches(station,engine):
        if route['branch']['id'] not in enabled:continue
        route['work'].mkdir(parents=True,exist_ok=True)
        cmd=[sys.executable,str(station.repo/'tools'/'unesco_pilot'/'decouvrir_articles_relies_v28.py'),
             'discover','--branch',str(route['manifest']),'--work',str(route['work']),
             '--catalogue-db',str(station.catalogue),'--max-seeds',str(max_seeds)]
        proc=subprocess.run(cmd,cwd=station.repo,text=True,encoding='utf-8',errors='replace',
                            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=7200)
        if proc.returncode:
            reason=proc.stdout.lower()
            if ('ne correspond pas a l index v21' in reason or
                'ne correspond pas à l index v21' in reason or
                'signature du xml differente' in reason):
                relational_discover(station,engine,route['manifest'],route['work'],max_seeds)
                produced.append(route['branch']['id'])
            else:station._log('Découverte '+route['branch']['id']+' refusée : '+proc.stdout[-500:])
        else:produced.append(route['branch']['id'])
    return produced
