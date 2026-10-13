"""Skope intégré à EncyK : CLI index partagé, sans importeur Wikidata concurrent."""
import argparse
import json
from pathlib import Path
from contextlib import closing
from .arketype import load_guidance
from .api import serve
from .db import connect,meta
from .scope import explore
from .export import bundle

TOOL=Path(__file__).resolve().parents[1]
ROOT=TOOL.parents[2]
DEFAULT_DB=ROOT/'30_working/wikidata/wikidata.compact.sqlite'

def main(argv=None):
    p=argparse.ArgumentParser(description='Skope dans EncyKlopedia (lecture seule de l’index global)')
    subs=p.add_subparsers(dest='action',required=True)
    for cmd in ('serve','meta','preview','export'):
        q=subs.add_parser(cmd)
        q.add_argument('--db',default=str(DEFAULT_DB))
        if cmd in ('preview','export'):q.add_argument('--recipe',required=True)
        if cmd=='export':
            q.add_argument('--out',required=True)
            q.add_argument('--scope-key',default=None)
            q.add_argument('--guidance',default=None,help='Guide Arketype v1.4 non canonique facultatif')
        if cmd=='serve':
            q.add_argument('--kristal',default=None,help='Dossier du Kristal cible ; lecture seule')
            q.add_argument('--recipe',default=None)
            q.add_argument('--guidance',default=None)
            q.add_argument('--host',default='127.0.0.1')
            q.add_argument('--port',default=8767,type=int)
    args=p.parse_args(argv)
    if args.action=='serve':serve(args.db,args.host,args.port,args.recipe,args.guidance,args.kristal);return
    with closing(connect(args.db)) as db:
        if args.action=='meta': result=meta(db)
        else:
            recipe=json.loads(Path(args.recipe).read_text(encoding='utf-8-sig'))
            if args.action=='preview':result=explore(db,recipe)
            else:
                dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(bundle(db,recipe,args.scope_key,load_guidance(args.guidance)))
                result={'file':str(dest),'status':'working_non_canonical','raw_evidence_included':False}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
