"""One-command, local-only UNESCO mt1.10 research pilot: concept10, then 41.

Reuses installed cumulative Lots 1-3 tools; DOES NOT create canonical
KQ/KP/KA/KS, translate articles, call AI APIs, or publish to GitHub.

Resume is at COMPLETE STAGE boundaries. A partial monolithic .bz2 XML pass
has no random-access restart here: on retry it is archived, then rescanned.
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from zipfile import ZipFile

PROFILE='koa.unesco-mt1-10-local-autopilot/1.0'
DEFAULT_DB=Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite')
DEFAULT_XML=Path(r'D:\EncyKlopedia\10_sources\wikipedia\enwiki\2026-10\enwiki-latest-pages-articles-multistream.xml.bz2')
DEFAULT_WORK=Path(r'D:\EncyKlopedia\30_working\unesco_mt1_10\autopilot_concept10_puis_41')
ROOT_DEFAULT=Path(r'C:\mycode')
PILOT_GLOB='UNESCO-Educational-Policy-Scope-EN-*.zip'
LOCALES=('en','fr','es','de','nl','sv','da','no','nn','fi','et','af','it','pt')


class PilotAutomationError(RuntimeError):pass


def now():return datetime.now(timezone.utc).isoformat(timespec='seconds')
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def sha_file(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for part in iter(lambda:f.read(1_048_576),b''):h.update(part)
    return h.hexdigest()


def json_read(p:Path, max_bytes=30_000_000):
    if not p.is_file() or p.stat().st_size>max_bytes:raise PilotAutomationError(f'Fichier absent/trop volumineux: {p}')
    return json.loads(p.read_text(encoding='utf-8'))


def atomic_json(p:Path,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,nam=tempfile.mkstemp(prefix='.tmp_unesco_',dir=p.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as out:
            json.dump(obj,out,sort_keys=True,indent=2,ensure_ascii=False)
            out.write('\n');out.flush();os.fsync(out.fileno())
        os.replace(nam,p)
    finally:
        if os.path.exists(nam):os.unlink(nam)


def stamp(p:Path,*,hash_small=False):
    if not p.is_file():raise PilotAutomationError('Fichier introuvable: '+str(p))
    a={'path':str(p.resolve()),'bytes':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns}
    if hash_small:a['sha256']=sha_file(p)
    return a


def outside_git(work:Path, roots:list[Path]):
    w=work.resolve()
    if w.is_symlink():raise PilotAutomationError('Chemin de travail symbolique interdit')
    for anc in (w,*w.parents):
        if (anc/'.git').exists():raise PilotAutomationError('Sortie privée impossible dans un dépôt Git: '+str(anc))
    for r in roots:
        if w==r.resolve() or r.resolve().is_relative_to(w):
            raise PilotAutomationError('La sortie ne doit pas englober une source')
    if w.exists() and not w.is_dir():raise PilotAutomationError('Sortie doit être un dossier')
    usage=shutil.disk_usage(w if w.exists() else next((a for a in w.parents if a.exists()), w.parent))
    if usage.free<2*1024**3:raise PilotAutomationError('Moins de 2 Gio libres: arrêt par prudence')
    return w


def choose_scope_zip(explicit:Path|None,root:Path,work:Path,interactive:bool):
    if explicit:return explicit.resolve()
    statefile=work/'etat_reprise.json'
    if statefile.is_file():
        state=json_read(statefile,max_bytes=1_000_000)
        saved=state.get('inputs',{}).get('scope_zip',{}).get('path')
        if isinstance(saved,str) and Path(saved).is_file():
            return Path(saved).resolve()
    dirs=[Path.home()/'Downloads',Path.home()/'Desktop',root/'EncyKlopedia'/'EncyKlopedia',
          root/'EncyKlopedia'/'UNESCO_Workbench',root/'Kristal'/'locals',work.parent]
    # Search only bounded directories, not recursive across large D: storage.
    found=[]
    for d in dirs:
        if d.is_dir():
            try:found += list(d.glob(PILOT_GLOB))
            except OSError:pass
    found=[p.resolve() for p in found if p.is_file()]
    unique={str(p):p for p in found}
    if len(unique)==1:return next(iter(unique.values()))
    if len(unique)>1:
        # Deterministic selection only if ALL candidate ZIP bytes are identical.
        digests={sha_file(p) for p in unique.values()}
        if len(digests)==1:return sorted(unique.values(),key=lambda p:str(p))[0]
    if interactive:
        try:
            import tkinter as tk
            from tkinter import filedialog
            r=tk.Tk();r.withdraw();r.attributes('-topmost',True)
            picked=filedialog.askopenfilename(title='Choisir le ZIP UNESCO Educational Policy (41 concepts)',
                                            filetypes=[('Archives ZIP','*.zip')])
            r.destroy()
            if picked:return Path(picked).resolve()
        except Exception:
            # Headless Windows, missing Tk or a canceled chooser: CLI error below.
            pass
    raise PilotAutomationError('ZIP UNESCO non trouvé sans ambiguïté. Glisser le ZIP sur le lanceur, ou utiliser --scope-zip.')


def _script(root:Path,rel:str):
    p=root/rel
    if not p.is_file():raise PilotAutomationError('Module du Lot 1/2/3 manquant: '+str(p))
    return p


def module_paths(root:Path):
    return {
        'preflight':_script(root,'EncyKlopedia/EncyKlopedia/tools/unesco_pilot/cumulative_preflight.py'),
        'inventory':_script(root,'EncyKlopedia/EncyKlopedia/tools/unesco_pilot/local_wikipedia_bridge.py'),
        'queue':_script(root,'Spek_Semantic-publishing/Spek/spek/unesco_pilot.py'),
        'xml':_script(root,'EncyKlopedia/EncyKlopedia/tools/unesco_pilot/offline_xml_evidence.py'),
        'dossier':_script(root,'Skope/Skope/tools/unesco_local_source_dossier.py'),
        'readiness':_script(root,'SemantiK_Architect/SemantiK_Runtime_Orchestrator/tools/unesco_14_locale_readiness.py'),
    }


class Runner:
    def __init__(self,work:Path, quiet=False):
        self.work=work;self.quiet=quiet
        self.log=work/'journal_autopilote.log'
        work.mkdir(parents=True,exist_ok=True)

    def say(self,event,**kw):
        line=json.dumps({'at':now(),'event':event,**kw},ensure_ascii=False,sort_keys=True)
        with self.log.open('a',encoding='utf-8') as f:f.write(line+'\n')
        if not self.quiet:print(line,flush=True)

    def cmd(self,stage,args,*,cwd=None):
        self.say('start',stage=stage)
        # Never launch a module inside ``spek/`` as a file: that makes the
        # sibling spek/locale.py shadow Python's standard-library ``locale``.
        # This matters with the user's Windows Python 3.14 (argparse -> gettext).
        command=[sys.executable,str(args[0]),*map(str,args[1:])]
        if stage=='projection_queue':
            spek_script=Path(args[0]).resolve()
            spek_pkg=spek_script.parent
            if (spek_script.name!='unesco_pilot.py' or spek_pkg.name!='spek' or
                    not (spek_pkg/'__init__.py').is_file()):
                raise PilotAutomationError('Spek: module UNESCO introuvable ou structure de paquet invalide')
            # Python -m resolves the package from its repository root, so
            # spek/locale.py cannot be mistaken for standard-library locale.
            cwd=spek_pkg.parent
            command=[sys.executable,'-m','spek.unesco_pilot',*map(str,args[1:])]
        with subprocess.Popen(command,
             cwd=str(cwd) if cwd else None,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
             encoding='utf-8',errors='replace',bufsize=1) as p:
            assert p.stdout is not None
            for raw in p.stdout:
                line=raw.rstrip('\r\n')
                with self.log.open('a',encoding='utf8') as f:f.write(line+'\n')
                if not self.quiet:print(line,flush=True)
            code=p.wait()
        if code!=0:raise PilotAutomationError(f'Étape {stage}: code {code}. Voir {self.log}')


class Lock:
    def __init__(self,folder):self.path=folder/'.autopilot.lock';self.fp=None
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.fp=self.path.open('a+b')
        if self.fp.tell()==0:self.fp.write(b'0');self.fp.flush()
        self.fp.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(self.fp.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(self.fp.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as e:
            self.fp.close()
            raise PilotAutomationError('Un autre autopilote est déjà actif pour ce dossier') from e
        return self
    def __exit__(self,exc_type,exc,tb):
        self.fp.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(self.fp.fileno(),msvcrt.LK_UNLCK,1)
        else:
            import fcntl
            fcntl.flock(self.fp.fileno(),fcntl.LOCK_UN)
        self.fp.close()


def verify_completed_step(state,name,file:Path):
    entry=state['steps'].get(name)
    if entry is None:
        if file.exists():raise PilotAutomationError(f'Sortie non enregistrée déjà présente: {file}; ne pas écraser')
        return False
    if not file.is_file() or sha_file(file)!=entry.get('sha256'):
        raise PilotAutomationError(f'Fichier déjà terminé modifié: {file}')
    return True


def commit_step(state,statefile,name,file,runner):
    if not file.is_file():raise PilotAutomationError(f'Résultat manquant pour {name}: {file}')
    state['steps'][name]={'path':str(file),'sha256':sha_file(file),'completed_at':now()}
    state['updated_at']=now()
    atomic_json(statefile,state)
    runner.say('stage_complete',stage=name,file=str(file))


def check_index_finished(db:Path):
    import sqlite3
    from urllib.parse import quote
    # SQLite is read-only; immutable requires a fully finished, inactive source.
    uri=db.resolve().as_uri()+'?mode=ro&immutable=1'
    try:
        conn=sqlite3.connect(uri,uri=True,timeout=8)
        conn.execute('PRAGMA query_only=ON')
        rows={row[0]:bool(row[1]) for row in conn.execute('SELECT stage,completed FROM ingest_state')}
        conn.close()
    except sqlite3.Error as e:
        raise PilotAutomationError('Index SQL illisible ou ingest_state absent : '+str(e)) from e
    wanted={'page','page_props','linktarget','externallinks','pagelinks','categorylinks'}
    if not all(rows.get(s) for s in wanted):
        raise PilotAutomationError('Index Wikipédia non achevé, stades manquants: '+', '.join(sorted(s for s in wanted if not rows.get(s))))


def verify_extraction(manifest:Path):
    d=json_read(manifest,max_bytes=20_000_000)
    if d.get('profile')!='encyklopedia.unesco-enwiki-text-evidence/1.0' or d.get('public_upload_authorized') is not False:
        raise PilotAutomationError('Manifest XML inattendu')
    for page in d.get('pages',[]):
        rel=page.get('relative_path')
        if rel:
            pid=page.get('page_id')
            if rel!=f'page-{pid}.wikitext.txt':raise PilotAutomationError('Chemin XML non sûr')
            p=manifest.parent/rel
            if not p.is_file() or sha_file(p)!=page.get('sha256'):
                raise PilotAutomationError('Empreinte XML modifiée : '+str(p))
    return d


def concept_record(inv:dict,dos:dict|None=None, cid='concept10'):
    records={r['unesco_id']:r for r in inv['records']}
    if cid not in records:raise PilotAutomationError('Concept cible absent : '+cid)
    r=records[cid]
    e=next((x for x in dos.get('entries',[]) if x.get('unesco_id')==cid),None) if dos else None
    eligible=0
    refs=[]
    if e:
        for link in e.get('wikipedia_en',[]):
            t=link.get('local_text') or {}
            if t.get('ai_context_eligible') is True:eligible+=1
            refs.append({'page_id':link.get('page_id'),'wikipedia_title':(link.get('wikipedia_page_metadata') or {}).get('title'),
                         'revision_id':t.get('revision_id'), 'text_sha256':t.get('text_sha256'),
                         'candidate_context_usable':t.get('ai_context_eligible') is True,
                         'source_status':t.get('source_integrity_status','NOT_EXTRACTED'),
                         'local_path':t.get('local_private_path') if t.get('ai_context_eligible') is True else None})
    else:
        refs=[{'page_id':x.get('page_id'),'wikipedia_title':x.get('title'),
               'candidate_context_usable':False,'source_status':'XML_NOT_YET_SCANNED'} for x in r.get('wikipedia_en_inventory',[])]
    return {'format':'koa.unesco-mt1-10-concept-research/1.0','branch':'unesco-mt1-10','unesco_id':cid,
            'source_uri':r.get('unesco_uri'),'preferred_labels':r.get('unesco_preferred_labels'),
            'skos':r.get('skos'),'wikidata_qid_candidate':r.get('wikidata',{}).get('qid'),
            'canonical_exact_match':False,'canonical_KQ':None,'canonical_KA':[],'canonical_KS':[],
            'wikipedia_local':refs,'candidate_wikipedia_contexts':eligible,
            'target_locales':list(LOCALES),'generated_articles':0,'semantic_grain':'one_branch_kristal',
            'research_only':True,'public_release_authorized':False,
            'next_step':'Explicit identity/claim/source review, canonical Kristal build and verified language realizations required.'}


def safe_resume_extract(out:Path,runner:Runner):
    if not out.exists():return
    if (out/'manifest.json').is_file():
        raise PilotAutomationError('Manifest XML déjà présent mais étape non validée; examen manuel nécessaire: '+str(out))
    backup=out.with_name(out.name+'-INCOMPLETE-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    if backup.exists():raise PilotAutomationError('Sauvegarde incomplète en conflit: '+str(backup))
    out.rename(backup)
    runner.say('archived_incomplete_xml_pass',path=str(backup))


def _finish_report(work,state,runner,*,xml_used):
    inv=json_read(work/'inventory.json')
    dossier=json_read(work/'skope_dossier.json') if (work/'skope_dossier.json').is_file() else None
    focus=concept_record(inv,dossier)
    report={'format':PROFILE,'branch':'unesco-mt1-10','status':'PRIVATE_RESEARCH_PREPARED_NOT_PUBLISHED',
            'concepts_discovered':len(inv['records']),'pilot_concept':'concept10',
            'qid_candidates':sum(bool(r['wikidata'].get('qid')) for r in inv['records']),
            'wikipedia_inventory_pages':sum(len(r.get('wikipedia_en_inventory',[])) for r in inv['records']),
            'wikipedia_candidate_contexts_eligible':sum(
                 1 for e in (dossier.get('entries',[]) if dossier else [])
                 for x in e.get('wikipedia_en',[]) if (x.get('local_text') or {}).get('ai_context_eligible') is True),
            'pilot_wikipedia_candidate_contexts_eligible':focus['candidate_wikipedia_contexts'],
            'xml_scan_performed':xml_used,'projections_planned':574,'articles_generated':0,
            'canonical_KA_approved':0,'locale_runtime_qualification_proven':False,
            'source_license_review_complete':False,'public_release_authorized':False,
            'work_directory':str(work),'steps_completed':sorted(state['steps'])}
    atomic_json(work/'RAPPORT_AUTO.json',report)
    text=('AUTOPILOTE UNESCO EDUCATIONAL POLICY — RECHERCHE PRIVÉE\n'
          '41 concepts; concept10 prioritaire; 14 langues; 574 emplacements planifiés.\n'
          f"Correspondances QID candidates : {report['qid_candidates']}\n"
          f"Contextes Wikipédia EN concordants pour concept10 : {focus['candidate_wikipedia_contexts']}\n"
          f"Contexte XML extrait : {'oui' if xml_used else 'non'}\n"
          'AUCUN Kristal canonique, KA/KS approuvé ou article publié créé automatiquement.\n'
          'Prêt pour l’examen sémantique et les vrais RuntimeSets linguistiques.\n'
          f'Rapport : {work / "RAPPORT_AUTO.json"}\n')
    (work/'LIRE_RESULTAT.txt').write_text(text,encoding='utf-8')
    runner.say('finish',**{k:v for k,v in report.items() if k in ('status','concepts_discovered','qid_candidates','projections_planned','wikipedia_candidate_contexts_eligible','pilot_wikipedia_candidate_contexts_eligible')})
    return report


def run(root:Path,scope_zip:Path,db:Path,xml:Path,work:Path,*,metadata_only=False,skip_install_preflight=False,quiet=False,runtime_root:Path|None=None):
    root=root.resolve();scope_zip=scope_zip.resolve();db=db.resolve();xml=xml.resolve()
    work=outside_git(work,[root,scope_zip,db,xml])
    files=module_paths(root)
    if not scope_zip.is_file():raise PilotAutomationError('ZIP source UNESCO absent')
    if not db.is_file():raise PilotAutomationError('Index SQLite absent: '+str(db))
    if not metadata_only and not xml.is_file():
        raise PilotAutomationError('Dump XML local absent: '+str(xml)+' ; utiliser --metadata-only pour préparer uniquement l’inventaire')
    with Lock(work):
        r=Runner(work,quiet=quiet)
        if not skip_install_preflight:r.cmd('installation',[files['preflight'],'--root',root])
        check_index_finished(db)
        # Source ZIP hashed once; for the huge DB/XML, track file metadata.
        inputs={'scope_zip':stamp(scope_zip,hash_small=True),'sqlite_index':stamp(db),
                'xml':stamp(xml) if xml.is_file() else None}
        statefile=work/'etat_reprise.json'
        if statefile.exists():
            state=json_read(statefile,max_bytes=1_000_000)
            if state.get('format')!=PROFILE or state.get('inputs')!=inputs:
                raise PilotAutomationError('Sources modifiées depuis la première exécution; choisir un nouveau --work, ne pas mélanger des archives')
            if state.get('public_release_authorized') is not False:raise PilotAutomationError('Statut de publication inattendu')
        else:
            state={'format':PROFILE,'inputs':inputs,'steps':{},'branch':'unesco-mt1-10',
                   'public_release_authorized':False,'started_at':now()}
            atomic_json(statefile,state)
        r.say('pilot_start',scope_zip=str(scope_zip),work=str(work),metadata_only=metadata_only)

        inventory=work/'inventory.json'
        if not verify_completed_step(state,'inventory',inventory):
            r.cmd('inventory',[files['inventory'],'build','--scope-zip',scope_zip,'--db',db,'--out',inventory])
            if len(json_read(inventory)['records'])!=41:raise PilotAutomationError('Inventaire ne contient pas 41 concepts')
            commit_step(state,statefile,'inventory',inventory,r)
        else:r.say('resume_skip',stage='inventory')
        inv=json_read(inventory)
        focus=work/'concept10'/'recherche_preliminaire.json'
        if not verify_completed_step(state,'concept10_preliminary',focus):
            atomic_json(focus,concept_record(inv))
            commit_step(state,statefile,'concept10_preliminary',focus,r)
        else:r.say('resume_skip',stage='concept10_preliminary')
        queue=work/'projection_queue_14_langues.json'
        if not verify_completed_step(state,'projection_queue',queue):
            r.cmd('projection_queue',[files['queue'],'--inventory',inventory,'--out',queue])
            if json_read(queue).get('projection_queue_size')!=574:raise PilotAutomationError('File de projections incorrecte')
            commit_step(state,statefile,'projection_queue',queue,r)
        else:r.say('resume_skip',stage='projection_queue')

        xml_manifest=None
        xmlout=work/'wikipedia_extract'
        if not metadata_only:
            xml_manifest=xmlout/'manifest.json'
            if state['steps'].get('xml_extract'):
                if not verify_completed_step(state,'xml_extract',xml_manifest):raise PilotAutomationError('Manifest XML manquant')
                verify_extraction(xml_manifest)
                r.say('resume_skip',stage='xml_extract')
            else:
                safe_resume_extract(xmlout,r)
                r.cmd('xml_extract',[files['xml'],'--inventory',inventory,'--xml',xml,'--out',xmlout,'--progress-every','1000000'])
                verify_extraction(xml_manifest)
                commit_step(state,statefile,'xml_extract',xml_manifest,r)

        if not metadata_only:
            dossier=work/'skope_dossier.json'
            if not verify_completed_step(state,'skope_dossier',dossier):
                r.cmd('skope_dossier',[files['dossier'],'--inventory',inventory,'--xml-manifest',xml_manifest,'--out',dossier])
                commit_step(state,statefile,'skope_dossier',dossier,r)
            else:r.say('resume_skip',stage='skope_dossier')
            d=json_read(dossier)
            # Atomic set of 41 per-concept cards, each idempotent.
            for rec in inv['records']:
                cid=rec['unesco_id']
                file=work/'fiches'/(cid+'.json')
                key='fiche_'+cid
                if not verify_completed_step(state,key,file):
                    atomic_json(file,concept_record(inv,d,cid=cid))
                    commit_step(state,statefile,key,file,r)
            pilot=work/'concept10'/'recherche_avec_sources.json'
            if not verify_completed_step(state,'concept10_research',pilot):
                atomic_json(pilot,concept_record(inv,d))
                commit_step(state,statefile,'concept10_research',pilot,r)
            else:r.say('resume_skip',stage='concept10_research')

            # Runtime readiness is information only. Never assert 14 qualified.
            rt=root/'SemantiK_Architect'/'SemantiK_Runtime_Orchestrator'
            rtroot=runtime_root or Path(r'D:\EncyKlopedia\30_working\semantik-runtime')
            if rtroot.is_dir():
                out=work/'readiness_14_langues.json'
                if not verify_completed_step(state,'runtime_readiness',out):
                    try:
                        r.cmd('runtime_readiness',[files['readiness'],'--runtime-root',rtroot,'--out',out],cwd=rt)
                    except PilotAutomationError as error:
                        # Runtime qualification is optional research information,
                        # not a reason to hide completed research stage outputs.
                        r.say('runtime_readiness_blocked',detail=str(error))
                    else:
                        commit_step(state,statefile,'runtime_readiness',out,r)
            else:
                r.say('readiness_not_run',detail='RuntimeSet folder absent; aucune langue déclarée qualifiée')
        report=_finish_report(work,state,r,xml_used=not metadata_only)
        return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',nargs='?',choices=('run','status'),default='run')
    p.add_argument('--root',type=Path,default=ROOT_DEFAULT)
    p.add_argument('--scope-zip',type=Path)
    p.add_argument('--db',type=Path,default=DEFAULT_DB)
    p.add_argument('--xml',type=Path,default=DEFAULT_XML)
    p.add_argument('--work',type=Path,default=DEFAULT_WORK)
    p.add_argument('--runtime-root',type=Path,help='Optional real SemantiK runtime folder; checked only if present')
    p.add_argument('--metadata-only',action='store_true',help='No XML scan, just pilot/inventory/574 queue')
    p.add_argument('--non-interactive',action='store_true',help='Fail if no unique source ZIP can be found')
    args=p.parse_args(argv)
    try:
        if args.command=='status':
            file=args.work/'RAPPORT_AUTO.json'
            if file.is_file():print(json.dumps(json_read(file),indent=2,ensure_ascii=False))
            else:
                state=args.work/'etat_reprise.json'
                print(json.dumps(json_read(state) if state.is_file() else {'status':'NEVER_STARTED'},indent=2,ensure_ascii=False))
            return 0
        archive=choose_scope_zip(args.scope_zip,args.root,args.work,interactive=not args.non_interactive)
        report=run(args.root,archive,args.db,args.xml,args.work,metadata_only=args.metadata_only,runtime_root=args.runtime_root)
        print('\nFIN : '+report['status']+'\nRapport : '+str(args.work/'RAPPORT_AUTO.json'),flush=True)
        return 0
    except (PilotAutomationError,ValueError,KeyError,TypeError,OSError,subprocess.SubprocessError) as e:
        print(json.dumps({'status':'BLOCKED','error':str(e),'public_release_authorized':False},ensure_ascii=False),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
