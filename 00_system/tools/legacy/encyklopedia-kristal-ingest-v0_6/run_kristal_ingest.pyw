from __future__ import annotations
import json, os, queue, sqlite3, subprocess, sys, threading, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

BASE=Path(__file__).resolve().parent

def find_root():
    for p in [BASE,*BASE.parents]:
        if (p/'MANIFEST.json').exists() and (p/'10_sources').exists(): return p
    return BASE.parents[2]
ROOT=find_root(); SCRIPTS=BASE/'scripts'

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('EncyKlopedia — People / Works / Currents → Kristal handoff v0.6'); self.geometry('1180x820'); self.minsize(960,680)
        self.proc=None; self.q=queue.Queue(); self.status=tk.StringVar(value='Prêt'); self.kristal=tk.StringVar(value=''); self.partial=tk.BooleanVar(value=False); self.med=tk.BooleanVar(value=True)
        self._ui(); self.after(100,self._drain); self._preflight()
    def _ui(self):
        root=ttk.Frame(self,padding=10); root.pack(fill='both',expand=True); root.columnconfigure(0,weight=1); root.rowconfigure(2,weight=1)
        bar=ttk.Frame(root); bar.grid(row=0,column=0,sticky='ew')
        ttk.Label(bar,text='Racine:').pack(side='left'); ttk.Label(bar,text=str(ROOT)).pack(side='left',padx=6)
        ttk.Button(bar,text='Ouvrir racine',command=lambda:self._open(ROOT)).pack(side='left',padx=4)
        ttk.Button(bar,text='Pipeline complet',command=self._full).pack(side='right')
        cfg=ttk.LabelFrame(root,text='Kristal / options',padding=8); cfg.grid(row=1,column=0,sticky='ew',pady=8); cfg.columnconfigure(1,weight=1)
        ttk.Label(cfg,text='Kristal root (optionnel)').grid(row=0,column=0,sticky='w'); ttk.Entry(cfg,textvariable=self.kristal).grid(row=0,column=1,sticky='ew',padx=6); ttk.Button(cfg,text='…',command=self._choose_k).grid(row=0,column=2)
        ttk.Checkbutton(cfg,text='Autoriser index Wikidata partiel',variable=self.partial).grid(row=1,column=0,sticky='w',pady=(5,0)); ttk.Checkbutton(cfg,text='Publier candidats UCKK Médiathèque',variable=self.med).grid(row=1,column=1,sticky='w',pady=(5,0))
        self.nb=ttk.Notebook(root); self.nb.grid(row=2,column=0,sticky='nsew')
        self.t1=ttk.Frame(self.nb,padding=10); self.t2=ttk.Frame(self.nb,padding=10); self.t3=ttk.Frame(self.nb,padding=10)
        self.nb.add(self.t1,text='1 · Préflight & commandes'); self.nb.add(self.t2,text='2 · Exécution'); self.nb.add(self.t3,text='3 · Résultats')
        self._preflight_ui(); self._run_ui(); self._results_ui()
        bot=ttk.Frame(root); bot.grid(row=3,column=0,sticky='ew',pady=(8,0)); ttk.Label(bot,textvariable=self.status).pack(side='left'); self.stop=ttk.Button(bot,text='Arrêter',command=self._stop,state='disabled'); self.stop.pack(side='right')
    def _preflight_ui(self):
        t=self.t1; t.columnconfigure(0,weight=1); t.rowconfigure(2,weight=1)
        b=ttk.Frame(t); b.grid(row=0,column=0,sticky='ew')
        ttk.Button(b,text='Préflight',command=self._preflight).pack(side='left'); ttk.Button(b,text='Résoudre les noms',command=self._resolve).pack(side='left',padx=5); ttk.Button(b,text='Ouvrir config relations',command=lambda:self._open(BASE/'config/harvest.default.json')).pack(side='left')
        ttk.Label(t,text='Plan: personnes → œuvres/documents (P50/P800) → courants/idéologies (P135/P1142) + domaines P101 + influence P737 → snapshot immuable → handoff Da\'at.').grid(row=1,column=0,sticky='w',pady=8)
        self.pre=tk.Text(t,state='disabled',wrap='word'); self.pre.grid(row=2,column=0,sticky='nsew')
    def _run_ui(self):
        t=self.t2; t.columnconfigure(0,weight=1); t.rowconfigure(1,weight=1)
        b=ttk.Frame(t); b.grid(row=0,column=0,sticky='ew')
        ttk.Button(b,text='Pipeline complet',command=self._full).pack(side='left')
        ttk.Button(b,text='Ouvrir dernier working',command=self._open_latest_working).pack(side='left',padx=5)
        ttk.Button(b,text='Ouvrir dernier snapshot',command=self._open_latest_snapshot).pack(side='left')
        ttk.Button(b,text='Ouvrir dernier handoff',command=self._open_latest_handoff).pack(side='left',padx=5)
        self.log=tk.Text(t,state='disabled',wrap='word'); self.log.grid(row=1,column=0,sticky='nsew',pady=(8,0))
    def _results_ui(self):
        t=self.t3; t.columnconfigure(0,weight=1); t.rowconfigure(1,weight=1)
        b=ttk.Frame(t); b.grid(row=0,column=0,sticky='ew'); ttk.Button(b,text='Rafraîchir',command=self._results).pack(side='left'); ttk.Button(b,text='50_mediatheque',command=lambda:self._open(ROOT/'50_mediatheque')).pack(side='left',padx=5); ttk.Button(b,text='20_ingest',command=lambda:self._open(ROOT/'20_ingest')).pack(side='left')
        self.restxt=tk.Text(t,state='disabled',wrap='word'); self.restxt.grid(row=1,column=0,sticky='nsew',pady=(8,0))
    def _append(self,box,s): box.configure(state='normal'); box.insert('end',s); box.see('end'); box.configure(state='disabled')
    def _set(self,box,s): box.configure(state='normal'); box.delete('1.0','end'); box.insert('1.0',s); box.configure(state='disabled')
    def _choose_k(self):
        p=filedialog.askdirectory(title='Racine du dépôt Kristal v5 piné');
        if p:self.kristal.set(p)
    def _open(self,p):
        p=Path(p)
        if not p.exists(): messagebox.showinfo('Absent',str(p)); return
        if os.name=='nt': os.startfile(str(p))
        else: subprocess.Popen(['xdg-open',str(p)])
    def _run(self,cmd,on_done=None):
        if self.proc: messagebox.showwarning('En cours','Un processus est déjà actif.'); return
        self.nb.select(self.t2); self.status.set('En cours…'); self.stop.configure(state='normal'); self._append(self.log,'\n$ '+' '.join(map(str,cmd))+'\n')
        self.proc=subprocess.Popen([str(x) for x in cmd],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1)
        def pump():
            assert self.proc and self.proc.stdout
            for line in self.proc.stdout:self.q.put(('line',line))
            rc=self.proc.wait(); self.q.put(('done',(rc,on_done)))
        threading.Thread(target=pump,daemon=True).start()
    def _drain(self):
        try:
            while True:
                kind,val=self.q.get_nowait()
                if kind=='line': self._append(self.log,val)
                else:
                    rc,cb=val; self.proc=None; self.stop.configure(state='disabled'); self.status.set('Terminé' if rc==0 else f'Échec ({rc})')
                    if rc==0 and cb: cb()
        except queue.Empty: pass
        self.after(100,self._drain)
    def _stop(self):
        if self.proc:self.proc.terminate(); self.status.set('Arrêt demandé')
    def _paths(self):
        return {'db':ROOT/'30_working/wikidata/wikidata.compact.sqlite','registry':ROOT/'10_sources/seeds/active/intellectual-registry/intellectuals.seed.json','qid':ROOT/'30_working/registry/qid-map.local.json'}
    def _preflight(self):
        p=self._paths(); lines=[]
        for k,v in p.items(): lines.append(f"{k:10} {'OK' if v.exists() else 'ABSENT'}  {v}")
        if p['db'].exists():
            try:
                c=sqlite3.connect(f"file:{p['db'].resolve().as_posix()}?mode=ro",uri=True); m=dict(c.execute('SELECT key,value FROM meta').fetchall()); c.close(); lines.append(f"\nindex complete={m.get('complete')} processed={m.get('processed_entities')} dump={m.get('dump_file')}")
            except Exception as e: lines.append(f"\nIndex error: {e}")
        lines.append('\n40_kristal reste protégé: ce tool prépare un handoff Da\'at; il ne fabrique pas de Reference Exchange.')
        self._set(self.pre,'\n'.join(lines)); self._results()
    def _resolve(self): self._run([sys.executable,SCRIPTS/'01_resolve_people.py','--root',ROOT],self._preflight)
    def _full(self):
        cmd=[sys.executable,SCRIPTS/'run_pipeline.py','--root',ROOT]
        if self.kristal.get().strip():cmd += ['--kristal-root',self.kristal.get().strip()]
        if self.partial.get():cmd.append('--allow-partial-db')
        if not self.med.get():cmd.append('--skip-mediatheque')
        self._run(cmd,lambda:(self._results(),self.nb.select(self.t3)))
    def _latest(self,path):
        try:return json.loads(Path(path).read_text(encoding='utf-8-sig'))
        except:return {}
    def _open_latest_working(self):
        o=self._latest(ROOT/'30_working/encyklopedia-harvest/latest.json'); self._open(ROOT/o.get('path','__missing__'))
    def _open_latest_snapshot(self):
        o=self._latest(ROOT/'20_ingest/snapshots/encyklopedia/latest.json'); self._open(ROOT/o.get('path','__missing__'))
    def _open_latest_handoff(self):
        o=self._latest(ROOT/'20_ingest/handoffs/kristal/latest.json'); self._open(ROOT/o.get('path','__missing__'))
    def _results(self):
        w=self._latest(ROOT/'30_working/encyklopedia-harvest/latest.json'); s=self._latest(ROOT/'20_ingest/snapshots/encyklopedia/latest.json'); h=self._latest(ROOT/'20_ingest/handoffs/kristal/latest.json')
        lines=['Derniers artefacts:']
        lines.append('working : '+json.dumps(w,ensure_ascii=False,indent=2)); lines.append('\nsnapshot : '+json.dumps(s,ensure_ascii=False,indent=2)); lines.append('\nhandoff : '+json.dumps(h,ensure_ascii=False,indent=2))
        if w.get('path'):
            d=ROOT/w['path']
            for fn in ['people.summary.json','works.summary.json','intellectual-context.summary.json']:
                p=d/fn
                if p.exists(): lines.append(f"\n{fn}:\n"+p.read_text(encoding='utf-8-sig'))
        self._set(self.restxt,'\n'.join(lines))

if __name__=='__main__': App().mainloop()
