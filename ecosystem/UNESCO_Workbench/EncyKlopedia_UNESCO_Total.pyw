"""Windows local-only control panel for UNESCO branch research. No publication control."""
from __future__ import annotations
import importlib.util
import json
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

# User's consolidated Windows repository; derive a portable fallback for tests.
HARDCODED_HOME = Path(r'C:\mycode\EncyKlopedia')
LOCAL_HOME = Path(__file__).resolve().parent.parent
HOME = HARDCODED_HOME if (HARDCODED_HOME/'UNESCO_Workbench').is_dir() else LOCAL_HOME
WB = HOME/'UNESCO_Workbench'
SCRIPT = WB/'pipelines/unesco_total.py'
OUTPUT = WB/'output/private/educational-policy-en/research-view.json'
READER = HOME/'EncyKlopedia/Start_UNESCO_Research.cmd'

spec = importlib.util.spec_from_file_location('unesco_total', SCRIPT)
if not spec or not spec.loader:
    raise RuntimeError('Missing UNESCO integration script')
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)

class Panel:
    def __init__(self, window:tk.Tk):
        self.win=window
        window.title('EncyKlopedia × UNESCO — Version intégrée EN (PRIVATE)')
        window.geometry('930x620')
        window.minsize(740,480)
        header=ttk.Frame(window,padding=18);header.pack(fill='x')
        ttk.Label(header,text='UNESCO · Educational policy · English-first',font=('Segoe UI',17,'bold')).pack(anchor='w')
        ttk.Label(header,text='41 concepts / v11 provisoire / 2025 RDF comparatif / 19 propositions · aucune publication',wraplength=800).pack(anchor='w',pady=(5,0))
        ttk.Label(header,text=f'Racine du projet : {HOME}',wraplength=850).pack(anchor='w',pady=(8,0))
        actions=ttk.Frame(window,padding=(18,4));actions.pack(fill='x')
        self.buttons=[]
        for label,action in [('1. Analyser les entrées',self.preflight),('2. Construire la vue privée',self.build),
                             ('3. Vérifier les empreintes',self.check),('4. Ouvrir EncyKlopedia',self.open_reader)]:
            b=ttk.Button(actions,text=label,command=action);b.pack(side='left',padx=(0,9),pady=5)
            self.buttons.append(b)
        self.message=tk.StringVar(value='Prêt. Commencer par « Analyser les entrées ».')
        ttk.Label(window,textvariable=self.message,padding=(18,6)).pack(fill='x')
        frame=ttk.Frame(window,padding=(18,0,18,12));frame.pack(fill='both',expand=True)
        self.log=tk.Text(frame,wrap='word',font=('Consolas',10),state='disabled')
        self.log.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(frame,command=self.log.yview);scroll.pack(side='right',fill='y')
        self.log.configure(yscrollcommand=scroll.set)
        self.append('Aucune source, identité, assertion ou publication n’est modifiée.\n')

    def append(self,what):
        self.log.configure(state='normal')
        self.log.insert('end',what+'\n');self.log.see('end')
        self.log.configure(state='disabled')

    def worker(self,description,func):
        self.message.set(description)
        for button in self.buttons:button.configure(state='disabled')
        def perform():
            try:
                response=func()
                text=json.dumps(response,ensure_ascii=False,indent=2) if isinstance(response,dict) else str(response)
                self.win.after(0,lambda:self.done(True,text))
            except Exception as exc:
                detail=f'{type(exc).__name__}: {exc}'
                self.win.after(0,lambda:self.done(False,detail))
        threading.Thread(target=perform,daemon=True).start()

    def done(self,ok,text):
        for b in self.buttons:b.configure(state='normal')
        self.append(('OK' if ok else 'ERREUR')+'\n'+text+'\n')
        self.message.set('Terminée.' if ok else 'Échec : lire le journal.')
        if not ok:messagebox.showerror('UNESCO',text,parent=self.win)

    def preflight(self):
        def run():
            chosen=backend.paths_for(WB)
            view=backend.make_view(WB)
            report={
                'workspace':str(WB),'inputs':{k:str(v) for k,v in chosen.items()},
                'concepts':len(view['articles']),'wikidata_proposals':36,'atomic_proposals':19,
                'branch_kristals_detected':len(view['root_catalog']),
                'historical_2025_matches':view['rdf_comparison']['historical_matched'],
                'public_release':False
            }
            return report
        self.worker('Vérification des sources et contrats…',run)

    def build(self):
        self.worker('Construction atomique de la vue de recherche privée…',lambda:backend.build(WB))

    def check(self):
        self.worker('Contrôle SHA-256 des artefacts privés…',lambda:backend.check(WB))

    def open_reader(self):
        try:
            backend.check(WB)
            if os.name!='nt':raise OSError('Windows required for .cmd reader')
            if not READER.is_file():raise FileNotFoundError(READER)
            os.startfile(str(READER))
            self.append('Serveur privé lancé (ouverture séparée). Adresse: http://127.0.0.1:8787')
        except Exception as exc:
            messagebox.showerror('EncyKlopedia',str(exc),parent=self.win)

if __name__=='__main__':
    app=tk.Tk();Panel(app);app.mainloop()
