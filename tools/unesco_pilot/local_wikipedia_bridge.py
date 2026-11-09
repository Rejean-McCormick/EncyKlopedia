"""Local, noncanonical UNESCO mt1.10 => Wikimedia EN inventory bridge.

Reads one operator-selected UNESCO pilot ZIP and existing Wikimedia SQL index.
No network. No dictionary synthesis, asserted exactMatch, article translation,
semantic state mutation, or GitHub publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
from urllib.parse import quote
from zipfile import ZipFile

PROFILE = 'encyklopedia.unesco-local-wikipedia-handoff/1.0'
LOCALES = ('en','fr','es','de','nl','sv','da','no','nn','fi','et','af','it','pt')
PREFIX = '01_CANDIDATE_WORKSPACE/unesco-mt1-10/'
SCOPE_FILE = PREFIX + 'derived/encyclopedia_scope.en.json'
CONCEPT_FILE = PREFIX + 'canon/domain/unesco-source.json'
MAPPING_FILE = PREFIX + 'derived/wikidata-p3916-candidates.json'
QID = re.compile(r'^Q[1-9][0-9]*$')
CONCEPT = re.compile(r'^concept[1-9][0-9]*$')


class PilotError(ValueError):
    """Safe, actionable preflight rejection."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extract_json(z: ZipFile, name: str) -> tuple[dict, bytes]:
    info = z.getinfo(name)
    if info.file_size > 4_000_000:
        raise PilotError(f'Pilot source exceeds 4 MB limit: {name}')
    data = z.read(name)
    obj = json.loads(data)
    if not isinstance(obj, dict):
        raise PilotError(f'Expected JSON object: {name}')
    return obj, data


def read_pilot_zip(path: Path):
    if not path.is_file():
        raise PilotError(f'Selected scope ZIP absent: {path}')
    with ZipFile(path) as z:
        s, sb = _extract_json(z, SCOPE_FILE)
        c, cb = _extract_json(z, CONCEPT_FILE)
        m, mb = _extract_json(z, MAPPING_FILE)
    grain = s.get('grain') or {}
    if not all(grain.get(k) is True for k in ('one_branch_kristal','no_one_kristal_per_concept','individual_articles_are_projections')):
        raise PilotError('The source does not declare one branch Kristal with article projections')
    if s.get('subject',{}).get('unesco_branch_slug')!='unesco-mt1-10' or s['subject'].get('expected_seed_count')!=41:
        raise PilotError('Pilot is not the expected UNESCO Educational Policy 41-concept scope')
    if s.get('source_sha256')!=sha256(cb):
        raise PilotError('Source bytes do not match the scope SHA-256')
    concepts=c.get('concepts'); mappings=m.get('mappings')
    if not isinstance(concepts,list) or len(concepts)!=41 or not isinstance(mappings,list) or len(mappings)!=41:
        raise PilotError('Exactly 41 source concepts and 41 mapping candidates are required')
    cids=[a.get('unesco_id') for a in concepts]
    if not all(isinstance(x,str) and CONCEPT.fullmatch(x) for x in cids) or len(set(cids))!=41:
        raise PilotError('Duplicate or malformed UNESCO concept identifiers')
    mapped={}
    for row in mappings:
        cid=row.get('unesco_id')
        if cid not in cids or cid in mapped:
            raise PilotError(f'Unexpected or repeated mapping for {cid!r}')
        qid=row.get('qid_candidate') or None
        if qid is not None and not QID.fullmatch(qid):
            raise PilotError(f'Invalid QID candidate for {cid}')
        if qid and row.get('status') != 'SINGLE_P3916_CANDIDATE':
            raise PilotError('Only explicit single P3916 candidates may be queried')
        mapped[cid]={'candidate_qid':qid,'mapping_status':row.get('status')}
    if len(mapped)!=41:
        raise PilotError('The QID candidate inventory is incomplete')
    return s,c,m,mapped, {'scope':sha256(sb),'unesco':sha256(cb),'candidate_mappings':sha256(mb)}


def _cols(conn,table):
    return {str(r[1]) for r in conn.execute(f'PRAGMA table_info({table})')}


def _one_of(cols,*names):
    for n in names:
        if n in cols: return n
    raise PilotError(f'Required SQLite column absent; expected one of {names}, got {sorted(cols)}')


def _sql_id(name):
    # Never interpolate unchecked external column names.
    if not re.fullmatch(r'[a-zA-Z_][a-zA-Z0-9_]*',name):
        raise PilotError('Malformed SQLite schema column')
    return '"'+name+'"'


def open_inventory(path: Path):
    if not path.is_file():
        raise PilotError(f'SQLite inventory not found: {path}')
    # immutable=1 avoids SQLite sidecars and guarantees no index mutation.
    # Only use on a fully finished index, not during concurrent import.
    uri=path.resolve().as_uri()+'?mode=ro&immutable=1'
    conn=sqlite3.connect(uri,uri=True,timeout=10)
    conn.execute('PRAGMA query_only=ON')
    qcols=_cols(conn,'wiki_qid'); pcols=_cols(conn,'wiki_pages')
    if not qcols or not pcols:
        conn.close()
        raise PilotError('Expected wiki_qid and wiki_pages tables not present')
    spec={
        'qid':_one_of(qcols,'qid','wikibase_item'),
        'qid_page':_one_of(qcols,'page_id','pp_page'),
        'page_id':_one_of(pcols,'page_id'),
        'title':_one_of(pcols,'title','page_title'),
        'ns':_one_of(pcols,'ns','namespace','page_namespace'),
        'revision':next((n for n in ('latest_rev','latest_revision','page_latest') if n in pcols),None),
        'redirect':next((n for n in ('is_redirect','page_is_redirect') if n in pcols),None),
    }
    return conn,spec


def query_wikipedia(conn,spec,qid):
    if not qid: return []
    cols=spec
    rev= f', p.{_sql_id(cols["revision"])}' if cols['revision'] else ''
    redirect=f', p.{_sql_id(cols["redirect"])}' if cols['redirect'] else ''
    q=f'''SELECT p.{_sql_id(cols['page_id'])},p.{_sql_id(cols['title'])}{rev}{redirect}
         FROM wiki_qid AS q JOIN wiki_pages AS p
           ON p.{_sql_id(cols['page_id'])}=q.{_sql_id(cols['qid_page'])}
         WHERE q.{_sql_id(cols['qid'])}=? AND p.{_sql_id(cols['ns'])}=0
         LIMIT 5'''
    rows=[]
    for r in conn.execute(q,(qid,)):
        page_id,title=r[:2]
        if isinstance(title,bytes):title=title.decode('utf8','replace')
        if not isinstance(title,str) or page_id is None:continue
        off=2
        revision=r[off] if cols['revision'] else None
        off+=int(bool(cols['revision']))
        is_redirect=bool(r[off]) if cols['redirect'] else None
        rows.append({'page_id':page_id,'title':title,'latest_revision_id':revision,
                     'redirect':is_redirect,'wiki_page_url':'https://en.wikipedia.org/wiki/'+quote(title.replace(' ','_'),safe='():,')})
    return rows


def build_manifest(scope_zip:Path, db_path:Path):
    s,c,m,mapped,hashes=read_pilot_zip(scope_zip)
    conn,spec=open_inventory(db_path)
    try:
        records=[]
        for entry in c['concepts']:
            concept_id=entry['unesco_id']; can=mapped[concept_id]
            labels=entry.get('preferred_labels',{})
            lexical={locale:{'unesco_terms':labels.get(locale,[]),
                              'label_status':'source_label_present' if labels.get(locale) else 'missing'} for locale in LOCALES}
            records.append({
                'unesco_id':concept_id,
                'unesco_uri':entry.get('source_uri'),
                'unesco_preferred_labels':labels,
                'skos':{k:entry.get(k,[]) for k in ('broader','narrower','related')},
                'wikidata':{'qid':can['candidate_qid'],'match_status':'unreviewed_candidate' if can['candidate_qid'] else 'none',
                            'source_mapping_status':can['mapping_status'],'canonical_exact_match':False},
                'wikipedia_en_inventory':query_wikipedia(conn,spec,can['candidate_qid']),
                'language_channels':lexical,
                'article_projection_status':'not_generated',
                'canonical_KQ':None,'canonical_KA':[], 'canonical_KS':[],
                'editorial_review_status':'not_reviewed'
            })
    finally:conn.close()
    return {
       'profile':PROFILE,'branch':'unesco-mt1-10','semantic_grain':'one_branch_kristal',
       'not_canonical':True,'not_publication':True,'approval_status':'BLOCKED',
       'wiki_content_extracted':False,'wikidata_mapping_approval':False,
       'article_count':0,'target_projection_count':41*len(LOCALES),
       'languages':list(LOCALES),'records':records,
       'input_checksums_sha256':hashes,
       'wikipedia_source':'local_sqlite_metadata_only',
       'licensing_note':'UNESCO Thesaurus license attribution is separate from Wikimedia article text; no article text redistributed.',
    }


def atomic_json_write(destination:Path, obj):
    destination=destination.resolve()
    for ancestor in (destination.parent,*destination.parents):
        if (ancestor/'.git').exists():
            raise PilotError('Output inside a Git checkout refused. Choose a private working folder outside Git.')
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.exists():
        raise PilotError('Output exists; choose a new filename (no overwrites)')
    fd,name=tempfile.mkstemp(prefix='.unesco_pilot_',suffix='.tmp',dir=destination.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as w:
            json.dump(obj,w,ensure_ascii=False,sort_keys=True,indent=2)
            w.write('\n');w.flush();os.fsync(w.fileno())
        # Avoid racing an old output file. Unique filenames recommended.
        if destination.exists(): raise PilotError('Output appeared during build')
        os.replace(name,destination)
    finally:
        if os.path.exists(name):os.unlink(name)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['plan','build'])
    parser.add_argument('--scope-zip',required=True,type=Path,help='Explicit UNESCO Educational Policy pilot ZIP')
    parser.add_argument('--db',type=Path,default=Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite'))
    parser.add_argument('--out',type=Path,help='Private output JSON outside Git checkout (build only)')
    opts=parser.parse_args(argv)
    try:
        data=build_manifest(opts.scope_zip,opts.db)
        summary={'profile':PROFILE,'branch':data['branch'],'concepts':len(data['records']),
                 'qid_candidates':sum(bool(r['wikidata']['qid']) for r in data['records']),
                 'wikipedia_en_pages_found':sum(len(r['wikipedia_en_inventory']) for r in data['records']),
                 'requested_language_channels':len(LOCALES),'articles_generated':0,
                 'status':'PRIVATE_INVENTORY_ONLY_NO_PUBLICATION'}
        if opts.command=='build':
            if opts.out is None: raise PilotError('--out required for build')
            atomic_json_write(opts.out,data)
            summary['out']=str(opts.out.resolve())
        print(json.dumps(summary,ensure_ascii=False,sort_keys=True))
        return 0
    except (PilotError,sqlite3.Error,ValueError,KeyError) as exc:
        print(json.dumps({'error':str(exc),'status':'BLOCKED'},ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=='__main__':raise SystemExit(main())
