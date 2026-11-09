#!/usr/bin/env python3
"""UNESCO Educational Policy V17: one-command full *available* production pass.

Runs real Kit v11 checks, Workbench↔editorial reconciliation, source/admission
checks, real GF readiness probes, and produces a 41-page English local reader.
It is deliberately impossible to turn candidate KQ/KP/KS into approved canon,
claim multilingual realizations, or push GitHub through this command.

Use --require-final to fail closed if the final product prerequisites are absent.
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
import subprocess
import sys
import tempfile

BRANCH='unesco-mt1-10'
LOCALES=('en','fr','es','de','nl','sv','da','no','nn','fi','et','af','it','pt')
DEFAULT_ROOT=Path(__file__).resolve().parents[4]
DEFAULT_WORK=Path(r'D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41')
DEFAULT_OUT='semantic_stage_v17_integrated_product'
DEFAULT_WORKBENCH=Path('EncyKlopedia/UNESCO_Workbench/candidates/educational-policy-en-v11/unesco-mt1-10')
DECISION_COUNTS={'DECISIONS_41_IDENTITES_EDITABLE.csv':41,
                 'DECISIONS_85_PROPOSITIONS_EDITABLE.csv':85,
                 'DECISIONS_61_RELATIONS_EDITABLE.csv':61,
                 'DECISIONS_4_SOURCES_CONCEPT10_EDITABLE.csv':4}
class PipelineError(ValueError):pass

def sha(b:bytes):return hashlib.sha256(b).hexdigest()
def jb(obj):return (json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
def read_bytes(path:Path,max_bytes=20_000_000):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>max_bytes:
        raise PipelineError('Entree absente, symbolique ou trop volumineuse: '+str(path))
    return path.read_bytes()
def read_json(path:Path):return json.loads(read_bytes(path).decode('utf-8-sig'))
def read_csv(path:Path):
    r=csv.DictReader(io.StringIO(read_bytes(path,5_000_000).decode('utf-8-sig'),newline=''))
    data=list(r)
    if not r.fieldnames or any(None in a or any(x is None for x in a.values()) for a in data):
        raise PipelineError('CSV invalide: '+str(path))
    return data

def import_file(file:Path,name:str):
    read_bytes(file,1_000_000)
    spec=importlib.util.spec_from_file_location(name,file)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def verified_source(work:Path,root:Path):
    """Read all meaningful anchors directly; don't trust previous status strings alone."""
    stage14=work/'semantic_stage_v14_editorial'
    stage15=work/'semantic_stage_v15_workspace'
    stage11=work/'semantic_stage_v11_global'
    candidates={
        'stage14/report':stage14/'RAPPORT_EDITIONS_V14.json',
        'stage14/graph':stage14/'KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json',
        'stage14/manifest':stage14/'MANIFESTE_EDITORIAL_V14.json',
        'stage15/report':stage15/'RAPPORT_V15.json',
        'stage15/manifest':stage15/'MANIFESTE_V15.json',
        'stage11/manifest':stage11/'MANIFESTE_PASSE_GLOBALE.json',
        'stage11/leads':stage11/'FILE_81_SOURCES_A_ATTESTER.csv',
        'stage11/projections':stage11/'PROJECTIONS_574_NON_GENEREES.csv',
    }
    for name in DECISION_COUNTS:candidates['stage11/'+name]=stage11/name
    anchors={name:sha(read_bytes(p)) for name,p in candidates.items()}
    report14=read_json(stage14/'RAPPORT_EDITIONS_V14.json')
    report15=read_json(stage15/'RAPPORT_V15.json')
    if (report14.get('branch')!=BRANCH or report14.get('editorial_claims_selected')!=85
        or report14.get('private_english_concept_previews')!=41
        or report14.get('canonical_kristal_built') is not False):raise PipelineError('V14 incoherent')
    if (report15.get('branch')!=BRANCH or report15.get('kit_standard_check_passed') is not True
        or report15.get('canonical_KQ_KP_KA_KS_created')!=0):raise PipelineError('V15 incomplet')
    # Pin source data through the already accepted V15 manifest too. This
    # detects local modification of V14 plus its own rehashed manifest.
    m15=read_json(stage15/'MANIFESTE_V15.json')
    pinned15=m15.get('input_sha256',{})
    if not isinstance(pinned15,dict) or not pinned15:
        raise PipelineError('Manifeste V15 sans ancrage de provenance')
    checked=0
    for rel,expected in pinned15.items():
        if not isinstance(rel,str) or not rel.startswith(('semantic_stage_v11_global/','semantic_stage_v14_editorial/')):
            continue
        if ':' in rel or '\\' in rel or '..' in Path(rel).parts:
            raise PipelineError('Chemin v15 non fiable: '+rel)
        if sha(read_bytes(work/rel))!=expected:
            raise PipelineError('Ancrage V15 divergent: '+rel)
        checked+=1
    if checked<3:raise PipelineError('Manifeste V15 insuffisant pour ancrer le contenu')
    manifest14=read_json(stage14/'MANIFESTE_EDITORIAL_V14.json')
    pinned=manifest14.get('files_sha256',{})
    if not pinned or any('/' in x and x.startswith('../') for x in pinned):raise PipelineError('Manifest V14 invalide')
    for rel,expected in pinned.items():
        if (not isinstance(rel,str) or rel.startswith('/') or '\\' in rel or ':' in rel
            or '..' in Path(rel).parts or sha(read_bytes(stage14/rel))!=expected):
            raise PipelineError('Modification V14 non autorisee: '+str(rel))
    editorial=read_json(stage14/'KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json')
    if editorial.get('canonical_graph_built') is not False or editorial.get('claims_approved_as_KA')!=0:
        raise PipelineError('V14 non candidat')
    # Look for the user-selected v16 audit, without forcing a new scan.
    audited=[]
    for name in ('semantic_stage_v16_workbench_candidat_20261108','semantic_stage_v16_identites_preuves'):
        p=work/name
        if not p.is_dir() or p.is_symlink():continue
        r=read_json(p/'RAPPORT_V16.json')
        if (r.get('branch')!=BRANCH or r.get('kit_private_workspace_check_passed') is not True
            or r.get('source_KS_approved')!=0):raise PipelineError('V16 incoherent: '+name)
        audited.append({'report_path':str(p/'RAPPORT_V16.json'),
                        'report_sha256':sha(read_bytes(p/'RAPPORT_V16.json')),
                        'registry_verified_branch_workspaces':r.get('registry_v11_verified_branch_workspaces',0)})
    dec={}
    for name,expected in DECISION_COUNTS.items():
        data=read_csv(stage11/name)
        if len(data)!=expected or 'decision' not in data[0]:raise PipelineError('Decisions incompletes: '+name)
        dec[name]=data
    leads=read_csv(stage11/'FILE_81_SOURCES_A_ATTESTER.csv')
    slots=read_csv(stage11/'PROJECTIONS_574_NON_GENEREES.csv')
    if len(leads)!=81 or len(slots)!=574:raise PipelineError('81 pistes et 574 slots attendus')
    nodeids={n['unesco_id'] for n in editorial.get('nodes',[])}
    if len(nodeids)!=41 or {(r['unesco_id'],r['locale']) for r in slots}!={(cid,lang) for cid in nodeids for lang in LOCALES}:
        raise PipelineError('Grille 41 x 14 incorrecte')
    if any(x.get('article_generated')!='NO' or x.get('publication_authorized')!='NO' for x in slots):
        raise PipelineError('Statut de projection v11 douteux')
    for name,rows in dec.items():
        if any(r['decision']!='PENDING' for r in rows):
            # Do not silently reuse editorial decisions as human authorization.
            raise PipelineError('Decisions humaines modifiees: exiger requalification independante pour '+name)
    return editorial,dec,leads,slots,anchors,audited

def official_kit(kit:Path,workspace:Path):
    for cmd in ('check','check-v11'):
        p=subprocess.run([sys.executable,str(kit),cmd,str(workspace)],capture_output=True,text=True,timeout=120)
        if p.returncode:raise PipelineError('Kit '+cmd+' refuse le Workbench: '+(p.stderr or p.stdout)[-900:])

def independent_framework_check(repo_root:Path,workspace:Path):
    """Run official pinned Framework/Integration v11 qualification, read-only.

    A structural Kit check is not an independent Framework qualification.
    Older Workbench dictionaries may legitimately fail the latest schema;
    report this rather than bypassing the official validator.
    """
    script=repo_root/'Kristal/Kristal-Authoring-Kit/scripts/qualify_framework_v11.py'
    framework=repo_root/'Kristal/Kristal-Framework'
    integration=repo_root/'Kristal/Kristal-Integration-Pack'
    if not all(x.exists() for x in (script,framework,integration)):
        return {'independent_qualified':False,'status':'PINNED_QUALIFIER_OR_INTEGRATION_MISSING'}
    proc=subprocess.run([sys.executable,str(script),'--project',str(workspace),
        '--framework',str(framework),'--integration-pack',str(integration)],
        capture_output=True,text=True,timeout=120)
    if proc.returncode:
        return {'independent_qualified':False,'status':'PINNED_FRAMEWORK_QUALIFICATION_FAILED',
          'diagnostic':(proc.stderr or proc.stdout)[-1200:]}
    try:report=json.loads(proc.stdout)
    except ValueError:return {'independent_qualified':False,'status':'PINNED_QUALIFICATION_NON_JSON'}
    return {'independent_qualified':report.get('valid') is True,
      'status':'PINNED_QUALIFICATION_PASSED' if report.get('valid') is True else 'PINNED_QUALIFICATION_REFUSED',
      'report':report}

def runtime_matrix(repo_root:Path):
    script=repo_root/'SemantiK_Architect/SemantiK_Runtime_Orchestrator/tools/unesco_runtime_matrix_v15.py'
    root=repo_root/'SemantiK_Architect/SemantiK_Architect/runtime'
    p=subprocess.run([sys.executable,str(script),'--runtime-root',str(root)],capture_output=True,text=True,timeout=120)
    if p.returncode:raise PipelineError('Controle GF refuse: '+(p.stderr or p.stdout)[-900:])
    try:r=json.loads(p.stdout)
    except ValueError as e:raise PipelineError('GF retour non JSON') from e
    if r.get('languages_targeted')!=14 or r.get('publication_authorized') is not False:
        raise PipelineError('Bilan GF incorrect')
    return r

def inspect_release(align:dict,decisions:dict,kit_ok:bool,runtime:dict,framework:dict):
    # An executable, fail-closed release contract. No certificate or human
    # signature can be manufactured by editing a CSV, and GF integrity alone
    # never qualifies a language or a projection.
    checks={
      'C1_implementation_and_framework_contract_qualified':False,
      'C2_content_rights_security_and_approvals':False,
      'C3_immutable_materialization_digests_rollback':False,
      'C4_independent_public_exposure_approval':False,
    }
    reasons=['PROVISIONAL_KQ_KP_KS_NOT_APPROVED',
      'NO_ATTESTED_KS_OR_SIGNED_ADMISSION',
      'NO_QUALIFIED_CANONICAL_SEMANTIC_GRAPH',
      'GF_ARTIFACT_READY_NOT_REALIZATION_OR_LINGUISTIC_APPROVAL',
      'NO_C1_C4_PUBLICATION_AUTHORIZATION']
    if framework.get('independent_qualified') is not True:
        reasons.append('PINNED_FRAMEWORK_INDEPENDENT_QUALIFICATION_NOT_PASSED')
    return {'format':'koa.unesco-v17-final-product-release-gates/1.0','branch':BRANCH,
        'kit_structural_validation_passed':kit_ok,
        'independent_framework_qualification_passed':framework.get('independent_qualified') is True,
        'editorial_decisions_present':191,'human_admissions_pending':sum(r['decision']=='PENDING' for rows in decisions.values() for r in rows),
        'provisional_KQ_count':align['provisional_KQ_count'],
        'provisional_KP_count':align['provisional_KP_count'],'provisional_KS_count':align['provisional_KS_count'],
        'approved_KQ':0,'approved_KP':0,'approved_KS':0,'approved_KA':0,
        'GF_artifact_ready_profiles':runtime['artifact_integrity_ready_profiles'],
        'realizations_qualified':0,'canonical_identity_and_evidence_qualified':False,
        'public_release_checks':checks,
        'blocking_reasons':reasons,'final_product_publishable':False,
        'repo_sync_performed':False,'git_push_performed':False,
        'user_authorization_inferred':False}

def verify_output(out:Path,expected_inputs:dict|None=None):
    if out.is_symlink() or not out.is_dir():raise PipelineError('Sortie absente ou symbolique')
    manifest=read_json(out/'MANIFESTE_V17.json')
    content=manifest.get('files_sha256')
    if not isinstance(content,dict) or len(content)<80:raise PipelineError('Manifest V17 incomplet')
    if expected_inputs is not None and manifest.get('input_sha256')!=expected_inputs:
        raise PipelineError('Sources modifiees: choisir nouveau dossier v17, sans ecraser')
    actual=set()
    for p in out.rglob('*'):
        if p.is_symlink():raise PipelineError('Sortie contient lien symbolique')
        if p.is_file():actual.add(p.relative_to(out).as_posix())
    if actual!=set(content)|{'MANIFESTE_V17.json'}:
        raise PipelineError('Sortie manque ou contient des fichiers inconnus')
    for rel,expected in content.items():
        if (not isinstance(rel,str) or not rel or ':' in rel or '\\' in rel
            or Path(rel).is_absolute() or '..' in Path(rel).parts
            or sha(read_bytes(out/rel,20_000_000))!=expected):
            raise PipelineError('Sortie modifiee: '+str(rel))
    return manifest

def execute(work:Path,root:Path,workbench:Path,*,output_name=DEFAULT_OUT,check_only=False,require_final=False):
    if not re.fullmatch(r'semantic_stage_v17_[a-z0-9_-]{3,70}',output_name):
        raise PipelineError('Nom de sortie invalide')
    if not Path(work).is_dir() or Path(work).is_symlink():raise PipelineError('Dossier D prive absent')
    work=Path(work).resolve(strict=True);root=Path(root).resolve(strict=True)
    if (root/'.git').exists() or (work/'.git').exists():raise PipelineError('Ne pas ecrire dans un depot Git')
    if not workbench.is_absolute():workbench=root/workbench
    workbench=workbench.resolve(strict=True)
    if 'demo-semantic-v11' in workbench.parts or 'examples' in workbench.parts:raise PipelineError('Workspace demo non recevable')
    if not workbench.is_dir() or workbench.is_symlink():raise PipelineError('Workbench absent')
    editorial,decisions,leads,slots,input_anchors,audited=verified_source(work,root)
    kit=root/'Kristal/Kristal-Authoring-Kit/tools/kristal.py'
    official_kit(kit,workbench)
    for rel in ('kristal.workspace.json','.kristal/v11/authoring.json',
         '.kristal/v11/identity-migration-map.json','canon/domain/v11/registry.json',
         'canon/domain/v11/graph.json','canon/domain/v11/crosswalk.json'):
        input_anchors['workbench/'+rel]=sha(read_bytes(workbench/rel))
    scripts={
      'align':root/'Kristal/Kristal-Manager/kristal_manager/unesco_workbench_alignment_v17.py',
      'kitclone':root/'Kristal/Kristal-Authoring-Kit/tools/unesco_candidate_workspace_v17.py',
      'reader':root/'Spek_Semantic-publishing/Spek/spek/unesco_private_reader_v17.py',
      'runtime':root/'SemantiK_Architect/SemantiK_Runtime_Orchestrator/tools/unesco_runtime_matrix_v15.py',
    }
    for n,p in scripts.items():input_anchors['code/'+n]=sha(read_bytes(p))
    input_anchors['workbench_abspath']=str(workbench)
    mgr=import_file(scripts['align'],'manager_v17_align')
    alignment=mgr.align(workbench,editorial)
    spek=import_file(scripts['reader'],'spek_v17_reader')
    pages=spek.build(editorial,alignment)
    runtime=runtime_matrix(root)
    framework=independent_framework_check(root,workbench)
    gates=inspect_release(alignment,decisions,True,runtime,framework)
    if require_final and not gates['final_product_publishable']:
        raise PipelineError('PRODUIT FINAL BLOQUE: '+', '.join(gates['blocking_reasons']))
    summary={'format':'koa.unesco-mt1-10-integrated-product-pipeline/1.0','branch':BRANCH,
      'status':'PRIVATE_INTEGRATED_PRODUCT_READY_FINAL_RELEASE_BLOCKED',
      'one_branch_kristal':True,'Kit_workbench_check_v11_passed':True,
      'provisional_registry_KQ':41,'provisional_registry_KP':3,'provisional_registry_KS':1,
      'workbench_crosswalk_candidates':36,'editorial_statements':85,'editorial_concepts':41,
      'skos_internal_distinct':61,'source_leads_unattested':len(leads),
      'private_english_reading_pages':41,'private_reader_home':'reader_en/index.html',
      'multilingual_slots_planned':574,'multilingual_slots_realized':0,
      'GF_artifact_integrity_ready_profiles':runtime['artifact_integrity_ready_profiles'],
      'pinned_Framework_qualification_status':framework['status'],
      'C1_C4_qualified':False,'human_admissions_pending':191,'canonical_assertions_created':0,
      'canonical_workspace_written':False,'official_articles_generated':0,'github_push':False,
      'next':'Qualified KS + authorized decisions + canonical Kit v11 registry/graph + GF/SemantiK realization + release gates'}
    out=work/output_name
    if out.exists():
        verify_output(out,input_anchors)
        if read_json(out/'RAPPORT_PRODUIT_V17.json')!=summary:
            raise PipelineError('Etat du rapport differe; choisir autre sortie')
        return {**summary,'operation':'DEJA_PRESENT_INTACT','output':str(out)}
    if check_only:raise PipelineError('Sortie absente: audit impossible')
    kit_module=import_file(scripts['kitclone'],'kit_v17_clone')
    with tempfile.TemporaryDirectory(prefix='_unesco-v17-staging-',dir=work) as tmp:
        stage=Path(tmp)/output_name;stage.mkdir()
        clone=kit_module.prepare(workbench,stage/'workbench_v11_candidat_prive',kit,editorial,alignment)
        payload={
         'RAPPORT_PRODUIT_V17.json':jb(summary),
         'GATES_PRODUIT_FINAL_V17.json':jb(gates),
         'ALIGNEMENT_WORKBENCH_41_V17.json':jb(alignment),
         'KIT_WORKBENCH_CLONAGE_V17.json':jb({k:v for k,v in clone.items() if k!='source_files_sha256'}),
         'GF_RUNTIME_MATRIX_V17.json':jb(runtime),
         'FRAMEWORK_V11_QUALIFICATION_V17.json':jb(framework),
         'CANDIDAT_SEMANTIQUE_85_V17.json':jb(editorial),
         'PROVENANCE_81_PISTES_NON_KS.json':jb({'branch':BRANCH,'approved_KS':0,'items':leads}),
         'PROJECTIONS_574_NON_REALISEES.json':jb({'branch':BRANCH,'realized':0,'items':slots}),
         'AUDITS_V16_HISTORIQUES.json':jb(audited),
         'README_PRODUIT_PRIVE.md':("# UNESCO Educational Policy — produit de lecture PRIVÉ\n\n"
            "Ouvrir `reader_en/index.html` localement pour consulter les **41 aperçus anglais**.\n\n"
            "Ce sont **des brouillons éditoriaux**, pas des articles canoniques ou des réalisations GF.\n"
            "Le workspace v11 ici est une copie isolée du Workbench PROVISOIRE; aucune identité n'est approuvée.\n"
            "Voir `GATES_PRODUIT_FINAL_V17.json` pour les conditions de finalisation. Aucun dépôt GitHub modifié.\n").encode('utf-8'),
        }
        payload.update(pages)
        for name,raw in payload.items():
            target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        files={p.relative_to(stage).as_posix():sha(p.read_bytes()) for p in stage.rglob('*') if p.is_file()}
        (stage/'MANIFESTE_V17.json').write_bytes(jb({'format':'koa.unesco-v17-integrated-manifest/1.0',
            'branch':BRANCH,'input_sha256':input_anchors,'files_sha256':files,
            'canonical_approval_not_performed':True,'public_release_authorized':False}))
        if out.exists():raise PipelineError('Sortie apparue pendant preparation; aucun ecrasement')
        stage.rename(out)
    return {**summary,'operation':'NOUVEAU_PRODUIT_PRIVE','output':str(out)}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,default=DEFAULT_WORK)
    p.add_argument('--repo-root',type=Path,default=DEFAULT_ROOT)
    p.add_argument('--workbench-workspace',type=Path,default=DEFAULT_WORKBENCH)
    p.add_argument('--output-name',default=DEFAULT_OUT)
    p.add_argument('--check-only',action='store_true')
    p.add_argument('--require-final',action='store_true',help='refuser si conditions du vrai produit final absentes')
    a=p.parse_args(argv)
    result=execute(a.work,a.repo_root,a.workbench_workspace,
        output_name=a.output_name,check_only=a.check_only,require_final=a.require_final)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (PipelineError,ValueError,KeyError,TypeError,OSError,UnicodeError,json.JSONDecodeError,subprocess.TimeoutExpired) as e:
        print('UNESCO V17 BLOQUE SANS PUBLICATION: '+str(e),file=sys.stderr);sys.exit(2)
