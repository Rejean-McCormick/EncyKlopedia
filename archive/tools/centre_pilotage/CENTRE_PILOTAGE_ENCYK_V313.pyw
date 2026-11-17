#!/usr/bin/env python3
"""Centre EncyKlopedia v31.3 — supervised, read-only, noncanonical.

Uses the unchanged v31.2 audit as the source of truth for branch reconciliation.
No imports, scheduling of production, admissions, deletions or DB writes.
"""
from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import json
import queue
import threading
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import encyk_global_v313 as monitor

HERE = Path(__file__).resolve().parent
AUDIT_SCRIPT = HERE / 'AUDIT_AUTOMATIQUE_BRANCHE_V312.pyw'


def load_audit():
    if not AUDIT_SCRIPT.is_file():
        raise FileNotFoundError(f'Moteur d’audit v31.2 introuvable : {AUDIT_SCRIPT}')
    loader = importlib.machinery.SourceFileLoader('encyk_auto_v312', str(AUDIT_SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def collect(paths, branch, audit=None):
    """One coherent method for CLI and GUI; sequential read-only source checks."""
    a = audit or load_audit()
    args = SimpleNamespace(branche=branch,station=Path(paths['station']),
                           catalogue=Path(paths['catalogue']),decouverte=Path(paths['decouverte']))
    branch_report, concepts, actions, samples, discovered = a.analyze_branch(args)
    global_report = monitor.summarize(paths, branch)
    return {'branche': branch_report, 'global': global_report}, concepts, actions, samples, discovered


def export_reports(folder, result, concepts, actions, samples, discovered, audit=None):
    """Exports solely to the requested report folder; never into SQLite sources."""
    a = audit or load_audit()
    folder = Path(folder).expanduser().resolve()
    source_paths = {Path(x['path']).resolve() for x in result['global']['sources'].values() if x.get('available')}
    if folder in source_paths or any(folder == p.parent for p in source_paths):
        raise ValueError('Choisir un dossier de rapports différent de celui des bases de production')
    branch_paths, _summary = a.save_auto_report(folder, result['branche'], concepts, actions, samples, discovered)
    d = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    overall = folder / f'SUPERVISION_GLOBALE_V313_{d}.json'
    a.write_atomic(overall,(json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    return [overall, *branch_paths]


def human(v):
    if v is None: return '—'
    if isinstance(v, int): return format(v, ',').replace(',', ' ')
    if isinstance(v, float): return format(v,'.2f').replace('.', ',')
    return str(v)


def snapshot_summary(result):
    br, glob = result['branche'], result['global']
    stat, rec = br.get('station', {}), br.get('rapprochement', {})
    s=glob.get('station',{}); k=glob.get('kristal_prive',{})
    return '\n'.join([
        'EncyKlopedia — centre de pilotage v31.3 (lecture seule)',
        'Branche : ' + str(br.get('branch_id')),
        'Tâches station : ' + human(s.get('jobs_total')) + '; READY : ' + human(s.get('jobs_ready')),
        'UNESCO tranchés : ' + human(stat.get('avancement_stock_station_tranche_pct')) + ' %',
        'HOLD à préserver : ' + human(rec.get('paires_station_hold')),
        'Découverts absents des deux index : ' + human(rec.get('paires_decouvertes_absentes_station_et_catalogue')),
        'Concepts sans APPROVE : ' + human(rec.get('concepts_configures_sans_approve')),
        'Kristal privé : ' + human(k.get('claims')) + ' connaissances candidates',
        'Achèvement réel : NON DÉMONTRÉ (rappel/saturation non évalués).',
    ])


def main():
    parser=argparse.ArgumentParser(description='Centre de pilotage EncyKlopedia v31.3 — lecture seule')
    parser.add_argument('--once',action='store_true',help='diagnostic+export une fois, sans interface')
    parser.add_argument('--branche',default='unesco.mt1.10')
    parser.add_argument('--output',type=Path,default=Path.home()/'Documents'/'EncyKlopedia_Audits')
    for name, default in monitor.DEFAULT_PATHS.items():
        parser.add_argument('--'+name,type=Path,default=default)
    opts=parser.parse_args()
    paths={k: getattr(opts,k) for k in monitor.DEFAULT_PATHS}
    if opts.once:
        result, concepts, actions, samples, discovered = collect(paths, opts.branche)
        files=export_reports(opts.output,result,concepts,actions,samples,discovered)
        print(snapshot_summary(result))
        print('Rapports :', *map(str,files), sep='\n  ')
        return
    dashboard=Dashboard(paths, opts.branche, opts.output)
    dashboard.mainloop()


class Dashboard:
    """Tkinter wrapper, created only when a user starts the graphical UI."""
    def __new__(cls, paths, branche, output):
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        from tkinter.scrolledtext import ScrolledText
        BG='#f4f7fb'; DARK='#132e49'; SLATE='#415a72'; BLUE='#1766a3'; TEAL='#14796d'
        root=tk.Tk();root.title('EncyKlopedia · Centre de pilotage v31.3 · Lecture seule')
        root.geometry('1130x810');root.minsize(900,650);root.configure(bg=BG)
        try: root.tk.call('tk','scaling',1.2)
        except tk.TclError: pass
        q=queue.Queue(); state={'busy':False,'result':None,'concepts':None,'actions':None,'samples':None,
                               'keys':None,'timer':None}
        branch=tk.StringVar(value=branche);folder=tk.StringVar(value=str(output))
        interval=tk.StringVar(value='Désactivé');status=tk.StringVar(value='Lecture seule · aucune modification des bases de production')
        path_vars={k:tk.StringVar(value=str(v)) for k,v in paths.items()}

        style=ttk.Style(root)
        try:style.theme_use('clam')
        except tk.TclError:pass
        style.configure('Treeview',rowheight=25,font=('Segoe UI',9))
        style.configure('Treeview.Heading',font=('Segoe UI Semibold',9))
        style.configure('TNotebook.Tab',padding=(18,10))
        header=tk.Frame(root,bg=DARK,padx=20,pady=16);header.pack(fill='x')
        tk.Label(header,text='ENCYKLOPEDIA   /   CENTRE DE PILOTAGE',font=('Segoe UI Semibold',17),
                 bg=DARK,fg='white').pack(anchor='w')
        tk.Label(header,text='UNESCO · couverture · station · Kristal privé   •   aucune admission canonique',
                 font=('Segoe UI',10),bg=DARK,fg='#bbd8ec').pack(anchor='w',pady=(4,0))
        controls=tk.Frame(root,bg=BG,padx=16,pady=10);controls.pack(fill='x')
        tk.Label(controls,text='Branche',bg=BG,fg=SLATE).pack(side='left')
        tk.Entry(controls,textvariable=branch,width=20).pack(side='left',padx=(8,16))
        update_btn=ttk.Button(controls,text='Actualiser les 5 bases');update_btn.pack(side='left',padx=(0,8))
        export_btn=ttk.Button(controls,text='Exporter les rapports',state='disabled');export_btn.pack(side='left',padx=(0,8))
        copy_btn=ttk.Button(controls,text='Copier le bilan',state='disabled');copy_btn.pack(side='left')
        tk.Label(controls,text='Suivi local',bg=BG,fg=SLATE).pack(side='left',padx=(18,6))
        combo=ttk.Combobox(controls,textvariable=interval,values=['Désactivé','15 minutes','30 minutes','60 minutes'],
                           width=14,state='readonly');combo.pack(side='left')

        tabs=ttk.Notebook(root);tabs.pack(fill='both',expand=True,padx=14,pady=(0,10))
        overview=ttk.Frame(tabs,padding=16);unesco=ttk.Frame(tabs,padding=14)
        kristal=ttk.Frame(tabs,padding=16);sources=ttk.Frame(tabs,padding=14)
        tabs.add(overview,text='Vue générale');tabs.add(unesco,text='UNESCO · 41 concepts')
        tabs.add(kristal,text='Kristal privé');tabs.add(sources,text='Sources et sécurité')

        summary=ScrolledText(overview,height=11,font=('Consolas',11),wrap='word',padx=12,pady=10)
        summary.pack(fill='both',expand=True);summary.configure(state='disabled')
        tk.Label(overview,text='Alertes de supervision (aucune opération exécutée)',
                 font=('Segoe UI Semibold',11),fg=DARK).pack(anchor='w',pady=(12,4))
        alerts=ScrolledText(overview,height=9,wrap='word',font=('Segoe UI',10),padx=12,pady=9)
        alerts.pack(fill='both',expand=True);alerts.configure(state='disabled')

        tree_frame=tk.Frame(unesco);tree_frame.pack(fill='both',expand=True)
        concept_cols=[('concept_id',135),('label_fr',290),('candidats_decouverts',95),
                      ('approve_importes',75),('hold_station',75),('absents_station_et_catalogue',85),('alertes',325)]
        concept_tree=ttk.Treeview(tree_frame,columns=[x[0] for x in concept_cols],show='headings')
        for col,width in concept_cols:
            concept_tree.heading(col,text={'concept_id':'Concept','label_fr':'Libellé','candidats_decouverts':'Découverts',
               'approve_importes':'APPROVE','hold_station':'HOLD','absents_station_et_catalogue':'Non suivis',
               'alertes':'Vérifications'}.get(col,col))
            concept_tree.column(col,width=width,minwidth=55,stretch=(col in ('label_fr','alertes')))
        concept_tree.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(tree_frame,command=concept_tree.yview);scroll.pack(side='right',fill='y')
        concept_tree.configure(yscrollcommand=scroll.set)
        action_label=tk.StringVar(value='Aucun résultat chargé')
        ttk.Label(unesco,textvariable=action_label).pack(anchor='w',pady=(10,5))
        action_cols=['type','concept_fr','page_id','title','candidate_id']
        action_tree=ttk.Treeview(unesco,columns=action_cols,show='headings',height=9)
        for col,width in zip(action_cols,[170,200,80,340,185]):
            action_tree.heading(col,text={'type':'Motif','concept_fr':'Concept','page_id':'Page',
                                           'title':'Article','candidate_id':'Candidat'}[col])
            action_tree.column(col,width=width,stretch=col in ('title','concept_fr'))
        action_tree.pack(fill='both',expand=True)

        private_intro=tk.Label(kristal,fg=DARK,text='Kristal : supervision agrégée uniquement',
            font=('Segoe UI Semibold',14));private_intro.pack(anchor='w',pady=(0,7))
        tk.Label(kristal,fg=SLATE,justify='left',wraplength=900,text=(
            'Les connaissances, citations, contenus d’articles et charges utiles privées ne sont jamais chargés '
            'dans l’interface. Seuls les compteurs agrégés sont lus.')).pack(anchor='w',pady=(0,14))
        private_text=ScrolledText(kristal,font=('Consolas',12),wrap='word',padx=12,pady=12)
        private_text.pack(fill='both',expand=True);private_text.configure(state='disabled')

        ttk.Label(sources,text='Chemins SQLite existants — lecture seule').pack(anchor='w',pady=(0,10))
        for k,label in [('station','Station v30'),('catalogue','Catalogue v25'),('decouverte','Découverte v28'),
                        ('kristal','Kristal cumulatif privé'),('packs','File et packs Kristal')]:
            row=ttk.Frame(sources);row.pack(fill='x',pady=4)
            ttk.Label(row,text=label,width=25).pack(side='left')
            ttk.Entry(row,textvariable=path_vars[k]).pack(side='left',fill='x',expand=True,padx=(0,5))
            def pick(name=k):
                x=filedialog.askopenfilename(parent=root,title='Choisir la base SQLite '+name,
                    filetypes=[('SQLite','*.sqlite'),('Tous fichiers','*.*')]);
                if x:path_vars[name].set(x)
            ttk.Button(row,text='Parcourir',command=pick).pack(side='right')
        ttk.Separator(sources).pack(fill='x',pady=15)
        ttk.Label(sources,text='Dossier de rapports (écritures locales uniquement)').pack(anchor='w',pady=(0,6))
        outrow=ttk.Frame(sources);outrow.pack(fill='x')
        ttk.Entry(outrow,textvariable=folder).pack(side='left',fill='x',expand=True,padx=(0,8))
        ttk.Button(outrow,text='Choisir',command=lambda:folder.set(filedialog.askdirectory(parent=root) or folder.get())).pack(side='left')
        security=ScrolledText(sources,height=11,wrap='word',font=('Segoe UI',10),padx=10,pady=7)
        security.pack(fill='both',expand=True,pady=(15,0));security.insert('end',(
            'GARANTIES\n\n'
            '• Connexions SQLite avec mode=ro et query_only=ON.\n'
            '• Aucun démarrage/arrêt de tâche ni découverte.\n'
            '• Aucun import UNESCO, aucune admission canonique, aucune publication.\n'
            '• Aucun effacement des candidats, HOLD, preuves ou empreintes.\n'
            '• Le module d’audit v31.2 est réutilisé sans modification.\n'
            '• Le pourcentage réel de complétude demeure indéterminé.\n'
            '• Les lectures entre bases ne constituent pas un instantané atomique.\n'
            '• Les exports peuvent contenir des titres et métadonnées : les garder locaux.\n'))
        security.configure(state='disabled')
        bottom=tk.Frame(root,bg=BG,padx=16,pady=10);bottom.pack(fill='x')
        ttk.Label(bottom,textvariable=status).pack(side='left',fill='x',expand=True)

        def set_text(widget,text):
            widget.configure(state='normal');widget.delete('1.0','end');widget.insert('1.0',text);widget.configure(state='disabled')

        def fill(data):
            res, concepts, actions, samples, keys=data
            state.update(result=res,concepts=concepts,actions=actions,samples=samples,keys=keys)
            set_text(summary,snapshot_summary(res)+'\n\nDonnées diagnostiques (elles ne constituent pas une preuve de saturation).')
            set_text(alerts,'\n'.join('• '+x for x in (res['global']['alertes']+res['branche'].get('avertissements',[]))) or 'Aucune alerte signalée.')
            for x in concept_tree.get_children(): concept_tree.delete(x)
            for row in concepts:
                concept_tree.insert('', 'end', values=[human(row.get(c)) for c,_ in concept_cols])
            for x in action_tree.get_children(): action_tree.delete(x)
            for row in actions[:300]:
                action_tree.insert('', 'end', values=[human(row.get(c)) for c in action_cols])
            action_label.set(f'{human(len(actions))} lignes à vérifier (300 premières affichées ; CSV intégral sur export)')
            k=res['global']['kristal_prive'];p=res['global']['packs_kristal'];s=res['global']['station']
            lines=[
                'Connaissances privées : '+human(k.get('claims')),
                'Citations enregistrées : '+human(k.get('citations')),
                'Articles visités : '+human(k.get('article_visits')),
                'Deltas importés : '+human(k.get('delta_imports')),
                'Packs préparés : '+human(p.get('packs_prepares')),
                'États de la file source : '+json.dumps(p.get('articles_par_etat'),ensure_ascii=False),
                'États de provenance : '+json.dumps(k.get('claims_par_source_status'),ensure_ascii=False),
                '\nStation globale (UNESCO + Kristal) :',
                'Tâches totales : '+human(s.get('jobs_total')),
                'Tâches READY : '+human(s.get('jobs_ready')),
                'Tâches ouvertes : '+human(s.get('jobs_ouverts')),
                'Répartition : '+json.dumps(s.get('jobs_par_type'),ensure_ascii=False,indent=2),
            ]
            set_text(private_text,'\n'.join(lines))
            export_btn.configure(state='normal');copy_btn.configure(state='normal')
            status.set('Audit terminé en lecture seule ; aucune tâche ou preuve modifiée')

        def request_run():
            if state['busy']: return
            p={k:Path(v.get().strip()) for k,v in path_vars.items()}
            name=branch.get().strip() or 'unesco.mt1.10'
            state['busy']=True;update_btn.configure(state='disabled')
            status.set('Lecture des cinq bases en cours…')
            def worker():
                try: q.put(('ok',collect(p,name)))
                except Exception as e: q.put(('error',type(e).__name__+': '+str(e)))
            threading.Thread(target=worker,daemon=True).start()

        def poll():
            try:
                kind,payload=q.get_nowait()
            except queue.Empty:
                root.after(100,poll);return
            state['busy']=False;update_btn.configure(state='normal')
            if kind=='error':
                status.set('Échec du diagnostic — sources inchangées');messagebox.showerror('EncyKlopedia',payload,parent=root)
            else: fill(payload)
            root.after(100,poll)

        def export():
            if state['result'] is None:return
            try:
                files=export_reports(folder.get(),state['result'],state['concepts'],state['actions'],
                                     state['samples'],state['keys'])
                status.set(f'{len(files)} rapports enregistrés dans '+str(Path(folder.get())))
                messagebox.showinfo('Exports terminés','\n'.join(str(p.name) for p in files),parent=root)
            except Exception as e:messagebox.showerror('Export impossible',str(e),parent=root)

        def copy():
            if not state['result']: return
            root.clipboard_clear();root.clipboard_append(snapshot_summary(state['result']))
            status.set('Bilan copié dans le presse-papiers')

        def schedule_refresh(*_):
            if state['timer'] is not None:
                root.after_cancel(state['timer']);state['timer']=None
            minutes={'15 minutes':15,'30 minutes':30,'60 minutes':60}.get(interval.get())
            if minutes:
                def fire():
                    state['timer']=None;request_run();schedule_refresh()
                state['timer']=root.after(minutes*60*1000,fire)
        update_btn.configure(command=request_run)
        export_btn.configure(command=export);copy_btn.configure(command=copy)
        combo.bind('<<ComboboxSelected>>',schedule_refresh)
        def on_close():
            if state['timer'] is not None:root.after_cancel(state['timer'])
            root.destroy()
        root.protocol('WM_DELETE_WINDOW',on_close)
        root.after(150,request_run);root.after(100,poll)
        return root


if __name__=='__main__':
    main()
