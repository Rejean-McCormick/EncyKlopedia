#!/usr/bin/env python3
"""Export explicite d'artefacts de lecture pour revue IA hors Spek.

Il ne modifie aucun Kristal et ne contacte aucun réseau.
Mode par défaut : manifeste seulement. --include-content requiert une action humaine.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

PATHS=(
  'kristal.workspace.json',
  'canon/state.index.json',
  '.kristal/v8/portable-state.kristal-state.json',
  '.kristal/v11/semantic-graph.json',
  'state/state-snapshot.json',
  'knowledge-base/corpus/index.json',
)
LIMIT_PER_FILE=20_000_000

def build_manifest(spek_root:Path, locals_root:Path) -> list[dict]:
    proposals=json.loads((spek_root/'template_library/wiki/kristal-ai-proposals.json').read_text(encoding='utf-8'))['proposals']
    rows=[]
    for slug,p in sorted(proposals.items()):
        if p.get('canonical_review_status')!='AWAITING_CANONICAL_CONTENT':
            continue
        relative=Path(p['source_workspace_relative'])
        if (relative.is_absolute() or len(relative.parts)!=1 or any(part in {'..','.'} for part in relative.parts)):
            rows.append({'slug':slug,'folder':str(relative),'status':'INVALID_WORKSPACE_PATH','files':[]})
            continue
        folder=locals_root/relative
        if folder.is_symlink() or not folder.resolve(strict=False).is_relative_to(locals_root):
            rows.append({'slug':slug,'folder':str(relative),'status':'UNSAFE_WORKSPACE_PATH','files':[]})
            continue
        files=[]
        for rel in PATHS:
            file=folder/rel
            if not file.is_file() or file.is_symlink():continue
            size=file.stat().st_size
            if size > LIMIT_PER_FILE:
                files.append({'relative':rel,'status':'SKIPPED_TOO_LARGE','bytes':size})
                continue
            files.append({'relative':rel,'status':'AVAILABLE','bytes':size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
        rows.append({'slug':slug,'folder':p['source_workspace_relative'],'status':'AVAILABLE' if files else 'NO_RECOGNIZED_ARTIFACT','files':files})
    return rows

def main(args=None)->int:
    ap=argparse.ArgumentParser(description='Préparer un bundle privé pour revue IA des Kristals restants')
    ap.add_argument('--root',required=True,help='Racine des locaux Kristal (lecture seule)')
    ap.add_argument('--out',required=True,help='Répertoire de sortie différent de locals')
    ap.add_argument('--include-content',action='store_true',help='Inclure les contenus JSON; vérifier leur confidentialité avant partage')
    a=ap.parse_args(args)
    root=Path(a.root).expanduser().resolve(); out=Path(a.out).expanduser().resolve()
    if not root.is_dir():ap.error('Racine des Kristals absente')
    if out==root or root in out.parents:ap.error('La sortie doit être hors du dossier locals')
    repo=Path(__file__).resolve().parents[1]
    rows=build_manifest(repo,root)
    out.mkdir(parents=True,exist_ok=True)
    manifest={'format':'spek.private-review-source-bundle/1.0','publisher':'NONE','read_only':True,'source_root':str(root),'content_included':a.include_content,'kristals':len(rows),'entries':rows}
    target=out/('SPEK_SOURCES_PRIVÉES_122_A_VERIFIER.zip' if a.include_content else 'SPEK_INVENTAIRE_SOURCES_122.zip')
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zipf:
        zipf.writestr('MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        zipf.writestr('CONFIDENTIALITE_AVANT_PARTAGE.txt','ATTENTION : le mode --include-content peut contenir des assertions et des informations privées.\nVérifier le contenu avant tout partage. Aucun fichier ne doit être publié automatiquement.\n')
        if a.include_content:
            for row in rows:
                for f in row['files']:
                    if f['status']!='AVAILABLE':continue
                    source=root/row['folder']/f['relative']
                    if source.is_symlink() or source.stat().st_size > LIMIT_PER_FILE:continue
                    arc=f"{row['folder']}/{f['relative']}"
                    zipf.write(source,arcname=arc)
    print(target)
    print('Kristals:',len(rows),'avec fichiers:',sum(any(f['status']=='AVAILABLE' for f in r['files']) for r in rows),'contenu inclus:',a.include_content)
    return 0

if __name__=='__main__':sys.exit(main())
