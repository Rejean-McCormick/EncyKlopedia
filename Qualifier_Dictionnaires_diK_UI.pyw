#!/usr/bin/env python3
"""EncyKlopedia → diK v0.7 — local private candidate qualification (Tkinter)."""
from __future__ import annotations

import json
import os
import queue
import sqlite3
import subprocess
import sys
import threading
import unicodedata
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

BASE = Path(__file__).resolve().parent
ENGINE = BASE / 'tools' / 'dictionary-harvester' / 'dik_qualification.py'
DEFAULT = os.environ.get('ENCYK_DATA_ROOT', r'D:\EncyKlopedia')
OUT = Path('30_working/lexical/harvester/dik-qualification-v1')
IN_DB = Path('30_working/lexical/harvester/dik-enrichment-v1/enrichment.sqlite3')
TITLE = 'EncyKlopedia → diK — Qualification candidate v0.7'


def ro(db):
    x = sqlite3.connect(db.as_uri()+'?mode=ro',uri=True,timeout=20)
    x.execute('PRAGMA query_only=ON')
    return x


class App:
    def __init__(self,win):
        self.win=win
        win.title(TITLE);win.geometry('1200x810');win.minsize(900,625)
        self.rootvar=tk.StringVar(value=DEFAULT)
        self.status=tk.StringVar(value='Code sur C: • données sur D: • staging non approuvé')
        self.progress_label=tk.StringVar(value='Prêt')
        self.events=queue.Queue();self.worker=None;self.proc=None
        self.create()
        win.after(100,self.poll)
        win.after(300,self.inspect)
        win.protocol('WM_DELETE_WINDOW',self.close)

    def root(self):return Path(self.rootvar.get()).expanduser().resolve()
    def running(self):return bool(self.worker and self.worker.is_alive())
    def out(self):return self.root()/OUT

    def create(self):
        shell=ttk.Frame(self.win,padding=16);shell.pack(fill='both',expand=True)
        ttk.Label(shell,text='DIK-LEX-1 · Qualification et gouvernance v0.7',font=('Segoe UI',17,'bold')).pack(anchor='w')
        ttk.Label(shell,text='Classement explicable • homographies ambiguës • licences bloquées • notes humaines non normatives',foreground='#526473').pack(anchor='w',pady=(2,4))
        ttk.Label(shell,text='AUCUNE équivalence acceptée, aucun KQ/KP, aucune publication et aucune écriture dans diK.',foreground='#a05b16').pack(anchor='w',pady=(0,11))
        path=ttk.Frame(shell);path.pack(fill='x',pady=(0,12))
        ttk.Label(path,text='Données sur D:').pack(side='left')
        ttk.Entry(path,textvariable=self.rootvar).pack(side='left',fill='x',expand=True,padx=8)
        ttk.Button(path,text='Parcourir…',command=self.browse).pack(side='left')
        self.check=ttk.Button(path,text='Vérifier',command=self.inspect);self.check.pack(side='left',padx=(7,0))
        buttons=ttk.Frame(shell);buttons.pack(fill='x',pady=(0,8))
        self.buttons=[]
        for label,mode in [('Plan','plan'),('Pilote fr/en','pilot'),('Lancer / reprendre le monde','world'),('Vérifier SHA-256','verify')]:
            w=ttk.Button(buttons,text=label,command=lambda m=mode:self.start(m))
            w.pack(side='left',padx=(0,7));self.buttons.append(w)
        self.stop_btn=ttk.Button(buttons,text='Interrompre',command=self.stop,state='disabled');self.stop_btn.pack(side='left')
        ttk.Button(buttons,text='Ouvrir le rapport',command=self.report).pack(side='right')
        ttk.Label(shell,textvariable=self.status,foreground='#186d78',wraplength=1150).pack(anchor='w',pady=(1,9))
        p=ttk.Frame(shell);p.pack(fill='x')
        ttk.Label(p,textvariable=self.progress_label,width=56).pack(side='left')
        self.progress=ttk.Progressbar(p,maximum=100);self.progress.pack(side='left',fill='x',expand=True)
        self.tab=ttk.Notebook(shell);self.tab.pack(fill='both',expand=True,pady=(12,0))
        self.summary_tab=ttk.Frame(self.tab,padding=10)
        self.cand_tab=ttk.Frame(self.tab,padding=10)
        self.lic_tab=ttk.Frame(self.tab,padding=10)
        self.log_tab=ttk.Frame(self.tab,padding=10)
        for frame,label in [(self.summary_tab,'Tableau de bord'),(self.cand_tab,'Explorer et annoter les candidats'),
                            (self.lic_tab,'Licences — revue manuelle'),(self.log_tab,'Journal')]:
            self.tab.add(frame,text=label)
        self.info=ttk.Treeview(self.summary_tab,columns=('item','value'),show='headings',height=12)
        for col,t,w in [('item','Indicateur',310),('value','Valeur',740)]:
            self.info.heading(col,text=t);self.info.column(col,width=w)
        self.info.pack(fill='both',expand=True)
        ttk.Label(self.summary_tab,text='Tous les résultats sont des candidats. Les notes de revue n’équivalent pas aux décisions diK/Framework.',foreground='#925d20',wraplength=980).pack(anchor='w',pady=8)
        # Candidates explorer: bounded SQL paging, never load 1.55M rows into Tk.
        search=ttk.Frame(self.cand_tab);search.pack(fill='x',pady=(0,8))
        self.lang=tk.StringVar(value='fr');self.prefix=tk.StringVar();self.tier=tk.StringVar(value='Toutes')
        ttk.Label(search,text='Langue').pack(side='left')
        ttk.Entry(search,textvariable=self.lang,width=12).pack(side='left',padx=(4,10))
        ttk.Label(search,text='Graphie préfixe').pack(side='left')
        ttk.Entry(search,textvariable=self.prefix,width=26).pack(side='left',padx=(4,10))
        ttk.Label(search,text='Catégorie').pack(side='left')
        ttk.Combobox(search,textvariable=self.tier,width=37,state='readonly',values=[
            'Toutes','source_evidence_incomplete','possible_lexeme_or_normalization_ambiguity',
            'pos_mapping_review','sense_comparison_queue','limited_sense_evidence','lemma_morphology_only']).pack(side='left',padx=(4,10))
        ttk.Button(search,text='Chercher (100)',command=self.search).pack(side='left')
        self.candidates=ttk.Treeview(self.cand_tab,columns=('priority','key','tier','id'),show='headings',height=11)
        for col,label,w in [('priority','Priorité',75),('key','Graphie',270),('tier','Classement de revue',375),('id','Référence candidate',350)]:
            self.candidates.heading(col,text=label);self.candidates.column(col,width=w)
        self.candidates.pack(fill='both',expand=True)
        self.candidates.bind('<<TreeviewSelect>>',self.show_detail)
        self.details=tk.Text(self.cand_tab,font=('Consolas',9),height=12,wrap='word')
        self.details.pack(fill='both',expand=True,pady=(8,6));self.details.configure(state='disabled')
        action=ttk.Frame(self.cand_tab);action.pack(fill='x')
        ttk.Button(action,text='Annoter le candidat sélectionné',command=self.annotate_candidate).pack(side='left')
        ttk.Label(action,text='Notes locales append-only, jamais accepted/exactMatch',foreground='#86551a').pack(side='left',padx=15)
        # Licenses, one row per original source; no automatic legal decision.
        licbar=ttk.Frame(self.lic_tab);licbar.pack(fill='x',pady=(0,8))
        ttk.Button(licbar,text='Afficher les 210 sources',command=self.load_licenses).pack(side='left')
        ttk.Button(licbar,text='Annoter cette source',command=self.annotate_license).pack(side='left',padx=8)
        ttk.Label(licbar,text='Statut par défaut : droits inconnus, non publiable',foreground='#8b5c23').pack(side='left',padx=8)
        self.licenses=ttk.Treeview(self.lic_tab,columns=('id','family','edition','path'),show='headings',height=18)
        for col,label,w in [('id','ID',70),('family','Famille',110),('edition','Édition',180),('path','Fichier original sur D:',760)]:
            self.licenses.heading(col,text=label);self.licenses.column(col,width=w)
        self.licenses.pack(fill='both',expand=True)
        self.log=tk.Text(self.log_tab,font=('Consolas',9),wrap='word',state='disabled')
        self.log.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(self.log_tab,command=self.log.yview);scroll.pack(side='right',fill='y')
        self.log.configure(yscrollcommand=scroll.set)

    def browse(self):
        d=filedialog.askdirectory(initialdir=str(self.root()) if self.root().is_dir() else None)
        if d:self.rootvar.set(d);self.inspect()

    def logline(self,line):
        self.log.configure(state='normal');self.log.insert('end',line+'\n')
        if int(self.log.index('end-1c').split('.')[0])>1400:self.log.delete('1.0','201.0')
        self.log.see('end');self.log.configure(state='disabled')

    def inspect(self):
        if self.running():return
        for c in self.info.get_children():self.info.delete(c)
        root=self.root()
        ready=ENGINE.is_file() and (root/IN_DB).is_file() and (root/'10_sources/lexical').is_dir()
        for w in self.buttons[:3]:w.configure(state='normal' if ready else 'disabled')
        self.buttons[3].configure(state='normal' if (self.out()/'qualification.sqlite3').is_file() else 'disabled')
        if not ready:
            self.status.set('Données v0.6 ou moteur sur C: absents. Vérifier le dépôt et D:\\EncyKlopedia.');return
        self.info.insert('','end',values=('v0.6','Présente (lecture seule)'))
        self.info.insert('','end',values=('Données',str(root)))
        state=self.out()/'qualification.sqlite3'
        if state.is_file():
            try:
                with ro(state) as db:
                    langs=db.execute('SELECT COUNT(*) FROM completed_languages').fetchone()[0]
                    total=db.execute('SELECT COALESCE(SUM(candidates),0) FROM completed_languages').fetchone()[0]
                    review=db.execute('SELECT COUNT(*) FROM review_events').fetchone()[0]
                    licenses=db.execute('SELECT COUNT(*) FROM license_events').fetchone()[0]
                    tiers=dict(db.execute('SELECT tier,COUNT(*) FROM candidates GROUP BY tier'))
                for k,v in [('Langues traitées',f'{langs:,} / 6 848 (si corpus inchangé)'),('Candidats classés',f'{total:,}'),
                            ('Annotations lexicales',review),('Notes sur les licences',licenses),('Classes',str(tiers))]:
                    self.info.insert('','end',values=(k,v))
                self.status.set('Catalogue candidat consultable; vérification SHA-256 recommandée après la fin du traitement.')
            except (OSError,sqlite3.Error) as exc:self.status.set('Index v0.7 inaccessible : '+str(exc))
        else:self.status.set('Prêt pour pilote ou traitement mondial. Aucune donnée v0.7 encore écrite.')

    def start(self,mode):
        if self.running():return
        if mode=='world' and not messagebox.askyesno(TITLE,'Traiter toutes les langues v0.6 ?\nPeut occuper plusieurs Go sur D: et se reprend par langue.\n\nAucune fusion, acceptation de droits ou publication.'):
            return
        self.tab.select(self.log_tab);self.progress['value']=0;self.progress_label.set('Démarrage…')
        for w in self.buttons:w.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.logline('=== '+{'plan':'PLAN','pilot':'PILOTE FR/EN','world':'QUALIFICATION MONDIALE','verify':'VÉRIFICATION SHA-256'}[mode]+' ===')
        self.worker=threading.Thread(target=self.execute,args=(mode,str(self.root())),daemon=True);self.worker.start()

    def execute(self,mode,root):
        exe=Path(sys.executable)
        if os.name=='nt' and exe.name.lower()=='pythonw.exe':
            x=exe.with_name('python.exe')
            if x.exists():exe=x
        cmd=[str(exe),'-u',str(ENGINE),'plan' if mode=='plan' else 'verify' if mode=='verify' else 'run','--data-root',root]
        if mode=='pilot':cmd+=['--languages','fr,en']
        try:
            self.proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                encoding='utf-8',errors='replace',text=True,bufsize=1,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            for line in self.proc.stdout:self.events.put(('line',line.rstrip()))
            self.events.put(('done',self.proc.wait()))
        except Exception as exc:self.events.put(('error',str(exc)))
        finally:self.proc=None

    def poll(self):
        try:
            for _ in range(200):
                typ,value=self.events.get_nowait()
                if typ=='line':
                    if value.startswith('QUALIFY|'):
                        fields=value.split('|',4)
                        self.progress_label.set(f'Langue {fields[1]}/{fields[2]} : {fields[3]} ({fields[4]})')
                        try:self.progress['value']=min(100,100*int(fields[1])/max(1,int(fields[2])))
                        except ValueError:pass
                    elif value.startswith('REVIEW|'):
                        self.progress_label.set('Classement en cours : '+value.split('|',2)[-1])
                    self.logline(value)
                elif typ=='done':
                    self.logline('=== Code de sortie : '+str(value)+' ===')
                    self.progress_label.set('Terminé' if value==0 else 'Arrêt / erreur')
                    self.stop_btn.configure(state='disabled');self.worker=None;self.inspect()
                elif typ=='error':
                    self.logline('ERREUR: '+value);self.progress_label.set('Erreur')
                    self.stop_btn.configure(state='disabled');self.worker=None;self.inspect()
        except queue.Empty:pass
        self.win.after(140,self.poll)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate();self.logline('Interruption demandée. Les langues déjà terminées restent enregistrées.')

    def close(self):
        if self.running():
            if not messagebox.askyesno(TITLE,'Interrompre le traitement en cours ?'):return
            self.stop()
        self.win.destroy()

    def search(self):
        for item in self.candidates.get_children():self.candidates.delete(item)
        path=self.out()/'qualification.sqlite3'
        if not path.is_file():messagebox.showinfo(TITLE,'Lancer le pilote ou la qualification mondiale d’abord.');return
        lang=self.lang.get().strip().lower();prefix=self.prefix.get().strip()
        try:
            if not lang or len(lang)>40:raise ValueError('Langue invalide')
            with ro(path) as db:
                sql='SELECT priority,lemma_key,tier,candidate_id FROM candidates WHERE language=?'
                params=[lang]
                if prefix:
                    # Search keys from v0.4 are NFKC+casefold; escape LIKE wildcards by avoiding LIKE.
                    search_key=unicodedata.normalize('NFKC',prefix).casefold()
                    sql+=' AND substr(lemma_key,1,?)=?';params.extend([len(search_key),search_key])
                if self.tier.get()!='Toutes':sql+=' AND tier=?';params.append(self.tier.get())
                sql+=' ORDER BY priority,lemma_key LIMIT 100'
                for row in db.execute(sql,params):self.candidates.insert('','end',values=row)
            self.status.set(f'Candidats affichés : {len(self.candidates.get_children())} (maximum 100), non normatifs.')
        except (sqlite3.Error,ValueError,OSError) as exc:messagebox.showerror(TITLE,str(exc))

    def chosen(self):
        selection=self.candidates.selection()
        return self.candidates.item(selection[0],'values')[3] if selection else None

    def show_detail(self,event=None):
        cid=self.chosen()
        if not cid:return
        try:
            with ro(self.out()/'qualification.sqlite3') as db:
                row=db.execute('SELECT summary_json FROM candidates WHERE candidate_id=?',(cid,)).fetchone()
                notes=list(db.execute('SELECT reviewer_id,disposition,rationale,created_at FROM review_events WHERE candidate_id=? ORDER BY seq DESC LIMIT 8',(cid,)))
            if not row:return
            view=json.dumps({'qualification':json.loads(row[0]),'human_annotations_not_normative':notes},ensure_ascii=False,indent=2)
            self.details.configure(state='normal');self.details.delete('1.0','end');self.details.insert('1.0',view);self.details.configure(state='disabled')
        except (OSError,sqlite3.Error) as exc:self.status.set('Erreur lecture candidate: '+str(exc))

    def note_dialog(self,kind,subject):
        if self.running():messagebox.showwarning(TITLE,'Arrêter ou terminer le traitement avant d’annoter.');return
        top=tk.Toplevel(self.win);top.title('Annotation locale non normative');top.geometry('670x390');top.transient(self.win);top.grab_set()
        ttk.Label(top,text='Cette annotation ne crée JAMAIS de décision diK acceptée ou de droit d’usage.',foreground='#975515',wraplength=620).pack(anchor='w',padx=14,pady=(13,6))
        ttk.Label(top,text='Référence : '+str(subject),wraplength=620).pack(anchor='w',padx=14)
        reviewer=tk.StringVar();choice=tk.StringVar(value='needs_more_evidence' if kind=='review' else 'needs_legal_review')
        for label,var in [('Identifiant du réviseur',reviewer)]:
            line=ttk.Frame(top);line.pack(fill='x',padx=14,pady=6)
            ttk.Label(line,text=label,width=25).pack(side='left');ttk.Entry(line,textvariable=var).pack(side='left',fill='x',expand=True)
        line=ttk.Frame(top);line.pack(fill='x',padx=14,pady=6)
        ttk.Label(line,text='Disposition',width=25).pack(side='left')
        choices=sorted({'needs_more_evidence','defer','reject_lexical_candidate','escalate_ambiguity','escalate_rights'} if kind=='review' else
                       {'needs_legal_review','source_license_claim_recorded','hold','needs_attribution_review'})
        ttk.Combobox(line,textvariable=choice,values=choices,state='readonly').pack(side='left',fill='x',expand=True)
        ttk.Label(top,text='Justification (obligatoire, 8 caractères min.)').pack(anchor='w',padx=14,pady=(8,2))
        txt=tk.Text(top,height=6,wrap='word');txt.pack(fill='both',expand=True,padx=14,pady=(0,6))
        url=tk.StringVar()
        if kind=='license':
            line=ttk.Frame(top);line.pack(fill='x',padx=14,pady=4)
            ttk.Label(line,text='URL de référence HTTPS',width=25).pack(side='left')
            ttk.Entry(line,textvariable=url).pack(side='left',fill='x',expand=True)
        def save():
            try:
                # Imported backend is local code from this overlay, not any network service.
                sys.path.insert(0,str(ENGINE.parent))
                from dik_qualification import append_event
                result=append_event(self.root(),kind=kind,subject=subject,reviewer=reviewer.get(),
                    disposition=choice.get(),rationale=txt.get('1.0','end').strip(),reference_url=url.get().strip() or None)
                messagebox.showinfo(TITLE,'Note conservée (non normative) : '+result['event_id'],parent=top)
                top.destroy();self.inspect();self.show_detail()
            except (ValueError,sqlite3.Error,OSError) as exc:messagebox.showerror(TITLE,str(exc),parent=top)
        ttk.Button(top,text='Enregistrer la note append-only',command=save).pack(side='right',padx=14,pady=10)

    def annotate_candidate(self):
        cid=self.chosen()
        if cid:self.note_dialog('review',cid)
        else:messagebox.showinfo(TITLE,'Sélectionner une ligne candidate.')

    def load_licenses(self):
        for item in self.licenses.get_children():self.licenses.delete(item)
        p=self.out()/'source_license_review_queue.csv'
        if not p.is_file():messagebox.showinfo(TITLE,'Lancer le pilote ou la qualification mondiale d’abord.');return
        import csv
        with p.open(encoding='utf-8',newline='') as f:
            for r in csv.DictReader(f):self.licenses.insert('','end',values=(r['source_id'],r['family'],r['edition'],r['source_path']))

    def annotate_license(self):
        sel=self.licenses.selection()
        if sel:self.note_dialog('license',int(self.licenses.item(sel[0],'values')[0]))
        else:messagebox.showinfo(TITLE,'Sélectionner une source à annoter.')

    def report(self):
        p=self.out()/'RAPPORT_QUALIFICATION.md'
        if not p.is_file():messagebox.showinfo(TITLE,'Rapport pas encore créé.');return
        if os.name=='nt':os.startfile(p)
        else:messagebox.showinfo(TITLE,str(p))


def main():
    win=tk.Tk()
    try:ttk.Style().theme_use('clam')
    except tk.TclError:pass
    App(win);win.mainloop()

if __name__=='__main__':main()
