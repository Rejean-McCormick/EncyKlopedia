#!/usr/bin/env python3
"""Etat des bases EncyKlopedia v30, en lecture seule et avec cout des requetes borne.

Ne deduit jamais le taux d'achevement de la BRANCHE a partir des seuls lots traites.
"""
import argparse, collections, csv, datetime as dt, html, json, os, re, sqlite3, sys, time
from pathlib import Path

DEFAULT_BASES={
 'station_v30':r'D:\EncyKlopedia\30_working\poste_chatgpt_v30\station_v30.sqlite',
 'decouverte_unesco_v28':r'D:\EncyKlopedia\30_working\decouverte_articles_relies_v28\DECOUVERTE_ARTICLES_RELIES_V28.sqlite',
 'catalogue_unesco_wikipedia_v25':r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite',
 'kristal_v27':r'D:\EncyKlopedia\30_working\production_kristals_v27\KRISTAL_CUMULATIF_PRIVE_V27.sqlite',
}
TERM=re.compile(r'candidate|candidat|revue|review|decis|tache|task|lot|batch|assign|affect|article|concept|unesco|kristal|import|catalog|queue|branch|branche|link|lien',re.I)
STATUS_RE=re.compile(r'(^|_)(status|statut|etat|state|decision|resultat|review_status)(_|$)',re.I)
CAND_RE=re.compile(r'candidate_id|candidat_id|id_candidate|id_candidat',re.I)
BRANCH_RE=re.compile(r'branch_id|branche_id|branch|branche',re.I)
DONE={'APPROVE','REJECT','HOLD'}


def q(name):return '"'+str(name).replace('"','""')+'"'


def bounded(con,sql,params=(),seconds=1.5):
    limit=time.monotonic()+seconds
    con.set_progress_handler(lambda: int(time.monotonic()>limit),1000)
    try:return con.execute(sql,params).fetchall()
    finally:con.set_progress_handler(None,0)


def inspect_db(name,filepath,table_limit=100,per_query_timeout=1.4,per_base_timeout=25):
    deadline=time.monotonic()+per_base_timeout
    result={'nom':name,'chemin':str(filepath),'existe':Path(filepath).is_file(),'erreurs':[], 'tables':[], 'branche_couverture':[]}
    if not result['existe']:return result
    result['taille_octets']=Path(filepath).stat().st_size
    try:
        # URI read-only: no implicit creation, no data updates, zero ALTER/INSERT.
        conn=sqlite3.connect(Path(filepath).resolve().as_uri()+'?mode=ro',uri=True,timeout=2)
        conn.execute('PRAGMA query_only=ON')
        conn.execute('PRAGMA busy_timeout=1500')
        try:
            tablenames=[r[0] for r in bounded(conn,"SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name",seconds=3)]
        except sqlite3.Error as exc:
            result['erreurs'].append('Liste tables indisponible: '+str(exc));return result
        result['nombre_tables']=len(tablenames)
        chosen=[t for t in tablenames if TERM.search(t)]
        if not chosen:chosen=tablenames[:table_limit]
        if len(chosen)>table_limit:
            result['erreurs'].append(f'{len(chosen)-table_limit} tables non analysees (limite de protection)')
        for table in chosen[:table_limit]:
            if time.monotonic()>=deadline:
                result['erreurs'].append('Analyse arretee par limite de temps sans toucher a la base')
                break
            t={'table':table,'lignes':None,'lignes_exactes':False,'colonnes':[],'repartitions':{},'avertissements':[]}
            try:
                cols=[r[1] for r in conn.execute(f'PRAGMA table_info({q(table)})')]
                t['colonnes']=cols
                try:
                    val=bounded(conn,f'SELECT COUNT(*) FROM {q(table)}',seconds=min(per_query_timeout,max(.1,deadline-time.monotonic())))
                    t['lignes']=int(val[0][0])
                    t['lignes_exactes']=True
                except (sqlite3.Error,IndexError,ValueError) as exc:
                    t['avertissements'].append('Comptage interrompu pour eviter une requete lourde')
                if t['lignes_exactes'] and t['lignes']<=180000 and t['lignes']>0:
                    stcols=[col for col in cols if STATUS_RE.search(col)]
                    for col in stcols[:3]:
                        try:
                            data=bounded(conn,f'SELECT CAST({q(col)} AS TEXT),COUNT(*) FROM {q(table)} GROUP BY {q(col)} ORDER BY COUNT(*) DESC LIMIT 24',seconds=min(per_query_timeout,max(.1,deadline-time.monotonic())))
                            t['repartitions'][col]=[[str(v or '(vide)')[:200],int(n)] for v,n in data]
                        except sqlite3.Error:
                            t['avertissements'].append('Statuts incomplets: '+col)
                # La couverture par branche est le taux de revue parmi les candidats
                # deja presents dans cette table, PAS la completion du thésaurus.
                cid=next((col for col in cols if CAND_RE.fullmatch(col)),None)
                branch=next((col for col in cols if BRANCH_RE.fullmatch(col)),None)
                dec=next((col for col in cols if col.lower() in ('decision','decision_final','review_decision','review_status')),None)
                if cid and branch and dec and t['lignes_exactes'] and t['lignes']<=180000:
                    try:
                        data=bounded(conn,f'SELECT {q(branch)}, COUNT(DISTINCT {q(cid)}), '
                            f"COUNT(DISTINCT CASE WHEN UPPER(TRIM(CAST({q(dec)} AS TEXT))) IN ('APPROVE','REJECT','HOLD') THEN {q(cid)} END) "
                            f'FROM {q(table)} WHERE {q(cid)} IS NOT NULL GROUP BY {q(branch)}',
                            seconds=min(per_query_timeout,max(.1,deadline-time.monotonic())))
                        for branch_name,total,reviewed in data:
                            if not total: continue
                            result['branche_couverture'].append({
                                'base':name,'table':table,'branche':str(branch_name or '(non renseignee)'),
                                'identifies':int(total),'revus':int(reviewed),
                                'pourcentage_revu_parmi_identifies':round(100*int(reviewed)/int(total),2),
                                'note':'Taux sur identifiants distincts dans cette table seulement; pas la fin de la branche UNESCO.'})
                    except sqlite3.Error:t['avertissements'].append('Repartition par branche non disponible')
            except sqlite3.Error as exc:t['avertissements'].append(str(exc))
            result['tables'].append(t)
        try:conn.close()
        except Exception:pass
    except Exception as exc:result['erreurs'].append(str(exc))
    return result


def read_local_returns(dirs,scan_limit=2500):
    """Comptabiliser les fichiers DECISIONS locaux, pas tous les imports v30."""
    import zipfile,io
    files=[];seenpaths=set();errors=[]
    for folder in dirs:
        p=Path(folder)
        if not p.is_dir():continue
        for base,subdirs,filenames in os.walk(p):
            depth=len(Path(base).relative_to(p).parts)
            if depth>=3:subdirs[:]=[]
            for f in filenames:
                if f.startswith('RETOUR_UNESCO_V28_') and f.lower().endswith('.zip'):
                    path=Path(base)/f
                    if path not in seenpaths:files.append(path);seenpaths.add(path)
                if len(files)>=scan_limit:break
            if len(files)>=scan_limit:break
    counts=collections.Counter();packs={}
    for path in files:
        try:
            with zipfile.ZipFile(path) as z:
                candidates=[n for n in z.namelist() if re.search(r'(^|/)DECISIONS_v28_.*\.csv$',n,re.I)]
                if len(candidates)!=1:continue
                data=list(csv.DictReader(io.StringIO(z.read(candidates[0]).decode('utf-8-sig'))))
                valid=bool(data) and all(row.get('candidate_id','').strip() for row in data) and len(set(row.get('candidate_id','') for row in data))==len(data)
                if not valid:errors.append(f'candidate_id dupliques : {path}');continue
                pid=Path(candidates[0]).stem.removeprefix('DECISIONS_')
                if pid in packs:continue  # evite doublons de fichiers copies
                c=collections.Counter(row.get('decision','').strip().upper() for row in data)
                if set(c)-DONE:
                    errors.append(f'Decisions inconnues : {path}');continue
                packs[pid]={'archive':str(path),'lignes':len(data),'decisions':dict(c)}
                counts.update(c)
        except Exception as exc:errors.append(f'{path}: {exc}')
    n=sum(counts.values())
    tranche=counts.get('APPROVE',0)+counts.get('REJECT',0)
    synthese={'propositions_dans_retours':n,
              'approbations':counts.get('APPROVE',0),'rejets':counts.get('REJECT',0),
              'holds':counts.get('HOLD',0),
              'taux_approbation_sur_propositions_pourcentage':round(100*counts.get('APPROVE',0)/n,2) if n else None,
              'taux_rejet_sur_propositions_pourcentage':round(100*counts.get('REJECT',0)/n,2) if n else None,
              'taux_decisions_tranchees_pourcentage':round(100*tranche/n,2) if n else None,
              'taille_moyenne_lot':round(n/len(packs),2) if packs else None,
              'plus_petit_lot':min((p['lignes'] for p in packs.values()),default=None),
              'plus_grand_lot':max((p['lignes'] for p in packs.values()),default=None)}
    return {'synthese':synthese,'archives_reperees':len(files),'lots_valides_distincts':len(packs),'decisions_des_fichiers_locaux':dict(counts),
            'lots':packs,'erreurs':errors,
            'note':'Les retours ZIP locaux ne prouvent pas leur import dans la station v30; ne pas les additionner aux totaux de base.'}


def write_html(report,path):
    esc=html.escape
    cards=[]
    for name,db in report['bases'].items():
        if not db['existe']:
            cards.append('<section><h2>'+esc(name)+'</h2><p>Base absente sur ce poste.</p></section>');continue
        rows=[]
        for t in db['tables']:
            counts='non mesure' if t['lignes'] is None else format(t['lignes'],',').replace(',',' ')
            statuses='; '.join(esc(col)+': '+', '.join(esc(s)+'='+str(n) for s,n in values[:8]) for col,values in t['repartitions'].items())
            rows.append('<tr><td>'+esc(t['table'])+'</td><td class="num">'+counts+'</td><td>'+statuses+'</td></tr>')
        cards.append(f'<section><h2>{esc(name)}</h2><p>{esc(db["chemin"])} — {db.get("nombre_tables","?")} tables</p>'+
            '<table><thead><tr><th>Table</th><th>Lignes</th><th>Etats possibles</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></section>')
    branchcards=[]
    for db in report['bases'].values():
        for row in db['branche_couverture']:
            pct=row['pourcentage_revu_parmi_identifies'] or 0
            branchcards.append('<tr><td>'+esc(row['base']+' / '+row['table']+' / '+row['branche'])+'</td><td>'+str(row['revus'])+'</td><td>'+str(row['identifies'])+'</td><td>'+str(pct)+' %</td></tr>')
    section='<section><h2>Revues des candidats dejà identifiés</h2><p>Attention : le taux suivant ne mesure jamais le pourcentage de la branche UNESCO globale.</p><table><tr><th>Provenance</th><th>Revus</th><th>Identifiés</th><th>Taux sur stock connu</th></tr>'+''.join(branchcards)+'</table></section>' if branchcards else ''
    returns=report['retours_locaux']
    resume=returns['synthese']
    output=f'''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EncyKlopedia v30 — Statistiques globales</title><style>
body{{font:15px/1.55 system-ui,Segoe UI,Arial,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1.5rem;color:#203040;background:#f5f7f9}}
h1{{margin-bottom:0}}p{{color:#4e6070}}section{{background:#fff;border:1px solid #dde3ea;border-radius:12px;padding:18px;margin:18px 0;overflow:auto}}
table{{border-collapse:collapse;width:100%;font-size:13px}}th,td{{padding:9px 10px;border-bottom:1px solid #e4e7ed;text-align:left;vertical-align:top}}th{{background:#f0f4f8}}.num{{text-align:right;white-space:nowrap}}.notice{{background:#fff8e9;border-left:4px solid #b58e31;padding:14px}}
</style><body><h1>EncyKlopedia v30 — Statistiques globales</h1><p>Généré : {esc(report['date'])}</p>
<p class="notice"><b>Avancement de toute la branche UNESCO : inconnu sans inventaire complet du travail futur.</b> Les nombres affichés sont des instantanés en lecture seule, pas un contrôle de l'état canonique.</p>
<section><h2>ZIPs de decisions repérés localement</h2><p>{returns['lots_valides_distincts']} lots distincts ; {esc(str(returns['decisions_des_fichiers_locaux']))}</p><p><strong>APPROVE : {resume['approbations']} | REJECT : {resume['rejets']} | HOLD : {resume['holds']}</strong><br>Taux de rejet parmi ces fichiers : {resume['taux_rejet_sur_propositions_pourcentage'] if resume['taux_rejet_sur_propositions_pourcentage'] is not None else 'indisponible'} % ; taille moyenne des lots : {resume['taille_moyenne_lot'] if resume['taille_moyenne_lot'] is not None else 'indisponible'}.</p><p>Ce relevé n'atteste ni l'import ni la publication.</p></section>
{section}{''.join(cards)}</body></html>'''
    path.write_text(output,encoding='utf-8')


def main(argv=None):
    ap=argparse.ArgumentParser(description='Rapports de bases v30 en lecture seule')
    ap.add_argument('--sortie',type=Path,default=Path(os.environ.get('TEMP') or '.')/'STATS_GLOBAL_ENCYKLOPEDIA_V30')
    ap.add_argument('--station');ap.add_argument('--decouverte');ap.add_argument('--catalogue');ap.add_argument('--kristal')
    ap.add_argument('--repertoires-retours',nargs='*',default=[])
    ap.add_argument('--secondes-par-requete',type=float,default=1.5)
    args=ap.parse_args(argv)
    paths=dict(DEFAULT_BASES)
    for k,v in [('station_v30',args.station),('decouverte_unesco_v28',args.decouverte),('catalogue_unesco_wikipedia_v25',args.catalogue),('kristal_v27',args.kristal)]:
        if v:paths[k]=v
    out=args.sortie;out.mkdir(parents=True,exist_ok=True)
    reports={name:inspect_db(name,path,per_query_timeout=max(.2,min(10,args.secondes_par_requete))) for name,path in paths.items()}
    ret=read_local_returns(args.repertoires_retours)
    report={'format':'encyklopedia.stats.globales.v30/1','date':dt.datetime.now().isoformat(timespec='seconds'),
            'mode':'lecture_seule','bases':reports,'retours_locaux':ret,
            'branche_globale_achèvement_pourcentage':None,
            'note':'Pourcentage de la branche totale impossible a calculer sans univers exhaustif (candidats pas encore decouverts). Aucun taux n est invente.'}
    (out/'STATS_GLOBAL_ENCYKLOPEDIA_V30.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[f"ENCIKLOPEDIA V30 | {report['date']}","LECTURE SEULE - AUCUNE MODIFICATION SQLITE",
           'BRANCHE UNESCO COMPLETE : POURCENTAGE INCONNU sans inventaire exhaustif des candidats futurs.','']
    for name,base in reports.items():
        lines.extend(['='*75,'BASE : '+name,'CHEMIN : '+base['chemin'],
                      'DISPONIBLE : '+('OUI' if base['existe'] else 'NON')])
        if not base['existe']:continue
        lines.append('NB TABLES : '+str(base.get('nombre_tables','inconnu')))
        for t in base['tables']:
            n=str(t['lignes']) if t['lignes_exactes'] else 'non mesure (requete bornee)'
            lines.append('  '+t['table']+' | '+n+' lignes | colonnes: '+', '.join(t['colonnes']))
            for col,vals in t['repartitions'].items():lines.append('    '+col+' = '+str(vals))
            if t['avertissements']:lines.append('    Attention : '+'; '.join(t['avertissements']))
        if base['branche_couverture']:
            lines.append('COUVERTURE CANDIDATS IDENTIFIES (NE PAS CONFONDRE AVEC BRANCHE GLOBALE) :')
            for v in base['branche_couverture']:
                lines.append(f"  {v['table']} / {v['branche']}: {v['revus']} / {v['identifies']} soit {v['pourcentage_revu_parmi_identifies']} %")
        if base['erreurs']:lines.append('ERREURS : '+str(base['erreurs']))
    lines.extend(['','='*75,'FICHIERS RETOURS DISPONIBLES LOCALEMENT',
                  f"Lots distincts : {ret['lots_valides_distincts']}",
                  'Decisions dans ZIPs (ne prouvent pas leur import) : '+str(ret['decisions_des_fichiers_locaux']),
                  'Synthese des retours locaux : '+str(ret['synthese']),
                  'RAPPEL : ne pas additionner les compteurs de tables et de retours locaux.'])
    (out/'STATS_GLOBAL_ENCYKLOPEDIA_V30.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
    with (out/'TABLES_ENCYKLOPEDIA_V30.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['base','table','lignes','exact','colonnes','distributions_statuts'])
        for name,b in reports.items():
            for t in b['tables']:writer.writerow([name,t['table'],t['lignes'] if t['lignes'] is not None else '',t['lignes_exactes'],'; '.join(t['colonnes']),json.dumps(t['repartitions'],ensure_ascii=False)])
    with (out/'STATISTIQUES_RETOURS_UNESCO_V28.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['lot','lignes','APPROVE','REJECT','HOLD','taux_approbation_pourcentage','taux_rejet_pourcentage','archive_locale'])
        for lot,donnees in sorted(ret['lots'].items()):
            n=donnees['lignes'];c=donnees['decisions']
            writer.writerow([lot,n,c.get('APPROVE',0),c.get('REJECT',0),c.get('HOLD',0),
                             round(100*c.get('APPROVE',0)/n,2) if n else '',
                             round(100*c.get('REJECT',0)/n,2) if n else '',donnees['archive']])
    write_html(report,out/'TABLEAU_DE_BORD_ENCYKLOPEDIA_V30.html')
    print('Rapports statistiques generes :',out)
    for base in reports.values():print(base['nom'],':', 'OK' if base['existe'] else 'absente', '| tables:',base.get('nombre_tables','?'))
    print('Pourcentage global de branche : inconnu sans inventaire complet.')
    return 0

if __name__=='__main__':sys.exit(main())
