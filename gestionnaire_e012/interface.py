"""Interface E2-R2 : appels explicites aux lecteurs et outils natifs."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import json, os, queue, subprocess, sys, threading
from pathlib import Path

NAV = ('Accueil','Ressources','Langues','Production','Publication','Diagnostics','Maintenance')
BG='#f1f4f7'; NAVBG='#183541'; INK='#1c303c'; MUTED='#536775'; ACCENT='#176b79'; WHITE='#ffffff'

STATES={'DECLARED_COMPLETE':'Déclaré terminé','PRESENT_NOT_VALIDATED':'Présent, non validé','MANIFEST_MATCHES_METADATA':'Manifeste concordant, lecture à vérifier','SIDECARS_NOT_FOUND':'Fichiers non trouvés','COMPLETE':'Complet (déclaré)','FOUND_IN_COMPACT':'Trouvé dans le compact','FOUND_IN_LOCAL_DUMP':'Trouvé dans le dump local','NOT_FOUND_IN_Q_LOCATOR':'Absent du localisateur Q','NOT_FOUND_IN_COMPACT':'Absent du compact'}
LANG_NAMES=dict(fr='Français',en='Anglais',es='Espagnol',it='Italien',fi='Finnois',de='Allemand',af='Afrikaans',da='Danois',et='Estonien',nl='Néerlandais',nn='Norvégien nynorsk',no='Norvégien (historique)',pt='Portugais',sv='Suédois')
def state(x):return STATES.get(x,x)

def number(x):
    try: return '—' if x is None else f'{int(x):,}'.replace(',',' ')
    except (ValueError,TypeError): return '—'
def gib(x): return '—' if x is None else f'{x/1024**3:,.2f} Gio'.replace(',',' ').replace('.',',')

class Window:
    def __init__(self,root,api):
        self.root,self.api=root,api; self.page='Accueil'; self.report=None; self.busy=False; self.processes={}; self.last_lookup=None; self.search_id='Q2'; self.search_lang='fr,en,es,it,fi,de'
        root.title('EncyKlopedia — Gestionnaire E2–E3 R3');root.geometry('1150x760');root.minsize(860,570);root.configure(bg=BG)
        style=ttk.Style(root);style.theme_use('clam');style.configure('TButton',font=('Segoe UI',10),padding=(10,6));style.configure('Treeview',font=('Segoe UI',10),rowheight=29,background=WHITE,fieldbackground=WHITE,foreground=INK);style.configure('Treeview.Heading',font=('Segoe UI',10,'bold'),padding=6);style.configure('TEntry',padding=5)
        side=tk.Frame(root,bg=NAVBG,width=205);side.pack(side='left',fill='y');side.pack_propagate(False)
        tk.Label(side,text='EncyKlopedia',font=('Segoe UI',19,'bold'),bg=NAVBG,fg=WHITE).pack(anchor='w',padx=15,pady=(24,0))
        tk.Label(side,text='Centre de gestion',font=('Segoe UI',10),bg=NAVBG,fg='#b7d0d8').pack(anchor='w',padx=16,pady=(0,30))
        self.nav={}
        for name in NAV:
            b=tk.Button(side,text=name,anchor='w',font=('Segoe UI',11),bd=0,padx=18,pady=10,bg=NAVBG,fg=WHITE,activebackground=ACCENT,activeforeground=WHITE,command=lambda n=name:self.navigate(n));b.pack(fill='x',padx=8,pady=2);self.nav[name]=b
        tk.Label(side,text='Local d’abord\nCandidats privés',justify='left',bg=NAVBG,fg='#b7d0d8',font=('Segoe UI',10)).pack(side='bottom',anchor='w',padx=16,pady=22)
        main=tk.Frame(root,bg=BG);main.pack(side='left',fill='both',expand=True)
        bar=tk.Frame(main,bg=WHITE,padx=20,pady=12);bar.pack(fill='x')
        self.header=tk.Label(bar,bg=WHITE,fg=INK,font=('Segoe UI',20,'bold'));self.header.pack(side='left')
        self.refresh_button=ttk.Button(bar,text='Actualiser les états',command=self.refresh);self.refresh_button.pack(side='right')
        self.status=tk.StringVar(value='Aucune lecture de données lourdes au démarrage. Actualiser pour relever les métadonnées.')
        tk.Label(main,textvariable=self.status,bg=BG,fg=MUTED,font=('Segoe UI',10),anchor='w',justify='left',wraplength=800,padx=20,pady=8).pack(side='bottom',fill='x')
        area=tk.Frame(main,bg=BG);area.pack(fill='both',expand=True,padx=18,pady=12)
        self.canvas=tk.Canvas(area,bg=BG,highlightthickness=0);scroll=ttk.Scrollbar(area,orient='vertical',command=self.canvas.yview);scroll.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True);self.canvas.configure(yscrollcommand=scroll.set)
        self.body=tk.Frame(self.canvas,bg=BG);self.window=self.canvas.create_window((0,0),window=self.body,anchor='nw');self.body.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')));self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.window,width=e.width))
        root.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units') if e.delta else None)
        root.bind('<Button-4>',lambda e:self.canvas.yview_scroll(-1,'units'));root.bind('<Button-5>',lambda e:self.canvas.yview_scroll(1,'units'))
        self.navigate('Accueil')
    def navigate(self,page):
        self.page=page;self.header.configure(text=page)
        for n,b in self.nav.items(): b.configure(bg=ACCENT if n==page else NAVBG)
        self.render();self.canvas.yview_moveto(0)
    def label(self,parent,text,large=False,muted=False):
        return tk.Label(parent,text=text,bg=WHITE,fg=MUTED if muted else INK,font=('Segoe UI',15 if large else 10,'bold' if large else 'normal'),justify='left',anchor='w',wraplength=620)
    def panel(self,title,detail=None):
        f=tk.Frame(self.body,bg=WHITE,padx=15,pady=13,highlightthickness=1,highlightbackground='#dce4e9');f.pack(fill='x',pady=(0,10),padx=1)
        self.label(f,title,True).pack(fill='x')
        if detail:self.label(f,detail,muted=True).pack(fill='x',pady=(4,5))
        return f
    def text(self,p,text):self.label(p,text).pack(fill='x',pady=3)
    def button(self,p,text,cmd):ttk.Button(p,text=text,command=cmd).pack(anchor='w',pady=(5,0))
    def details(self,title,data):
        w=tk.Toplevel(self.root);w.title(title);w.geometry('850x600');f=ttk.Frame(w,padding=10);f.pack(fill='both',expand=True);s=ttk.Scrollbar(f);s.pack(side='right',fill='y');t=tk.Text(f,wrap='word',yscrollcommand=s.set,font=('Consolas',10));t.pack(fill='both',expand=True);s.configure(command=t.yview);t.insert('1.0',json.dumps(data,ensure_ascii=False,indent=2));t.configure(state='disabled')
    def async_run(self,fn,done):
        if self.busy:return
        self.busy=True;self.refresh_button.configure(state='disabled');self.status.set('Lecture locale en cours…');q=queue.Queue()
        def work():
            try:q.put((True,fn()))
            except Exception as e:q.put((False,str(e)))
        def poll():
            try:ok,value=q.get_nowait()
            except queue.Empty:self.root.after(100,poll);return
            self.busy=False;self.refresh_button.configure(state='normal')
            if ok:self.status.set('Lecture terminée · métadonnées / observations locales, non qualification.');done(value)
            else:self.status.set('Lecture interrompue : '+value);messagebox.showerror('Lecture impossible',value,parent=self.root)
        threading.Thread(target=work,daemon=True).start();self.root.after(100,poll)
    def refresh(self):
        self.async_run(self.api['dashboard'],self.receive)
    def receive(self,r):self.report=r;self.render()
    def open_folder(self,p):
        p=Path(p)
        try:os.startfile(str(p if p.is_dir() else p.parent))
        except (AttributeError,OSError) as e:messagebox.showerror('Ouverture impossible',str(e),parent=self.root)
    def launch(self,row):
        p=Path(row['resolved']);key=row['id']
        if row['kind']!='python' or not p.is_file():return
        if key in self.processes and self.processes[key].poll() is None:messagebox.showinfo('Déjà ouvert','Ce gestionnaire a déjà lancé cet outil.',parent=self.root);return
        if not messagebox.askyesno('Ouverture explicite',row['label']+'\n'+str(p)+'\n\nL’outil natif peut modifier son propre espace. Vérifier qu’il n’est pas déjà ouvert ailleurs. Continuer ?',parent=self.root):return
        try:self.processes[key]=subprocess.Popen([sys.executable,str(p)],cwd=str(p.parent))
        except OSError as e:messagebox.showerror('Démarrage impossible',str(e),parent=self.root)
    def tools(self,sections,ids=None):
        for row in self.api['inventory']():
            if row['section'] not in sections or (ids is not None and row['id'] not in ids):continue
            f=self.panel(row['label'],row['description']);self.text(f,('Fichier présent' if row['presence']=='PRESENT' else 'Fichier absent')+' · fonctionnement non vérifié')
            b=tk.Frame(f,bg=WHITE);b.pack(fill='x');exists=row['presence']=='PRESENT'
            ttk.Button(b,text='Dossier',state='normal' if exists else 'disabled',command=lambda p=row['resolved']:self.open_folder(p)).pack(side='left')
            if row['kind']=='python':ttk.Button(b,text='Ouvrir outil',state='normal' if exists else 'disabled',command=lambda r=row:self.launch(r)).pack(side='left',padx=8)
    def render(self):
        for w in self.body.winfo_children():w.destroy()
        r=self.report or {}; wd=r.get('wikidata',{}); lex=r.get('lexical',{}); fast=r.get('fast_access',{})
        if self.page=='Accueil':
            f=self.panel('Vue générale','Valeurs lues localement après actualisation. Aucun chiffre de démonstration.')
            g=tk.Frame(f,bg=WHITE);g.pack(fill='x',pady=6)
            for i,(label,val) in enumerate([('Branches UNESCO déclarées',number(r.get('branch_labels_declared'))),('Entités traitées (méta)',number(wd.get('meta',{}).get('processed_entities'))),('Observations diK (méta lues)',number(lex.get('observations_metadata_total'))),('Espace libre des données',gib(r.get('disk_free_bytes')))]):
                box=tk.Frame(g,bg='#edf4f5',padx=12,pady=12);box.grid(row=i//2,column=i%2,sticky='nsew',padx=4,pady=4);g.columnconfigure(i%2,weight=1);tk.Label(box,text=label,bg='#edf4f5',fg=MUTED,font=('Segoe UI',10),wraplength=235,justify='left').pack(anchor='w');tk.Label(box,text=val,bg='#edf4f5',fg=INK,font=('Segoe UI',21,'bold')).pack(anchor='w')
            f=self.panel('État des ressources');self.text(f,'Wikidata : '+state(wd.get('state','Non relevé')));self.text(f,'Outils présents : '+number(r.get('tools_present'))+' / '+number(r.get('tools_total'))+' (présence uniquement)');self.text(f,'Langues diK : '+number(lex.get('languages_metadata_read'))+' métadonnées lues');self.text(f,'Accès rapide : '+state(fast.get('state','Non relevé')))
            f=self.panel('Continuer le travail','Les moteurs restent propriétaires de leurs opérations.');self.button(f,'Consulter les ressources Wikidata',lambda:self.navigate('Ressources'));self.button(f,'Examiner les dictionnaires',lambda:self.navigate('Langues'));self.button(f,'Accéder à la production',lambda:self.navigate('Production'))
        elif self.page=='Ressources':
            f=self.panel('Wikidata local','Index compact existant — consultation exacte Q/P. Aucun accès réseau ni extraction du dump.')
            self.text(f,'État : '+state(wd.get('state','Non relevé'))+' · Langues déclarées : '+str(wd.get('meta',{}).get('languages','—')));self.text(f,'Dump : '+gib(wd.get('dump',{}).get('bytes'))+' · intégrité non recalculée')
            if wd:self.button(f,'Rapport Wikidata',lambda:self.details('Wikidata',wd))
            f=self.panel('Consulter une identité','Ex. Q2 ou P31. Champ langues vide = toutes les langues réellement présentes dans l’index ; aucun repli.')
            b=tk.Frame(f,bg=WHITE);b.pack(fill='x',pady=6);self.wid=ttk.Entry(b,width=13);self.wid.insert(0,self.search_id);self.wid.pack(side='left');self.lang=ttk.Entry(b,width=28);self.lang.insert(0,self.search_lang);self.lang.pack(side='left',padx=8);ttk.Button(b,text='Index compact Q/P',command=self.search).pack(side='left');
            if 'lookup_world' in self.api:self.button(f,'Dump mondial Q · toutes langues si champ vide',lambda:self.search(world=True))
            if self.last_lookup:self.show_result(f,self.last_lookup)
            f=self.panel('Accès rapide au dump','Manifeste et tailles contrôlés à l’actualisation ; lecture Q explicite uniquement. Aucun repli ni reconstruction.')
            self.text(f,'État : '+state(fast.get('state','Non relevé'))+' · indexed_bzip2 : '+('environnement isolé présent (à tester)' if fast.get('isolated_runtime') else 'présent' if fast.get('indexed_bzip2') else 'absent' if fast else 'non relevé'))
            if fast.get('manifest_check',{}).get('q_items'):self.text(f,number(fast['manifest_check']['q_items'])+' Q localisés (manifeste)')
            if fast:self.button(f,'Emplacements et fichiers',lambda:self.details('Accès rapide',fast))
            f=self.panel('Autres sources','Les index Wikipédia et UNESCO restent gérés par leurs outils natifs.');self.button(f,'Ouvrir le dossier des données',lambda:self.open_folder(self.api['data']))
        elif self.page=='Langues':
            g=self.panel('Patrimoine lexical EncyKlopedia','Rapport historique de l’entrepôt, distinct de la collection diK. Les codes observés ne sont pas des dictionnaires complets.')
            er=lex.get('encyk_report',{});tot=er.get('totals',{}) or {}
            for k,title in [('lemma_observations','Lemmes'),('sense_observations','Sens'),('form_observations','Formes'),('translation_observations','Traductions')]:self.text(g,title+' : '+number(tot.get(k)))
            self.text(g,'Codes observés : '+number(er.get('number_of_observed_language_codes'))+' · Sources : '+number(er.get('number_of_source_files'))+' · Rapport : '+str(er.get('generated_at','non relevé')))
            f=self.panel('Dictionnaires locaux diK','Les compteurs sont des observations, pas des sens uniques ou des traductions approuvées.')
            if lex:
                self.text(f,'Collection : '+state(lex.get('dik_declared_status','non vérifiée'))+' · '+number(lex.get('observations_metadata_total'))+' observations dans les métadonnées lues')
                cols=('lang','status','obs','manifest'); tree=ttk.Treeview(f,columns=cols,show='headings',height=min(14,max(3,len(lex.get('languages',[])))))
                for col,title,width in zip(cols,('Langue','État SQLite','Observations','Manifest'),(70,155,125,110)):tree.heading(col,text=title);tree.column(col,width=width,anchor='e' if col=='obs' else 'w')
                for x in lex.get('languages',[]):tree.insert('','end',values=(LANG_NAMES.get(x['language'],x['language'])+' ('+x['language']+')',state(x.get('status','Non vérifié')),number(x.get('observations')),'Concordant' if x.get('manifest_matches') else 'À vérifier'))
                tree.pack(fill='x',pady=5);self.button(f,'Rapport lexical et provenance',lambda:self.details('Ressources linguistiques',lex))
            else:self.text(f,'Actualiser pour lire les métadonnées de la collection.')
            self.tools(('Ressources',))
        elif self.page=='Production':self.tools(('Production',))
        elif self.page=='Publication':self.tools(('Publication',));f=self.panel('Frontière de publication','Aucune admission, promotion canonique ou publication depuis le gestionnaire.')
        elif self.page=='Diagnostics':
            f=self.panel('Diagnostics locaux','Les diagnostics existants restent indépendants.');
            for w in wd.get('warnings',[])+lex.get('warnings',[]):self.text(f,w)
            if r:self.button(f,'Rapport complet',lambda:self.details('Diagnostic',r))
            self.tools(('Administration',),('diag','branch-audit'))
        elif self.page=='Maintenance':
            f=self.panel('Maintenance conservatrice','Aucune modification des bases, aucune restauration ou mise à jour automatique.');self.button(f,'Reçus des overlays',lambda:self.open_folder(Path.home()/'ENCYK_OVERLAY_RECEIPTS'));self.tools(('Administration',),('launcher',))
    def search(self,world=False):
        wid=self.wid.get().strip(); raw=self.lang.get().strip(); self.search_id=wid;self.search_lang=raw; langs=[s.strip() for s in raw.split(',')] if raw else None
        def done(r):
            self.last_lookup=r
            if self.page=='Ressources':self.render()
            self.details('Identité '+wid,r)
        if world and not messagebox.askyesno('Lecture locale explicite','Lecture Q du dump via les index dérivés locaux. Pas de réseau ni de reconstruction. Continuer ?',parent=self.root):return
        self.async_run(lambda:self.api['lookup_world' if world else 'lookup'](wid,langs),done)
    def show_result(self,f,r):
        self.text(f,r['external_id']+' · '+state(r['state'])+' · '+str(r.get('dump_file') or 'source non datée'))
        for row in r.get('rows',[]):self.text(f,row['language']+' : '+str(row['label'] or 'libellé non disponible')+' · '+str(len(row['names']))+' noms indexés')
        if r.get('not_observed_in_index'):self.text(f,'Non observées dans cet index : '+', '.join(r['not_observed_in_index']))
        self.button(f,'Détail de la dernière consultation',lambda:self.details('Identité',r))

def gui(api):
    root=tk.Tk();Window(root,api);root.mainloop()
