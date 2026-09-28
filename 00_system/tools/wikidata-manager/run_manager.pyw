from __future__ import annotations
import csv,json,os,queue,shutil,subprocess,sys,threading,tkinter as tk
from pathlib import Path
from tkinter import filedialog,messagebox,ttk

BASE=Path(__file__).resolve().parent; ROOT=BASE.parents[2]; SCRIPTS=BASE/'scripts'; DIAG=BASE/'diagnostics'/'diag_environment.ps1'; DEFAULT_REG=ROOT/'10_sources/seeds/active/intellectual-registry/intellectuals.seed.json'

class App(tk.Tk):
    def __init__(self):
        super().__init__();self.title('EncyKlopedia — Wikidata Local Manager v0.9 FAST');self.geometry('1220x820');self.minsize(980,700)
        self.proc=None;self.q=queue.Queue();self.chain=[];self.rows=[];self.sel=set()
        self.registry=tk.StringVar(value=str(DEFAULT_REG));self.languages=tk.StringVar(value='fr,en,mul');self.depth=tk.IntVar(value=3);self.filter=tk.StringVar();self.status=tk.StringVar(value='Prêt')
        self._ui();self.after(100,self._drain);self._refresh_paths()
    def _ui(self):
        root=ttk.Frame(self,padding=8);root.pack(fill='both',expand=True);root.columnconfigure(0,weight=1);root.rowconfigure(1,weight=1)
        bar=ttk.Frame(root);bar.grid(row=0,column=0,sticky='ew',pady=(0,6));ttk.Label(bar,text='Racine').pack(side='left');ttk.Label(bar,text=str(ROOT)).pack(side='left',padx=6);ttk.Button(bar,text='Ouvrir racine',command=self._open_ws).pack(side='left',padx=4);ttk.Button(bar,text='Scopes → Evidence/Kristal',command=self._open_kristal_ingest).pack(side='left',padx=4);ttk.Button(bar,text='AUTO index global (optionnel)',command=self._auto).pack(side='right')
        self.nb=ttk.Notebook(root);self.nb.grid(row=1,column=0,sticky='nsew');self.tabs=[]
        for name in ['1 · Environnement','2 · Dump','3 · Index local','4 · Explorer']:
            f=ttk.Frame(self.nb,padding=10);self.nb.add(f,text=name);self.tabs.append(f)
        self._env(self.tabs[0]);self._dump(self.tabs[1]);self._index(self.tabs[2]);self._explorer(self.tabs[3])
        bot=ttk.Frame(root);bot.grid(row=2,column=0,sticky='ew',pady=(6,0));ttk.Label(bot,textvariable=self.status).pack(side='left');self.stop=ttk.Button(bot,text='Arrêter processus',command=self._stop,state='disabled');self.stop.pack(side='right')
    def _logbox(self,parent,row):
        parent.rowconfigure(row,weight=1);parent.columnconfigure(0,weight=1);t=tk.Text(parent,state='disabled',wrap='word');t.grid(row=row,column=0,columnspan=4,sticky='nsew',pady=(8,0));return t
    def _env(self,t):
        ttk.Button(t,text='Lancer diagnostic PowerShell 7',command=self._diag).grid(row=0,column=0,sticky='w');ttk.Button(t,text='Charger environment.json',command=self._load_diag).grid(row=0,column=1,sticky='w',padx=6);ttk.Button(t,text='Découvrir dump + plan',command=self._discover).grid(row=0,column=2,sticky='w');self.envtxt=self._logbox(t,1)
    def _dump(self,t):
        ttk.Button(t,text='Découvrir snapshot',command=self._discover).grid(row=0,column=0,sticky='w');ttk.Button(t,text='Télécharger / reprendre',command=self._download).grid(row=0,column=1,sticky='w',padx=6);ttk.Button(t,text='Vérifier SHA-1',command=self._verify).grid(row=0,column=2,sticky='w');self.dumptxt=self._logbox(t,1)
    def _index(self,t):
        ttk.Label(t,text='Langues labels/alias').grid(row=0,column=0,sticky='w');ttk.Entry(t,textvariable=self.languages,width=24).grid(row=0,column=1,sticky='w',padx=6);ttk.Button(t,text='Construire / reprendre index SQLite',command=self._build).grid(row=0,column=2,sticky='w');ttk.Button(t,text='Réinitialiser index',command=self._fresh_build).grid(row=0,column=3,sticky='w',padx=6);self.idxtxt=self._logbox(t,1)
    def _explorer(self,t):
        t.columnconfigure(1,weight=1);ttk.Label(t,text='Registre').grid(row=0,column=0,sticky='w');ttk.Entry(t,textvariable=self.registry).grid(row=0,column=1,sticky='ew',padx=6);ttk.Button(t,text='…',command=self._choose_reg).grid(row=0,column=2)
        b=ttk.Frame(t);b.grid(row=1,column=0,columnspan=3,sticky='ew',pady=6);ttk.Button(b,text='Résoudre noms localement',command=self._resolve).pack(side='left');ttk.Button(b,text='Construire signatures N1',command=self._signature).pack(side='left',padx=6);ttk.Button(b,text='Charger catalogue',command=self._load_catalog).pack(side='left');ttk.Button(b,text='Trier popularité',command=self._sort).pack(side='left',padx=6);ttk.Button(b,text='Tout décocher',command=self._clear).pack(side='left')
        f=ttk.Frame(t);f.grid(row=2,column=0,columnspan=3,sticky='ew');ttk.Label(f,text='Filtre').pack(side='left');e=ttk.Entry(f,textvariable=self.filter,width=30);e.pack(side='left',padx=6);e.bind('<KeyRelease>',lambda _e:self._render());ttk.Label(f,text='Niveaux').pack(side='left',padx=(20,4));ttk.Spinbox(f,from_=2,to=15,textvariable=self.depth,width=5).pack(side='left');ttk.Button(f,text='Estimer exactement',command=self._estimate).pack(side='right');ttk.Button(f,text='Étendre',command=self._expand).pack(side='right',padx=6)
        cols=('sel','pid','fr','en','class','people','coverage','statements');self.tree=ttk.Treeview(t,columns=cols,show='headings',height=18)
        heads={'sel':'✓','pid':'PID','fr':'Relation FR','en':'Relation EN','class':'Classe','people':'Personnes','coverage':'Couverture %','statements':'Statements'}
        for c in cols:self.tree.heading(c,text=heads[c]);self.tree.column(c,width={'sel':35,'pid':70,'fr':220,'en':220,'class':130,'people':80,'coverage':90,'statements':90}[c])
        self.tree.grid(row=3,column=0,columnspan=3,sticky='nsew',pady=6);t.rowconfigure(3,weight=1);self.tree.bind('<Double-1>',self._toggle)
        self.explog=tk.Text(t,state='disabled',height=9,wrap='word');self.explog.grid(row=4,column=0,columnspan=3,sticky='ew')
    def _paths(self):
        return {
            'root':ROOT,
            'env':ROOT/'00_system/config/environment.json',
            'snap':ROOT/'20_ingest/snapshots/wikidata/latest.json',
            'dumpdir':ROOT/'10_sources/wikidata/dumps/current',
            'db':ROOT/'30_working/wikidata/wikidata.compact.sqlite',
            'state':ROOT/'20_ingest/checkpoints/wikidata-index-state.json',
            'qid':ROOT/'30_working/registry/qid-map.local.json',
            'n1':ROOT/'30_working/relation-maps/level_1',
            'expbase':ROOT/'30_working/relation-maps/expansions',
            'sel':ROOT/'30_working/relation-maps/selected-relations.json',
            'verified':ROOT/'20_ingest/manifests/wikidata-dump-verified.json'
        }
    def _refresh_paths(self):
        for p in self._paths().values():
            if isinstance(p,Path):
                (p if p.suffix=='' else p.parent).mkdir(parents=True,exist_ok=True)
    def _choose_reg(self):
        p=filedialog.askopenfilename(filetypes=[('JSON','*.json'),('All','*.*')]);
        if p:self.registry.set(p)
    def _open_ws(self):
        os.startfile(str(ROOT)) if os.name=='nt' else subprocess.Popen(['xdg-open',str(ROOT)])
    def _open_kristal_ingest(self):
        app=ROOT/'00_system/tools/encyklopedia-kristal-ingest/run_kristal_ingest.pyw'
        if not app.exists():
            messagebox.showinfo('Absent',str(app));return
        subprocess.Popen([sys.executable,str(app)],cwd=str(ROOT))
    def _append(self,box,s):box.configure(state='normal');box.insert('end',s);box.see('end');box.configure(state='disabled')
    def _run(self,cmd,box,on_done=None):
        if self.proc:messagebox.showwarning('En cours','Un processus est déjà actif.');return
        self.status.set('En cours…');self.stop.configure(state='normal');self._append(box,'\n$ '+' '.join(map(str,cmd))+'\n')
        self.proc=subprocess.Popen([str(x) for x in cmd],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1)
        def pump():
            assert self.proc and self.proc.stdout
            for line in self.proc.stdout:self.q.put((box,line))
            rc=self.proc.wait();self.q.put(('DONE',(rc,on_done)))
        threading.Thread(target=pump,daemon=True).start()
    def _drain(self):
        try:
            while True:
                a,b=self.q.get_nowait()
                if a=='DONE':
                    rc,cb=b;self.proc=None;self.stop.configure(state='disabled');self.status.set('Terminé' if rc==0 else f'Échec ({rc})');
                    if rc==0 and cb:cb()
                else:self._append(a,b)
        except queue.Empty:pass
        self.after(100,self._drain)
    def _stop(self):
        if self.proc:self.proc.terminate();self.status.set('Arrêt demandé — fichiers partiels conservés')
    def _diag(self):
        p=self._paths();cmd=['pwsh','-NoProfile','-ExecutionPolicy','Bypass','-File',DIAG,'-OutputPath',p['env']];self._run(cmd,self.envtxt,self._load_diag)
    def _load_diag(self):
        p=self._paths()['env'];
        if not p.exists():messagebox.showinfo('Diagnostic','Aucun environment.json encore.');return
        o=json.loads(p.read_text(encoding='utf-8-sig'));disks=o.get('logical_disks',[]);best=max(disks,key=lambda x:x.get('free_gib',0),default={})
        s=f"PowerShell {o.get('powershell',{}).get('version')} | RAM {o.get('memory',{}).get('total_gib')} GiB | CPU {o.get('cpu',{}).get('physical_cores')}c/{o.get('cpu',{}).get('logical_processors')}t\n"
        s+=f"Meilleur disque: {best.get('drive')} libre {best.get('free_gib')} GiB / {best.get('size_gib')} GiB\nRéseau dumps: {o.get('network_probe',{}).get('ok')}\n"
        tools=o.get('tools',{});s+='Outils: '+', '.join(k for k,v in tools.items() if v.get('found'))+'\n';self._append(self.envtxt,s)
    def _discover(self):
        p=self._paths();p['snap'].parent.mkdir(parents=True,exist_ok=True);cmd=[sys.executable,SCRIPTS/'discover_dump.py','--out',p['snap']];self._run(cmd,self.dumptxt,lambda:self._show_plan())
    def _show_plan(self):
        p=self._paths();s=json.loads(p['snap'].read_text());size=s.get('content_length',0);free=shutil.disk_usage(ROOT).free;need=size*3.2
        msg=f"Snapshot {s['dump_date']} — {s['human_size']}\nSHA1: {s.get('sha1')}\nLibre workspace: {free/1024**3:.1f} GiB\nSeuil prudent full JSON + index: {need/1024**3:.1f} GiB\n"
        msg+=('OK pour pipeline complet.\n' if free>=need else 'ATTENTION: espace sous le seuil prudent; choisir un autre disque ou ne pas lancer AUTO.\n');self._append(self.dumptxt,msg);self._append(self.envtxt,msg)
    def _download(self):
        p=self._paths();
        if not p['snap'].exists():messagebox.showinfo('Snapshot','Découvre d’abord le snapshot.');return
        cmd=[sys.executable,SCRIPTS/'download_dump.py','--snapshot',p['snap'],'--dest-dir',p['dumpdir']];self._run(cmd,self.dumptxt)
    def _dump_file(self):
        p=self._paths();
        if not p['snap'].exists():return None
        s=json.loads(p['snap'].read_text());return p['dumpdir']/s['filename']
    def _verify(self):
        p=self._paths();d=self._dump_file();
        if not d or not d.exists():messagebox.showinfo('Dump','Dump absent.');return
        self._run([sys.executable,SCRIPTS/'verify_dump.py','--snapshot',p['snap'],'--file',d,'--write-marker',p['verified']],self.dumptxt)
    def _build(self,fresh=False):
        p=self._paths();d=self._dump_file();
        if not d or not d.exists():messagebox.showinfo('Dump','Télécharge le dump d’abord.');return
        cmd=[sys.executable,SCRIPTS/'build_compact_index.py','--dump',d,'--db',p['db'],'--languages',self.languages.get(),'--state',p['state'],'--skip-sha1'];
        if fresh:cmd.append('--fresh')
        self._run(cmd,self.idxtxt)
    def _fresh_build(self):
        if messagebox.askyesno('Réinitialiser','Supprimer/reconstruire l’index local ?'):self._build(True)
    def _resolve(self):
        p=self._paths();self._run([sys.executable,SCRIPTS/'local_graph.py','resolve','--db',p['db'],'--registry',self.registry.get(),'--out',p['qid']],self.explog)
    def _signature(self):
        p=self._paths();self._run([sys.executable,SCRIPTS/'local_graph.py','signature','--db',p['db'],'--qid-map',p['qid'],'--out',p['n1']],self.explog,self._load_catalog)
    def _load_catalog(self):
        f=self._paths()['n1']/'relations.catalog.csv';
        if not f.exists():return
        with f.open(encoding='utf-8-sig',newline='') as h:self.rows=list(csv.DictReader(h));self._sort()
    def _sort(self):self.rows.sort(key=lambda r:int(r.get('people_with_relation') or 0),reverse=True);self._render()
    def _render(self):
        for x in self.tree.get_children():self.tree.delete(x)
        f=self.filter.get().casefold()
        for r in self.rows:
            hay=' '.join(str(r.get(k,'') or '') for k in ['property_id','label_fr','label_en','relation_class']).casefold()
            if f and f not in hay:continue
            pid=r['property_id'];self.tree.insert('', 'end', iid=pid, values=('☑' if pid in self.sel else '☐',pid,r.get('label_fr',''),r.get('label_en',''),r.get('relation_class',''),r.get('people_with_relation',''),r.get('coverage_pct',''),r.get('total_statements','')))
    def _toggle(self,_e=None):
        it=self.tree.focus();
        if not it:return
        if it in self.sel:self.sel.remove(it)
        else:self.sel.add(it)
        self._render()
    def _clear(self):self.sel.clear();self._render()
    def _write_sel(self):
        p=self._paths();p['sel'].write_text(json.dumps({'selected_properties':sorted(self.sel)},indent=2)+"\n",encoding='utf-8')
    def _estimate(self):
        if not self.sel:messagebox.showinfo('Relations','Coche au moins une relation.');return
        self._write_sel();p=self._paths();self._run([sys.executable,SCRIPTS/'local_graph.py','estimate','--db',p['db'],'--qid-map',p['qid'],'--properties-file',p['sel'],'--levels',self.depth.get()],self.explog)
    def _expand(self):
        if not self.sel:messagebox.showinfo('Relations','Coche au moins une relation.');return
        self._write_sel();p=self._paths();self._run([sys.executable,SCRIPTS/'local_graph.py','expand','--db',p['db'],'--qid-map',p['qid'],'--properties-file',p['sel'],'--levels',self.depth.get(),'--out',p['expbase']/__import__('datetime').datetime.now().strftime('exp_%Y%m%d_%H%M%S')],self.explog)
    def _auto(self):
        p=self._paths();cmd=[sys.executable,SCRIPTS/'auto_pipeline.py','--root',ROOT,'--languages',self.languages.get()];self._run(cmd,self.envtxt)

if __name__=='__main__':App().mainloop()
