#!/usr/bin/env python3
"""Framework v11 draft.3 profile adapter, stdlib-only, strict, file-backed.

This is a conservative structural/integrity checker, not a substitute for the
Framework's authoritative JSON Schemas or a semantic truth qualification.
Existing v9/v10 profiles are unaffected unless enabled explicitly.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata

PROFILE='kristal.semantic-identity/11.0'
KIND={'KQ':'entity','KP':'property','KA':'assertion','KS':'source'}
ID=re.compile(r'^K(Q|P|A|S)[1-9][0-9]*$')
EXT=re.compile(r'^[QP][1-9][0-9]*$')
HEX=re.compile(r'^[0-9a-f]{64}$')
LANG=re.compile(r'^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$')
CONFIG='.kristal/v11/authoring.json'

class V11Error(ValueError):pass

def must(ok,message):
    if not ok:raise V11Error(message)

def read(p):
    return json.loads(Path(p).read_text(encoding='utf8'))

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def safe(root,rel,*,exists=True):
    must(isinstance(rel,str) and bool(rel),'invalid empty path')
    p=Path(rel)
    must(not p.is_absolute() and '..' not in p.parts and '\\' not in rel,'absolute or traversal path forbidden')
    base=Path(root).resolve(); path=(base/p).resolve()
    must(path.is_relative_to(base),'path escapes workspace via symlink')
    if exists:must(path.is_file(),f'missing expected file: {rel}')
    return path

def id_kind(s,kind):
    must(isinstance(s,str) and bool(ID.fullmatch(s)) and KIND[s[:2]]==kind, f'expected {kind} KQ/KP/KA/KS identifier, got {s!r}')

def registry_check(reg):
    must(reg.get('schema_version')=='11.0' and reg.get('artifact_type')=='kristal_identity_registry','bad v11 registry envelope')
    ns=reg.get('namespace_id');must(isinstance(ns,str) and ns,'registry namespace required')
    ids={}
    for e in reg.get('identities',[]):
        ident=e.get('id');kind=e.get('kind');id_kind(ident,kind)
        must(ident not in ids,'duplicate registry identity')
        must(e.get('status') in ('stable','provisional','deprecated'), 'invalid identity status')
        ids[ident]=kind
    must(bool(ids),'empty identity registry')
    return ns,ids

def graph_check(graph,namespace,ids):
    must(graph.get('schema_version')=='11.0' and graph.get('artifact_type')=='kristal_semantic_graph','bad graph envelope')
    must(graph.get('namespace_id')==namespace,'graph namespace mismatch')
    must(set(graph)=={'schema_version','artifact_type','namespace_id','graph_id','entities','properties','sources','assertions'},'unexpected field in canonical semantic graph (lexical labels are forbidden)')
    for field,kind in [('entities','entity'),('properties','property'),('sources','source')]:
        values=graph.get(field);must(isinstance(values,list) and len(values)==len(set(values)),f'bad or duplicate {field}')
        for value in values:id_kind(value,kind);must(ids.get(value)==kind,f'undeclared {field}: {value}')
    entities,properties,sources=map(lambda k:set(graph[k]),('entities','properties','sources'))
    def objcheck(obj):
        must(isinstance(obj,dict),'object must be an explicit typed value')
        if obj.get('kind')=='entity':
            must(set(obj)=={'kind','id'},'entity object shape error');id_kind(obj['id'],'entity');must(obj['id'] in entities,'undeclared graph target')
        elif obj.get('kind')=='literal':
            must(set(obj)<= {'kind','datatype','value','language'} and {'datatype','value'} <= set(obj),'literal shape error')
            datatype=obj['datatype']; value=obj['value']
            good={'string':lambda v:isinstance(v,str),'boolean':lambda v:isinstance(v,bool),
              'integer':lambda v:type(v)==int,'number':lambda v:type(v) in (int,float),
              'date':lambda v:isinstance(v,str),'dateTime':lambda v:isinstance(v,str),
              'uri':lambda v:isinstance(v,str)}
            must(datatype in good and good[datatype](value),'literal datatype/value mismatch')
            if 'language' in obj:
                must(datatype=='string' and bool(LANG.fullmatch(obj['language'])),'literal locale only allowed for strings')
        else:raise V11Error('object must be kind entity or literal')
    seen=set()
    for a in graph.get('assertions',[]):
        must(isinstance(a,dict) and {'id','subject','predicate','object','sources'}<=set(a),'bad assertion')
        must(set(a)<= {'id','subject','predicate','object','sources','qualifiers'},'unexpected assertion labels or fields')
        id_kind(a['id'],'assertion');must(ids.get(a['id'])=='assertion' and a['id'] not in seen,'undeclared/duplicate assertion')
        seen.add(a['id']);must(a['subject'] in entities and a['predicate'] in properties,'subject/predicate must be declared KQ/KP')
        objcheck(a['object'])
        must(isinstance(a['sources'],list) and all(s in sources for s in a['sources']),'source missing KS')
        for q in a.get('qualifiers',[]):
            must(set(q)=={'predicate','object'} and q['predicate'] in properties,'qualifier property missing KP')
            objcheck(q['object'])
    must(isinstance(graph.get('graph_id'),str) and graph['graph_id'],'missing graph_id')
    return entities,properties

def crosswalk_check(crosswalk,ns,ids):
    must(crosswalk.get('schema_version')=='11.0' and crosswalk.get('artifact_type')=='kristal_external_crosswalk','bad crosswalk envelope')
    active_local=set();active_external=set();external_to_local={};seen=set()
    for m in crosswalk.get('mappings',[]):
        mid=m.get('mapping_id');must(isinstance(mid,str) and mid not in seen,'duplicate/bad mapping_id');seen.add(mid)
        local=m['local_ref'];ext=m['external_ref'];kid=local['id'];eid=ext['id']
        must(local['namespace_id']==ns,'crosswalk namespace mismatch')
        must(kid in ids and ids[kid] in ('entity','property'),'crosswalk local KQ/KP unknown')
        must(ext.get('system')=='wikidata' and isinstance(eid,str) and EXT.fullmatch(eid),'only Wikidata Q/P permitted')
        must((kid.startswith('KQ') and eid.startswith('Q')) or (kid.startswith('KP') and eid.startswith('P')),'Q/KQ or P/KP kind mismatch')
        status=m.get('status');relation=m.get('relation')
        must(status in ('candidate','accepted','rejected','superseded') and relation in ('exactMatch','closeMatch','broadMatch','narrowMatch','relatedMatch'),'bad mapping relation/status')
        if status=='accepted':
            rev=m.get('review');must(isinstance(rev,dict) and rev.get('method') in ('human','audited_rule') and rev.get('decision_id'),'accepted mapping requires reviewed decision')
            evidence=rev.get('evidence_refs');must(isinstance(evidence,list) and bool(evidence) and all(ids.get(s)=='source' for s in evidence),'accepted mapping requires declared KS evidence')
        if status=='accepted' and relation=='exactMatch':
            must(kid not in active_local and eid not in active_external,'conflicting active exactMatch')
            active_local.add(kid);active_external.add(eid);external_to_local[eid]=kid
    return external_to_local

def _iter_layer(path,kind):
    if kind=='curated':
        d=read(path)
        must(d.get('schema_version')=='11.0' and d.get('artifact_type')=='kristal_curated_dictionary','invalid curated document')
        for e in d.get('entries',[]):yield e,d
    else:
        with path.open(encoding='utf8') as f:
            for n,line in enumerate(f,1):
                if not line.strip():continue
                try:entry=json.loads(line)
                except ValueError as exc:raise V11Error(f'invalid JSONL line {n} in {path.name}') from exc
                yield entry,None

def catalog_check(catalog_path,ns,ids,exact,needed=None):
    catalog=read(catalog_path)
    must(catalog.get('schema_version')=='11.0' and catalog.get('artifact_type')=='kristal_dictionary_catalog','bad lexical catalog')
    must(catalog.get('namespace_id')==ns,'catalog namespace mismatch')
    must(isinstance(catalog.get('catalog_id'),str) and catalog['catalog_id'],'catalog_id required')
    langs={}
    for loc in catalog.get('languages',[]):
        tag=loc.get('tag');must(isinstance(tag,str) and LANG.fullmatch(tag) and tag not in langs,'duplicate/invalid locale')
        langs[tag]=loc
    for tag,loc in langs.items():
        f=loc.get('fallbacks');must(isinstance(f,list) and len(f)==len(set(f)) and all(x in langs and x!=tag for x in f),'invalid/undeclared locale fallback')
    def walk(tag,path):
        must(tag not in path,'cyclic locale fallback');return [x for t in langs[tag]['fallbacks'] for x in [t]+walk(t,path+[tag])]
    for tag in langs:walk(tag,[])
    seen_by_loc={}
    for tag,loc in langs.items():
        keyterms={};layerids=set();pref={}
        for layer in loc.get('layers',[]):
            kind=layer.get('kind');must(kind in ('wikidata','external','curated'),'unknown dictionary kind')
            layerid=layer.get('layer_id');must(isinstance(layerid,str) and layerid not in layerids,'duplicate layer id');layerids.add(layerid)
            priority=layer.get('priority');must(type(priority)==int and priority>=0,'invalid layer priority')
            p=safe(catalog_path.parent,layer.get('path'))
            must(isinstance(layer.get('sha256'),str) and digest(p)==layer['sha256'],'dictionary digest mismatch')
            localids=set()
            for row,parent in _iter_layer(p,kind):
                kid=row.get('semantic_id');must(ids.get(kid) in ('entity','property'),'unknown dictionary KQ/KP')
                must(kid not in localids,'duplicate entry in one layer');localids.add(kid)
                term=row.get('preferred_term');must(isinstance(term,str) and term and unicodedata.is_normalized('NFC',term),'missing or non-NFC term')
                if kind=='curated':
                    must(parent['namespace_id']==ns and parent['language']==tag,'curated namespace/locale mismatch')
                    rev=row.get('review');must(isinstance(rev,dict) and all(rev.get(x) for x in ('decision_id','reviewer','reason')),'unreviewed curated label')
                elif kind=='wikidata':
                    must(row.get('namespace_id')==ns and row.get('language')==tag and row.get('source_snapshot')==layer.get('source_snapshot'),'Wikidata provenance mismatch')
                    must(exact.get(row.get('external_id'))==kid,'Wikidata label without accepted exact crosswalk')
                else:
                    must(row.get('namespace_id')==ns and row.get('language')==tag and all(row.get(x)==layer.get(x) for x in ('source_system','source_snapshot','license')),'external provenance mismatch')
                    must(row.get('source_record_id') and all(ids.get(s)=='source' for s in row.get('alignment',{}).get('evidence_refs',[])) and bool(row.get('alignment',{}).get('evidence_refs')),'external alignment evidence missing')
                if needed is not None and kid not in needed:continue
                k=(priority,kid)
                must(k not in keyterms or keyterms[k]==term,'conflicting equal-priority labels')
                keyterms[k]=term
                if kid not in pref or priority>pref[kid][0]:pref[kid]=(priority,term)
        seen_by_loc[tag]=pref
    return catalog,langs,seen_by_loc

def load_profile(root):
    root=Path(root).resolve();p=root/CONFIG
    if not p.is_file():return None
    config=read(p)
    must(config.get('format')=='kristal.authoring-v11-profile/1.0' and config.get('semantic_profile')==PROFILE,'unrecognized v11 authoring profile')
    must(set(config)=={'format','semantic_profile','registry','graph','crosswalk','catalog'},'unexpected v11 profile metadata')
    return config

def validate(root,config=None,*,require_registered=True):
    root=Path(root).resolve();_assert_no_pending(root);config=config if config is not None else load_profile(root)
    must(config is not None,'no enabled v11 semantic profile')
    files={k:safe(root,config[k]) for k in ('registry','graph','crosswalk','catalog')}
    if require_registered:
        idx=read(safe(root,'canon/state.index.json'))
        registered={x.get('path') for x in idx.get('canonical_artifacts',[]) if isinstance(x,dict)}
        must(all(files[k].relative_to(root).as_posix() in registered for k in files),'v11 registry/graph/crosswalk/catalog MUST be registered v9 Logical Artifacts')
    registry=read(files['registry']);ns,ids=registry_check(registry)
    graph=read(files['graph']);entities,properties=graph_check(graph,ns,ids)
    crosswalk=read(files['crosswalk']);exact=crosswalk_check(crosswalk,ns,ids)
    catalog,langs,terms=catalog_check(files['catalog'],ns,ids,exact,entities|properties)
    return {'namespace_id':ns,'graph_id':graph['graph_id'],'registry_ids':len(ids),
      'KQ':sorted(entities),'KP':sorted(properties),'catalog_id':catalog['catalog_id'],
      'languages':langs,'lexical_terms':terms,'files':files}

def coverage(root,config=None,locales=None):
    root=Path(root); data=validate(root,config)
    langs=data['languages']; selected=list(locales) if locales else list(langs)
    must(bool(selected) and len(set(selected))==len(selected),'selection must contain unique locales')
    must(all(tag in langs for tag in selected),'unknown/unregistered locale')
    rows=[];all_d={k:set(data[k]) for k in ('KQ','KP')};all_u={k:set(data[k]) for k in ('KQ','KP')}
    for tag in selected:
        direct=set(data['lexical_terms'][tag]); usable=set(direct)
        for fallback in langs[tag]['fallbacks']:usable|=set(data['lexical_terms'][fallback])
        row={'tag':tag}
        for kind in ('KQ','KP'):
            ids=set(data[kind]);d=ids&direct;f=ids&(usable-direct);m=ids-usable
            row[kind]={'total':len(ids),'direct':len(d),'fallback':len(f),'missing':len(m),
              'conflicted':0,'missing_ids_sample':sorted(m)[:25],'sample_truncated':len(m)>25}
            all_d[kind]&=d;all_u[kind]&=(d|f)
        row['complete_direct']=all(row[k]['total']==row[k]['direct'] for k in ('KQ','KP'))
        row['complete_usable']=all(row[k]['missing']==0 for k in ('KQ','KP'))
        rows.append(row)
    graph_path=data['files']['graph']; catalog_path=data['files']['catalog']
    sha_g=digest(graph_path);sha_c=digest(catalog_path)
    seed=json.dumps([data['graph_id'],sha_g,sha_c,selected],ensure_ascii=False,separators=(',',':'))
    return {'schema_version':'11.0','artifact_type':'kristal_dik_coverage_report',
      'report_id':'dik-coverage-'+hashlib.sha256(seed.encode()).hexdigest()[:20],
      'namespace_id':data['namespace_id'],'graph_id':data['graph_id'],'graph_sha256':sha_g,
      'catalog_id':data['catalog_id'],'catalog_sha256':sha_c,
      'semantic_reference_count':{k:len(data[k]) for k in ('KQ','KP')},'locales':rows,
      'all_locales':{key:{kind:len(v[kind]) for kind in ('KQ','KP')} for key,v in [('direct',all_d),('usable',all_u)]}}

def ptr_get(document,pointer):
    must(isinstance(pointer,str) and pointer.startswith('/'),'bad JSON pointer')
    current=document
    for t in pointer.split('/')[1:]:
        must('~' not in re.sub('~[01]','',t),'invalid JSON pointer escaping')
        t=t.replace('~1','/').replace('~0','~')
        if isinstance(current,dict):must(t in current,f'path {pointer} not found');current=current[t]
        elif isinstance(current,list):must(t.isdigit() and (len(t)<2 or not t.startswith('0')) and int(t)<len(current),f'invalid array index in {pointer}');current=current[int(t)]
        else:raise V11Error('pointer traverses non-container')
    return current

def ptr_set(document,pointer,value):
    parts=pointer.split('/')[1:];cur=document
    for t in parts[:-1]:
        t=t.replace('~1','/').replace('~0','~');cur=cur[int(t)] if isinstance(cur,list) else cur[t]
    last=parts[-1].replace('~1','/').replace('~0','~')
    if isinstance(cur,list):cur[int(last)]=value
    else:cur[last]=value

def semantic_path_role(source,pointer):
    """Allow only semantic slots of a v11-shaped draft; never free-text fields."""
    if not isinstance(source,dict) or source.get('schema_version')!='11.0' or source.get('artifact_type')!='kristal_semantic_graph':
        return None
    if re.fullmatch(r'/entities/(?:0|[1-9][0-9]*)', pointer):return 'entity'
    if re.fullmatch(r'/properties/(?:0|[1-9][0-9]*)', pointer):return 'property'
    if re.fullmatch(r'/assertions/(?:0|[1-9][0-9]*)/subject', pointer):return 'entity'
    if re.fullmatch(r'/assertions/(?:0|[1-9][0-9]*)/predicate', pointer):return 'property'
    if re.fullmatch(r'/assertions/(?:0|[1-9][0-9]*)/qualifiers/(?:0|[1-9][0-9]*)/predicate', pointer):return 'property'
    if re.fullmatch(r'/assertions/(?:0|[1-9][0-9]*)/(?:object|qualifiers/(?:0|[1-9][0-9]*)/object)/id', pointer):
        parent=pointer.rsplit('/',1)[0]
        return 'entity' if isinstance(ptr_get(source,parent),dict) and ptr_get(source,parent).get('kind')=='entity' else None
    return None

def plan_verify(plan,source_path,registry,roles=None,*,require_approved=True):
    must(plan.get('schema_version')=='11.0' and plan.get('artifact_type')=='kristal_dik_conversion_plan','bad diK plan')
    ns,ids=registry_check(registry);must(plan.get('namespace_id')==ns,'plan namespace mismatch')
    source=plan.get('source',{});must(HEX.fullmatch(source.get('sha256','')) and digest(source_path)==source['sha256'],'source hash changed from reviewed plan')
    must(source.get('artifact_id') and source.get('declared_version') and plan.get('plan_id') and plan.get('catalog_id') and plan.get('crosswalk_id'),'incomplete plan provenance')
    original=read(source_path);ops=plan.get('operations');must(isinstance(ops,list) and bool(ops),'empty migration plan')
    used=set();new=deepcopy(original)
    for op in ops:
        pointer=op.get('source_path');must(pointer not in used,'duplicate operation path');used.add(pointer)
        must(isinstance(op.get('operation_id'),str) and op['operation_id'],'missing operation ID')
        role=op.get('semantic_role');kid=op.get('target_id');must(ids.get(kid)==role and role in ('entity','property'),'migration KQ/KP kind mismatch')
        must(semantic_path_role(original,pointer)==role,'conversion path is not a typed semantic identity slot')
        must(roles is None or roles.get(pointer)==role,'conversion path not declared as identity role')
        must(ptr_get(original,pointer)==op.get('original_value') and isinstance(op.get('original_value'),str),'reviewed source value mismatch')
        decision=op.get('decision',{});status=decision.get('status')
        must(status in ('approved','pending','rejected'), 'unknown decision status')
        if status=='approved':
            must(all(decision.get(k) for k in ('decision_id','reviewer','reason')),'approved operation lacks reviewer')
            proof=decision.get('evidence_refs')
            must(isinstance(proof,list) and bool(proof) and all(ids.get(s)=='source' for s in proof),'approved operation lacks registered KS evidence')
            ptr_set(new,pointer,kid)
        elif require_approved:
            raise V11Error('every conversion operation must be approved before application')
    if roles is not None:must(set(roles)==used,'not all declared identity role paths have reviewed conversion')
    return new

# --- v4.0.0-draft.3: diK catalog exchange and recoverable v11 artifact registration ---

import shutil
import uuid


def _json_bytes(value):
    return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf8')


def _transaction_home(root):
    home=Path(root).resolve()/'.kristal/v11/transactions'
    home.mkdir(parents=True,exist_ok=True)
    return home


def _assert_no_pending(root):
    home=Path(root).resolve()/'.kristal/v11/transactions'
    if not home.is_dir():return
    for p in sorted(home.glob('*.json')):
        entry=read(p)
        if entry.get('profile')!='kristal.v11-recoverable-registration/1.0' or entry.get('status') not in ('pending','complete','rolled_back'):
            raise V11Error(f'unrecognized v11 journal {p.name}; manual examination required')
        if entry['status']=='pending':
            raise V11Error(f'pending v11 transaction {p.name}; run recover-v11 --mode finish or rollback')


def _write_exclusive_synced(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f:
        f.write(payload);f.flush();os.fsync(f.fileno())


def _replace_synced(path, payload):
    tmp=path.with_name(path.name+'.new-'+uuid.uuid4().hex)
    try:
        _write_exclusive_synced(tmp,payload)
        os.replace(tmp,path)
    finally:
        tmp.unlink(missing_ok=True)


def _v11_tx_lock(root):
    lock=_transaction_home(root)/'writer.lock'
    try:_write_exclusive_synced(lock,str(os.getpid()).encode('ascii'))
    except FileExistsError as exc:raise V11Error('v11 writer lock exists; check active writers before manual removal') from exc
    return lock


def register_artifact_recoverably(root, *, rel, payload, artifact_id, contract_id,
                                  fault=None, allow_existing=False):
    """Register a NEW canonical JSON in a recoverable two-file logical transaction.

    Crash after installing the file or the state index is handled by recover_v11.
    No existing canonical file is overwritten or unregistered.
    """
    root=Path(root).resolve()
    _assert_no_pending(root)
    must(isinstance(payload,bytes) and payload, 'empty artifact payload')
    must(isinstance(artifact_id,str) and bool(artifact_id) and isinstance(contract_id,str) and bool(contract_id), 'artifact_id and contract required')
    target=safe(root,rel,exists=False)
    must(target.is_relative_to((root/'canon/domain').resolve()) and target.suffix=='.json', 'new v11 artifact must be a canonical JSON')
    must(not target.exists() or (allow_existing and target.is_file() and digest(target)==hashlib.sha256(payload).hexdigest()),
         'canonical output already exists or does not match proposed registered bytes')
    idx_path=safe(root,'canon/state.index.json')
    old_index=idx_path.read_bytes();idx=json.loads(old_index)
    arts=idx.setdefault('canonical_artifacts',[])
    must(all(x.get('artifact_id')!=artifact_id and x.get('path')!=rel for x in arts if isinstance(x,dict)), 'registered artifact_id or path already exists')
    entry={'artifact_id':artifact_id,'path':rel,
           'logical_contract':{'id':contract_id,'version':'11.0'},
           'commitment':{'mode':'compute-json-jcs','profile':'kristal.logical/jcs-sha256-v1'}}
    # Artifact is prevalidated by its producer; serialized output must be JSON.
    json.loads(payload)
    arts.append(entry)
    new_index=_json_bytes(idx)
    lock=_v11_tx_lock(root)
    try:
        _assert_no_pending(root)
        token=uuid.uuid4().hex
        home=_transaction_home(root)
        staged=home/(token+'.artifact')
        journal=home/(token+'.json')
        _write_exclusive_synced(staged,payload)
        state={'profile':'kristal.v11-recoverable-registration/1.0','status':'pending',
               'target':rel,'artifact_id':artifact_id,'contract_id':contract_id,
               'artifact_sha256':hashlib.sha256(payload).hexdigest(),
               'old_index_sha256':hashlib.sha256(old_index).hexdigest(),
               'new_index_sha256':hashlib.sha256(new_index).hexdigest(),
               'new_index':idx,'stage':staged.name}
        _write_exclusive_synced(journal,_json_bytes(state))
        _finish_v11_transaction(root,journal,fault=fault)
        return {'transaction_id':token,'artifact':rel,'artifact_sha256':state['artifact_sha256'], 'status':'registered'}
    finally:
        lock.unlink(missing_ok=True)


def _finish_v11_transaction(root,journal,*,fault=None):
    root=Path(root).resolve();home=_transaction_home(root)
    state=read(journal)
    must(state.get('profile')=='kristal.v11-recoverable-registration/1.0','unknown v11 transaction')
    must(state['status'] in ('pending','complete'),'invalid v11 transaction status')
    dest=safe(root,state['target'],exists=False)
    stage=safe(home,state['stage']) if state['status']=='pending' else None
    if dest.exists():
        must(digest(dest)==state['artifact_sha256'], 'canonical output changed; manual recovery required')
    elif state['status']=='pending':
        must(digest(stage)==state['artifact_sha256'],'staged artifact changed')
        dest.parent.mkdir(parents=True,exist_ok=True)
        try:os.link(stage,dest)   # link does not overwrite an existing target
        except FileExistsError:raise V11Error('canonical output appeared concurrently')
    else:raise V11Error('completed transaction lost canonical artifact')
    if fault=='after_artifact':raise V11Error('INJECTED_CRASH_AFTER_ARTIFACT')
    idx_path=root/'canon/state.index.json';current=idx_path.read_bytes()
    sha=hashlib.sha256(current).hexdigest()
    if sha==state['old_index_sha256']:
        new_bytes=_json_bytes(state['new_index'])
        must(hashlib.sha256(new_bytes).hexdigest()==state['new_index_sha256'],'journal index tampered')
        _replace_synced(idx_path,new_bytes)
    elif sha != state['new_index_sha256']:
        raise V11Error('state index modified concurrently; manual recovery required')
    if fault=='after_index':raise V11Error('INJECTED_CRASH_AFTER_INDEX')
    state['status']='complete'
    _replace_synced(journal,_json_bytes(state))
    if stage:stage.unlink(missing_ok=True)
    return {'status':'complete','target':state['target'],'artifact_sha256':state['artifact_sha256']}


def recover_v11(root, *, mode='status'):
    """Explicit recovery of pending v11 registrations; never guesses a rollback after commit."""
    must(mode in ('status','finish','rollback'), 'invalid recovery mode')
    root=Path(root).resolve();home=_transaction_home(root)
    paths=sorted(home.glob('*.json'))
    if mode=='status':
        return [{'transaction_id':p.stem,'status':read(p).get('status'),
                 'target':read(p).get('target')} for p in paths]
    lock=_v11_tx_lock(root)
    try:
        events=[]
        for path in paths:
            state=read(path)
            if state.get('status')!='pending':continue
            if mode=='finish':events.append(_finish_v11_transaction(root,path))
            else:
                idx=root/'canon/state.index.json';sha=digest(idx)
                must(sha==state['old_index_sha256'], 'rollback forbidden after index commit: finish transaction instead')
                target=safe(root,state['target'],exists=False)
                if target.exists():
                    must(digest(target)==state['artifact_sha256'], 'artifact differs: refusing rollback')
                    target.unlink()
                stage=safe(home,state['stage']);stage.unlink(missing_ok=True)
                state['status']='rolled_back'
                _replace_synced(path,_json_bytes(state))
                events.append({'status':'rolled_back','target':state['target']})
        return events
    finally:lock.unlink(missing_ok=True)


def build_dik_catalog_revision(root, dik_catalog_path, revision):
    """Create a NEW catalog by replacing imported Wikidata layers, preserving curation.

    No catalog is selected or accepted as canonical by this function. All
    referenced source shards are hashed and copied into an immutable revision.
    """
    root=Path(root).resolve()
    must(isinstance(revision,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}',revision)
         and revision not in ('.','..'), 'invalid dictionary revision slug')
    _assert_no_pending(root)
    data=validate(root)
    config=load_profile(root)
    ns,ids=registry_check(read(data['files']['registry']))
    exact=crosswalk_check(read(data['files']['crosswalk']),ns,ids)
    source=Path(dik_catalog_path).resolve()
    # Verify incoming diK catalog's identity scope, every record and SHA.
    imported,_,_=catalog_check(source,ns,ids,exact)
    must(bool(imported['languages']),'incoming catalog has no declared languages')
    must(all(all(layer['kind']=='wikidata' for layer in lang['layers']) for lang in imported['languages']),
         'incoming diK snapshot must contain only imported Wikidata layers; curated edits belong to their own review')
    base_catalog=data['files']['catalog'];current=read(base_catalog)
    base_layers={x['tag']:x for x in current['languages']}
    imports={x['tag']:x for x in imported['languages']}
    candidate={'schema_version':'11.0','artifact_type':'kristal_dictionary_catalog',
               'catalog_id':current['catalog_id']+'-dik-'+revision,'namespace_id':ns,'languages':[]}
    final_rel=f'canon/domain/v11/dictionaries/dik-revisions/{revision}'
    final=root/final_rel
    must(not final.exists(), 'dictionary revision already exists')
    # Copy the two catalog layer sets into their own immutable folder first.
    # A failed copy leaves no canon catalog, only an orphan candidate folder.
    final.mkdir(parents=True,exist_ok=False)
    try:
        for tag in sorted(set(base_layers)|set(imports)):
            old=base_layers.get(tag, {'tag':tag,'fallbacks':[], 'layers':[]})
            newer=imports.get(tag)
            kept=[layer for layer in old['layers'] if not newer or layer['kind']!='wikidata']
            mixed=[(layer,base_catalog.parent,'old') for layer in kept]
            if newer:mixed += [(layer,source.parent,'dik') for layer in newer['layers']]
            seen_ids=set();layers=[]
            for i,(layer,parent,origin) in enumerate(mixed):
                must(layer['layer_id'] not in seen_ids, 'duplicate layer ID in merged catalog')
                seen_ids.add(layer['layer_id'])
                original=safe(parent,layer['path'])
                must(digest(original)==layer['sha256'], 'input layer digest mismatch')
                # Does not preserve foreign paths; all new catalog paths are local to revision.
                rel=f'layers/{tag}/{origin}-{i}.json' + ('l' if layer['kind']!='curated' else '')
                if layer['kind']=='curated':rel=f'layers/{tag}/{origin}-{i}.json'
                else:rel=f'layers/{tag}/{origin}-{i}.jsonl'
                target=final/rel;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(original,target)  # stream large dictionary layers
                must(digest(target)==layer['sha256'], 'copied shard digest mismatch')
                new_layer=dict(layer);new_layer['path']=rel
                layers.append(new_layer)
            candidate['languages'].append({'tag':tag,'fallbacks':list(old['fallbacks']) if tag in base_layers else [],'layers':layers})
        path=final/'catalog.json'
        _write_exclusive_synced(path,_json_bytes(candidate))
        receipt={'profile':'kristal.dik-catalog-proposal/1.0',
                 'source_catalog_sha256':digest(source),'previous_catalog_sha256':digest(base_catalog),
                 'new_catalog_sha256':digest(path),'revision':revision,
                 'status_at_creation':'candidate_before_optional_registration'}
        _write_exclusive_synced(final/'DIK_IMPORT_RECEIPT.json',_json_bytes(receipt))
        # Validate merged catalog, never adopt a conflict or an undeclared Q.
        catalog_check(path,ns,ids,exact)
        return {'catalog':path.relative_to(root).as_posix(),'catalog_id':candidate['catalog_id'],
                'sha256':digest(path), 'old_catalog_sha256':digest(base_catalog),
                'source_catalog_sha256':digest(source), 'registered':False, 'selected':False}
    except BaseException:
        # Newly created revision folder cannot contain any previously registered artifacts.
        shutil.rmtree(final)
        raise
