"""E3.1/E3.2 : lecture bornée de métadonnées, sans nouvelle base ni réseau."""
from __future__ import annotations
from contextlib import closing, contextmanager
from pathlib import Path
import importlib.util, json, re, shutil, sqlite3, time

DIK_ROOT = Path(r'D:\diK\lexical\collection-v57')
V8_ROOT = Path(r'D:\ENCYK_V8_88_BRANCHES')
LANGUAGES = ('fr','en','es','it','fi','de','af','da','et','nl','nn','no','pt','sv')
PROFILE = 'dik.local-lexical-library/5.7-candidate'

def small_json(path):
    with Path(path).open('rb') as f:
        raw = f.read(2*1024*1024+1)
    if len(raw)>2*1024*1024: raise ValueError('Rapport trop volumineux')
    doc=json.loads(raw.decode('utf-8-sig'))
    if not isinstance(doc,dict): raise ValueError('Objet JSON attendu')
    return doc

@contextmanager
def reader(path):
    path=Path(path)
    if not path.is_file(): raise FileNotFoundError(str(path))
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=1)) as c:
        c.execute('PRAGMA query_only=ON'); c.execute('BEGIN')
        deadline=time.monotonic()+3
        c.set_progress_handler(lambda: int(time.monotonic()>deadline),1000)
        yield c

def file_info(p):
    p=Path(p)
    try:
        if not p.is_file(): return {'path':str(p),'present':False}
        return {'path':str(p),'present':True,'bytes':p.stat().st_size}
    except OSError as e: return {'path':str(p),'present':False,'error':str(e)}

def lexical_inventory(data, dik=DIK_ROOT):
    data,dik=Path(data),Path(dik)
    out={'scope':'METADATA_READ_ONLY','publication_authorized':False,'languages':[], 'warnings':[]}
    idx=data/'30_working/lexical/harvester/index-v1'
    out['encyk_index']=file_info(idx/'lexical.sqlite3')
    try:
        m=small_json(idx/'latest.json')
        if (m.get('profile')!='encyklopedia.lexical-source-index/candidate-v1' or m.get('published') is not False or Path(m['database']).resolve()!=(idx/'lexical.sqlite3').resolve()): raise ValueError('Contrat EncyK inattendu')
        out['encyk_report']={k:m.get(k) for k in ('generated_at','number_of_source_files','number_of_observed_language_codes','totals','sources_by_status')}
    except (OSError,ValueError,KeyError,TypeError) as e: out['warnings'].append('Rapport EncyK : '+str(e))
    out['dik_manifest']=file_info(dik/'manifest.json')
    try:
        m=small_json(dik/'manifest.json')
        if m.get('profile')!=PROFILE or m.get('published_dictionaries')!=0 or not isinstance(m.get('languages'),dict): raise ValueError('Contrat diK inattendu')
        out['dik_generated_at']=m.get('generated_at');out['dik_declared_status']=m.get('status')
        for lang in LANGUAGES:
            d=m['languages'].get(lang)
            if not isinstance(d,dict): continue
            path=dik/(lang+'.sqlite3'); row={'language':lang,'file':file_info(path),'declared_status':d.get('status'),'state':'UNVERIFIED'}
            try:
                with reader(path) as c: meta=dict(c.execute('SELECT key,value FROM meta'))
                if meta.get('profile')!=PROFILE or meta.get('language')!=lang or meta.get('source_fingerprint')!=m.get('source_fingerprint') or not m.get('source_fingerprint') or meta.get('published')!='0': raise ValueError('Métadonnées diK incompatibles')
                obs=int(meta['rows_imported']); exp=int(meta['expected_rows']); status=meta['status']
                if obs<0 or exp<0 or obs>exp or (status=='COMPLETE' and obs!=exp): raise ValueError('Compteurs incohérents')
                row.update(observations=obs,expected=exp,status=status,state='METADATA_READ',manifest_matches=(d.get('observations')==obs and d.get('expected')==exp and d.get('status')==status))
            except (OSError,sqlite3.Error,ValueError,KeyError,TypeError) as e: row['error']=str(e)
            out['languages'].append(row)
        out['observations_metadata_total']=sum(x['observations'] for x in out['languages'] if x['state']=='METADATA_READ')
        out['languages_metadata_read']=sum(x['state']=='METADATA_READ' for x in out['languages'])
    except (OSError,ValueError,KeyError,TypeError) as e: out['warnings'].append('Collection diK : '+str(e))
    return out

def fast_inventory(data, health):
    data=Path(data); dump=health.get('dump',{}); sha=dump.get('sha1_recorded')
    out={'scope':'PRESENCE_ONLY','indexed_bzip2':importlib.util.find_spec('indexed_bzip2') is not None,'state':'UNVERIFIED','locations':[]}
    if not isinstance(sha,str) or not re.fullmatch('[a-fA-F0-9]{40}',sha): return out
    for directory in (data/'30_working/wikidata-fast'/('sha1-'+sha.lower()),data/'30_working/wikidata'):
        out['locations'].append({'directory':str(directory),'manifest':file_info(directory/'manifest.json'),'locator':file_info(directory/'qid-locator.bin'),'compression':file_info(directory/'compression.bz2blocks.pkl')})
    out['sidecars_present']=any(x['locator']['present'] and x['compression']['present'] for x in out['locations'])
    out['state']='PRESENT_NOT_VALIDATED' if out['sidecars_present'] else 'SIDECARS_NOT_FOUND'
    # Never load a pickle on inventory.
    from world import status, isolated_python
    runtime=isolated_python()
    out['isolated_runtime']=str(runtime) if runtime else None
    out['manifest_check']=status(data)
    if out['manifest_check']['state']=='MANIFEST_MATCHES_METADATA': out['state']='MANIFEST_MATCHES_METADATA'
    return out

def dashboard(data, dik, v8, health, tools):
    data=Path(data); v8=Path(v8)
    out={'scope':'METADATA_READ_ONLY','publication_authorized':False,'wikidata':health,'tools_present':sum(x['presence']=='PRESENT' for x in tools),'tools_total':len(tools),'lexical':lexical_inventory(data,dik),'fast_access':fast_inventory(data,health)}
    try: out['disk_free_bytes']=shutil.disk_usage(data).free
    except OSError: out['disk_free_bytes']=None
    try:
        branches=small_json(v8/'station/libelles_88_branches_unesco.json')
        # Number of declared entries, not number of active branches.
        labels=branches.get('labels')
        if not isinstance(labels,dict) or any(not re.fullmatch(r'unesco\.mt[1-7]\.[0-9]{2}',k) or not isinstance(v,str) or not v.strip() for k,v in labels.items()): raise ValueError('Contrat branches inattendu')
        out['branch_labels_declared']=len(labels)
    except (ValueError,OSError): out['branch_labels_declared']=None
    return out

def indexed_query(c, sql, params):
    plan=[str(r[3]).upper() for r in c.execute('EXPLAIN QUERY PLAN '+sql,params)]
    if not any('SEARCH' in line for line in plan) or any('SCAN' in line for line in plan): raise ValueError('Accès indexé absent : scan massif refusé')
    return c.execute(sql,params)

def lookup(compact,wid,languages=None):
    """Exact Q/P lookup; no implicit language fallback, no name_kind inference."""
    if not isinstance(wid,str) or not re.fullmatch(r'[QP][1-9][0-9]{0,17}',wid): raise ValueError('Identifiant exact Q/P attendu (ex. Q2, P31)')
    if languages is not None:
        if not languages or len(languages)>16 or len(set(languages))!=len(languages) or any(not re.fullmatch(r'[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*',s) or len(s)>40 for s in languages): raise ValueError('Codes exacts : 1 à 16 langues distinctes')
    out={'scope':'COMPACT_INDEX_READ_ONLY','source':str(compact),'external_id':wid,'publication_authorized':False,'fallback':False,'source_revision':None,'languages_requested':languages,'rows':[]}
    with reader(compact) as c:
        meta=dict(c.execute('SELECT key,value FROM meta'))
        if meta.get('schema_version')!='encyklopedia-wikidata-compact-index/v1': raise ValueError('Schéma compact incompatible')
        out['dump_file']=meta.get('dump_file');out['indexed_languages']=meta.get('languages');out['complete_declared']=meta.get('complete')=='1'
        cols={r[1] for r in c.execute('PRAGMA table_info(entity)')}
        required={'id','wid','kind','label_fr','label_en','label_mul','description_fr','description_en'}
        if not required<=cols: raise ValueError('Colonnes entity absentes')
        row=indexed_query(c,'SELECT id,wid,kind,label_fr,label_en,label_mul,description_fr,description_en FROM entity WHERE wid=?',(wid,)).fetchone()
        if row is None: out['state']='NOT_FOUND_IN_COMPACT';return out
        ident,actual,kind,*values=row
        if actual!=wid: raise ValueError('Identité incohérente')
        out['kind']=kind;out['state']='FOUND_IN_COMPACT';out['rows']=[{'language':lang,'label':label,'description':desc,'names':[]} for lang,label,desc in zip(('fr','en','mul'),values[:3],[*values[3:],None]) if (languages is None or lang in languages) and (label is not None or desc is not None)]
        by_lang={r['language']:r for r in out['rows']}
        sql='SELECT lang,name_kind,value FROM name WHERE entity_id=?';args=[ident]
        if languages is not None:
            sql+=' AND lang IN ('+','.join('?' for _ in languages)+')';args.extend(languages)
        # Do not sort or count massive tables. The bound is per entity.
        records=indexed_query(c,sql+' LIMIT 1001',args).fetchall()
        out['names_truncated']=len(records)>1000
        for lang,k,value in records[:1000]:
            if lang not in by_lang: by_lang[lang]={'language':lang,'label':None,'description':None,'names':[]};out['rows'].append(by_lang[lang])
            by_lang[lang]['names'].append({'name_kind':k,'value':value})
        out['rows'].sort(key=lambda r:r['language'])
        if languages is not None: out['not_observed_in_index']=[x for x in languages if x not in by_lang]
    return out
