#!/usr/bin/env python3
"""EncyKlopedia v28 : decouverte indexee, revue explicite, integration incrementale.

Aucun balayage de l'XML : articles graines lus un par un via l'index v21.
Toutes les suggestions sont documentaires, NON canoniques. Aucune acceptation implicite.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import heapq
import csv
from datetime import datetime, timezone
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import zipfile

# Python -I used by the Windows launcher strips the script directory from sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogue_global_v25 as v25
import integrer_ponts_revus_v26 as v26
import production_kristals_v27 as v27

FORMAT = 'encyklopedia.linked-article-discovery.v28/1'
REVIEW_FORMAT = 'encyklopedia.linked-article-review.v28/1'
DEFAULT_WORK = Path(r'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28')
LINK_PATTERN = re.compile(r'\[\[([^\[\]\r\n]{1,350})\]\]')
TOKEN_PATTERN = re.compile(r'[a-z]{4,}', re.I)
STOPWORDS = {'that','this','with','from','have','such','which','into','school','schools','education',
             'educational','article','articles','policy','policies','history','american','united',
             'states','theory','university','universities','students','study','studies'}
FIELDS = ('candidate_id','branch_id','concept_id','concept_en','page_id','title','priority',
          'seed_count','link_evidence','category_evidence','subcategory_evidence','evidence_sha256',
          'examples','decision','justification')

class Refusal(v25.Refusal):
    pass


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def jbytes(obj):
    return v25.blob(obj)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def candidate_id(bid, cid, pageid):
    return 'V28_' + digest(f'{bid}\0{cid}\0{pageid}'.encode())[:24]


def tokens(text):
    return set(TOKEN_PATTERN.findall(str(text).lower())) - STOPWORDS


def title_word_match(title, concept):
    t = tokens(title)
    c = tokens(concept)
    return len(t & c) if c else 0


def parse_wikilinks(text, maximum):
    """Scan the entire wikitext, but bound the number of indexed title lookups.

    Spread sampled links throughout the full article, including its ending.
    This does not truncate or modify the original article.
    """
    unique = {}
    for match in LINK_PATTERN.finditer(text):
        raw = html.unescape(match.group(1).split('|', 1)[0].split('#', 1)[0]).strip()
        raw = ' '.join(raw.replace('_', ' ').split())
        if (not raw or raw.startswith(':') or ':' in raw or len(raw) > 240
                or any(ord(x) < 32 for x in raw) or raw.startswith(('/', '#'))):
            continue
        raw = raw[0].upper() + raw[1:]
        unique.setdefault(raw, None)
    names = list(unique)
    if len(names) <= maximum:
        return names
    # Both lead and end of the article are represented in a reproducible sample.
    indices = [(i * (len(names)-1)) // (maximum-1) for i in range(maximum)]
    return [names[i] for i in dict.fromkeys(indices)]


INIT = '''
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS seed_queue(
  branch_id TEXT NOT NULL,page_id INTEGER NOT NULL,title TEXT NOT NULL,revision TEXT NOT NULL,
  concept_sha TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'PENDING',
  processed_utc TEXT,PRIMARY KEY(branch_id,page_id));
CREATE INDEX IF NOT EXISTS idx_v28_seeds ON seed_queue(branch_id,state,page_id);
CREATE TABLE IF NOT EXISTS candidates(
  branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,page_id INTEGER NOT NULL,
  title TEXT NOT NULL,revision TEXT NOT NULL,first_seen TEXT NOT NULL,
  PRIMARY KEY(branch_id,concept_id,page_id));
CREATE INDEX IF NOT EXISTS idx_v28_candidate_article ON candidates(branch_id,page_id);
CREATE TABLE IF NOT EXISTS evidence(
  branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,page_id INTEGER NOT NULL,
  seed_page_id INTEGER NOT NULL,kind TEXT NOT NULL,detail TEXT NOT NULL,
  PRIMARY KEY(branch_id,concept_id,page_id,seed_page_id,kind,detail));
CREATE INDEX IF NOT EXISTS idx_v28_evidence ON evidence(branch_id,concept_id,page_id);
-- Optional observation ledger. Added safely by CREATE IF NOT EXISTS to existing v28
-- workspaces, including those interrupted after 100 or more completed seeds.
CREATE TABLE IF NOT EXISTS seed_revision_mismatches(
  branch_id TEXT NOT NULL,page_id INTEGER NOT NULL,
  catalogue_revision TEXT NOT NULL,xml_revision TEXT NOT NULL,
  xml_title TEXT NOT NULL,observed_utc TEXT NOT NULL,
  PRIMARY KEY(branch_id,page_id));
'''


def open_work(path):
    return v27.state_db(path, FORMAT, INIT)


def checked_source(source_path, catalogue_path, branch):
    if source_path.resolve() == catalogue_path.resolve():
        raise Refusal('La base source et le catalogue doivent etre distincts')
    source = v25.source_ro(source_path)
    try:
        info, signature = v25.source_fingerprint(source, source_path)
        cat = v26.read_catalogue_ro(catalogue_path)
        try:
            v26.verify_catalogue(cat, branch, signature)
            return source, cat, signature
        except BaseException:
            cat.close()
            raise
    except BaseException:
        source.close()
        raise


def bind_work(work, signature, xml_signature, branch):
    data = {'source_sha': signature, 'xml_signature': json.dumps(xml_signature, sort_keys=True),
            'branch_id': branch['id'], 'branch_signature': branch['signature']}
    with work:
        for key, val in data.items():
            old = v25.meta(work, key)
            if old is not None and old != val:
                raise Refusal('L espace v28 est lie a une autre source/branche: ' + key)
            work.execute('INSERT OR IGNORE INTO meta(key,value) VALUES(?,?)', (key, val))


def concepts_for_page(cat, bid, page_id):
    return [(r['concept_id'], int(r['score'])) for r in cat.execute(
        "SELECT concept_id,score FROM assignments WHERE branch_id=? AND wiki='enwiki' AND page_id=? "
        'ORDER BY concept_id', (bid, page_id))]


def sync_seeds(cat, work, bid, sequence, batch_size=2000):
    """Incremental keyset scan of small derived catalogue, durable per chunk."""
    last = v25.meta(work, 'catalogue_sequence')
    if last == str(sequence) and v25.meta(work, 'sync_page_id') is None:
        return 0
    cursor = int(v25.meta(work, 'sync_page_id') or 0)
    if v25.meta(work, 'sync_target') != str(sequence):
        with work:
            work.execute("INSERT INTO meta VALUES('sync_target',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(sequence),))
            work.execute("INSERT INTO meta VALUES('sync_page_id','0') ON CONFLICT(key) DO UPDATE SET value='0'")
        cursor = 0
    changed = 0
    while True:
        rows = cat.execute('''SELECT a.page_id,a.title,a.revision_id FROM articles a
            WHERE a.wiki='enwiki' AND a.page_id>?
            AND EXISTS(SELECT 1 FROM assignments x WHERE x.branch_id=? AND x.wiki=a.wiki AND x.page_id=a.page_id)
            ORDER BY a.page_id LIMIT ?''',(cursor,bid,batch_size)).fetchall()
        if not rows:
            with work:
                work.execute("INSERT INTO meta VALUES('catalogue_sequence',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(sequence),))
                work.execute("DELETE FROM meta WHERE key IN ('sync_page_id','sync_target')")
            return changed
        with work:
            for a in rows:
                pid = int(a['page_id'])
                cats = concepts_for_page(cat, bid, pid)
                concept_sha = digest(jbytes(cats))
                revision = str(a['revision_id'] or '')
                old = work.execute('SELECT revision,concept_sha,state FROM seed_queue WHERE branch_id=? AND page_id=?',
                                   (bid,pid)).fetchone()
                if old is None:
                    work.execute('INSERT INTO seed_queue(branch_id,page_id,title,revision,concept_sha) VALUES(?,?,?,?,?)',
                                 (bid,pid,str(a['title']),revision,concept_sha))
                    changed += 1
                elif old['revision'] != revision or old['concept_sha'] != concept_sha:
                    work.execute("UPDATE seed_queue SET title=?,revision=?,concept_sha=?,state='PENDING',processed_utc=NULL "
                                 'WHERE branch_id=? AND page_id=?', (str(a['title']),revision,concept_sha,bid,pid))
                    changed += 1
            cursor = int(rows[-1]['page_id'])
            work.execute("INSERT INTO meta VALUES('sync_page_id',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(cursor),))


def category_labels(source, page_id, max_found=50):
    rows = source.execute('''SELECT lt.target_id,lt.title FROM wiki_categorylink_ids c INDEXED BY idx_wiki_catid_from
         JOIN wiki_linktargets lt ON lt.target_id=c.target_id AND lt.ns=14
         WHERE c.source_page_id=? LIMIT ?''',(page_id,max_found+1)).fetchall()
    return [(int(r['target_id']),str(r['title']).replace('_',' ')) for r in rows[:max_found]]


def bounded_members(source, target_id, size_limit, take, kind):
    """Never enumerate an oversized category, never full-table scan."""
    rows = source.execute('''SELECT c.source_page_id,c.type,p.page_id,p.ns,p.title,p.redirect,p.latest_revision,p.content_bytes
       FROM wiki_categorylink_ids c INDEXED BY idx_wiki_catid_target
       LEFT JOIN wiki_pages p ON p.page_id=c.source_page_id
       WHERE c.target_id=? ORDER BY c.rowid LIMIT ?''',(target_id,size_limit+1)).fetchall()
    if len(rows) > size_limit:
        return [], True
    chosen = []
    for r in rows:
        if r['page_id'] is None or int(r['redirect'] or 0):
            continue
        if (kind == 'page' and int(r['ns']) == 0) or (kind == 'subcat' and int(r['ns']) == 14 and str(r['type']).lower()=='subcat'):
            chosen.append(r)
            if len(chosen) >= take:
                break
    return chosen, False


def reviewed_roots(cat, bid):
    found = defaultdict(set)
    if cat.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='reviewed_bridges_v26'").fetchone():
        for row in cat.execute('SELECT concept_id,category_title FROM reviewed_bridges_v26 WHERE branch_id=?', (bid,)):
            found[row['concept_id']].add(v25.normalize(row['category_title']))
    return found


def page_lookup(source, title):
    r = v25.source_page(source, title)
    if r is None or int(r['redirect']) or int(r['ns']) != 0:
        return None
    return r


def collect_seed(source, cat, ix, xml_file, seed, branch, caps, labels, roots):
    pid = int(seed['page_id'])
    # The SQL-derived catalogue may store a different revision from the XML
    # dump. V27 already permits this and records both revisions in its packs.
    # v27.page_from_index independently verifies XML against the v21 offset
    # index, page ID, title and content; never waive that integrity check.
    raw, revision, title = v27.page_from_index(ix, xml_file, pid)
    concepts = concepts_for_page(cat, branch['id'], pid)
    # Map: (concept, page) => a bounded set of independent evidence triples.
    discovered = defaultdict(set)
    page_info = {}
    link_titles = parse_wikilinks(raw.decode('utf-8'), caps.max_links_per_seed)
    for linked in link_titles:
        p = page_lookup(source, linked)
        if p is None or int(p['page_id']) == pid:
            continue
        target_id = int(p['page_id'])
        page_info[target_id] = p
        for cid, _ in concepts:
            discovered[(cid,target_id)].add(('WIKILINK', '[[%s]]' % linked))
    original_cats = category_labels(source,pid, caps.max_seed_categories)
    for cid,_ in concepts:
        concept_en = labels[cid]
        qualified = [(tid,name) for tid,name in original_cats
                     if v25.topic_category(name) and
                     (v25.normalize(name) in roots[cid] or title_word_match(name,concept_en)>0)]
        for target_id, name in qualified[:caps.max_categories_per_concept]:
            members, oversized = bounded_members(source,target_id,caps.max_category_size,
                                                   caps.max_neighbors_per_category,'page')
            if not oversized:
                for p in members:
                    target = int(p['page_id'])
                    if target != pid:
                        page_info[target] = p
                        discovered[(cid,target)].add(('SHARED_CATEGORY','Category:'+name))
            if caps.max_subcategories == 0:
                continue
            subcats, too_large = bounded_members(source,target_id,caps.max_category_size,
                                                 caps.max_subcategories,'subcat')
            if too_large:
                continue
            for sub in subcats:
                sub_name = str(sub['title']).replace('_',' ')
                if not v25.topic_category(sub_name) or title_word_match(sub_name,concept_en)==0:
                    continue
                subtarget = v25.cat_target(source,sub_name)
                if subtarget is None:
                    continue
                for p in bounded_members(source,subtarget,caps.max_category_size,
                                          caps.max_neighbors_per_category,'page')[0]:
                    target=int(p['page_id'])
                    if target != pid:
                        page_info[target]=p
                        discovered[(cid,target)].add(('SUBCATEGORY','Category:'+name+' > Category:'+sub_name))
    # Exclude current (page,concept) assignments, but allow a known article to gain a new concept.
    current = {(cid,pid) for cid,_ in concepts}
    edges = [(cid, target, page_info[target], kind, detail)
             for (cid,target), evs in sorted(discovered.items()) if (cid,target) not in current
             for kind,detail in sorted(evs)]
    return edges, revision, title


def discover(args):
    branch=v25.load_branch(args.branch)
    source,cat,source_sha=checked_source(args.source_db,args.catalogue_db,branch)
    ix=None
    work=None
    try:
        validated_cat,ix,src_info = v27.validated_sources(args.catalogue_db,args.index,args.xml)
        validated_cat.close()
    except BaseException:
        source.close();cat.close()
        raise
    return _discover_body(args,branch,source,cat,source_sha,ix,src_info)


def _discover_body(args,branch,source,cat,source_sha,ix,src_info):
    work=None
    try:
        if v25.meta(cat,'source_sha') != src_info['catalog_source_sha']:
            raise Refusal('Origine catalogue v25 differente de l index v27')
        workpath=args.work/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        v27.check_private_work(args.work,(args.source_db,args.catalogue_db,args.xml,args.index))
        work=open_work(workpath)
        bind_work(work,source_sha,src_info['xml_signature'],branch)
        seq=int(v25.meta(cat,'sequence'))
        added=sync_seeds(cat,work,branch['id'],seq)
        labels={c['unesco_id']:v25.label(c,'en') for c in branch['concepts']}
        roots=reviewed_roots(cat,branch['id'])
        processed=0;new_evidence=0;revision_mismatches_this_run=0
        with args.xml.open('rb') as xml_file:
            for _ in range(args.max_seeds):
                seed=work.execute("SELECT * FROM seed_queue WHERE branch_id=? AND state='PENDING' ORDER BY page_id LIMIT 1",
                                  (branch['id'],)).fetchone()
                if seed is None:
                    break
                edges,xml_revision,xml_title=collect_seed(source,cat,ix,xml_file,seed,branch,args,labels,roots)
                mismatch=(str(xml_revision)!=str(seed['revision']))
                with work:
                    # Keep the exact provenance of the text used for link
                    # discovery, even if SQL and XML snapshots are not aligned.
                    # Update the audit and seed state in the SAME transaction.
                    if mismatch:
                        work.execute('''INSERT INTO seed_revision_mismatches
                            (branch_id,page_id,catalogue_revision,xml_revision,xml_title,observed_utc)
                            VALUES(?,?,?,?,?,?)
                            ON CONFLICT(branch_id,page_id) DO UPDATE SET
                              catalogue_revision=excluded.catalogue_revision,
                              xml_revision=excluded.xml_revision,
                              xml_title=excluded.xml_title,observed_utc=excluded.observed_utc''',
                            (branch['id'],int(seed['page_id']),str(seed['revision']),
                             str(xml_revision),str(xml_title),now()))
                    else:
                        work.execute('DELETE FROM seed_revision_mismatches WHERE branch_id=? AND page_id=?',
                                     (branch['id'],int(seed['page_id'])))
                    for cid,pid,p,kind,detail in edges:
                        work.execute('INSERT OR IGNORE INTO candidates VALUES(?,?,?,?,?,?)',
                                     (branch['id'],cid,pid,str(p['title']).replace('_',' '),
                                      str(p['latest_revision'] or ''),now()))
                        new_evidence+=work.execute('INSERT OR IGNORE INTO evidence VALUES(?,?,?,?,?,?)',
                                      (branch['id'],cid,pid,int(seed['page_id']),kind,detail)).rowcount
                    work.execute("UPDATE seed_queue SET state='DONE',processed_utc=? WHERE branch_id=? AND page_id=?",
                                 (now(),branch['id'],int(seed['page_id'])))
                processed+=1
                revision_mismatches_this_run+=int(mismatch)
                if processed%100==0:
                    print(json.dumps({'event':'V28_DISCOVERY_PROGRESS','seeds_done_this_run':processed,
                                      'new_evidence':new_evidence},ensure_ascii=False),flush=True)
        pending=work.execute("SELECT count(*) FROM seed_queue WHERE branch_id=? AND state='PENDING'",(branch['id'],)).fetchone()[0]
        candidates=work.execute('SELECT count(*) FROM candidates WHERE branch_id=?',(branch['id'],)).fetchone()[0]
        mismatches=work.execute('SELECT count(*) FROM seed_revision_mismatches WHERE branch_id=?',
                                (branch['id'],)).fetchone()[0]
        return {'status':'V28_DISCOVERY_OK','branch_id':branch['id'],'catalog_sequence':seq,
                'seed_queue_new_or_changed':added,'seeds_processed_this_run':processed,
                'seeds_pending':pending,'candidate_pairs':candidates,'new_evidence':new_evidence,
                'revision_mismatches_this_run':revision_mismatches_this_run,
                'revision_mismatches_recorded':mismatches,
                'source_sql_read_only':True,'source_xml_read_only':True,'catalogue_modified':False,
                'canonical_admissions':0}
    finally:
        if work:work.close()
        ix.close(); cat.close();source.close()


def priority(row, label):
    seeds=int(row['seed_count'])
    links=int(row['links']); shared=int(row['shared']); subs=int(row['subs'])
    score=40+ min(20, 6*max(0,seeds-1))+min(12, 4*links)+min(12,6*shared)+min(8,4*subs)
    return min(90,score+min(15,5*title_word_match(row['title'],label)))


def build_candidate(work, r, label):
    evidence=list(work.execute('SELECT seed_page_id,kind,detail FROM evidence WHERE branch_id=? AND concept_id=? AND page_id=? '
                               'ORDER BY seed_page_id,kind,detail',(r['branch_id'],r['concept_id'],r['page_id'])))
    if not evidence:
        return None
    examples=[]
    counts=Counter(x['kind'] for x in evidence)
    for e in evidence[:6]:
        seed=work.execute('SELECT title FROM seed_queue WHERE branch_id=? AND page_id=?',
                          (r['branch_id'],int(e['seed_page_id']))).fetchone()
        source_title=(seed['title'] if seed else str(e['seed_page_id']))
        examples.append(source_title+' ['+str(e['seed_page_id'])+']:'+e['kind']+':'+e['detail'])
    seed_count=len(set(int(e['seed_page_id']) for e in evidence))
    detail_sha=digest(jbytes([list(x) for x in evidence]))
    row={'candidate_id':candidate_id(r['branch_id'],r['concept_id'],int(r['page_id'])),
         'branch_id':r['branch_id'],'concept_id':r['concept_id'],'concept_en':label,
         'page_id':int(r['page_id']),'title':r['title'],
         'seed_count':seed_count,'links':counts['WIKILINK'],'shared':counts['SHARED_CATEGORY'],
         'subs':counts['SUBCATEGORY'],'evidence_sha256':detail_sha,'examples':' | '.join(examples)}
    row['priority']=priority(row,label)
    return row


def rank_key(row):
    # Higher is better; smaller page id and concept id break ties deterministically.
    return (row['priority'],row['seed_count'],row['links']+row['shared']+row['subs'],
            -row['page_id'],row['concept_id'])


def candidate_rows(work, branch, cap, exclude=None):
    labels={c['unesco_id']:v25.label(c,'en') for c in branch['concepts']}
    best=[];total=0
    # Aggregate metadata once in SQLite, using the small v28 staging database.
    # Only the highest-ranked candidates need SHA-256 evidence and readable examples.
    query='''SELECT c.branch_id,c.concept_id,c.page_id,c.title,
             COUNT(DISTINCT e.seed_page_id) seed_count,
             SUM(CASE WHEN e.kind='WIKILINK' THEN 1 ELSE 0 END) links,
             SUM(CASE WHEN e.kind='SHARED_CATEGORY' THEN 1 ELSE 0 END) shared,
             SUM(CASE WHEN e.kind='SUBCATEGORY' THEN 1 ELSE 0 END) subs
             FROM candidates c JOIN evidence e ON e.branch_id=c.branch_id
                  AND e.concept_id=c.concept_id AND e.page_id=c.page_id
             WHERE c.branch_id=? GROUP BY c.branch_id,c.concept_id,c.page_id'''
    for r in work.execute(query,(branch['id'],)):
        item=dict(r)
        if item['concept_id'] not in labels:
            raise Refusal('Concept obsolete dans la base v28')
        item['priority']=priority(item,labels[item['concept_id']])
        if exclude is not None and exclude(item):continue
        total+=1
        key=rank_key(item)
        if len(best)<cap:
            heapq.heappush(best,(key,item))
        elif key>best[0][0]:
            heapq.heapreplace(best,(key,item))
    result=[]
    for _, item in sorted(best,key=lambda x:x[0],reverse=True):
        candidate=build_candidate(work,item,labels[item['concept_id']])
        if candidate is None or candidate['priority']!=item['priority']:
            raise Refusal('Preuves v28 incoherentes pendant export')
        result.append(candidate)
    return result,total


def export(args):
    branch=v25.load_branch(args.branch)
    workpath=args.work/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
    if not workpath.is_file():raise Refusal('Aucune decouverte v28 disponible; lancer Discover')
    work=v27.ro_sql(workpath)
    catalogue=v26.read_catalogue_ro(args.catalogue_db)
    try:
        if v25.meta(work,'schema')!=FORMAT or v25.meta(work,'branch_signature')!=branch['signature']:
            raise Refusal('Etat v28 incompatible avec la branche')
        if v25.meta(catalogue,'schema') != v25.SCHEMA:
            raise Refusal('Catalogue v25 incompatible durant l export')
        ledger_available=catalogue.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='reviewed_article_links_v28'").fetchone() is not None
        def already_classified_or_reviewed(item):
            key=(item['branch_id'],item['page_id'],item['concept_id'])
            if catalogue.execute("SELECT 1 FROM assignments WHERE branch_id=? AND wiki='enwiki' AND page_id=? AND concept_id=?",key).fetchone():
                return True
            if ledger_available:
                return catalogue.execute('SELECT 1 FROM reviewed_article_links_v28 WHERE branch_id=? AND page_id=? AND concept_id=?',key).fetchone() is not None
            return False
        rows,total=candidate_rows(work,branch,args.max_export,already_classified_or_reviewed)
        # Export all scored proposals within the explicit limit; no implicit approvals.
        csv_io=io.StringIO(newline='')
        writer=csv.DictWriter(csv_io,fieldnames=FIELDS,lineterminator='\n')
        writer.writeheader()
        for r in rows:
            writer.writerow({'candidate_id':r['candidate_id'],'branch_id':r['branch_id'],
                            'concept_id':r['concept_id'],'concept_en':r['concept_en'],
                            'page_id':r['page_id'],'title':r['title'],'priority':r['priority'],
                            'seed_count':r['seed_count'],'link_evidence':r['links'],
                            'category_evidence':r['shared'],'subcategory_evidence':r['subs'],
                            'evidence_sha256':r['evidence_sha256'],'examples':r['examples'],
                            'decision':'HOLD','justification':''})
        csv_raw=('\ufeff'+csv_io.getvalue()).encode('utf-8')
        report={'format':REVIEW_FORMAT,'branch_id':branch['id'],'catalogue_sequence_at_sync':v25.meta(work,'catalogue_sequence'),
                'proposals_total':total,'exported':len(rows),'more_proposals_not_exported':max(0,total-len(rows)),
                'decisions_default':'HOLD','review_before_apply':True,'canonical_admissions':0,
                'source_sql_unmodified':True,'catalogue_modified':False}
        instructions=('REVUE V28 — candidats de routage documentaire, pas des faits canoniques.\n'
                      'Pour chaque ligne: decision = APPROVE, HOLD ou REJECT.\n'
                      'APPROVE exige une justification explicite (>= 20 caracteres).\n'
                      'Ne changez ni les identifiants, ni les empreintes de preuve.\n'
                      'Renvoie ce ZIP/CSV pour revue IA avant import.\n'
                      'Les articles complets restent dans le XML local ; ce ZIP ne contient que des candidats.\n')
        args.work.mkdir(parents=True,exist_ok=True)
        folder=args.work/'exports'
        folder.mkdir(parents=True,exist_ok=True)
        filename=f'REVUE_ARTICLES_RELIES_V28_s{str(v25.meta(work,"catalogue_sequence") or "0").zfill(10)}_top{len(rows)}.csv'
        csv_path=folder/filename
        if csv_path.exists() and csv_path.read_bytes()!=csv_raw:
            # No overwrite of an older review with same name, potentially already in progress.
            filename=filename.replace('.csv','_'+digest(csv_raw)[:12]+'.csv')
            csv_path=folder/filename
        csv_path.write_bytes(csv_raw)
        zip_path=folder/f'EXPORT_V28_POUR_CHATGPT_{digest(csv_raw)[:16]}.zip'
        contents={filename:csv_raw,'RAPPORT_V28.json':jbytes(report),'INSTRUCTIONS_REVUE_V28.txt':instructions.encode('utf-8')}
        manifest={'format':REVIEW_FORMAT,'sha256':{k:digest(v) for k,v in contents.items()}}
        contents['MANIFEST_SHA256_V28.json']=jbytes(manifest)
        if zip_path.exists():
            with zipfile.ZipFile(zip_path) as z:
                if set(z.namelist())!=set(contents) or any(z.read(k)!=v for k,v in contents.items()):
                    raise Refusal('Export existant incompatible: '+str(zip_path))
        else:
            tmp=zip_path.with_suffix('.partial')
            if tmp.exists():tmp.unlink()
            with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
                for name,data in contents.items():z.writestr(name,data)
            os.replace(tmp,zip_path)
        return {'status':'V28_EXPORT_OK','candidate_pairs_total':total,'exported':len(rows),
                'csv':str(csv_path),'export_for_chatgpt':str(zip_path),'sha256':digest(csv_raw),
                'canonical_admissions':0,'catalogue_modified':False}
    finally:
        catalogue.close()
        work.close()


def read_decisions(path):
    if not path.is_file() or path.is_symlink():raise Refusal('CSV de decisions absent')
    raw=path.read_bytes()
    if len(raw)>100_000_000:raise Refusal('CSV de decisions trop volumineux')
    with io.StringIO(raw.decode('utf-8-sig'),newline='') as stream:
        reader=csv.DictReader(stream)
        if not set(FIELDS)<=set(reader.fieldnames or []):raise Refusal('Colonnes CSV v28 manquantes')
        result=[]; seen=set()
        for row in reader:
            key=row['candidate_id'].strip()
            if key in seen:raise Refusal('Candidat duplique dans le CSV: '+key)
            seen.add(key)
            decision=row['decision'].strip().upper()
            if decision not in ('APPROVE','HOLD','REJECT'):
                raise Refusal('Decision inconnue pour '+key)
            reason=row['justification'].strip()
            if decision=='APPROVE' and len(reason)<20:
                raise Refusal('Justification insuffisante pour '+key)
            try:pid=int(row['page_id'])
            except ValueError as ex:raise Refusal('Page invalide pour '+key) from ex
            result.append({'candidate_id':key,'branch_id':row['branch_id'],
                           'concept_id':row['concept_id'],'page_id':pid,'title':row['title'],
                           'evidence_sha256':row['evidence_sha256'],'decision':decision,
                           'justification':reason})
    if not result:raise Refusal('CSV de decisions sans ligne')
    return result,digest(raw)


def apply(args):
    branch=v25.load_branch(args.branch)
    if not args.decisions:raise Refusal('Apply exige -DecisionsFile')
    decisions,decisions_sha=read_decisions(args.decisions)
    if not args.catalogue_db.is_file():raise Refusal('Catalogue original absent')
    staging=args.work/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
    if not staging.is_file():raise Refusal('Decouverte v28 absente; impossible de verifier les preuves')
    work=v27.ro_sql(staging)
    source,cat,source_sha=checked_source(args.source_db,args.catalogue_db,branch)
    try:
        if (v25.meta(work,'schema')!=FORMAT or v25.meta(work,'source_sha')!=source_sha or
            v25.meta(work,'branch_signature')!=branch['signature']):
            raise Refusal('Propositions v28 creees avec une source ou branche differente')
        labels={c['unesco_id']:v25.label(c,'en') for c in branch['concepts']}
        planned=[]
        for row in decisions:
            candidate=work.execute('SELECT * FROM candidates WHERE branch_id=? AND concept_id=? AND page_id=?',
                                   (row['branch_id'],row['concept_id'],row['page_id'])).fetchone()
            existing=(build_candidate(work,candidate,labels[candidate['concept_id']])
                      if candidate and candidate['concept_id'] in labels else None)
            if not existing or any((row[k]!=existing[k] for k in ('candidate_id','branch_id','concept_id','page_id','title','evidence_sha256'))):
                raise Refusal('Candidat absent ou preuves modifiees; refaire export: '+row['candidate_id'])
            if row['decision']=='APPROVE':
                p=source.execute('SELECT page_id,ns,title,redirect,latest_revision,content_bytes FROM wiki_pages WHERE page_id=?',
                                 (row['page_id'],)).fetchone()
                if not p or int(p['ns'])!=0 or int(p['redirect']):
                    raise Refusal('Page approuvee absente/redirect: '+row['candidate_id'])
                if str(p['title']).replace('_',' ') != row['title']:
                    raise Refusal('Titre source change: '+row['candidate_id'])
                planned.append((row,p,existing))
        if len(decisions)>20000:raise Refusal('Importer au plus 20 000 decisions par execution')
        if args.dry_run:
            return {'status':'V28_APPLY_PREFLIGHT_OK','decisions':len(decisions),
                    'approved':len(planned),'catalogue_modified':False,'canonical_admissions':0}
    finally:
        cat.close();source.close();work.close()
    # Reverify metadata from writable catalog before altering any data.
    db=v25.open_catalog(args.catalogue_db)
    try:
        v26.verify_catalogue(db,branch,source_sha)
        baseline=db.execute('SELECT count(*) FROM articles').fetchone()[0]
        actionable=sum(r['decision']!='HOLD' for r in decisions)
        if not actionable:
            return {'status':'V28_APPLY_NO_ACTION','decisions':len(decisions),
                    'articles_after':baseline,'catalogue_modified':False,'canonical_admissions':0}
        approved=0;new_articles=0;new_assignments=0;seen_decisions=0
        db.execute('BEGIN IMMEDIATE')
        try:
            db.execute('''CREATE TABLE IF NOT EXISTS reviewed_article_links_v28(
                branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,page_id INTEGER NOT NULL,
                candidate_id TEXT NOT NULL,evidence_sha256 TEXT NOT NULL,decision TEXT NOT NULL,
                reason TEXT NOT NULL,import_sha256 TEXT NOT NULL,imported_utc TEXT NOT NULL,
                PRIMARY KEY(branch_id,concept_id,page_id))''')
            planned_index={r['candidate_id']:(r,p,score) for r,p,score in planned}
            for row in decisions:
                if row['decision']=='HOLD':
                    continue  # HOLD is provisional, never frozen in the editorial ledger.
                key=(row['branch_id'],row['concept_id'],row['page_id'])
                prior=db.execute('SELECT decision,reason,evidence_sha256 FROM reviewed_article_links_v28 WHERE branch_id=? AND concept_id=? AND page_id=?',key).fetchone()
                if prior:
                    if tuple(prior)!=(row['decision'],row['justification'],row['evidence_sha256']):
                        raise Refusal('Une decision deja importee a change: '+row['candidate_id'])
                    seen_decisions+=1
                    continue
                db.execute('INSERT INTO reviewed_article_links_v28 VALUES(?,?,?,?,?,?,?,?,?)',
                           (*key,row['candidate_id'],row['evidence_sha256'],row['decision'],
                            row['justification'],decisions_sha,now()))
                if row['decision']=='APPROVE':
                    _,p,proposal=planned_index[row['candidate_id']]
                    exists=db.execute("SELECT 1 FROM articles WHERE wiki='enwiki' AND page_id=?",(row['page_id'],)).fetchone()
                    assigned=db.execute("SELECT 1 FROM assignments WHERE branch_id=? AND wiki='enwiki' AND page_id=? AND concept_id=?",key).fetchone()
                    # Explicit review only; do not count discovery as additional corroboration.
                    v25.associate(db,branch['id'],branch['vocab'],row['concept_id'],p,
                                  max(35,min(80,proposal['priority'])),'V28_REVIEWED_LINK_CANDIDATE',
                                  'V28:'+row['candidate_id'],'')
                    approved+=1
                    new_articles+=0 if exists else 1
                    new_assignments+=0 if assigned else 1
            if actionable>seen_decisions:
                db.execute('INSERT INTO audit_events(branch_id,kind,description,created_utc) VALUES(?,?,?,?)',
                           (branch['id'],'V28_REVIEWED_LINKS',json.dumps({'decisions_sha256':decisions_sha,
                            'reviewed':actionable-seen_decisions,'approved':approved,'new_articles':new_articles,
                            'new_assignments':new_assignments}),now()))
                v25.tick(db)
            db.commit()
        except BaseException:
            db.rollback();raise
        after=db.execute('SELECT count(*) FROM articles').fetchone()[0]
        if after < baseline:
            raise Refusal('Regression du nombre d articles')
        snap=v25.snapshot(db,args.catalogue_db,args.catalogue_output,args.sample_limit)
        return {'status':'V28_APPLY_OK','decisions':len(decisions),'already_reviewed':seen_decisions,
                'new_approvals':approved,'new_articles':new_articles,'new_assignments':new_assignments,
                'articles_before':baseline,'articles_after':after,'catalogue_sequence':int(v25.meta(db,'sequence')),
                'v25_snapshot':snap['status'],'v27_discovers_new_articles_on_next_Packs':True,
                'canonical_admissions':0,'publication_authorized':False}
    finally:db.close()


def status(args):
    path=args.work/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
    if not path.exists():raise Refusal('Etat v28 absent; lancer Discover')
    db=v27.ro_sql(path)
    try:
        if v25.meta(db,'schema')!=FORMAT:raise Refusal('Base v28 incompatible')
        bid=v25.meta(db,'branch_id')
        q={r['state']:r['n'] for r in db.execute('SELECT state,count(*) n FROM seed_queue WHERE branch_id=? GROUP BY state',(bid,))}
        # The audit table is created automatically on the next Discover.
        # Status remains compatible with an existing pre-correction workspace.
        has_audit=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='seed_revision_mismatches'").fetchone()
        mismatch_count=(db.execute('SELECT count(*) FROM seed_revision_mismatches WHERE branch_id=?',
                                   (bid,)).fetchone()[0] if has_audit else 0)
        mismatch_examples=([{'page_id':r['page_id'],'catalogue_revision':r['catalogue_revision'],
                             'xml_revision':r['xml_revision']}
                            for r in db.execute('SELECT page_id,catalogue_revision,xml_revision '
                                                'FROM seed_revision_mismatches WHERE branch_id=? '
                                                'ORDER BY page_id LIMIT 10',(bid,))] if has_audit else [])
        return {'status':'V28_STATUS_OK','branch_id':bid,'seeds':q,
                'candidate_pairs':db.execute('SELECT count(*) FROM candidates WHERE branch_id=?',(bid,)).fetchone()[0],
                'evidence_count':db.execute('SELECT count(*) FROM evidence WHERE branch_id=?',(bid,)).fetchone()[0],
                'revision_mismatches_recorded':mismatch_count,
                'revision_mismatch_examples':mismatch_examples,
                'catalogue_sequence_at_last_sync':v25.meta(db,'catalogue_sequence'),
                'catalogue_modified':False,'canonical_admissions':0}
    finally:db.close()


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action',choices=('preflight','discover','export','apply','status'))
    ap.add_argument('--source-db',type=Path,default=v25.DEFAULT_SOURCE)
    ap.add_argument('--catalogue-db',type=Path,default=v25.DEFAULT_CATALOG)
    ap.add_argument('--index',type=Path,default=v27.DEFAULT_INDEX)
    ap.add_argument('--xml',type=Path,default=v27.DEFAULT_XML)
    ap.add_argument('--branch',type=Path,default=v25.DEFAULT_BRANCH)
    ap.add_argument('--work',type=Path,default=DEFAULT_WORK)
    ap.add_argument('--catalogue-output',type=Path,default=v25.DEFAULT_OUTPUT)
    ap.add_argument('--max-seeds',type=int,default=1000)
    ap.add_argument('--max-links-per-seed',type=int,default=160)
    ap.add_argument('--max-seed-categories',type=int,default=35)
    ap.add_argument('--max-categories-per-concept',type=int,default=3)
    ap.add_argument('--max-category-size',type=int,default=250)
    ap.add_argument('--max-neighbors-per-category',type=int,default=45)
    ap.add_argument('--max-subcategories',type=int,default=3)
    ap.add_argument('--max-export',type=int,default=1500)
    ap.add_argument('--sample-limit',type=int,default=300)
    ap.add_argument('--decisions',type=Path)
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args(argv)
    bounds=((1<=args.max_seeds<=25000),(2<=args.max_links_per_seed<=2000),
            (0<=args.max_seed_categories<=100),(0<=args.max_categories_per_concept<=15),
            (20<=args.max_category_size<=10000),(1<=args.max_neighbors_per_category<=500),
            (0<=args.max_subcategories<=15),(1<=args.max_export<=20000),
            (10<=args.sample_limit<=10000))
    if not all(bounds):raise Refusal('Parametres v28 hors limites')
    if args.action=='status':result=status(args)
    elif args.action=='export':result=export(args)
    elif args.action=='apply':result=apply(args)
    else:
        branch=v25.load_branch(args.branch)
        src,cat,source_sha=checked_source(args.source_db,args.catalogue_db,branch)
        src.close();cat.close()
        # Check v21 index and XML signature; never read full dump.
        c,ix,info=v27.validated_sources(args.catalogue_db,args.index,args.xml)
        c.close();ix.close()
        if args.action=='preflight':
            result={'status':'V28_PREFLIGHT_OK','branch_id':branch['id'],
                    'source_sha256':source_sha,'xml_signature':info['xml_signature'],
                    'catalogue_modified':False,'canonical_admissions':0}
        else:
            result=discover(args)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (Refusal,v25.Refusal,v27.Refusal,sqlite3.Error,OSError,ValueError,KeyError,TypeError,UnicodeError) as e:
        print(json.dumps({'status':'V28_REFUS','reason':str(e)},ensure_ascii=False),file=sys.stderr)
        sys.exit(2)
