"""Découverte et consultation d'îlots Kristal existants, sans écrire au canon."""
from __future__ import annotations
from pathlib import Path
import hashlib
import json
from .sources import utc
from .config import ROOT
from .locking import serialized


def _within(root,path):
    return path.resolve().is_relative_to(root.resolve())


def _state_id(path,data):
    artifacts=data.get('canonical_artifacts',[])
    if isinstance(artifacts,list):
        for a in artifacts:
            aid=a.get('artifact_id','') if isinstance(a,dict) else ''
            if aid.startswith('urn:kristal:'):
                parts=aid.split(':')
                if len(parts)>=4:return 'urn:kristal:'+parts[2]
    return 'local:workspace:'+hashlib.sha256(str(path.resolve()).encode()).hexdigest()[:20]


@serialized
def scan_islands(db,roots):
    results={'readable':0,'unavailable':[],'ignored':0}
    for root_name in roots:
        root=Path(root_name)
        if not root.is_dir():
            results['unavailable'].append(str(root));continue
        # Inspect declared workspace state indices only; no blind content migration.
        for path in root.rglob('canon/state.index.json'):
            if not path.is_file():continue
            base=path.parent.parent
            if not _within(root,base):results['ignored']+=1;continue
            try:data=json.loads(path.read_text(encoding='utf-8-sig'))
            except (ValueError,OSError):results['ignored']+=1;continue
            island=_state_id(base,data)
            with db:
                origin='ARCHIVED_REFERENCE_NOT_LIVE' if (ROOT/'ecosystem').resolve() in base.resolve().parents else 'EXTERNAL_KRISTAL_READ_ONLY'
                db.execute('INSERT OR REPLACE INTO island_locations VALUES(?,?,?,?,?)',
                  (island,str(base.resolve()),str(path.resolve()),origin,utc()))
                locations=[dict(x) for x in db.execute('SELECT * FROM island_locations WHERE island_key=?',(island,))
                           if Path(x['state_index']).is_file()]
                live=[x for x in locations if x['source']=='EXTERNAL_KRISTAL_READ_ONLY']
                preferred=live or locations
                chosen=sorted(preferred,key=lambda x:x['root'])[0]
                chosen_source=chosen['source'] if len(live)<=1 else 'AUTHORITY_CONFLICT'
                authority=db.execute('SELECT value FROM meta WHERE key=?',('island_authority:'+island,)).fetchone()
                if authority:
                    approved=next((x for x in locations if x['root']==authority[0]),None)
                    if approved:chosen=approved;chosen_source=approved['source']
                    else:chosen_source='AUTHORITY_UNAVAILABLE'
                db.execute('''INSERT INTO kristal_islands(island_key,root,state_index,model,source,scan_utc)
                   VALUES(?,?,?,?,?,?) ON CONFLICT(island_key) DO UPDATE SET
                   root=excluded.root,state_index=excluded.state_index,model=excluded.model,
                   source=excluded.source,scan_utc=excluded.scan_utc''',
                   (island,chosen['root'],chosen['state_index'],str(data.get('format','UNKNOWN')),
                    chosen_source,utc()))
                # UNESCO branch affinity is navigational, not an assertion of canon alignment.
                if base.name.startswith('unesco-mt'):
                    parts=base.name.removeprefix('unesco-mt').split('-')
                    if len(parts)==2 and all(x.isdigit() for x in parts):
                        bid=f'unesco.mt{int(parts[0])}.{int(parts[1]):02d}'
                        db.execute('INSERT OR IGNORE INTO island_branch_links VALUES(?,?,?)',
                                   (island,bid,'SOURCE_WORKSPACE_NAVIGATION'))
            results['readable']+=1
    return results


def list_islands(db,branch=None,limit=200):
    if branch:
        rows=db.execute('''SELECT DISTINCT i.* FROM kristal_islands i
                         JOIN island_branch_links l ON l.island_key=i.island_key
                         WHERE l.branch_id=? ORDER BY i.island_key LIMIT ?''',(branch,limit))
    else:
        rows=db.execute('SELECT * FROM kristal_islands ORDER BY island_key LIMIT ?',(limit,))
    return [dict(r) for r in rows]


def describe_island(db,island_key,include_preview=True):
    row=db.execute('SELECT * FROM kristal_islands WHERE island_key=?',(island_key,)).fetchone()
    if not row:raise ValueError('Îlot non recensé')
    if row['source']=='AUTHORITY_UNAVAILABLE':raise ValueError('Workspace autoritaire indisponible; aucun remplacement implicite')
    if row['source']=='AUTHORITY_CONFLICT':raise ValueError('Plusieurs workspaces vivants pour cet îlot; autorité à résoudre explicitement')
    root=Path(row['root']);index=Path(row['state_index'])
    if not _within(root,index) or not index.is_file():raise FileNotFoundError('État canonique indisponible')
    data=json.loads(index.read_text(encoding='utf-8-sig'))
    artifacts=[]
    for a in data.get('canonical_artifacts',[]):
        if not isinstance(a,dict):continue
        raw=a.get('path','')
        rel=Path(raw)
        if rel.is_absolute() or '..' in rel.parts:continue
        target=root/rel
        if not _within(root,target):continue
        desc={**a,'available':target.is_file()}
        if include_preview and target.is_file() and target.stat().st_size<512*1024 and target.suffix in ('.json','.md','.txt'):
            # Preview is a faithful excerpt, never interpreted as admitted knowledge on its own.
            desc['preview']=target.read_text(encoding='utf-8',errors='replace')[:1200]
        artifacts.append(desc)
    return {'island_key':island_key,'root':str(root),'inventory_source':row['source'],'state_format':data.get('format'),'index_sha256':hashlib.sha256(index.read_bytes()).hexdigest(),
            'canonical_artifacts':artifacts,'read_only':True,
            'publication_authorized':False,'admission_authorized':False}


def export_federated_read_view(db,island_keys,out_path):
    """VUE, pas état parent Kristal publié; les ressources manquantes restent explicites."""
    records=[]
    for island in island_keys:
        try:records.append(describe_island(db,island,include_preview=False))
        except (ValueError,OSError,KeyError) as exc:records.append({'island_key':island,'error':str(exc)})
    report={'format':'encyk.federated-read-view.v32/1','created_utc':utc(),
            'status':'DERIVED_NOT_CANONICAL_SNAPSHOT','islands':records,
            'note':'Les métadonnées de lecture ne démontrent aucune qualification Framework/Kit.'}
    target=Path(out_path);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return str(target)


def admit_proposals(*_args,**_kwargs):
    raise RuntimeError('Admission désactivée : Authoring Kit v11 non qualifié dans les sources disponibles. '
                       'Exporter les propositions privées; ne pas écrire directement dans canon/domain.')


@serialized
def choose_island_location(db,island_key,root):
    root=str(Path(root).resolve())
    row=db.execute('SELECT * FROM island_locations WHERE island_key=? AND root=?',(island_key,root)).fetchone()
    if not row or not Path(row['state_index']).is_file():raise ValueError('Emplacement non recensé ou indisponible')
    data=json.loads(Path(row['state_index']).read_text(encoding='utf-8-sig'))
    if _state_id(Path(root),data)!=island_key:raise ValueError('Identité du workspace modifiée')
    with db:
        db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',('island_authority:'+island_key,root))
        db.execute('UPDATE kristal_islands SET root=?,state_index=?,model=?,source=?,scan_utc=? WHERE island_key=?',
          (root,row['state_index'],data.get('format','UNKNOWN'),row['source'],utc(),island_key))
        db.execute('INSERT INTO events(created_utc,kind,details) VALUES(?,?,?)',
          (utc(),'ISLAND_AUTHORITY',json.dumps({'island_key':island_key,'root':root})))
    return {'island_key':island_key,'root':root,'read_only':True}
