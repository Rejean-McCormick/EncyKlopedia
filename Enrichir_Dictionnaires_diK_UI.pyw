#!/usr/bin/env python3
"""Interface Tkinter pour enrichissement lexical probatoire v0.6, standard library."""
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
from tkinter import ttk, filedialog, messagebox

TITLE = 'EncyKlopedia → diK — Preuves lexicales v0.6'
DEFAULT_ROOT = r'D:\EncyKlopedia'
ENGINE = Path(__file__).resolve().parent/'tools'/'dictionary-harvester'/'semantic_enrichment.py'
INDEX = Path('30_working/lexical/harvester/index-v1/lexical.sqlite3')
V05 = Path('30_working/lexical/harvester/dik-reconciliation-v1/reconciliation.sqlite3')
OUT = Path('30_working/lexical/harvester/dik-enrichment-v1')

class App:
    def __init__(self, win):
        self.win = win
        win.title(TITLE)
        win.geometry('1110x770')
        win.minsize(800,550)
        self.data_root=tk.StringVar(value=os.environ.get('ENCYK_DATA_ROOT',DEFAULT_ROOT))
        self.phase=tk.StringVar(value='Prêt à vérifier les entrées v0.5')
        self.status=tk.StringVar(value='Code sur C: • index et archives sur D: • aucune publication')
        self.events=queue.Queue()
        self.worker=None
        self.proc=None
        self.create_widgets()
        win.after(150,self.poll)
        win.after(300,self.inspect)
        win.protocol('WM_DELETE_WINDOW',self.close)

    def create_widgets(self):
        root=ttk.Frame(self.win,padding=16)
        root.pack(fill='both',expand=True)
        ttk.Label(root,text='Enrichissement des preuves lexicales → diK',font=('Segoe UI',17,'bold')).pack(anchor='w')
        ttk.Label(root,text='Glose Kaikki • IDs Wikidata L/S/F • flexions UniMorph • revue humaine obligatoire',
                  foreground='#546775').pack(anchor='w',pady=(2,10))
        path_row=ttk.Frame(root)
        path_row.pack(fill='x',pady=(0,10))
        ttk.Label(path_row,text='Données sur D:').pack(side='left')
        ttk.Entry(path_row,textvariable=self.data_root).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(path_row,text='Parcourir…',command=self.browse).pack(side='left')
        self.check_btn=ttk.Button(path_row,text='Vérifier',command=self.inspect)
        self.check_btn.pack(side='left',padx=(7,0))
        buttons=ttk.Frame(root)
        buttons.pack(fill='x',pady=(0,11))
        self.plan_btn=ttk.Button(buttons,text='Voir le plan',command=lambda:self.start('plan'))
        self.plan_btn.pack(side='left')
        self.pilot_btn=ttk.Button(buttons,text='Pilote fr + en',command=lambda:self.start('pilot'))
        self.pilot_btn.pack(side='left',padx=(6,0))
        self.world_btn=ttk.Button(buttons,text='Lancer / reprendre le monde',command=lambda:self.start('world'))
        self.world_btn.pack(side='left',padx=(6,0))
        self.stop_btn=ttk.Button(buttons,text='Interrompre',command=self.stop,state='disabled')
        self.stop_btn.pack(side='left',padx=(6,0))
        ttk.Button(buttons,text='Ouvrir le rapport',command=self.open_report).pack(side='right')
        ttk.Button(buttons,text='Explorer les preuves',command=self.explore).pack(side='right',padx=(0,7))
        self.verify_btn=ttk.Button(buttons,text='SHA-256 des exports',command=lambda:self.start('verify'))
        self.verify_btn.pack(side='right',padx=(0,7))
        ttk.Label(root,textvariable=self.status,foreground='#196e7a',wraplength=1040).pack(anchor='w')
        prog=ttk.Frame(root)
        prog.pack(fill='x',pady=(10,8))
        ttk.Label(prog,textvariable=self.phase,width=58).pack(side='left')
        self.progress=ttk.Progressbar(prog,maximum=100,mode='determinate')
        self.progress.pack(side='left',fill='x',expand=True)
        ttk.Label(root,text='Méthode : ancrages source v0.5 → relecture sélective d’archives → preuves structurées → exports JSONL candidats.',
                  wraplength=1030).pack(anchor='w',pady=(2,4))
        ttk.Label(root,text='Échantillons de provenance seulement; pas tous les sens. Aucun exactMatch, aucune approbation, aucune publication.',
                  foreground='#916723',wraplength=1030).pack(anchor='w',pady=(0,8))
        self.table=ttk.Treeview(root,columns=('key','value'),show='headings',height=6)
        self.table.heading('key',text='Élément')
        self.table.heading('value',text='État')
        self.table.column('key',width=260)
        self.table.column('value',width=760)
        self.table.pack(fill='x',pady=(0,12))
        ttk.Label(root,text='Journal de traitement',font=('Segoe UI',10,'bold')).pack(anchor='w')
        pane=ttk.Frame(root)
        pane.pack(fill='both',expand=True)
        self.log=tk.Text(pane,font=('Consolas',9),wrap='word',state='disabled')
        self.log.pack(side='left',fill='both',expand=True)
        sb=ttk.Scrollbar(pane,command=self.log.yview)
        sb.pack(side='right',fill='y')
        self.log.configure(yscrollcommand=sb.set)

    def root(self):return Path(self.data_root.get()).expanduser().resolve()

    def running(self):return self.worker is not None and self.worker.is_alive()

    def browse(self):
        directory=filedialog.askdirectory(initialdir=str(self.root()) if self.root().is_dir() else None)
        if directory:self.data_root.set(directory);self.inspect()

    def logline(self,text):
        self.log.configure(state='normal')
        self.log.insert('end',text.rstrip()+'\n')
        if int(self.log.index('end-1c').split('.')[0])>1800:
            self.log.delete('1.0','201.0')
        self.log.see('end')
        self.log.configure(state='disabled')

    def inspect(self):
        if self.running():return
        for item in self.table.get_children():self.table.delete(item)
        root=self.root()
        ready=ENGINE.is_file() and (root/INDEX).is_file() and (root/V05).is_file()
        for button in (self.plan_btn,self.pilot_btn,self.world_btn):
            button.configure(state='normal' if ready else 'disabled')
        self.verify_btn.configure(state='normal' if (root/OUT/'enrichment.sqlite3').is_file() else 'disabled')
        if not ready:
            self.status.set('Entrées v0.5 ou moteur manquants : vérifier l’extraction sur C: et les bases sur D:')
            return
        try:
            def ro(path):return sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=5)
            with ro(root/V05) as db:
                n_lang=db.execute('SELECT COUNT(*) FROM completed_languages').fetchone()[0]
                n_cand=db.execute('SELECT COUNT(*) FROM candidates').fetchone()[0]
            self.table.insert('','end',values=('Base v0.5',str(root/V05)))
            self.table.insert('','end',values=('Langues conciliées',f'{n_lang:,}'))
            self.table.insert('','end',values=('Clés candidates',f'{n_cand:,}'))
            enrich=root/OUT/'enrichment.sqlite3'
            if enrich.is_file():
                with ro(enrich) as db:
                    st=db.execute('SELECT COUNT(*) FROM staged_languages').fetchone()[0]
                    sources=dict(db.execute('SELECT status,COUNT(*) FROM source_progress GROUP BY status'))
                    evidences=db.execute('SELECT COUNT(*) FROM evidence').fetchone()[0]
                self.table.insert('','end',values=('Langues préparées',f'{st:,}/{n_lang:,}'))
                self.table.insert('','end',values=('Sources',str(sources)))
                self.table.insert('','end',values=('Preuves capturées',f'{evidences:,}'))
            self.status.set('Prêt : sources lues sur D:, résultats candidats séparés; libre sur D: à surveiller.')
        except (OSError,sqlite3.Error) as exc:
            self.status.set('Base SQLite inaccessible : '+str(exc))

    def start(self,mode):
        if self.running():return
        if mode=='world' and not messagebox.askyesno(TITLE,'Analyser les archives compressées et les preuves ancrées pour toutes les langues ?\n\nLe traitement est massif, reprenable et peut occuper plusieurs Go sur D:. Aucun fichier canonique n’est modifié.'):
            return
        self.progress['value']=0
        self.phase.set('Démarrage…')
        for b in (self.plan_btn,self.pilot_btn,self.world_btn,self.check_btn,self.verify_btn):b.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.logline('=== '+{'plan':'Plan','pilot':'Pilote fr/en','world':'Enrichissement mondial','verify':'Vérification SHA-256'}[mode]+' ===')
        self.worker=threading.Thread(target=self.execute,args=(mode,str(self.root())),daemon=True)
        self.worker.start()

    def execute(self,mode,root):
        exe=Path(sys.executable)
        if os.name=='nt' and exe.name.lower()=='pythonw.exe':
            alt=exe.with_name('python.exe')
            if alt.exists():exe=alt
        cmd=[str(exe),'-u',str(ENGINE), 'plan' if mode=='plan' else 'verify' if mode=='verify' else 'run','--data-root',root]
        if mode=='pilot':cmd.extend(['--languages','fr,en'])
        try:
            self.proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                encoding='utf-8',errors='replace',text=True,bufsize=1,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            for line in self.proc.stdout:
                self.events.put(('line',line.rstrip()))
            self.events.put(('done',self.proc.wait()))
        except Exception as ex:self.events.put(('error',str(ex)))
        finally:self.proc=None

    def poll(self):
        try:
            for _ in range(200):
                typ,value=self.events.get_nowait()
                if typ=='line':
                    if value.startswith('STAGE|'):
                        parts=value.split('|',4)
                        self.phase.set(f'Préparation des ancrages : langue {parts[1]}/{parts[2]}')
                    elif value.startswith('SOURCE|'):
                        _,i,total,label=value.split('|',3)
                        self.phase.set(f'Source {i}/{total} : {label}')
                        self.progress['value']=min(100,(int(i)-1)/max(1,int(total))*100)
                    elif value.startswith('EXPORT|'):
                        self.logline('Export : '+value)
                    elif value.startswith('PROGRESS|'):
                        self.phase.set('Lecture archive : '+value)
                    else:self.logline(value)
                if typ in ('done','error'):
                    self.stop_btn.configure(state='disabled')
                    self.phase.set('Terminé' if typ=='done' and value==0 else 'Interrompu ou erreur')
                    self.logline('=== '+('Code de sortie : '+str(value) if typ=='done' else 'Erreur : '+value)+' ===')
                    self.win.after(300,self.inspect)
        except queue.Empty:pass
        self.win.after(130,self.poll)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.logline('Interruption : les checkpoints de lots déjà validés restent sur D:.')
        self.stop_btn.configure(state='disabled')

    def open_report(self):
        p=self.root()/OUT/'RAPPORT_ENRICHISSEMENT.md'
        if not p.is_file():
            messagebox.showinfo(TITLE,'Aucun rapport encore généré.');return
        if os.name=='nt':os.startfile(str(p))
        else:messagebox.showinfo(TITLE,str(p))

    def explore(self):
        path=self.root()/OUT/'enrichment.sqlite3'
        if not path.is_file():
            messagebox.showinfo(TITLE,'Lancer le pilote avant d’explorer les preuves.');return
        win=tk.Toplevel(self.win)
        win.title('Preuves extraites — non approuvées')
        win.geometry('1000x700')
        root=ttk.Frame(win,padding=14);root.pack(fill='both',expand=True)
        ttk.Label(root,text='Preuves lexicales ancrées — aucune équivalence de sens automatique',
                  font=('Segoe UI',12,'bold')).pack(anchor='w')
        bar=ttk.Frame(root);bar.pack(fill='x',pady=8)
        lang=tk.StringVar(value='fr');search=tk.StringVar(value='')
        ttk.Label(bar,text='Langue').pack(side='left')
        ttk.Entry(bar,textvariable=lang,width=9).pack(side='left',padx=7)
        ttk.Label(bar,text='Début de graphie').pack(side='left')
        ttk.Entry(bar,textvariable=search,width=24).pack(side='left',padx=7)
        rows=ttk.Treeview(root,columns=('key','family','result'),show='headings',height=13)
        for k,title,w in (('key','Graphie',300),('family','Famille',140),('result','Statut',150)):
            rows.heading(k,text=title);rows.column(k,width=w)
        rows.pack(fill='x',pady=6)
        text=tk.Text(root,font=('Consolas',9),wrap='word')
        text.pack(fill='both',expand=True)
        selected={}
        def load():
            for i in rows.get_children():rows.delete(i)
            text.delete('1.0','end');selected.clear()
            language=lang.get().strip().lower()
            prefix=search.get().strip().casefold()
            if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,39}',language):
                messagebox.showerror(TITLE,'Langue invalide',parent=win);return
            recon=self.root()/V05
            try:
                con=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=5)
                source=sqlite3.connect(recon.as_uri()+'?mode=ro',uri=True,timeout=5)
                try:
                    query='SELECT candidate_id,lemma_key FROM candidates WHERE language=?'
                    params=[language]
                    if prefix:query+=' AND lemma_key>=? AND lemma_key<?';params.extend((prefix,prefix+'\U0010ffff'))
                    query+=' ORDER BY lemma_key LIMIT 100'
                    for cid,key in source.execute(query,params):
                        evs=list(con.execute('SELECT family,status,payload_json FROM evidence WHERE candidate_id=? ORDER BY source_id,source_line',(cid,)))
                        if not evs:continue
                        for family,status,payload in evs:
                            item=rows.insert('','end',values=(key,family,status))
                            selected[item]=payload
                finally:con.close();source.close()
            except Exception as ex:messagebox.showerror(TITLE,str(ex),parent=win)
        def show(_event=None):
            ids=rows.selection()
            if not ids:return
            data=json.loads(selected[ids[0]])
            text.delete('1.0','end')
            text.insert('end',json.dumps(data,ensure_ascii=False,indent=2))
        rows.bind('<<TreeviewSelect>>',show)
        ttk.Button(bar,text='Chercher',command=load).pack(side='left',padx=7)
        load()

    def close(self):
        if self.running():
            messagebox.showwarning(TITLE,'Traitement actif : utiliser Interrompre avant de fermer.');return
        self.win.destroy()


def main():
    w=tk.Tk()
    ttk.Style(w).theme_use('clam')
    App(w)
    w.mainloop()

if __name__=='__main__':main()
