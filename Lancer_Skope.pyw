# -*- coding: utf-8 -*-
"""Assistant EncyK: choisir un Kristal, guider Skope et préparer Discovery.

Skope n'écrit jamais dans le canon. Le Kit est lancé seulement sur clic confirmé.
"""
from pathlib import Path
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import webbrowser
import threading

ROOT=Path(__file__).resolve().parent
TOOL=ROOT/'00_system/tools/skope'
sys.path.insert(0,str(TOOL))
from skope.project import (DEFAULT_LOCALS, default_database, default_guidance,
                           find_kristals, read_kristal, safe_target)
from skope.arketype import load_guidance
from skope.db import connect,meta

KIT_CANDIDATES=[
    Path(os.environ['KRISTAL_AUTHORING_KIT_TOOL']) if os.environ.get('KRISTAL_AUTHORING_KIT_TOOL') else None,
    Path(r'C:\mycode\Kristal\Kristal-Authoring-Kit\tools\kristal.py'),
]

class App:
    def __init__(self, window):
        self.window=window; self.proc=None; self.proc_config=None; self.kristals={}; self.manual_guide=False
        window.title('EncyKlopedia — Enrich a Kristal with Skope')
        window.geometry('930x450'); window.minsize(770,420)
        frame=ttk.Frame(window,padding=18);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Enrich a Kristal · EncyK + Skope',font=('Segoe UI',15,'bold')).pack(anchor='w')
        ttk.Label(frame,text='Choose a target Kristal, explore Wikidata on D:, then export a proposal. No automatic canonical injection.',wraplength=840).pack(anchor='w',pady=(2,13))
        self.kristal=tk.StringVar(value='')
        self.db=tk.StringVar(value=str(default_database()))
        self.guidance=tk.StringVar(value='')
        self.kit=tk.StringVar(value=str(next((p for p in KIT_CANDIDATES if p and p.is_file()),' ')).strip())
        self.state=tk.StringVar(value='Select a Kristal, then open Skope.')

        row=ttk.Frame(frame);row.pack(fill='x',pady=5)
        ttk.Label(row,text='Target Kristal',width=23).pack(side='left')
        self.kristal_combo=ttk.Combobox(row,textvariable=self.kristal,state='readonly')
        self.kristal_combo.pack(side='left',fill='x',expand=True)
        self.kristal_combo.bind('<<ComboboxSelected>>',lambda _:self.on_kristal_change())
        ttk.Button(row,text='Browse folder…',command=self.pick_kristal).pack(side='left',padx=(7,0))
        ttk.Button(row,text='Refresh',command=self.refresh_kristals).pack(side='left',padx=(7,0))
        self.detail=tk.StringVar(value='No Kristal selected')
        ttk.Label(frame,textvariable=self.detail,foreground='#4e6678',wraplength=840).pack(anchor='w',pady=(0,7))

        row=ttk.Frame(frame);row.pack(fill='x',pady=5)
        ttk.Label(row,text='Wikidata index (D:)',width=23).pack(side='left')
        ttk.Entry(row,textvariable=self.db).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Browse…',command=self.pick_db).pack(side='left',padx=(7,0))

        row=ttk.Frame(frame);row.pack(fill='x',pady=5)
        ttk.Label(row,text='Guide Arketype 1.4',width=23).pack(side='left')
        ttk.Entry(row,textvariable=self.guidance).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Choose…',command=self.pick_guidance).pack(side='left',padx=(7,0))
        ttk.Button(row,text='Auto',command=self.auto_guidance).pack(side='left',padx=(7,0))

        ttk.Label(frame,text='Arketype PRF-03 is design guidance for Botany only. It grants no permissions and does not change the canon.',foreground='#4e6678',wraplength=840).pack(anchor='w',pady=(1,9))
        controls=ttk.Frame(frame);controls.pack(fill='x',pady=(5,12))
        ttk.Button(controls,text='Open Skope',command=self.start).pack(side='left')
        ttk.Button(controls,text='Stop Skope',command=self.stop).pack(side='left',padx=8)
        ttk.Separator(frame).pack(fill='x',pady=10)
        ttk.Label(frame,text='Authoring Kit 3.3.1 · Non-canonical Discovery',font=('Segoe UI',10,'bold')).pack(anchor='w')
        row=ttk.Frame(frame);row.pack(fill='x',pady=6)
        ttk.Label(row,text='Authoring Kit tool',width=23).pack(side='left')
        ttk.Entry(row,textvariable=self.kit).pack(side='left',fill='x',expand=True)
        ttk.Button(row,text='Choose…',command=self.pick_kit).pack(side='left',padx=(7,0))
        controls=ttk.Frame(frame);controls.pack(fill='x',pady=6)
        ttk.Button(controls,text='Check Kristal',command=lambda:self.kit_action('check')).pack(side='left')
        ttk.Button(controls,text='Build Discovery',command=lambda:self.kit_action('build-discovery')).pack(side='left',padx=8)
        ttk.Label(frame,textvariable=self.state,wraplength=860).pack(anchor='w',pady=(5,0))
        self.refresh_kristals()
        window.protocol('WM_DELETE_WINDOW',self.quit)

    def refresh_kristals(self):
        old=self.kristal.get()
        self.kristals={str(p):d for p,d in find_kristals()}
        # Préserver un Kristal choisi hors de la bibliothèque standard.
        if old and old not in self.kristals and Path(old,'kristal.workspace.json').is_file():
            try:self.kristals[old]=read_kristal(old)
            except (ValueError,OSError):pass
        choices=list(self.kristals)
        self.kristal_combo['values']=choices
        if old in self.kristals:selection=old
        else:selection=next((p for p,d in self.kristals.items() if d['slug'].lower()=='kristal-botany'),choices[0] if choices else '')
        self.kristal.set(selection)
        self.on_kristal_change()

    def pick_kristal(self):
        folder=filedialog.askdirectory(title='Select a Kristal folder containing kristal.workspace.json',initialdir=str(DEFAULT_LOCALS))
        if not folder:return
        try:d=read_kristal(folder)
        except (ValueError,OSError) as ex:messagebox.showerror('Invalid Kristal',str(ex));return
        self.kristals[folder]=d;self.kristal_combo['values']=list(self.kristals)
        self.kristal.set(folder);self.on_kristal_change()

    def on_kristal_change(self):
        d=self.kristals.get(self.kristal.get())
        if d:
            self.detail.set(f"{d['title']} · {d['state_ref']} · domain: {d['domain'] or 'not declared'} · {d['state_architecture']}")
        else:self.detail.set('No Kristal found; choose a folder')
        if not self.manual_guide:self.auto_guidance()

    def auto_guidance(self):
        d=self.kristals.get(self.kristal.get())
        path=default_guidance(d)
        self.guidance.set(str(path) if path else '')
        self.manual_guide=False

    def pick_guidance(self):
        x=filedialog.askopenfilename(title='Arketype design guidance',filetypes=[('JSON','*.json')])
        if x:self.guidance.set(x);self.manual_guide=True

    def pick_db(self):
        x=filedialog.askopenfilename(title='EncyK SQLite index (read-only)',filetypes=[('SQLite','*.sqlite *.db'),('All files','*.*')])
        if x:self.db.set(x)

    def pick_kit(self):
        x=filedialog.askopenfilename(title='Authoring Kit tools/kristal.py',filetypes=[('Python','*.py')])
        if x:self.kit.set(x)

    def selected(self):
        folder=self.kristal.get()
        if not folder:raise ValueError('Choose a target Kristal')
        d=read_kristal(folder)  # relire la cible au moment de l'action
        return folder,d

    def start(self):
        try:
            folder,target=self.selected()
            path=Path(self.db.get())
            if not path.is_file():raise ValueError('EncyK index not found; check D:\\EncyKlopedia')
            intended=(str(Path(folder).resolve()),str(path.resolve()),self.guidance.get().strip())
            if self.proc and self.proc.poll() is None:
                if self.proc_config==intended:
                    webbrowser.open('http://127.0.0.1:8767');return
                self.stop()  # ne jamais réutiliser silencieusement l'ancienne cible
            with connect(path) as db:meta(db)
            args=[]
            if self.guidance.get().strip():
                g=Path(self.guidance.get().strip());load_guidance(g)
                args+=['--guidance',str(g)]
            env=os.environ.copy();env['PYTHONPATH']=str(TOOL)+os.pathsep+env.get('PYTHONPATH','')
            self.proc=subprocess.Popen([sys.executable,'-m','skope','serve','--db',str(path),'--port','8767','--kristal',str(folder),*args],
                    cwd=str(ROOT),env=env,creationflags=(subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0))
            self.proc_config=intended
            self.state.set(f"Skope started for {target['title']} (non-canonical proposal).")
            self.window.after(950,self.open_if_running)
        except Exception as exc:messagebox.showerror('Skope',str(exc))

    def open_if_running(self):
        if self.proc and self.proc.poll() is None:webbrowser.open('http://127.0.0.1:8767')
        else:self.state.set('Could not start Skope. Port 8767 may be in use, or the server failed.')

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate();self.proc=None;self.proc_config=None;self.state.set('Skope stopped.')

    def kit_action(self,command):
        try:
            folder,target=self.selected()
            tool=Path(self.kit.get().strip())
            if not tool.is_file() or tool.name!='kristal.py':
                raise ValueError('Select tools/kristal.py from Authoring Kit 3.3.1')
            if command=='build-discovery' and not messagebox.askyesno('Update Discovery',
                 'Generate/refresh kristal.discovery.json and two derived reader files for '+target['title']+' ?\n\nNo canonical state will be modified.'):
                return
            self.state.set('Authoring Kit : '+command+'…')
            def worker():
                try:
                    p=subprocess.run([sys.executable,str(tool),command,str(folder)],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
                    msg=(p.stdout or p.stderr or 'Command completed').strip()
                    title='Authoring Kit' if p.returncode==0 else 'Authoring Kit failed'
                    self.window.after(0,lambda:messagebox.showinfo(title,msg[-3500:]) if p.returncode==0 else messagebox.showerror(title,msg[-3500:]))
                    self.window.after(0,lambda:self.state.set('Command completed.' if p.returncode==0 else 'Command failed.'))
                except Exception as ex:
                    self.window.after(0,lambda ex=ex:messagebox.showerror('Kit',str(ex)))
            threading.Thread(target=worker,daemon=True).start()
        except Exception as exc:messagebox.showerror('Authoring Kit',str(exc))

    def quit(self):self.stop();self.window.destroy()

if __name__=='__main__':
    window=tk.Tk();App(window);window.mainloop()
