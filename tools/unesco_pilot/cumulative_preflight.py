"""Read-only local installation checker for UNESCO mt1.10 cumulative Lots 1+2+3.

This hashes the exact installed overlay files, checks the 13 coordination
manifests and critical non-publication flags, and reports status. It neither
validates real semantic assertions nor certifies grammar/runtime availability.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from repo_preflight import RELATIVE_REPOS, LOCALES

MANIFEST='UNESCO_MT1_10_CUMULATIF_SHA256.json'
STATUS='koa.unesco-mt1-10-lot3-repository-status/1.0'
PATH_RE=re.compile(r'^(?!/)(?!.*\\)(?!.*(?:^|/)\.\.(?:/|$))[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$')


def check(root:Path,manifest_path:Path|None=None):
    root=root.resolve()
    manifest_path=manifest_path or root/MANIFEST
    problems=[]
    try:
        if not manifest_path.is_file() or manifest_path.stat().st_size>400_000:
            raise ValueError('Missing or oversized cumulative manifest')
        m=json.loads(manifest_path.read_text('utf8'))
        if (m.get('format')!='koa.unesco-mt1-10-cumulative-integrity/1.0' or
            m.get('branch')!='unesco-mt1-10' or m.get('lots')!=[1,2,3] or
            m.get('repositories_expected')!=13):
            raise ValueError('Unexpected cumulative manifest')
        files=m.get('file_sha256')
        if not isinstance(files,dict) or not files:
            raise ValueError('No overlay file fingerprints')
        for rel,expected in files.items():
            if not isinstance(rel,str) or not PATH_RE.fullmatch(rel) or not isinstance(expected,str) or not re.fullmatch(r'[0-9a-f]{64}',expected):
                problems.append('Unsafe or malformed digest record: '+str(rel));continue
            p=root/rel
            if p.is_symlink() or not p.is_file():
                problems.append('Missing or symlinked: '+rel);continue
            if hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
                problems.append('SHA mismatch: '+rel)
    except (OSError,ValueError,TypeError,KeyError) as exc:
        problems.append('Cumulative manifest: '+str(exc))
    repo_status={}
    for repo,relative in RELATIVE_REPOS.items():
        p=root/relative/'integrations/unesco-mt1-10/lot3-status.json'
        try:
            d=json.loads(p.read_text('utf8'))
            grain=d.get('semantic_grain')
            if (d.get('format')!=STATUS or d.get('repo')!=repo or d.get('local_relative_path')!=relative or
                d.get('branch')!='unesco-mt1-10' or d.get('unesco_seed_concepts')!=41 or
                d.get('target_locales')!=list(LOCALES) or d.get('status')!='LOCAL_PRIVATE_RESEARCH_AND_PROJECTIONS_ONLY' or
                not isinstance(grain,dict) or grain.get('one_branch_kristal') is not True or
                grain.get('articles_are_projections') is not True or grain.get('one_kristal_per_locale') is not False or
                grain.get('one_kristal_per_concept') is not False or
                any(d.get(flag) is not False for flag in (
                    'automatic_exact_match','automatic_canonical_minting','ai_training_as_source_KS',
                    'wikipedia_content_license_cleared','verified_14_language_runtimes',
                    'github_publication_enabled','independent_release_approval_verified'))):
                problems.append('Unsafe or inconsistent repo status: '+repo)
            else:repo_status[repo]='LOCAL_PRIVATE_ONLY'
        except (OSError,ValueError,TypeError):
            problems.append('Missing/malformed repo status: '+repo)
    return {'format':'koa.unesco-mt1-10-cumulative-preflight/1.0',
            'lots':[1,2,3],'repositories_expected':13,'repositories_status_valid':len(repo_status),
            'manifest_file_count':len(m.get('file_sha256',{})) if 'm' in locals() and isinstance(m,dict) else 0,
            'installation_contracts_valid':not problems,
            'private_semantic_pipeline_only':True,
            'canonical_assertions_qualified_by_preflight':False,
            'multilingual_runtimes_qualified_by_preflight':False,
            'public_release_authorized':False,
            'status':'INSTALLATION_VALID_PUBLICATION_BLOCKED' if not problems else 'BLOCKED',
            'problems':problems}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(r'C:\mycode'))
    p.add_argument('--manifest',type=Path)
    a=p.parse_args(argv)
    try:
        d=check(a.root,a.manifest)
        print(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True))
        return 0 if d['installation_contracts_valid'] else 2
    except (OSError,ValueError,TypeError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc),'public_release_authorized':False},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
