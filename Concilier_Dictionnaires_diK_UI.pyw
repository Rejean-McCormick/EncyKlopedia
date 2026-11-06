#!/usr/bin/env python3
"""UI Tkinter autonome: conciliation candidate à très grande échelle, C code / D data."""
from __future__ import annotations

import json
import os
import queue
import re
import sqlite3
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

TITLE='EncyKlopedia → diK — Conciliation lexicale candidate v0.5'
ROOT_DEFAULT=r'D:\EncyKlopedia'
INDEX=Path('30_working/lexical/harvester/index-v1/lexical.sqlite3')
OUT=Path('30_working/lexical/harvester/dik-reconciliation-v1')
ENGINE=Path(__file__).resolve().parent/'tools'/'dictionary-harvester'/'dik_reconciliation.py'

class App:
    def __init__(self,win):
        self.win=win
        win.title(TITLE)
        win.geometry('1000x735')
        win.minsize(760,540)
        self.data_root=tk.StringVar(value=os.environ.get('ENCYK_DATA_ROOT',ROOT_DEFAULT))
        self.status=tk.StringVar(value='Lecture seule sur index-v1; sorties candidates sur D:.')
        self.phase=tk.StringVar(value='En attente')
        self.events=queue.Queue()
        self.worker=None
        self.proc=None
        self.stopping=False
        self._widgets()
        win.after(100,self._drain)
        win.after(200,self.inspect)
        win.protocol('WM_DELETE_WINDOW',self.close)

    def _widgets(self):
        outer=ttk.Frame(self.win,padding=16)
        outer.pack(fill='both',expand=True)
        ttk.Label(outer,text='Conciliation lexicale mondiale → diK',
                  font=('Segoe UI',17,'bold')).pack(anchor='w')
        ttk.Label(outer,text='Graphies candidates, provenance et revue — aucune identité KQ/KP, aucune publication.',
                  foreground='#566678').pack(anchor='w',pady=(2,10))
        root=ttk.Frame(outer)
        root.pack(fill='x',pady=5)
        ttk.Label(root,text='Données sur D:').pack(side='left')
        ttk.Entry(root,textvariable=self.data_root).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(root,text='Parcourir…',command=self.browse).pack(side='left')
        self.refresh=ttk.Button(root,text='Vérifier',command=self.inspect)
        self.refresh.pack(side='left',padx=(7,0))
        bar=ttk.Frame(outer)
        bar.pack(fill='x',pady=10)
        self.plan=ttk.Button(bar,text='Voir le plan',command=lambda:self.start('plan'))
        self.plan.pack(side='left')
        self.pilot=ttk.Button(bar,text='Pilote français + anglais',command=lambda:self.start('pilot'))
        self.pilot.pack(side='left',padx=(7,0))
        self.full=ttk.Button(bar,text='Lancer / reprendre les 6 848 langues',command=lambda:self.start('full'))
        self.full.pack(side='left',padx=(7,0))
        self.stop_btn=ttk.Button(bar,text='Interrompre',command=self.stop,state='disabled')
        self.stop_btn.pack(side='left',padx=(7,0))
        ttk.Button(bar,text='Ouvrir les résultats',command=self.open_report).pack(side='right')
        ttk.Button(bar,text='Explorer les candidats',command=self.explore).pack(side='right',padx=(0,9))
        self.verify_btn=ttk.Button(bar,text='Vérifier les exports',command=lambda:self.start('verify'))
        self.verify_btn.pack(side='right',padx=(0,9))
        ttk.Label(outer,textvariable=self.status,foreground='#22757c',wraplength=980).pack(anchor='w')
        prog=ttk.Frame(outer)
        prog.pack(fill='x',pady=(10,8))
        ttk.Label(prog,textvariable=self.phase,width=47).pack(side='left')
        self.progress=ttk.Progressbar(prog,maximum=100,mode='determinate')
        self.progress.pack(side='left',fill='x',expand=True,padx=(6,0))
        ttk.Label(outer,text='Étapes automatiques : index existant → rapprochements homographes → preuves → JSONL candidats → rapport + licences.',
                  wraplength=960).pack(anchor='w',pady=(7,5))
        ttk.Label(outer,text='Les étapes de validation humaine, d’alignement sémantique et de publication restent volontairement bloquées.',
                  foreground='#8a6623',wraplength=960).pack(anchor='w',pady=(0,8))
        columns=('kind','value')
        self.table=ttk.Treeview(outer,columns=columns,show='headings',height=5)
        self.table.heading('kind',text='Élément')
        self.table.heading('value',text='État')
        self.table.column('kind',width=260)
        self.table.column('value',width=680)
        self.table.pack(fill='x',pady=(4,10))
        ttk.Label(outer,text='Journal de traitement',font=('Segoe UI',10,'bold')).pack(anchor='w')
        frame=ttk.Frame(outer)
        frame.pack(fill='both',expand=True)
        self.log=tk.Text(frame,font=('Consolas',9),height=13,state='disabled',wrap='word')
        self.log.pack(side='left',fill='both',expand=True)
        sc=ttk.Scrollbar(frame,command=self.log.yview)
        sc.pack(side='right',fill='y')
        self.log.config(yscrollcommand=sc.set)

    def root(self):return Path(self.data_root.get()).expanduser().resolve()

    def browse(self):
        choice=filedialog.askdirectory(initialdir=str(self.root()) if self.root().is_dir() else None)
        if choice:self.data_root.set(choice);self.inspect()

    def logline(self,s):
        self.log.config(state='normal')
        self.log.insert('end',s.rstrip()+'\n')
        if int(self.log.index('end-1c').split('.')[0])>2200:self.log.delete('1.0','201.0')
        self.log.see('end');self.log.config(state='disabled')

    def running(self):return self.worker is not None and self.worker.is_alive()

    def inspect(self):
        if self.running():return
        for item in self.table.get_children():self.table.delete(item)
        root=self.root()
        db=root/INDEX
        enabled=ENGINE.is_file() and db.is_file()
        for b in (self.plan,self.pilot,self.full):b.config(state='normal' if enabled else 'disabled')
        self.verify_btn.config(state='normal' if enabled and (root/OUT/'reconciliation.sqlite3').is_file() else 'disabled')
        if not ENGINE.is_file():self.status.set('Moteur manquant : extraire le ZIP entier sur C:');return
        if not db.is_file():self.status.set(f'Index absent : {db}');return
        try:
            con=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=8)
            try:
                src=con.execute('SELECT COUNT(*) FROM source_files').fetchone()[0]
                rows=con.execute('SELECT SUM(lemma_observations),COUNT(DISTINCT language_code) FROM language_stats').fetchone()
            finally:con.close()
            self.table.insert('', 'end',values=('Base existante',str(db)))
            self.table.insert('', 'end',values=('Fichiers sources',str(src)))
            self.table.insert('', 'end',values=('Observations de lemmes',f'{rows[0]:,}' if rows[0] else '0'))
            self.table.insert('', 'end',values=('Codes linguistiques',str(rows[1])))
            manifest=root/OUT/'latest.json'
            if manifest.exists():
                state=json.loads(manifest.read_text(encoding='utf-8'))
                self.table.insert('', 'end',values=('Conciliation candidate',
                     f"{state.get('languages_staged',0):,}/{state.get('languages_total',0):,} langues ; {state.get('cross_family_candidate_keys',0):,} clés candidates"))
            self.status.set('Prêt : code sur C:, observations et nouveaux résultats sur D:.')
        except (sqlite3.Error,OSError,ValueError) as e:
            self.status.set('Lecture index impossible : '+str(e))
            for b in (self.plan,self.pilot,self.full):b.config(state='disabled')

    def start(self,mode):
        if self.running():return
        if mode=='full':
            if not messagebox.askyesno(TITLE,'Le mode mondial peut analyser plus de 87 millions de lignes et écrire des fichiers volumineux sur D:.\n\nIl reprend par langue et ne modifie pas l’index source. Démarrer ?'):
                return
        if mode=='pilot':
            if not messagebox.askyesno(TITLE,'Analyser le français et l’anglais ?\nLes mêmes résultats seront repris lors de l’exécution globale.'):
                return
        self.progress['value']=0
        self.stopping=False
        self.phase.set('Démarrage…')
        for b in (self.plan,self.pilot,self.full,self.refresh,self.verify_btn):b.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.logline('=== '+{'full':'Conciliation mondiale','pilot':'Pilote fr,en','plan':'Inventaire','verify':'Vérification SHA-256'}[mode]+' ===')
        self.worker=threading.Thread(target=self.execute,args=(mode,str(self.root())),daemon=True)
        self.worker.start()

    def execute(self,mode,root):
        exe=Path(sys.executable)
        if os.name=='nt' and exe.name.lower()=='pythonw.exe':
            new=exe.with_name('python.exe')
            if new.exists():exe=new
        cmd=[str(exe),'-u',str(ENGINE),'plan' if mode=='plan' else 'verify' if mode=='verify' else 'run','--data-root',root]
        if mode=='pilot':cmd.extend(['--languages','fr,en'])
        try:
            self.proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                encoding='utf-8',errors='replace',text=True,bufsize=1,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            for line in self.proc.stdout:self.events.put(('line',line.rstrip()))
            self.events.put(('done',self.proc.wait()))
        except Exception as exc:
            self.events.put(('error',str(exc)))
        finally:self.proc=None

    def _drain(self):
        try:
            while True:
                typ,value=self.events.get_nowait()
                if typ=='line':
                    if value.startswith('LANGUAGE|'):
                        _,i,total,lang=value.split('|',3)
                        self.phase.set(f'{i}/{total} langues · {lang}')
                        self.progress['value']=int(i)/max(1,int(total))*100
                    elif value.startswith('CHECKPOINT|'):
                        self.logline('Checkpoint confirmé : '+value)
                    else:self.logline(value)
                elif typ in ('done','error'):
                    self.stop_btn.config(state='disabled')
                    self.phase.set('Terminé' if typ=='done' and value==0 else 'Arrêté ou erreur')
                    self.logline('=== '+('Code de sortie : '+str(value) if typ=='done' else 'Erreur : '+value)+' ===')
                    self.win.after(300,self.inspect)
        except queue.Empty:pass
        self.win.after(120,self._drain)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.stopping=True
            self.proc.terminate()
            self.logline('Interruption demandée; les langues validées sont conservées. Relancer pour reprendre.')
        self.stop_btn.config(state='disabled')

    def open_report(self):
        path=self.root()/OUT/'RAPPORT_RECONCILIATION.md'
        if not path.is_file():messagebox.showinfo(TITLE,'Aucun rapport disponible; lancer le traitement.');return
        if os.name=='nt':os.startfile(str(path))
        else:messagebox.showinfo(TITLE,str(path))

    def explore(self):
        path=self.root()/OUT/'reconciliation.sqlite3'
        if not path.is_file():
            messagebox.showinfo(TITLE,'Commence par le pilote fr/en pour creer la base candidate.')
            return
        popup=tk.Toplevel(self.win)
        popup.title('Explorer les graphies candidates (lecture seule)')
        popup.geometry('900x680')
        box=ttk.Frame(popup,padding=12)
        box.pack(fill='both',expand=True)
        ttk.Label(box,text='Chercher dans les candidats — homographies, pas équivalences de sens',
                  font=('Segoe UI',12,'bold')).pack(anchor='w')
        form=ttk.Frame(box);form.pack(fill='x',pady=10)
        ttk.Label(form,text='Langue :').pack(side='left')
        lang=tk.StringVar(value='fr')
        ttk.Entry(form,textvariable=lang,width=9).pack(side='left',padx=(5,12))
        ttk.Label(form,text='Début de graphie :').pack(side='left')
        lemma=tk.StringVar()
        ttk.Entry(form,textvariable=lemma,width=28).pack(side='left',padx=(5,8))
        ttk.Label(form,text='100 premiers résultats maximum').pack(side='right')
        tree=ttk.Treeview(box,columns=('key','obs','fam'),show='headings',height=9)
        for col,title,w in [('key','Graphie',330),('obs','Observations',115),('fam','Familles',400)]:
            tree.heading(col,text=title);tree.column(col,width=w)
        tree.pack(fill='x')
        detail=tk.Text(box,font=('Consolas',9),height=18,wrap='word')
        detail.pack(fill='both',expand=True,pady=(8,0))
        selected={}
        def search():
            for row in tree.get_children():tree.delete(row)
            selected.clear();detail.delete('1.0','end')
            l=lang.get().strip().lower()
            p=lemma.get().strip().casefold()
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,39}',l):
                messagebox.showerror(TITLE,'Code de langue invalide.',parent=popup);return
            try:
                con=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=6)
                try:
                    if p:
                        rows=con.execute('''SELECT lemma_key,observations,families_mask,provenance_json
                           FROM candidates WHERE language=? AND lemma_key>=? AND lemma_key<?
                           ORDER BY lemma_key LIMIT 100''',(l,p,p+'\U0010ffff')).fetchall()
                    else:
                        rows=con.execute('''SELECT lemma_key,observations,families_mask,provenance_json
                           FROM candidates WHERE language=? ORDER BY lemma_key LIMIT 100''',(l,)).fetchall()
                finally:con.close()
                for key,obs,mask,prov in rows:
                    families=', '.join(n for n,b in [('Kaikki',1),('UniMorph',2),('Wikidata',4)] if mask&b)
                    rid=tree.insert('','end',values=(key,f'{obs:,}',families))
                    selected[rid]=prov
            except (OSError,sqlite3.Error) as exc:
                messagebox.showerror(TITLE,'Lecture impossible : '+str(exc),parent=popup)
        def show(_event=None):
            ids=tree.selection()
            if not ids:return
            value=json.dumps(json.loads(selected[ids[0]]),ensure_ascii=False,indent=2)
            detail.delete('1.0','end');detail.insert('end',value)
        tree.bind('<<TreeviewSelect>>',show)
        ttk.Button(form,text='Chercher',command=search).pack(side='left')
        search()

    def close(self):
        if self.running():
            messagebox.showwarning(TITLE,'Traitement actif : utiliser Interrompre avant de fermer.');return
        self.win.destroy()


def main():
    win=tk.Tk()
    ttk.Style(win).theme_use('clam')
    App(win)
    win.mainloop()

if __name__=='__main__':main()
