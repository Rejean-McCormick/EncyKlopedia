#!/usr/bin/env python3
"""UNESCO 41-concept canonical-handoff *readiness* overlay, private/offline.

Runs real Kristalizer, Manager and Authoring-Kit read-only gates. Writes only
new, reproducible handoff diagnostics under semantic_stage_v13_bridge.
NEVER runs Kit init, enable-v11, register, build, publish or Git.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from review_global_overlay_v12 import (BRANCH, check_private_directory, load_stage11,
    read_json_bytes, read_json_bytes as read_json, json_bytes, rows_file,
    verify_output, publish_new_files, ReviewError)

FORMAT='koa.unesco-mt1-10-kit-manager-kristalizer-bridge/1.0'
DEFAULT_WORK=Path(r'D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41')
DEFAULT_ROOT=Path(__file__).resolve().parents[4]
OUT='semantic_stage_v13_bridge'

class BridgeError(ValueError):pass

def run_gate(script:Path, *args):
    if not script.is_file() or script.is_symlink():
        raise BridgeError('Correctif absent : '+str(script))
    try:
        p=subprocess.run([sys.executable,str(script),*map(str,args)],
                         capture_output=True,text=True,timeout=90)
    except subprocess.TimeoutExpired as e:
        raise BridgeError('Delai depasse dans : '+script.name) from e
    if p.returncode:
        raise BridgeError(f'{script.name}: {p.stderr[-1200:] or p.stdout[-1200:]}')
    try: return json.loads(p.stdout)
    except json.JSONDecodeError as exc:
        raise BridgeError('Sortie non JSON : '+script.name) from exc

def sha(data:bytes):return sha256(data).hexdigest()

def build(work:Path,repo_root:Path,workspace:Path|None=None):
    work=check_private_directory(work)
    stage12=work/'semantic_stage_v12_revue_chatgpt'
    stage11=work/'semantic_stage_v11_global'
    if not stage12.is_dir() or stage12.is_symlink():
        raise BridgeError('Etape 12 attendue, lancer LANCER_UNESCO_OVERLAY_REVUE_41.cmd')
    manifest_file=stage12/'MANIFESTE_RECOMMANDATIONS.json'
    if not manifest_file.is_file() or manifest_file.is_symlink():
        raise BridgeError('Manifeste de revue manquant')
    review_manifest=read_json(manifest_file.read_bytes())
    original_manifest,tables,decisions=load_stage11(work,review_manifest)
    # The independent Kristalizer gate checks every stage-12 immutable SHA.
    kr_script=repo_root/'Kristal/Kristalizer/tools/unesco_admission_contract_v13.py'
    kr=run_gate(kr_script,'--work',work)
    if kr.get('status')!='INTEGRITY_PASSED_CONTENT_NOT_ADMITTED' or kr.get('unsigned_recommendations_validated')!=85:
        raise BridgeError('Kristalizer: validation de la revue manquante')
    kit_script=repo_root/'Kristal/Kristal-Authoring-Kit/tools/unesco_v11_readonly_gate.py'
    kit_args=['--workspace',str(workspace)] if workspace is not None else []
    kit=run_gate(kit_script,*kit_args)
    if kit.get('canonical_writes')!=0 or kit.get('publication_authorized') is not False:
        raise BridgeError('Le Kit ne doit rien ecrire')
    manager_script=repo_root/'Kristal/Kristal-Manager/kristal_manager/unesco_admission_bridge.py'
    # Pass the exact Kit registry inspection to the Manager via an ephemeral file.
    with tempfile.TemporaryDirectory(prefix='unesco-v13-kit-') as tmp:
        report_path=Path(tmp)/'kit.json';report_path.write_bytes(json_bytes(kit))
        mgr=run_gate(manager_script,'--stage11',stage11,'--kit-report',report_path)
    if (mgr.get('rows_total')!=191 or mgr.get('canon_write_authorized') is not False
            or mgr.get('canonical_created')!=0):
        raise BridgeError('Manager: resultats de revue inattendus')
    # Source content is verified against each prior manifest; mutable decisions
    # are bound to their exact current bytes to make changed decisions detectable.
    decision_sha={filename:sha((stage11/filename).read_bytes()) for filename,_,_ in (
        ('DECISIONS_41_IDENTITES_EDITABLE.csv','',0),
        ('DECISIONS_85_PROPOSITIONS_EDITABLE.csv','',0),
        ('DECISIONS_61_RELATIONS_EDITABLE.csv','',0),
        ('DECISIONS_4_SOURCES_CONCEPT10_EDITABLE.csv','',0))}
    source_info={
        'stage12_recommendations_handoff_sha256':sha((stage12/'RECOMMANDATIONS_85_POUR_KRISTALIZER_NON_CANONIQUES.json').read_bytes()),
        'stage11_manifest_sha256':sha((stage11/'MANIFESTE_PASSE_GLOBALE.json').read_bytes()),
        'stage12_manifest_sha256':sha((stage12/'MANIFESTE_OVERLAY_ETAPE12.json').read_bytes()),
        'stage12_review_sha256':sha(manifest_file.read_bytes()),
        'decision_sha256':decision_sha,
    }
    editorial=read_json((stage12/'RECOMMANDATIONS_85_POUR_KRISTALIZER_NON_CANONIQUES.json').read_bytes())
    indexed_editorial={r['proposal_ref']:r for r in editorial['proposals']}
    if len(indexed_editorial)!=85 or len(editorial['proposals'])!=85:
        raise BridgeError('Recommandations editoriales doublees ou absentes')
    candidates=[]
    by_ref=tables['proposals']
    for ref, row in sorted(by_ref.items()):
        d=decisions['DECISIONS_85_PROPOSITIONS_EDITABLE.csv'][ref]
        review=indexed_editorial[ref]
        if review['statement_original_en']!=row['statement_en']:
            raise BridgeError('Texte original different de la revue')
        candidates.append({'proposal_ref':ref,'unesco_id':row['unesco_id'],
            'original_en':row['statement_en'],
            'suggested_en_unapproved':review['editorial_suggestion_en'],
            'semantic_risk_fr':review['semantic_risk_fr'],
            'source_search_hint_fr':review['source_search_hint_fr'],
            'prior_editorial_assessment':row['review_preavis'],
            'decision_status':d['decision'],'human_reviewer_declared':bool(d['responsable']),
            'canonical_admission_status':'NOT_APPROVED',
            'evidence_status':row['source_status']})
    handoff={
        'format':'koa.unesco-mt1-10-v11-private-candidate-handoff/1.0',
        'branch':BRANCH,'one_branch_kristal':True,
        'concept_count':41,
        'identities':[{'unesco_id':ref,'unesco_uri':r['unesco_uri'],
                       'label_en_metadata':r['label_en'],'qid_candidate':r['qid_candidat'],
                       'KQ_existing_unverified':decisions['DECISIONS_41_IDENTITES_EDITABLE.csv'][ref]['KQ_existant'],
                       'decision':decisions['DECISIONS_41_IDENTITES_EDITABLE.csv'][ref]['decision'],
                       'exact_match_approved_by_tool':False}
                      for ref,r in sorted(tables['identities'].items())],
        'proposals':candidates,'skos_internal_distinct':61,
        'skos_internal_groups':[{'ref':ref,'source':r['source_ou_membre_a'],
                  'target':r['cible_ou_membre_b'],'skos_relation':r['relation_normalisee'],
                  'observed_reciprocal_indexes':r['observations_reciproques'],
                  'decision':decisions['DECISIONS_61_RELATIONS_EDITABLE.csv'][ref]['decision']}
                  for ref,r in sorted(tables['relations'].items())],
        'source_leads':[{'reference_id':ref,'portee':r['portee'],
                 'document_type':r['document_type'],'url':r['url'],
                 'approved_KS_by_tool':False}
                 for ref,r in sorted(tables['sources'].items())],
        'skos_external_observations':112,'projection_slots_planned':574,
        'source_anchors':source_info,
        'framework_target':'11.0.0-draft.4',
        'kit_readiness':kit['workspace_v11_status'],
        'pending_review_decisions':mgr['pending'],
        'approved_exact_matches':0,'approved_assertions':0,'approved_KS':0,
        'canonical_identifiers_minted':0,'admission_authorized':False,
        'release_gates_qualified':False,'public_release_authorized':False,
        'projections_are_plans_only':True,
    }
    summary={
        'format':FORMAT,'branch':BRANCH,
        'status':'PRIVATE_V11_HANDOFF_READY_CANONICAL_APPROVAL_BLOCKED',
        'kristalizer_gate':'PASSED_NON_CANONICAL',
        'manager_decisions_total':mgr['rows_total'],
        'manager_pending_decisions':mgr['pending'],
        'manager_submitted_for_review':mgr['submitted_for_review'],
        'kit_v11_existing_workspace':kit['workspace_v11_status'],
        'registry_identities_checked':len(mgr['explicit_canonical_refs_checked']),
        'approval_authorized':False, 'canonical_kristal_built':False,
        'canonical_KQ_KP_KA_KS_created':0,'articles_generated':0,'git_push':False,
        'one_branch_kristal':True,'planned_projection_slots':574,
        'next':'Attestations KS, reconciliation du registre KQ/KP et decisions autorisees; Kit check-v11 en lecture seule sur workspace explicite',
    }
    files={
        'RAPPORT_PONT_V11.json':json_bytes(summary),
        'CONTRAT_KRISTALIZER.json':json_bytes(kr),
        'DIAGNOSTIC_MANAGER_191.json':json_bytes(mgr),
        'DIAGNOSTIC_KIT_V11.json':json_bytes(kit),
        'HANDOFF_KRISTAL_CANDIDAT_PRIVE.json':json_bytes(handoff),
    }
    m={'format':'koa.unesco-mt1-10-bridge-output-manifest/1.0','branch':BRANCH,
       'source_anchors':source_info,'files_sha256':{k:sha(v) for k,v in sorted(files.items())},
       'canonical_created':0,'publication_authorized':False}
    files['MANIFESTE_PONT_V11.json']=json_bytes(m)
    return summary,files

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work',type=Path,default=DEFAULT_WORK)
    p.add_argument('--repo-root',type=Path,default=DEFAULT_ROOT)
    p.add_argument('--workspace',type=Path,help='workspace Kit v11 EXISTANT; controle read-only')
    p.add_argument('--output',type=Path,help='dossier cible prive distinct, sinon semantic_stage_v13_bridge')
    p.add_argument('--check-only',action='store_true')
    args=p.parse_args(argv)
    summary,files=build(args.work,args.repo_root,args.workspace)
    out=args.output or args.work/OUT
    # Arbitrary output path is never allowed in Git, canon, or source folders.
    if out.resolve() == args.work.resolve() or not out.resolve().is_relative_to(args.work.resolve()):
        raise BridgeError('Sortie doit rester sous le dossier de travail prive')
    for folder in (out,*out.parents):
        if (folder/'.git').exists():raise BridgeError('Sortie dans depot Git interdite')
    status,existing=publish_new_files(out,files,check_only=args.check_only)
    summary={**summary,'operation':status,'existing_output_files':existing,'output':str(out)}
    print(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (BridgeError,ReviewError,ValueError,OSError,TypeError,KeyError,UnicodeError,json.JSONDecodeError) as exc:
        print('PONT V11 BLOQUE SANS CANONISATION: '+str(exc),file=sys.stderr);sys.exit(2)
