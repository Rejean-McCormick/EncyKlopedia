#!/usr/bin/env python3
"""One-pass UNESCO Kit private workspace + registry + KS + GF gate (four real repos).

- SOURCE: stage v14 private editorial work, hash-checked against v11-v13.
- OUTPUT: new Kit-initialized workspace in PRIVATE work/semantic_stage_v15_workspace/.
- NO v11 enable, canonical KQ/KP/KA/KS, source attestations, GF realization,
  Github, or public release. Always fail closed on drift or modified output.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from editorial_advance_v14 import make as make_v14, DEFAULT_WORK, DEFAULT_ROOT
from review_global_overlay_v12 import verify_output, ReviewError

BRANCH='unesco-mt1-10'
OUT='semantic_stage_v15_workspace'
CANONICAL_FILES=(
    'DECISIONS_41_IDENTITES_EDITABLE.csv',
    'DECISIONS_85_PROPOSITIONS_EDITABLE.csv',
    'DECISIONS_61_RELATIONS_EDITABLE.csv',
    'DECISIONS_4_SOURCES_CONCEPT10_EDITABLE.csv',
)
class Stage15Error(ValueError):pass

def sha(raw):return hashlib.sha256(raw).hexdigest()
def jb(obj):return (json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
def read_json(path:Path,max_size=12_000_000):
    if not path.is_file() or path.is_symlink() or path.stat().st_size>max_size:
        raise Stage15Error('JSON absent ou hors limite: '+str(path))
    return json.loads(path.read_text('utf-8-sig'))
def read_csv(path:Path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size>4_000_000:
        raise Stage15Error('CSV absent ou hors limite: '+str(path))
    reader=csv.DictReader(io.StringIO(path.read_text('utf-8-sig'),newline=''))
    rows=list(reader)
    if not reader.fieldnames or any(None in row or any(v is None for v in row.values()) for row in rows):
        raise Stage15Error('CSV malforme: '+str(path))
    return rows

def import_module(path:Path,name:str):
    if not path.is_file() or path.is_symlink():raise Stage15Error('Overlay manquant: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def gate(path:Path,*args):
    if not path.is_file() or path.is_symlink():raise Stage15Error('Gate absent: '+str(path))
    p=subprocess.run([sys.executable,str(path),*map(str,args)],capture_output=True,text=True,timeout=120)
    if p.returncode:raise Stage15Error('Gate '+path.name+': '+(p.stderr or p.stdout)[-1200:])
    try:return json.loads(p.stdout)
    except ValueError as exc:raise Stage15Error('Gate JSON invalide: '+path.name) from exc

def ensure_work(work:Path):
    if work.is_symlink():raise Stage15Error('Dossier de travail symbolique interdit')
    work=work.resolve(strict=True)
    if not work.is_dir() or work.is_symlink():raise Stage15Error('Dossier prive invalide')
    if (work/'semantic_stage_v14_editorial').is_symlink():raise Stage15Error('Dossier editorial symbolique')
    for parent in (work,*work.parents):
        if (parent/'.git').exists():raise Stage15Error('Ecriture sous un depot Git refusee')
    return work

def source_anchors(work:Path,repo_root:Path,existing:Path|None):
    stage14=work/'semantic_stage_v14_editorial'
    previous,files=make_v14(work,repo_root)
    verify_output(stage14,files)
    if previous['editorial_claims_selected']!=85 or previous['private_english_concept_previews']!=41:
        raise Stage15Error('V14 incomplet')
    stage11=work/'semantic_stage_v11_global'
    stage13=work/'semantic_stage_v13_bridge'
    anchors={}
    for p in [stage14/'MANIFESTE_EDITORIAL_V14.json',
              stage14/'KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json',
              stage13/'MANIFESTE_PONT_V11.json',
              stage11/'MANIFESTE_PASSE_GLOBALE.json'] + [stage11/k for k in CANONICAL_FILES]:
        if not p.is_file() or p.is_symlink():raise Stage15Error('Source manquante: '+str(p))
        anchors[str(p.relative_to(work)).replace('\\','/')]=sha(p.read_bytes())
    for dep in (
        'Kristal/Kristal-Authoring-Kit/tools/kristal.py',
        'Kristal/Kristal-Authoring-Kit/tools/unesco_private_workspace_v15.py',
        'Kristal/Kristal-Authoring-Kit/tools/unesco_v11_readonly_gate.py',
        'Kristal/Kristal-Manager/kristal_manager/unesco_registry_reconcile_v15.py',
        'SemantiK_Architect/SemantiK_Runtime_Orchestrator/tools/unesco_runtime_matrix_v15.py',
        'SemantiK_Architect/SemantiK_Runtime_Orchestrator/src/semantik_runtime_orchestrator/readiness.py'):
        p=repo_root/dep
        if not p.is_file() or p.is_symlink():raise Stage15Error('Dependance absente: '+str(p))
        anchors['code/'+dep]=sha(p.read_bytes())
    if existing is not None:
        p=existing.resolve(strict=True)
        if not p.is_dir() or existing.is_symlink():raise Stage15Error('Workspace explicite invalide')
        # This helps make mistaken use of the Kit demo a hard failure.
        if 'examples' in p.parts and 'demo-semantic-v11' in p.parts:
            raise Stage15Error('Workspace demonstration interdit')
        anchors['registry_workspace_explicit']=str(p)
        for rel in ('kristal.workspace.json','.kristal/v11/authoring.json','canon/state.index.json',
                    'canon/domain/v11/registry.json','canon/domain/v11/graph.json',
                    'canon/domain/v11/crosswalk.json','canon/domain/v11/dictionaries/catalog.json'):
            f=p/rel
            anchors['registry_workspace/'+rel]=sha(f.read_bytes()) if f.is_file() and not f.is_symlink() else 'MISSING'
    return anchors

def run_pipeline(work:Path,repo_root:Path,existing:Path|None=None,*,output_name:str=OUT,check_only=False):
    work=ensure_work(work)
    repo_root=repo_root.resolve(strict=True)
    if not re.fullmatch(r'semantic_stage_v15_[a-z0-9_-]{3,50}',output_name):
        raise Stage15Error('Nom de sortie prive non conforme')
    anchors=source_anchors(work,repo_root,existing)
    stage14=work/'semantic_stage_v14_editorial'
    candidate=read_json(stage14/'KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json')
    candidate_sha=sha((stage14/'KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json').read_bytes())
    kit_gate_script=repo_root/'Kristal/Kristal-Authoring-Kit/tools/unesco_v11_readonly_gate.py'
    kit=gate(kit_gate_script,*(['--workspace',existing] if existing else []))
    if kit.get('publication_authorized') is not False or kit.get('canonical_writes')!=0:
        raise Stage15Error('Gate Kit canonique inattendu')
    if existing is not None and kit.get('workspace_branch_binding')=='NOT_ESTABLISHED' and kit.get('workspace_v11_status')=='EXISTING_WORKSPACE_KIT_CHECK_V11_PASSED':
        raise Stage15Error('Workspace v11 externe sans liaison UNESCO explicite')
    manager=import_module(repo_root/'Kristal/Kristal-Manager/kristal_manager/unesco_registry_reconcile_v15.py','unesco_registry_v15')
    reconciliation=manager.reconcile(candidate,kit)
    if (reconciliation['count']!=41 or reconciliation['qid_candidates']!=36 or
        reconciliation['exactmatch_existing_candidates']>36):raise Stage15Error('Reconciliation inattendue')
    stage11=work/'semantic_stage_v11_global'
    leads=read_csv(stage11/'FILE_81_SOURCES_A_ATTESTER.csv')
    if len(leads)!=81:raise Stage15Error('Pistes KS incompletes')
    source_leads={'format':'koa.unesco-mt1-10-ks-proof-worklist/1.0','branch':BRANCH,
        'total_leads':81,'unesco_anchor_leads':41,'wikidata_crosswalk_leads':36,
        'primary_legal_locator_leads':4,
        'rows':[{'reference_id':r.get('reference_id'),'document_type':r.get('document_type'),
                 'url':r.get('url'),'scope':r.get('portee'),
                 'independent_fact_evidence_qualified':False,'KS_approved':False,
                 'source_needs_attestation':True} for r in leads],
        'attested_KS':0,'canonical_approval_authorized':False}
    runtime_root=repo_root/'SemantiK_Architect/SemantiK_Architect/runtime'
    runtime_script=repo_root/'SemantiK_Architect/SemantiK_Runtime_Orchestrator/tools/unesco_runtime_matrix_v15.py'
    runtime=gate(runtime_script,'--runtime-root',runtime_root)
    if runtime.get('languages_targeted')!=14 or runtime.get('publication_authorized') is not False:
        raise Stage15Error('Etat GF inattendu')
    projections=read_csv(stage11/'PROJECTIONS_574_NON_GENEREES.csv')
    if len(projections)!=574 or any(row.get('article_generated')!='NO' for row in projections):
        raise Stage15Error('File de projection non privee')
    slot_names={(r.get('unesco_id',''),r.get('locale','')) for r in projections}
    locales={'en','fr','es','de','nl','sv','da','no','nn','fi','et','af','it','pt'}
    nodes={n['unesco_id'] for n in candidate['nodes']}
    if len(slot_names)!=574 or {u for u,l in slot_names}!=nodes or {l for u,l in slot_names}!=locales:
        raise Stage15Error('Grille de projections 41 x 14 incomplete/dupliquee')
    projection_report={'format':'koa.unesco-mt1-10-runtime-projection-preflight/1.0','branch':BRANCH,
        'private_projection_slots':574,'concepts':41,'target_locales':14,
        'runtime_artifact_ready_profiles':runtime['artifact_integrity_ready_profiles'],
        'actual_generated_articles':0,'GF_realizations_performed':0,
        'SemantiK_requests_emitted':0,'reason':'NO_APPROVED_KQ_KP_KA_KS_FOR_CANONICAL_REALIZATION',
        'publication_authorized':False}
    previous_summary=read_json(stage14/'RAPPORT_EDITIONS_V14.json')
    summary={'format':'koa.unesco-mt1-10-private-kit-workspace-registry-runtime/1.0',
        'branch':BRANCH,'status':'KIT_PRIVATE_WORKSPACE_INITIALIZED_V11_CANON_BLOCKED',
        'kit_workspace_slug':BRANCH,'kit_workspace_real_cli_initialized':True,
        'kit_standard_check_passed':True,'kit_v11_profile_enabled':False,
        'existing_registry_workspace_status':kit.get('workspace_v11_status'),
        'existing_registry_branch_bound':kit.get('workspace_branch_binding')=='EXPLICIT_SLUG_MATCH',
        'qid_candidates':36,'existing_crosswalk_candidates_verified':reconciliation['exactmatch_existing_candidates'],
        'editorial_candidate_concepts':41,'editorial_candidate_statements':85,
        'skos_internal_distinct':61,'source_leads_unattested':81,
        'human_decisions_still_pending':previous_summary['human_decisions_still_pending'],'source_KS_approved':0,
        'runtime_artifact_ready_profiles':runtime['artifact_integrity_ready_profiles'],
        'realized_multilingual_projections':0,'planned_multilingual_slots':574,
        'canonical_KQ_KP_KA_KS_created':0,'canonical_kristal_built':False,
        'articles_generated':0,'git_push':False,'public_release_authorized':False,
        'next':'Revue de registre et de preuves dans un workspace v11 deja qualifie, puis approbations autorisees; runtime GF execution a qualifier',
    }
    out=work/output_name
    if out.is_symlink():raise Stage15Error('Sortie symbolique interdite')
    if check_only and not out.exists():raise Stage15Error('Sortie absente: audit impossible')
    if out.exists():
        manifest=read_json(out/'MANIFESTE_V15.json')
        if manifest.get('input_sha256')!={k:anchors[k] for k in sorted(anchors)}:
            raise Stage15Error('Sources et/ou registre modifies: sortie ancienne; utiliser --output-name nouveau')
        for name,expected in manifest.get('files_sha256',{}).items():
            if not isinstance(name,str) or not name or '\\' in name or ':' in name or '..' in Path(name).parts:
                raise Stage15Error('Manifeste de chemins non fiables')
            p=out/name
            if not p.is_file() or p.is_symlink() or sha(p.read_bytes())!=expected:
                raise Stage15Error('Sortie deja presente mais modifiee: '+name)
        if any(p.is_symlink() for p in out.rglob('*')):
            raise Stage15Error('Liens symboliques dans la sortie refuses')
        actual={str(p.relative_to(out)).replace('\\','/') for p in out.rglob('*') if p.is_file()}
        if actual!=set(manifest['files_sha256'])|{'MANIFESTE_V15.json'}:
            raise Stage15Error('Dossier de sortie modifie: fichiers supplementaires ou manquants')
        if read_json(out/'RAPPORT_V15.json')!=summary:
            raise Stage15Error('Le diagnostic actuel differe du dossier existant')
        # Recheck actual official Kit functionality on the retained new workspace.
        scaffold=import_module(repo_root/'Kristal/Kristal-Authoring-Kit/tools/unesco_private_workspace_v15.py','private_kit_v15')
        scaffold.command('check',out/'kit_workspace',kit=scaffold.KIT)
        return {**summary,'operation':'DEJA_PRESENT_INTACT','output':str(out)}
    if check_only:raise Stage15Error('Sortie absente')
    with tempfile.TemporaryDirectory(prefix='_unesco-v15-staging-',dir=work) as temp:
        staging=Path(temp)/output_name
        staging.mkdir()
        scaffold=import_module(repo_root/'Kristal/Kristal-Authoring-Kit/tools/unesco_private_workspace_v15.py','private_kit_v15')
        result=scaffold.make(staging/'kit_workspace',candidate,candidate_sha,kit=scaffold.KIT)
        to_write={
           'RAPPORT_V15.json':summary,
           'KIT_WORKSPACE_VALIDATION.json':result,
           'KIT_REGISTRE_EXISTANT_LECTURE_SEULE.json':kit,
           'RECONCILIATION_41_IDENTITES.json':reconciliation,
           'KS_81_PISTES_NON_ATTESTEES.json':source_leads,
           'GF_14_LANGUES_READINESS.json':runtime,
           'PROJECTIONS_574_GATES.json':projection_report,
        }
        for filename,data in to_write.items():
            (staging/filename).write_bytes(jb(data))
        files_sha={str(p.relative_to(staging)).replace('\\','/'):sha(p.read_bytes())
                   for p in staging.rglob('*') if p.is_file() and not p.is_symlink()}
        (staging/'MANIFESTE_V15.json').write_bytes(jb({'format':'koa.unesco-mt1-10-v15-manifest/1.0',
            'branch':BRANCH,'input_sha256':{k:anchors[k] for k in sorted(anchors)},
            'files_sha256':{k:files_sha[k] for k in sorted(files_sha)},
            'canonical_created':0,'release_authorized':False}))
        if out.exists():raise Stage15Error('Sortie apparue pendant execution; aucun ecrasement')
        staging.rename(out)
    return {**summary,'operation':'NOUVEAU_WORKSPACE_PRIVE','output':str(out)}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,default=DEFAULT_WORK)
    p.add_argument('--repo-root',type=Path,default=DEFAULT_ROOT)
    p.add_argument('--existing-workspace',type=Path,help='Workspace v11 existant et explicitement lie a UNESCO; lecture seule')
    p.add_argument('--output-name',default=OUT)
    p.add_argument('--check-only',action='store_true')
    args=p.parse_args(argv)
    result=run_pipeline(args.work,args.repo_root,args.existing_workspace,output_name=args.output_name,check_only=args.check_only)
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True));return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (Stage15Error,ReviewError,ValueError,OSError,KeyError,TypeError,UnicodeError,subprocess.TimeoutExpired,json.JSONDecodeError) as exc:
        print('V15 BLOQUE SANS CANONISATION: '+str(exc),file=sys.stderr);sys.exit(2)
