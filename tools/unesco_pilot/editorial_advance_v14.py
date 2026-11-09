#!/usr/bin/env python3
"""UNESCO private editorial advancement, 41 concepts, genuine multi-repository overlay.

Uses the already-installed v11/v12/v13 integrity and read-only admission gates.
Makes ChatGPT editorial choices for *private previews*, NOT human signatures,
canonical KQ/KP/KA/KS, actual RuntimeSet, articles, or GitHub publication.
"""
from __future__ import annotations
import argparse
import importlib.util
from hashlib import sha256
import json
from pathlib import Path
import sys

from canonical_bridge_v13 import build as build_v13, DEFAULT_ROOT, DEFAULT_WORK
from review_global_overlay_v12 import (load_stage11, verify_semantics, read_json_bytes,
    json_bytes, rows_file, check_private_directory, publish_new_files, verify_output, ReviewError)

FORMAT='koa.unesco-mt1-10-editorial-decision-pipeline/1.0'
OUT='semantic_stage_v14_editorial'
class AdvanceError(ValueError): pass

def loader(path:Path, name:str):
    if not path.is_file() or path.is_symlink():raise AdvanceError('Overlay absent : '+str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def sha(raw):return sha256(raw).hexdigest()

def make(work:Path,root:Path):
    work=check_private_directory(work)
    stage11=work/'semantic_stage_v11_global'
    stage12=work/'semantic_stage_v12_revue_chatgpt'
    stage13=work/'semantic_stage_v13_bridge'
    if stage13.is_symlink() or not stage13.is_dir():raise AdvanceError('Pont V13 absent : lancer le lanceur 4 depots')
    # Re-execute the actual gates from v13; no writes.
    bridge_summary,bridge_files=build_v13(work,root)
    verify_output(stage13,bridge_files)
    if any(not (stage13/k).is_file() for k in bridge_files):
        raise AdvanceError('Pont V13 incomplet')
    if bridge_summary['status']!='PRIVATE_V11_HANDOFF_READY_CANONICAL_APPROVAL_BLOCKED':
        raise AdvanceError('Etat du pont v11 inattendu')
    manifest=read_json_bytes((stage12/'MANIFESTE_RECOMMANDATIONS.json').read_bytes())
    _,tables,decisions=load_stage11(work,manifest)
    reviewfiles={name:(stage12/name).read_bytes() for name in (
        'REVUE_41_IDENTITES_NON_SIGNEE.csv','REVUE_85_PROPOSITIONS_NON_SIGNEE.csv',
        'REVUE_61_RELATIONS_SKOS_NON_SIGNEE.csv','REVUE_81_PISTES_DE_SOURCES_NON_KS.csv',
        '191_RECOMMANDATIONS_NON_SIGNEES.csv','CONCEPT10_8_FRAGMENTS_ANNOTES_NON_KA.csv')}
    rp,ri,rr,rs=verify_semantics(reviewfiles,tables)
    mgr=loader(root/'Kristal/Kristal-Manager/kristal_manager/unesco_editorial_decisions_v14.py','manager_editorial_v14')
    kr=loader(root/'Kristal/Kristalizer/tools/unesco_editorial_intake_v14.py','kristalizer_editorial_v14')
    spek=loader(root/'Spek_Semantic-publishing/Spek/spek/unesco_editorial_previews_v14.py','spek_editorial_v14')
    positions=mgr.decide(tables,{'identities':ri,'proposals':rp,'relations':rr,'sources':rs})
    gate=kr.validate(positions,tables,{'proposals':rp,'relations':rr})
    if gate['positions_verified']!=191:raise AdvanceError('Kristalizer n a pas valide les positions')
    previews=spek.compose(positions)
    if len(previews)!=41:raise AdvanceError('Apercus Spek incomplets')
    external=rows_file(stage11/'FRONTIERE_112_OBSERVATIONS_HORS_BRANCHE.csv')
    projections=rows_file(stage11/'PROJECTIONS_574_NON_GENEREES.csv')
    if len(external)!=112 or len(projections)!=574:raise AdvanceError('Frontieres ou emplacements linguistiques incomplets')
    if any(p.get('article_generated')!='NO' or p.get('canonical_qualified')!='NO' or
           p.get('runtime_set_qualified')!='NO' or p.get('publication_authorized')!='NO' for p in projections):
        raise AdvanceError('Projection faussement realisee ou approuvee')
    selected=positions['decisions']
    graph={
        'format':'koa.unesco-mt1-10-private-editorial-kristal-candidate/1.0',
        'branch':'unesco-mt1-10','one_branch_kristal':True,
        'nodes':[{'unesco_id':p['ref'],'label_en':p['label_en'],'label_fr':p['label_fr'],
                  'unesco_uri':p['source_uri'],'qid_candidate_unapproved':p['qid_candidate']}
                 for p in selected if p['type']=='IDENTITE'],
        'candidate_statements':[{'proposal_ref':p['ref'],'unesco_id':p['unesco_id'],
            'original_en':p['original_en'],'editorial_selected_en':p['chosen_text_en'],
            'editorial_status':p['decision_editoriale'],'evidence_status':'NOT_ATTESTED',
            'source_lead_not_KS':p['source_lead']} for p in selected if p['type']=='PROPOSITION'],
        'skos_internal_observations':[{'ref':p['ref'],'source':p['source_unesco_id'],
            'target':p['target_unesco_id'],'relation':p['relation_skos'],
            'reciprocal_indexes':p['observations_reciproques'],'review_flag':p['decision_editoriale']}
            for p in selected if p['type']=='SKOS_INTERNE'],
        'cross_branch_skos_observations_count':112,
        'source_leads_count':81,'projection_slots_planned':574,
        'local_canonical_registry_verified':False,'canonical_graph_built':False,
        'claims_approved_as_KA':0,'identity_exact_matches_approved':0,
        'approved_KS':0,'canonical_identifiers_minted':0,
        'human_authority_signatures_verified':0,
        'runtime_sets_qualified':False,'public_release_authorized':False,
    }
    if (len(graph['nodes']),len(graph['candidate_statements']),len(graph['skos_internal_observations']))!=(41,85,61):
        raise AdvanceError('Graphe candidat incomplet')
    summary={
        'format':FORMAT,'branch':'unesco-mt1-10',
        'status':'PRIVATE_EDITORIAL_DECISIONS_APPLIED_DRAFTS_READY_CANONICAL_BLOCKED',
        'editorial_decisions_taken_by_ChatGPT':191,
        'editorial_identity_anchors_retained':41,'candidate_wikidata_crosswalks':36,
        'skos_internal_relations_retained':61,'external_skos_observations_retained':112,
        'editorial_claims_selected':85,'rewritten_claims_used_in_private_previews':10,
        'legal_claims_needing_primary_evidence':3,
        'private_english_concept_previews':41,'multilingual_projection_slots_planned_not_realized':574,
        'human_decisions_still_pending':sum(v['decision']=='PENDING' for group in decisions.values() for v in group.values()),
        'canonical_KQ_KP_KA_KS_created':0,'canonical_kristal_built':False,
        'articles_generated':0,'git_push':False,'public_release_authorized':False,
        'next':'Real UNESCO-bound Kit v11 workspace plus attested KS/registry identities and authorized review; then GF/SemantiK realization and C1-C4',
    }
    inputs={
        'stage11_manifest_sha256':sha((stage11/'MANIFESTE_PASSE_GLOBALE.json').read_bytes()),
        'stage12_manifest_sha256':sha((stage12/'MANIFESTE_OVERLAY_ETAPE12.json').read_bytes()),
        'stage13_manifest_sha256':sha((stage13/'MANIFESTE_PONT_V11.json').read_bytes()),
        'review_sha256':sha((stage12/'MANIFESTE_RECOMMANDATIONS.json').read_bytes()),
        'mutable_human_decisions_sha256':{k:sha((stage11/k).read_bytes()) for k in (
            'DECISIONS_41_IDENTITES_EDITABLE.csv','DECISIONS_85_PROPOSITIONS_EDITABLE.csv',
            'DECISIONS_61_RELATIONS_EDITABLE.csv','DECISIONS_4_SOURCES_CONCEPT10_EDITABLE.csv')},
    }
    files={
        'DECISIONS_EDITORIALES_191_CHATGPT_NON_SIGNEES.json':json_bytes(positions),
        'KRISTALIZER_CONTROLE_EDITORIAL_V14.json':json_bytes(gate),
        'KRISTAL_CANDIDAT_EDITORIAL_PRIVE.json':json_bytes(graph),
        'RAPPORT_EDITIONS_V14.json':json_bytes(summary),
    }
    files.update(previews)
    files['MANIFESTE_EDITORIAL_V14.json']=json_bytes({
        'format':'koa.unesco-mt1-10-private-editorial-manifest/1.0',
        'branch':'unesco-mt1-10','source_anchors_sha256':inputs,
        'files_sha256':{k:sha(v) for k,v in sorted(files.items())},
        'canonical_created':0,'publication_authorized':False})
    return summary,files

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--work',type=Path,default=DEFAULT_WORK)
    a.add_argument('--repo-root',type=Path,default=DEFAULT_ROOT)
    a.add_argument('--check-only',action='store_true')
    args=a.parse_args(argv)
    summary,files=make(args.work,args.repo_root)
    out=args.work/OUT
    if args.check_only and (not out.is_dir() or any(not (out/name).is_file() for name in files)):
        raise AdvanceError('Dossier V14 encore absent ou incomplet : audit impossible')
    op,existing=publish_new_files(out,files,check_only=args.check_only)
    print(json.dumps({**summary,'operation':op,'existing_files':existing,'out':str(out)},ensure_ascii=False,indent=2,sort_keys=True))
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except (AdvanceError,ReviewError,ValueError,TypeError,KeyError,OSError,UnicodeError,json.JSONDecodeError) as exc:
        print('AVANCEMENT EDITORIAL V14 BLOQUE SANS CANON: '+str(exc),file=sys.stderr);sys.exit(2)
