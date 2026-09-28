from __future__ import annotations
import json, os, queue, subprocess, sys, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

HERE=Path(__file__).resolve().parent; SCRIPTS=HERE/'scripts'
def find_root():
    for c in [HERE,*HERE.parents]:
        if (c/'MANIFEST.json').exists() and (c/'30_working').exists():return c
    return HERE
ROOT=find_root()

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('EncyKlopedia — Scope → Evidence → Da\'at v0.11'); self.geometry('1180x800'); self.proc=None; self.q=queue.Queue(); self.status=tk.StringVar(value='Prêt')
        self.scope_cath=tk.BooleanVar(value=True); self.scope_int=tk.BooleanVar(value=False); self.backend=tk.StringVar(value='auto'); self.threads=tk.StringVar(value='0'); self.query_index=tk.BooleanVar(value=False); self.cache_vault=tk.BooleanVar(value=False); self.allow_full_scan=tk.BooleanVar(value=False); self.kristal=tk.StringVar(value=''); self.ik=tk.StringVar(value=str(ROOT/'00_system/integrations/Interaction-Kernel'))
        self._ui(); self.after(100,self._drain); self._refresh()
    def _ui(self):
        top=ttk.Frame(self,padding=8); top.pack(fill='x'); ttk.Label(top,text=f'Root: {ROOT}').pack(side='left'); ttk.Button(top,text='Ouvrir root',command=lambda:self._open(ROOT)).pack(side='right'); ttk.Button(top,text='Actualiser statut',command=self._refresh).pack(side='right',padx=6)
        scope=ttk.LabelFrame(self,text='Scopes',padding=8); scope.pack(fill='x',padx=8,pady=4)
        ttk.Checkbutton(scope,text='Catholic intellectual pilot',variable=self.scope_cath).grid(row=0,column=0,sticky='w'); ttk.Checkbutton(scope,text='Historical intellectuals',variable=self.scope_int).grid(row=0,column=1,sticky='w',padx=18)
        ttk.Label(scope,text='Discovery').grid(row=0,column=2,sticky='e'); ttk.Combobox(scope,textvariable=self.backend,values=['auto','index','fast','raw'],state='readonly',width=9).grid(row=0,column=3,sticky='w',padx=5)
        ttk.Checkbutton(scope,text='SQLite projet optionnel',variable=self.query_index).grid(row=0,column=4,sticky='w',padx=12); ttk.Checkbutton(scope,text='Cache vault optionnel',variable=self.cache_vault).grid(row=0,column=5,sticky='w'); ttk.Checkbutton(scope,text='Autoriser full scan',variable=self.allow_full_scan).grid(row=1,column=5,sticky='w'); ttk.Label(scope,text='Threads (0=auto)').grid(row=0,column=6,padx=(14,2)); ttk.Entry(scope,textvariable=self.threads,width=5).grid(row=0,column=7)
        env=ttk.LabelFrame(self,text='Intégration optionnelle',padding=8); env.pack(fill='x',padx=8,pady=4); env.columnconfigure(1,weight=1); env.columnconfigure(4,weight=1)
        ttk.Label(env,text='Kristal root').grid(row=0,column=0); ttk.Entry(env,textvariable=self.kristal).grid(row=0,column=1,sticky='ew',padx=5); ttk.Button(env,text='…',command=lambda:self._pick(self.kristal)).grid(row=0,column=2)
        ttk.Label(env,text='IK root').grid(row=0,column=3,padx=(15,0)); ttk.Entry(env,textvariable=self.ik).grid(row=0,column=4,sticky='ew',padx=5); ttk.Button(env,text='…',command=lambda:self._pick(self.ik)).grid(row=0,column=5)
        ttk.Label(env,text="IK snapshot fourni: contrats/runtime/TCK sont embarqués comme référence locale; l'upstream reste l'autorité.").grid(row=1,column=0,columnspan=6,sticky='w',pady=(5,0))
        perf=ttk.LabelFrame(self,text='Moteur performance',padding=8); perf.pack(fill='x',padx=8,pady=4)
        ttk.Button(perf,text='État moteur',command=lambda:self._run_perf('fast_status.py')).pack(side='left')
        ttk.Button(perf,text='Installer orjson + rapidgzip',command=lambda:self._run_perf('install_fast_deps.py')).pack(side='left',padx=5)
        ttk.Button(perf,text='Benchmark dump',command=lambda:self._run_perf('benchmark_dump.py')).pack(side='left',padx=5)
        ttk.Button(perf,text='Préparer Fast Access',command=lambda:self._run_perf('build_fast_access.py')).pack(side='left',padx=5)
        actions=ttk.LabelFrame(self,text='Pipeline optimisé',padding=8); actions.pack(fill='x',padx=8,pady=4)
        ttk.Button(actions,text='1. Résoudre + découvrir + geler',command=lambda:self._run_pipeline('freeze')).pack(side='left')
        ttk.Button(actions,text='Estimer',command=self._estimate).pack(side='left',padx=6)
        ttk.Button(actions,text='2. Evidence → référents/médias → Da\'at',command=lambda:self._run_pipeline('handoff',from_stage='evidence')).pack(side='left',padx=6)
        ttk.Button(actions,text='TOUT',command=lambda:self._run_pipeline('handoff')).pack(side='left',padx=6)
        ttk.Button(actions,text='Run si inputs changés',command=self._smart_run).pack(side='left',padx=6)
        self.stop=ttk.Button(actions,text='Arrêter',command=self._stop,state='disabled'); self.stop.pack(side='right')
        mid=ttk.Panedwindow(self,orient='horizontal'); mid.pack(fill='both',expand=True,padx=8,pady=4); lf=ttk.Frame(mid); rf=ttk.Frame(mid); mid.add(lf,weight=1); mid.add(rf,weight=2)
        ttk.Label(lf,text='Statut').pack(anchor='w'); self.stat=tk.Text(lf,wrap='word',height=28); self.stat.pack(fill='both',expand=True)
        ttk.Label(rf,text='Journal').pack(anchor='w'); self.log=tk.Text(rf,wrap='none',height=28); self.log.pack(fill='both',expand=True)
        bot=ttk.Frame(self,padding=8); bot.pack(fill='x'); ttk.Label(bot,textvariable=self.status).pack(side='left'); ttk.Button(bot,text='Scopes',command=lambda:self._open(ROOT/'30_working/scopes')).pack(side='right'); ttk.Button(bot,text='Evidence',command=lambda:self._open(ROOT/'20_ingest/scope-snapshots')).pack(side='right',padx=6); ttk.Button(bot,text='Handoffs',command=lambda:self._open(ROOT/'20_ingest/daat-handoff')).pack(side='right',padx=6); ttk.Button(bot,text='Référents',command=lambda:self._open(ROOT/'20_ingest/referent-registries')).pack(side='right',padx=6)
    def _pick(self,var):
        p=filedialog.askdirectory()
        if p:var.set(p)
    def _open(self,p):
        p=Path(p); p.mkdir(parents=True,exist_ok=True)
        if os.name=='nt':os.startfile(p)
        else:subprocess.Popen(['xdg-open',str(p)])
    def _scopes(self):
        out=[]
        if self.scope_cath.get():out.append('catholic-pilot')
        if self.scope_int.get():out.append('intellectuals')
        if not out:messagebox.showinfo('Scope','Sélectionne au moins un scope.')
        return out
    def _cmd(self,script,*args):return [sys.executable,SCRIPTS/script,'--root',ROOT,*args]
    def _augment(self,cmd):
        if self.query_index.get():cmd.append('--build-query-index')
        if self.cache_vault.get():cmd.append('--cache-vault')
        if self.allow_full_scan.get():cmd.append('--allow-full-scan')
        if self.kristal.get().strip():cmd += ['--kristal-root',self.kristal.get().strip()]
        if self.ik.get().strip():cmd += ['--ik-root',self.ik.get().strip()]
        try:
            t=int(self.threads.get().strip() or '0')
            if t>0:cmd += ['--threads',str(t)]
        except ValueError:pass
        return cmd
    def _run(self,cmd):
        if self.proc:messagebox.showwarning('En cours','Un processus est déjà actif.');return
        self.log.insert('end','\n$ '+' '.join(map(str,cmd))+'\n'); self.log.see('end'); self.status.set('En cours…'); self.stop.configure(state='normal')
        self.proc=subprocess.Popen([str(x) for x in cmd],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',bufsize=1)
        def pump():
            assert self.proc and self.proc.stdout
            for line in self.proc.stdout:self.q.put(('line',line))
            rc=self.proc.wait(); self.q.put(('done',rc))
        threading.Thread(target=pump,daemon=True).start()
    def _drain(self):
        try:
            while True:
                typ,val=self.q.get_nowait()
                if typ=='line':self.log.insert('end',val); self.log.see('end')
                else:self.proc=None; self.stop.configure(state='disabled'); self.status.set('Terminé' if val==0 else f'Échec ({val})'); self._refresh()
        except queue.Empty:pass
        self.after(100,self._drain)
    def _stop(self):
        if self.proc:self.proc.terminate(); self.status.set('Arrêt demandé')
    def _run_perf(self,script):
        perf=ROOT/'00_system/tools/performance/scripts'/script
        cmd=[sys.executable,perf,'--root',ROOT]
        try:
            t=int(self.threads.get().strip() or '0')
            if t>0 and script in {'benchmark_dump.py','build_fast_access.py'}:cmd += ['--threads',str(t)]
        except ValueError:pass
        self._run(cmd)
    def _estimate(self):
        scopes=self._scopes()
        if not scopes:return
        cmd=self._cmd('estimate_selected.py')
        for s in scopes:cmd += ['--scope',s]
        self._run(cmd)
    def _run_pipeline(self,through,from_stage='resolve'):
        scopes=self._scopes()
        if not scopes:return
        cmd=self._cmd('run_scope_pipeline.py','--through',through,'--from-stage',from_stage,'--discovery-backend',self.backend.get())
        for s in scopes:cmd += ['--scope',s]
        self._run(self._augment(cmd))
    def _smart_run(self):
        scopes=self._scopes()
        if not scopes:return
        cmd=self._cmd('watch_then_run.py','--through','handoff','--discovery-backend',self.backend.get())
        for s in scopes:cmd += ['--scope',s]
        self._run(self._augment(cmd))
    def _refresh(self):
        try:r=subprocess.run(self._cmd('09_status.py'),capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=20); self.stat.delete('1.0','end'); self.stat.insert('end',r.stdout or r.stderr)
        except Exception as e:self.stat.delete('1.0','end'); self.stat.insert('end',str(e))

if __name__=='__main__':App().mainloop()
