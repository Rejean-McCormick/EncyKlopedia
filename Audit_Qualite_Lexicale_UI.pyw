#!/usr/bin/env python3
"""EncyKlopedia lexical quality audit UI (Tkinter / Python stdlib)."""
import json
import os
import queue
import sqlite3
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

TITLE = 'EncyKlopedia — Audit de qualité lexicale v0.4'
DEFAULT_ROOT = r'D:\EncyKlopedia'
INDEX_SUB = Path('30_working/lexical/harvester/index-v1')
QUALITY_SUB = Path('30_working/lexical/harvester/quality-v1')
SCRIPT = Path(__file__).resolve().parent/'tools'/'dictionary-harvester'/'quality_audit.py'


class QualityUI:
    def __init__(self, win):
        self.win=win
        self.win.title(TITLE)
        self.win.geometry('1050x735')
        self.win.minsize(815,580)
        self.data_root=tk.StringVar(value=os.environ.get('ENCYK_DATA_ROOT',DEFAULT_ROOT))
        self.status=tk.StringVar(value='Prêt : source index v1 en lecture seule.')
        self.phase=tk.StringVar(value='Aucun traitement actif')
        self.events=queue.Queue()
        self.process=None
        self.worker=None
        self.current_job=None
        self._build()
        self.win.protocol('WM_DELETE_WINDOW',self._close)
        self.win.after(60,self.inspect)
        self.win.after(100,self._drain)

    def _build(self):
        host=ttk.Frame(self.win,padding=15)
        host.pack(fill='both',expand=True)
        ttk.Label(host,text='Audit qualité · dictionnaires multilingues',font=('Segoe UI',17,'bold')).pack(anchor='w')
        ttk.Label(host,text='Sources et index v1 : lecture seule. Résultats séparés sur D:. Aucune intégration canonique diK.',
                  foreground='#53677b').pack(anchor='w',pady=(2,11))
        row=ttk.Frame(host)
        row.pack(fill='x',pady=(0,7))
        ttk.Label(row,text='Données (D:) :').pack(side='left')
        ttk.Entry(row,textvariable=self.data_root).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(row,text='Parcourir',command=self.browse).pack(side='left')
        self.refresh_btn=ttk.Button(row,text='Actualiser',command=self.inspect)
        self.refresh_btn.pack(side='left',padx=(7,0))
        buttonrow=ttk.Frame(host)
        buttonrow.pack(fill='x',pady=8)
        self.diag_btn=ttk.Button(buttonrow,text='Diagnostiquer pib + sdh',command=lambda:self.start('diagnostic'))
        self.diag_btn.pack(side='left')
        self.pilot_btn=ttk.Button(buttonrow,text='Audit pilote (fr/en)',command=lambda:self.start('pilot'))
        self.pilot_btn.pack(side='left',padx=(8,0))
        self.full_btn=ttk.Button(buttonrow,text='Lancer / reprendre l’audit complet',command=lambda:self.start('audit'))
        self.full_btn.pack(side='left',padx=(8,0))
        self.stop_btn=ttk.Button(buttonrow,text='Interrompre',command=self.stop,state='disabled')
        self.stop_btn.pack(side='left',padx=(8,0))
        ttk.Button(buttonrow,text='Ouvrir rapport',command=self.open_report).pack(side='right')
        ttk.Label(host,textvariable=self.status,foreground='#306a6c',wraplength=995).pack(anchor='w',pady=(4,3))
        progress_frame=ttk.Frame(host)
        progress_frame.pack(fill='x',pady=(4,10))
        ttk.Label(progress_frame,textvariable=self.phase,width=41).pack(side='left')
        self.progress=ttk.Progressbar(progress_frame,maximum=100,mode='determinate')
        self.progress.pack(side='left',fill='x',expand=True,padx=(10,0))
        ttk.Label(host,text='Sources à qualifier (vue index actuelle) :',font=('Segoe UI',10,'bold')).pack(anchor='w')
        box=ttk.Frame(host)
        box.pack(fill='both',expand=True,pady=(4,10))
        cols=('edition','status','accepted','rejected','reason')
        self.table=ttk.Treeview(box,columns=cols,show='headings',height=9)
        fields=(('edition','Source',95),('status','Statut',135),('accepted','Acceptées',125),
                ('rejected','Rejetées',125),('reason','Observation',440))
        for name,label,width in fields:
            self.table.heading(name,text=label)
            self.table.column(name,width=width,anchor='w' if name=='reason' else 'center')
        self.table.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(box,orient='vertical',command=self.table.yview)
        scroll.pack(side='right',fill='y')
        self.table.configure(yscrollcommand=scroll.set)
        ttk.Label(host,text='Journal de l’audit :',font=('Segoe UI',10,'bold')).pack(anchor='w')
        logs=ttk.Frame(host)
        logs.pack(fill='both',expand=True,pady=(4,0))
        self.log=tk.Text(logs,font=('Consolas',9),height=12,wrap='word',state='disabled')
        self.log.pack(side='left',fill='both',expand=True)
        s2=ttk.Scrollbar(logs,command=self.log.yview)
        s2.pack(side='right',fill='y')
        self.log.configure(yscrollcommand=s2.set)
        ttk.Label(host,text='Un chevauchement de graphies n’est PAS une équivalence de sens. Licences et provenance à vérifier.',
                  foreground='#8d6e27').pack(anchor='w',pady=(10,0))

    def _root(self):
        return Path(self.data_root.get()).expanduser().resolve()

    def browse(self):
        loc=self.data_root.get()
        selected=filedialog.askdirectory(initialdir=loc if Path(loc).is_dir() else None)
        if selected:
            self.data_root.set(selected)
            self.inspect()

    def _running(self):
        return self.worker is not None and self.worker.is_alive()

    def _log(self,text):
        self.log.configure(state='normal')
        self.log.insert('end',text.rstrip()+'\n')
        # Avoid runaway long-running log text memory.
        if int(self.log.index('end-1c').split('.')[0])>3500:
            self.log.delete('1.0','501.0')
        self.log.see('end')
        self.log.configure(state='disabled')

    def inspect(self):
        if self._running():return
        for item in self.table.get_children():self.table.delete(item)
        root=self._root()
        db=root/INDEX_SUB/'lexical.sqlite3'
        ok=SCRIPT.is_file() and db.is_file()
        for button in (self.diag_btn,self.pilot_btn,self.full_btn):
            button.configure(state='normal' if ok else 'disabled')
        if not SCRIPT.is_file():
            self.status.set('Module quality_audit.py absent : extraire tout l’overlay v0.4 sur C:.')
            return
        if not db.is_file():
            self.status.set(f'Index lexical introuvable : {db}. Vérifie D:.')
            return
        try:
            conn=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=4)
            try:
                all_count=conn.execute('SELECT COUNT(*) FROM source_files').fetchone()[0]
                complete=conn.execute("SELECT COUNT(*) FROM source_files WHERE status='complete'").fetchone()[0]
                for name,status,accepted,rejected in conn.execute('''SELECT edition,status,accepted,rejected
                  FROM source_files WHERE status != 'complete' OR (accepted+rejected>0 AND rejected*1.0/(accepted+rejected)>=0.20)
                  ORDER BY CASE WHEN status != 'complete' THEN 0 ELSE 1 END, edition LIMIT 70'''):
                    reason=('Sans lignes exploitables connues' if status=='no_data' else
                            'Taux de rejet élevé' if status=='complete' else 'À examiner')
                    self.table.insert('', 'end', values=(name,status,f'{accepted:,}',f'{rejected:,}',reason))
            finally:conn.close()
            pointer=root/QUALITY_SUB/'latest.json'
            state='Aucun audit complet lancé.'
            if pointer.is_file():
                recent=json.loads(pointer.read_text(encoding='utf-8'))
                state=f'Audit existant : {recent.get("languages_audited",0):,}/{recent.get("languages_total",0):,} langues traitées.'
            self.status.set(f'Index : {complete}/{all_count} sources complètes. {state}')
        except (OSError,sqlite3.Error,ValueError,KeyError) as exc:
            self.status.set(f'Impossible de lire l’index : {exc}')
            for button in (self.diag_btn,self.pilot_btn,self.full_btn):button.configure(state='disabled')

    def start(self,job):
        if self._running():return
        root=self._root()
        if job=='audit':
            prompt=('Audit global de toutes les langues indexées.\n\n'
                    'Il peut parcourir des dizaines de millions de lignes SQLite et prendre longtemps. '
                    'Les checkpoints seront conservés par langue et la base initiale restera en lecture seule.\n\nDémarrer ?')
            if not messagebox.askyesno(TITLE,prompt):return
        self.progress['value']=0
        self.current_job=job
        self.phase.set('Démarrage du traitement…')
        self._log('=== '+('Diagnostic pib/sdh' if job=='diagnostic' else 'Audit pilote fr/en' if job=='pilot' else 'Audit exhaustif')+' ===')
        for b in (self.diag_btn,self.pilot_btn,self.full_btn,self.refresh_btn):b.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.worker=threading.Thread(target=self._execute,args=(job,str(root)),daemon=True)
        self.worker.start()

    def _execute(self,job,root):
        exe=Path(sys.executable)
        if os.name=='nt' and exe.name.lower()=='pythonw.exe':
            console=exe.with_name('python.exe')
            if console.is_file():exe=console
        cmd=[str(exe),'-u',str(SCRIPT), 'diagnostic' if job=='diagnostic' else 'audit',
             '--data-root',root]
        if job=='pilot':cmd+=['--languages','fr,en']
        try:
            self.process=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                text=True,encoding='utf-8',errors='replace',bufsize=1,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            for line in self.process.stdout:
                self.events.put(('line',line.rstrip()))
            result=self.process.wait()
            self.events.put(('done',result))
        except Exception as exc:
            self.events.put(('error',str(exc)))
        finally:
            self.process=None

    def _drain(self):
        while True:
            try:kind,data=self.events.get_nowait()
            except queue.Empty:break
            if kind=='line':
                if data.startswith('PROGRESS|'):
                    try:
                        _,done,total,lang=data.split('|',3)
                        self.progress['value']=100*int(done)/max(1,int(total))
                        self.phase.set(f'{int(done):,} / {int(total):,} langues · {lang}')
                    except (ValueError,ZeroDivisionError):self._log(data)
                else:self._log(data)
            elif kind in ('done','error'):
                self.stop_btn.configure(state='disabled')
                self.current_job=None
                if kind=='done':
                    self._log(f'=== Processus terminé (code {data}) ===')
                    self.phase.set('Terminé' if data==0 else 'Interrompu ou en erreur')
                else:
                    self._log('ERREUR : '+data)
                    self.phase.set('Erreur de lancement')
                self.win.after(300,self.inspect)
        self.win.after(130,self._drain)

    def stop(self):
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self._log('Interruption demandée. Les langues déjà validées restent dans la base qualité. Relancer pour continuer.')
            self.stop_btn.configure(state='disabled')

    def open_report(self):
        root=self._root()
        pointer=root/QUALITY_SUB/'latest.json'
        report=root/QUALITY_SUB/'DIAGNOSTIC_PIB_SDH.md'
        if pointer.is_file():
            try:
                current=json.loads(pointer.read_text(encoding='utf-8'))
                target=Path(current['report']).resolve()
                if root in target.parents and target.is_file():report=target
            except (OSError,ValueError,KeyError):pass
        if not report.is_file():
            messagebox.showinfo(TITLE,'Aucun rapport disponible. Lance un diagnostic ou un audit.')
        elif os.name=='nt':os.startfile(str(report))
        else:messagebox.showinfo(TITLE,str(report))

    def _close(self):
        if self._running():
            messagebox.showwarning(TITLE,'Audit actif : clique sur Interrompre avant de fermer. Les checkpoints seront conservés.')
            return
        self.win.destroy()


def main():
    win=tk.Tk()
    ttk.Style(win).theme_use('clam')
    QualityUI(win)
    win.mainloop()


if __name__=='__main__':main()
