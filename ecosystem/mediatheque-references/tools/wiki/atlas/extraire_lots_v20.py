#!/usr/bin/env python3
"""UNESCO v20: make a real 25-text ChatGPT ZIP from local Wikipedia XML.

Offline, bounded in memory, resume-safe, with a derived index only. Reuses the
v19 ZIP/atlas contract and its source-hash checks. No canonical operations.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import zipfile

import atlas_wikipedia as v19
from extraction_multistream_v20 import (DEFAULT_XML,DEFAULT_SIDECAR,
    VERSION as INDEX_VERSION, audit_index, ensure_offsets, signature, emit)

DEFAULT_ATLAS = v19.DEFAULT_OUT
DEFAULT_SELECTION = Path(__file__).with_name('SELECTION_UNESCO_ATLAS_V19_LOT_002_25_PAGES.csv')
DEFAULT_OUTPUT = v19.DEFAULT_WORK / 'atlas_documentaire_v19_LOT_002_CHATGPT.zip'
DEFAULT_CACHE = v19.DEFAULT_CACHE
RECEIPT_FORMAT = 'koa.unesco-wikipedia-lot-extraction-v20/1.0'
EXPECTED_PAGE_IDS = frozenset({2287044,10870972,9252,24983,22089591,31899,46945565,30631120,4378212,9384153,13323043,25572436,430890,2128182,4003872,479983,465183,214737,18456,436831,8997,1944675,375170,293121,2805394})


def checksum(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()


def json_bytes(v):
    return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')


def receipt_path(out:Path):
    return out.with_suffix(out.suffix+'.v20.json')


def verify_output(out:Path):
    receipt=receipt_path(out)
    if not out.is_file() or not receipt.is_file():
        raise ValueError('Lot V20 incomplet ou receipt absent : '+str(out))
    d=json.loads(receipt.read_text(encoding='utf-8'))
    if d.get('format')!=RECEIPT_FORMAT or checksum(out)!=d.get('zip_sha256'):
        raise ValueError('Empreinte du ZIP V20 non conforme')
    with zipfile.ZipFile(out) as z:
        manifest=json.loads(z.read('LOT_MANIFEST.json'))
        if manifest['branch']!='unesco-mt1-10':
            raise ValueError('Lot hors branche UNESCO')
        extracted=[x for x in manifest['items'] if x['status']=='TEXT_EXTRACTED']
        if len(manifest['items'])!=d['pages_selected'] or len(extracted)!=d['texts_extracted']:
            raise ValueError('Compte des textes du ZIP V20 incohérent')
        for it in extracted:
            rel=it['text_relative_path']
            if rel not in z.namelist() or v19.sha(z.read(rel))!=it['text_sha256']:
                raise ValueError('Texte du ZIP modifié : '+str(it['page_id']))
        if len(extracted)!=len(manifest['items']):
            raise ValueError('ZIP V20 incomplet : '+str(len(manifest['items'])-len(extracted))+' texte(s) manquant(s)')
    return {'status':'LOT_V20_INTEGRITE_VERIFIEE','output':str(out),
            'pages_selected':len(manifest['items']),'texts_extracted':len(extracted),
            'revision_mismatches':d['revision_mismatches'], 'source_index':d['index_kind'],
            'zip_sha256':d['zip_sha256'],'no_canonical_changes':True}


def source_and_index(args):
    xml=Path(args.xml)
    if not xml.is_file():
        raise ValueError('Fichier XML multistream introuvable : '+str(xml)+
                         ' ; indiquer son chemin avec --xml')
    official=Path(args.official_index) if args.official_index else None
    if official is None and not args.force_reconstruct:
        stem=xml.name.removesuffix('.xml.bz2')
        for n in (stem+'-index.txt.bz2',stem+'-index.txt'):
            candidate=xml.with_name(n)
            if candidate.is_file():official=candidate;break
    if official and not official.is_file():
        raise ValueError('Index officiel explicitement indiqué mais absent : '+str(official))
    return xml,official


def read_context(args):
    atlas=Path(args.atlas)
    validation=v19.audit(atlas)
    selection=Path(args.selection)
    if not selection.is_file():
        raise ValueError('Sélection lot 002 absente : '+str(selection))
    selected,allowed=v19.load_selection(atlas,selection,100)
    if not 1<=len(selected)<=100 or len(set(selected))!=len(selected):
        raise ValueError('Sélection V20 invalide : 1 à 100 pages uniques attendues')
    if args.future_lot:
        if selection.resolve()==DEFAULT_SELECTION.resolve() or Path(args.output)==DEFAULT_OUTPUT:
            raise ValueError('Pour un futur lot, préciser --selection CSV et --output ZIP distincts du lot 002')
    elif len(selected)!=25 or set(selected)!=EXPECTED_PAGE_IDS:
        raise ValueError('Lot 002 V20 : sélection éditoriale exacte des 25 pages attendue; --future-lot pour les lots suivants')
    import csv
    with selection.open(encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            if str(row.get('selected','')).strip().lower() not in ('1','yes','oui','true','y'):
                continue
            known=allowed[int(row['page_id'])]
            if any(str(row.get(k,''))!=str(known.get(k,''))
                   for k in ('title','revision_id','qid')):
                raise ValueError('Sélection éditoriale divergente de l’atlas v19 : '+str(row['page_id']))
    return atlas,selection,selected,allowed,validation


def index_offsets(xml,official,selected,allowed,args):
    # Official index path is normally faster and needs no derived SQLite.
    if official:
        values=v19.index_offsets(official,set(selected))
        not_found=sorted(set(selected)-set(values))
        if not_found:
            raise ValueError('Index multistream fourni sans les pages sélectionnées : '+str(not_found))
        return values,'WIKIMEDIA_OFFICIAL_INDEX',{'index_path':str(official),
                     'index_size':official.stat().st_size,'index_sha256':checksum(official)},None
    result=ensure_offsets(xml,Path(args.sidecar),set(selected),args.max_streams,args.progress_every)
    if result['status']!='OFFSETS_READY':
        emit(status=result['status'],indexed_bytes=result['checkpoint'],
             compressed_total_bytes=result['xml_signature']['bytes'],
             ids_indexed=result.get('page_ids_indexed'),missing_page_ids=result.get('missing',[]),
             continue_command='Relancer exactement le meme lanceur; le checkpoint est conserve')
        return None,'LOCAL_RECONSTRUCTED_INDEX',result,result['status']
    return result['offsets'],'LOCAL_RECONSTRUCTED_INDEX',{
        'sidecar_path':str(Path(args.sidecar)), 'index_complete':result['complete'],
        'checkpoint':result['checkpoint'],'page_ids_indexed':result['page_ids_indexed'],
        'streams_indexed':result['streams_indexed']},None


def preflight(args):
    atlas,selection,selected,allowed,_=read_context(args)
    xml,official=source_and_index(args)
    info={'status':'V20_PREREQUIS_VERIFIES','branch':'unesco-mt1-10',
          'atlas':str(atlas),'selection':str(selection),'selected_pages':len(selected),
          'xml_signature':signature(xml),
          'index_strategy':('OFFICIAL_EXISTING' if official else 'RECONSTRUCT_LOCAL_RESUMABLE'),
          'official_index':str(official) if official else None,
          'sidecar_index':str(Path(args.sidecar)) if not official else None,
          'target_output':str(Path(args.output)),'original_sqlite':'READ_ONLY_NO_CHANGES',
          'canonical_kristal':'UNCHANGED'}
    if not official and Path(args.sidecar).exists():
        info['local_index']=audit_index(xml,Path(args.sidecar))
    return info


def safe_emit_status(out,info):
    path=out.with_suffix(out.suffix+'.v20_status.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_bytes(json_bytes(info));tmp.replace(path)


def build(args):
    atlas,selection,selected,allowed,_=read_context(args)
    xml,official=source_and_index(args)
    out=Path(args.output)
    if out.exists() or receipt_path(out).exists():
        v=verify_output(out)
        old=json.loads(receipt_path(out).read_text(encoding='utf-8'))
        if (old.get('selection_sha256')!=checksum(selection) or
            old.get('atlas_manifest_sha256')!=checksum(atlas/'manifest.json') or
            old.get('xml_signature')!=signature(xml)):
            raise ValueError('Entrées modifiées depuis ce lot : utiliser un nouveau --output')
        v['operation']='REPRISE_IDENTIQUE';return v
    values,index_kind,index_info,unfinished=index_offsets(xml,official,selected,allowed,args)
    if unfinished:
        safe_emit_status(out,{'status':unfinished,'page_ids_missing':index_info.get('missing',[]),
                              'checkpoint':index_info.get('checkpoint'),
                              'xml_signature':index_info.get('xml_signature'),
                              'sidecar_index':str(Path(args.sidecar)),
                              'result_zip_created':False})
        return {'status':unfinished,'output_not_created':str(out),
                'remaining_page_ids':index_info.get('missing',[]),
                'continue_by_rerunning':True}
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.unesco_v20_',dir=out.parent) as t:
        tmp=Path(t)
        # The source of offsets is the official index OR our separately derived
        # indexed SQLite. The v19 pack consumes the same official line contract.
        sparse=tmp/'selected_multistream_offsets.txt'
        sparse.write_text(''.join(f'{values[p]}:{p}:{allowed[p]["title"]}\n'
                           for p in sorted(selected,key=lambda q:(values[q],q))),encoding='utf-8')
        intermediate=tmp/'LOT_002_VERIFICATION.zip'
        argv=['pack','--atlas',str(atlas),'--selection',str(selection),
              '--output',str(intermediate),'--limit',str(len(selected)),'--cache',str(args.cache),
              '--try-multistream','--xml',str(xml),'--multistream-index',str(sparse)]
        if v19.main(argv):
            raise ValueError('La création du lot v19 a échoué; aucun ZIP final créé')
        with zipfile.ZipFile(intermediate) as z:
            d=json.loads(z.read('LOT_MANIFEST.json'))
            if d.get('selected_pages')!=len(selected) or [int(x['page_id']) for x in d['items']]!=selected:
                raise ValueError('Ordre ou sélection du lot produits non conformes')
            missing=[{'page_id':x['page_id'],'title':x['title'],'reason':x.get('reason')}
                     for x in d['items'] if x['status']!='TEXT_EXTRACTED']
            mismatches=[{'page_id':x['page_id'],'title':x['title'],
                         'xml_revision':x.get('text_revision_id'),
                         'sql_revision':x.get('atlas_revision_id')}
                        for x in d['items'] if x.get('revision_mismatch_with_SQL')]
            if missing:
                safe_emit_status(out,{'status':'TEXTES_PARTIELS_AUCUN_ZIP_FINAL',
                                      'texts_found':len(selected)-len(missing),'missing':missing,
                                      'index_kind':index_kind,'xml_signature':signature(xml)})
                return {'status':'TEXTES_PARTIELS_AUCUN_ZIP_FINAL',
                        'missing':missing,'texts_available':len(selected)-len(missing),
                        'output_not_created':str(out)}
            for x in d['items']:
                content=z.read(x['text_relative_path'])
                if v19.sha(content)!=x['text_sha256']:
                    raise ValueError('Empreinte de texte incorrecte : '+str(x['page_id']))
        # Atomic final ZIP then receipt; never replace an existing version.
        if out.exists():raise FileExistsError('Sortie créée entretemps : '+str(out))
        shutil.copyfile(intermediate,out)
        receipt={'format':RECEIPT_FORMAT,'branch':'unesco-mt1-10',
                 'created_utc':datetime.now(timezone.utc).isoformat(),
                 'status':'LOT_V20_TEXTES_PRETS_POUR_CHATGPT',
                 'output':str(out),'zip_sha256':checksum(out),
                 'pages_selected':len(selected),'texts_extracted':len(selected),
                 'selection_sha256':checksum(selection),
                 'atlas_manifest_sha256':checksum(atlas/'manifest.json'),
                 'xml_signature':signature(xml),'index_kind':index_kind,'index_details':index_info,
                 'revision_mismatches':mismatches,
                 'no_new_KQ_KP_KA_KS':True,'no_canonical_changes':True,
                 'wikipedia_text_rights':'REQUIRES_CC_BY_SA_ATTRIBUTION_AND_REVISION_PROVENANCE',
                 'notes':'Private research batch; not canonical facts or official articles.'}
        r=receipt_path(out)
        temp=r.with_suffix(r.suffix+'.tmp')
        temp.write_bytes(json_bytes(receipt));temp.replace(r)
    v=verify_output(out)
    v['status']='LOT_V20_TEXTES_PRETS_POUR_CHATGPT'
    return v


def parse(argv=None):
    p=argparse.ArgumentParser(description='Extraction Wikipedia multistream lot UNESCO 002 (offline, reprise)')
    subs=p.add_subparsers(dest='action',required=True)
    for cmd in ('preflight','build','audit'):
        a=subs.add_parser(cmd)
        a.add_argument('--atlas',default=str(DEFAULT_ATLAS))
        a.add_argument('--selection',default=str(DEFAULT_SELECTION))
        a.add_argument('--output',default=str(DEFAULT_OUTPUT))
        a.add_argument('--xml',default=str(DEFAULT_XML))
        a.add_argument('--official-index')
        a.add_argument('--force-reconstruct',action='store_true')
        a.add_argument('--future-lot',action='store_true',
                       help='autoriser un nouveau CSV 1..100 pages et un nouveau chemin de ZIP')
        a.add_argument('--sidecar',default=str(DEFAULT_SIDECAR))
        a.add_argument('--cache',default=str(DEFAULT_CACHE))
        a.add_argument('--max-streams',type=int,default=0,
                       help='0 = jusqu’a trouver les 25 pages; valeur positive = reprise bornée')
        a.add_argument('--progress-every',type=int,default=500)
    return p.parse_args(argv)


def main(argv=None):
    try:
        args=parse(argv)
        if args.action=='preflight':out=preflight(args)
        elif args.action=='audit':out=verify_output(Path(args.output))
        else:out=build(args)
        emit(**out)
        return 0 if out['status'] not in ('INDEX_PAUSED','PAGES_ABSENTES_DU_DUMP',
                                          'TEXTES_PARTIELS_AUCUN_ZIP_FINAL') else 3
    except KeyboardInterrupt:
        emit(status='EXTRACTION_INTERROMPUE_INDEX_REPRENABLE',
             advice='Relancer la meme commande pour reprendre au dernier flux valide')
        return 130
    except (OSError,ValueError,KeyError,sqlite3.DatabaseError,zipfile.BadZipFile) as exc:
        emit(status='V20_ERREUR_SANS_PUBLICATION',error=str(exc))
        return 2

if __name__=='__main__':
    sys.exit(main())
