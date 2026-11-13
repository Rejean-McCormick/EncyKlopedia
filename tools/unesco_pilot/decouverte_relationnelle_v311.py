#!/usr/bin/env python3
"""Découverte UNESCO v28 par liens SQL indexés, sans index d'offsets XML v21.

Réutilise les contrats exacts candidats/evidence/seed_queue de v28. Une preuve
WIKILINK provient d'une ligne réelle de wiki_pagelinks et de son target_id;
elles ne prétend pas citer un passage XML. L'importeur v28 reste inchangé.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sqlite3
import sys
import decouvrir_articles_relies_v28 as v28


def _targets(source,pid,limit):
    # La cible d'un wiki_pagelink est un linktarget, pas directement un page_id.
    query='''SELECT DISTINCT p.page_id,p.ns,p.title,p.redirect,p.latest_revision,p.content_bytes,lt.title AS linked_title
      FROM wiki_pagelinks l
      JOIN wiki_linktargets lt ON lt.target_id=l.target_id AND lt.ns=0
      JOIN wiki_pages p ON p.ns=lt.ns AND p.title=lt.title
      WHERE l.source_page_id=? AND p.redirect=0 AND p.ns=0
      ORDER BY p.page_id LIMIT ?'''
    for row in source.execute(query,(pid,limit)):
        if int(row['page_id'])!=pid:
            yield row


def _new_evidence(source,cat,seed,branch,labels,roots,max_links,max_cat=25,max_members=60):
    pid=int(seed['page_id']);bid=branch['id']
    concepts=v28.concepts_for_page(cat,bid,pid)
    results=defaultdict(set);pages={}
    for p in _targets(source,pid,max_links):
        target=int(p['page_id']);pages[target]=p
        for cid,_ in concepts:
            results[(cid,target)].add(('WIKILINK','WIKILINK_SQL: '+str(p['linked_title']).replace('_',' ')))
    # Les catégories doivent être liées au concept, non une simple coïncidence géographique.
    origin=v28.category_labels(source,pid,max_cat)
    for cid,_ in concepts:
        label=labels[cid]
        qualified=[(target,title) for target,title in origin
           if v28.v25.topic_category(title) and (v28.v25.normalize(title) in roots[cid] or
                                               v28.title_word_match(title,label)>0)]
        for category_id,category_name in qualified[:2]:
            members,too_large=v28.bounded_members(source,category_id,250,max_members,'page')
            if too_large:continue
            for p in members:
                target=int(p['page_id'])
                if target==pid:continue
                pages[target]=p
                results[(cid,target)].add(('SHARED_CATEGORY','CATEGORY_SQL: '+category_name))
    own={(cid,pid) for cid,_ in concepts}
    for cid,target in sorted(results):
        if (cid,target) in own:continue
        for kind,detail in sorted(results[(cid,target)]):
            yield cid,target,pages[target],kind,detail


def run(source_db,catalogue_db,branch_path,work_dir,*,max_seeds=3000,max_links=160):
    if not 1<=max_seeds<=25000 or not 2<=max_links<=2000:
        raise ValueError('Bornes hors limites')
    branch=v28.v25.load_branch(branch_path)
    source,cat,source_sig=v28.checked_source(source_db,catalogue_db,branch)
    path=work_dir/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
    work=None
    try:
        work_dir.mkdir(parents=True,exist_ok=True)
        work=v28.open_work(path)
        current_branch=v28.v25.meta(work,'branch_id')
        if current_branch is None:
            # Conserver la vraie signature du dump, si présent, pour permettre
            # une future reprise native une fois l'index v21 corrigé.
            try:
                xml_sig=(v28.v27.xml_signature(v28.v27.DEFAULT_XML)
                         if v28.v27.DEFAULT_XML.is_file() else
                         {'mode':'SQL_RELATIONAL_V311','source_sha':source_sig})
            except (OSError,ValueError,v28.v27.Refusal):
                xml_sig={'mode':'SQL_RELATIONAL_V311','source_sha':source_sig}
            v28.bind_work(work,source_sig,xml_sig,branch)
        elif (current_branch!=branch['id'] or
              v28.v25.meta(work,'branch_signature')!=branch['signature'] or
              v28.v25.meta(work,'source_sha')!=source_sig):
            raise ValueError('Base de découverte liée à une autre branche/source')
        # Ne jamais réinitialiser des tâches déjà figées ni changer l'origine des preuves.
        seq=int(v28.v25.meta(cat,'sequence'))
        added_seeds=v28.sync_seeds(cat,work,branch['id'],seq)
        labels={c['unesco_id']:v28.v25.label(c,'en') for c in branch['concepts']}
        roots=v28.reviewed_roots(cat,branch['id'])
        processed=0;edges=0
        while processed<max_seeds:
            seed=work.execute("SELECT * FROM seed_queue WHERE branch_id=? AND state='PENDING' ORDER BY page_id LIMIT 1",
                              (branch['id'],)).fetchone()
            if seed is None:break
            # La référence de révision provient de l'index SQL, pas d'un XML non validé.
            actual=source.execute('SELECT latest_revision,title,redirect,ns FROM wiki_pages WHERE page_id=?',
                                  (int(seed['page_id']),)).fetchone()
            if (actual is None or int(actual['ns'])!=0 or int(actual['redirect']) or
                    str(actual['latest_revision'])!=str(seed['revision'])):
                raise ValueError('Révision de la graine/source SQL divergente : '+str(seed['page_id']))
            found=list(_new_evidence(source,cat,seed,branch,labels,roots,max_links))
            with work:
                for cid,pid,p,kind,detail in found:
                    work.execute('INSERT OR IGNORE INTO candidates VALUES(?,?,?,?,?,?)',
                          (branch['id'],cid,pid,str(p['title']).replace('_',' '),
                           str(p['latest_revision'] or ''),v28.now()))
                    edges+=work.execute('INSERT OR IGNORE INTO evidence VALUES(?,?,?,?,?,?)',
                          (branch['id'],cid,pid,int(seed['page_id']),kind,detail)).rowcount
                work.execute("UPDATE seed_queue SET state='DONE',processed_utc=? WHERE branch_id=? AND page_id=?",
                             (v28.now(),branch['id'],int(seed['page_id'])))
            processed+=1
        pending=work.execute("SELECT COUNT(*) FROM seed_queue WHERE branch_id=? AND state='PENDING'",(branch['id'],)).fetchone()[0]
        return {'status':'V311_SQL_DISCOVERY_OK','branch_id':branch['id'],'new_seeds':added_seeds,
                'seeds_processed':processed,'seeds_pending':pending,'new_evidence':edges,
                'candidate_pairs':work.execute('SELECT COUNT(*) FROM candidates WHERE branch_id=?',(branch['id'],)).fetchone()[0],
                'origin':'wiki_pagelinks/wiki_linktargets/wiki_pages et catégories SQL',
                'xml_excerpt_verified':False,'catalogue_modified':False,'canonical_admissions':0}
    finally:
        if work is not None:work.close()
        cat.close();source.close()


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-db',type=Path,default=v28.v25.DEFAULT_SOURCE)
    p.add_argument('--catalogue-db',type=Path,default=v28.v25.DEFAULT_CATALOG)
    p.add_argument('--branch',type=Path,default=v28.v25.DEFAULT_BRANCH)
    p.add_argument('--work',type=Path,default=v28.DEFAULT_WORK)
    p.add_argument('--max-seeds',type=int,default=3000)
    p.add_argument('--max-links-per-seed',type=int,default=160)
    a=p.parse_args(argv)
    try:
        print(json.dumps(run(a.source_db,a.catalogue_db,a.branch,a.work,
                             max_seeds=a.max_seeds,max_links=a.max_links_per_seed),ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,sqlite3.Error,v28.Refusal,v28.v25.Refusal) as ex:
        print(json.dumps({'status':'V311_SQL_DISCOVERY_REFUS','reason':str(ex)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
