#!/usr/bin/env python3
"""UNESCO V16: actual Kit workspace check + bounded v11 discovery + local evidence audit.

Only creates a new *private diagnostic* stage. No v11 enable, no canonical KQ/KP/KA/KS,
no new dump scan, no GF generation, no Manager publication functions or GitHub.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from workspace_readiness_v15 import DEFAULT_WORK, DEFAULT_ROOT, OUT as V15_OUT, ensure_work

BRANCH='unesco-mt1-10'
OUT='semantic_stage_v16_identites_preuves'
DECISIONS=('DECISIONS_41_IDENTITES_EDITABLE.csv','DECISIONS_85_PROPOSITIONS_EDITABLE.csv',
           'DECISIONS_61_RELATIONS_EDITABLE.csv','DECISIONS_4_SOURCES_CONCEPT10_EDITABLE.csv')
class V16Error(ValueError): pass

def sha(raw:bytes):return hashlib.sha256(raw).hexdigest()
def jb(obj):return (json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
def read_json(p:Path,limit=12_000_000):
    if not p.is_file() or p.is_symlink() or p.stat().st_size>limit:raise V16Error('JSON absent ou taille excessive: '+str(p))
    return json.loads(p.read_text('utf-8-sig'))
def load(path:Path,name:str):
    if not path.is_file() or path.is_symlink():raise V16Error('Module absent: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def integrity(folder:Path,manifest_name:str,items_key:str):
    if folder.is_symlink() or not folder.is_dir():raise V16Error('Dossier prive absent: '+str(folder))
    manifest=read_json(folder/manifest_name)
    entries=manifest.get(items_key)
    if not isinstance(entries,dict) or not entries:raise V16Error('Manifeste sans empreintes')
    for rel,expected in entries.items():
        if (not isinstance(rel,str) or not rel or '\\' in rel or ':' in rel or
             Path(rel).is_absolute() or '..' in Path(rel).parts):raise V16Error('Chemin manifeste incorrect')
        f=folder/rel
        if not f.is_file() or f.is_symlink() or sha(f.read_bytes())!=expected:
            raise V16Error('Empreinte invalide: '+str(f))
    # No untracked generated files or tampered output.
    actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    if actual!=set(entries)|{manifest_name}:raise V16Error('Fichiers supplementaires ou manquants: '+str(folder))
    if any(p.is_symlink() for p in folder.rglob('*')):raise V16Error('Lien symbolique dans source/sortie')
    return manifest

def verify_v15_input_contract(v15_manifest:dict,work:Path,root:Path):
    """Reject drift in any file pinned by the previous V15 execution."""
    inputs=v15_manifest.get('input_sha256')
    if not isinstance(inputs,dict) or not inputs:raise V16Error('V15 sans ancrages de provenance')
    for name,expected in inputs.items():
        if name in ('registry_workspace_explicit',) or name.startswith('registry_workspace/'):
            # An explicitly supplied registry is an external input, not a default discovery target.
            # V16 checks it independently when --registry-workspace is provided.
            continue
        if not isinstance(expected,str) or not re.fullmatch(r'[0-9a-f]{64}',expected):
            raise V16Error('Ancrage V15 invalide: '+str(name))
        if not isinstance(name,str) or '\\' in name or ':' in name or Path(name).is_absolute() or '..' in Path(name).parts:
            raise V16Error('Chemin ancrage V15 non sur')
        path=(root/name[5:]) if name.startswith('code/') else (work/name)
        if not path.is_file() or path.is_symlink() or sha(path.read_bytes())!=expected:
            raise V16Error('Entree V15 modifiee, refuser de poursuivre: '+name)

def _decisions(path:Path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size>3_000_000:raise V16Error('Decisions absentes')
    r=csv.DictReader(io.StringIO(path.read_text('utf-8-sig'),newline=''))
    rows=list(r)
    if 'decision' not in (r.fieldnames or []) or any(None in x or any(v is None for v in x.values()) for x in rows):
        raise V16Error('Tableau de decisions invalide')
    return rows

def kit_private_check(root:Path,stage15:Path,stage14:Path):
    ws=stage15/'kit_workspace'
    official=root/'Kristal/Kristal-Authoring-Kit/tools/kristal.py'
    if not official.is_file() or official.is_symlink():raise V16Error('Kit officiel absent')
    if (ws/'.kristal/v11/authoring.json').exists():raise V16Error('Profil v11 trouve dans le workspace prive, traitement refuse')
    meta=read_json(ws/'kristal.workspace.json')
    if meta.get('slug')!=BRANCH:raise V16Error('Workspace de branche inattendu')
    derived=read_json(ws/'derived/unesco-mt1-10/candidat_editorial_sans_KQ.json')
    original=read_json(stage14/'KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json')
    if derived!=original or derived.get('canonical_graph_built') is not False:
        raise V16Error('Candidat derive Kit ne correspond pas a la revue V14')
    p=subprocess.run([sys.executable,str(official),'check',str(ws)],capture_output=True,text=True,timeout=120)
    if p.returncode:raise V16Error('Echec de la commande officielle Kit check: '+(p.stderr or p.stdout)[-900:])
    return {'kit_workspace_verified_again':True,'kit_standard_check':'PASSED',
        'derived_graph_sha256':sha((ws/'derived/unesco-mt1-10/candidat_editorial_sans_KQ.json').read_bytes()),
        'v11_profile_enabled':False,'canonical_writes':0}

def run(work:Path,root:Path,*,registry_roots:list[Path]|None=None,
        registry_workspace:Path|None=None,check_only:bool=False,output_name:str=OUT):
    if not re.fullmatch(r"semantic_stage_v16_[a-z0-9_-]{3,60}",output_name):
        raise V16Error("Nom de nouveau dossier v16 interdit")
    work=ensure_work(Path(work));root=Path(root).resolve(strict=True)
    stage15=work/V15_OUT;stage14=work/'semantic_stage_v14_editorial';stage11=work/'semantic_stage_v11_global'
    v15=integrity(stage15,'MANIFESTE_V15.json','files_sha256')
    verify_v15_input_contract(v15,work,root)
    v15report=read_json(stage15/'RAPPORT_V15.json')
    if (v15report.get('status')!='KIT_PRIVATE_WORKSPACE_INITIALIZED_V11_CANON_BLOCKED'
        or v15report.get('canonical_KQ_KP_KA_KS_created')!=0
        or v15report.get('kit_workspace_real_cli_initialized') is not True):
        raise V16Error('V15 non conforme ou encore absente')
    kit=kit_private_check(root,stage15,stage14)
    dec=[]
    for name in DECISIONS:dec.extend(_decisions(stage11/name))
    pending=sum(x.get('decision')=='PENDING' for x in dec)
    if len(dec)!=191:raise V16Error('191 decisions attendues')
    anchors={'stage15_manifest_sha256':sha((stage15/'MANIFESTE_V15.json').read_bytes()),
             'stage14_graph_sha256':sha((stage14/'KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json').read_bytes()),
             'stage11_manifest_sha256':sha((stage11/'MANIFESTE_PASSE_GLOBALE.json').read_bytes())}
    for name in DECISIONS:anchors['decisions/'+name]=sha((stage11/name).read_bytes())
    extract=work/'wikipedia_extract'
    anchors['wiki_manifest_sha256']=sha((extract/'manifest.json').read_bytes())
    provenance_script=root/'Kristal/Kristalizer/tools/unesco_local_provenance_v16.py'
    discovery_script=root/'Kristal/Kristal-Manager/kristal_manager/unesco_registry_discovery_v16.py'
    reconciliation_script=root/'Kristal/Kristal-Manager/kristal_manager/unesco_registry_reconcile_v15.py'
    matrix_script=root/'SemantiK_Architect/SemantiK_Runtime_Orchestrator/tools/unesco_runtime_matrix_v15.py'
    kit_gate=root/'Kristal/Kristal-Authoring-Kit/tools/unesco_v11_readonly_gate.py'
    for name,p in [('provenance',provenance_script),('discovery',discovery_script),('reconcile',reconciliation_script),('runtime',matrix_script),('kit_gate',kit_gate)]:
        if not p.is_file() or p.is_symlink():raise V16Error('Dependance absente '+name)
        anchors['code/'+name]=sha(p.read_bytes())
    provenance=load(provenance_script,'unesco_provenance_v16').verify(extract,stage11)
    if (provenance['candidate_research_contexts_verified']!=16 or provenance['redirect_pages_excluded']!=2 or
       provenance['approved_KS']!=0):raise V16Error('Audit documentaire inattendu')
    if registry_roots is None:
        registry_roots=[root/'Kristal/locals',root/'Kristal/Kristal-Manager/workspaces',root/'Kristal/Kristal-Authoring-Kit/workspaces']
    # Explicit roots are read only; their identity becomes part of the immutable run contract.
    anchors['registry_roots']=[str(Path(p).resolve()) if p.exists() else str(p) for p in registry_roots]
    anchors['explicit_registry_workspace']=str(registry_workspace.resolve(strict=True)) if registry_workspace is not None else None
    mgr=load(discovery_script,'unesco_registry_discovery_v16')
    discovery=mgr.discover(registry_roots,kit_gate,explicit_workspace=registry_workspace)
    candidate=read_json(stage14/'KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json')
    reconcile=load(reconciliation_script,'unesco_reconcile_v15')
    reconciled=reconcile.reconcile(candidate,discovery.get('selected_kit_report') or {})
    if reconciled.get('count')!=41 or reconciled.get('qid_candidates')!=36:raise V16Error('Reconciliation inattendue')
    runtime_root=root/'SemantiK_Architect/SemantiK_Architect/runtime'
    sys.path.insert(0,str(matrix_script.parent))
    matrix=load(matrix_script,'unesco_runtime_v15').matrix(runtime_root)
    if matrix.get('languages_targeted')!=14 or matrix.get('publication_authorized') is not False:
        raise V16Error('Readiness GF inattendu')
    blockers=['NO_AUTHORIZED_HUMAN_ADMISSION' if pending else 'ADMISSION_REQUIRES_INDEPENDENT_VERIFICATION',
              'NO_ATTESTED_KS','NO_CANONICAL_KQ_KP_KA_KS_IN_PRIVATE_WORKSPACE',
              'GF_ARTIFACT_INTEGRITY_IS_NOT_REALIZATION']
    if not discovery['selected_readonly_workspace']:blockers.append('NO_UNAMBIGUOUS_EXISTING_UNESCO_V11_REGISTRY')
    summary={'format':'koa.unesco-mt1-10-registry-provenance-bridge/1.0','branch':BRANCH,
        'status':'PRIVATE_V16_REGISTRY_PROVENANCE_AUDITED_CANON_BLOCKED',
        'kit_private_workspace_check_passed':kit['kit_workspace_verified_again'],
        'registry_v11_candidates_checked':discovery['candidate_workspace_count'],
        'registry_v11_verified_branch_workspaces':discovery['branch_verified_workspace_count'],
        'existing_crosswalk_candidates_verified':reconciled['exactmatch_existing_candidates'],
        'concepts':41,'editorial_statements':85,'skos_internal_distinct':61,
        'human_admission_decisions_pending':pending,'source_leads_unattested':81,
        'local_contexts_sha256_verified':16,'local_wikipedia_substantive_pages':provenance['substantive_pages'],
        'local_wikipedia_redirects_excluded':2,
        'GF_artifact_integrity_ready_profiles':matrix['artifact_integrity_ready_profiles'],
        'realization_execution_verified':False,'multilingual_slots_planned':574,
        'canonical_KQ_KP_KA_KS_created':0,'source_KS_approved':0,'articles_generated':0,
        'kit_v11_enabled_by_this_tool':False,'git_push':False,'publication_authorized':False,
        'blocking_requirements':blockers}
    files={'RAPPORT_V16.json':jb(summary),'KIT_PRIVÉ_CHECK_V16.json':jb(kit),
        'REGISTRES_V11_DECOUVERTS.json':jb(discovery),'RECONCILIATION_V16.json':jb(reconciled),
        'WIKIPEDIA_PROVENANCE_V16.json':jb(provenance),'GF_RUNTIME_REALITE_V16.json':jb(matrix),
        'EXIGENCES_ADMISSION_V16.json':jb({'branch':BRANCH,'outstanding':blockers,'human_signature_minted':False,
          'KS_attested':0,'no_canonical_build':True,'manual_next':'Verifier workspace v11 explicite, preuves KS et decisions autorisees'})}
    out=work/output_name
    if out.is_symlink():raise V16Error('Sortie symbolique interdite')
    if out.exists():
        manifest=integrity(out,'MANIFESTE_V16.json','files_sha256')
        if manifest.get('input_sha256')!=anchors or manifest.get('files_sha256')!={k:sha(v) for k,v in files.items()}:
            raise V16Error('Sources ou rapport ont change : conserver cette version, choisir un nouveau dossier')
        return {**summary,'operation':'DEJA_PRESENT_INTACT','output':str(out)}
    if check_only:raise V16Error('Sortie V16 absente, audit impossible')
    with tempfile.TemporaryDirectory(prefix='_unesco-v16-staging-',dir=work) as td:
        staging=Path(td)/output_name;staging.mkdir()
        for name,data in files.items():(staging/name).write_bytes(data)
        (staging/'MANIFESTE_V16.json').write_bytes(jb({'format':'koa.unesco-mt1-10-v16-manifest/1.0',
            'branch':BRANCH,'input_sha256':anchors,'files_sha256':{k:sha(v) for k,v in files.items()},
            'canonical_created':0,'publication_authorized':False}))
        if out.exists():raise V16Error('Sortie apparue pendant execution, aucun ecrasement')
        staging.rename(out)
    return {**summary,'operation':'NOUVEAU_DIAGNOSTIC_PRIVE','output':str(out)}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,default=DEFAULT_WORK)
    p.add_argument('--repo-root',type=Path,default=DEFAULT_ROOT)
    p.add_argument('--registry-root',type=Path,action='append',dest='registry_roots')
    p.add_argument('--registry-workspace',type=Path)
    p.add_argument('--check-only',action='store_true')
    p.add_argument('--output-name',default=OUT,help='nouveau nom quand le registre fourni change, jamais de remplacement')
    a=p.parse_args(argv)
    print(json.dumps(run(a.work,a.repo_root,registry_roots=a.registry_roots,
       registry_workspace=a.registry_workspace,check_only=a.check_only,output_name=a.output_name),ensure_ascii=False,indent=2,sort_keys=True))

if __name__=='__main__':
    try:main()
    except (V16Error,ValueError,KeyError,TypeError,OSError,RuntimeError,subprocess.TimeoutExpired) as e:
        print('V16 BLOQUE SANS CANONISATION : '+str(e),file=sys.stderr);sys.exit(2)
