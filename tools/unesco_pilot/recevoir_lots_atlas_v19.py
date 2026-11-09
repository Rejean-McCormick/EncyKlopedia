#!/usr/bin/env python3
"""Append-only, NON CANONICAL intake for ChatGPT documentary research batches.

This is NOT a replacement for Kristalizer/Authoring Kit admission.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile

DEFAULT_BASE=Path(r'D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41')
DEFAULT_LEDGER=DEFAULT_BASE/'atlas_documentaire_v19_candidats'
FORMAT='koa.unesco-documentary-proposals/1.0'


def sha(b:bytes):return hashlib.sha256(b).hexdigest()

def jb(o):return (json.dumps(o,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')


def validate_batch(batch:Path):
    with zipfile.ZipFile(batch) as z:
        names=set(z.namelist())
        if 'LOT_MANIFEST.json' not in names:raise ValueError('LOT_MANIFEST.json absent du ZIP')
        raw=z.read('LOT_MANIFEST.json');m=json.loads(raw)
        if m.get('format')!='koa.unesco-wikipedia-chatgpt-research-batch/1.0' or m.get('branch')!='unesco-mt1-10':
            raise ValueError('Lot ChatGPT de mauvaise branche ou version')
        anchor_name='atlas/ancrages_kristal_stables.json'
        if anchor_name not in names:
            raise ValueError('Ancrages UNESCO stables absents du lot')
        anchor_doc=json.loads(z.read(anchor_name))
        if anchor_doc.get('branch')!='unesco-mt1-10' or len(anchor_doc.get('anchors',[]))!=41:
            raise ValueError('Carte des 41 ancrages absente ou invalide')
        anchors={r['unesco_id'] for r in anchor_doc['anchors']}
        if len(anchors)!=41:raise ValueError('Ancrages UNESCO dupliqués')
        allowed={}
        for item in m['items']:
            pid=int(item['page_id'])
            if pid in allowed:raise ValueError('Page dupliquée dans le lot')
            if item['status']=='TEXT_EXTRACTED':
                name=item['text_relative_path']
                if name not in names or not name.startswith('articles/page-') or '..' in Path(name).parts:
                    raise ValueError('Texte absent ou chemin dangereux : '+str(pid))
                if sha(z.read(name))!=item['text_sha256']:
                    raise ValueError('Empreinte du texte divergente : '+str(pid))
            allowed[pid]=item
        return m,sha(raw),allowed,anchors


def validate_changeset(batch:Path, doc:Path):
    m,bhash,allowed,anchors=validate_batch(batch)
    r=json.loads(doc.read_text(encoding='utf-8-sig'))
    if r.get('format')!=FORMAT or r.get('branch')!='unesco-mt1-10':
        raise ValueError('Contrat de propositions incompatible')
    if r.get('batch_manifest_sha256')!=bhash:
        raise ValueError('Le fichier IA ne correspond pas au lot source')
    entries=r.get('proposals')
    if not isinstance(entries,list) or not entries:
        raise ValueError('Au moins une proposition explicite est nécessaire')
    seen=set();out=[]
    for item in entries:
        cid=item.get('candidate_id','')
        if not isinstance(cid,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{3,90}',cid):
            raise ValueError('candidate_id invalide')
        if cid in seen:raise ValueError('candidate_id dupliqué : '+cid)
        seen.add(cid)
        concept=item.get('unesco_id')
        if not isinstance(concept,str) or concept not in anchors:
            raise ValueError('Ancrage UNESCO absent ou invalide')
        pid=item.get('source_page_id')
        if not isinstance(pid,int) or pid not in allowed or allowed[pid]['status']!='TEXT_EXTRACTED':
            raise ValueError('Source non extraite dans ce lot : '+str(pid))
        text=item.get('statement','')
        locator=item.get('source_locator','')
        if not isinstance(text,str) or len(text.strip())<12 or len(text)>2400:
            raise ValueError('Proposition absente ou trop longue : '+cid)
        if not isinstance(locator,str) or not locator.strip() or len(locator)>400:
            raise ValueError('Localisateur source nécessaire : '+cid)
        rev=str(item.get('source_revision_id',''))
        if rev!=str(allowed[pid].get('text_revision_id','')):
            raise ValueError('Révision source divergente : '+cid)
        out.append({'candidate_id':cid,'unesco_id':concept,'source_page_id':pid,
                    'source_revision_id':rev,'source_text_sha256':allowed[pid]['text_sha256'],
                    'source_locator':locator.strip(),'statement':text.strip(),
                    'attribution':item.get('attribution','Wikipédia EN, texte de recherche non vérifié'),
                    'evidence_status':'UNVERIFIED_WIKIPEDIA_CONTEXT',
                    'semantic_status':'AI_CANDIDATE_NOT_CANONICAL',
                    'no_approved_KQ_KP_KA_KS':True})
    return {'format':'koa.unesco-documentary-candidate-ledger/1.0','branch':'unesco-mt1-10',
            'batch_manifest_sha256':bhash,'candidates':out,
            'canonical_KQ_KP_KA_KS_created':0,'publication_authorized':False}


def stage(args):
    batch=Path(args.batch); doc=Path(args.proposals);root=Path(args.ledger)
    payload=validate_changeset(batch,doc)
    data=jb(payload);digest=sha(data)
    path=root/(digest+'.json')
    root.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if sha(path.read_bytes())!=digest:raise ValueError('Entrée du ledger altérée')
        state='DEJA_PRESENT'
    else:
        with tempfile.NamedTemporaryFile(dir=root,prefix='.atlas_intake_',delete=False) as temp:
            temp.write(data);tmp=Path(temp.name)
        try:tmp.rename(path)
        finally:
            if tmp.exists():tmp.unlink()
        state='CANDIDATS_PRIVATE_LEDGER_ADDED'
    print(json.dumps({'status':state,'file':str(path),
                      'new_candidate_records':len(payload['candidates']),
                      'canonical_admissions':0},ensure_ascii=False,indent=2))


def report(args):
    root=Path(args.ledger)
    total=0;files=0;per_concept=Counter();uids=set();exact_claims=set()
    for f in sorted(root.glob('*.json')) if root.is_dir() else []:
        raw=f.read_bytes()
        if sha(raw)!=f.stem:raise ValueError('Altération détectée : '+f.name)
        d=json.loads(raw)
        if d.get('format')!='koa.unesco-documentary-candidate-ledger/1.0':continue
        files+=1
        for c in d.get('candidates',[]):
            total+=1;per_concept[c['unesco_id']]+=1
            uids.add((d['batch_manifest_sha256'],c['candidate_id']))
            exact_claims.add((c['unesco_id'],c['statement'].casefold().strip(),c['source_page_id']))
    print(json.dumps({'status':'PRIVATE_CANDIDATE_LEDGER_AUDITED','intake_files':files,
                      'candidate_records':total,'unique_candidate_keys':len(uids),
                      'unique_statement_source_combinations':len(exact_claims),
                      'concepts_with_proposals':len(per_concept),
                      'canonical_admissions':0,'publication_authorized':False},ensure_ascii=False,indent=2))


def main(argv=None):
    p=argparse.ArgumentParser(description='Réception append-only des propositions ChatGPT, jamais canonique')
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('intake');a.add_argument('--batch',required=True);a.add_argument('--proposals',required=True)
    a.add_argument('--ledger',default=str(DEFAULT_LEDGER))
    a=sub.add_parser('report');a.add_argument('--ledger',default=str(DEFAULT_LEDGER))
    args=p.parse_args(argv)
    try:
        stage(args) if args.command=='intake' else report(args)
        return 0
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as e:
        print(json.dumps({'status':'REFUS_ENTREE_NON_CANONIQUE','error':str(e)},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
