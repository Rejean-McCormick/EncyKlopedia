#!/usr/bin/env python3
"""Tableau de bord V31: inventaire mondial, branches, qualifications et production.
Toutes les bases EncyKlopedia sont ouvertes avec mode=ro. L'outil n'écrit
que les fichiers du dossier de rapports. Les dénominateurs inconnus restent nuls.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
from html import escape
import importlib.util
import json
from pathlib import Path
import sqlite3
import time

SOURCE=Path(r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite')
QUAL=Path(r'D:\EncyKlopedia\30_working\qualification_multibranche_v31\qualification_multibranche_v31.sqlite')
STATION=Path(r'D:\EncyKlopedia\30_working\poste_chatgpt_v30\station_v30.sqlite')
DISCOVERY=Path(r'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28\DECOUVERTE_ARTICLES_RELIES_V28.sqlite')
CAT=Path(r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite')
KRISTAL=Path(r'D:\EncyKlopedia\30_working\production_kristals_v27\KRISTAL_CUMULATIF_PRIVE_V27.sqlite')

def utc():return datetime.now(timezone.utc).isoformat(timespec='seconds')

def ro(path):
    if not path.is_file():return None
    db=sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=5)
    db.execute('PRAGMA query_only=ON');db.execute('PRAGMA busy_timeout=3000')
    return db

def bounded(db,sql,params=(),seconds=8):
    deadline=time.monotonic()+seconds
    db.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
    try:return db.execute(sql,params).fetchall()
    finally:db.set_progress_handler(None,0)

def read_table(db,sql,params=()):
    if db is None:return None
    try:return bounded(db,sql,params)[0][0]
    except (sqlite3.Error,IndexError):return None

def group(db,sql):
    if db is None:return []
    try:return [list(x) for x in bounded(db,sql,seconds=12)]
    except sqlite3.Error:return []

def inspect(paths):
    result={'format':'encyklopedia.global-statistics.v31/2','date_utc':utc(),'bases':{},
            'avancement_complet_des_branches':None,'publication_autorisee':False,
            'note':'Les candidats connus ne sont pas tous les candidats qui restent à découvrir. Les profils ne valent pas validation UNESCO.'}
    for kind,path in paths.items():
        entry={'chemin':str(path),'present':path.is_file(),'octets':path.stat().st_size if path.is_file() else None}
        result['bases'][kind]=entry
        db=ro(path)
        if db is None:continue
        try:
            if kind=='source':
                # wiki_pages has an index on (ns,title); if counting is costly, leave unknown.
                entry['pages_ns0']=read_table(db,'SELECT COUNT(*) FROM wiki_pages WHERE ns=0')
                entry['pages_ns0_redirections']=read_table(db,'SELECT COUNT(*) FROM wiki_pages WHERE ns=0 AND redirect=1')
                entry['index_complet']=group(db,'SELECT stage,completed,rows_imported FROM ingest_state')
            elif kind=='qualification':
                entry['profils']=read_table(db,'SELECT COUNT(*) FROM article_profiles')
                entry['sans_branche']=read_table(db,'SELECT COUNT(*) FROM article_profiles WHERE branch_candidates=0')
                entry['suggestions']=read_table(db,'SELECT COUNT(*) FROM branch_suggestions')
                entry['multibranches']=read_table(db,'SELECT COUNT(*) FROM article_profiles WHERE branch_candidates>1')
                entry['par_branche']=group(db,'SELECT branch_id,COUNT(*),ROUND(AVG(score),1) FROM branch_suggestions GROUP BY branch_id ORDER BY COUNT(*) DESC')
                entry['par_type']=group(db,'SELECT kind,COUNT(*) FROM article_profiles GROUP BY kind ORDER BY COUNT(*) DESC')
                entry['dernier_page_id']=read_table(db,"SELECT CAST(value AS INTEGER) FROM meta WHERE key='cursor_page_id'")
            elif kind=='station':
                entry['taches_par_statut']=group(db,'SELECT kind,status,COUNT(*),SUM(count) FROM jobs GROUP BY kind,status ORDER BY kind,status')
                entry['candidats_par_statut']=group(db,'SELECT state,COUNT(*) FROM review_index GROUP BY state')
                entry['decisions_importees']=group(db,"SELECT SUM(review_approved),SUM(review_rejected),SUM(review_hold) FROM jobs WHERE kind='v28' AND status='DONE'")
                entry['postes']=read_table(db,'SELECT COUNT(*) FROM lanes')
                entry['candidats_par_branche_et_statut']=group(db,
                    'SELECT branch_id,state,COUNT(*) FROM review_index GROUP BY branch_id,state ORDER BY branch_id,state')
                entry['reserve_differee']=read_table(db,"SELECT COUNT(*) FROM review_index WHERE state='DEFERRED'")
                entry['profils_nouvelles_branches']=read_table(db,'SELECT COUNT(DISTINCT branch_id) FROM review_index')
                entry['revues_terminees_par_branche']=group(db,'''
                    SELECT COALESCE(route.branch_id,'branche_historique'),COUNT(*),
                      SUM(j.review_approved),SUM(j.review_rejected),SUM(j.review_hold)
                    FROM jobs j LEFT JOIN v311_job_routes route ON route.job_id=j.id
                    WHERE j.kind='v28' AND j.status='DONE'
                    GROUP BY COALESCE(route.branch_id,'branche_historique')''')
            elif kind=='decouverte':
                entry['candidats_connus']=read_table(db,'SELECT COUNT(*) FROM candidates')
                entry['preuves_liens']=read_table(db,'SELECT COUNT(*) FROM evidence')
                entry['candidats_par_branche']=group(db,'SELECT branch_id,COUNT(*) FROM candidates GROUP BY branch_id')
                entry['graines_par_branche']=group(db,'SELECT branch_id,state,COUNT(*) FROM seed_queue GROUP BY branch_id,state')
            elif kind=='catalogue':
                entry['branches']=read_table(db,'SELECT COUNT(*) FROM branches')
                entry['concepts']=read_table(db,'SELECT COUNT(*) FROM concepts')
                entry['articles_integres']=read_table(db,'SELECT COUNT(*) FROM articles')
                entry['affectations']=read_table(db,'SELECT COUNT(*) FROM assignments')
                entry['par_branche']=group(db,'SELECT branch_id,COUNT(*) FROM assignments GROUP BY branch_id')
                entry['decisions_v28']=read_table(db,'SELECT COUNT(*) FROM reviewed_article_links_v28')
            elif kind=='kristal':
                entry['claims_prives']=read_table(db,'SELECT COUNT(*) FROM claims')
                entry['citations']=read_table(db,'SELECT COUNT(*) FROM citations')
                entry['deltas']=read_table(db,'SELECT COUNT(*) FROM delta_imports')
        finally:db.close()
    count=result['bases'].get('source',{}).get('pages_ns0')
    profile=result['bases'].get('qualification',{}).get('profils')
    result['inventaire_ns0_traite_pct']=round(profile/count*100,3) if count and profile is not None else None
    # This is coverage of the known *article namespace*, not completeness of concept classification.
    return result

def html_report(r):
    bases=r['bases']
    def value(k,field):
        v=bases.get(k,{}).get(field)
        return '—' if v is None else f'{v:,}'.replace(',',' ')
    cards=[('Articles Wikipédia ns=0',value('source','pages_ns0')),
           ('Profils V31',value('qualification','profils')),
           ('Sans branche (conservés)',value('qualification','sans_branche')),
           ('Associations proposées',value('qualification','suggestions')),
           ('Branches du catalogue',value('catalogue','branches')),
           ('Articles intégrés v25',value('catalogue','articles_integres')),
           ('Candidats UNESCO v28',value('decouverte','candidats_connus')),
           ('Kristal privé : citations',value('kristal','citations')),
           ('Candidats différés (non rejetés)',value('station','reserve_differee'))]
    blocks=''.join(f'<div class="card"><small>{escape(k)}</small><strong>{escape(v)}</strong></div>' for k,v in cards)
    tables=[]
    for name,d in bases.items():
        if not d.get('present'):continue
        rows=''.join(f'<tr><th>{escape(str(k))}</th><td>{escape(json.dumps(v,ensure_ascii=False))}</td></tr>' for k,v in d.items() if k not in ('chemin','present','octets'))
        tables.append(f'<section><h2>{escape(name)}</h2><p>{escape(d["chemin"])}</p><table>{rows}</table></section>')
    progress='Inconnu' if r['inventaire_ns0_traite_pct'] is None else str(r['inventaire_ns0_traite_pct'])+' %'
    return f'''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EncyKlopedia — Tableau de bord global V31</title>
<style>body{{margin:0;background:#f4f7fa;color:#243348;font:15px/1.6 system-ui,Segoe UI,sans-serif}}
header{{background:#18324b;color:#fff;padding:30px 5%}}main{{max-width:1220px;margin:24px auto;padding:0 20px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}}.card,section{{background:#fff;padding:18px;border:1px solid #dbe4ec;border-radius:12px}}
.card small{{display:block;color:#63758b}}.card strong{{display:block;font-size:26px;margin-top:6px}}
section{{margin-top:16px;overflow:auto}}table{{width:100%;border-collapse:collapse}}th,td{{text-align:left;border-bottom:1px solid #e2eaf2;padding:8px;vertical-align:top}}
th{{width:33%}}td{{overflow-wrap:anywhere}}p{{color:#54667b}}header p{{color:#e4edf5}}.caution{{border-left:4px solid #b68f42;padding:12px;background:#fff8ed}}</style>
<header><h1>EncyKlopedia · Statistiques globales V31</h1><p>Généré le {escape(r['date_utc'])} (UTC) · Bases consultées en lecture seule</p></header>
<main><div class="cards">{blocks}</div>
<section><h2>Progression d'inventaire</h2><p><strong>{escape(progress)}</strong> des pages ns=0 profilées, lorsque le dénominateur est mesuré.</p>
<p class="caution">Ceci n'est pas le taux d'achèvement des branches. Les rapprochements candidats ne sont pas des APPROVE et les profils sans branche restent conservés.</p></section>
{''.join(tables)}</main></html>'''

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sortie',type=Path,default=Path.home()/'Downloads'/'STATS_GLOBALES_ENCYKLOPEDIA_V31')
    for name,default in [('source',SOURCE),('qualification',QUAL),('station',STATION),('decouverte',DISCOVERY),('catalogue',CAT),('kristal',KRISTAL)]:
        ap.add_argument('--'+name,type=Path,default=default)
    ap.add_argument('--avec-historique-v30',action='store_true')
    a=ap.parse_args(argv)
    out=a.sortie;out.mkdir(parents=True,exist_ok=True)
    paths={name:getattr(a,name) for name in ('source','qualification','station','decouverte','catalogue','kristal')}
    try:r=inspect(paths)
    except (OSError,sqlite3.Error) as ex:
        print('Erreur statistiques V31:',ex);return 2
    (out/'STATS_GLOBALES_ENCYKLOPEDIA_V31.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'TABLEAU_DE_BORD_ENCYKLOPEDIA_V31.html').write_text(html_report(r),encoding='utf-8')
    if a.avec_historique_v30:
        old=Path(__file__).resolve().parents[2]/'outils_v30'/'stats_globales_v30.py'
        if old.is_file():
            spec=importlib.util.spec_from_file_location('stats_v30_existing',old)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            module.main(['--sortie',str(out/'Historique_V30'),
                '--station',str(a.station),'--decouverte',str(a.decouverte),
                '--catalogue',str(a.catalogue),'--kristal',str(a.kristal),
                '--repertoires-retours',str(Path.home()/'Downloads')])
    print(json.dumps({'status':'STATS_GLOBALES_V31_OK','rapport':str(out/'STATS_GLOBALES_ENCYKLOPEDIA_V31.json'),
       'tableau':str(out/'TABLEAU_DE_BORD_ENCYKLOPEDIA_V31.html'),
       'progression_inventaire_ns0_pct':r['inventaire_ns0_traite_pct'],
       'progression_des_branches_pct':None},ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':raise SystemExit(main())
