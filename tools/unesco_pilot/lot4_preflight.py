"""Verify cumulative Lots 1-3 plus patched local semantic-stage Lot 4.

Does not open network, execute AI, create KQ/KA/KS or publish to GitHub.
"""
from __future__ import annotations
import argparse,hashlib,json,re,sys
from pathlib import Path
from cumulative_preflight import check as check_cumulative

FORMAT='koa.unesco-mt1-10-lot4-preflight/1.0'
MANIFEST='UNESCO_MT1_10_LOT4_SHA256.json'
PATH=re.compile(r'^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$')

def check(root:Path):
    root=root.resolve()
    base=check_cumulative(root)
    problems=list(base.get('problems',[]))
    names={}
    try:
        p=root/MANIFEST
        if not p.is_file() or p.stat().st_size>50000:raise ValueError('Lot 4 manifest missing or oversized')
        obj=json.loads(p.read_text(encoding='utf8'))
        if (obj.get('format')!='koa.unesco-mt1-10-lot4-integrity/1.0' or
            obj.get('branch')!='unesco-mt1-10' or obj.get('public_release_authorized') is not False or
            obj.get('repo_files_modified')!=['EncyKlopedia','Skope','Kristalizer']):
            raise ValueError('Unexpected Lot 4 authority or scope')
        names=obj['file_sha256']
        if not isinstance(names,dict) or len(names)!=8:raise ValueError('Unexpected Lot 4 file count')
        for rel,expected in names.items():
            if not isinstance(rel,str) or not PATH.fullmatch(rel) or not re.fullmatch(r'[a-f0-9]{64}',str(expected)):
                problems.append('Invalid Lot 4 manifest path/digest: '+str(rel));continue
            q=root/rel
            if q.is_symlink() or not q.is_file() or hashlib.sha256(q.read_bytes()).hexdigest()!=expected:
                problems.append('Lot 4 missing/changed: '+rel)
    except (OSError,ValueError,KeyError,TypeError) as e:
        problems.append('Lot 4 manifest: '+str(e))
    return {'format':FORMAT,'branch':'unesco-mt1-10','cumulative_installation_valid':base['installation_contracts_valid'],
            'base_manifest_file_count':base['manifest_file_count'],
            'base_repositories_valid':base['repositories_status_valid'],
            'lot4_files_verified':len(names),'public_release_authorized':False,
            'canonical_KA_approved':False,'languages_qualified':False,
            'status':'INSTALLATION_VALID_PRIVATE_STAGE_ONLY' if not problems else 'BLOCKED',
            'problems':problems}

def main(argv=None):
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--root',type=Path,default=Path(r'C:\mycode'))
    args=a.parse_args(argv)
    try:
        result=check(args.root)
        print(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2))
        return 0 if not result['problems'] else 2
    except (OSError,ValueError,TypeError) as e:
        print(json.dumps({'status':'BLOCKED','error':str(e),'public_release_authorized':False}),file=sys.stderr)
        return 2
if __name__=='__main__':raise SystemExit(main())
