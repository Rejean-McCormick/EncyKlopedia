# -*- coding: utf-8 -*-
"""Interface Windows autonome: pas de console obligatoire."""
from __future__ import annotations
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from pilot import run_pilot, find_latest_run

KRISTAL_DEFAULT = r'C:\mycode\Kristal'
SA_DEFAULT = r'C:\mycode\SemantiK_Architect\SemantiK_Architect'

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Kristal UNESCO — Pilote Spek / SemantiK / GF')
        self.minsize(940, 630)
        self.geometry('1050x760')
        self.configure(bg='#f2f4f8')
        self.q = queue.Queue()
        self.cancel_flag = threading.Event()
        self.busy = False
        self.last_zip = None
        self.vars = {
          'Kristal':tk.StringVar(value=KRISTAL_DEFAULT),
          'SemantiK':tk.StringVar(value=SA_DEFAULT),
          'RUN':tk.StringVar(value=''),
          'GF.exe (facultatif)':tk.StringVar(value=''),
          'Concept':tk.StringVar(value='concept10'),
          'Sortie':tk.StringVar(value=str(Path.home()/'Downloads')),
        }
        self.both = tk.BooleanVar(value=True)
        self._build()
        self.after(100, self.poll)
    def _build(self):
        h=ttk.Frame(self,padding=16);h.pack(fill='x')
        ttk.Label(h,text='Kristal · UNESCO · Spek · SemantiK · GF',font=('Segoe UI',19,'bold')).pack(anchor='w')
        ttk.Label(h,text='Pilote privé et non canonique. Aucun fichier du projet modifié; publication désactivée.',
                  foreground='#525d70').pack(anchor='w',pady=(3,13))
        p=ttk.Frame(h);p.pack(fill='x')
        for row,name in enumerate(self.vars):
            ttk.Label(p,text=name,width=22).grid(row=row,column=0,sticky='w',pady=5)
            entry=ttk.Entry(p,textvariable=self.vars[name],width=75)
            entry.grid(row=row,column=1,sticky='ew',padx=(4,5),pady=5)
            ttk.Button(p,text='…',width=4,command=lambda n=name:self.choose(n)).grid(row=row,column=2,pady=5)
        p.columnconfigure(1,weight=1)
        options=ttk.Frame(h);options.pack(fill='x',pady=8)
        ttk.Checkbutton(options,text='Tester aussi l’anglais (français toujours inclus)',variable=self.both).pack(side='left')
        ttk.Button(options,text='Détecter le dernier RUN',command=self.detect_run).pack(side='right')
        actions=ttk.Frame(h);actions.pack(fill='x',pady=(8,8))
        self.launch=ttk.Button(actions,text='Préparer et tester le pilote',command=self.start)
        self.launch.pack(side='left')
        self.cancel=ttk.Button(actions,text='Annuler',command=self.stop,state='disabled')
        self.cancel.pack(side='left',padx=8)
        ttk.Button(actions,text='Ouvrir les résultats',command=self.open_output).pack(side='left',padx=7)
        self.status=tk.StringVar(value='Prêt. Compilation et réalisation GF seulement si gf.exe est disponible.')
        ttk.Label(h,textvariable=self.status,foreground='#283c6b').pack(anchor='w',pady=(5,0))
        frame=ttk.Frame(self,padding=(16,0,16,14));frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Journal en direct',font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(10,6))
        sub=ttk.Frame(frame);sub.pack(fill='both',expand=True)
        self.log=tk.Text(sub,wrap='word',font=('Consolas',10),state='disabled',bg='#111827',fg='#d1e9ff')
        scr=ttk.Scrollbar(sub,orient='vertical',command=self.log.yview)
        self.log.configure(yscrollcommand=scr.set)
        self.log.pack(side='left',fill='both',expand=True);scr.pack(side='right',fill='y')
        self.append('À savoir : « GF compilateur absent » est un résultat honnête, pas une réussite fictive.\n')
    def choose(self,name):
        if self.busy:return
        if name == 'GF.exe (facultatif)':
            x=filedialog.askopenfilename(title='Choisir gf.exe',filetypes=[('Exécutable GF','*.exe'),('Tous les fichiers','*.*')])
        elif name == 'Concept':
            return
        else:
            x=filedialog.askdirectory(title='Choisir '+name)
        if x:self.vars[name].set(x)
    def append(self,msg):
        self.log.configure(state='normal')
        self.log.insert('end',msg+'\n' if not msg.endswith('\n') else msg)
        self.log.see('end');self.log.configure(state='disabled')
    def detect_run(self):
        try:
            r=find_latest_run(Path(self.vars['Kristal'].get().strip()))
            self.vars['RUN'].set(str(r));self.append('RUN détecté : '+str(r))
        except Exception as exc:messagebox.showwarning('RUN introuvable',str(exc))
    def start(self):
        if self.busy:return
        self.busy=True;self.cancel_flag.clear();self.launch.configure(state='disabled');self.cancel.configure(state='normal')
        self.status.set('Travail en cours — fenêtre toujours utilisable')
        v={key:var.get().strip().strip('"') for key,var in self.vars.items()}
        langs=('fr','en') if self.both.get() else ('fr',)
        def worker():
            try:
                k=Path(v['Kristal']);s=Path(v['SemantiK'])
                if not (s/'src'/'semantik_architect').is_dir() and (s/'SemantiK_Architect'/'src'/'semantik_architect').is_dir():
                    s=s/'SemantiK_Architect'
                run=Path(v['RUN']) if v['RUN'] else find_latest_run(k)
                archive=run_pilot(run,k/'Kristal_UNESCO_Factory',s,Path(v['Sortie']),
                        cid=v['Concept'],langs=langs,gf_executable=v['GF.exe (facultatif)'],
                        callback=lambda m:self.q.put(('log',m)),
                        is_cancelled=self.cancel_flag.is_set)
                report=json.loads((archive.with_suffix('')/'report.json').read_text(encoding='utf-8'))
                self.q.put(('done',(str(archive),report['status'])))
            except Exception as exc:
                self.q.put(('fatal',str(exc)))
        threading.Thread(target=worker,daemon=True).start()
    def stop(self):
        if self.busy:
            self.cancel_flag.set()
            self.append('Annulation demandée (opération GF en cours bornée à 45 secondes).')
    def poll(self):
        try:
            while True:
                kind,value=self.q.get_nowait()
                if kind=='log':self.append(value)
                elif kind=='done':
                    self.last_zip=value[0]
                    self.status.set('Terminé : '+value[1])
                    self.append('ZIP : '+value[0])
                    self._end()
                    messagebox.showinfo('Résultats',f'Statut: {value[1]}\n\nArchive:\n{value[0]}\n\nVoir report.json pour le détail.')
                elif kind=='fatal':
                    self.append('ERREUR : '+value)
                    self.status.set('Erreur avant ou pendant la création des résultats')
                    self._end()
                    messagebox.showerror('Erreur',value)
        except queue.Empty:
            pass
        self.after(100,self.poll)
    def _end(self):
        self.busy=False;self.launch.configure(state='normal');self.cancel.configure(state='disabled')
    def open_output(self):
        directory=Path(self.vars['Sortie'].get().strip())
        if not directory.exists():return messagebox.showinfo('Dossier',str(directory)+' n’existe pas encore.')
        if sys.platform=='win32':
            import os
            os.startfile(str(directory))
        else:
            subprocess.Popen(['xdg-open',str(directory)])

if __name__=='__main__':
    try: Application().mainloop()
    except Exception as exc:
        try: messagebox.showerror('Erreur au démarrage',str(exc))
        except Exception: pass
