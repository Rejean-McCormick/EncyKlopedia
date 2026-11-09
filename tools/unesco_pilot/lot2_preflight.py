"""Cross-repository UNESCO mt1.10 Lot 2 local preflight (NO release authority).

Checks the installed 13-repository contracts from Lot 1 and the actual source
pin / runtime checks of Lot 2. Does not mutate Framework, diK, Kristals, GitHub
or any D: store. Its only output is a JSON report printed to stdout.
"""
from __future__ import annotations
import argparse,importlib.util,json,sys
from pathlib import Path

from repo_preflight import inspect,RELATIVE_REPOS

NEW_TOOLS={
 'Skope':('tools/unesco_local_source_dossier.py',),
 'Kristalizer':('tools/unesco_ai_proposal_intake.py',),
 'diK': ('tools/unesco_framework_drift.py',),
 'EncyKlopedia':('tools/unesco_pilot/offline_xml_evidence.py',),
 'Kristal-Integration-Pack':('tools/unesco_mt1_10_view_bridge.py',),
 'SemantiK_Architect':('src/semantik_architect/adapters/ecosystem/unesco_v11.py','tools/unesco_v11_request.py'),
 'Spek':('spek/unesco_private_drafts.py',),
 'SemantiK_Runtime_Orchestrator':('tools/unesco_14_locale_readiness.py',),
}

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if not spec or not spec.loader:raise ValueError('Module missing: '+str(path))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def preflight(root:Path,*,runtime_root:Path):
    root=root.resolve()
    old=inspect(root)
    missing=[]
    for repo,tools in NEW_TOOLS.items():
        for tool in tools:
            p=root/RELATIVE_REPOS[repo]/tool
            if not p.is_file():missing.append(str(p))
    result={'format':'koa.unesco-mt1-10-lot2-preflight/1.0','branch':'unesco-mt1-10',
            'repositories_expected':13,
            'lot1_contracts_valid':old['installation_contracts_valid'],
            'lot2_tools_present':not missing,'missing_tools':missing,
            'framework_source_compatible':False,'framework_pin_verified':False,
            'runtime_attemptable_locales':0,'target_locales':14,
            'article_projection_qualified_locales':0,
            'publication_authorized':False,'status':'BLOCKED'}
    status_mismatches=[]
    for repo,relative in RELATIVE_REPOS.items():
        status_file=root/relative/'integrations/unesco-mt1-10/lot2-status.json'
        try:
            obj=json.loads(status_file.read_text('utf8'))
            if (obj.get('format')!='koa.unesco-mt1-10-lot2-repository-status/1.0' or
                obj.get('repo')!=repo or obj.get('local_relative_path')!=relative or
                obj.get('requested_languages')!=14 or obj.get('unesco_seed_concepts')!=41 or
                obj.get('status')!='INTEGRATION_CANDIDATE_NOT_PRODUCTION' or
                any(obj.get(k) is not False for k in (
                    'automatic_canonical_minting','source_evidence_approved',
                    'language_runtimes_all_qualified','remote_upload_authorized',
                    'publication_gates_passed'))):
                status_mismatches.append(repo)
        except (OSError,ValueError,TypeError):status_mismatches.append(repo)
    result['lot2_repository_status_valid']=not status_mismatches
    result['lot2_repository_status_invalid']=status_mismatches
    if missing or status_mismatches or not old['installation_contracts_valid']:
        result['problems']=old['problems']+missing+['Bad Lot2 status: '+x for x in status_mismatches]
        return result
    diK=load('unesco_drift',root/RELATIVE_REPOS['diK']/'tools/unesco_framework_drift.py')
    d=diK.inspect(framework=root/RELATIVE_REPOS['Kristal-Framework'],
                  diK=root/RELATIVE_REPOS['diK'],
                  integration_pack=root/RELATIVE_REPOS['Kristal-Integration-Pack'])
    result['framework_source_compatible']=d['upstream_source_unchanged_for_dik_subset']
    result['framework_pin_verified']=d['pinned_framework_verified']
    result['framework_source_files_matched']=d['source_files_matched']
    result['framework_source_files_compared']=d['source_files_compared']
    runtime=load('unesco_runtime',root/RELATIVE_REPOS['SemantiK_Runtime_Orchestrator']/'tools/unesco_14_locale_readiness.py')
    cov=runtime.audit(runtime_root)
    result['runtime_attemptable_locales']=cov['runtime_artifact_attemptable']
    result['runtime_blocked_locales']=cov['runtime_artifact_blocked']
    result['source_extraction_can_be_attempted']=bool(d['pinned_framework_verified'] and d['upstream_source_unchanged_for_dik_subset'])
    result['problems']=([{'component':'diK vs Framework','detail':d['mismatches']}] if not result['framework_pin_verified'] else [])+[
       'Local runtime qualification and actual realized text have not been certified',
       'Canonical KQ/KA/KS and public rights/authorization must be independently reviewed']
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(r'C:\mycode'))
    p.add_argument('--runtime-root',type=Path,default=Path(r'D:\EncyKlopedia\30_working\semantik-runtime'))
    a=p.parse_args(argv)
    try:
        d=preflight(a.root,runtime_root=a.runtime_root)
        print(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2));return 0 if d['lot1_contracts_valid'] and d['lot2_tools_present'] and d['lot2_repository_status_valid'] and d['framework_pin_verified'] else 2
    except (OSError,ValueError,KeyError,ImportError) as e:
        print(json.dumps({'status':'BLOCKED','error':str(e),'publication_authorized':False},ensure_ascii=False),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
