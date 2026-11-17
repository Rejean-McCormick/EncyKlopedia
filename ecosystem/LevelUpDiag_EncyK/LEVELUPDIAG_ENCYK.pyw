# -*- coding: utf-8 -*-
"""External EncyK profile launcher for the standalone LevelUpDiag application.
Never starts/stops Skope or writes to EncyK/data roots.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import os
import subprocess
import sys
import shutil
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import re

TOOL = Path(__file__).resolve().parent
DEFAULT_TARGET = r'C:\mycode\EncyKlopedia\EncyKlopedia'


def missing_runtime(tool=TOOL):
    """Fail before launching a subprocess when only the add-on was installed."""
    expected = ('levelupdiag.py', 'levelupdiag_core/cli.py',
                'levelupdiag_core/runner.py', 'levelupdiag_manifest.json',
                'levelupdiag.config.json')
    return [name for name in expected if not (Path(tool) / name).is_file()]


def default_python():
    """Use console Python, not pythonw associated with .pyw files."""
    path = shutil.which('python') or shutil.which('python.exe')
    if path and Path(path).is_file():
        return str(Path(path))
    candidate = Path(sys.executable)
    if candidate.name.lower() == 'pythonw.exe':
        console = candidate.with_name('python.exe')
        if console.is_file():
            return str(console)
    return str(candidate)

class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('LevelUpDiag — EncyK only')
        self.geometry('910x610')
        self.minsize(750,490)
        self.target=tk.StringVar(value=DEFAULT_TARGET)
        self.python_path=tk.StringVar(value=default_python())
        self.current=tk.StringVar(value='reader')
        self.status=tk.StringVar(value='Ready. Does not modify EncyK, Wikidata or Kristals.')
        self.last_run=None
        body=ttk.Frame(self,padding=16);body.pack(fill='both',expand=True)
        ttk.Label(body,text='LevelUpDiag · Diagnostic EncyK',font=('Segoe UI',16,'bold')).pack(anchor='w')
        ttk.Label(body,text='Diagnostics exclusivement EncyK : dépôt, Wikidata, provenance, et pont facultatif avec Skope. Aucune modification des données.',wraplength=840).pack(anchor='w',pady=(4,16))
        pathrow=ttk.Frame(body);pathrow.pack(fill='x')
        ttk.Label(pathrow,text='EncyK repository').pack(side='left')
        ttk.Entry(pathrow,textvariable=self.target).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(pathrow,text='Browse',command=self.browse).pack(side='left')
        pythonrow=ttk.Frame(body);pythonrow.pack(fill='x',pady=(7,0))
        ttk.Label(pythonrow,text='Python for diagnostics').pack(side='left')
        ttk.Entry(pythonrow,textvariable=self.python_path).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(pythonrow,text='Browse',command=self.browse_python).pack(side='left')
        c=ttk.LabelFrame(body,text='Campaign',padding=10);c.pack(fill='x',pady=14)
        choices=[('reader','Reader — EncyK SQLite, index rapide et compatibilité du pont'),('quick','Quick — état EncyK, index et preuves'),('repository','Repository — EncyK clean + pull bridge'),('bridge','Bridge — contrat d’importation EncyK ← Skope'),('standard','Standard — all read-only checks')]
        for v,label in choices:
            ttk.Radiobutton(c,text=label,variable=self.current,value=v).pack(anchor='w',pady=3)
        row=ttk.Frame(body);row.pack(fill='x',pady=(1,12))
        self.btn=ttk.Button(row,text='Run diagnostics',command=self.run);self.btn.pack(side='left')
        ttk.Button(row,text='Export last report ZIP',command=self.export).pack(side='left',padx=8)
        ttk.Button(row,text='Open reports folder',command=self.openfolder).pack(side='left',padx=4)
        ttk.Label(body,textvariable=self.status,wraplength=850).pack(anchor='w',pady=(3,8))
        logframe=ttk.Frame(body);logframe.pack(fill='both',expand=True)
        self.log=tk.Text(logframe,wrap='word',height=15,font=('Consolas',10));self.log.pack(side='left',fill='both',expand=True)
        scrollbar=ttk.Scrollbar(logframe,command=self.log.yview);scrollbar.pack(side='right',fill='y');self.log.configure(yscrollcommand=scrollbar.set)
        self.append('Le service externe Skope est optionnel ; les diagnostics ne lancent aucun job.\n')
        missing=missing_runtime()
        if missing:
            self.append('INCOMPLETE LEVELUPDIAG INSTALLATION: '+', '.join(missing)+'\n')
            self.status.set('Missing LevelUpDiag engine. Install the FULL standalone release in this folder.')

    def append(self,message):
        self.log.insert('end',message)
        self.log.see('end')

    def browse(self):
        p=filedialog.askdirectory(initialdir=self.target.get(),title='Choose separate EncyK repository')
        if p:self.target.set(p)

    def browse_python(self):
        p=filedialog.askopenfilename(title='Choose console python.exe',
            filetypes=[('Python console','python.exe'),('All executables','*.exe'),('All files','*.*')])
        if p:self.python_path.set(p)

    def run(self):
        missing=missing_runtime()
        if missing:
            messagebox.showerror('Incomplete LevelUpDiag installation',
                'Missing: '+', '.join(missing)+'\n\n'
                'This folder contains only the EncyK add-on. Extract the FULL LevelUpDiag '
                'standalone ZIP into this same folder. EncyK itself stays separate.')
            return
        python=Path(self.python_path.get().strip().strip('"'))
        if not python.is_file() or python.name.casefold()=='pythonw.exe':
            messagebox.showerror('Python console required',
                'Choose a working python.exe (prefer the one used by Skope). '
                'For this computer, the Python 3.12 interpreter with indexed_bzip2 is recommended.')
            return
        target=Path(self.target.get().strip())
        if not all((target/f).is_file() for f in ('MANIFEST.json','VERSION','00_system/integrations/skope_bridge.py')):
            messagebox.showerror('Invalid target','Choose EncyK 0.14.x (VERSION, MANIFEST.json, Skope bridge).')
            return
        self.btn.configure(state='disabled')
        self.status.set('Running '+self.current.get()+'…')
        profile=self.current.get()
        self.append('\n>>> '+profile+'\n')
        def task():
            try:
                args=[str(python),'-B',str(TOOL/'levelupdiag.py'),'--target',str(target),'run',profile]
                env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
                proc=subprocess.run(args,cwd=str(TOOL),env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                    text=True,encoding='utf-8',errors='replace',timeout=360,check=False)
                output=(proc.stdout or '')+'\n'+(proc.stderr or '')
                match=re.search(r'(?m)^Report:\s*(.+summary\.json)\s*$',output)
                if match:self.last_run=Path(match.group(1)).parent
                self.after(0,lambda:self.append('Interpreter: '+str(python)+'\n'+output))
                self.after(0,lambda:self.status.set('Finished (exit '+str(proc.returncode)+'). Reports are inside LevelUpDiag.'))
            except Exception as exc:
                self.after(0,lambda exc=exc:self.append(type(exc).__name__+': '+str(exc)+'\n'))
                self.after(0,lambda:self.status.set('Failed to launch.'))
            finally:self.after(0,lambda:self.btn.configure(state='normal'))
        threading.Thread(target=task,daemon=True).start()

    def export(self):
        p=self.last_run
        if not p or not p.is_dir():
            messagebox.showwarning('No report yet','Run a campaign first.');return
        out=filedialog.asksaveasfilename(defaultextension='.zip',filetypes=[('ZIP','*.zip')],initialfile=p.name+'-encyk-diag.zip',title='Export LevelUpDiag report')
        if not out:return
        files=[]
        for item in p.rglob('*'):
            if not item.is_file() or item.is_symlink():continue
            rel=item.relative_to(p)
            if len(files)>=250 or item.stat().st_size>5_000_000:
                messagebox.showerror('Too many files','Report exceeds safe ZIP export limits.');return
            files.append((item,rel))
        with ZipFile(out,'w',compression=ZIP_DEFLATED) as z:
            for item,rel in files:z.write(item,arcname=rel.as_posix())
        self.status.set('Report ZIP saved to '+out)

    def openfolder(self):
        p=TOOL/'.levelupdiag/encyk/runs'
        if not p.is_dir():
            messagebox.showwarning('Reports','No reports yet.');return
        if sys.platform=='win32':os.startfile(p)
        else:messagebox.showinfo('Reports location',str(p))

if __name__=='__main__':Window().mainloop()
