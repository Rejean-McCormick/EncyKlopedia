#!/usr/bin/env python3
"""Export private UNESCO research ZIPs from direct XML byte offsets (v21).

The existing atlas v19 defines the selection and stable UNESCO anchors. This
module exports a compatible LOT_MANIFEST.json but does not modify any Kristal
or Mediatheque state. Its mediatheque handoff is a *candidate* only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

import atlas_wikipedia as v19
from index_xml_v21 import (DEFAULT_DB, DEFAULT_XML, audit as audit_index,
                            read_one, ro_connect, signature, emit)

DEFAULT_ATLAS = v19.DEFAULT_OUT
DEFAULT_SELECTION = Path(__file__).with_name('SELECTION_UNESCO_ATLAS_V19_LOT_002_25_PAGES.csv')
DEFAULT_OUTPUT = v19.DEFAULT_WORK / 'atlas_documentaire_v19_LOT_002_CHATGPT_V21.zip'
RECEIPT_FORMAT = 'koa.unesco-wikipedia-direct-xml-lot/1.0'
EXPECTED_IDS = frozenset({2287044,10870972,9252,24983,22089591,31899,46945565,30631120,4378212,9384153,13323043,25572436,430890,2128182,4003872,479983,465183,214737,18456,436831,8997,1944675,375170,293121,2805394})
MAX_TEXT_BYTES = 5 * 1024 * 1024


def sha(data: bytes):return hashlib.sha256(data).hexdigest()


def file_sha(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
    return h.hexdigest()


def jbytes(obj):return (json.dumps(obj,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def receipt_path(out:Path):return Path(str(out)+'.v21.json')


def read_selection(atlas:Path,selection:Path, future_lot:bool):
    v19.audit(atlas)
    picked, allowed=v19.load_selection(atlas,selection,100)
    if not future_lot and (len(picked)!=25 or set(picked)!=EXPECTED_IDS):
        raise ValueError('Selection LOT 002 modifiee : 25 identifiants originaux requis')
    import csv
    with selection.open('r',encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if str(r.get('selected','')).strip().lower() not in ('1','yes','oui','true','y'):
                continue
            pid=int(r['page_id']);known=allowed[pid]
            for k in ('title','revision_id','qid'):
                if str(r.get(k,''))!=str(known.get(k,'')):
                    raise ValueError('Selection incoherente avec atlas V19: '+str(pid)+' '+k)
    return picked, allowed


def preflight(a):
    atlas=Path(a.atlas);selection=Path(a.selection)
    picked,_=read_selection(atlas,selection,a.future_lot)
    if a.future_lot and (selection.resolve()==DEFAULT_SELECTION.resolve() or Path(a.output)==DEFAULT_OUTPUT):
        raise ValueError('Futur lot: passer --selection et --output nouveaux, sans modifier lot 002')
    result=audit_index(Path(a.xml),Path(a.db),require_complete=True)
    return {'status':'V21_LOT_PRET_A_EXTRAIRE','atlas':str(atlas),
            'selected_pages':len(picked),'index_pages':result['pages_indexed'],
            'xml':str(a.xml),'output':str(a.output),
            'source_read_only':True,'kristal_unchanged':True}


def read_wikitext(raw:bytes, page_id:int):
    try:node=ET.fromstring(raw)
    except ET.ParseError as exc:raise ValueError(f'XML page {page_id} mal forme: {exc}') from exc
    if int(node.findtext('./id') or '0')!=page_id:
        raise ValueError('Page XML id non conforme: '+str(page_id))
    if node.findtext('./ns')!='0':
        raise ValueError('Page demandee hors espace principal: '+str(page_id))
    if node.find('redirect') is not None:
        raise ValueError('Redirection selectionnee plutot qu un article: '+str(page_id))
    revision=node.find('./revision')
    if revision is None:
        raise ValueError('Revision absente pour '+str(page_id))
    rev_id=revision.findtext('./id') or ''
    text=revision.findtext('./text') or ''
    if not text.strip():raise ValueError('Texte vide: '+str(page_id))
    payload=text.encode('utf-8')
    if len(payload)>MAX_TEXT_BYTES:
        raise ValueError('Article depasse la limite de lot de 5 MiB: '+str(page_id))
    return payload,rev_id


def verify(out:Path):
    receipt=receipt_path(out)
    if not out.is_file() or not receipt.is_file():
        raise ValueError('ZIP V21 ou recu absent: '+str(out))
    r=json.loads(receipt.read_text(encoding='utf-8'))
    if r.get('format')!=RECEIPT_FORMAT or file_sha(out)!=r['zip_sha256']:
        raise ValueError('Empreinte ou format du lot V21 invalide')
    with zipfile.ZipFile(out) as z:
        manifest=z.read('LOT_MANIFEST.json')
        if sha(manifest)!=r['lot_manifest_sha256']:
            raise ValueError('Manifeste ZIP modifie')
        m=json.loads(manifest)
        if m.get('format')!=v19.ZIP_FORMAT or m['branch']!='unesco-mt1-10':
            raise ValueError('Format branche / ZIP incorrect')
        if m['texts_missing']!=0 or m['texts_available']!=m['selected_pages']:
            raise ValueError('Lot incomplet')
        for item in m['items']:
            name=item['text_relative_path']
            if name not in z.namelist() or sha(z.read(name))!=item['text_sha256']:
                raise ValueError('Texte ZIP altere: '+str(item['page_id']))
        for needed in ('MODELE_PROPOSITIONS_CHATGPT.json','LISEZ_MOI_CHATGPT.md',
                       'MEDIATHEQUE_HANDOFF_CANDIDAT.json',
                       'atlas/ancrages_kristal_stables.json',
                       'atlas/liens_internes.csv','atlas/pages_prioritaires_a_selectionner.csv'):
            if needed not in z.namelist():raise ValueError('Fichier lot absent: '+needed)
    return {'status':'V21_LOT_INTEGRITE_VERIFIEE','lot_zip':str(out),
            'selected':m['selected_pages'],'texts_extracted':m['texts_available'],
            'source':'XML_UNCOMPRESSED_DIRECT_OFFSETS',
            'revision_mismatches':len(r['revision_mismatches']),
            'zip_sha256':r['zip_sha256'],'canonical_unchanged':True}


def build(a):
    ctx=preflight(a)
    atlas=Path(a.atlas);selection=Path(a.selection);out=Path(a.output)
    source=Path(a.xml); db=Path(a.db)
    srcsig=signature(source)
    if out.exists() or receipt_path(out).exists():
        val=verify(out)
        old=json.loads(receipt_path(out).read_text(encoding='utf-8'))
        if (old['xml_signature']!=srcsig or old['selection_sha256']!=file_sha(selection) or
            old['atlas_manifest_sha256']!=file_sha(atlas/'manifest.json')):
            raise ValueError('ZIP existant avec des sources changees: nouveau --output requis')
        val['operation']='REPRISE_IDENTIQUE';return val
    picked, allowed=read_selection(atlas,selection,a.future_lot)
    rows={}
    with ro_connect(db) as c:
        for pid in picked:
            row=c.execute('''SELECT page_id,byte_offset,byte_length,namespace,title,revision_id,is_redirect
                             FROM pages WHERE page_id=?''',(pid,)).fetchone()
            if row is None:
                raise ValueError('Article non present dans l index V21 complet: '+str(pid))
            rows[pid]=row
    items=[]; zfiles={}; mediatheque=[]; mismatches=[]
    with source.open('rb') as f:
        for pid in picked:
            raw=read_one(f,rows[pid],pid)
            payload,rev_id=read_wikitext(raw,pid)
            known=allowed[pid]
            mismatch=bool(known.get('revision_id') and str(known['revision_id'])!=rev_id)
            if mismatch:mismatches.append({'page_id':pid,'atlas_revision':known['revision_id'],
                                            'xml_revision':rev_id})
            path=f'articles/page-{pid}.wikitext.txt'
            digest=sha(payload)
            zfiles[path]=payload
            page_url='https://en.wikipedia.org/w/index.php?'+urllib.parse.urlencode({'title':known['title'],'oldid':rev_id})
            items.append({'page_id':pid,'title':known['title'],'qid':known.get('qid',''),
                          'atlas_rank':known.get('rank'),'atlas_revision_id':known.get('revision_id',''),
                          'status':'TEXT_EXTRACTED','discovery_is_not_semantic_evidence':True,
                          'text_relative_path':path,'text_sha256':digest,'text_revision_id':rev_id,
                          'revision_mismatch_with_SQL':mismatch,
                          'local_source':'LOCAL_UNCOMPRESSED_XML_V21_DIRECT_INDEX',
                          'wikipedia_revision_url':page_url,'source_byte_offset':rows[pid][1],
                          'source_byte_length':rows[pid][2]})
            mediatheque.append({'kind':'WIKIPEDIA_PAGE_SOURCE_CANDIDATE','page_id':pid,
                                'revision_id':rev_id,'title':known['title'],
                                'source_url':page_url,'wikitext_sha256':digest,
                                'xml_parent_signature':srcsig,
                                'approved_source_record':False})
    for filename in ('ancrages_kristal_stables.json','liens_internes.csv',
                     'pages_prioritaires_a_selectionner.csv'):
        zfiles['atlas/'+filename]=(atlas/filename).read_bytes()
    manifest={'format':v19.ZIP_FORMAT,'branch':'unesco-mt1-10',
              'atlas_manifest_sha256':file_sha(atlas/'manifest.json'),
              'items':items,'selected_pages':len(picked),'texts_available':len(picked),
              'texts_missing':0,'no_KQ_KP_KA_KS_approved':True,
              'purpose':'CHATGPT_PRIVATE_RESEARCH_NOT_PUBLICATION',
              'wikipedia_license_notice':'CC BY-SA attribution and revision traceability required; investigate exceptions',
              'direct_xml_index_version':'v21'}
    data=jbytes(manifest)
    zfiles['LOT_MANIFEST.json']=data
    zfiles['MODELE_PROPOSITIONS_CHATGPT.json']=jbytes({
        'format':'koa.unesco-documentary-proposals/1.0','branch':'unesco-mt1-10',
        'batch_manifest_sha256':sha(data),'proposals':[],
        '_instructions':'Propositions candidates avec source_page_id, source_revision_id, source_locator et statement. Aucun canon automatique.'})
    zfiles['MEDIATHEQUE_HANDOFF_CANDIDAT.json']=jbytes({
        'format':'koa.wikipedia-mediatheque-source-leads-v21/1.0',
        'status':'CANDIDATE_ONLY_NOT_IMPORTED_NOT_ATTESTED',
        'source_archive':'enwiki-2026-10','branch':'unesco-mt1-10',
        'wikipedia_source_signature':srcsig,'sources':mediatheque,
        'does_not_register_ks':True})
    zfiles['LISEZ_MOI_CHATGPT.md']=(
        '# Lot UNESCO Wikipédia EN (accès direct v21)\n\n'
        'Source documentaire privée, non un Kristal canonique. '\
        'Les liens entre pages sont des observations, pas des faits.\n\n'
        'Le texte Wikipédia exige attribution et suivi de licence CC BY-SA. '\
        'Les localisateurs de sections et les révisions sont requis pour les propositions IA.\n\n'
        'Le fichier `MEDIATHEQUE_HANDOFF_CANDIDAT.json` n’est **pas** une importation en Médiathèque '\
        'et n’atteste aucune source KS.\n').encode('utf-8')
    out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.v21_lot_',suffix='.zip',dir=out.parent,delete=False) as tmp:
        temp=Path(tmp.name)
    try:
        with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for name in sorted(zfiles):z.writestr(name,zfiles[name])
        if out.exists():raise FileExistsError('ZIP cree simultanement: '+str(out))
        temp.replace(out)
    finally:
        if temp.exists():temp.unlink()
    receipt={'format':RECEIPT_FORMAT,'created_utc':datetime.now(timezone.utc).isoformat(),
             'branch':'unesco-mt1-10','xml_signature':srcsig,
             'selection_sha256':file_sha(selection),'atlas_manifest_sha256':file_sha(atlas/'manifest.json'),
             'lot_manifest_sha256':sha(data),'zip_sha256':file_sha(out),
             'selected_count':len(picked),'revision_mismatches':mismatches,
             'no_new_KQ_KP_KA_KS':True,'mediatheque_handoff_is_candidate_only':True}
    path=receipt_path(out); tmp=Path(str(path)+'.tmp')
    tmp.write_bytes(jbytes(receipt));tmp.replace(path)
    val=verify(out);val['status']='V21_LOT_PRET_POUR_CHATGPT';return val


def parse(argv=None):
    p=argparse.ArgumentParser(description='Extraire les lots de recherche UNESCO depuis index XML direct V21')
    sub=p.add_subparsers(dest='action',required=True)
    for action in ('preflight','build','audit'):
        a=sub.add_parser(action)
        a.add_argument('--xml',default=str(DEFAULT_XML))
        a.add_argument('--db',default=str(DEFAULT_DB))
        a.add_argument('--atlas',default=str(DEFAULT_ATLAS))
        a.add_argument('--selection',default=str(DEFAULT_SELECTION))
        a.add_argument('--output',default=str(DEFAULT_OUTPUT))
        a.add_argument('--future-lot',action='store_true')
    return p.parse_args(argv)


def main(argv=None):
    try:
        a=parse(argv)
        if a.action=='preflight':val=preflight(a)
        elif a.action=='build':val=build(a)
        else:val=verify(Path(a.output))
        emit(**val);return 0
    except KeyboardInterrupt:
        emit(status='V21_LOT_INTERROMPU',advice='Relancer; aucun ZIP incomplet publie')
        return 130
    except (OSError,ValueError,KeyError,sqlite3.DatabaseError,zipfile.BadZipFile,ET.ParseError) as exc:
        emit(status='V21_LOT_ECHEC_SANS_MODIFICATION_CANONIQUE',error=str(exc))
        return 2

if __name__=='__main__':sys.exit(main())
