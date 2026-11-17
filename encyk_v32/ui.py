"""Une fenêtre Windows, six domaines, opérations lentes en arrière-plan; Tk stdlib."""
from __future__ import annotations
from pathlib import Path
import json
from contextlib import closing
import queue
import threading
from zipfile import ZipFile
import tkinter as tk
from tkinter import ttk,filedialog,messagebox,simpledialog
from .config import Settings
from .sql import open_work
from .sources import import_unesco,discover,discover_fallback
from .pipeline import make_wave,import_for_job,jobs_overview,export_proposals,retry_candidates,cancel_job,recovery_report
from .federation import scan_islands,list_islands
from .doctor import run as doctor_run

class ManagerUI(tk.Tk):
    def __init__(self,settings=None):
        super().__init__()
        self.settings=settings or Settings.load()
        self.title('EncyKlopedia V32.2 · Centre unifié')
        self.geometry('1190x790')
        self.minsize(950,600)
        self.configure(bg='#edf2f6')
        self.channel=queue.Queue();self.busy=False
        self.branch=tk.StringVar(value='')
        self.status=tk.StringVar(value='Prêt — registre privé, aucun accès canonique en écriture')
        self._layout()
        self.after(120,self._poll)
        self.after(380,self.refresh)

    def _layout(self):
        header=tk.Frame(self,bg='#15314a',padx=20,pady=16);header.pack(fill='x')
        tk.Label(header,text='ENCYKLOPEDIA   /   V32.2',bg='#15314a',fg='#a9d1eb',font=('Segoe UI Semibold',10)).pack(anchor='w')
        tk.Label(header,text='Manager de connaissances · UNESCO × Wikidata × Wikipédia × Kristal',
                 bg='#15314a',fg='white',font=('Segoe UI Semibold',17)).pack(anchor='w',pady=5)
        tk.Label(header,text='Propositions privées • états Kristal externes lus sans modification • 10 postes ChatGPT',
                 bg='#15314a',fg='#c8dce9',font=('Segoe UI',10)).pack(anchor='w')
        bar=tk.Frame(self,bg='#e3ebf3',padx=20,pady=10);bar.pack(fill='x')
        tk.Label(bar,text='Branche (vide = toutes)',bg='#e3ebf3').pack(side='left')
        ttk.Entry(bar,textvariable=self.branch,width=22).pack(side='left',padx=8)
        self.refresh_btn=ttk.Button(bar,text='Actualiser',command=self.refresh);self.refresh_btn.pack(side='left',padx=5)
        ttk.Button(bar,text='Vérifier les index',command=lambda:self._launch(self._doctor)).pack(side='left',padx=5)
        self.nb=ttk.Notebook(self);self.nb.pack(fill='both',expand=True,padx=14,pady=(10,4))
        self.views={}
        for key,title in [('dashboard','Vue globale'),('sources','Sources & index'),
                           ('branches','Branches UNESCO'),('production','Production ChatGPT'),
                           ('federation','Îlots Kristal'),('logs','Journal & diagnostics')]:
            page=tk.Frame(self.nb,bg='white',padx=14,pady=12)
            self.nb.add(page,text=title);self.views[key]=page
        self._make_dashboard();self._make_sources();self._make_branches();self._make_production();self._make_federation();self._make_logs()
        tk.Label(self,textvariable=self.status,anchor='w',bg='#e3ebf3',fg='#243f56',padx=14,pady=8).pack(fill='x')

    def _title(self,parent,title,subtitle=''):
        tk.Label(parent,text=title,bg='white',fg='#19344c',font=('Segoe UI Semibold',15)).pack(anchor='w',pady=(2,4))
        if subtitle:tk.Label(parent,text=subtitle,bg='white',fg='#647589',wraplength=950,justify='left').pack(anchor='w',pady=(0,10))

    def _make_dashboard(self):
        page=self.views['dashboard'];self._title(page,'Vue d’ensemble','Les chiffres décrivent le stock connu, pas la saturation encyclopédique.')
        self.dashboard=tk.Text(page,font=('Consolas',11),wrap='word',bg='#f7fafc',height=18,relief='flat',padx=15,pady=14)
        self.dashboard.pack(fill='both',expand=True)
        ttk.Button(page,text='Actualiser les compteurs',command=self.refresh).pack(anchor='w',pady=9)

    def _make_sources(self):
        page=self.views['sources'];self._title(page,'Sources et index locaux','Toujours réutiliser les index D:; aucun import global ni copie des dumps.')
        action=tk.Frame(page,bg='white');action.pack(anchor='w',pady=8)
        ttk.Button(action,text='1 · Indexer les 88 branches UNESCO',command=lambda:self._launch(self._index)).pack(side='left',padx=4)
        ttk.Button(action,text='2 · Découvrir par QID et graphe',command=lambda:self._launch(self._discover)).pack(side='left',padx=4)
        ttk.Button(action,text='Compléter les concepts sans QID',command=lambda:self._launch(self._fallback)).pack(side='left',padx=4)
        ttk.Button(action,text='Diagnostic des index',command=lambda:self._launch(self._doctor)).pack(side='left',padx=4)
        self.source_text=self._text(page)

    def _make_branches(self):
        page=self.views['branches'];self._title(page,'Branches et concepts UNESCO','88 espaces préparés; les correspondances P3916 restent des candidats.')
        self.branch_tree=ttk.Treeview(page,columns=('concepts','candidates'),show='headings')
        self.branch_tree['columns']=('branch','concepts','candidates')
        for name,label,w in [('branch','Branche',250),('concepts','Concepts',110),('candidates','Candidats',130)]:
            self.branch_tree.heading(name,text=label);self.branch_tree.column(name,width=w,anchor='w')
        self.branch_tree.pack(fill='both',expand=True)
        self.branch_tree.bind('<Double-1>',lambda e:self._set_branch())
        ttk.Button(page,text='Utiliser la branche sélectionnée',command=self._set_branch).pack(anchor='w',pady=8)

    def _make_production(self):
        page=self.views['production'];self._title(page,'Production ChatGPT — deux passes',
               'Passe 1 : sélectionner la pertinence. Passe 2 : enrichir généreusement les articles complets. Aucun canon écrit.')
        bar=tk.Frame(page,bg='white');bar.pack(anchor='w')
        ttk.Button(bar,text='Préparer la prochaine vague (10 postes max.)',command=lambda:self._launch(self._prepare)).pack(side='left',padx=3)
        ttk.Button(bar,text='Importer un ZIP de retour',command=self._pick_reply).pack(side='left',padx=3)
        ttk.Button(bar,text='Exporter les propositions privées',command=self._export).pack(side='left',padx=3)
        self.jobs_tree=ttk.Treeview(page,columns=('lane','type','job','count','status'),show='headings',height=11)
        for name,width in [('lane',70),('type',130),('job',145),('count',95),('status',150)]:
            self.jobs_tree.heading(name,text=name.capitalize());self.jobs_tree.column(name,width=width)
        self.jobs_tree.pack(fill='both',expand=True,pady=12)
        bottom=tk.Frame(page,bg='white');bottom.pack(anchor='w',pady=4)
        ttk.Button(bottom,text='Copier le prompt ChatGPT',command=self._copy_prompt).pack(side='left',padx=(0,7))
        ttk.Button(bottom,text='Afficher le dossier du ZIP',command=self._show_pack).pack(side='left')
        ttk.Button(bottom,text='Réexaminer un candidat',command=self._retry).pack(side='left',padx=5)
        ttk.Button(bottom,text='Annuler une tâche',command=self._cancel).pack(side='left',padx=5)
        ttk.Button(bottom,text='Diagnostic de reprise',command=lambda:self._launch(self._recover)).pack(side='left',padx=5)
        self.work_note=tk.StringVar(value='Aucun pack sélectionné')
        tk.Label(page,textvariable=self.work_note,bg='white',fg='#516578',wraplength=930).pack(anchor='w')

    def _make_federation(self):
        page=self.views['federation'];self._title(page,'Îlots Kristal — lecture fédérée',
               'Inventaire les espaces existants. Une vue dérivée ne vaut pas admission dans le Framework.')
        ttk.Button(page,text='Recenser les îlots (lecture seule)',command=lambda:self._launch(self._scan_islands)).pack(anchor='w',pady=8)
        self.islands=self._text(page)

    def _make_logs(self):
        page=self.views['logs'];self._title(page,'Journal d’exécution et diagnostics','Aucun contrôle global de 125 Go exécuté au lancement.')
        self.log=self._text(page)

    def _text(self,parent):
        wrap=tk.Text(parent,wrap='word',font=('Consolas',10),bg='#f7fafc',relief='flat',padx=12,pady=10)
        wrap.pack(fill='both',expand=True);return wrap

    def _set(self,widget,text):
        widget.configure(state='normal');widget.delete('1.0','end')
        widget.insert('end',text);widget.configure(state='disabled')

    def _append(self,message):
        self.log.configure(state='normal');self.log.insert('end',message+'\n\n');self.log.see('end');self.log.configure(state='disabled')

    def _launch(self,func):
        if self.busy:return
        self._branch_snapshot=self.branch.get().strip() or None
        self.busy=True;self.status.set('Opération en cours — les autres fonctions restent visibles')
        def run():
            try:self.channel.put(('result',func()))
            except Exception as exc:self.channel.put(('error',str(exc)))
        threading.Thread(target=run,daemon=True).start()

    def _poll(self):
        try:
            while True:
                kind,payload=self.channel.get_nowait()
                if kind=='sources':
                    self._set(self.source_text,json.dumps(payload,ensure_ascii=False,indent=2))
                    continue
                self.busy=False
                if kind=='error':
                    self.status.set('Opération refusée : '+payload)
                    self._append('ERREUR : '+payload)
                    messagebox.showerror('EncyK',payload)
                else:
                    self.status.set('Opération terminée')
                    self._append(json.dumps(payload,ensure_ascii=False,indent=2,default=str))
                    self.refresh()
        except queue.Empty:pass
        self.after(120,self._poll)

    def _doctor(self):
        result=doctor_run(self.settings)
        self.channel.put(('sources',result))
        return result
    def _index(self):
        with closing(open_work(self.settings.db_path)) as db:return import_unesco(db,self.settings.unesco_root)
    def _discover(self):
        with closing(open_work(self.settings.db_path)) as db:return discover(db,self.settings,getattr(self,'_branch_snapshot',None),max_pairs=10000)
    def _fallback(self):
        with closing(open_work(self.settings.db_path)) as db:
            return discover_fallback(db,self.settings,getattr(self,'_branch_snapshot',None),max_pages=2500)
    def _prepare(self):
        with closing(open_work(self.settings.db_path)) as db:return make_wave(db,self.settings,getattr(self,'_branch_snapshot',None))
    def _scan_islands(self):
        with closing(open_work(self.settings.db_path)) as db:return scan_islands(db,self.settings.kristal_roots)
    def _pick_reply(self):
        src=filedialog.askopenfilename(filetypes=[('Retours','*.zip *.csv *.json'),('Tous','*.*')])
        if not src:return
        job=simpledialog.askstring('Tâche source','ID du poste (SEL_000001 ou ENR_000001) :')
        if not job:return
        def op():
            with closing(open_work(self.settings.db_path)) as db:return import_for_job(db,Path(src),job.strip())
        self._launch(op)
    def _export(self):
        path=filedialog.asksaveasfilename(defaultextension='.jsonl',initialfile='ENCYK_PROPOSITIONS_PRIVEES.jsonl')
        if not path:return
        def op():
            with closing(open_work(self.settings.db_path)) as db:return export_proposals(db,path,getattr(self,'_branch_snapshot',None))
        self._launch(op)
    def _retry(self):
        cid=simpledialog.askstring('Réexamen','Identifiant du candidat (visible dans la CLI candidates) :')
        if not cid:return
        reason=simpledialog.askstring('Motif','Pourquoi réexaminer ce candidat ?')
        if not reason:return
        def op():
            with closing(open_work(self.settings.db_path)) as db:return retry_candidates(db,[cid.strip()],reason)
        self._launch(op)
    def _cancel(self):
        job=simpledialog.askstring('Annuler une tâche','Identifiant SEL_… ou ENR_… (les retours tardifs seront refusés) :')
        if not job:return
        reason=simpledialog.askstring('Motif','Pourquoi annuler cette tâche ?')
        if not reason:return
        def op():
            with closing(open_work(self.settings.db_path)) as db:return cancel_job(db,job.strip(),reason)
        self._launch(op)
    def _recover(self):
        with closing(open_work(self.settings.db_path)) as db:return recovery_report(db)
    def _copy_prompt(self):
        items=self.jobs_tree.selection()
        if not items:return
        tag=self.jobs_tree.item(items[0])['tags']
        if not tag:return
        try:
            with ZipFile(tag[0]) as z:prompt=z.read('INSTRUCTIONS_CHATGPT.md').decode('utf-8')
            self.clipboard_clear();self.clipboard_append(prompt)
            self.status.set('Prompt copié · joindre le ZIP manuellement dans une conversation ChatGPT')
        except (OSError,KeyError,ValueError) as exc:messagebox.showerror('Prompt inaccessible',str(exc))

    def _show_pack(self):
        items=self.jobs_tree.selection()
        if not items:return
        tag=self.jobs_tree.item(items[0])['tags']
        if not tag:return
        path=tag[0];self.work_note.set('Fichier ZIP : '+path)
        try:
            import os
            if os.name=='nt':os.startfile(str(Path(path).parent))
        except OSError:pass
    def _set_branch(self):
        sel=self.branch_tree.selection()
        if sel:self.branch.set(self.branch_tree.item(sel[0])['values'][0])

    def refresh(self):
        try:
            with closing(open_work(self.settings.db_path)) as db:
                data=jobs_overview(db)
                branches=[tuple(r) for r in db.execute('''SELECT b.branch_id,(SELECT COUNT(*) FROM branch_concepts WHERE branch_id=b.branch_id),
                      (SELECT COUNT(*) FROM candidates WHERE branch_id=b.branch_id) FROM branches b ORDER BY b.branch_id''')]
                islands=list_islands(db,limit=120)
            overview=(f'Branches: {data["branches"]}\nPropositions privées: {data["proposals"]}\n'
                      f'Candidats par état :\n{json.dumps(data["candidates"],indent=2,ensure_ascii=False)}\n\n'
                      f'Postes occupés : {sum(bool(x["job_id"]) for x in data["lanes"])}/10\n\n'
                      f'Index sources et configuration :\n{json.dumps(self.settings.paths_status(),indent=2,ensure_ascii=False)}')
            self._set(self.dashboard,overview)
            self._set(self.source_text,json.dumps(self.settings.paths_status(),ensure_ascii=False,indent=2))
            for item in self.branch_tree.get_children():self.branch_tree.delete(item)
            for item in branches:self.branch_tree.insert('', 'end',values=item)
            for item in self.jobs_tree.get_children():self.jobs_tree.delete(item)
            jobs={x['job_id']:x for x in data['jobs']}
            for l in data['lanes']:
                j=jobs.get(l['job_id']);values=(l['lane'],j['kind'] if j else 'LIBRE',l['job_id'] or '—',j['count'] if j else 0,j['status'] if j else '')
                self.jobs_tree.insert('','end',values=values,tags=((j['pack_path'],) if j else ()))
            self._set(self.islands,json.dumps(islands,ensure_ascii=False,indent=2))
        except Exception as exc:self._append('Actualisation impossible : '+str(exc))


def launch():
    ManagerUI().mainloop()
