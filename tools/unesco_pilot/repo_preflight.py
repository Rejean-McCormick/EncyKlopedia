"""Verify UNESCO mt1.10 additive handoff files in 13 *local* checkouts.

This checks presence/shape only. Passing does NOT qualify semantics, 14 GF
languages, license review, publication rights, GitHub uploads, or activation.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
import sys

RELATIVE_REPOS={
    'Skope':'Skope/Skope',
    'Kristalizer':'Kristal/Kristalizer',
    'diK':'diK/diK',
    'Kristal-Framework':'Kristal/Kristal-Framework',
    'Kristal-Authoring-Kit':'Kristal/Kristal-Authoring-Kit',
    'Kristal-Manager':'Kristal/Kristal-Manager',
    'Kristal-Integration-Pack':'Kristal/Kristal-Integration-Pack',
    'SemantiK_Architect':'SemantiK_Architect/SemantiK_Architect',
    'SemantiK_Runtime_Orchestrator':'SemantiK_Architect/SemantiK_Runtime_Orchestrator',
    'Spek':'Spek_Semantic-publishing/Spek',
    'EncyKlopedia':'EncyKlopedia/EncyKlopedia',
    'kristal-public':'Kristal/kristal-public',
    'Konstellation-Publisher':'Konstellation/Konstellation-Publisher',
}
LOCALES=('en','fr','es','de','nl','sv','da','no','nn','fi','et','af','it','pt')
REQUIRED_INVARIANTS=('automatic_exact_match','automatic_canonical_write','public_upload_authorized','public_deployment_authorized')


def inspect(base:Path, *, snapshot_layout:bool=False):
    problems=[]; details=[]
    for repo,relative in RELATIVE_REPOS.items():
        path=base / (repo if snapshot_layout else relative)
        handoff=path/'integrations'/'unesco-mt1-10'/'handoff.json'
        info={'repo':repo,'local_path':str(path),'manifest_exists':handoff.is_file()}
        if not handoff.is_file():
            problems.append(f'{repo}: missing {handoff}')
            details.append(info);continue
        try:
            d=json.loads(handoff.read_text(encoding='utf8'))
            if d['schema']!='koa.unesco-mt1-10-repo-handoff/1.0' or d['repo']!=repo:
                problems.append(f'{repo}: invalid schema or repo name')
            if d['branch']!='unesco-mt1-10' or d['baseline_concept_count']!=41:
                problems.append(f'{repo}: unexpected branch or concept count')
            if d['target_locales']!=list(LOCALES):
                problems.append(f'{repo}: divergent locale contract')
            grain=d['semantic_grain']
            if not grain['one_branch_kristal'] or not grain['articles_are_projections'] or grain['one_kristal_per_language'] or grain['one_kristal_per_concept']:
                problems.append(f'{repo}: invalid semantic granularity')
            if any(d[k] is not False for k in REQUIRED_INVARIANTS):
                problems.append(f'{repo}: unsafe automatic approval or public upload flag')
            if d['current_gate']!='CANDIDATE_INTEGRATION_ONLY':
                problems.append(f'{repo}: publication authorization changed')
            info['role']=d['component_role']
            info['status']='STAGED_CANDIDATE_ONLY'
        except (KeyError,TypeError,ValueError,json.JSONDecodeError) as exc:
            problems.append(f'{repo}: malformed contract: {exc}')
        details.append(info)
    return {
      'format':'koa.unesco-mt1-10-coordination-preflight/1.0',
      'branch':'unesco-mt1-10','repos_expected':13,
      'repos_present':sum(1 for x in details if x['manifest_exists']),
      'installation_contracts_valid':not problems,
      'ready_for_publication':False,'language_14_qualified':False,
      'canonical_41_approved':False,
      'known_compatibility_followups':[
          'diK alpha.7 Framework v11 draft.3 vs Framework/Integration Pack draft.4: compare exact source pins and requalify',
          'SemantiK Architect v6/v7 articulation must be explicitly tested with v11 derived views',
          'SemantiK RuntimeSets and Spek output have not been qualified for 14 languages',
          'Manager and kristal-public public GitHub synchronization remain sealed',
      ],
      'problems':problems,'repos':details,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(r'C:\mycode'))
    p.add_argument('--snapshot-layout',action='store_true',help='For unpacked snapshot-test directories only')
    a=p.parse_args(argv)
    r=inspect(a.root,snapshot_layout=a.snapshot_layout)
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return 0 if r['installation_contracts_valid'] else 2

if __name__=='__main__':raise SystemExit(main())
