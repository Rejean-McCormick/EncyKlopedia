"""Interface Windows, journal live et exécution unique de bout en bout."""
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Les fichiers .pyw ouverts directement par Windows peuvent utiliser le mauvais
# pythonw.exe. Sélection et installation automatique avant toute exécution.
from runtime_bootstrap import bootstrap, BOOT_LOG, worker_executable
bootstrap()
from factory_core import Factory

BASE = Path(__file__).resolve().parent
from unesco_paths import default_factory_paths
PATHS = default_factory_paths(BASE)
ROOT = PATHS['root']

class App:
    def __init__(self,root):
        self.root=root;root.title('Kristal — Fabrique encyclopédique UNESCO × Wikidata × Spek — v1.6')
        root.geometry('1220x820');root.minsize(900,660)
        self.q=queue.Queue();self.cancel=threading.Event();self.running=False
        self.run_dir=None;self.report=None;self.catalogue=None;self.audit=None;self.artifacts={}
        self.configure_style()
        self.vars={
          'ttl':tk.StringVar(value=str(PATHS['ttl'])),
          'claims':tk.StringVar(value=str(PATHS['claims'])),
          'index':tk.StringVar(value=str(PATHS['index'])),
          'output':tk.StringVar(value=str(PATHS['output'])),
          'full_source':tk.StringVar(value=''), 'full_enabled':tk.BooleanVar(value=True),
          'ai_enabled':tk.BooleanVar(value=False),'ai_model':tk.StringVar(value=''),
          'ai_limit':tk.StringVar(value='0')}
        self.make_ui()
        self.add_artifact('ENVIRONNEMENT PYTHON : journal d’amorçage', BOOT_LOG)
        self.log.configure(state='normal')
        self.log.insert('end', f'Python GUI : {sys.executable}\nPython principal : {worker_executable()} (lecteur WD isolé au besoin)\nJournal Python : {BOOT_LOG}\n')
        self.log.configure(state='disabled')
        root.after(100,self.poll)
    def configure_style(self):
        s=ttk.Style(self.root)
        for theme in ('vista','clam'):
            if theme in s.theme_names():s.theme_use(theme);break
        s.configure('Heading.TLabel',font=('Segoe UI',17,'bold'))
        s.configure('Small.TLabel',font=('Segoe UI',9))
        s.configure('Large.TButton',font=('Segoe UI',11,'bold'),padding=(16,10))
    def make_ui(self):
        self.root.configure(bg='#f5f7fb')
        top=ttk.Frame(self.root,padding=14);top.pack(fill='x')
        ttk.Label(top,text='FABRIQUE · UNESCO → WIKIDATA → KRISTALS → SPEK',style='Heading.TLabel').pack(anchor='w')
        ttk.Label(top,text='Un seul lancement · 88 kristals v9 · 4 500 notices Spek FR/EN · journal de preuve · aucune publication',style='Small.TLabel').pack(anchor='w',pady=(3,0))
        fields=ttk.LabelFrame(self.root,text='Sources et sortie (lecture seule des sources)',padding=10)
        fields.pack(fill='x',padx=14,pady=3)
        for i,(key,title,kind) in enumerate([
           ('ttl','Turtle UNESCO officiel','file'),('claims','CSV P3916 (facultatif : téléchargement si absent)','file'),
           ('index','SQLite Wikidata local (facultatif)','file'),
           ('full_source','Source fiches complètes Wikidata : dump indexé / JSONL / dossier Skope (vide = auto)','file'),
           ('output','Racine de sortie — nouveau RUN à chaque exécution','dir')]):
            ttk.Label(fields,text=title).grid(row=i,column=0,sticky='w',padx=(0,10),pady=4)
            ttk.Entry(fields,textvariable=self.vars[key]).grid(row=i,column=1,sticky='ew',pady=4)
            ttk.Button(fields,text='Parcourir…',command=lambda k=key,t=kind:self.browse(k,t)).grid(row=i,column=2,padx=(8,0))
        fields.grid_columnconfigure(1,weight=1)
        fullopts=ttk.Frame(self.root,padding=(14,6));fullopts.pack(fill='x')
        ttk.Checkbutton(fullopts,text='Importer les entités Wikidata complètes (dump local indexé ou fiches préextraites) — sans modification du canon',variable=self.vars['full_enabled']).pack(side='left')
        opts=ttk.Frame(self.root,padding=(14,8));opts.pack(fill='x')
        ttk.Checkbutton(opts,text='Enrichissement local Ollama (propositions séparées, NON canoniques)',variable=self.vars['ai_enabled']).pack(side='left')
        ttk.Label(opts,text='Modèle :').pack(side='left',padx=(14,4))
        ttk.Entry(opts,width=17,textvariable=self.vars['ai_model']).pack(side='left')
        ttk.Label(opts,text='Limite (0 = tous) :').pack(side='left',padx=(14,4))
        ttk.Entry(opts,width=7,textvariable=self.vars['ai_limit']).pack(side='left')
        actions=ttk.Frame(self.root,padding=(14,3));actions.pack(fill='x')
        self.btn_run=ttk.Button(actions,text='▶  TOUT CONSTRUIRE + VALIDER',style='Large.TButton',command=self.start)
        self.btn_run.pack(side='left')
        self.btn_stop=ttk.Button(actions,text='■  Arrêter',command=self.request_stop,state='disabled')
        self.btn_stop.pack(side='left',padx=7)
        secondary_actions=ttk.Frame(self.root,padding=(14,0));secondary_actions.pack(fill='x')
        for i,(name,action) in enumerate([('Ouvrir encyclopédie',self.open_catalogue),('Ouvrir sortie',self.open_folder),
                            ('Ouvrir audit',self.open_audit),('Ouvrir discours Spek',self.open_discourse),('Ouvrir faits WD',self.open_facts),('Diagnostic WD',self.open_reader_diag),('Ouvrir log',self.open_log),('Copier log',self.copy_log),
                            ('Copier rapport',self.copy_report)]):
            parent=actions if i<4 else secondary_actions
            ttk.Button(parent,text=name,command=action).pack(side='left',padx=(4,0))
        status=ttk.Frame(self.root,padding=(14,6));status.pack(fill='x')
        self.phase=tk.StringVar(value='Prêt');ttk.Label(status,textvariable=self.phase).pack(side='left')
        self.progress=ttk.Progressbar(status,mode='determinate');self.progress.pack(side='right',fill='x',expand=True,padx=(25,0))
        main=ttk.Panedwindow(self.root,orient='horizontal');main.pack(fill='both',expand=True,padx=14,pady=(0,12))
        left=ttk.LabelFrame(main,text='Étapes et fichiers (double-clic = ouvrir)',padding=6)
        main.add(left,weight=1)
        self.tree=ttk.Treeview(left,show='tree',selectmode='browse')
        self.tree.pack(fill='both',expand=True,side='left')
        vs=ttk.Scrollbar(left,orient='vertical',command=self.tree.yview);vs.pack(side='right',fill='y')
        self.tree.configure(yscrollcommand=vs.set)
        self.tree.bind('<Double-1>',self.open_selection)
        self.tree.bind('<Button-3>',lambda e:self.copy_selection())
        ttk.Button(left,text='Copier contenu ou chemin sélectionné',command=self.copy_selected_content).pack(side='bottom',fill='x')
        right=ttk.LabelFrame(main,text='Journal en direct — commandes, résultats et erreurs',padding=6)
        main.add(right,weight=3)
        self.log=tk.Text(right,font=('Consolas',9),wrap='word',bg='#111d2c',fg='#e3ebf5',insertbackground='white')
        self.log.pack(fill='both',expand=True,side='left')
        sc=ttk.Scrollbar(right,orient='vertical',command=self.log.yview);sc.pack(side='right',fill='y')
        self.log.configure(yscrollcommand=sc.set)
        self.log.tag_configure('ERROR',foreground='#ff9a8a')
        self.log.tag_configure('WARN',foreground='#ffd18a')
        self.log.tag_configure('INFO',foreground='#dde9f6')
        self.log.insert('end','Prêt. Appuie sur « TOUT CONSTRUIRE + VALIDER ».\nLe processus crée un RUN indépendant et ne publie rien.\n')
        self.log.configure(state='disabled')
    def browse(self,key,kind):
        if key=='full_source':
            v=filedialog.askopenfilename(title='Source Wikidata complète ou annuler pour choisir le dossier Skope')
            if not v:v=filedialog.askdirectory(title='Dossier de parts Skope (snapshot-manifest.json)')
        else:v=filedialog.askdirectory() if kind=='dir' else filedialog.askopenfilename()
        if v:self.vars[key].set(v)
    def start(self):
        if self.running:return
        try:
            limit=int(self.vars['ai_limit'].get())
            if limit<0:raise ValueError()
        except ValueError:
            messagebox.showerror('Configuration','La limite IA doit être un entier positif ou 0.');return
        if self.vars['ai_enabled'].get() and not self.vars['ai_model'].get().strip():
            messagebox.showerror('Configuration','Indique le nom du modèle local Ollama ou désactive IA.');return
        cfg={k:v.get() for k,v in self.vars.items()};cfg['ai_limit']=limit
        self.running=True;self.cancel.clear();self.artifacts={}
        self.tree.delete(*self.tree.get_children())
        self.phase.set('Démarrage du pipeline complet...')
        self.progress['value']=0
        self.btn_run.configure(state='disabled');self.btn_stop.configure(state='normal')
        self.report=None;self.catalogue=None;self.audit=None;self.run_dir=None
        def work():
            try:Factory(cfg,event=lambda k,v:self.q.put((k,v)),stop=self.cancel.is_set).run()
            except Exception:pass  # Factory emits a full incident report and error event.
            finally:self.q.put(('thread_finished',{}))
        threading.Thread(target=work,daemon=True).start()
    def request_stop(self):
        if self.running:
            self.cancel.set();self.phase.set('Arrêt demandé…')
    def poll(self):
        try:
            for _ in range(150):
                typ,detail=self.q.get_nowait()
                if typ=='log':
                    self.log.configure(state='normal')
                    self.log.insert('end',detail['text']+'\n',detail['level'])
                    self.log.see('end');self.log.configure(state='disabled')
                elif typ=='run':
                    self.run_dir=Path(detail['path']);self.add_artifact('DOSSIER RUN',self.run_dir)
                elif typ=='phase':
                    self.phase.set(detail['name']+' · en cours')
                elif typ=='artifact':
                    self.add_artifact(detail['phase']+' : '+detail['name'],detail['path'])
                elif typ=='progress':
                    self.progress.configure(maximum=detail['total'],value=detail['done'])
                    self.phase.set(f"{detail['phase']} : {detail['done']} / {detail['total']}")
                elif typ=='complete':
                    self.report=Path(detail['report']);self.catalogue=Path(detail['catalogue'])
                    self.audit=Path(detail['audit']) if detail.get('audit') else None
                    if detail.get('discourse'):self.add_artifact('GRAMMAIRE DISCURSIVE SPEK : catalogue',detail['discourse'])
                    self.phase.set('TERMINÉ : '+detail['status'])
                    self.add_artifact('RAPPORT FINAL',self.report)
                elif typ=='failed':self.phase.set('ÉCHEC : '+detail['phase'])
                elif typ=='thread_finished':
                    self.running=False;self.btn_run.configure(state='normal');self.btn_stop.configure(state='disabled')
        except queue.Empty:pass
        self.root.after(130,self.poll)
    def add_artifact(self,name,path):
        key=str(len(self.artifacts)+1)
        self.artifacts[key]=str(path)
        self.tree.insert('','end',iid=key,text=name[:94])
        self.tree.see(key)
    def selected_path(self):
        ids=self.tree.selection()
        return Path(self.artifacts[ids[0]]) if ids else None
    def open_selection(self,event=None):self.open_path(self.selected_path())
    def copy_selection(self):
        p=self.selected_path()
        if p:self.copy(str(p))
    def copy_selected_content(self):
        p=self.selected_path()
        if not p:return
        if p.is_file() and p.stat().st_size<=4_000_000:
            try:self.copy(p.read_text(encoding='utf-8-sig'));return
            except UnicodeError:pass
        self.copy(str(p))
    def copy(self,txt):
        self.root.clipboard_clear();self.root.clipboard_append(txt);self.root.update()
    def open_path(self,p):
        if not p or not Path(p).exists():messagebox.showinfo('Information','Fichier non disponible pour le moment.');return
        try:
            if os.name=='nt':os.startfile(str(p))
            elif sys.platform=='darwin':subprocess.Popen(['open',str(p)])
            else:subprocess.Popen(['xdg-open',str(p)])
        except Exception as e:messagebox.showerror('Ouverture',str(e))
    def open_catalogue(self):self.open_path(self.catalogue or (self.run_dir/'04_SPEK/index.html' if self.run_dir else None))
    def open_audit(self):self.open_path(self.audit or (self.run_dir/'06_AUDIT/audit_p3916.html' if self.run_dir else None))
    def open_discourse(self):self.open_path(self.run_dir/'07_DISCOURS/index.html' if self.run_dir else None)
    def open_facts(self):self.open_path(self.run_dir/'02_WIKIDATA/FAITS_COMPLETS/faits_consultables.html' if self.run_dir else None)
    def open_reader_diag(self):self.open_path(self.run_dir/'02_WIKIDATA/FAITS_COMPLETS/reader_runtime.json' if self.run_dir else None)
    def open_folder(self):self.open_path(self.run_dir)
    def open_log(self):self.open_path(self.run_dir/'fabrique.log' if self.run_dir else None)
    def copy_log(self):
        if self.run_dir and (self.run_dir/'fabrique.log').exists():
            self.copy((self.run_dir/'fabrique.log').read_text(encoding='utf-8'))
        else:self.copy(self.log.get('1.0','end'))
    def copy_report(self):
        p=self.report or (self.run_dir/'RAPPORT_INCIDENT.json' if self.run_dir else None)
        if p and p.is_file():self.copy(p.read_text(encoding='utf-8'))
        else:messagebox.showinfo('Information','Rapport non encore disponible.')

def main():
    root=tk.Tk();App(root);root.mainloop()
if __name__=='__main__':main()
