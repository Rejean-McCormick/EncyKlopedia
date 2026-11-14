#!/usr/bin/env python3
"""EncyKlopedia v30: local ten-lane production orchestrator.

Stdlib only, durable SQLite state, immutable task inputs, validated data-only returns.
The installed v27/v28 engines remain the exclusive writers of Kristal/catalogue.
"""
from __future__ import annotations
import argparse
import base64
import csv
from datetime import datetime, timezone
from contextlib import closing
from email import policy
from email.parser import BytesParser
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import statistics
import shutil
import sqlite3
import subprocess
import sys
# ENCYK_V315_IMPORT_ROUTAGE_START
_encyk_pilot_dir = str(Path(__file__).resolve().parent)
if _encyk_pilot_dir not in sys.path:
    sys.path.insert(0, _encyk_pilot_dir)
# ENCYK_V315_IMPORT_ROUTAGE_END
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse
import webbrowser
import zipfile

VERSION='encyklopedia.station.v30/1'
LANES=10
REVIEW_SIZE=880
MIN_REVIEW_SIZE=650
MAX_REVIEW_SIZE=880
REVIEW_BUDGET=3200
QUEUE_BUFFER=20
MAX_REQUEST=110*1024*1024
MAX_FILE=100*1024*1024
MAX_UNPACK=130*1024*1024
WORK_DEFAULT=Path(r'D:\EncyKlopedia\30_working\poste_chatgpt_v30')
V27_DEFAULT=Path(r'D:\EncyKlopedia\30_working\production_kristals_v27')
V28_DEFAULT=Path(r'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28')
CAT_DEFAULT=Path(r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite')
FIELDS=['candidate_id','branch_id','concept_id','concept_en','page_id','title','priority',
        'seed_count','link_evidence','category_evidence','subcategory_evidence','evidence_sha256',
        'examples','decision','justification']
CLOSED=('DONE','SKIPPED')
OPEN=('WAITING','READY','SENT','ERROR','IMPORTING','NEEDS_CONFIRMATION')

SCHEMA='''
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS jobs(
 id TEXT PRIMARY KEY,kind TEXT NOT NULL,key TEXT NOT NULL,count INTEGER NOT NULL,
 status TEXT NOT NULL,source_path TEXT NOT NULL,source_sha256 TEXT NOT NULL,
 bundle_path TEXT NOT NULL,bundle_sha256 TEXT NOT NULL DEFAULT '',
 created_utc TEXT NOT NULL,sent_utc TEXT,finished_utc TEXT,return_sha256 TEXT,
 error TEXT NOT NULL DEFAULT '',attempts INTEGER NOT NULL DEFAULT 0,
 review_approved INTEGER NOT NULL DEFAULT 0,review_rejected INTEGER NOT NULL DEFAULT 0,
 review_hold INTEGER NOT NULL DEFAULT 0,review_return_path TEXT,
 source_generation TEXT NOT NULL DEFAULT '');
CREATE INDEX IF NOT EXISTS idx_job_queue ON jobs(status,created_utc,id);
CREATE INDEX IF NOT EXISTS idx_job_kind ON jobs(kind,status);
CREATE TABLE IF NOT EXISTS lanes(lane INTEGER PRIMARY KEY CHECK(lane BETWEEN 1 AND 10),job_id TEXT REFERENCES jobs(id));
CREATE TABLE IF NOT EXISTS review_index(
 candidate_id TEXT PRIMARY KEY,branch_id TEXT NOT NULL,concept_id TEXT NOT NULL,
 page_id INTEGER NOT NULL,title TEXT NOT NULL,priority INTEGER NOT NULL,
 seed_count INTEGER NOT NULL,link_evidence INTEGER NOT NULL,
 category_evidence INTEGER NOT NULL,subcategory_evidence INTEGER NOT NULL,
 state TEXT NOT NULL DEFAULT 'PENDING',task_id TEXT,evidence_sha256 TEXT,
 last_seen_utc TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_review_priority ON review_index(state,priority DESC,seed_count DESC,page_id ASC);
CREATE TABLE IF NOT EXISTS receipts(id INTEGER PRIMARY KEY AUTOINCREMENT,at_utc TEXT NOT NULL,
 filename TEXT NOT NULL,job_id TEXT,status TEXT NOT NULL,detail TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,at_utc TEXT NOT NULL,message TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS v311_job_routes(job_id TEXT PRIMARY KEY REFERENCES jobs(id),branch_id TEXT NOT NULL,manifest_path TEXT NOT NULL,stage_path TEXT NOT NULL,work_path TEXT NOT NULL,branch_signature TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS updates(id TEXT PRIMARY KEY,status TEXT NOT NULL,manifest_json TEXT NOT NULL,zip_path TEXT NOT NULL,backup_path TEXT NOT NULL,created_utc TEXT NOT NULL,applied_utc TEXT,error TEXT NOT NULL DEFAULT '');
'''

def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def sha_path(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def uri_ro(path:Path):
    if not path.is_file():raise ValueError('Base SQLite absente : '+str(path))
    con=sqlite3.connect('file:'+path.resolve().as_posix()+'?mode=ro',uri=True,timeout=5)
    con.row_factory=sqlite3.Row
    return con

def csv_bytes(rows:list[dict])->bytes:
    f=io.StringIO(newline='');w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore',lineterminator='\n')
    w.writeheader();w.writerows(rows)
    return ('\ufeff'+f.getvalue()).encode('utf-8')

def read_baseline(raw:bytes):
    try:r=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline=''))
    except UnicodeDecodeError as ex:raise ValueError('CSV source non UTF-8') from ex
    if not set(FIELDS).issubset(r.fieldnames or []):raise ValueError('Colonnes source UNESCO absentes')
    rows=list(r)
    if not rows or len(rows)>20000:raise ValueError('CSV source vide ou trop volumineux')
    if len({x['candidate_id'] for x in rows})!=len(rows):raise ValueError('Identifiants source dupliqués')
    return rows

def parse_reply_csv(raw:bytes):
    try:r=csv.DictReader(io.StringIO(raw.decode('utf-8-sig'),newline=''))
    except UnicodeDecodeError as ex:raise ValueError('CSV retour non UTF-8') from ex
    hdr=r.fieldnames or []
    if len(hdr)==3 and set(hdr)=={'candidate_id','decision','justification'}:mode='short'
    elif set(FIELDS).issubset(hdr):mode='full'
    else:raise ValueError('Retour CSV : colonnes candidate_id,decision,justification requises')
    rows=list(r)
    if len(rows)>20000:raise ValueError('Trop de décisions dans le CSV retour')
    if any(None in x for x in rows):raise ValueError('CSV mal formé : colonnes excédentaires')
    return mode,rows

def json_text(obj):return (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

def prompt(job):
    if job['kind']=='v27':
        return f'''ENCYKLOPEDIA — KRISTAL PRIVE v27 — {job['key']}\n\nANALYSE LE ZIP JOINT: {Path(job['bundle_path']).name}\nSHA-256 exact du pack: {job['source_sha256']}\n\nLis MANIFEST_PACK_V27.json, MODELE_DELTA_KRISTAL_V27.json et les textes complets. Extrait des faits encyclopédiques SELECTIFS, précis, appuyés sur leurs propres passages. Ne fabrique rien d'après un titre ou une déduction. Source Wikipédia non vérifiée indépendamment. Respecte chaque page_id, revision_id et concept_id. Fournis source_locator et courte source_quote quand disponible. Garde les rattachements UNESCO uniquement si le contenu les justifie. Pas de canon, pas de publication.\n\nRENVOIE UN SEUL ZIP contenant DELTA_KRISTAL_{job['key']}.json conforme au modèle du pack, format encyklopedia.kristal-ai-delta.v27/1, pack_id={job['key']}, pack_sha256={job['source_sha256']}, canonical_admissions=0, publication_authorized=false. AUCUN script ou exécutable. La validité des faits est toujours candidate, pas canonique.\n'''
    return f'''ENCYKLOPEDIA — REVUE UNESCO v28 — TACHE {job['id']}\n\nANALYSE LE ZIP JOINT : {Path(job['bundle_path']).name} ({job['count']} propositions).\n\nLis chaque ligne du CSV REVUE_*.csv ET du fichier CONTEXTES_DOCUMENTAIRES_V28.jsonl (meme candidate_id). Lis toutes les propositions, meme dans les lots de 650 a 880 (dernier lot possiblement plus petit). Les preuves complementaires incluent les notes de portee UNESCO, les categories et, si disponible, un extrait du texte Wikipedia original par index local. Le manifeste indique explicitement les textes absents. APPROVE lorsque l'article traite substantiellement du concept UNESCO (pas une simple mention). Justification concise en francais de 20 caracteres minimum, expliquant le lien sans inventer de faits. REJECT les rapprochements manifestement hors sujet ou accessoires. HOLD seulement si l'information disponible ne permet pas une decision defendable. Ne fabrique aucun fait, ni connaissance canonique.\n\nRENVOIE UN SEUL ZIP contenant exactement DECISIONS_{job['id']}.csv, UTF-8, avec STRICTEMENT trois colonnes candidate_id,decision,justification. OBLIGATOIRE : une ligne pour CHACUN des {job['count']} candidate_id, y compris HOLD. Ceci prouve au moins que chaque candidat a reçu une décision; ne fabrique aucun identifiant. Un CSV de réponses abrégé peut être accepté pour compatibilité, mais l'interface exigera alors une confirmation humaine avant import. Une revue tout-HOLD demande aussi confirmation. N'ajoute aucun code exécutable.\n\nAprès vérification des identifiants et des preuves, l'interface reconstruira le CSV complet pour le véritable importeur v28.\n'''


def extract_zip_files(name:str,raw:bytes):
    if not raw.startswith(b'PK\x03\x04'):
        if name.lower().endswith(('.json','.csv')):return [(Path(name).name,raw)]
        raise ValueError('Retour attendu : ZIP contenant CSV ou JSON')
    out=[];total=0
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if len(z.infolist())>50:raise ValueError('Trop de fichiers dans le ZIP retour')
            for x in z.infolist():
                if x.is_dir():continue
                if x.flag_bits&1:raise ValueError('ZIP chiffré refusé')
                if (x.external_attr>>16)&0o170000==0o120000:raise ValueError('Lien symbolique dans le ZIP refusé')
                if x.file_size>MAX_UNPACK:raise ValueError('Fichier décompressé trop volumineux')
                total+=x.file_size
                if total>MAX_UNPACK:raise ValueError('ZIP trop volumineux après décompression')
                base=Path(x.filename.replace('\\','/')).name
                if not base or x.filename.replace('\\','/').startswith('/') or '..' in x.filename.replace('\\','/').split('/'):
                    raise ValueError('Chemin ZIP non fiable')
                ext=Path(base).suffix.lower()
                if ext in ('.csv','.json'):out.append((base,z.read(x)))
                elif ext not in ('.txt','.md'):raise ValueError('Type de fichier interdit dans ZIP retour : '+ext)
    except (zipfile.BadZipFile,RuntimeError) as ex:raise ValueError('ZIP invalide') from ex
    if not out:raise ValueError('ZIP sans CSV ou JSON exploitable')
    return out

class Station:
    def __init__(self,repo:Path,work:Path,v27:Path=V27_DEFAULT,v28:Path=V28_DEFAULT,catalogue:Path=CAT_DEFAULT):
        self.repo=repo.resolve();self.work=work.resolve();self.v27=v27;self.v28=v28;self.catalogue=catalogue
        self.lock=threading.RLock();self.busy=False;self.operation='';self._event_count=0
        self.work.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.work/'station_v30.sqlite',check_same_thread=False,timeout=15)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL');self.db.execute('PRAGMA busy_timeout=10000')
        self.db.executescript(SCHEMA)
        for i in range(1,LANES+1):self.db.execute('INSERT OR IGNORE INTO lanes(lane,job_id) VALUES(?,NULL)',(i,))
        self.db.commit()
        self._log('Poste v30 initialisé — file persistante SQLite')
        self._migrate_v29()
        with self.lock:
            with self.db:
                self.db.execute("UPDATE jobs SET status='ERROR',error='Import interrompu : redéposer le retour pour reprendre sans doublon' WHERE status='IMPORTING'")
                self._fill_lanes()

    def _log(self,message):
        with self.lock:
            with self.db:
                self.db.execute('INSERT INTO events(at_utc,message) VALUES(?,?)',(now(),str(message)[:900]))
                self._event_count+=1
                if self._event_count%200==0:
                    self.db.execute('DELETE FROM events WHERE id < (SELECT MAX(id)-6000 FROM events)')

    def _row(self,id):return self.db.execute('SELECT * FROM jobs WHERE id=?',(id,)).fetchone()
    def _jobs(self,status=None):
        if status:return list(self.db.execute('SELECT * FROM jobs WHERE status=? ORDER BY created_utc,id',(status,)))
        return list(self.db.execute('SELECT * FROM jobs ORDER BY created_utc,id'))

    def _migrate_v29(self):
        path=self.work.parent/'poste_chatgpt_v29'/'state.json'
        if not path.is_file() or self.db.execute('SELECT count(*) FROM jobs').fetchone()[0]:return
        try:
            data=json.loads(path.read_text('utf-8'))
            if not str(data.get('version','')).startswith('encyklopedia.poste-chatgpt.v29'):return
            added=0
            with self.db:
                for old in data.get('jobs',[]):
                    if old.get('kind') not in ('v27','v28') or not old.get('id'):continue
                    src=Path(old.get('source',''));bun=Path(old.get('bundle',''))
                    if not src.is_file() or not bun.is_file():continue
                    status=old.get('status','WAITING')
                    status={'ACTIVE':'READY','WAITING':'WAITING','IMPORTING':'ERROR'}.get(status,status)
                    if status not in ('WAITING','READY','ERROR','DONE'):status='ERROR'
                    source_hash=old.get('source_sha256') or sha_path(src)
                    self.db.execute('''INSERT OR IGNORE INTO jobs(id,kind,key,count,status,source_path,source_sha256,
                      bundle_path,bundle_sha256,created_utc,error) VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                      (old['id'],old['kind'],old.get('key',old['id']),int(old.get('count',0)),status,
                       str(src),source_hash,str(bun),sha_path(bun),old.get('created',now()),old.get('error','')))
                    if old.get('kind')=='v28':
                        for pair in old.get('pairs',[]):
                            cid=pair.split(':',1)[0]
                            # A legacy task must not be scheduled a second time by the v30 index.
                            self.db.execute('INSERT OR IGNORE INTO review_index(candidate_id,branch_id,concept_id,page_id,title,priority,seed_count,link_evidence,category_evidence,subcategory_evidence,state,task_id,evidence_sha256,last_seen_utc) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                              (cid,'legacy','','0','',0,0,0,0,0,'DONE' if status=='DONE' else 'QUEUED',old['id'],pair.split(':',1)[-1],now()))
                    added+=1
            self._log(f'Migration v29 : {added} tâches conservées, anciens fichiers intacts')
        except (OSError,ValueError,sqlite3.Error) as ex:self._log('Migration v29 ignorée : '+str(ex))

    def _fill_lanes(self):
        # Preserve assigned tasks; distribute newly free slots fairly between v27/v28.
        in_lane={'v27':0,'v28':0}
        for r in self.db.execute("""SELECT j.kind,count(*) AS n FROM lanes l JOIN jobs j ON j.id=l.job_id
                                   WHERE j.status NOT IN ('DONE','SKIPPED') GROUP BY j.kind"""):
            in_lane[r['kind']]=r['n']
        for lane in range(1,LANES+1):
            row=self.db.execute('SELECT job_id FROM lanes WHERE lane=?',(lane,)).fetchone()
            job=self._row(row['job_id']) if row and row['job_id'] else None
            if job is not None and job['status'] not in CLOSED:continue
            self.db.execute('UPDATE lanes SET job_id=NULL WHERE lane=?',(lane,))
            picks=[]
            for kind in ('v27','v28'):
                candidate=self.db.execute("""SELECT id,kind,created_utc FROM jobs
                    WHERE status='WAITING' AND kind=? AND id NOT IN
                    (SELECT job_id FROM lanes WHERE job_id IS NOT NULL)
                    ORDER BY created_utc,id LIMIT 1""",(kind,)).fetchone()
                if candidate:picks.append(candidate)
            if not picks:continue
            chosen=min(picks,key=lambda x:(in_lane[x['kind']],x['created_utc'],x['id']))
            self.db.execute("UPDATE jobs SET status='READY' WHERE id=?",(chosen['id'],))
            self.db.execute('UPDATE lanes SET job_id=? WHERE lane=?',(chosen['id'],lane))
            in_lane[chosen['kind']]+=1

    def _counts(self):
        x={'articles':None,'claims':None,'deltas':None,'packs':None}
        db=self.v27/'KRISTAL_CUMULATIF_PRIVE_V27.sqlite'
        if db.is_file():
            try:
                with closing(uri_ro(db)) as c:
                    x['claims']=c.execute('SELECT count(*) FROM claims').fetchone()[0]
                    x['deltas']=c.execute('SELECT count(*) FROM delta_imports').fetchone()[0]
            except sqlite3.Error:pass
        if self.catalogue.is_file():
            try:
                with closing(uri_ro(self.catalogue)) as c:x['articles']=c.execute('SELECT count(*) FROM articles').fetchone()[0]
            except sqlite3.Error:pass
        packs=self.v27/'packs'
        if packs.is_dir():x['packs']=len(list(packs.glob('PACK_V27_*.zip')))
        return x

    def _small_ready_group(self):
        # Group only already-prepared UNESCO jobs. NEVER rewrite their source ZIP,
        # review_index, hashes, lane assignments or frozen evidence.
        selected=[];total=0
        for j in self.db.execute("""SELECT * FROM jobs WHERE kind='v28' AND status='READY'
                                   AND count BETWEEN 1 AND 300 ORDER BY created_utc,id"""):
            if len(selected)>=10:break
            if total+int(j['count'])>880:continue
            selected.append(j);total+=int(j['count'])
        return selected,total

    def dispatch_small_v315(self):
        # Multiple unchanged task ZIPs carried in a single transfer envelope.
        # One response ZIP with separate DECISIONS_<task_id>.csv files can be
        # imported through the existing, fully validated multi-CSV importer.
        with self.lock:
            group,total=self._small_ready_group()
            if len(group)<2:raise ValueError('Au moins deux petits packs UNESCO READY sont requis')
            parts=[];nbytes=0
            for j in group:
                # bundle() checks the immutable original and enriches in a cache.
                path=self.bundle(j['id'])
                raw=path.read_bytes()
                if not zipfile.is_zipfile(io.BytesIO(raw)):
                    raise ValueError('Bundle non ZIP : '+j['id'])
                nbytes+=len(raw)
                if nbytes>80*1024*1024:
                    raise ValueError('Lot consolidé >80 Mio; utiliser les packs individuellement')
                parts.append((j,raw))
            manifest={'format':'encyklopedia.transfert-multi-v28.v315/1',
                      'mode':'transport-uniquement','count':total,'tasks':[
                {'job_id':j['id'],'candidate_count':j['count'],
                 'source_sha256':j['source_sha256'],'bundle_transfer_sha256':sha(raw)}
                for j,raw in parts]}
            instruction=['ENCYKLOPEDIA — TRANSFERT GROUPE DE PETITS PACKS UNESCO v28',
                'Ce ZIP est une enveloppe de transport. Chaque ZIP dans PACKS/ reste une tâche originale distincte.',
                'Lis et décompresse TOUS les ZIP contenus dans PACKS/, puis examine chaque REVUE_*.csv avec son contexte.',
                'Pour chaque tâche, produis EXACTEMENT DECISIONS_<job_id>.csv : colonnes candidate_id,decision,justification.',
                'Une ligne pour CHACUN des candidate_id du CSV original, sans exception, y compris HOLD.',
                'APPROVE si le sujet traite substantiellement du concept UNESCO; REJECT si lien accessoire; HOLD si incertain.',
                'Justifications APPROVE en français d’au moins 20 caractères. Ne jamais inventer de citation.',
                'IMPORTANT : ne combine jamais deux listes de candidats dans un seul CSV.',
                'RENVOIE UN ZIP UNIQUE contenant chaque CSV de décision individuel à la racine.',
                'Le moteur importera chaque CSV avec son identifiant original et vérifiera les preuves et tous les champs.',
                'Aucune admission canonique, aucune publication, aucun script exécutable.',
                'Tâches du transfert:']
            instruction.extend(f"- {j['id']}: {j['count']} propositions, réponse DECISIONS_{j['id']}.csv" for j,_ in parts)
            b=io.BytesIO()
            with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
                z.writestr('MANIFEST_TRANSFERT_MULTI_V315.json',json_text(manifest))
                z.writestr('INSTRUCTIONS_TRANSFERT_MULTI_V315.txt','\n'.join(instruction)+'\n')
                for j,raw in parts:
                    z.writestr('PACKS/'+j['id']+'.zip',raw,compress_type=zipfile.ZIP_STORED)
            data=b.getvalue()
            name='TRANSFERT_MULTI_V28_'+sha(data)[:16]+'.zip'
            return name,data

    def volume_v315(self):
        # Non-destructive telemetry. Measures elapsed time INCLUDING human idle time.
        # Pack size does not prove which version created a job.
        from collections import Counter
        jobs=list(self.db.execute('''SELECT id,kind,count,status,created_utc,sent_utc,finished_utc
                                      FROM jobs ORDER BY created_utc,id'''))
        grouped,group_total=self._small_ready_group()
        open_jobs=[j for j in jobs if j['status'] in OPEN]
        unesco=[j for j in open_jobs if j['kind']=='v28']
        kristal=[j for j in open_jobs if j['kind']=='v27']
        sizes={'petits_300_ou_moins':sum(j['count']<=300 for j in unesco),
               'intermediaires_301_649':sum(301<=j['count']<650 for j in unesco),
               'volume_650_880':sum(650<=j['count']<=880 for j in unesco),
               'hors_plage':sum(j['count']>880 or j['count']<=0 for j in unesco)}
        ready=[{'id':j['id'],'kind':j['kind'],'taille':j['count'],'etat':j['status']}
               for j in jobs if j['status']=='READY']
        durations=[]
        format_delays={'unesco_300_ou_moins':[], 'unesco_301_649':[], 'unesco_650_880':[], 'kristal':[]}
        for j in jobs:
            if j['status']!='DONE' or not j['sent_utc'] or not j['finished_utc']:continue
            try:
                begin=datetime.fromisoformat(j['sent_utc'])
                end=datetime.fromisoformat(j['finished_utc'])
                elapsed=(end-begin).total_seconds()/60
            except (ValueError, TypeError):continue
            if 0<=elapsed<=60*24*60:
                durations.append(elapsed)
                if j['kind']=='v27':bucket='kristal'
                elif j['count']<=300:bucket='unesco_300_ou_moins'
                elif j['count']<650:bucket='unesco_301_649'
                else:bucket='unesco_650_880'
                format_delays[bucket].append(elapsed)
        by_format={key:{'mediane':round(statistics.median(values),1) if values else None,
                        'observations':len(values)} for key,values in format_delays.items()}
        return {
            'contrat':{'unesco_cible':REVIEW_SIZE,'unesco_plafond':MAX_REVIEW_SIZE,
                       'unesco_minimum_souple':MIN_REVIEW_SIZE,'kristal_articles_max':24,
                       'kristal_mots_cibles':80000,'conversations':LANES},
            'total_ouverts':len(open_jobs),'unesco_ouverts':len(unesco),
            'kristal_ouverts':len(kristal),'unesco_par_taille':sizes,
            'ready_par_type':dict(Counter(j['kind'] for j in jobs if j['status']=='READY')),
            'transfert_groupe':{'packs':len(grouped),'propositions':group_total,'possible':len(grouped)>=2},
            'ready_details':ready,'unesco_en_attente':dict(Counter(j['status'] for j in unesco)),
            'delai_par_format_minutes':by_format,
            'delai_transfert_import_minutes':{
                'mediane':round(statistics.median(durations),1) if durations else None,
                'observations':len(durations),
                'interpretation':'Délai entre clic de transmission et import : inclut les pauses humaines, pas le seul travail IA'},
            'note':'Les petits packs existants ne sont jamais reconditionnés. Leur taille ne date pas avec certitude leur création.'}

    def snapshot(self):
        with self.lock:
            lanes=[]
            for ln in self.db.execute('SELECT lane,job_id FROM lanes ORDER BY lane'):
                j=self._row(ln['job_id']) if ln['job_id'] else None
                fields=('id','kind','key','count','status','error','created_utc','sent_utc','attempts','review_approved','review_rejected','review_hold')
                lanes.append({'lane':ln['lane'],'job':{f:j[f] for f in fields} if j else None})
            stat=dict(self.db.execute('SELECT status,count(*) n FROM jobs GROUP BY status').fetchall())
            ix=dict(self.db.execute('SELECT state,count(*) n FROM review_index GROUP BY state').fetchall())
            events=[r['message'] for r in self.db.execute('SELECT message FROM events ORDER BY id DESC LIMIT 35')][::-1]
            receipts=[dict(r) for r in self.db.execute('SELECT at_utc,filename,job_id,status,detail FROM receipts ORDER BY id DESC LIMIT 14')]
            updates=[dict(r) for r in self.db.execute('SELECT id,status,created_utc,applied_utc FROM updates ORDER BY created_utc DESC LIMIT 3')]
            quality_row=self.db.execute("SELECT COALESCE(SUM(review_approved),0),COALESCE(SUM(review_rejected),0),COALESCE(SUM(review_hold),0) FROM jobs WHERE status='DONE' AND kind='v28'").fetchone()
            quality={'approved':quality_row[0],'rejected':quality_row[1],'hold':quality_row[2]}
            qualification={'available':False,'cursor_page_id':None,'cached_bytes':0}
            qpath=self.work.parent/'qualification_multibranche_v31'/'qualification_multibranche_v31.sqlite'
            if qpath.is_file():
                qualification['available']=True
                qualification['cached_bytes']=qpath.stat().st_size
                try:
                    with closing(uri_ro(qpath)) as qdb:
                        rr=qdb.execute("SELECT value FROM meta WHERE key='cursor_page_id'").fetchone()
                        qualification['cursor_page_id']=int(rr[0]) if rr else None
                except (ValueError,sqlite3.Error):pass
            return {'volume_v315':self.volume_v315(),'qualification_v31':qualification,'version':VERSION,'busy':self.busy,'operation':self.operation,'lanes':lanes,'jobs':stat,
                    'review_index':ix,'stats':self._counts(),'events':events,'receipts':receipts,'updates':updates,'quality':quality,'work':str(self.work),
                    'v28_frozen':self._open_review_count()>0}

    def _start(self,name,fn,*args):
        with self.lock:
            if self.busy:raise ValueError('Une opération est déjà en cours : '+self.operation)
            self.busy=True;self.operation=name
        def runner():
            try:fn(*args);self._log('TERMINÉ : '+name)
            except Exception as ex:self._log('ERREUR : '+name+' — '+str(ex))
            finally:
                with self.lock:self.busy=False;self.operation=''
        threading.Thread(target=runner,daemon=True).start()

    def _run(self,script,options):
        path=self.repo/script
        if not path.is_file():raise ValueError('Script moteur absent : '+str(path))
        pwsh=shutil.which('pwsh')
        if pwsh is None:raise ValueError('pwsh (PowerShell 7) introuvable')
        cmd=[pwsh,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(path)]+list(options)
        self._log('▶ '+script+' '+' '.join(options))
        p=subprocess.Popen(cmd,cwd=str(self.repo),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                           encoding='utf-8',errors='replace',text=True,bufsize=1)
        out=[]
        assert p.stdout is not None
        for line in p.stdout:
            line=line.rstrip('\r\n')
            if line:self._log(line[:550]);out.append(line[-800:])
            if len(out)>400:out=out[-200:]
        if p.wait()!=0:raise ValueError(f'{script} a échoué : '+(' '.join(out[-5:]))[-700:])
        return '\n'.join(out)

    def _open_review_count(self):
        return self.db.execute("SELECT count(*) FROM jobs WHERE kind='v28' AND status IN ('WAITING','READY','SENT','ERROR','IMPORTING','NEEDS_CONFIRMATION')").fetchone()[0]

    def batch(self):self._start('Batch global local',self._batch)
    def _batch(self):
        self._log('BATCH : empaquetage v27, découverte protégée v28, index complet et file')
        for pass_i in range(12):
            text=self._run('PRODUIRE_KRISTALS_V27.ps1',['-Action','Packs','-MaxPacks','100','-MaxArticles','24','-TargetWords','80000','-TargetBytes','12582912'])
            if re.search(r'"queue"\s*:\s*\{\s*"PACKED"',text) or re.search(r'"PENDING"\s*:\s*0\b',text):break
            if re.search(r'"packets_created_this_run"\s*:\s*0\b',text):break
            if pass_i==11:self._log('12 passes v27 atteintes; prochain batch continuera les packs.')
        with self.lock:frozen=self._open_review_count()>0
        if frozen:
            self._log('DÉCOUVERTE REPORTÉE : retours v28 en cours; preuves figées jusqu’à clôture des lots.')
        else:
            for step in range(12):
                try:
                    res=self._run('DECOUVRIR_ARTICLES_RELIES_V28.ps1',['-Action','Discover','-MaxSeeds','10000'])
                except ValueError as ex:
                    reason=str(ex).lower()
                    # Seule l'incompatibilité avérée XML/index entraîne un changement
                    # de moteur de découverte; les contrôles de source restent actifs.
                    mismatch=('ne correspond pas a l index v21' in reason or
                              'ne correspond pas à l index v21' in reason or
                              'signature du xml differente' in reason)
                    if not mismatch:raise
                    from routage_branches_v311 import relational_discover
                    self._log('Index XML v21 incompatible : découverte SQL relationnelle sans citations XML')
                    res=relational_discover(self,self._v28_engine(),self._v28_engine().v25.DEFAULT_BRANCH,
                                            self.v28,max_seeds=10000)
                mo=re.search(r'"seeds_pending"\s*:\s*(\d+)',res)
                if mo and int(mo.group(1))==0:break
                mo_done=re.search(r'"(?:seeds_processed_this_run|seeds_processed)"\s*:\s*(\d+)',res)
                if mo_done and int(mo_done.group(1))==0:break
            from routage_branches_v311 import discover_other
            other=discover_other(self,self._v28_engine())
            if other:self._log('Découvertes multibranches mises à jour : '+', '.join(other))
        self._prepare()

    def prepare(self):self._start('Préparation des postes',self._prepare)

    def _imported_pack_ids(self):
        path=self.v27/'KRISTAL_CUMULATIF_PRIVE_V27.sqlite'
        if not path.is_file():return set()
        try:
            with closing(uri_ro(path)) as c:return {row[0] for row in c.execute('SELECT pack_id FROM delta_imports')}
        except sqlite3.Error as ex:raise ValueError('Base cumulative v27 illisible; aucune tâche recréée') from ex

    def _prepare_v27(self):
        imported=self._imported_pack_ids();added=0
        packs=self.v27/'packs'
        for path in sorted(packs.glob('PACK_V27_*.zip')) if packs.is_dir() else []:
            key=path.stem;jid='v27_'+key
            if key in imported or self._row(jid):continue
            try:
                with zipfile.ZipFile(path) as z:
                    data=json.loads(z.read('MANIFEST_PACK_V27.json'))
                    if data['pack_id']!=key:raise ValueError('ID pack incohérent')
                    n=len(data['articles'])
            except (OSError,zipfile.BadZipFile,KeyError,ValueError) as ex:
                self._log(f'Pack ignoré : {path.name} — {ex}');continue
            pack_digest=sha_path(path)
            self.db.execute('''INSERT INTO jobs(id,kind,key,count,status,source_path,source_sha256,
              bundle_path,bundle_sha256,created_utc) VALUES(?,?,?,?,?,?,?,?,?,?)''',
              (jid,'v27',key,n,'WAITING',str(path),pack_digest,str(path),pack_digest,now()))
            added+=1
        return added

    def _v28_engine(self):
        path=self.repo/'tools'/'unesco_pilot'/'decouvrir_articles_relies_v28.py'
        if not path.is_file():raise ValueError('Moteur v28 absent : '+str(path))
        importdir=str(path.parent)
        if importdir not in sys.path:sys.path.insert(0,importdir)
        spec=importlib.util.spec_from_file_location('encyklopedia_v28_runtime',path)
        mod=importlib.util.module_from_spec(spec);assert spec.loader
        spec.loader.exec_module(mod)
        return mod

    def _refresh_review_index(self):
        stage=self.v28/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        if not stage.is_file():
            self._log('Découverte historique v28 absente : vérification des autres branches')
            from routage_branches_v311 import refresh
            return refresh(self,self._v28_engine())
        m=self._v28_engine();branch=m.v25.load_branch(m.v25.DEFAULT_BRANCH)
        work=uri_ro(stage)
        try:
            if m.v25.meta(work,'schema')!=m.FORMAT or m.v25.meta(work,'branch_signature')!=branch['signature']:
                raise ValueError('Découverte v28 et branche UNESCO incompatibles')
            labels={c['unesco_id']:m.v25.label(c,'en') for c in branch['concepts']}
            from priorisation_native_v31 import score as v31_score
            # Cache multibranche V31 réutilisé si déjà alimenté ; jamais un prérequis
            # pour les imports/retours des tâches en cours.
            profile_db=None
            cache=self.work.parent/'qualification_multibranche_v31'/'qualification_multibranche_v31.sqlite'
            if cache.is_file():
                try:
                    profile_db=uri_ro(cache)
                    profile_db.execute('SELECT 1 FROM branch_suggestions LIMIT 1').fetchone()
                except (ValueError,sqlite3.Error):
                    if profile_db:profile_db.close()
                    profile_db=None
            classified=set()
            if self.catalogue.is_file():
                with closing(uri_ro(self.catalogue)) as cat:
                    classified.update((r[0],int(r[1])) for r in cat.execute("SELECT concept_id,page_id FROM assignments WHERE branch_id=? AND wiki='enwiki'",(branch['id'],)))
                    if cat.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='reviewed_article_links_v28'").fetchone():
                        classified.update((r[0],int(r[1])) for r in cat.execute('SELECT concept_id,page_id FROM reviewed_article_links_v28 WHERE branch_id=?',(branch['id'],)))
            # Import prior manually reviewed HOLD rows from the already-installed v28 overlays.
            # v28 intentionally never writes HOLD to its catalogue ledger; without this step
            # the station would repeatedly send the same provisional candidates to ChatGPT.
            historical=0
            reviews=self.repo/'tools'/'unesco_pilot'/'v28_data'
            for review in sorted(reviews.rglob('DECISIONS_ARTICLES_RELIES_V28*.csv')) if reviews.is_dir() else []:
                try:old_rows=read_baseline(review.read_bytes())
                except (OSError,UnicodeError,ValueError) as ex:
                    self._log('Revue historique ignorée : '+review.name+' — '+str(ex));continue
                with self.lock:
                    with self.db:
                        for old in old_rows:
                            if str(old.get('decision','')).strip().upper()!='HOLD':continue
                            key=(old['concept_id'],int(old['page_id']))
                            if key in classified:continue
                            try:priority=int(old['priority'])
                            except (ValueError,TypeError):priority=0
                            params=(old['candidate_id'],old['branch_id'],old['concept_id'],int(old['page_id']),
                                old['title'],priority,int(old['seed_count'] or 0),int(old['link_evidence'] or 0),
                                int(old['category_evidence'] or 0),int(old['subcategory_evidence'] or 0),
                                'HOLD',old.get('evidence_sha256',''),now())
                            cur=self.db.execute('''INSERT OR IGNORE INTO review_index(candidate_id,branch_id,concept_id,page_id,
                                 title,priority,seed_count,link_evidence,category_evidence,subcategory_evidence,
                                 state,evidence_sha256,last_seen_utc) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',params)
                            historical+=cur.rowcount
            if historical:self._log(f'Anciennes décisions HOLD préservées : {historical} ; pas de relecture automatique')
            q='''SELECT c.branch_id,c.concept_id,c.page_id,c.title,
             COUNT(DISTINCT e.seed_page_id) seed_count,
             SUM(CASE WHEN e.kind='WIKILINK' THEN 1 ELSE 0 END) links,
             SUM(CASE WHEN e.kind='SHARED_CATEGORY' THEN 1 ELSE 0 END) shared,
             SUM(CASE WHEN e.kind='SUBCATEGORY' THEN 1 ELSE 0 END) subs
             FROM candidates c JOIN evidence e ON e.branch_id=c.branch_id
             AND e.concept_id=c.concept_id AND e.page_id=c.page_id
             WHERE c.branch_id=? GROUP BY c.branch_id,c.concept_id,c.page_id'''
            added=0;checked=0
            with self.lock:
                with self.db:
                    for row in work.execute(q,(branch['id'],)):
                        r=dict(row);key=(r['concept_id'],int(r['page_id']))
                        if key in classified:continue
                        if r['concept_id'] not in labels:continue
                        cid=m.candidate_id(branch['id'],r['concept_id'],int(r['page_id']))
                        score=v31_score(r,labels[r['concept_id']])
                        if profile_db is not None:
                            prof=profile_db.execute('SELECT score,concept_id_suggested FROM branch_suggestions WHERE page_id=? AND branch_id=?',
                                (int(r['page_id']),branch['id'])).fetchone()
                            if prof is not None:
                                score=min(100,round(score*0.8+int(prof['score'])*0.2+
                                    (5 if prof['concept_id_suggested']==r['concept_id'] else 0)))
                        checked+=1
                        cur=self.db.execute('''INSERT OR IGNORE INTO review_index(candidate_id,branch_id,concept_id,page_id,title,
                            priority,seed_count,link_evidence,category_evidence,subcategory_evidence,state,last_seen_utc)
                            VALUES(?,?,?,?,?,?,?,?,?,?,'PENDING',?)''',
                            (cid,branch['id'],r['concept_id'],int(r['page_id']),r['title'],score,
                             int(r['seed_count']),int(r['links']),int(r['shared']),int(r['subs']),now()))
                        added+=cur.rowcount
                        # Re-rank only unscheduled tasks; never invalidate a pending ChatGPT job.
                        self.db.execute('''UPDATE review_index SET priority=?,seed_count=?,link_evidence=?,
                             category_evidence=?,subcategory_evidence=?,title=?,last_seen_utc=?,
                             state=CASE WHEN ?<15 AND ?=0 THEN 'DEFERRED' ELSE 'PENDING' END
                             WHERE candidate_id=? AND state IN ('PENDING','DEFERRED') ''',
                             (score,int(r['seed_count']),int(r['links']),int(r['shared']),int(r['subs']),r['title'],now(),
                              score,int(r['links']),cid))
            self._log(f'Index UNESCO v30 : {checked} propositions éligibles, {added} nouvelles; HOLD conservés.')
            from routage_branches_v311 import refresh
            return added+refresh(self,m)
        finally:
            work.close()
            if 'profile_db' in locals() and profile_db is not None:profile_db.close()

    def _prepare_v28(self, allow_fallback=False):
        # v31.5: one GLOBAL buffer shared by all UNESCO branches. The historical
        # branch receives a fair first pass; only a later fallback may fill spare
        # slots after other branches have had a chance to prepare their work.
        queued=self._open_review_count()
        if queued>=QUEUE_BUFFER:return 0
        m=self._v28_engine();branch=m.v25.load_branch(m.v25.DEFAULT_BRANCH)
        from routage_branches_v311 import live
        active_extras=live(self,m)
        legacy_queued=self.db.execute('''SELECT count(*) FROM jobs j
            WHERE j.kind='v28' AND j.status IN
            ('WAITING','READY','SENT','ERROR','IMPORTING','NEEDS_CONFIRMATION')
            AND NOT EXISTS (SELECT 1 FROM v311_job_routes r WHERE r.job_id=j.id)''').fetchone()[0]
        legacy_target=(QUEUE_BUFFER if allow_fallback or not active_extras
                       else max(1,QUEUE_BUFFER//(len(active_extras)+1)))
        labels={c['unesco_id']:m.v25.label(c,'en') for c in branch['concepts']}
        stage=self.v28/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
        if not stage.is_file():return 0
        work=uri_ro(stage)
        created=0
        try:
            while queued<QUEUE_BUFFER and legacy_queued<legacy_target:
                # Packs natifs élargis : qualification V31 + exploration stratifiée.
                # Aucun candidat n'est rejeté automatiquement et aucune tâche existante n'est remaniée.
                from priorisation_native_v31 import select as v31_select
                ranked=list(self.db.execute('''SELECT * FROM review_index WHERE state='PENDING' AND branch_id=?
                    ORDER BY priority DESC,seed_count DESC,
                    (link_evidence+category_evidence+subcategory_evidence) DESC,page_id ASC,concept_id DESC
                    LIMIT ?''',(branch['id'],max(REVIEW_SIZE*15,6000))))
                if not ranked:break  # le stock faible reste en réserve, non rejeté
                take=min(REVIEW_SIZE,MAX_REVIEW_SIZE)
                top=v31_select(ranked,min(len(ranked),round(take*.75)),explore=0.18)
                weak=list(self.db.execute('''SELECT * FROM review_index WHERE state='DEFERRED' AND branch_id=?
                    ORDER BY priority DESC,seed_count DESC,page_id ASC LIMIT ?''',
                    (branch['id'],max(REVIEW_SIZE*15,6000))))
                reserve=v31_select(weak,min(take-len(top),len(weak)),explore=1.0)
                picked=top+reserve
                if len(picked)<take:
                    seen={x['candidate_id'] for x in picked}
                    picked.extend(x for x in ranked if x['candidate_id'] not in seen)
                    picked=picked[:take]
                rows=[];ids=[];complexity=0
                for r in picked:
                    item_cost=1+min(3,(int(r['link_evidence'])+int(r['category_evidence'])+int(r['subcategory_evidence']))//8)
                    if len(rows)>=MIN_REVIEW_SIZE and complexity+item_cost>REVIEW_BUDGET:break
                    complexity+=item_cost
                    src=work.execute('SELECT * FROM candidates WHERE branch_id=? AND concept_id=? AND page_id=?',
                                     (r['branch_id'],r['concept_id'],r['page_id'])).fetchone()
                    if not src:
                        # Historical HOLDs may outlive a changed discovery snapshot.
                        self.db.execute("UPDATE review_index SET state='STALE' WHERE candidate_id=?",(r['candidate_id'],))
                        continue
                    candidate=m.build_candidate(work,src,labels[r['concept_id']])
                    if not candidate or candidate['candidate_id']!=r['candidate_id']:
                        raise ValueError('Candidat v28 incohérent : '+r['candidate_id'])
                    rows.append({'candidate_id':candidate['candidate_id'],'branch_id':candidate['branch_id'],
                         'concept_id':candidate['concept_id'],'concept_en':candidate['concept_en'],
                         'page_id':candidate['page_id'],'title':candidate['title'],'priority':candidate['priority'],
                         'seed_count':candidate['seed_count'],'link_evidence':candidate['links'],
                         'category_evidence':candidate['shared'],'subcategory_evidence':candidate['subs'],
                         'evidence_sha256':candidate['evidence_sha256'],'examples':candidate['examples'],
                         'decision':'HOLD','justification':''})
                    ids.append(candidate['candidate_id'])
                if not rows:
                    self.db.commit()
                    continue
                raw=csv_bytes(rows);jid='v28_'+sha(raw)[:14]+'_'+secrets.token_hex(4)
                basedir=self.work/'review_sources';basedir.mkdir(parents=True,exist_ok=True)
                srcpath=basedir/(jid+'.csv');bundle=self.work/'bundles'/(jid+'.zip')
                bundle.parent.mkdir(parents=True,exist_ok=True)
                if srcpath.is_file() and sha_path(srcpath)!=sha(raw):raise ValueError('Source v28 existante modifiée : '+jid)
                if not srcpath.is_file():srcpath.write_bytes(raw)
                description={'id':jid,'kind':'v28','count':len(rows),'bundle_path':str(bundle)}
                inst='''REVUE DOCUMENTAIRE UNESCO : titres et preuves uniquement. Renvoie DECISIONS_<id>.csv, exactement 3 colonnes candidate_id,decision,justification, AVEC UNE LIGNE PAR CANDIDAT (HOLD explicite). Aucune colonne source recopiée. APPROVE : justification de 20 caractères minimum. Ne fabrique aucun fait ou identifiant. Pas de canon.\n'''
                temp=bundle.with_suffix('.tmp')
                with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
                    z.writestr('REVUE_'+jid+'.csv',raw)
                    z.writestr('INSTRUCTIONS_CHATGPT.txt',inst)
                    z.writestr('PROMPT_CHATGPT.txt',prompt(description))
                os.replace(temp,bundle)
                self.db.execute('''INSERT OR IGNORE INTO jobs(id,kind,key,count,status,source_path,source_sha256,
                 bundle_path,bundle_sha256,created_utc,source_generation) VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
                 (jid,'v28',jid,len(rows),'WAITING',str(srcpath),sha(raw),str(bundle),sha_path(bundle),now(),str(m.v25.meta(work,'catalogue_sequence') or '')))
                self.db.executemany("UPDATE review_index SET state='QUEUED',task_id=?,evidence_sha256=? WHERE candidate_id=? AND state IN ('PENDING','DEFERRED')",
                    [(jid,r['evidence_sha256'],r['candidate_id']) for r in rows])
                queued+=1;legacy_queued+=1;created+=1
            self.db.commit()
            return created
        finally:work.close()

    def _prepare(self):
        with self.lock:
            with self.db:a=self._prepare_v27()
        self._refresh_review_index()
        with self.lock:
            b=self._prepare_v28()
            from routage_branches_v311 import prepare as prepare_branches
            b+=prepare_branches(self,self._v28_engine())
            b+=self._prepare_v28(allow_fallback=True)
            with self.db:self._fill_lanes()
        self._log(f'File alimentée : {a} packs Kristal et {b} nouvelles revues UNESCO ; 10 postes renouvelés.')

    def task(self,jid):
        with self.lock:
            j=self._row(jid)
            if not j or j['status'] not in ('READY','SENT','ERROR','NEEDS_CONFIRMATION'):
                raise ValueError('Tâche non disponible dans les postes')
            return dict(j)

    def bundle(self,jid):
        job=self.task(jid);path=Path(job['bundle_path'])
        if not path.is_file() or sha_path(path)!=job['bundle_sha256']:
            raise ValueError('Paquet source absent ou modifié : '+jid)
        if job['kind']=='v28':
            # Enrichment is only an extra review document. The immutable baseline CSV,
            # task id, input hashes, review DB, and imported decisions are unchanged.
            path_context=self.repo/'tools'/'unesco_pilot'/'contexte_revue_unesco_v28.py'
            spec=importlib.util.spec_from_file_location('encyklopedia_v28_context',path_context)
            context=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(context)
            original=Path(job['source_path'])
            if not original.is_file() or sha_path(original)!=job['source_sha256']:
                raise ValueError('Source UNESCO originale absente ou modifiée : '+jid)
            from routage_branches_v311 import job_route
            route=job_route(self,jid)
            stage=Path(route['stage_path']) if route is not None else self.v28/'DECOUVERTE_ARTICLES_RELIES_V28.sqlite'
            return context.cached_enriched_bundle(path,original,self.repo,stage,self.work)
        return path

    def mark_sent(self,jid):
        with self.lock:
            j=self.task(jid)
            if j['status']=='READY':
                with self.db:self.db.execute("UPDATE jobs SET status='SENT',sent_utc=? WHERE id=?",(now(),jid))
            return {'ok':True,'sent':True}

    def native_clipboard(self,jid):
        job=self.task(jid);txt=prompt(job);path=self.bundle(jid)
        if os.name!='nt':return False,'Presse-papiers Windows indisponible; texte et téléchargement séparés.'
        exe=shutil.which('powershell.exe') or shutil.which('powershell')
        if not exe:return False,'Windows PowerShell introuvable'
        t=base64.b64encode(txt.encode('utf-8')).decode('ascii')
        p=base64.b64encode(str(path).encode('utf-8')).decode('ascii')
        command=f'''Add-Type -AssemblyName System.Windows.Forms
$txt=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{t}'))
$file=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{p}'))
$clipboard=New-Object System.Windows.Forms.DataObject
$clipboard.SetData([System.Windows.Forms.DataFormats]::UnicodeText,$txt)
$items=New-Object System.Collections.Specialized.StringCollection
[void]$items.Add($file)
$clipboard.SetFileDropList($items)
[System.Windows.Forms.Clipboard]::SetDataObject($clipboard,$true)
'''
        enc=base64.b64encode(command.encode('utf-16le')).decode('ascii')
        try:
            result=subprocess.run([exe,'-NoProfile','-STA','-EncodedCommand',enc],capture_output=True,timeout=18)
            return result.returncode==0,('Presse-papiers avec texte + fichier préparé' if result.returncode==0 else 'Presse-papiers occupé; utiliser copie texte et ZIP téléchargé')
        except (OSError,subprocess.SubprocessError):return False,'Presse-papiers indisponible'

    def merge_review(self,job,raw):
        sourcefile=Path(job['source_path'])
        if not sourcefile.is_file() or sha_path(sourcefile)!=job['source_sha256']:
            raise ValueError('Preuves UNESCO locales changées : tâche figée, import refusé')
        baseline=read_baseline(sourcefile.read_bytes())
        mode,rows=parse_reply_csv(raw)
        if len(rows)>len(baseline):raise ValueError('Retour avec plus de lignes que les propositions')
        index={r['candidate_id']:r for r in baseline};used=set()
        for row in rows:
            cid=row['candidate_id'].strip()
            if cid in used:raise ValueError('Identifiant dupliqué dans le retour : '+cid)
            used.add(cid)
            if cid not in index:raise ValueError('Identifiant étranger au lot : '+cid)
            original=index[cid]
            if mode=='full':
                for col in FIELDS:
                    if col not in ('decision','justification') and row[col]!=original[col]:
                        raise ValueError('Preuve source modifiée : '+col+' ('+cid+')')
            dec=row['decision'].strip().upper();why=row['justification'].strip()
            if dec not in ('APPROVE','REJECT','HOLD'):raise ValueError('Décision inconnue : '+dec)
            if dec=='APPROVE' and len(why)<20:raise ValueError('Justification APPROVE trop courte : '+cid)
            # Trois colonnes restent compactes, mais une ligne par candidat est préférable.
            # Un retour partiel est retenu pour confirmation humaine, jamais importé silencieusement.
            original['decision']=dec;original['justification']=why
        if mode=='full' and len(rows)!=len(baseline):raise ValueError('CSV complet incomplet')
        counts={d:sum(r['decision']==d for r in baseline) for d in ('APPROVE','REJECT','HOLD')}
        return csv_bytes(baseline),counts

    def _resolve_return(self,name,content):
        base=Path(name).name
        with self.lock:
            active=[dict(r) for r in self.db.execute("SELECT * FROM jobs WHERE status IN ('READY','SENT','ERROR')")]
        if base.lower().endswith('.json'):
            try:obj=json.loads(content.decode('utf-8-sig'))
            except (UnicodeDecodeError,ValueError) as ex:raise ValueError('Delta JSON illisible') from ex
            if not isinstance(obj,dict) or obj.get('format')!='encyklopedia.kristal-ai-delta.v27/1':
                raise ValueError('JSON non reconnu comme delta Kristal v27')
            eligible=[j for j in active if j['kind']=='v27' and j['key']==obj.get('pack_id')]
            if len(eligible)!=1:raise ValueError('Aucun poste actif ne correspond au pack '+str(obj.get('pack_id')))
            job=eligible[0]
            if obj.get('pack_sha256')!=job['source_sha256']:raise ValueError('SHA du pack non conforme')
            if obj.get('canonical_admissions',0)!=0 or obj.get('publication_authorized',False) is not False:
                raise ValueError('Admission canonique ou publication non permise')
            return job,'v27'
        if base.lower().endswith('.csv'):
            mode,rows=parse_reply_csv(content)
            ids=[r['candidate_id'].strip() for r in rows]
            if len(ids)!=len(set(ids)):raise ValueError('Identifiant dupliqué dans CSV retour')
            # Empty compact replies MUST carry the task ID in their exact filename.
            named=[j for j in active if j['kind']=='v28' and base.lower()==('DECISIONS_'+j['id']+'.csv').lower()]
            if len(named)==1:return named[0],'v28'
            if not ids:raise ValueError('Réponse tout-HOLD : le nom de fichier doit être DECISIONS_<task_id>.csv')
            subset=set(ids);eligible=[]
            for j in active:
                if j['kind']!='v28':continue
                if not Path(j['source_path']).is_file():continue
                baseline=read_baseline(Path(j['source_path']).read_bytes())
                if subset.issubset({r['candidate_id'] for r in baseline}):eligible.append(j)
            if len(eligible)!=1:raise ValueError('Retour UNESCO ambigu : utiliser le nom DECISIONS_<task_id>.csv')
            return eligible[0],'v28'
        raise ValueError('Retour non pris en charge')

    def _receipt(self,name,job,status,detail):
        with self.lock:
            with self.db:self.db.execute('INSERT INTO receipts(at_utc,filename,job_id,status,detail) VALUES(?,?,?,?,?)',
                                           (now(),name,job,status,str(detail)[:600]))

    def receive(self,files):
        if not 1<=len(files)<=30:raise ValueError('Dépose 1 à 30 ZIP')
        if sum(len(b) for _,b in files)>MAX_REQUEST:raise ValueError('Taille cumulée maximale 110 Mo')
        self._start('Validation et import des retours',self._process_returns,files)
        return {'queued_files':len(files)}

    def _process_returns(self,files):
        processed=set()
        for name,raw in files:
            try:
                if len(raw)>MAX_FILE:raise ValueError('ZIP retour >100 Mo')
                entries=extract_zip_files(name,raw)
                for entry_name,content in entries:
                    try:
                        job,kind=self._resolve_return(entry_name,content)
                        if job['id'] in processed:raise ValueError('Retour en double dans le même dépôt')
                        processed.add(job['id'])
                        self._import_one(job,kind,content)
                        with self.lock:
                            current=self._row(job['id'])
                        receipt_status='EN_ATTENTE' if current['status']=='NEEDS_CONFIRMATION' else 'OK'
                        detail='Revue partielle ou tout-HOLD à confirmer' if receipt_status=='EN_ATTENTE' else 'Résultat vérifié et intégré'
                        self._receipt(name,job['id'],receipt_status,detail)
                    except Exception as ex:
                        self._receipt(name,None,'REFUS',entry_name+' : '+str(ex))
                        self._log('✗ Retour '+entry_name+' refusé : '+str(ex))
            except Exception as ex:
                self._receipt(name,None,'REFUS',str(ex));self._log('✗ Archive '+name+' refusée : '+str(ex))
        self._log(f'Réception terminée : {len(processed)} tâche(s) identifiée(s), voir le tableau des retours.')

    def _import_one(self,job,kind,content):
        jid=job['id'];store=self.work/'returns';store.mkdir(parents=True,exist_ok=True)
        target=store/(jid+'_'+sha(content)[:16]+('.json' if kind=='v27' else '.csv'))
        if not target.exists():target.write_bytes(content)
        with self.lock:
            with self.db:
                self.db.execute("UPDATE jobs SET status='IMPORTING',error='',attempts=attempts+1,review_return_path=? WHERE id=?",
                                (str(target),jid))
        try:
            if kind=='v27':
                source=Path(job['source_path'])
                if not source.is_file() or sha_path(source)!=job['source_sha256']:
                    raise ValueError('Pack local changé ou disparu')
                dest=self.v27/'deltas'/('DELTA_KRISTAL_'+job['key']+'.json')
                if dest.is_file() and sha_path(dest)!=sha(content):
                    raise ValueError('Un autre delta existe sur D:, remplacement interdit')
                self._run('PRODUIRE_KRISTALS_V27.ps1',['-Action','Import','-Pack',str(source),'-Delta',str(target)])
                dest.parent.mkdir(parents=True,exist_ok=True)
                if not dest.exists():dest.write_bytes(content)
                counts={'APPROVE':0,'REJECT':0,'HOLD':0}
            else:
                merged,counts=self.merge_review(job,content)
                mode,returned=parse_reply_csv(content)
                incomplete=(len(returned)!=job['count'])
                all_hold=(counts['APPROVE']==0 and counts['REJECT']==0)
                if incomplete or all_hold:
                    with self.lock:
                        with self.db:
                            self.db.execute("UPDATE jobs SET status='NEEDS_CONFIRMATION',review_approved=?,review_rejected=?,review_hold=? WHERE id=?",
                                            (counts['APPROVE'],counts['REJECT'],counts['HOLD'],jid))
                    why='TOUT-HOLD' if all_hold else f'RETOUR PARTIEL {len(returned)}/{job["count"]} : HOLD implicites'
                    self._log('REVUE À CONFIRMER '+jid+' — '+why)
                    return
                complete=store/(jid+'_'+sha(merged)[:16]+'_COMPLET.csv')
                if not complete.exists():complete.write_bytes(merged)
                from routage_branches_v311 import apply as routed_apply
                routed_apply(self,self._v28_engine(),job,complete,True)
                routed_apply(self,self._v28_engine(),job,complete,False)
            self._complete(job,kind,content,counts)
        except Exception as ex:
            with self.lock:
                with self.db:self.db.execute("UPDATE jobs SET status='ERROR',error=? WHERE id=?",(str(ex)[:700],jid))
            self._log('✗ Import '+jid+' échoué : '+str(ex))
            raise

    def _complete(self,job,kind,content,counts):
        jid=job['id']
        with self.lock:
            with self.db:
                self.db.execute('''UPDATE jobs SET status='DONE',finished_utc=?,error='',return_sha256=?,
                    review_approved=?,review_rejected=?,review_hold=? WHERE id=?''',
                    (now(),sha(content),counts['APPROVE'],counts['REJECT'],counts['HOLD'],jid))
                if kind=='v28':
                    self.db.execute("UPDATE review_index SET state='HOLD' WHERE task_id=?",(jid,))
                    path=Path(job['source_path'])
                    _,ret=parse_reply_csv(content)
                    decision_map={r['candidate_id'].strip():r['decision'].strip().upper() for r in ret}
                    self.db.executemany("UPDATE review_index SET state='DECIDED' WHERE candidate_id=? AND task_id=?",
                                        [(cid,jid) for cid,d in decision_map.items() if d in ('APPROVE','REJECT')])
                self._fill_lanes()
            self._log('✓ '+jid+' intégré; poste renouvelé')
        # Populate future review jobs automatically; no new Discovery during outstanding reviews.
        with self.lock:
            if kind=='v28':
                try:
                    self._prepare_v28()
                    from routage_branches_v311 import prepare as prepare_branches
                    prepare_branches(self,self._v28_engine())
                    self._prepare_v28(allow_fallback=True)
                    with self.db:self._fill_lanes()
                except Exception as ex:self._log('Préparation de nouveaux lots différée : '+str(ex))

    def confirm_hold(self,jid):
        with self.lock:
            if self.busy:raise ValueError('Attendre la fin des importations')
            j=self._row(jid)
            if not j or j['status']!='NEEDS_CONFIRMATION':
                raise ValueError('Aucune revue en attente de confirmation')
            ret=Path(j['review_return_path'])
            if not ret.is_file():raise ValueError('Retour source disparu')
            content=ret.read_bytes();merged,counts=self.merge_review(dict(j),content)
            # All-HOLD is a private editorial staging decision; never pollute v28's catalogue ledger.
            if counts['APPROVE'] or counts['REJECT']:
                store=self.work/'returns';complete=store/(jid+'_'+sha(merged)[:16]+'_COMPLET.csv')
                if not complete.exists():complete.write_bytes(merged)
                from routage_branches_v311 import apply as routed_apply
                routed_apply(self,self._v28_engine(),dict(j),complete,True)
                routed_apply(self,self._v28_engine(),dict(j),complete,False)
            self._complete(dict(j),'v28',content,counts)
            return {'ok':True}

    def retry(self,jid):
        with self.lock:
            j=self._row(jid)
            if not j or j['status'] not in ('ERROR','SKIPPED'):
                raise ValueError('Seules les tâches en erreur ou ignorées peuvent être reprises')
            with self.db:
                assigned=self.db.execute('SELECT 1 FROM lanes WHERE job_id=?',(jid,)).fetchone() is not None
                status='READY' if assigned else 'WAITING'
                self.db.execute("UPDATE jobs SET status=?,error='',finished_utc=NULL WHERE id=?",(status,jid))
                if j['kind']=='v28':self.db.execute("UPDATE review_index SET state='QUEUED' WHERE task_id=?",(jid,))
                self._fill_lanes()
            self._log('Tâche réactivée : '+jid)
            return {'ok':True}

    def skip(self,jid):
        with self.lock:
            j=self._row(jid)
            if not j or j['status'] in CLOSED:raise ValueError('Tâche absente ou déjà terminée')
            if j['status']=='IMPORTING':raise ValueError('Importation en cours : annulation interdite')
            with self.db:
                self.db.execute("UPDATE jobs SET status='SKIPPED',finished_utc=? WHERE id=?",(now(),jid))
                if j['kind']=='v28':self.db.execute("UPDATE review_index SET state='SKIPPED' WHERE task_id=?",(jid,))
                self._fill_lanes()
            if j['kind']=='v28':
                self._prepare_v28()
                from routage_branches_v311 import prepare as prepare_branches
                prepare_branches(self,self._v28_engine())
                self._prepare_v28(allow_fallback=True)
                with self.db:self._fill_lanes()
            self._log('Tâche ignorée : '+jid)
            return {'ok':True}

    def reopen_holds(self,limit=500):
        # Explicit user-driven revisit. Never silently recycle HOLDs.
        with self.lock:
            if self.busy:raise ValueError('Attendre la fin du batch avant de rouvrir les HOLD')
            with self.db:
                ids=[r[0] for r in self.db.execute("SELECT candidate_id FROM review_index WHERE state='HOLD' ORDER BY priority DESC LIMIT ?",(int(limit),))]
                self.db.executemany("UPDATE review_index SET state='PENDING',task_id=NULL,evidence_sha256=NULL WHERE candidate_id=?",[(cid,) for cid in ids])
            self._log(f'{len(ids)} HOLD remis à examiner explicitement')
        self.prepare();return {'reopened':len(ids)}

    # Software overlays are separate from knowledge returns: never auto-install source code.
    def _check_overlay(self,raw:bytes):
        if len(raw)>20*1024*1024:raise ValueError('Overlay logiciel >20 Mo')
        try:z=zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile as ex:raise ValueError('Overlay ZIP illisible') from ex
        with z:
            names=z.namelist()
            if len(names)>220 or len(names)!=len(set(names)):
                raise ValueError('Overlay avec trop de fichiers ou doublons')
            if 'ENCYK_OVERLAY_MANIFEST_V30.json' not in names:
                raise ValueError('Overlay : manifeste ENCYK_OVERLAY_MANIFEST_V30.json absent')
            try:manifest=json.loads(z.read('ENCYK_OVERLAY_MANIFEST_V30.json').decode('utf-8'))
            except (KeyError,ValueError,UnicodeError) as ex:raise ValueError('Manifeste overlay invalide') from ex
            if manifest.get('format')!='encyklopedia.safe-overlay.v30/1':
                raise ValueError('Format manifeste overlay non reconnu')
            items=manifest.get('files')
            if not isinstance(items,list) or not 1<=len(items)<=200:
                raise ValueError('Manifeste doit lister 1 à 200 fichiers')
            allowed={'.py','.ps1','.html','.js','.css','.json','.md','.txt','.csv','.sql','.xml','.yml','.yaml','.toml','.cs','.csproj','.sln','.props','.targets'}
            reserved={'.git','.env','.ssh','.vscode','node_modules','venv','.venv','__pycache__','.idea'}
            clean=set();folded=set();info=[];total=0
            for item in items:
                if not isinstance(item,dict):raise ValueError('Entrée de manifeste invalide')
                name=item.get('path','');digest=item.get('sha256','')
                if not isinstance(name,str) or not isinstance(digest,str):raise ValueError('Chemin ou SHA absent')
                parts=PurePosixPath(name).parts
                if (not parts or name.startswith(('/','\\')) or '\\' in name or ':' in name or
                    any(x in ('','..','.') or x.startswith('.') for x in parts) or
                    any(x.lower() in reserved for x in parts) or len(name)>260):
                    raise ValueError('Chemin logiciel interdit : '+name)
                if PurePosixPath(name).suffix.lower() not in allowed:
                    raise ValueError('Extension logicielle non autorisée : '+name)
                if len(digest)!=64 or not re.fullmatch('[0-9a-f]{64}',digest):
                    raise ValueError('SHA-256 manquant ou incorrect : '+name)
                if name in clean or name.casefold() in folded or name not in names:
                    raise ValueError('Membre manquant/dupliqué : '+name)
                folded.add(name.casefold())
                entry=z.getinfo(name)
                if entry.flag_bits&1 or (entry.external_attr>>16)&0o170000==0o120000:
                    raise ValueError('Overlay chiffré ou lien symbolique refusé')
                total+=entry.file_size
                if total>40*1024*1024:raise ValueError('Overlay décompressé >40 Mo')
                body=z.read(name)
                if sha(body)!=digest:raise ValueError('SHA incorrect : '+name)
                clean.add(name)
                dest=self.repo.joinpath(*parts)
                if not dest.resolve().is_relative_to(self.repo):raise ValueError('Sortie du dépôt refusée')
                exists=dest.is_file()
                old=sha_path(dest) if exists else None
                requires=item.get('requires_sha256')
                if requires is not None and requires!=old:
                    raise ValueError('Précondition de version non satisfaite : '+name)
                info.append({'path':name,'sha256':digest,'previous_sha256':old,
                             'overwrite':exists,'size':entry.file_size})
            if set(names)-clean-{'ENCYK_OVERLAY_MANIFEST_V30.json'}:
                raise ValueError('ZIP contient des fichiers non déclarés au manifeste')
            return manifest,info

    def stage_update(self,raw):
        with self.lock:
            if self.busy:raise ValueError('Attendre la fin des imports avant mise à jour')
            manifest,info=self._check_overlay(raw)
            uid='upd_'+sha(raw)[:16]
            store=self.work/'software_updates';store.mkdir(exist_ok=True)
            zip_path=store/(uid+'.zip')
            if not zip_path.exists():zip_path.write_bytes(raw)
            data={'files':info,'description':str(manifest.get('description',''))[:300]}
            with self.db:
                self.db.execute('INSERT OR IGNORE INTO updates(id,status,manifest_json,zip_path,backup_path,created_utc) VALUES(?,?,?,?,?,?)',
                    (uid,'STAGED',json.dumps(data,ensure_ascii=False),str(zip_path),str(store/uid),now()))
            self._log(f'Overlay logiciel {uid} prêt à vérifier : {len(info)} fichiers, aucun installé')
            return {'id':uid,'files':info,'description':data['description'],
                    'warning':'SHA-256 vérifie l’intégrité, PAS l’authenticité du code. Vérifier la provenance avant de confirmer.'}

    def apply_update(self,uid):
        with self.lock:
            if self.busy:raise ValueError('Attendre la fin du batch/import')
            row=self.db.execute('SELECT * FROM updates WHERE id=?',(uid,)).fetchone()
            if not row or row['status']!='STAGED':raise ValueError('Mise à jour introuvable ou déjà appliquée')
            path=Path(row['zip_path']);raw=path.read_bytes()
            manifest,info=self._check_overlay(raw)
            expected=json.loads(row['manifest_json'])['files']
            if info!=expected:raise ValueError('Fichiers locaux modifiés depuis la prévalidation')
            backup=Path(row['backup_path']);backup.mkdir(parents=True,exist_ok=True)
            for f in info:
                if f['overwrite']:
                    dest=self.repo.joinpath(*PurePosixPath(f['path']).parts)
                    saved=backup.joinpath(*PurePosixPath(f['path']).parts)
                    saved.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(dest,saved)
                    if sha_path(saved)!=f['previous_sha256']:raise ValueError('Échec sauvegarde : '+f['path'])
            replaced=[]
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as z:
                    for f in info:
                        dst=self.repo.joinpath(*PurePosixPath(f['path']).parts)
                        dst.parent.mkdir(parents=True,exist_ok=True)
                        temp=dst.with_name(dst.name+'.v30_install_tmp')
                        temp.write_bytes(z.read(f['path']))
                        if sha_path(temp)!=f['sha256']:
                            temp.unlink(missing_ok=True);raise ValueError('Échec écriture : '+f['path'])
                        os.replace(temp,dst);replaced.append(f)
            except Exception:
                for f in reversed(replaced):
                    dst=self.repo.joinpath(*PurePosixPath(f['path']).parts)
                    if f['overwrite']:shutil.copy2(backup.joinpath(*PurePosixPath(f['path']).parts),dst)
                    else:dst.unlink(missing_ok=True)
                raise
            with self.db:self.db.execute("UPDATE updates SET status='APPLIED',applied_utc=? WHERE id=?",(now(),uid))
            self._log(f'Mise à jour {uid} installée ({len(info)} fichiers), redémarrage recommandé')
            return {'ok':True,'installed':len(info),'restart_required':True,'update_id':uid}

    def rollback_update(self,uid):
        with self.lock:
            if self.busy:raise ValueError('Attendre la fin du batch/import')
            row=self.db.execute('SELECT * FROM updates WHERE id=?',(uid,)).fetchone()
            if not row or row['status']!='APPLIED':raise ValueError('Mise à jour non appliquée')
            infos=json.loads(row['manifest_json'])['files'];backup=Path(row['backup_path'])
            for f in infos:
                dst=self.repo.joinpath(*PurePosixPath(f['path']).parts)
                if not dst.is_file() or sha_path(dst)!=f['sha256']:
                    raise ValueError('Fichier modifié depuis l’installation : '+f['path'])
                if f['overwrite'] and sha_path(backup.joinpath(*PurePosixPath(f['path']).parts))!=f['previous_sha256']:
                    raise ValueError('Sauvegarde endommagée : '+f['path'])
            for f in reversed(infos):
                dst=self.repo.joinpath(*PurePosixPath(f['path']).parts)
                if f['overwrite']:shutil.copy2(backup.joinpath(*PurePosixPath(f['path']).parts),dst)
                else:dst.unlink()
            with self.db:self.db.execute("UPDATE updates SET status='ROLLED_BACK' WHERE id=?",(uid,))
            self._log('Retour arrière logiciel réalisé : '+uid)
            return {'ok':True,'restart_required':True}

class Handler(BaseHTTPRequestHandler):
    server_version='EncyKlopediaStation/30'
    def log_message(self,*args):pass
    def _send(self,status,obj,mime='application/json; charset=utf-8',filename=None):
        raw=obj if isinstance(obj,bytes) else json_text(obj)
        self.send_response(status)
        self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.send_header('X-Frame-Options','DENY')
        if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
        self.end_headers();self.wfile.write(raw)
    def _path(self):return urlparse(self.path).path
    def do_GET(self):
        s=self.server.station;p=self._path()
        try:
            if p=='/':self._send(200,(s.repo/'tools/unesco_pilot/poste_chatgpt_v30.html').read_bytes(),'text/html; charset=utf-8')
            elif p=='/app.js':self._send(200,(s.repo/'tools/unesco_pilot/poste_chatgpt_v30.js').read_bytes(),'text/javascript; charset=utf-8')
            elif p=='/bootstrap.js':self._send(200,('window.STATION_TOKEN='+json.dumps(self.server.token)+';').encode(),'text/javascript; charset=utf-8')
            elif p=='/api/state':self._send(200,s.snapshot())
            elif p=='/api/dispatch-small':
                name,raw=s.dispatch_small_v315();self._send(200,raw,'application/zip',name)
            elif p.startswith('/api/prompt/'):
                j=s.task(unquote(p.split('/')[-1]));self._send(200,{'prompt':prompt(j)})
            elif p.startswith('/api/bundle/'):
                path=s.bundle(unquote(p.split('/')[-1]));self._send(200,path.read_bytes(),'application/zip',path.name)
            else:self._send(404,{'error':'Route inconnue'})
        except (ValueError,OSError) as ex:self._send(400,{'error':str(ex)})
    def do_POST(self):
        s=self.server.station;p=self._path();host=f'127.0.0.1:{self.server.server_address[1]}'
        if (self.headers.get('Host')!=host or self.headers.get('Origin') not in (None,'http://'+host)
            or self.headers.get('Sec-Fetch-Site') not in (None,'same-origin','none')
            or self.headers.get('X-Station-Token')!=self.server.token):
            self._send(403,{'error':'Requête non locale refusée'});return
        try:
            if p=='/api/batch':s.batch();self._send(202,{'ok':True})
            elif p=='/api/prepare':s.prepare();self._send(202,{'ok':True})
            elif p.startswith('/api/sent/'):
                self._send(200,s.mark_sent(unquote(p.split('/')[-1])))
            elif p.startswith('/api/copy/'):
                ok,msg=s.native_clipboard(unquote(p.split('/')[-1]));self._send(200,{'ok':ok,'message':msg})
            elif p.startswith('/api/retry/'):
                self._send(200,s.retry(unquote(p.split('/')[-1])))
            elif p.startswith('/api/skip/'):
                self._send(200,s.skip(unquote(p.split('/')[-1])))
            elif p.startswith('/api/confirm-hold/'):
                self._send(200,s.confirm_hold(unquote(p.split('/')[-1])))
            elif p=='/api/reopen-holds':
                self._send(200,s.reopen_holds(500))
            elif p.startswith('/api/update/apply/'):
                self._send(200,s.apply_update(unquote(p.split('/')[-1])))
            elif p.startswith('/api/update/rollback/'):
                self._send(200,s.rollback_update(unquote(p.split('/')[-1])))
            elif p=='/api/update/stage':
                n=int(self.headers.get('Content-Length','-1'))
                if n<0 or n>21*1024*1024:raise ValueError('Overlay logiciel trop volumineux')
                if self.headers.get('Content-Type')!='application/zip':raise ValueError('Overlay ZIP requis')
                self._send(200,s.stage_update(self.rfile.read(n)))
            elif p=='/api/upload-batch':
                n=int(self.headers.get('Content-Length','-1'))
                if n<0 or n>MAX_REQUEST:raise ValueError('Upload trop volumineux (limite 110 Mo)')
                kind=self.headers.get('Content-Type','')
                if not kind.lower().startswith('multipart/form-data;'):raise ValueError('Envoi multipart requis')
                raw=self.rfile.read(n)
                mime=b'MIME-Version: 1.0\r\nContent-Type: '+kind.encode('ascii')+b'\r\n\r\n'+raw
                msg=BytesParser(policy=policy.default).parsebytes(mime)
                files=[]
                for part in msg.iter_parts():
                    if part.get_content_disposition()=='form-data' and part.get_filename():
                        data=part.get_payload(decode=True)
                        if data is not None:files.append((Path(part.get_filename()).name,data))
                self._send(202,s.receive(files))
            else:self._send(404,{'error':'Route inconnue'})
        except (ValueError,TypeError,OSError,sqlite3.Error,UnicodeError) as ex:self._send(400,{'error':str(ex)})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2])
    ap.add_argument('--work',type=Path,default=Path(os.environ.get('ENCYK_STATION_V30_WORK',WORK_DEFAULT)))
    ap.add_argument('--v27-work',type=Path,default=V27_DEFAULT)
    ap.add_argument('--v28-work',type=Path,default=V28_DEFAULT)
    ap.add_argument('--catalogue',type=Path,default=CAT_DEFAULT)
    ap.add_argument('--port',type=int,default=0)
    ap.add_argument('--no-browser',action='store_true')
    args=ap.parse_args();station=Station(args.repo,args.work,args.v27_work,args.v28_work,args.catalogue)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler);server.station=station;server.token=secrets.token_urlsafe(32)
    url=f'http://127.0.0.1:{server.server_address[1]}/'
    print('POSTE_CHATGPT_V30_OK '+url,flush=True)
    print('État SQLite : '+str(station.work/'station_v30.sqlite'),flush=True)
    if not args.no_browser:threading.Timer(.7,lambda:webbrowser.open(url)).start()
    try:server.serve_forever(poll_interval=.25)
    except KeyboardInterrupt:pass
    finally:server.server_close();station.db.close()
if __name__=='__main__':main()
