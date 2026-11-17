# -*- coding: utf-8 -*-
"""Gestionnaire local de la bibliothèque Spek (Tkinter, aucun service réseau)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import traceback
import webbrowser
import threading
from datetime import datetime
from pathlib import Path

# Un .pyw ne dispose pas de console Windows. Rien ne doit échouer silencieusement.
def _log_path():
    root = Path(os.environ.get('LOCALAPPDATA') or tempfile.gettempdir()) / 'Spek' / 'TemplateManager'
    root.mkdir(parents=True, exist_ok=True)
    return root / 'launcher-errors.log'


def _show_fatal(title, detail):
    message = str(detail) + '\n\nJournal : ' + str(_log_path())
    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
            return
        except Exception:
            pass
    try:
        from tkinter import messagebox as _mb
        _mb.showerror(title, message)
    except Exception:
        print(title + ': ' + message, file=sys.stderr or sys.stdout)


def _record_error(message):
    try:
        with _log_path().open('a', encoding='utf-8') as fp:
            fp.write('\n[' + datetime.now().isoformat(timespec='seconds') + '] ' + message + '\n')
    except Exception:
        pass


try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog, ttk
except Exception as exc:
    _record_error('Tkinter indisponible: ' + traceback.format_exc())
    _show_fatal('Spek - Tkinter indisponible',
                'Cette installation de Python ne contient pas Tkinter.\n' + str(exc))
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent


def _repo_usable(folder):
    try:
        p = Path(folder).expanduser().resolve()
        return (p / 'spek' / 'core.py').is_file() and (p / 'spek' / 'template_manager.py').is_file() \
               and (p / 'template_library').is_dir() and (p / 'layouts').is_dir()
    except Exception:
        return False


def _find_repo():
    candidates = [ROOT, ROOT / 'Spek', ROOT.parent / 'Spek', Path.cwd(), Path.cwd() / 'Spek']
    if os.environ.get('SPEK_ROOT'):
        candidates.insert(0, Path(os.environ['SPEK_ROOT']))
    if sys.platform == 'win32':
        candidates.append(Path('C:/mycode/Kristal/Spek'))
    for path in candidates:
        if _repo_usable(path):
            return Path(path).resolve()
    chooser = tk.Tk()
    chooser.withdraw()
    try:
        messagebox.showinfo('Spek - emplacement du depot',
            'Le gestionnaire ne trouve pas les fichiers Spek a cote du lanceur.\n'
            'Choisis le dossier contenant spek/, layouts/ et template_library/.', parent=chooser)
        selected = filedialog.askdirectory(parent=chooser, title='Choisir le depot Spek', initialdir=str(ROOT))
        if not selected:
            raise RuntimeError('Dossier Spek non selectionne. Place le lanceur dans la racine du depot ou choisis le dossier.')
        if not _repo_usable(selected):
            raise RuntimeError('Depot incomplet : il manque spek/template_manager.py, spek/core.py, layouts/ ou template_library/. '
                               'Decompresse le ZIP correctif dans la racine C:\\mycode\\Kristal (pas dans Spek\\Spek).')
        return Path(selected).resolve()
    finally:
        chooser.destroy()


def _load_spek(repository):
    # Import retarde : un lanceur place dans Telechargements peut localiser le depot d'abord.
    # Eviter de charger un autre module spek d'une installation Python deja presente.
    old = sys.modules.get('spek')
    if old is not None and not Path(getattr(old, '__file__', '')).resolve().is_relative_to(repository):
        raise RuntimeError('Un autre module spek est deja charge. Relance le gestionnaire.')
    if str(repository) not in sys.path:
        sys.path.insert(0, str(repository))
    from spek.core import ValidationError
    from spek.template_manager import (
        TemplateConflict, change_json, create_category, create_family_template,
        create_layout, delete_template, digest, format_json, read_object,
        safe_file, save_profile, source_root, template_inventory,
        validate_category, validate_family_template, validate_layout, validate_profile,
    )
    from spek.composition_registry import read_registry
    from spek.ai_proposals import read_proposals
    from spek.studio_workflow import inspect_kristal, execute_preview
    globals().update(locals())


class TemplateManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Spek — Atelier de publication')
        self.geometry('1260x810')
        self.minsize(900, 580)
        self.root_folder = ROOT
        self.inv = {}
        self.selection: tuple | None = None
        self.editor_original = ''
        self.editor_hash = None
        self.node_map: dict[str, tuple] = {}
        self.current_key = None
        self._changing = False
        self.article_path = None
        self.realizations_path = None
        self.kristal_details = None
        self.preview_busy = False
        self.registry = None
        self.proposals = {}
        self.guide_var = tk.StringVar()
        self.next_steps_var = tk.StringVar()
        self._build()
        self._refresh_guide()
        self.load_inventory()

    def _build(self):
        style=ttk.Style(self)
        if 'vista' in style.theme_names() and sys.platform=='win32':
            style.theme_use('vista')
        top=ttk.Frame(self,padding=(14,10));top.pack(fill='x')
        ttk.Label(top,text='SPEK · ATELIER',font=('Segoe UI',15,'bold')).pack(side='left')
        ttk.Label(top,text='Ouvrir un Kristal ou un article · Comprendre la composition · Prévisualiser localement · Aucune publication',foreground='#667085').pack(side='right')

        # Parcours principal (UX-15 / UX-16) : un seul espace de travail.
        work=ttk.LabelFrame(self,text='1) Mon travail · Ouvrir → Vérifier → Prévisualiser',padding=9)
        work.pack(fill='x',padx=12,pady=(0,6))
        bar=ttk.Frame(work);bar.pack(fill='x')
        self.open_article_button=ttk.Button(bar,text='Ouvrir un article…',command=self.open_article)
        self.open_article_button.pack(side='left',padx=(0,7))
        self.open_kristal_button=ttk.Button(bar,text='Ouvrir un Kristal…',command=self.open_kristal)
        self.open_kristal_button.pack(side='left',padx=(0,7))
        self.goto_recipe_button=ttk.Button(bar,text='Voir la composition',command=self.goto_assigned_recipe)
        self.goto_recipe_button.pack(side='left',padx=(0,7))
        ttk.Label(bar,text='Langue').pack(side='left',padx=(18,4))
        self.lang_var=tk.StringVar(value='fr')
        ttk.Combobox(bar,values=('fr','en','it'),textvariable=self.lang_var,state='readonly',width=5).pack(side='left')
        self.verify_button=ttk.Button(bar,text='2) Vérifier',command=lambda:self.run_compiler(False))
        self.verify_button.pack(side='right',padx=(6,0))
        self.preview_button=ttk.Button(bar,text='3) Prévisualiser en HTML',command=lambda:self.run_compiler(True))
        self.preview_button.pack(side='right')
        privatebar=ttk.Frame(work);privatebar.pack(fill='x',pady=(7,0))
        self.structural_preview_button=ttk.Button(privatebar,text='Explorer les assertions dans la composition (aperçu privé)',command=self.open_structural_preview)
        self.structural_preview_button.pack(side='left')
        ttk.Label(privatebar,text='Pour les 5 Kristals étudiés, si le fichier local correspond au snapshot.',foreground='#525c6a').pack(side='left',padx=(12,0))
        semantikbar=ttk.Frame(work);semantikbar.pack(fill='x',pady=(5,0))
        self.semantik_import_button=ttk.Button(semantikbar,text='Importer des résultats SemantiK…',command=self.import_semantik)
        self.semantik_import_button.pack(side='left')
        self.semantik_prepare_button=ttk.Button(semantikbar,text='Préparer la correspondance…',command=self.prepare_semantik_mapping)
        self.semantik_prepare_button.pack(side='left',padx=(8,0))
        ttk.Label(semantikbar,text='Requêtes/résultats explicites · Privé, non qualifié',foreground='#525c6a').pack(side='left',padx=(12,0))
        self.context_var=tk.StringVar(value='Commence par ouvrir soit un Kristal (pour voir sa composition prescrite), soit un article.json + realizations.json (pour voir le vrai rendu).')
        ttk.Label(work,textvariable=self.context_var,foreground='#525c6a',wraplength=1130).pack(anchor='w',pady=(7,2))
        ttk.Label(work,textvariable=self.next_steps_var,foreground='#344054',wraplength=1130,justify='left').pack(anchor='w',pady=(0,2))

        helper=ttk.LabelFrame(self,text='Ce que tu peux faire ici',padding=8)
        helper.pack(fill='x',padx=12,pady=(0,8))
        helper.columnconfigure(0,weight=1)
        helper.columnconfigure(1,weight=1)
        helper.columnconfigure(2,weight=1)
        ttk.Label(helper,text='A · Parcourir la bibliothèque',font=('Segoe UI',10,'bold')).grid(row=0,column=0,sticky='w',padx=(0,10))
        ttk.Label(helper,text='Choisis à gauche une catégorie, un archétype Wiki, une composition IA ou un layout partagé.',wraplength=300,justify='left',foreground='#475467').grid(row=1,column=0,sticky='w',padx=(0,10))
        ttk.Label(helper,text='B · Ouvrir un Kristal',font=('Segoe UI',10,'bold')).grid(row=0,column=1,sticky='w',padx=(0,10))
        ttk.Label(helper,text='Lecture seule : Spek montre l’identité, le modèle natif et la composition qui lui est assignée dans le registre. Spek ne devine rien.',wraplength=300,justify='left',foreground='#475467').grid(row=1,column=1,sticky='w',padx=(0,10))
        ttk.Label(helper,text='C · Voir le rendu final',font=('Segoe UI',10,'bold')).grid(row=0,column=2,sticky='w')
        ttk.Label(helper,text='Un Kristal revu permet un aperçu privé de sa structure. Une vraie page exige article.json et realizations.json, puis Vérifier et Prévisualiser.',wraplength=300,justify='left',foreground='#475467').grid(row=1,column=2,sticky='w')
        ttk.Label(helper,textvariable=self.guide_var,foreground='#1d2939',wraplength=1120,justify='left').grid(row=2,column=0,columnspan=3,sticky='w',pady=(8,0))

        rootbar=ttk.LabelFrame(self,text='2) Dépôt Spek utilisé par l’atelier',padding=8)
        rootbar.pack(fill='x',padx=12,pady=(0,8))
        ttk.Label(rootbar,text='Bibliothèque :').pack(side='left')
        self.root_var=tk.StringVar(value=str(ROOT))
        ttk.Entry(rootbar,textvariable=self.root_var,state='readonly').pack(side='left',fill='x',expand=True,padx=6)
        self.change_root_button=ttk.Button(rootbar,text='Changer de dépôt…',command=self.choose_root)
        self.change_root_button.pack(side='left')
        self._update_buttons()

        pane=ttk.Panedwindow(self,orient='horizontal');pane.pack(fill='both',expand=True,padx=12,pady=(0,8))
        left=ttk.Frame(pane);pane.add(left,weight=1)
        ttk.Label(left,text='Catégories et gabarits',font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(0,4))
        lefttree=ttk.Frame(left);lefttree.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(lefttree,show='tree',selectmode='browse')
        y=ttk.Scrollbar(lefttree,orient='vertical',command=self.tree.yview)
        self.tree.configure(yscrollcommand=y.set)
        self.tree.pack(side='left',fill='both',expand=True)
        y.pack(side='right',fill='y')
        self.tree.bind('<<TreeviewSelect>>',self.on_select)
        self.tree.bind('<Double-1>',lambda _e:self.notebook.select(self.tab_preview))
        admin=ttk.LabelFrame(left,text='Gérer l’élément sélectionné',padding=6)
        self.admin_frame=admin
        buttons=ttk.Frame(admin);buttons.pack(fill='x')
        for name,method in [('Créer…',self.add_template),('Dupliquer',self.duplicate),('Enregistrer',self.save),('Valider',self.validate)]:
            ttk.Button(buttons,text=name,command=method).pack(side='left',padx=(0,5))
        more=ttk.Frame(admin);more.pack(fill='x',pady=(5,0))
        for name,method in [('Catégorie +',self.add_category),('Supprimer…',self.delete),('Dossier',self.open_folder),('Actualiser',self.reload)]:
            ttk.Button(more,text=name,command=method).pack(side='left',padx=(0,5))


        right=ttk.Frame(pane);pane.add(right,weight=3)
        self.header_var=tk.StringVar(value='Choisis un élément à gauche')
        ttk.Label(right,textvariable=self.header_var,font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(0,5))
        self.notebook=ttk.Notebook(right);self.notebook.pack(fill='both',expand=True)
        self.tab_preview=ttk.Frame(self.notebook)
        self.tab_guide=ttk.Frame(self.notebook)
        self.tab_json=ttk.Frame(self.notebook)
        self.notebook.add(self.tab_preview,text='Aperçu et contexte')
        self.notebook.add(self.tab_guide,text='Guide pas à pas')
        self.notebook.add(self.tab_json,text='Avancé · Éditeur JSON')

        canvas_outer=ttk.Frame(self.tab_preview);canvas_outer.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(canvas_outer,bg='#f5f7fa',highlightthickness=0)
        sb=ttk.Scrollbar(canvas_outer,orient='vertical',command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side='left',fill='both',expand=True)
        sb.pack(side='right',fill='y')
        self.inner=ttk.Frame(self.canvas,padding=16)
        self.inner_id=self.canvas.create_window((0,0),anchor='nw',window=self.inner)
        self.inner.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.inner_id,width=e.width))

        guidewrap=ttk.Frame(self.tab_guide,padding=10)
        guidewrap.pack(fill='both',expand=True)
        ttk.Label(guidewrap,text='Guide d’utilisation',font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(0,6))
        self.guide_text=tk.Text(guidewrap,wrap='word',height=20,font=('Segoe UI',10),background='#fcfcfd')
        guide_scroll=ttk.Scrollbar(guidewrap,orient='vertical',command=self.guide_text.yview)
        self.guide_text.configure(yscrollcommand=guide_scroll.set)
        self.guide_text.pack(side='left',fill='both',expand=True)
        guide_scroll.pack(side='right',fill='y')
        self.guide_text.configure(state='disabled')

        editorbar=ttk.Frame(self.tab_json,padding=6);editorbar.pack(fill='x')
        ttk.Label(editorbar,text='Les modifications ne sont écrites qu’avec « Enregistrer ». Sauvegardes automatiques avant remplacement.',foreground='#525c6a').pack(anchor='w')
        editframe=ttk.Frame(self.tab_json);editframe.pack(fill='both',expand=True)
        self.text=tk.Text(editframe,wrap='none',undo=True,font=('Consolas',10),tabs=('30',),background='#fcfcfd')
        y2=ttk.Scrollbar(editframe,orient='vertical',command=self.text.yview)
        x2=ttk.Scrollbar(self.tab_json,orient='horizontal',command=self.text.xview)
        self.text.configure(yscrollcommand=y2.set,xscrollcommand=x2.set)
        self.text.pack(side='left',fill='both',expand=True);y2.pack(side='right',fill='y')
        x2.pack(fill='x')
        self.text.bind('<Control-s>',lambda e:(self.save(), 'break')[1])
        self.text.bind('<KeyRelease>',lambda e:self.after_idle(self.preview))
        self.bind('<F5>',lambda e:self.reload())
        self.bind('<Control-s>',lambda e:self.save())
        self.status_var=tk.StringVar(value='Prêt')
        ttk.Label(self,textvariable=self.status_var,relief='sunken',anchor='w',padding=(10,5)).pack(fill='x',side='bottom')

    def report_callback_exception(self, exc_type, exc_value, exc_traceback):
        detail = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        _record_error('Erreur de l interface : ' + detail)
        messagebox.showerror('Spek - erreur', str(exc_value) + '\n\nJournal : ' + str(_log_path()), parent=self)

    def _status(self,s):self.status_var.set(s)
    def _error(self,title,e):
        self._status('Erreur : '+str(e));messagebox.showerror(title,str(e),parent=self)

    def _set_readonly_text(self, widget, content):
        widget.configure(state='normal')
        widget.delete('1.0','end')
        widget.insert('1.0', content)
        widget.configure(state='disabled')

    def _refresh_guide(self):
        guide = [
            'SPEK — mode d’emploi rapide',
            '',
            '1. Si tu veux comprendre un Kristal : clique sur « Ouvrir un Kristal… ».',
            '   - Spek montre ses métadonnées déclarées et, si elle existe, la composition Wiki qui lui est attribuée.',
            '   - Spek ne choisit pas de templates automatiquement.',
            '',
            '2. Si SemantiK a déjà produit les textes : clique sur « Importer des résultats SemantiK… ».',
            '   - « Préparer la correspondance… » crée une liste de clés avec chemins à compléter.',
            '   - Sélectionne article.json puis un fichier de correspondance (requête/résultat par clé).',
            '   - Spek contrôle langue, obligations, couverture, sources et empreintes déterministes.',
            '   - Les réalisations restent importées/non revues : qualification RuntimeSet et C1/C2/C3 sont externes.',
            '',
            '3. Si tu veux voir une vraie page : clique sur « Ouvrir un article… ».',
            '   - Choisis article.json puis realizations.json.',
            '   - Clique sur « Vérifier » pour contrôler localement le projet.',
            '   - Clique sur « Prévisualiser en HTML » pour ouvrir le rendu final dans ton navigateur.',
            '',
            '3. Si tu veux gérer la bibliothèque : utilise l’arbre de gauche.',
            '   - Catégories : familles de templates (wiki, educational, scientific, report, book).',
            '   - Archétypes Wiki : profils autorisés pour les pages Wiki.',
            '   - Compositions IA : recettes éditoriales décidées par l’IA, non inférées par Spek.',
            '   - layouts : composants partagés utilisés par plusieurs templates.',
            '',
            '4. Si tu modifies un JSON : fais les changements dans l’onglet « Avancé · Éditeur JSON », puis clique sur « Enregistrer ».',
            '   - Spek crée une sauvegarde avant remplacement.',
            '',
            '5. Avec un Kristal revu, « Explorer les assertions dans la composition » ouvre un HTML de contrôle, NON PUBLIABLE.',
            '   - Aucune réalisation SemantiK n’est inventée. Pour un vrai Wiki, il faut le pipeline C1/C2/C3.',
            '',
            '6. Rien n’est publié depuis cette fenêtre. Tout reste local tant que tu n’utilises pas le pipeline de publication séparé.'
        ]
        if hasattr(self, 'guide_text'):
            self._set_readonly_text(self.guide_text, '\n'.join(guide))
        self.guide_var.set('Astuce : un Kristal sert surtout à consulter sa composition prescrite ; pour voir le rendu complet, il faut ensuite ouvrir ou produire le couple article.json + realizations.json.')
        self._refresh_next_steps()

    def _refresh_next_steps(self):
        if self.preview_busy:
            self.next_steps_var.set('En cours : attends la fin de la vérification ou de la prévisualisation avant de changer de source.')
            return
        if self.article_path and self.realizations_path:
            self.next_steps_var.set('Étapes suivantes : 1) clique sur « Vérifier » ; 2) si tout est correct, clique sur « Prévisualiser en HTML ».')
            return
        if self.kristal_details:
            if self.kristal_details.get('assignment'):
                self.next_steps_var.set('Étapes suivantes : 1) clique sur « Voir la composition » ; 2) inspecte la recette assignée ; 3) quand tu auras un article.json + realizations.json correspondant, utilise « Ouvrir un article… » pour voir le rendu.')
            elif self.kristal_details.get('proposal'):
                if (self.kristal_details.get('structure_review')
                        and self.kristal_details.get('source_snapshot_comparison') == 'MATCHES_UPLOADED_SNAPSHOT'):
                    self.next_steps_var.set('Étape suivante : « Explorer les assertions dans la composition » ouvre la vue structurelle PRIVÉE (pas une page Wiki publiée).')
                else:
                    self.next_steps_var.set('Étapes suivantes : consulte « Voir la composition ». L’exploration des sources exige une revue détaillée et un snapshot identique.')
            else:
                self.next_steps_var.set('Étapes suivantes : ce Kristal n’a pas encore de composition proposée. Le registre ne contient aucune correspondance.')
            return
        self.next_steps_var.set('Étapes suivantes : ouvre un Kristal pour comprendre sa projection, ou ouvre un article Spek pour voir directement le rendu final.')

    def _update_buttons(self):
        active=bool(self.article_path and self.realizations_path) and not self.preview_busy
        state='normal' if active else 'disabled'
        self.verify_button.configure(state=state)
        self.preview_button.configure(state=state)
        recipe_state = 'normal' if (self.kristal_details and (self.kristal_details.get('assignment') or self.kristal_details.get('proposal')) and not self.preview_busy) else 'disabled'
        self.goto_recipe_button.configure(state=recipe_state)
        can_audit = bool(self.kristal_details and self.kristal_details.get('structure_review')
                         and self.kristal_details.get('source_snapshot_comparison') == 'MATCHES_UPLOADED_SNAPSHOT'
                         and not self.preview_busy)
        self.structural_preview_button.configure(state='normal' if can_audit else 'disabled')
        for control in (self.open_article_button,self.open_kristal_button,self.change_root_button,self.semantik_import_button,self.semantik_prepare_button):
            control.configure(state='disabled' if self.preview_busy else 'normal')
        self._refresh_next_steps()

    def _show_workspace(self):
        # Tk does not emit a new selection event if the workspace is already selected.
        # A newly opened Kristal must repaint its name and proposed composition.
        for iid,key in self.node_map.items():
            if key==('workspace',):
                self.tree.selection_set(iid)
                self.tree.see(iid)
                self.on_select()
                break
        title = None
        if self.kristal_details:
            title = self.kristal_details.get('title') or self.kristal_details.get('identity')
        self.header_var.set('Mon travail · ' + str(title or 'Projet Spek'))
        self.preview()
        self.notebook.select(self.tab_preview)

    def goto_assigned_recipe(self):
        if not self.kristal_details:
            return
        if self.kristal_details.get('assignment'):
            target=('recipe', self.kristal_details['assignment']['composition_id'])
        elif self.kristal_details.get('proposal'):
            target=('proposal', self.kristal_details['identity'])
        else:
            messagebox.showinfo('Spek','Aucune composition proposée pour ce Kristal.',parent=self)
            return
        for iid,key in self.node_map.items():
            if key == target:
                self._expand_parents(iid)
                self.tree.selection_set(iid)
                self.tree.see(iid)
                self.on_select()
                self.notebook.select(self.tab_preview)
                return
        messagebox.showwarning('Spek','La composition assignée n’a pas été trouvée dans la bibliothèque courante.',parent=self)

    def open_article(self):
        if self.preview_busy:return
        source=filedialog.askopenfilename(parent=self,title='Choisir article.json',filetypes=[('Article JSON','*.json')])
        if not source:return
        # The operator explicitly chooses realizations; never infer or generate text.
        realizations=filedialog.askopenfilename(parent=self,title='Choisir les réalisations SemantiK / Spek',initialdir=str(Path(source).parent),filetypes=[('Réalisation JSON','*.json')])
        if not realizations:return
        try:
            from spek.studio_workflow import project_pair
            self.article_path,self.realizations_path=project_pair(Path(source),Path(realizations))
            self.context_var.set('Article chargé : '+self.article_path.name+' · Réalisations : '+self.realizations_path.name+' · Tu peux maintenant vérifier puis prévisualiser.')
            self._status('Article chargé, non encore vérifié')
            self._update_buttons();self._show_workspace();self._refresh_guide()
        except (ValueError,OSError,ValidationError) as e:self._error('Projet invalide',e)

    def prepare_semantik_mapping(self):
        if self.preview_busy:return
        article=filedialog.askopenfilename(parent=self,title='Choisir article.json pour préparer les clés de réalisation',
                                           initialdir=str(self.article_path.parent if self.article_path else self.root_folder),
                                           filetypes=[('Fichiers JSON','*.json')])
        if not article:return
        target=filedialog.asksaveasfilename(parent=self,title='Enregistrer le plan de liaison SemantiK',
                                           initialdir=str(Path(article).parent),initialfile='semantik-mapping.json',
                                           defaultextension='.json',filetypes=[('Fichiers JSON','*.json')])
        if not target:return
        try:
            from spek.semantik_transfer import prepare_mapping
            result=prepare_mapping(Path(article),self.lang_var.get(),Path(target))
            self._status(str(result['required_keys'])+' clés à relier dans '+result['mapping'])
            messagebox.showinfo('Spek · correspondance préparée',
                str(result['required_keys'])+' clés listées dans '+result['mapping']+'\n\n'
                'Spek n’a produit aucune requête ni texte. Remplis les chemins requests/ et results/ avec les sorties réelles de SemantiK Architect, puis utilise « Importer des résultats SemantiK… ».',parent=self)
        except (ValueError,OSError,ValidationError) as exc:self._error('Préparation du transfert',exc)

    def import_semantik(self):
        if self.preview_busy:return
        source=filedialog.askopenfilename(parent=self,title='Choisir l’article Spek (article.json)',
                                          initialdir=str(self.article_path.parent if self.article_path else self.root_folder),
                                          filetypes=[('Fichiers JSON','*.json')])
        if not source:return
        mapping=filedialog.askopenfilename(parent=self,title='Choisir le manifeste de correspondance SemantiK (mapping.json)',
                                           initialdir=str(Path(source).parent),filetypes=[('Fichiers JSON','*.json')])
        if not mapping:return
        snapshot=None
        try:
            source_obj=json.loads(Path(source).read_text(encoding='utf-8'))
            if source_obj.get('source',{}).get('origin')=='kristal_v9':
                snapshot=filedialog.askopenfilename(parent=self,title='Choisir le state snapshot v9 lié à cet article',
                                                    initialdir=str(Path(source).parent),filetypes=[('Fichiers JSON','*.json')])
                if not snapshot:return
        except (OSError,ValueError,AttributeError) as exc:
            self._error('Article illisible',exc);return
        from spek.semantik_transfer import transfer
        # Never write in a repository, to locals/, or over an earlier output.
        out=Path(tempfile.mkdtemp(prefix='spek-semantik-prive-'))/'transfert'
        self.preview_busy=True;self._update_buttons()
        self._status('Contrôle des requêtes et résultats SemantiK…')
        def worker():
            try:
                result=transfer(Path(source),Path(mapping),out,layouts=self.root_folder/'layouts',
                                state_snapshot=Path(snapshot) if snapshot else None)
            except Exception as exc:
                self.after(0,lambda err=str(exc):self._semantik_import_done(None,err,source))
            else:
                self.after(0,lambda res=result:self._semantik_import_done(res,None,source))
        threading.Thread(target=worker,daemon=True).start()

    def _semantik_import_done(self,result,error,source):
        self.preview_busy=False
        if error:
            self._update_buttons()
            self._status('Import SemantiK REFUSÉ : '+str(error)[:160])
            messagebox.showerror('Spek · import SemantiK refusé',str(error),parent=self)
            return
        self.article_path=Path(source)
        self.realizations_path=Path(result['realizations'])
        self.lang_var.set(result['language'])
        self.context_var.set('Transfert SemantiK : '+str(result['realization_count'])+' clés · IMPORTÉ, non qualifié · Aucune autorisation de publier.')
        self._update_buttons();self._show_workspace();self._refresh_guide()
        self._status('Transfert SemantiK privé · '+str(result['directory']))
        messagebox.showinfo('Spek · import SemantiK contrôlé',
            'Les textes reçus correspondent aux blocs, obligations et références déclarés.\n'
            'Aucune revue humaine ni authentification du RuntimeSet par Spek. Aucune publication autorisée.\n\n'
            'Tu peux maintenant vérifier puis prévisualiser le rendu local.\n\nRapport : '+str(result['report']),parent=self)

    def open_kristal(self):
        if self.preview_busy:return
        folder=filedialog.askdirectory(parent=self,title='Ouvrir un Kristal (lecture seule)',initialdir=str(self.root_folder.parent))
        if not folder:return
        try:
            self.kristal_details=inspect_kristal(Path(folder),self.root_folder)
            state = 'composition proposée par l’IA, non approuvée' if self.kristal_details.get('proposal') else 'aucune composition proposée'
            if self.kristal_details.get('assignment'):
                state = 'assignation présente, état source non revérifié ici'
            self.context_var.set('Kristal ouvert : '+str(self.kristal_details['identity'] or Path(folder).name)+' · '+state+' · Lecture seule, aucune publication.')
            self._status('Métadonnées Kristal ouvertes ; aucune projection générée')
            self._update_buttons();self._show_workspace();self._refresh_guide()
        except (ValueError,OSError,ValidationError) as e:self._error('Lecture Kristal',e)

    def open_structural_preview(self):
        if (self.preview_busy or not self.kristal_details
                or not self.kristal_details.get('structure_review')
                or self.kristal_details.get('source_snapshot_comparison') != 'MATCHES_UPLOADED_SNAPSHOT'):
            messagebox.showinfo('Spek · inspection',
                'Cet aperçu privé nécessite une revue structurelle explicite et un fichier source identique au snapshot étudié.',parent=self)
            return
        from spek.structural_preview import create_structural_preview
        folder=Path(self.kristal_details['folder'])
        root=self.root_folder
        self.preview_busy=True
        self._update_buttons()
        self._status('Préparation de l’inspection structurelle PRIVÉE…')
        def worker():
            try:
                result=create_structural_preview(root,folder)
            except Exception as exc:
                self.after(0, lambda err=str(exc):self._structural_preview_done(None,err))
            else:
                self.after(0, lambda res=result:self._structural_preview_done(res,None))
        threading.Thread(target=worker,daemon=True).start()

    def _structural_preview_done(self, result, error):
        self.preview_busy=False
        self._update_buttons()
        if error:
            self._status('Aperçu refusé : '+str(error)[:160])
            messagebox.showerror('Spek · aperçu structurel impossible',str(error),parent=self)
            return
        self._status('Inspection structurelle locale disponible : NON PUBLIABLE · '+str(result['directory']))
        webbrowser.open(Path(result['page']).as_uri())

    def run_compiler(self,build:bool):
        if self.preview_busy or not self.article_path or not self.realizations_path:return
        try:
            lang=self.lang_var.get()
            if lang not in {'fr','en','it'}:raise ValueError('Langue inconnue')
            root,article,realizations=self.root_folder,self.article_path,self.realizations_path
            self.preview_busy=True;self._update_buttons()
            self._status('Compilation en cours (locale, sans publication)…' if build else 'Vérification en cours…')
            def worker():
                try:
                    result=execute_preview(root,article,realizations,lang,build=build)
                except Exception as exc:
                    self.after(0,lambda msg=str(exc):self._compiler_done(None,msg,build))
                else:
                    self.after(0,lambda res=result:self._compiler_done(res,None,build))
            threading.Thread(target=worker,daemon=True).start()
        except (ValueError,OSError,ValidationError) as e:self._error('Exécution impossible',e)

    def _compiler_done(self,result,error,build):
        self.preview_busy=False;self._update_buttons()
        if error:
            self._status('Échec de la compilation : '+error[:180])
            self._refresh_next_steps()
            messagebox.showerror('Spek · Vérification refusée',error,parent=self)
            return
        if build:
            self._status('Aperçu HTML local compilé · NON PUBLIÉ · '+str(result['directory']))
            self._refresh_next_steps()
            webbrowser.open(Path(result['page']).as_uri())
        else:
            self._status('Vérifié localement · NON PUBLIÉ · '+result['output'].strip()[:150])
            self._refresh_next_steps()
            messagebox.showinfo('Spek · Vérifié',result['output'].strip()+'\n\nAucune publication, aucune qualification SemantiK effectuée.',parent=self)

    def choose_root(self):
        if self.preview_busy:return
        if not self.confirm_discard():return
        selected=filedialog.askdirectory(parent=self,title='Choisir la racine du dépôt Spek',initialdir=str(self.root_folder))
        if not selected:return
        try:
            folder=source_root(selected)
            self.root_folder=folder;self.root_var.set(str(folder))
            self.kristal_details=None
            self.load_inventory()
        except (OSError,ValidationError) as e:self._error('Dépôt invalide',e)

    def confirm_discard(self)->bool:
        if self.selection and self.text.get('1.0','end-1c')!=self.editor_original:
            ans=messagebox.askyesnocancel('Modifications non enregistrées','Enregistrer les modifications avant de changer de sélection ?',parent=self)
            if ans is None:return False
            if ans and not self.save():return False
        return True

    def load_inventory(self,preferred=None):
        try:self.inv=template_inventory(self.root_folder)
        except (OSError,ValueError,ValidationError) as e:
            self._error('Inventaire invalide',e);return
        self.node_map.clear();self._changing=True
        try:
            self.tree.delete(*self.tree.get_children())
            workspace=self.tree.insert('','end',text='Mon travail · projet / Kristal ouvert',open=True)
            self.node_map[workspace]=('workspace',)
            book=self.tree.insert('','end',text='Bibliothèque de templates',open=True)
            self.node_map[book]=('root',)
            try:
                self.registry=read_registry(self.root_folder)
                self.proposals=read_proposals(self.root_folder,self.registry)
            except (OSError,ValueError,ValidationError) as exc:
                self.registry=None
                self.proposals={}
                self._status('Registre IA inaccessible : '+str(exc))
            for cat in self.inv['categories']:
                n=cat['id'];enabled='actif' if cat['status']=='implemented' else 'réservé'
                folder=self.tree.insert(book,'end',text=f'{n}  [{enabled}]',open=(n=='wiki'))
                self.node_map[folder]=('category',n)
                if n=='wiki':
                    branch=self.tree.insert(folder,'end',text=f'Profils / Archétypes Wiki ({len(self.inv["profiles"])})',open=False)
                    self.node_map[branch]=('profiles',)
                    for slug,profile in sorted(self.inv['profiles'].items()):
                        child=self.tree.insert(branch,'end',text=slug)
                        self.node_map[child]=('profile',slug)
                if n=='wiki' and self.registry:
                    recipes=self.tree.insert(folder,'end',text=f'Compositions IA candidates ({len(self.registry["compositions"])})',open=False)
                    self.node_map[recipes]=('recipes',)
                    for cid in sorted(self.registry['compositions']):
                        item=self.tree.insert(recipes,'end',text=cid.removeprefix('arketype-'))
                        self.node_map[item]=('recipe',cid)
                    if self.proposals:
                        branch=self.tree.insert(folder,'end',text=f'Kristals · compositions proposées ({len(self.proposals)})',open=False)
                        self.node_map[branch]=('proposals',)
                        for slug,proposal in sorted(self.proposals.items()):
                            item=self.tree.insert(branch,'end',text=proposal['title']+'  ['+slug+']')
                            self.node_map[item]=('proposal',slug)
                drafts=self.inv['templates'].get(n,[])
                if drafts:
                    branch=self.tree.insert(folder,'end',text=f'Templates de catégorie ({len(drafts)})',open=True)
                    self.node_map[branch]=('drafts',n)
                    for slug in drafts:
                        child=self.tree.insert(branch,'end',text=slug)
                        self.node_map[child]=('family',n,slug)
            layouts=self.tree.insert('','end',text=f'Layouts partagés ({len(self.inv["layouts"])})',open=True)
            self.node_map[layouts]=('layouts',)
            for slug in self.inv['layouts']:
                child=self.tree.insert(layouts,'end',text=slug)
                self.node_map[child]=('layout',slug)
            self._set_none()
            if preferred:
                for iid,key in self.node_map.items():
                    if key==preferred:
                        self._expand_parents(iid)
                        self.tree.selection_set(iid);self.tree.see(iid)
                        break
            if not self.tree.selection():self.tree.selection_set(workspace)
        finally:self._changing=False
        self.on_select()
        self._refresh_guide()
        self._status(f"{len(self.inv['categories'])} catégories · {len(self.inv['layouts'])} layouts · {len(self.inv['profiles'])} archétypes Wiki")

    def _expand_parents(self,iid):
        parent=self.tree.parent(iid)
        while parent:
            self.tree.item(parent,open=True);parent=self.tree.parent(parent)

    def _set_none(self):
        self.selection=None;self.editor_hash=None
        self.editor_original=''
        self.text.delete('1.0','end')

    def on_select(self,_event=None):
        if self._changing:return
        selected=self.tree.selection()
        if not selected:return
        key=self.node_map.get(selected[0],('root',))
        if key==self.selection:return
        if not self.confirm_discard():
            self._changing=True
            try:
                if self.selection:
                    for iid,val in self.node_map.items():
                        if val==self.selection:self.tree.selection_set(iid);break
            finally:self._changing=False
            return
        self.selection=key
        kind=key[0]
        if kind in {'category','layout','profile','family','root','layouts','drafts','profiles'}:
            if not self.admin_frame.winfo_manager():
                self.admin_frame.pack(fill='x',pady=(8,0))
        elif self.admin_frame.winfo_manager():
            self.admin_frame.pack_forget()
        self.header_var.set(' · '.join(str(x) for x in key))
        try:
            if kind=='category':
                path=f'template_library/{key[1]}/category.json';obj=read_object(safe_file(self.root_folder,path))
            elif kind=='profile':
                path='template_library/wiki/archetype-profiles.json';obj=read_object(safe_file(self.root_folder,path))['archetypes'][key[1]]
            elif kind=='layout':
                path=f'layouts/{key[1]}.json';obj=read_object(safe_file(self.root_folder,path))
            elif kind=='family':
                path=f'template_library/{key[1]}/templates/{key[2]}.json';obj=read_object(safe_file(self.root_folder,path))
            else:
                self._set_none();self.selection=key
                self.preview();return
            self.editor_hash=digest(safe_file(self.root_folder,path))
            self.editor_original=format_json(obj)
            self.text.delete('1.0','end');self.text.insert('1.0',self.editor_original)
        except (OSError,ValidationError,KeyError) as e:
            self._error('Lecture',e);self._set_none();return
        self.preview()

    def _preview_line(self,text,style='body'):
        font=('Segoe UI',10)
        if style=='heading':font=('Segoe UI',14,'bold')
        if style=='sub':font=('Segoe UI',11,'bold')
        label=ttk.Label(self.inner,text=str(text),font=font,wraplength=650,justify='left')
        label.pack(anchor='w',fill='x',pady=(3,5) if style=='heading' else (2,2))

    def _preview_card(self,title,subtitle):
        frame=ttk.Frame(self.inner,relief='ridge',borderwidth=1,padding=9)
        frame.pack(fill='x',pady=4)
        ttk.Label(frame,text=title,font=('Segoe UI',10,'bold')).pack(anchor='w')
        ttk.Label(frame,text=str(subtitle),foreground='#5e6470',wraplength=600).pack(anchor='w')

    def preview(self):
        for child in self.inner.winfo_children():child.destroy()
        self.canvas.yview_moveto(0)
        if not self.selection:
            self._preview_line('Choisis un élément à gauche pour voir son rôle dans le workflow.','heading');return
        key=self.selection;kind=key[0]
        self._preview_line('Aperçu et mode d’emploi', 'heading')
        try:
            if kind in {'root','layouts','profiles','drafts','recipes','workspace','recipe','proposals','proposal'}:
                if kind=='workspace':
                    self._preview_line('Votre projet Spek', 'heading')
                    self._preview_line('Utilise cette vue comme tableau de bord. Elle te dit où tu en es et quoi faire ensuite.')
                    if self.article_path:
                        self._preview_card('Article à compiler',str(self.article_path))
                        self._preview_card('Formulations fournies',str(self.realizations_path))
                        self._preview_card('Prochaine action','Clique sur « Vérifier », puis sur « Prévisualiser en HTML » pour ouvrir le vrai rendu local.')
                    else:
                        self._preview_card('Aucun article chargé','Pour voir une vraie page, ouvre un article.json et son fichier realizations.json.')
                    if self.kristal_details:
                        obj=self.kristal_details
                        self._preview_card('Kristal ouvert · lecture seule',obj['folder'])
                        self._preview_card('Slug actuel',str(obj['identity'] or 'non déclaré'))
                        if obj.get('declared_identity') != obj.get('identity'):
                            self._preview_card('Slug dans le fichier ouvert (ancienne forme)', str(obj.get('declared_identity')))
                        self._preview_card('Titre déclaré',str(obj.get('title') or 'non déclaré'))
                        self._preview_card('Modèle natif déclaré',str(obj['native_model'] or 'non déclaré'))
                        if obj['assignment']:
                            self._preview_card('Composition assignée',obj['assignment']['composition_id']+' — utilise le bouton « Voir la composition » pour l’inspecter.')
                        elif obj.get('proposal'):
                            candidate=obj['proposal']
                            self._preview_card('Proposition IA · à vérifier',candidate['primary_composition_id']+' + '+', '.join(candidate['supplementary_composition_ids']))
                            self._preview_line('Sections proposées pour ce Kristal (contenu non réalisé) :','sub')
                            for n,section in enumerate(candidate['ordered_sections'],1):
                                self._preview_card(f'{n}. {section["proposed_function"]}',section['layout_id']+' · '+section['composition_id'].removeprefix('arketype-'))
                            if obj.get('structure_review'):
                                rev=obj['structure_review']
                                self._preview_card('Étude canonique disponible',f'{rev["source"]["assertion_occurrences"]} occurrences d’assertions v8 inspectées. Comparaison de l’état local : '+obj['source_snapshot_comparison'])
                                for section in rev['ordered_structural_sections']:
                                    self._preview_card(section['heading'],f'{section["source_observation"]["observed_assertion_occurrences"]} occurrences · Gabarit : {section["planned_template_id"]} · aperçu structurel privé si empreinte identique · layout typé exécutable si contenu SemantiK fourni')
                            self._preview_card('Important','Étude IA non approuvée. Aucune assertion n’est sélectionnée pour publier. L’aperçu HTML nécessite un article et des réalisations SemantiK explicites.')
                        else:
                            self._preview_card('Aucune proposition IA', 'Le registre ne contient pas de composition pour ce Kristal.')
                    else:
                        self._preview_card('Pas de Kristal ouvert','Ouvre un Kristal si tu veux voir quelle composition lui est prescrite.')
                    return
                if kind=='proposals':
                    self._preview_line('127 propositions de composition créées par l’IA','heading')
                    self._preview_line('Sélectionne un Kristal sous cette rubrique. Spek affiche les choix déjà prescrits sans analyser son contenu.')
                    self._preview_card('Statut','Propositions documentaires basées sur le rapport du Manager · aucune qualification des sources ni publication')
                    return
                if kind=='proposal':
                    proposal=self.proposals[key[1]]
                    self._preview_line(proposal['title']+' · composition proposée','heading')
                    self._preview_card('Kristal', proposal['kristal_identity']+' · '+proposal['source_state_ref'])
                    self._preview_card('Modèle déclaré',proposal['declared_native_model_kind']+' — '+proposal['declared_native_model_description'])
                    self._preview_card('Composition principale',proposal['primary_composition_id'].removeprefix('arketype-'))
                    self._preview_card('Compositions complémentaires',', '.join(c.removeprefix('arketype-') for c in proposal['supplementary_composition_ids']))
                    for n,section in enumerate(proposal['ordered_sections'],1):
                        self._preview_card(f'{n}. {section["proposed_function"]}',section['layout_id']+' / '+section['section_id']+' · '+section['composition_id'].removeprefix('arketype-'))
                    self._preview_card('Justification IA',proposal['editorial_rationale'])
                    if proposal.get('canonical_review_status')=='DEEP_SOURCE_INSPECTION_NOT_APPROVED':
                        try:
                            from spek.source_reviews import read_source_reviews
                            review=read_source_reviews(self.root_folder,self.proposals).get(key[1])
                        except (OSError,ValueError,ValidationError) as exc:
                            review=None
                            self._preview_card('Revue structurelle invalide',str(exc))
                        if review:
                            self._preview_card('Source étudiée',f'{review["source"]["assertion_occurrences"]} occurrences v8 · fichier : {review["source"]["portable_state_relative_path"]} · empreinte brute du snapshot (non qualifiée)')
                            self._preview_line('Plan IA du Kristal · layouts spécialisés typés disponibles, contenu SemantiK à fournir','sub')
                            for n,sec in enumerate(review['ordered_structural_sections'],1):
                                self._preview_card(f'{n}. {sec["heading"]}',f'{sec["source_observation"]["observed_assertion_occurrences"]} assertions inspectées · {sec["planned_template_id"]} · LAYOUT TYPÉ DISPONIBLE · À REMPLIR PAR SEMANTIK')
                            for risk in review['exclusions_and_risks']:
                                self._preview_card('Erreur de lecture à éviter',risk)
                    else:
                        self._preview_card('Analyse détaillée en attente','Le rapport Manager ne contient pas encore le graphe canonique de ce Kristal.')
                    self._preview_card('Non publiable','Les 19 layouts spécialisés sont exécutables avec un article Spek explicite et des réalisations SemantiK fournies. L’aperçu structurel est privé et n’approuve aucune assertion ni publication.')
                    return
                if kind=='recipe':
                    recipe=self.registry['compositions'][key[1]]
                    self._preview_line('Composition IA · '+recipe['archetype']['slug'],'heading')
                    self._preview_line('Ceci est une recette éditoriale décidée par l’IA. Spek l’affiche et l’utilise seulement si elle est assignée à un Kristal.')
                    for n,part in enumerate(recipe['sections_in_order'],1):
                        self._preview_card(f'{n}. {part["section_id"]} · {part["layout_id"]}',part.get('title_function','')+' · '+', '.join(part.get('required_slots',{})))
                    if recipe.get('needs_specialized_layouts_not_yet_implemented'):
                        self._preview_card('Layouts à concevoir',', '.join(recipe['needs_specialized_layouts_not_yet_implemented']))
                    return
                if kind=='recipes':
                    self._preview_line('Compositions conçues par l’IA','heading')
                    self._preview_line('Ces recettes indiquent comment plusieurs templates peuvent se combiner pour un même type de Kristal. Elles ne sont pas inférées par Spek.')
                    self._preview_card('À quoi ça sert ?','Quand un Kristal reçoit une assignation dans le registre, Spek peut afficher la recette correspondante et l’utiliser pour la projection.')
                    return
                if kind=='root':
                    self._preview_line('Toutes les catégories sont stockées dans template_library/. Explore-les pour comprendre les familles de publication disponibles.')
                    for c in self.inv['categories']:self._preview_card(c['id'],f"{c['status']} · {c['description']}")
                elif kind=='layouts':
                    for n in self.inv['layouts']:self._preview_card(n,'Layout partagé utilisé par les articles Spek')
                elif kind=='profiles':
                    for n,p in self.inv['profiles'].items():self._preview_card(n,p['preferred_layout'])
                else:self._preview_line('Brouillons de catégorie. Pas de moteur de rendu actif.')
                return
            data=json.loads(self.text.get('1.0','end-1c'))
            if not isinstance(data,dict):raise ValueError('Objet JSON attendu')
            if kind=='category':
                self._preview_line(key[1], 'heading')
                self._preview_card('État du moteur',data.get('status','?'))
                self._preview_line(data.get('description',''))
                if data.get('status')=='reserved':self._preview_line('Catégorie réservée : ses brouillons ne sont PAS des gabarits exécutables.')
            elif kind=='layout':
                self._preview_line(data.get('id',key[1]),'heading')
                self._preview_line(f"Intention : {data.get('intent','?')} · Public : {data.get('audience','?')}")
                self._preview_line('Emplacements sémantiques','sub')
                for name,spec in data.get('slots',{}).items():
                    kinds=', '.join(spec.get('allowed_kinds',[]))
                    self._preview_card(name,f"Types : {kinds}\nCardinalité : {spec.get('min')} à {spec.get('max')}")
                self._preview_line('Ceci est un aperçu structurel ; aucun énoncé ni aucune traduction n’est généré.')
            elif kind=='profile':
                self._preview_line(f"Archétype : {key[1]}", 'heading')
                self._preview_line(data.get('label',''))
                self._preview_card('Layout favori',data.get('preferred_layout','?'))
                for name in data.get('allowed_layouts',[]):
                    layout_path=self.root_folder/'layouts'/f'{name}.json'
                    if layout_path.exists():
                        layout=read_object(layout_path)
                        self._preview_card(name, ' • '.join(layout.get('slots',{})))
                    else:self._preview_card(name,'ABSENT')
                self._preview_card('Règle d’intégrité',data.get('integrity_rule','Non précisée'))
            elif kind=='family':
                self._preview_line(data.get('id',key[-1]),'heading')
                self._preview_card('Brouillon (non exécutable)',data.get('description',''))
                for section in data.get('sections',[]):self._preview_card('Section',str(section))
        except (ValueError,TypeError,AttributeError,KeyError) as e:self._preview_line('Erreur JSON : '+str(e))

    def save(self):
        if self.preview_busy:return False
        if not self.selection or self.selection[0] not in {'category','layout','profile','family'}:
            self._status('Sélectionne un template modifiable');return False
        key=self.selection;kind=key[0]
        try:
            data=json.loads(self.text.get('1.0','end-1c'))
            if not isinstance(data,dict):raise ValidationError('Objet JSON attendu')
            if kind=='profile':
                backup=save_profile(self.root_folder,key[1],data,self.editor_hash)
            else:
                if kind=='layout':rel=f'layouts/{key[1]}.json';item=key[1]
                elif kind=='category':rel=f'template_library/{key[1]}/category.json';item=key[1]
                else:rel=f'template_library/{key[1]}/templates/{key[2]}.json';item=key[2]
                backup=change_json(self.root_folder,rel,data,self.editor_hash,kind=kind,item=item)
            self.load_inventory(preferred=key)
            self._status('Enregistré avec sauvegarde : '+str(backup or '(nouveau fichier)'))
            return True
        except (OSError,ValueError,ValidationError) as e:
            self._error('Enregistrement impossible',e);return False

    def validate(self):
        if not self.selection:return
        key=self.selection;kind=key[0]
        try:
            data=json.loads(self.text.get('1.0','end-1c')) if kind in {'category','profile','layout','family'} else None
            if kind=='layout':validate_layout(data,key[1])
            elif kind=='category':
                previous=read_object(self.root_folder/'template_library'/key[1]/'category.json')
                validate_category(data,key[1],previous=previous)
            elif kind=='profile':validate_profile(data,key[1],self.inv['layouts'])
            elif kind=='family':validate_family_template(data,key[1],key[2])
            template_inventory(self.root_folder)
            self._status('Validation réussie : contrat édité et inventaire sur disque')
            messagebox.showinfo('Validation','Contrat JSON cohérent et inventaire sur disque vérifié.\nCela ne valide pas un RuntimeSet SemantiK ni la publication.',parent=self)
        except (OSError,ValueError,ValidationError) as e:self._error('Contrat invalide',e)

    def add_category(self):
        if not self.confirm_discard():return
        name=simpledialog.askstring('Nouvelle catégorie','Identifiant (ex. poster, briefing) :',parent=self)
        if not name:return
        description=simpledialog.askstring('Description','Description de la catégorie (réservée) :',parent=self)
        if description is None:return
        try:
            create_category(self.root_folder,name,description)
            self.load_inventory(preferred=('category',name))
            messagebox.showinfo('Catégorie créée','Catégorie réservée créée. Un moteur de rendu devra être développé séparément.',parent=self)
        except (OSError,ValidationError) as e:self._error('Création',e)

    def _new_layout(self,source=None):
        name=simpledialog.askstring('Nouveau layout','Identifiant du nouveau layout :',parent=self)
        if not name:return
        try:
            create_layout(self.root_folder,name,source=source)
            self.load_inventory(preferred=('layout',name))
        except (OSError,ValidationError) as e:self._error('Création layout',e)

    def _new_family(self,category,source=None):
        name=simpledialog.askstring('Nouveau brouillon','Identifiant du brouillon :',parent=self)
        if not name:return
        try:
            create_family_template(self.root_folder,category,name,source=source)
            self.load_inventory(preferred=('family',category,name))
        except (OSError,ValidationError) as e:self._error('Création brouillon',e)

    def add_template(self):
        if not self.confirm_discard():return
        kind=self.selection[0] if self.selection else 'root'
        if kind in {'category','family','drafts'}:
            category=self.selection[1]
            if category!='wiki':return self._new_family(category)
        if kind=='profile':
            messagebox.showinfo('Archétypes','Les 19 archétypes viennent d’Arketype : modifie leurs règles existantes, ou crée un nouveau layout partagé.',parent=self)
        self._new_layout()

    def duplicate(self):
        if not self.confirm_discard():return
        kind=self.selection[0] if self.selection else ''
        if kind=='layout':self._new_layout(source=self.selection[1])
        elif kind=='family':self._new_family(self.selection[1],source=self.selection[2])
        else:messagebox.showinfo('Duplication','Sélectionne un layout ou un brouillon de catégorie pour le dupliquer.',parent=self)

    def delete(self):
        if self.preview_busy:return
        if not self.selection or self.selection[0] not in {'layout','family'}:
            messagebox.showinfo('Suppression','Seuls les layouts inutilisés et les brouillons de catégorie peuvent être supprimés.',parent=self);return
        if not self.confirm_discard():return
        key=self.selection
        rel=f'layouts/{key[1]}.json' if key[0]=='layout' else f'template_library/{key[1]}/templates/{key[2]}.json'
        if not messagebox.askyesno('Confirmer la suppression',f'Supprimer {rel} ?\nUne copie de sauvegarde sera conservée hors du dépôt.',parent=self):return
        try:
            backup=delete_template(self.root_folder,rel,self.editor_hash)
            self.load_inventory()
            self._status('Supprimé — sauvegarde : '+str(backup))
        except (OSError,ValidationError) as e:self._error('Suppression interdite',e)

    def open_folder(self):
        try:
            key=self.selection or ('root',)
            if key[0]=='layout' or key[0]=='layouts':folder=self.root_folder/'layouts'
            elif key[0] in {'category','family','drafts'}:folder=self.root_folder/'template_library'/key[1]
            elif key[0] in {'profile','profiles','recipes','recipe'}:folder=self.root_folder/'template_library'/'wiki'
            else:folder=self.root_folder/'template_library'
            if not folder.is_dir() or folder.is_symlink():raise ValidationError('Dossier introuvable ou non sûr')
            if sys.platform=='win32':os.startfile(str(folder))
            elif sys.platform=='darwin':subprocess.Popen(['open',str(folder)])
            else:subprocess.Popen(['xdg-open',str(folder)])
        except (OSError,ValidationError) as e:self._error('Ouverture dossier',e)

    def reload(self):
        if self.confirm_discard():self.load_inventory(preferred=self.selection)


def main():
    global ROOT
    try:
        if sys.version_info < (3, 10):
            raise RuntimeError('Spek exige Python 3.10 ou plus recent. Version detectee : ' + sys.version.split()[0])
        ROOT = _find_repo()
        _load_spek(ROOT)
        if '--diagnostic' in sys.argv:
            inv = template_inventory(ROOT)
            print('OK - Spek : ' + str(ROOT))
            print('OK - Categories : ' + str(len(inv['categories'])))
            print('OK - Layouts : ' + str(len(inv['layouts'])))
            print('OK - Archetypes : ' + str(len(inv['profiles'])))
            return 0
        TemplateManagerApp().mainloop()
        return 0
    except Exception as exc:
        detail = traceback.format_exc()
        _record_error(detail)
        _show_fatal('Spek - echec de demarrage', str(exc))
        return 1


if __name__ == '__main__':
    sys.exit(main())
