"""Boucle à dix postes, deux passes, ZIP autonomes, reprises idempotentes.

Le registre de propositions est privé; aucune sortie ne devient un état canonique.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import csv
import hashlib
import io
import json
import os
import sqlite3
import math
from contextvars import ContextVar
from functools import wraps
import re
from datetime import timedelta
from .locking import serialized, database_path
import tempfile
import zipfile
from .sql import read_source
from .sources import utc


def json_bytes(o):
    return (json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def sha(x):return hashlib.sha256(x).hexdigest()

def filehash(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def pack_zip(path,items):
    """ZIP créé atomiquement, sans dump ni JSON de données tronqué."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise FileExistsError(path)
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.encyk_',suffix='.tmp',delete=False) as f:
        tmp=Path(f.name)
    try:
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for name,content in items.items():
                if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('Nom ZIP invalide')
                z.writestr(name,content)
        with zipfile.ZipFile(tmp) as z:
            bad=z.testzip()
            if bad:raise ValueError('Archive ZIP endommagée : '+bad)
        with tmp.open('r+b') as complete:os.fsync(complete.fileno())
        os.replace(tmp,path)
    finally:tmp.unlink(missing_ok=True)
    return filehash(path)

def _nextid(db,prefix):
    # Sequence inside one DB transaction; no overwrite after crash.
    row=db.execute('SELECT value FROM meta WHERE key=?',(prefix+'_sequence',)).fetchone()
    n=int(row[0]) + 1 if row else 1
    db.execute('INSERT INTO meta VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
               (prefix+'_sequence',str(n)))
    return prefix+'_'+str(n).zfill(6)

def _free_lane(db, limit=10):
    r=db.execute('SELECT lane FROM lanes WHERE job_id IS NULL AND lane<=? ORDER BY lane LIMIT 1',(limit,)).fetchone()
    return int(r[0]) if r else None

def _scope(db,cid):
    r=db.execute('SELECT label_fr,label_en,description FROM concepts WHERE concept_id=?',(cid,)).fetchone()
    return dict(r) if r else {}


def selection_prompt(job_id):
    return f'''# EncyK V32 — Passe 1 : Sélection ({job_id})

Lis TOUT le fichier `candidates.jsonl`, y compris les propositions de faible priorité.
Chaque ligne est une paire article/concept avec des routes de découverte et, lorsque disponible, un extrait
de l’article Wikipédia original dans source_context. Un extrait absent ou incomplet ne signifie pas
que l’article est hors sujet. Les liens Wikidata et P3916
sont des indices de candidature, pas une preuve de pertinence documentaire. Pour CHAQUE identifiant :
* SELECT si l'article est réellement pertinent pour le concept (sujet substantiel, pas mention incidente).
* REJECT si la correspondance est clairement hors sujet.
* HOLD seulement si l'information disponible ne permet pas de trancher.
Explique brièvement en français; n'invente pas de contenu absent des sources.

Consacre le travail nécessaire à la totalité du lot; répartis ton examen en tranches internes.
La cible est le débit utile, pas une revue triple ou une réponse superficielle. Ne redemande pas
à l'utilisateur de découper le lot. Ne change aucun identifiant, titre, page_id ou QID.

Renvoie UN ZIP avec `selection_decisions.csv`, UTF-8 et exactement trois colonnes :
`candidate_id,decision,justification`. Une ligne par candidat, sans candidate_id inventé.
Les décisions sont provisoires et n'autorisent aucune admission canonique ni publication.
'''

def enrichment_prompt(job_id):
    return f'''# EncyK V32 — Passe 2 : Enrichissement massif ({job_id})

Étudie les articles COMPLETS du dossier `articles/`, sans les considérer comme de simples résumés.
Sers-toi de `articles.jsonl` pour garder les sujets, QID, concepts et révisions stables.
Les extraits Wikidata éventuels sont du CONTEXTE structurant, non des citations originales complètes.

Produis généreusement des propositions de connaissance précises, distinctives et contextualisées :
définitions, dates et périodes, données chiffrées, institutions, mécanismes, séquences, lois historiques,
relations causales explicitement attribuées, contributions, désaccords et limites.
L'objectif est une encyclopédie gigantesque, non quelques généralités par article.
Ne crée pas de remplissage, ne répète pas les mêmes faits et ne transforme pas une hypothèse en certitude.
Chaque proposition s'appuie sur un passage exact et traçable dans le texte du pack.
Priorise l'extraction substantielle plutôt que les triples vérifications systématiques.

Format de retour : UN ZIP contenant `kristal_delta.json` :
{{"format":"encyk.enrichment-delta.v32/2","job_id":"{job_id}",
 "facts":[{{"page_id":123,"revision_id":"REVISION_DU_PACK","subject_key":"wd:Q...",
 "predicate":"describes","object":{{"type":"text","value":"..."}},
 "statement":"...","source_quote":"citation EXACTE dans le texte",
 "source_locator":"Section ou emplacement","concept_ids":["concept..."],"qualifiers":{{"period":"si pertinente"}}}}],
 "source_coverage":[{{"page_id":123,"status":"processed","note":"synthèse des dimensions examinées"}}],
 "canonical_admissions":0,"publication_authorized":false}}

Tous les articles doivent figurer dans `source_coverage`. Statuts : processed,
no_relevant_claim (avec motif précis), incomplete ou blocked. Ne pas déclarer processed
si le traitement est incomplet. Conserver les périodes, unités, populations, méthodes,
conditions et attributions dans qualifiers/context. number exige une valeur JSON numérique,
boolean un booléen JSON. Ne jamais inventer pour remplir un quota.
Pour TARGETED_COMPLEMENT, les prior_propositions sont un inventaire provisoire à ne pas
reproduire; traiter les nouvelles dimensions conceptuelles indiquées et sourcer tout ajout.
Une citation de courte longueur doit réellement appuyer son énoncé; ne l'invente jamais.
N'essaie ni d'admettre un état Kristal ni de publier. Renvoie uniquement les données privées.
'''

@serialized
def make_selection(db,settings,branch=None):
    """Crée un pack tant qu'un poste est libre; libère aucun candidat oublié."""
    if _free_lane(db,settings.lane_count) is None:return None
    # V6: pool prioritaire borne, puis un tour par concept pour diversifier les lots.
    pool_size=settings.select_pack_size*10
    params=(branch,pool_size,settings.select_pack_size) if branch else (pool_size,settings.select_pack_size)
    where='AND c.branch_id=?' if branch else ''
    rows=db.execute(f'''WITH pool AS (
          SELECT c.* FROM candidates c WHERE c.state='PENDING' {where}
          ORDER BY c.priority DESC,c.candidate_id LIMIT ?
        ), ranked AS (
          SELECT pool.*,ROW_NUMBER() OVER (PARTITION BY concept_id
            ORDER BY priority DESC,candidate_id) AS concept_turn FROM pool
        )
        SELECT * FROM ranked ORDER BY concept_turn,priority DESC,candidate_id LIMIT ?''',params).fetchall()
    if not rows:return None
    jobs=[dict(row) for row in rows]
    # Extraits documentaires de révisions locales; pas de vérification coûteuse par trois moteurs.
    excerpts={}
    if Path(settings.wikipedia_xml).is_file() and Path(settings.wikipedia_direct_index).is_file():
        try:
            from tools.unesco_pilot.production_kristals_v27 import page_from_index
            with read_source(settings.wikipedia_direct_index) as ix,Path(settings.wikipedia_xml).open('rb') as xml:
                for pid in sorted({x['page_id'] for x in jobs}):
                    try:
                        raw,rev,title=page_from_index(ix,xml,int(pid))
                        excerpts[pid]={'excerpt':raw.decode('utf-8','replace')[:settings.selection_excerpt_chars],
                                       'revision_id':str(rev),'original_title':title,
                                       'context_kind':'ORIGINAL_WIKIPEDIA_WIKITEXT_EXCERPT'}
                    except (OSError,ValueError):pass
        except (OSError,ImportError,sqlite3.Error):pass
    candidates=[]
    for c in jobs:
        routes=[dict(r) for r in db.execute('SELECT origin,anchor_qid,subject_qid,property_path FROM candidate_routes WHERE candidate_id=?',(c['candidate_id'],))]
        candidates.append({**{k:c[k] for k in ('candidate_id','branch_id','concept_id','subject_key','page_id','title','revision_id','priority')},
                           'concept':_scope(db,c['concept_id']),'routes':routes,
                           'context_completeness':'WIKITEXT_EXCERPT' if c['page_id'] in excerpts else 'TITLE_AND_GRAPH_ONLY_NO_ARTICLE_TEXT',
                           'source_context':excerpts.get(c['page_id']),
                           'review_policy':'SUBSTANTIVE_RELEVANCE_REQUIRED'})
    with db:jid=_nextid(db,'SEL')
    manifest={'format':'encyk.selection-pack.v32/1','job_id':jid,'candidates_count':len(jobs),
              'created_utc':utc(),'canonical_admissions':0,
              'excerpts_available':len(excerpts),'source':'UNESCO_WIKIDATA_WIKIPEDIA_INDEXED'}
    files={'selection_pack.json':json_bytes(manifest),'candidates.jsonl':
           ('\n'.join(json.dumps(r,ensure_ascii=False) for r in candidates)+'\n').encode('utf-8'),
           'INSTRUCTIONS_CHATGPT.md':selection_prompt(jid).encode('utf-8')}
    dst=settings.packs_path/(jid+'.zip');checksum=pack_zip(dst,files)
    with db:
        lane=_free_lane(db,settings.lane_count)
        if lane is None:raise RuntimeError('Aucun poste disponible (pack préservé)')
        db.execute('INSERT INTO jobs(job_id,kind,status,pack_path,pack_sha256,count,created_utc) VALUES(?,?,?,?,?,?,?)',
                   (jid,'SELECTION','READY',str(dst),checksum,len(jobs),utc()))
        for r in jobs:
            cur=db.execute("UPDATE candidates SET state='QUEUED_SELECTION' WHERE candidate_id=? AND state='PENDING'",(r['candidate_id'],))
            if cur.rowcount!=1:raise RuntimeError('Candidat déjà réservé')
            db.execute('INSERT INTO job_items VALUES(?,?)',(jid,r['candidate_id']))
            db.execute('INSERT INTO active_items VALUES(?,?)',(r['candidate_id'],jid))
        db.execute('UPDATE lanes SET job_id=? WHERE lane=?',(jid,lane))
    return {'job_id':jid,'kind':'SELECTION','lane':lane,'count':len(jobs),'path':str(dst)}


_article_session=ContextVar('encyk_article_session',default=None)


def _batch_articles(fn):
    @wraps(fn)
    def call(db,settings,*args,**kwargs):
        from contextlib import ExitStack
        with ExitStack() as stack:
            token=_article_session.set({'stack':stack,'reader':None})
            try:return fn(db,settings,*args,**kwargs)
            finally:_article_session.reset(token)
    return call


def _read_article(settings,page_id):
    """One read-only index/XML handle per preparation, with verified offsets."""
    from tools.unesco_pilot.production_kristals_v27 import page_from_index
    xml=Path(settings.wikipedia_xml)
    if not xml.is_file():raise FileNotFoundError('XML Wikipédia absent : '+str(xml))
    session=_article_session.get()
    if session is not None:
        if session['reader'] is None:
            ix=session['stack'].enter_context(read_source(settings.wikipedia_direct_index))
            inp=session['stack'].enter_context(xml.open('rb'))
            session['reader']=(ix,inp)
        return page_from_index(*session['reader'],int(page_id))
    with read_source(settings.wikipedia_direct_index) as ix,xml.open('rb') as inp:
        return page_from_index(ix,inp,int(page_id))


def _wikidata_previews(settings,qids):
    """Couches dérivées UNESCO: simples indices, jamais preuves Wikidata complètes."""
    wanted=set(qids);result={}
    if not wanted:return result
    root=Path(settings.unesco_root)/'branches'
    if not root.is_dir():return result
    for source in root.glob('unesco-mt*/derived/wikidata-full-facts-index.json'):
        if not wanted:break
        try:
            for entry in json.loads(source.read_text(encoding='utf-8-sig')).get('entities',[]):
                qid=entry.get('qid')
                if qid in wanted and qid not in result:
                    result[qid]={'qid':qid,'preview':entry.get('preview',[]),
                          'statement_count_reported':entry.get('statement_count'),
                          'source_path':str(source), 'provenance':'DERIVED_WIKIDATA_PREVIEW_NOT_ORIGINAL_STATEMENT'}
                    wanted.discard(qid)
        except (OSError,ValueError,TypeError):continue
    return result


@serialized
@_batch_articles
def make_enrichment(db,settings,branch=None):
    if _free_lane(db,settings.lane_count) is None:return None
    selected=[];sources={};words=bytes_count=0;errors=[];reused=0
    scanned=0;last=None;examined_pages=set()
    where='AND c.branch_id=?' if branch else ''
    while len(selected)<settings.enrich_pack_articles and scanned<settings.prepare_scan_limit:
        params=[branch] if branch else []
        cursor=''
        if last:
            cursor='AND (c.priority<? OR (c.priority=? AND c.candidate_id>?))'
            params += [last[0],last[0],last[1]]
        params += [min(128,settings.prepare_scan_limit-scanned)]
        rows=db.execute(f"""SELECT c.* FROM candidates c WHERE c.state='SELECTED' {where} {cursor}
                 ORDER BY c.priority DESC,c.candidate_id LIMIT ?""",params).fetchall()
        if not rows:break
        for row in rows:
            last=(row['priority'],row['candidate_id']);scanned+=1
            if row['page_id'] in examined_pages:continue
            pid=row['page_id'];examined_pages.add(pid)
            items=[dict(r) for r in db.execute(f"SELECT c.* FROM candidates c WHERE c.state='SELECTED' AND c.page_id=? {where}",
                                               (pid,branch) if branch else (pid,))]
            if not items:continue
            try:raw,revision,title=_read_article(settings,pid)
            except (ValueError,OSError,sqlite3.Error) as exc:
                _block_candidates(db,items,'SOURCE_BLOCKED',str(exc),settings.source_retry_seconds)
                errors.append({'page_id':pid,'reason':str(exc)[:180]});continue
            revision=str(revision);text_hash=sha(raw)
            concepts=sorted({x['concept_id'] for x in items});subjects=sorted({x['subject_key'] for x in items})
            # Reuse only explicit, successful coverage of this profile, revision and concepts.
            # A new domain requirement gets a targeted complement, never a fabricated fact/concept link.
            prior=[dict(x) for x in db.execute("""SELECT * FROM source_results WHERE page_id=? AND revision_id=?
              AND profile=? AND text_sha256=? AND status='PROCESSED' ORDER BY job_id""",
              (pid,revision,settings.extraction_profile,text_hash))]
            covered_concepts=set();covered_subjects=set()
            for prev in prior:
                covered_concepts.update(json.loads(prev['concepts_json']))
                covered_subjects.update(json.loads(prev['subjects_json']))
            reusable=[x for x in items if any(x['concept_id'] in json.loads(prev['concepts_json']) and x['subject_key'] in json.loads(prev['subjects_json']) for prev in prior)]
            if reusable:
                with db:
                    for item in reusable:
                        db.execute("UPDATE candidates SET state='REUSED',revision_id=? WHERE candidate_id=? AND state='SELECTED'",(revision,item['candidate_id']))
                        for prev in prior:
                            if item['concept_id'] in json.loads(prev['concepts_json']) and item['subject_key'] in json.loads(prev['subjects_json']):
                                db.execute('INSERT OR IGNORE INTO candidate_extractions VALUES(?,?,?,?)',
                                  (item['candidate_id'],prev['job_id'],pid,'REUSED_SAME_PROFILE_AND_CONCEPT'))
                        reused+=1
                items=[x for x in items if x not in reusable]
                if not items:continue
                concepts=sorted({x['concept_id'] for x in items});subjects=sorted({x['subject_key'] for x in items})
            wc=len(raw.decode('utf-8','replace').split())
            # V6: budget-mots SOUPLE; un grand article peut etre seul dans un pack.
            # La limite en octets reste ferme et explicite.
            if len(raw)>settings.enrich_byte_budget:
                _block_candidates(db,items,'OVERSIZE','Article au-dela du plafond octets; traitement special requis.',0)
                errors.append({'page_id':pid,'reason':'OVERSIZE_BYTES'});continue
            if selected and (words+wc>settings.enrich_word_budget or bytes_count+len(raw)>settings.enrich_byte_budget):continue
            file='articles/enwiki-'+str(pid)+'.wikitext.txt';sources[file]=raw
            prior_facts=[]
            # Le PARTIAL n'est JAMAIS reusable comme un PROCESSED.
            # Ses faits, en revanche, servent au complement et evitent les repetitions.
            prior_partial=[dict(x) for x in db.execute('''SELECT coverage_json FROM source_results
                WHERE page_id=? AND revision_id=? AND profile=? AND text_sha256=? AND status='PARTIAL'
                ORDER BY job_id''',(pid,revision,settings.extraction_profile,text_hash))]
            if prior or prior_partial:
                prior_facts=[dict(x) for x in db.execute("""SELECT proposal_id,statement,context_json FROM proposals
                  WHERE page_id=? AND revision_id=? AND status!='SUPERSEDED' ORDER BY proposal_id LIMIT 500""",(pid,revision))]
            selected.append({'page_id':pid,'revision_id':revision,'title':title,'text_path':file,
              'text_sha256':text_hash,'word_count':wc,'subjects':subjects,'concept_ids':concepts,
              'branches':sorted({x['branch_id'] for x in items}),'candidate_ids':[x['candidate_id'] for x in items],
              'extraction_profile':settings.extraction_profile,'task_mode':'TARGETED_COMPLEMENT' if (prior or prior_partial) else 'EXTRACTION',
              'prior_propositions':prior_facts,'prior_propositions_limit':500,
              'previous_partial_coverage':[json.loads(x['coverage_json']) for x in prior_partial]})
            words+=wc;bytes_count+=len(raw)
            if len(selected)>=settings.enrich_pack_articles or words>=settings.enrich_word_budget:break
    if not selected:
        if errors or reused or scanned:
            return {'status':'NO_PACK','reused':reused,'scanned':scanned,'blocked':errors[:20],
                    'scan_budget_reached':scanned>=settings.prepare_scan_limit}
        return None
    with db:jid=_nextid(db,'ENR')
    qids={subject[3:] for article in selected for subject in article['subjects'] if subject.startswith('wd:')}
    manifest={'format':'encyk.enrichment-pack.v32/2','job_id':jid,'articles_count':len(selected),
      'created_utc':utc(),'source_complete':True,'branch_scope':branch,'extraction_profile':settings.extraction_profile,
      'prompt_version':'32.2','canonical_admissions':0,'publication_authorized':False}
    files={**sources,'enrichment_pack.json':json_bytes(manifest),
      'articles.jsonl':('\n'.join(json.dumps(a,ensure_ascii=False) for a in selected)+'\n').encode(),
      'INSTRUCTIONS_CHATGPT.md':enrichment_prompt(jid).encode()}
    for qid,preview in _wikidata_previews(settings,qids).items():files['wikidata/'+qid+'.json']=json_bytes(preview)
    dst=settings.packs_path/(jid+'.zip');checksum=pack_zip(dst,files)
    with db:
        lane=_free_lane(db,settings.lane_count)
        if lane is None:raise RuntimeError('Aucun poste libre')
        db.execute('INSERT INTO jobs(job_id,kind,status,pack_path,pack_sha256,count,created_utc) VALUES (?,?,?,?,?,?,?)',
          (jid,'ENRICHMENT','READY',str(dst),checksum,len(selected),utc()))
        for article in selected:
            for cid in article['candidate_ids']:
                cur=db.execute("UPDATE candidates SET state='QUEUED_ENRICHMENT',revision_id=? WHERE candidate_id=? AND state='SELECTED'",(article['revision_id'],cid))
                if cur.rowcount!=1:raise RuntimeError('Candidat déjà réservé : '+cid)
                db.execute('INSERT INTO active_items VALUES(?,?)',(cid,jid))
                db.execute('INSERT INTO job_items VALUES(?,?)',(jid,cid))
        db.execute('UPDATE lanes SET job_id=? WHERE lane=?',(jid,lane))
    return {'job_id':jid,'kind':'ENRICHMENT','lane':lane,'count':len(selected),'words':words,
            'path':str(dst),'unavailable':errors[:20],'reused':reused}


def _block_candidates(db,items,state,reason,retry_seconds):
    deadline=(datetime.now(timezone.utc)+timedelta(seconds=retry_seconds)).isoformat(timespec='seconds')
    with db:
        for item in items:
            db.execute("UPDATE candidates SET state=?,decision_reason=? WHERE candidate_id=? AND state='SELECTED'",(state,reason,item['candidate_id']))
            db.execute("""INSERT INTO candidate_failures VALUES(?,1,?,?) ON CONFLICT(candidate_id)
              DO UPDATE SET attempts=attempts+1,reason=excluded.reason,next_retry_utc=excluded.next_retry_utc""",(item['candidate_id'],reason,deadline))


@serialized
def make_wave(db,settings,branch=None,kind='both'):
    outputs=[]
    with db:
        db.execute("""UPDATE candidates SET state='SELECTED' WHERE state='SOURCE_BLOCKED' AND candidate_id IN
          (SELECT candidate_id FROM candidate_failures WHERE next_retry_utc<=?)""",(utc(),))
    while _free_lane(db,settings.lane_count) is not None:
        job=make_enrichment(db,settings,branch) if kind in ('both','enrich') else None
        if job and job.get('status')=='NO_PACK':
            outputs.append(job);job=None
        if not job and kind in ('both','select'):job=make_selection(db,settings,branch)
        if not job:break
        outputs.append(job)
    return outputs


def read_return_zip(path):
    path=Path(path)
    if not path.is_file() or path.stat().st_size>115*1024*1024:raise ValueError('Retour introuvable ou excessif')
    if path.suffix.lower()=='.csv':return {path.name:path.read_bytes()}
    if path.suffix.lower()=='.json':return {path.name:path.read_bytes()}
    if path.suffix.lower()!='.zip':raise ValueError('Retour ZIP, CSV ou JSON attendu')
    result={};size=0
    with zipfile.ZipFile(path) as z:
        if len(z.infolist())>20:raise ValueError('Trop de fichiers de retour')
        for info in z.infolist():
            if info.is_dir():continue
            name=info.filename
            if '/' in name or '\\' in name or name.startswith('.') or (info.external_attr>>16)&0o170000==0o120000:
                raise ValueError('ZIP retour à chemin invalide')
            if info.file_size>100*1024*1024:raise ValueError('Retour décompressé excessif')
            size+=info.file_size
            if size>120*1024*1024:raise ValueError('ZIP décompressé excessif')
            if name in result:raise ValueError('Fichier retour dupliqué')
            result[name]=z.read(info)
    return result

def _get_job(db,jid):
    row=db.execute('SELECT * FROM jobs WHERE job_id=?',(jid,)).fetchone()
    if not row:raise ValueError('Tâche inconnue : '+jid)
    return dict(row)

def _source_pack(job):
    path=Path(job['pack_path'])
    if not path.is_file():raise ValueError('Pack source absent pour '+job['job_id'])
    if filehash(path)!=job['pack_sha256']:raise ValueError('Pack source modifié; aucune donnée importée')
    return zipfile.ZipFile(path)

def _selection_reply(files,jid):
    choices=[k for k in files if k in ('selection_decisions.csv','selection_decisions.jsonl',f'DECISIONS_{jid}.csv')]
    if len(choices)!=1:raise ValueError('Un seul fichier de décisions sélection attendu')
    name=choices[0];raw=files[name]
    if name.endswith('.jsonl'):
        rows=[json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
    else:
        r=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
        if not {'candidate_id','decision','justification'}.issubset(r.fieldnames or []):raise ValueError('Colonnes de décision absentes')
        rows=list(r)
    return rows

def _enrichment_reply(files):
    choices=[k for k in files if k in ('kristal_delta.json','proposals.json')]
    if len(choices)!=1:raise ValueError('kristal_delta.json attendu')
    return json.loads(files[choices[0]].decode('utf-8-sig'))


def import_reply(db,path):
    """Retour entier validé AVANT transaction; import sûr, partial, réentrant."""
    files=read_return_zip(path)
    # Resolve job ID only from declared response; filenames alone not trusted.
    jobid=None;delta=None
    if any(name.startswith('selection_decisions') or name.startswith('DECISIONS_') for name in files):
        for n in files:
            if n.startswith('DECISIONS_') and n.endswith('.csv'):jobid=n.removeprefix('DECISIONS_').removesuffix('.csv')
        if jobid is None:raise ValueError('Pour selection_decisions.csv, fournir --job-id via import_reply(...,job_id=...)')
    if 'kristal_delta.json' in files or 'proposals.json' in files:
        delta=_enrichment_reply(files);jobid=delta.get('job_id')
    if not jobid:raise ValueError('Identifiant de tâche absent')
    return import_for_job(db,path,jobid,files=files,delta=delta)


def _archive_return(db,path):
    path=Path(path)
    if not path.is_file() or path.stat().st_size>115*1024*1024:
        raise ValueError('Retour introuvable ou excessif')
    if path.suffix.lower() not in ('.zip','.csv','.json'):raise ValueError('Retour ZIP, CSV ou JSON attendu')
    raw=path.read_bytes()
    if len(raw)>115*1024*1024:raise ValueError('Retour excessif')
    checksum=sha(raw)
    root=database_path(db).parent/'returns';root.mkdir(exist_ok=True)
    target=root/(checksum+path.suffix.lower())
    if not target.exists():
        with tempfile.NamedTemporaryFile(dir=root,delete=False) as f:
            temp=Path(f.name);f.write(raw);f.flush();os.fsync(f.fileno())
        try:os.replace(temp,target)
        finally:temp.unlink(missing_ok=True)
    elif filehash(target)!=checksum:raise ValueError('Archive de retour altérée')
    with db:db.execute('INSERT OR IGNORE INTO return_archives VALUES(?,?,?)',(checksum,str(target),utc()))
    return target,checksum


def _validate_fact(fact,refs,source_text):
    if not isinstance(fact,dict):raise ValueError('Fait non JSON')
    pid=fact.get('page_id')
    if type(pid) is not int or pid not in refs:raise ValueError('Article source inconnu')
    if str(fact.get('revision_id',''))!=refs[pid]['revision_id']:raise ValueError('Révision de fait incorrecte')
    subject=fact.get('subject_key')
    if subject not in refs[pid]['subjects']:raise ValueError('Sujet hors pack; alignement séparé nécessaire')
    text=fact.get('statement');pred=fact.get('predicate');loc=fact.get('source_locator');quote=fact.get('source_quote')
    obj=fact.get('object')
    if not isinstance(obj,dict) or 'value' not in obj:raise ValueError('Objet factuel mal formé')
    kind=obj.get('type');value=obj['value']
    if kind=='number':
        good=type(value) in (int,float) and (not isinstance(value,float) or math.isfinite(value))
    elif kind=='boolean':good=type(value) is bool
    elif kind=='entity':good=isinstance(value,str) and bool(re.fullmatch(r'(?:wd:Q[1-9][0-9]*|Q[1-9][0-9]*|local:[\w.:-]+|enwiki:[1-9][0-9]*)',value))
    elif kind=='date':
        good=isinstance(value,str) and bool(re.fullmatch(r'-?\d{4,}(?:-\d{2}(?:-\d{2})?)?',value))
        if good and len(value)==10:
            from datetime import date
            try:date.fromisoformat(value)
            except ValueError:good=False
        elif good and len(value)==7:good=1<=int(value[5:7])<=12
    elif kind=='text':good=isinstance(value,str) and bool(value.strip())
    else:good=False
    if not good:raise ValueError('Valeur incompatible avec le type objet : '+str(kind))
    if not isinstance(text,str) or len(text.strip())<15 or not isinstance(pred,str) or not pred.strip():
        raise ValueError('Énoncé ou prédicat invalide')
    if not isinstance(quote,str) or not 5<=len(quote)<=500 or quote not in source_text[pid]:
        raise ValueError('Citation non présente dans la révision pour '+str(pid))
    if not isinstance(loc,str) or not loc.strip():raise ValueError('Localisateur manquant')
    concepts=fact.get('concept_ids',[])
    if not isinstance(concepts,list) or not all(isinstance(x,str) for x in concepts) or not set(concepts).issubset(refs[pid]['concept_ids']):
        raise ValueError('Concept étranger au pack')
    for key in ('qualifiers','context'):
        if key in fact and not isinstance(fact[key],dict):raise ValueError(key+' doit être un objet')
    if 'supersedes' in fact and not isinstance(fact['supersedes'],str):raise ValueError('supersedes invalide')
    # Conservative exact identity: all semantic and unknown fields retained.
    semantic={k:v for k,v in fact.items() if k not in ('source_quote','source_locator','concept_ids','supersedes')}
    semantic['revision_id']=str(fact['revision_id'])
    canonical=json.dumps(semantic,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))
    key='PROP2_'+sha(canonical.encode())[:40]
    context={k:v for k,v in semantic.items() if k not in ('subject_key','page_id','revision_id','statement','predicate','object')}
    return key,context


@serialized
def import_for_job(db,path,job_id,files=None,delta=None,correction=False,allow_partial=True):
    job=_get_job(db,job_id)
    archived,orig_sha=_archive_return(db,path)
    previous=db.execute('SELECT 1 FROM receipts WHERE job_id=? AND file_sha256=?',(job_id,orig_sha)).fetchone()
    if previous or job.get('return_sha256')==orig_sha:
        return {'status':'ALREADY_IMPORTED','job_id':job_id}
    terminal=job['status'] in ('DONE','PARTIAL','REVIEW_REQUIRED','DONE_EMPTY')
    if terminal and not correction:
        raise ValueError('RETURN_CONFLICT : retour différent pour une tâche terminée. Utiliser une correction explicite avec supersedes ou réexaminer les candidats.')
    if correction and (not terminal or job['kind']!='ENRICHMENT'):
        raise ValueError('Correction réservée aux tâches enrichissement terminées')
    if not terminal and job['status'] not in ('READY','SENT'):
        raise ValueError('État de tâche incompatible : '+job['status'])
    # Always parse the preserved bytes; caller-supplied parsed objects cannot bypass provenance.
    if archived.suffix=='.csv':files={'selection_decisions.csv':archived.read_bytes()}
    elif archived.suffix=='.json':files={'proposals.json':archived.read_bytes()}
    else:files=read_return_zip(archived)
    with _source_pack(job) as pack:
        if job['kind']=='SELECTION':
            parsed=_selection_reply(files,job_id)
            allowed={r[0] for r in db.execute('SELECT candidate_id FROM job_items WHERE job_id=?',(job_id,))}
            seen=set();values=[]
            for row in parsed:
                if not isinstance(row,dict):raise ValueError('Décision non objet')
                cid=row.get('candidate_id');decision=str(row.get('decision','')).upper().strip();just=str(row.get('justification','')).strip()
                if not isinstance(cid,str) or cid not in allowed or cid in seen:raise ValueError('ID de décision absent ou répété')
                if decision not in ('SELECT','REJECT','HOLD'):raise ValueError('Décision non reconnue')
                if len(just)<12:raise ValueError('Justification insuffisante')
                seen.add(cid);values.append((cid,decision,just))
            if not values:raise ValueError('Aucune décision')
            missing=allowed-seen
            with db:
                for cid,decision,just in values:
                    db.execute('INSERT INTO decision_history VALUES(?,?,?,?,?)',(cid,job_id,decision,just,utc()))
                    db.execute('INSERT OR REPLACE INTO decisions VALUES(?,?,?,?,?)',(cid,job_id,decision,just,utc()))
                    cur=db.execute("UPDATE candidates SET state=?,decision_reason=? WHERE candidate_id=? AND state='QUEUED_SELECTION'",
                        ({'SELECT':'SELECTED','REJECT':'REJECTED','HOLD':'HOLD'}[decision],just,cid))
                    if cur.rowcount!=1:raise ValueError('Réservation de sélection périmée')
                for cid in missing:db.execute("UPDATE candidates SET state='PENDING' WHERE candidate_id=? AND state='QUEUED_SELECTION'",(cid,))
                _finalize(db,job,orig_sha,archived,'PARTIAL' if missing else 'DONE','Décisions reçues '+str(len(values)))
            return {'status':'PARTIAL' if missing else 'IMPORTED','job_id':job_id,'decided':len(values),
                    'unanswered_requeued':len(missing),'counts':dict(Counter(d for _,d,_ in values))}
        if job['kind']!='ENRICHMENT':raise ValueError('Type de tâche inconnu')
        data=_enrichment_reply(files)
        if not isinstance(data,dict) or data.get('format') not in ('encyk.enrichment-delta.v32/1','encyk.enrichment-delta.v32/2') or data.get('job_id')!=job_id:
            raise ValueError('Format ou job_id non conforme')
        if data.get('canonical_admissions',0) not in (0,None) or data.get('publication_authorized',False) not in (False,None):
            raise ValueError('Admission canonique ou publication interdite')
        refs={r['page_id']:r for r in (json.loads(line) for line in pack.read('articles.jsonl').decode().splitlines() if line.strip())}
        manifest=json.loads(pack.read('enrichment_pack.json'))
        profile=manifest.get('extraction_profile','legacy.v32.1')
        coverage=data.get('source_coverage',[])
        if not isinstance(coverage,list):raise ValueError('source_coverage doit être une liste')
        coverage_map={}
        for item in coverage:
            if not isinstance(item,dict) or type(item.get('page_id')) is not int or item['page_id'] not in refs or item['page_id'] in coverage_map:
                raise ValueError('Couverture étrangère ou répétée')
            if not isinstance(item.get('note'),str) or not item['note'].strip():raise ValueError('Motif de couverture absent')
            status=item.get('status','legacy')
            if status not in ('legacy','processed','no_relevant_claim','incomplete','blocked'):raise ValueError('Statut de couverture invalide')
            coverage_map[item['page_id']]=item
        facts=data.get('facts',[])
        if not isinstance(facts,list) or len(facts)>25000:raise ValueError('Quantité de faits invalide')
        source_text={pid:pack.read(a['text_path']).decode('utf-8') for pid,a in refs.items()}
        valid=[];errors=[];bad_pages=set();seen_supersedes=set()
        for ordinal,fact in enumerate(facts):
            try:
                key,context=_validate_fact(fact,refs,source_text)
                supersedes=fact.get('supersedes')
                if correction and not supersedes:raise ValueError('Correction : supersedes obligatoire pour chaque fait')
                if supersedes:
                    old=db.execute('SELECT * FROM proposals WHERE proposal_id=?',(supersedes,)).fetchone()
                    if not old or old['subject_key']!=fact['subject_key'] or old['status']=='SUPERSEDED' or supersedes==key or supersedes in seen_supersedes:
                        raise ValueError('Cible supersedes absente, incompatible ou déjà remplacée')
                    if not correction:raise ValueError('Remplacement exige --correction sur le job original')
                    if old['source_job']!=job_id:raise ValueError('Correction rattachée au mauvais job original')
                    seen_supersedes.add(supersedes)
                valid.append((ordinal,fact,key,context))
            except (ValueError,TypeError,OverflowError) as exc:
                errors.append((ordinal,str(exc),fact))
                if isinstance(fact,dict) and type(fact.get('page_id')) is int and fact['page_id'] in refs:bad_pages.add(fact['page_id'])
                else:bad_pages.update(refs)
        if errors:
            with db:
                for ordinal,error,payload in errors:
                    db.execute('INSERT OR REPLACE INTO import_errors VALUES(?,?,?,?,?)',
                        (job_id,orig_sha,ordinal,error,json.dumps(payload,ensure_ascii=False)))
            if not valid or not allow_partial or correction:
                raise ValueError('Retour archivé, faits invalides : '+errors[0][1])
        if correction and not valid:raise ValueError('Correction vide')
        counts=Counter(f['page_id'] for _,f,_,_ in valid)
        outcomes={}
        for pid in refs:
            entry=coverage_map.get(pid);declared=entry.get('status','legacy') if entry else 'incomplete'
            if pid in bad_pages or declared in ('incomplete','blocked'):state='PARTIAL' if declared!='blocked' else 'SOURCE_BLOCKED'
            elif counts[pid]>0 and declared=='no_relevant_claim':raise ValueError('Couverture contradictoire : faits et absence de faits déclarés')
            elif counts[pid]>0:state='PROCESSED'
            elif declared=='no_relevant_claim':state='NO_RELEVANT_CLAIM'
            else:state='NO_FACTS_REVIEW'
            outcomes[pid]=state
        if not allow_partial and any(v not in ('PROCESSED','NO_RELEVANT_CLAIM') for v in outcomes.values()):
            raise ValueError('Mode strict : couverture incomplète ou résultat à examiner')
        with db:
            added=0
            for ordinal,fact,key,context in valid:
                obj=json.dumps(fact['object'],sort_keys=True,ensure_ascii=False,allow_nan=False)
                payload=json.dumps(fact,ensure_ascii=False,sort_keys=True,allow_nan=False)
                status='DRAFT' if fact.get('concept_ids') else 'UNASSIGNED'
                existing=db.execute('SELECT status FROM proposals WHERE proposal_id=?',(key,)).fetchone()
                if existing and existing[0]=='SUPERSEDED':raise ValueError('Proposition retirée; ne pas la réactiver implicitement')
                cur=db.execute('''INSERT OR IGNORE INTO proposals(proposal_id,subject_key,page_id,revision_id,statement,predicate,
                  object_json,source_quote,source_locator,status,source_job,created_utc,context_json,payload_json,supersedes)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                  (key,fact['subject_key'],fact['page_id'],str(fact['revision_id']),fact['statement'].strip(),fact['predicate'],
                   obj,fact['source_quote'],fact['source_locator'],status,job_id,utc(),json.dumps(context,ensure_ascii=False,sort_keys=True),payload,fact.get('supersedes')))
                added+=cur.rowcount
                db.execute('INSERT INTO proposal_occurrences VALUES(?,?,?,?,?)',(key,job_id,orig_sha,ordinal,payload))
                db.execute('INSERT OR IGNORE INTO proposal_citations VALUES(?,?,?,?,?)',
                    (key,fact['page_id'],str(fact['revision_id']),fact['source_quote'],fact['source_locator']))
                for cid in fact.get('concept_ids',[]):db.execute('INSERT OR IGNORE INTO proposal_concepts VALUES(?,?)',(key,cid))
                if fact.get('concept_ids'):db.execute("UPDATE proposals SET status='DRAFT' WHERE proposal_id=? AND status='UNASSIGNED'",(key,))
                if fact.get('supersedes'):
                    db.execute("UPDATE proposals SET status='SUPERSEDED' WHERE proposal_id=?",(fact['supersedes'],))
                    db.execute('INSERT INTO proposal_replacements VALUES(?,?,?,?,?)',(fact['supersedes'],key,job_id,orig_sha,utc()))
                    db.execute("""UPDATE source_results SET status='INVALIDATED' WHERE job_id IN
                      (SELECT job_id FROM proposal_occurrences WHERE proposal_id=?)""",(fact['supersedes'],))
            if not correction:
                for pid,a in refs.items():
                    entry=coverage_map.get(pid,{'page_id':pid,'status':'incomplete','note':'Couverture absente du retour'})
                    db.execute('INSERT OR REPLACE INTO source_results VALUES(?,?,?,?,?,?,?,?,?)',
                      (job_id,pid,a['revision_id'],profile,a['text_sha256'],('PROCESSED_LEGACY' if outcomes[pid]=='PROCESSED' and entry.get('status')!='processed' else outcomes[pid]),json.dumps(entry,ensure_ascii=False),
                       json.dumps(a['concept_ids']),json.dumps(a['subjects'])))
                    db.execute('INSERT OR REPLACE INTO article_sources VALUES(?,?,?,?,?)',
                      (pid,a['revision_id'],a['title'],a['text_sha256'],job['pack_path']+'!'+a['text_path']))
                    target={'PROCESSED':'ENRICHED','PARTIAL':'PARTIAL','SOURCE_BLOCKED':'SOURCE_BLOCKED',
                            'NO_RELEVANT_CLAIM':'NO_RELEVANT_CLAIM','NO_FACTS_REVIEW':'NO_FACTS_REVIEW'}[outcomes[pid]]
                    for cid in a['candidate_ids']:
                        cur=db.execute("UPDATE candidates SET state=?,decision_reason=? WHERE candidate_id=? AND state='QUEUED_ENRICHMENT'",(target,entry['note'],cid))
                        if cur.rowcount!=1:raise ValueError('Réservation enrichissement périmée')
                        db.execute('INSERT OR IGNORE INTO candidate_extractions VALUES(?,?,?,?)',(cid,job_id,pid,'EXTRACTED'))
                        if target=='SOURCE_BLOCKED':
                            deadline=(datetime.now(timezone.utc)+timedelta(hours=1)).isoformat(timespec='seconds')
                            db.execute('INSERT OR REPLACE INTO candidate_failures VALUES(?,1,?,?)',(cid,entry['note'],deadline))
            if correction:result_status='DONE'
            elif any(v in ('PARTIAL','SOURCE_BLOCKED') for v in outcomes.values()):result_status='PARTIAL'
            elif 'NO_FACTS_REVIEW' in outcomes.values():result_status='REVIEW_REQUIRED'
            elif not valid:result_status='DONE_EMPTY'
            else:result_status='DONE'
            _finalize(db,job,orig_sha,archived,result_status,'Propositions '+str(len(valid))+', erreurs '+str(len(errors)))
        return {'status':'CORRECTED' if correction else ('IMPORTED' if result_status=='DONE' else result_status),
            'job_id':job_id,'claims_submitted':len(facts),'new_proposals':added,'invalid_facts':len(errors),
            'source_results':outcomes,'empty_batch':not bool(valid),'archive_path':str(archived),
            'canonical_admissions':0,'publication_authorized':False}


def _finalize(db,job,orig_sha,path,status,detail):
    db.execute('UPDATE jobs SET status=?,completed_utc=?,return_sha256=? WHERE job_id=?',(status,utc(),orig_sha,job['job_id']))
    db.execute('UPDATE lanes SET job_id=NULL WHERE job_id=?',(job['job_id'],))
    db.execute('DELETE FROM active_items WHERE job_id=?',(job['job_id'],))
    db.execute('INSERT INTO receipts(created_utc,filename,file_sha256,job_id,status,detail) VALUES(?,?,?,?,?,?)',
      (utc(),str(path),orig_sha,job['job_id'],status,detail))


@serialized
def retry_candidates(db,candidate_ids,reason):
    if not isinstance(reason,str) or len(reason.strip())<12:raise ValueError('Justifier le réexamen (12 caractères minimum)')
    if not candidate_ids:raise ValueError('Aucun candidat choisi')
    with db:
        for cid in candidate_ids:
            row=db.execute('SELECT state FROM candidates WHERE candidate_id=?',(cid,)).fetchone()
            if not row or row[0] not in ('HOLD','REJECTED','SOURCE_BLOCKED','OVERSIZE','PARTIAL','NO_FACTS_REVIEW','NO_RELEVANT_CLAIM'):
                raise ValueError('Candidat non réexaminable : '+str(cid))
            if db.execute('SELECT 1 FROM active_items WHERE candidate_id=?',(cid,)).fetchone():raise ValueError('Candidat réservé')
            target='PENDING' if row[0] in ('HOLD','REJECTED') else 'SELECTED'
            db.execute('UPDATE candidates SET state=?,decision_reason=? WHERE candidate_id=?',(target,reason,cid))
            db.execute('DELETE FROM candidate_failures WHERE candidate_id=?',(cid,))
            db.execute('INSERT INTO events(created_utc,kind,details) VALUES(?,?,?)',
                (utc(),'RETRY',json.dumps({'candidate_id':cid,'from':row[0],'to':target,'reason':reason})))
    return {'retried':len(candidate_ids)}


@serialized
def cancel_job(db,job_id,reason):
    if len(reason.strip())<12:raise ValueError('Motif détaillé requis')
    job=_get_job(db,job_id)
    if job['status'] not in ('READY','SENT'):raise ValueError('Tâche non active')
    target='PENDING' if job['kind']=='SELECTION' else 'SELECTED'
    with db:
        db.execute('UPDATE candidates SET state=? WHERE candidate_id IN (SELECT candidate_id FROM active_items WHERE job_id=?)',(target,job_id))
        db.execute('DELETE FROM active_items WHERE job_id=?',(job_id,))
        db.execute('UPDATE lanes SET job_id=NULL WHERE job_id=?',(job_id,))
        db.execute("UPDATE jobs SET status='CANCELLED',completed_utc=? WHERE job_id=?",(utc(),job_id))
        db.execute('INSERT INTO events(created_utc,kind,details) VALUES(?,?,?)',(utc(),'CANCEL',json.dumps({'job_id':job_id,'reason':reason})))
    return {'status':'CANCELLED','job_id':job_id,'late_returns':'REFUSED'}


@serialized
def recovery_report(db):
    """Read-only reconciliation: preserve orphan files; never silently cancel active work."""
    root=database_path(db).parent/'packs'
    known={str(Path(x[0]).resolve()) for x in db.execute('SELECT pack_path FROM jobs')}
    orphan=[str(x) for x in root.glob('*.zip') if str(x.resolve()) not in known]
    broken=[]
    for row in db.execute("SELECT * FROM jobs WHERE status IN ('READY','SENT')"):
        try:
            with _source_pack(dict(row)):pass
        except (ValueError,OSError,zipfile.BadZipFile) as exc:broken.append({'job_id':row['job_id'],'reason':str(exc)})
    unreserved=[x[0] for x in db.execute("""SELECT candidate_id FROM candidates WHERE state IN ('QUEUED_SELECTION','QUEUED_ENRICHMENT')
      AND candidate_id NOT IN (SELECT candidate_id FROM active_items)""")]
    return {'orphan_packs_preserved':orphan,'broken_active_jobs':broken,'queued_without_reservation':unreserved,
      'action':'Utiliser cancel-job avec un motif pour libérer une tâche cassée; les retours tardifs seront refusés.'}


def jobs_overview(db):
    return {'lanes':[dict(r) for r in db.execute('SELECT * FROM lanes ORDER BY lane')],
      'jobs':[dict(r) for r in db.execute("""SELECT job_id,kind,status,pack_path,count,created_utc FROM jobs
         ORDER BY CASE WHEN status IN ('READY','SENT') THEN 0 ELSE 1 END,created_utc DESC,job_id DESC LIMIT 50""")],
      'candidates':dict(db.execute('SELECT state,COUNT(*) FROM candidates GROUP BY state')),
      'proposals':db.execute("SELECT COUNT(*) FROM proposals WHERE status!='SUPERSEDED'").fetchone()[0],
      'branches':db.execute('SELECT COUNT(*) FROM branches').fetchone()[0],
      'source_results':dict(db.execute('SELECT status,COUNT(*) FROM source_results GROUP BY status')),
      'import_errors':db.execute('SELECT COUNT(*) FROM import_errors').fetchone()[0]}


@serialized
def export_proposals(db,path,branch=None):
    if branch:
        rows=db.execute('''SELECT DISTINCT p.* FROM proposals p JOIN proposal_concepts pc ON pc.proposal_id=p.proposal_id
          JOIN branch_concepts bc ON bc.concept_id=pc.concept_id WHERE bc.branch_id=? ORDER BY p.proposal_id''',(branch,))
    else:rows=db.execute('SELECT * FROM proposals ORDER BY proposal_id')
    out=Path(path);out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=out.parent,delete=False) as f:
        temp=Path(f.name)
        try:
            for r in rows:
                v=dict(r);v['object']=json.loads(v.pop('object_json'));v['context']=json.loads(v.pop('context_json'))
                v['original_payload']=json.loads(v.pop('payload_json'))
                v['concept_ids']=[x[0] for x in db.execute('SELECT concept_id FROM proposal_concepts WHERE proposal_id=?',(v['proposal_id'],))]
                v['citations']=[dict(x) for x in db.execute('SELECT page_id,revision_id,quote,locator FROM proposal_citations WHERE proposal_id=?',(v['proposal_id'],))]
                v['occurrences']=[dict(x) for x in db.execute('SELECT job_id,return_sha256,ordinal,payload_json FROM proposal_occurrences WHERE proposal_id=?',(v['proposal_id'],))]
                for occurrence in v['occurrences']:occurrence['payload']=json.loads(occurrence.pop('payload_json'))
                v['replacements']=[dict(x) for x in db.execute('SELECT * FROM proposal_replacements WHERE old_id=? OR new_id=?',(v['proposal_id'],v['proposal_id']))]
                v['admission_status']='NOT_ADMITTED_PRIVATE_PROPOSAL'
                f.write(json.dumps(v,ensure_ascii=False)+'\n')
            f.flush();os.fsync(f.fileno())
        except Exception:
            f.close();temp.unlink(missing_ok=True);raise
    try:os.replace(temp,out)
    finally:temp.unlink(missing_ok=True)
    return str(out)
