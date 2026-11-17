# -*- coding: utf-8 -*-
"""Interface locale du pilote UNESCO GF, sans publication."""
from __future__ import annotations
from pathlib import Path
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pilot import run_pilot, find_latest_run, DEFAULT_GF, DEFAULT_WORDBENCH, DEFAULT_ORCHESTRATOR

FACTORY=Path(__file__).resolve().parents[2]

class UI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('UNESCO / Kristal / Spek / SemantiK / Wordbench — pilote privé')
        self.geometry('1050x680')
        self.q=queue.Queue()
        self.cancel=threading.Event()
        self.running=False
        self.fields={
            'Dossier RUN (vide = dernier)': '',
            'Fabrique':str(FACTORY),
            'SemantiK':r'C:\mycode\SemantiK_Architect\SemantiK_Architect',
            'Wordbench':str(DEFAULT_WORDBENCH),
            'Orchestrateur':str(DEFAULT_ORCHESTRATOR),
            'Compilateur gf.exe':str(DEFAULT_GF),
            'Concept':'concept10',
            'Sortie ZIP':str(Path.home()/'Downloads'),
        }
        frm=ttk.Frame(self,padding=12);frm.pack(fill='x')
        ttk.Label(frm,text='Pilote privé FR / EN — aucune publication ni activation',font=('Segoe UI',14,'bold')).grid(row=0,column=0,columnspan=3,sticky='w',pady=(0,9))
        self.vars={}
        for i,(name,value) in enumerate(self.fields.items(),1):
            ttk.Label(frm,text=name).grid(row=i,column=0,sticky='w',pady=3)
            v=tk.StringVar(value=value);self.vars[name]=v
            ttk.Entry(frm,textvariable=v,width=85).grid(row=i,column=1,sticky='ew',padx=5)
            if name not in {'Concept','Compilateur gf.exe'}:
                ttk.Button(frm,text='…',width=4,command=lambda n=name:self.choose(n)).grid(row=i,column=2)
        frm.columnconfigure(1,weight=1)
        buttons=ttk.Frame(self,padding=(12,6));buttons.pack(fill='x')
        self.launch=ttk.Button(buttons,text='Tester concept10 FR + EN',command=self.start)
        self.launch.pack(side='left')
        self.cancel_btn=ttk.Button(buttons,text='Annuler après étape',command=self.stop,state='disabled')
        self.cancel_btn.pack(side='left',padx=8)
        ttk.Button(buttons,text='Ouvrir Téléchargements',command=self.open_output).pack(side='left')
        self.status=tk.StringVar(value='Prêt. Vérifie les chemins. Les résultats restent privés.')
        ttk.Label(self,textvariable=self.status,padding=(12,3)).pack(anchor='w')
        self.text=tk.Text(self,wrap='word',bg='#17212b',fg='#d4eaff',font=('Consolas',10))
        self.text.pack(fill='both',expand=True,padx=12,pady=8)
        self.after(90,self.poll)

    def append(self,s):
        self.text.insert('end',str(s)+'\n');self.text.see('end')

    def choose(self,name):
        if self.running:return
        folder=filedialog.askdirectory(title=name)
        if folder:self.vars[name].set(folder)

    def open_output(self):
        p=Path(self.vars['Sortie ZIP'].get()).expanduser()
        if p.is_dir():
            if os.name=='nt':os.startfile(str(p))
        else:messagebox.showwarning('Sortie','Dossier absent')

    def stop(self):
        self.cancel.set();self.append('Annulation demandée : prise en compte entre deux opérations (GF borné à 90 s).')

    def start(self):
        if self.running:return
        self.running=True;self.cancel.clear()
        self.launch.configure(state='disabled');self.cancel_btn.configure(state='normal')
        values={k:v.get().strip().strip('"') for k,v in self.vars.items()}
        self.status.set('Pilote en cours, rapports dans Téléchargements...')
        threading.Thread(target=self.worker,args=(values,),daemon=True).start()

    def worker(self,v):
        try:
            factory=Path(v['Fabrique'])
            kristal=factory.parent
            run=Path(v['Dossier RUN (vide = dernier)']) if v['Dossier RUN (vide = dernier)'] else find_latest_run(kristal)
            zip_path=run_pilot(run, factory,Path(v['SemantiK']),Path(v['Sortie ZIP']),
                               cid=v['Concept'],langs=('fr','en'),gf_executable=v['Compilateur gf.exe'],
                               wordbench=Path(v['Wordbench']),orchestrator=Path(v['Orchestrateur']),
                               callback=lambda x:self.q.put(('log',x)),is_cancelled=self.cancel.is_set)
            result=json.loads(zip_path.with_suffix('').joinpath('report.json').read_text(encoding='utf-8'))
            self.q.put(('done',f"{result['status']}\nZIP: {zip_path}"))
        except Exception as exc:
            self.q.put(('done',f'ÉCHEC avant ZIP : {type(exc).__name__}: {exc}'))

    def poll(self):
        while True:
            try:kind,msg=self.q.get_nowait()
            except queue.Empty:break
            if kind=='log':self.append(msg)
            else:
                self.append(msg);self.status.set(msg.splitlines()[0]);self.running=False
                self.launch.configure(state='normal');self.cancel_btn.configure(state='disabled')
        self.after(90,self.poll)

if __name__=='__main__':UI().mainloop()
