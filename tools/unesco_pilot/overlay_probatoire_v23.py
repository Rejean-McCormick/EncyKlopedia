#!/usr/bin/env python3
"""UNESCO v23 additif: revues IA et references probatoires privees.

Ne modifie ni v22, ni v18, ni les registres canoniques, ni Git.
Le telechargement optionnel archive des bytes bruts; ne les approuve pas.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request

DEFAULT_WORK = Path(r'D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41')
STAGE22 = 'semantic_stage_v22_revue_ia'
STAGE23 = 'semantic_stage_v23_probatoire'
VERSION = '23.0'
MAX_FILE = 15_000_000
MAX_WEB = 5_000_000
REVIEW_IDS = {'LOT002-V21-003','LOT002-V21-004','LOT002-V21-007','LOT002-V21-012','LOT002-V21-013','LOT002-V21-014'}
HOLD_IDS = {'LOT002-V21-017','LOT002-V21-020','LOT002-V21-013','LOT002-V21-014'}
EXPECTED_V22_APPROVALS = 38
EXPECTED_41 = 41

class Refusal(RuntimeError):
    pass

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def serialize(obj) -> bytes: return (json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
def content(path: Path, limit=MAX_FILE) -> bytes:
    if path.is_symlink() or not path.is_file() or path.stat().st_size>limit:
        raise Refusal('Fichier manquant, symbolique ou trop gros : '+str(path))
    return path.read_bytes()
def js(path: Path): return json.loads(content(path).decode('utf-8-sig'))
def jsonlines(path: Path):
    return [json.loads(line) for line in content(path).decode('utf-8-sig').splitlines() if line.strip()]
def valid_rel(name: str):
    p=Path(name)
    return bool(name and '/' not in (name[0:1]) and not p.is_absolute() and not re.search(r'[:\\]',name)
            and all(x not in ('.','..','') for x in name.split('/')))
def unique(rows, key):
    ids=[r[key] for r in rows]
    if len(ids)!=len(set(ids)):raise Refusal('Identifiants dupliques: '+key)
    return set(ids)

def verified_22(work: Path):
    stage=work/STAGE22
    if not stage.is_dir() or stage.is_symlink(): raise Refusal('Sortie v22 absente: '+str(stage))
    man=js(stage/'MANIFESTE_V22.json')
    files=man.get('files_sha256')
    if not isinstance(files,dict) or len(files)!=53: raise Refusal('Manifeste v22 incomplet / structure inattendue')
    actual={p.relative_to(stage).as_posix() for p in stage.rglob('*') if p.is_file()}
    if actual!=set(files)|{'MANIFESTE_V22.json'}:
        raise Refusal('Fichiers v22 supplementaires ou manquants: '+str(actual.symmetric_difference(set(files)|{'MANIFESTE_V22.json'}))[:500])
    for name,dig in files.items():
        if not valid_rel(name) or not re.fullmatch('[0-9a-f]{64}',str(dig)) or sha(content(stage/name))!=dig:
            raise Refusal('Empreinte v22 incorrecte: '+name)
    report=js(stage/'RAPPORT_V22.json')
    counts=report.get('counts',{})
    if not (report.get('overlay_version')=='v22' and counts.get('all_reviewed')==44 and
            counts.get('approved_text_revised')==10 and counts.get('suspended')==6 and
            report.get('canonical_KQ_KP_KA_KS_created')==0 and report.get('publication_authorized') is False):
        raise Refusal('Rapport v22 incompatible / statut canonique suspect')
    lot=jsonlines(stage/'LOT_002_25_REVUES_IA_NON_CANONIQUES.jsonl')
    r2=jsonlines(stage/'R2_19_APPROBATIONS_IA_NON_CANONIQUES.jsonl')
    if len(lot)!=25 or len(r2)!=19:raise Refusal('44 revues v22 incomplètes')
    ids=unique(lot+r2,'proposal_id')
    suspended={r['proposal_id'] for r in lot if r['decision']=='SUSPENDU_PREUVES'}
    if suspended!=REVIEW_IDS:raise Refusal('Suspensions v22 ne correspondent pas aux six verifiees')
    mapping={r['proposal_id'] for r in lot if r['mapping_state']=='BLOQUE_CORRESPONDANCE'}
    if mapping!={'LOT002-V21-017','LOT002-V21-020'}:
        raise Refusal('Rattachements v22 inattendus')
    concepts=js(stage/'CARTOGRAPHIE_41_CONCEPTS_V22.json')['concepts']
    if len(concepts)!=41 or len({x['unesco_id'] for x in concepts})!=41:
        raise Refusal('Carte des 41 concepts modifiee')
    if not ids.issuperset(REVIEW_IDS|HOLD_IDS):raise Refusal('Propositions attendues absentes')
    return {'stage':stage,'manifest_sha256':sha(content(stage/'MANIFESTE_V22.json')),
            'report_sha256':sha(content(stage/'RAPPORT_V22.json')),
            'lot':lot,'r2':r2,'concepts':concepts}

def verified_payload(script: Path):
    payload_file=script.parent/'v23_payload'/'REVUE_ET_PREUVES_V23.json'
    p=js(payload_file)
    if p.get('branch')!='unesco-mt1-10' or p.get('version')!=VERSION:raise Refusal('Payload v23 non compatible')
    mods=p['changes_for_6_suspensions']; anchors=p['external_semantic_anchors']; src=p['source_catalog']
    if unique(mods,'proposal_id')!=REVIEW_IDS or unique(anchors,'proposal_id')!=HOLD_IDS:
        raise Refusal('Nombre / identifiants v23 inattendus')
    keys=unique(src,'source_id')
    for m in mods:
        if not set(m['source_ids']).issubset(keys) or len(m['effective_statement'])<65:
            raise Refusal('Proposition v23 sans source ou sans texte: '+m['proposal_id'])
    for a in anchors:
        if a['source_id'] not in keys or a['external_unesco_id'] not in ('concept88','concept17016','concept9197','concept5900'):
            raise Refusal('Rattachement externe invalide')
    if p['strict_policy']['canonical_admission'] is not False or p['strict_policy']['publication'] is not False:
        raise Refusal('Garde canonique affaiblie')
    return p,sha(content(payload_file))

def build_review(v22,payload):
    patches={x['proposal_id']:x for x in payload['changes_for_6_suspensions']}
    holds={x['proposal_id']:x for x in payload['external_semantic_anchors']}
    rows=[]
    for original in v22['lot']+v22['r2']:
        x=dict(original);pid=x['proposal_id']
        x['v23_origin_decision']=x['decision']
        if pid in patches:
            p=patches[pid];x['effective_statement']=p['effective_statement']
            x['decision']='APPROUVE_IA_REFORMULE_V23'
            x['decision_reason_fr']=p['rationale_fr']
            x['official_sources']=[{'source_id':sid,'url':next(s['url'] for s in payload['source_catalog'] if s['source_id']==sid)} for sid in p['source_ids']]
            x['editorial_review_date']='2026-11-10'
            x['review_state']='APPROUVE_IA_NON_CANONIQUE_PREUVES_A_ARCHIVER'
        if pid in holds:
            a=holds[pid]
            x['mapping_state']='ANCRE_EXTERNE_SEULE_SANS_KQ'
            x['external_unesco_id_suggested']=a['external_unesco_id']
            x['external_unesco_uri']='http://vocabularies.unesco.org/thesaurus/'+a['external_unesco_id']
            x['external_descriptor_label']=a['label']
            x['semantic_mapping_note_fr']=a['note_fr']
            # The original internal concept remains for traceability, but is NOT the effective semantic attachment.
            x['effective_unesco_id']=None
            x['provisional_kq_id']=None
        x['source_capture_status']='NOT_CAPTURED'
        x['source_capture_sha256']=None
        x['canonical_admission_authorized']=False
        x['publication_authorized']=False
        x['v23_evidence_status']='SOURCE_LOCATORS_CHECKED_BUT_ORIGINAL_BYTES_NOT_ARCHIVED'
        rows.append(x)
    if len(rows)!=44 or any(x['decision'].startswith('SUSPENDU') for x in rows) or sum(x['mapping_state']=='ANCRE_EXTERNE_SEULE_SANS_KQ' for x in rows)!=4:
        raise Refusal('Revue v23 incoherente')
    if sum(x['decision']=='APPROUVE_IA_REFORMULE_V23' for x in rows)!=6:raise Refusal('6 corrections absentes')
    if sum(x['decision']=='APPROUVE_IA_REFORMULE' for x in rows)!=10:raise Refusal('10 corrections v22 absentes')
    if any(x['mapping_state']=='ANCRE_EXTERNE_SEULE_SANS_KQ' and (x['effective_unesco_id'] or x['provisional_kq_id']) for x in rows):
        raise Refusal('Rattachement externe usurpe un KQ')
    return rows

def h(s):return html.escape(str(s),quote=True)

CSS='''body{font-family:system-ui,Segoe UI,Arial,sans-serif;max-width:1000px;margin:3rem auto;padding:0 1.2rem;line-height:1.55;color:#243247;background:#fafbfd}a{color:#23639b}header{border-bottom:3px solid #244a78;padding-bottom:1rem}article{background:white;border:1px solid #d9e2eb;border-radius:12px;padding:1.25rem;margin:1rem 0}.tag{font-size:.84rem;color:#49627b}.warn{border-left:4px solid #ba7835;padding:.8rem;background:#fff7ed}ul{padding-left:1.4rem}small{color:#667085}'''

def htmlpage(title,body):
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{h(title)}</title><style>{CSS}</style></head><body><header><h1>{h(title)}</h1>'
            f'<p class="tag">UNESCO v23 · Recherche privee · Aucune admission canonique · Aucune publication</p></header>{body}</body></html>')

def generate_files(v22,payload,rows):
    by_concept={c['unesco_id']:[] for c in v22['concepts']}
    out_branch=[]
    for x in rows:
        if x['mapping_state']=='ANCRE_EXTERNE_SEULE_SANS_KQ':out_branch.append(x)
        else:by_concept[x['effective_unesco_id']].append(x)
    files={}
    report={'format':'koa.unesco-v23-probatoire-private/1.0','branch':'unesco-mt1-10','version':VERSION,
            'reviews_total':44,'editorial_ai_approved':44,'v22_approved_preserved':38,'v23_reviewed_and_reformulated':6,
            'text_corrections_v22':10,'text_corrections_v23':6,'mapping_holds_external':4,
            'mapping_suggested_external_not_approved':4,'within_41_effective_mappings':40,
            'concepts_preserved':41,'raw_source_captures_bundled':0,'canonical_admissions':0,
            'publication_authorized':False,'framework_authorization_granted':False,
            'source_capture_status':'NOT_CAPTURED','source_captures_sha256':None,
            'boundary':'AI_EDITORIAL_REVIEW_ONLY__NOT_FRAMEWORK_OR_KRISTAL_APPROVAL'}
    files['RAPPORT_V23.json']=serialize(report)
    files['REVUES_44_V23.json']=serialize({'format':'koa.unesco-reviewed-research-v23/1','records':rows,'publication_authorized':False})
    files['REVUES_44_V23.jsonl']=''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows).encode('utf8')
    files['REFERENCES_PROBATOIRES_V23.json']=serialize({'capture_status':'NOT_CAPTURED','sources':payload['source_catalog'],
        'disclaimer':'Les URL et points de controle web ne sont pas des captures brutes de sources.'})
    files['RATTACHEMENTS_EXTERNES_V23.json']=serialize({'status':'EXTERNAL_ANCHORS_NOT_ADMITTED_IN_MT1_10',
        'remaps':payload['external_semantic_anchors'],'no_new_provisional_ids':True})
    files['REPRISE_6_SUSPENSIONS_V23.json']=serialize({'status':'AI_EDITORIAL_REVIEWED_SOURCE_CAPTURE_PENDING',
        'changes':payload['changes_for_6_suspensions']})
    files['PREADMISSION_CANONIQUE_BLOQUEE_V23.json']=serialize({
        'status':'REVIEWED_AI_NOT_ADMITTED',
        'candidate_count_within_41':40,
        'external_anchors_not_admissible_here':4,
        'authoritative_approval_source':'AI_EDITORIAL_REVIEW_NON_CANONICAL',
        'required_gates':{
            'G1_official_source_raw_captures_and_claim_locators':False,
            'G2_rights_and_attribution':False,
            'G3_independent_framework_and_kit_qualification':False,
            'G4_approved_identity_and_semantic_contract':False,
            'G5_independent_publication_authorization':False,
        },
        'admission_authorized':False,'publication_authorized':False,
        'reviewed_records':[{'proposal_id':x['proposal_id'],
                             'admission_state':'BLOCKED_PROVENANCE_RIGHTS_FRAMEWORK',
                             'effective_unesco_id':x['effective_unesco_id'],
                             'provisional_kq_id':x['provisional_kq_id'],
                             'external_anchor':x.get('external_unesco_id_suggested'),
                             'source_capture_status':'NOT_CAPTURED'} for x in rows]
    })
    index=['<p><strong>44 propositions revues par IA, dont 6 reformulees en v23.</strong> 40 sur les 41 concepts du pilote et 4 en attente de rattachement externe. Aucun nouvel identifiant canonique.</p>',
           '<p class="warn">Sources en attente de capture brute et de controle de droits. Les attestations de pages web ne sont pas des captures officielles archivees.</p>',
           '<p><a href="hors_branche.html">Quatre propositions avec ancre UNESCO externe (hors 41)</a></p>','<h2>41 ancrages inchanges</h2><ul>']
    for concept in v22['concepts']:
        cid=concept['unesco_id'];rowlist=by_concept[cid]
        index.append(f'<li><a href="{h(cid)}.html">{h(concept["english_label"])} ({h(cid)})</a> — {len(rowlist)} propositions</li>')
        body=[f'<p>Identifiant provisoire historique : <code>{h(concept["provisional_kq_id"])}</code>. Identite non canonique.</p>','<p><a href="index.html">Retour aux 41 concepts</a></p>']
        if rowlist:
            for r in rowlist:
                txt=r.get('effective_statement') or '(texte suspendu)'
                refs='; '.join(s.get('url','') for s in r.get('official_sources',[]) or [])
                body.append(f'<article><h3>{h(r["proposal_id"])}</h3><p>{h(txt)}</p><p class="tag">{h(r["decision"])} · {h(r["mapping_state"])}</p><small>Sources: {h(refs or "Voir registre de sources local")} · Captures: NON</small></article>')
        else:body.append('<p>Aucune proposition retenue pour cet ancrage dans les 44 revues.</p>')
        files['reader_fr/'+cid+'.html']=htmlpage(concept['english_label'],''.join(body)).encode('utf8')
    index.append('</ul>')
    files['reader_fr/index.html']=htmlpage('Educational Policy — revue IA v23',''.join(index)).encode('utf8')
    ext=['<p class="warn">Rattachements uniquement documentaires : aucun KQ invente; aucune proposition de cette page ne peut etre admise dans les 41 ancrages.</p><p><a href="index.html">Retour</a></p>']
    for r in out_branch:
        ext.append(f'<article><h3>{h(r["proposal_id"])} — {h(r["external_descriptor_label"])}</h3><p>{h(r["effective_statement"])}</p>'
            f'<p>Descripteur externe : <a href="{h(r["external_unesco_uri"])}">{h(r["external_unesco_id_suggested"])}</a></p><small>{h(r["semantic_mapping_note_fr"])}</small></article>')
    files['reader_fr/hors_branche.html']=htmlpage('Propositions hors des 41 concepts',''.join(ext)).encode('utf8')
    readme='''# UNESCO v23 — revue probatoire privee\n\n- 44 propositions approuvees editorialement par IA, dont 6 reformulees en v23.\n- Les 10 reformulations v22 restent conservees.\n- 4 rattachements pointent vers des descripteurs UNESCO externes, sans KQ; ils restent exclus des 41 ancrages.\n- Les 41 identites existantes ne sont pas modifiees.\n- L'archive contient des URL et des localisateurs de preuves, **pas** les octets originaux des pages officielles.\n- La commande separee CAPTURER_PREUVES_UNESCO_V23.cmd telecharge des documents sur l'ordinateur de l'utilisateur et en calcule les SHA-256 reels; le succes HTTP ne vaut ni verification intellectuelle ni autorisation de publication.\n- Aucun KS/KQ/KP/KA canonique n'est cree, et aucun processus public/GitHub n'est touche.\n\nOuvrir `reader_fr/index.html` pour visualiser la revue privee.\n'''
    files['LIRE_DABORD_V23.md']=readme.encode('utf8')
    files['PROVENANCE_V23.json']=serialize({'v22_manifest_sha256':v22['manifest_sha256'],
      'v22_report_sha256':v22['report_sha256'],'payload_v23_source':'REVUE_ET_PREUVES_V23.json',
      'source_capture_status':'NOT_CAPTURED','canonical_admissions':0})
    return files,report

def stage_manifest(files,inp):
    return {'format':'koa.unesco-v23-output-manifest/1','version':VERSION,'inputs':inp,
            'files_sha256':{k:sha(v) for k,v in sorted(files.items())},'admissions':0,'publication':False}

def verify_stage(out: Path, expected_inputs=None, expected_files_sha=None):
    if not out.is_dir() or out.is_symlink():raise Refusal('Sortie v23 absente ou symbolique')
    manifest=js(out/'MANIFESTE_V23.json')
    entries=manifest.get('files_sha256')
    if not isinstance(entries,dict) or len(entries)!=52:raise Refusal('Manifeste v23 incomplet: '+str(len(entries) if isinstance(entries,dict) else 'none'))
    if expected_inputs is not None and expected_inputs!=manifest.get('inputs'):
        raise Refusal('Sources modifiees depuis la generation de v23')
    if expected_files_sha is not None and entries!=expected_files_sha:
        raise Refusal('Contenu v23 diverge des fichiers generes depuis sources verifiees')
    actual={p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}
    if actual!=set(entries)|{'MANIFESTE_V23.json'}:
        raise Refusal('Sortie v23 altérée (fichiers supplementaires ou manquants)')
    if any(p.is_symlink() for p in out.rglob('*')):raise Refusal('Lien symbolique dans v23')
    for name,dig in entries.items():
        if not valid_rel(name) or sha(content(out/name))!=dig:raise Refusal('Empreinte v23 modifiee: '+name)
    rep=js(out/'RAPPORT_V23.json')
    if rep.get('canonical_admissions')!=0 or rep.get('publication_authorized') is not False:
        raise Refusal('Sortie v23 contraire a la politique privee')
    return {'status':'V23_CONTROLE_OK','files_verified':len(entries),'reviewed':rep['reviews_total'],
            'ai_editorial_approved':rep['editorial_ai_approved'],'external_holds':rep['mapping_holds_external'],
            'raw_source_captures':rep['raw_source_captures_bundled'],'canonical_admissions':0,'publication_authorized':False,
            'reader':str(out/'reader_fr'/'index.html')}

def process(work:Path,script:Path,mode:str):
    if work.is_symlink() or not work.is_dir():raise Refusal('Workspace absent ou symbolique: '+str(work))
    if (work/'.git').exists():raise Refusal('Aucune ecriture dans un depot Git')
    work=work.resolve(strict=True)
    v22=verified_22(work);payload,payload_sha=verified_payload(script)
    reviews=build_review(v22,payload)
    inp={'v22_manifest_sha256':v22['manifest_sha256'],'v22_report_sha256':v22['report_sha256'],'patch_payload_sha256':payload_sha}
    out=work/STAGE23
    files,report=generate_files(v22,payload,reviews)
    expected_manifest=stage_manifest(files,inp)
    if mode=='preflight':
        return {'status':'V23_PREFLIGHT_OK','reviews':len(reviews),'new_reformulations':6,
                'external_mapping_holds':4,'41_concepts_preserved':41,'target':str(out),'canonical_admissions':0}
    if mode=='verify':return verify_stage(out,inp,expected_manifest['files_sha256'])
    if mode=='apply':
        if out.exists() or out.is_symlink():
            result=verify_stage(out,inp,expected_manifest['files_sha256']);result['status']='V23_DEJA_INSTALLE_INTEGRE';return result
        manifest=expected_manifest
        tmp=Path(tempfile.mkdtemp(prefix='.tmp_semantic_stage_v23_',dir=work))
        try:
            for name,b in files.items():
                if not valid_rel(name):raise Refusal('Chemin de sortie invalide: '+name)
                path=tmp/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
            (tmp/'MANIFESTE_V23.json').write_bytes(serialize(manifest))
            verify_stage(tmp,inp,expected_manifest['files_sha256'])
            if out.exists():raise Refusal('Destination v23 est apparue pendant la preparation')
            tmp.rename(out)
        finally:
            if tmp.exists():shutil.rmtree(tmp)
        result=verify_stage(out,inp,expected_manifest['files_sha256']);result['status']='V23_CORRECTIONS_APPLIQUEES_PRIVÉES';return result
    raise Refusal('Mode inconnu')

ALLOWED_HOSTS={
 'databrowser.uis.unesco.org','www.oecd.org','www.unesco.org','www.unicef.org',
 'eric.ed.gov','pmc.ncbi.nlm.nih.gov','educationendowmentfoundation.org.uk',
 'vocabularies.unesco.org','www.un.org','2covenants.ohchr.org','www.uis.unesco.org'}

def fetch_one(source):
    u=source['url'];p=urllib.parse.urlparse(u)
    if p.scheme!='https' or p.hostname not in ALLOWED_HOSTS or p.username or p.password:
        return source['source_id'],{'status':'REFUSED_UNTRUSTED_URL','url':u},None
    try:
        req=urllib.request.Request(u,headers={'User-Agent':'EncyKlopedia-UNESCO-v23-private-source-archiver/1.0','Accept':'text/html,application/pdf,text/plain,application/json;q=0.5'})
        with urllib.request.urlopen(req,timeout=12) as resp:
            final=resp.geturl();q=urllib.parse.urlparse(final)
            if q.scheme!='https' or q.hostname not in ALLOWED_HOSTS:
                raise Refusal('Redirection hors des domaines autorises')
            ctype=resp.headers.get('Content-Type','').split(';',1)[0].lower()
            if ctype not in ('text/html','text/plain','application/pdf','application/json','application/xhtml+xml'):
                raise Refusal('Type non archive: '+ctype)
            raw=resp.read(MAX_WEB+1)
            if not raw or len(raw)>MAX_WEB:raise Refusal('Fichier vide ou depasse 5Mo')
            if ctype=='application/pdf' and not raw.startswith(b'%PDF'):raise Refusal('PDF sans signature')
            if ctype in ('text/html','application/xhtml+xml') and b'<html' not in raw[:4096].lower() and b'<!doctype' not in raw[:4096].lower():
                raise Refusal('Reponse HTML inattendue')
            ext='.pdf' if ctype=='application/pdf' else '.json' if ctype=='application/json' else '.html' if 'html' in ctype else '.txt'
            return source['source_id'],{'status':'CAPTURE_HTTP_SUCCESS_NOT_FACT_CHECKED','url':u,'final_url':final,'content_type':ctype,'bytes':len(raw),'sha256':sha(raw),'filename':source['source_id']+ext,
             'original_locator':source['locator'],'rights_status':'UNASSESSED_PRIVATE_RESEARCH_ONLY','http_status':resp.status},raw
    except Exception as ex:
        return source['source_id'],{'status':'NOT_CAPTURED','url':u,'error':str(ex)[:280]},None

def capture(work:Path,script:Path):
    check=process(work,script,'verify')
    payload,_=verified_payload(script)
    work=work.resolve(strict=True)
    sources=payload['source_catalog']
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    name='semantic_stage_v23_sources_capture_'+stamp
    dest=work/name
    if dest.exists():raise Refusal('Capture deja presente pour cet instant, ne pas ecraser')
    temp=Path(tempfile.mkdtemp(prefix='.tmp_v23_capture_',dir=work))
    try:
        saved={};out={}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for sid,metadata,raw in pool.map(fetch_one,sources):
                out[sid]=metadata
                if raw is not None:
                    filename=metadata['filename'];(temp/filename).write_bytes(raw);saved[filename]=sha(raw)
        archive={'format':'koa.unesco-v23-source-capture/1','capture_utc':stamp,
                 'meaning':'Archive of HTTP bytes, not automatic editorial/legal proof',
                 'sources':out,'files_sha256':saved,'canonical_admissions':0,'publication_authorized':False}
        (temp/'REGISTRE_CAPTURES.json').write_bytes(serialize(archive))
        manifest=stage_manifest({k:content(temp/k,MAX_WEB+50) for k in saved}|{'REGISTRE_CAPTURES.json':content(temp/'REGISTRE_CAPTURES.json')},{'v23_manifest_sha256':sha(content(work/STAGE23/'MANIFESTE_V23.json'))})
        (temp/'MANIFESTE_CAPTURES.json').write_bytes(serialize(manifest))
        temp.rename(dest)
    finally:
        if temp.exists():shutil.rmtree(temp)
    return {'status':'V23_CAPTURES_HTTP_TERMINEES','success_raw_captures':len(saved), 'not_captured':len(sources)-len(saved),
            'dest':str(dest),'rights_reviewed':False,'claims_reverified_from_captures':False,
            'canonical_admissions':0,'publication_authorized':False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('mode',choices=('preflight','apply','verify','capture'))
    ap.add_argument('--work-root',type=Path,default=DEFAULT_WORK)
    args=ap.parse_args()
    try:
        r=capture(args.work_root,Path(__file__)) if args.mode=='capture' else process(args.work_root,Path(__file__),args.mode)
        print(json.dumps(r,ensure_ascii=False,indent=2));return 0
    except (Refusal,ValueError,KeyError,TypeError,OSError) as e:
        print(json.dumps({'status':'V23_REFUS','reason':str(e)},ensure_ascii=False,indent=2),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
