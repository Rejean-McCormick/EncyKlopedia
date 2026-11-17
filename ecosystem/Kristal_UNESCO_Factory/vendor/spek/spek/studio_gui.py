"""Spek Studio — interface opérateur guidée, hors du gestionnaire technique.

Le registre contient des décisions éditoriales IA hors ligne. L'interface
ne déduit aucun template, ne sélectionne aucune assertion et ne publie rien.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from .ai_proposals import read_proposals
from .composition_registry import read_registry
from .core import ValidationError
from .local_kristals import discover_locals_root, find_local_kristal, save_locals_root, validate_locals_root
from .studio_view_model import display_name, filter_catalog, resolve_display, template_label
from .studio_workflow import execute_preview, inspect_kristal, project_pair

BRAND = '#1e6864'
DARK = '#152f2d'
MUTED = '#576e6a'
BG = '#f4f8f7'
WHITE = '#ffffff'
PALE = '#e4f2ef'
BORDER = '#d4e6e1'
AMBER = '#936b24'


def initial_window_size(screen_width: int, screen_height: int) -> tuple[int, int]:
    """Keep the whole window visible on a small Windows desktop.

    Screen dimensions are display measurements, not application content.  The
    workspace itself can scroll; there is no reason to open wider than the
    monitor (the former 1270px fixed geometry hid the right-side controls).
    """
    width = min(1270, max(620, int(screen_width) - 48))
    height = min(820, max(500, int(screen_height) - 90))
    return width, height


class ScrollPage(ttk.Frame):
    """Simple accessible scrolling region; width follows the notebook tab."""
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=BG)
        self.scroll = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.body = ttk.Frame(self.canvas, style='Surface.TFrame', padding=(24, 20))
        self.window = self.canvas.create_window((0, 0), window=self.body, anchor='nw')
        self.body.bind('<Configure>', lambda _: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfigure(self.window, width=e.width))

    def clear(self):
        for child in self.body.winfo_children():
            child.destroy()
        self.canvas.yview_moveto(0)


class StudioApp(tk.Tk):
    def __init__(self, root: Path):
        super().__init__()
        self.root_folder = Path(root).resolve()
        self.title('Spek — Atelier de composition')
        width, height = initial_window_size(self.winfo_screenwidth(), self.winfo_screenheight())
        self.geometry(f'{width}x{height}')
        self.minsize(min(820, width), min(550, height))
        self.configure(background=BG)
        self.registry = read_registry(self.root_folder)
        self.proposals = read_proposals(self.root_folder, self.registry)
        self.browsed_slug: str | None = None
        self.locals_root: Path | None = discover_locals_root(self.root_folder)
        self.local_candidate: Path | None = None
        self.local_lookup_issue: str | None = None
        self.kristal_details: dict | None = None
        self.article_path: Path | None = None
        self.realizations_path: Path | None = None
        self.preview_ready = False
        self.busy = False
        self._logo = None
        self._catalog_keys: list[str] = []
        self._init_styles()
        self._build()
        self._refresh_catalog()
        self._refresh_all()
        self.bind('<F1>', lambda _: self.show_help())
        self.bind('<Control-o>', lambda _: self.open_kristal())
        self.bind('<Control-l>', lambda _: self.open_article())
        self.bind('<F5>', lambda _: self.reload_catalog())

    def _init_styles(self):
        style = ttk.Style(self)
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        style.configure('TFrame', background=BG)
        style.configure('TLabel', background=BG, foreground=DARK, font=('Segoe UI', 10))
        style.configure('Surface.TFrame', background=BG)
        style.configure('White.TFrame', background=WHITE)
        style.configure('White.TLabel', background=WHITE, foreground=DARK)
        style.configure('Muted.TLabel', background=BG, foreground=MUTED)
        style.configure('Small.TLabel', background=BG, foreground=MUTED, font=('Segoe UI', 9))
        style.configure('Title.TLabel', background=BG, foreground=DARK, font=('Segoe UI', 20, 'bold'))
        style.configure('Section.TLabel', background=BG, foreground=DARK, font=('Segoe UI', 13, 'bold'))
        style.configure('Accent.TLabel', background=BG, foreground=BRAND, font=('Segoe UI', 10, 'bold'))
        style.configure('Header.TFrame', background=WHITE)
        style.configure('Header.TLabel', background=WHITE, foreground=BRAND)
        style.configure('TButton', padding=(12, 8), background=WHITE, foreground=BRAND, bordercolor=BORDER)
        style.map('TButton', background=[('active', PALE), ('disabled', '#eef1f0')], foreground=[('disabled', '#8c9b98')])
        style.configure('Primary.TButton', padding=(13, 9), background=BRAND, foreground=WHITE, bordercolor=BRAND)
        style.map('Primary.TButton', background=[('active', '#14534f'), ('disabled', '#e9efed')], foreground=[('disabled', '#82928e')])
        style.configure('TNotebook', background=BG, borderwidth=0)
        style.configure('TNotebook.Tab', padding=(18, 11), background='#eaf2f0', foreground=BRAND, font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', WHITE)], foreground=[('selected', DARK)])
        style.configure('TEntry', padding=7, fieldbackground=WHITE)
        style.configure('Catalog.Treeview', rowheight=31, background=WHITE, fieldbackground=WHITE,
                        foreground=DARK, borderwidth=0, font=('Segoe UI', 10))
        style.map('Catalog.Treeview', background=[('selected', PALE)], foreground=[('selected', DARK)])
        style.configure('TCombobox', padding=4)

    def _build(self):
        header = ttk.Frame(self, style='Header.TFrame', padding=(22, 12))
        header.pack(fill='x')
        try:
            path = self.root_folder / 'assets' / 'spek-logo.png'
            if path.is_file():
                self._logo = tk.PhotoImage(file=str(path))
                ttk.Label(header, image=self._logo, style='Header.TLabel').pack(side='left', padx=(0, 15))
        except (OSError, tk.TclError):
            pass
        brand_copy = ttk.Frame(header, style='Header.TFrame')
        brand_copy.pack(side='left')
        ttk.Label(brand_copy, text='SPEK · ATELIER DE COMPOSITION',
                  style='Header.TLabel', font=('Segoe UI', 15, 'bold')).pack(anchor='w')
        ttk.Label(brand_copy, text='Un Kristal · un plan documentaire · un aperçu contrôlé',
                  style='Header.TLabel', font=('Segoe UI', 9)).pack(anchor='w')
        ttk.Button(header, text='Aide  F1', command=self.show_help).pack(side='right')
        ttk.Button(header, text='Outils avancés', command=self.open_advanced).pack(side='right', padx=(0, 8))

        toolbar = ttk.Frame(self, padding=(17, 9))
        toolbar.pack(fill='x')
        ttk.Button(toolbar, text='Ouvrir un Kristal…', command=self.open_kristal,
                   style='Primary.TButton').pack(side='left')
        ttk.Button(toolbar, text='Charger un article…', command=self.open_article).pack(side='left', padx=(8, 0))
        ttk.Label(toolbar, text='Langue :').pack(side='left', padx=(23, 5))
        self.lang_var = tk.StringVar(value='fr')
        self.language = ttk.Combobox(toolbar, textvariable=self.lang_var,
                                     values=('fr', 'en', 'it'), state='readonly', width=5)
        self.language.pack(side='left')
        self.status_top = tk.StringVar(value='Aucune publication automatique')
        ttk.Label(toolbar, textvariable=self.status_top, style='Small.TLabel').pack(side='right')

        outer = ttk.Panedwindow(self, orient='horizontal')
        self.workspace_pane = outer
        outer.pack(fill='both', expand=True, padx=12, pady=(0, 8))
        left = ttk.Frame(outer, padding=(9, 12))
        outer.add(left, weight=1)
        ttk.Label(left, text='EXPLORER LES KRISTALS', style='Accent.TLabel').pack(anchor='w', pady=(0, 6))
        ttk.Label(left, text='Rechercher parmi les propositions IA', style='Small.TLabel').pack(anchor='w')
        self.search_var = tk.StringVar()
        self.search = ttk.Entry(left, textvariable=self.search_var)
        self.search.pack(fill='x', pady=(8, 7))
        self.search.bind('<KeyRelease>', lambda _: self._refresh_catalog())
        self.count_var = tk.StringVar(value='')
        ttk.Label(left, textvariable=self.count_var, style='Small.TLabel').pack(anchor='w', pady=(0, 7))
        locals_row = ttk.Frame(left)
        locals_row.pack(fill='x', pady=(0, 9))
        self.locals_status = tk.StringVar(value='')
        ttk.Label(locals_row, textvariable=self.locals_status, style='Small.TLabel',
                  wraplength=170).pack(side='left', fill='x', expand=True)
        ttk.Button(locals_row, text='Dossier locals…', command=self.choose_locals_root).pack(side='right')
        tree_box = ttk.Frame(left)
        tree_box.pack(fill='both', expand=True)
        self.catalog = ttk.Treeview(tree_box, show='tree', selectmode='browse', style='Catalog.Treeview')
        sy = ttk.Scrollbar(tree_box, orient='vertical', command=self.catalog.yview)
        self.catalog.configure(yscrollcommand=sy.set)
        self.catalog.pack(side='left', fill='both', expand=True)
        sy.pack(side='right', fill='y')
        self.catalog.bind('<<TreeviewSelect>>', self._select_catalog)
        self.catalog.bind('<Return>', self._select_catalog)
        ttk.Label(left, text='Catalogue : propositions IA, pas des publications approuvées.',
                  style='Small.TLabel', wraplength=230, justify='left').pack(anchor='w', pady=(9, 0))

        right = ttk.Frame(outer)
        outer.add(right, weight=4)
        self.workspace_heading = tk.StringVar(value='Choisis un Kristal pour commencer')
        ttk.Label(right, textvariable=self.workspace_heading,
                  style='Title.TLabel', wraplength=780).pack(anchor='w', padx=(12, 6), pady=(6, 1))
        self.workspace_sub = tk.StringVar(value='Les propositions sont disponibles même sans ouvrir les sources locales.')
        sub_label = ttk.Label(right, textvariable=self.workspace_sub, style='Muted.TLabel',
                              wraplength=540, justify='left')
        sub_label.pack(anchor='w', padx=(12, 6), pady=(0, 10), fill='x')
        right.bind('<Configure>', lambda e: sub_label.configure(wraplength=max(240, e.width - 35)), add='+')
        self.tabs = ttk.Notebook(right)
        self.tabs.pack(fill='both', expand=True)
        self.pages = [ScrollPage(self.tabs) for _ in range(4)]
        for page, name in zip(self.pages, ['1 · Kristal', '2 · Composition', '3 · Aperçu Wiki', '4 · Publication']):
            self.tabs.add(page, text=name)
        self.tabs.bind('<<NotebookTabChanged>>', lambda _: self._update_actions())

        foot = ttk.Frame(self, padding=(13, 5))
        foot.pack(fill='x')
        self.feedback = tk.StringVar(value='Prêt · Travail local, aucune publication')
        ttk.Label(foot, textvariable=self.feedback, style='Small.TLabel').pack(anchor='w')
        self.after_idle(self._fit_sidebar)

    def _fit_sidebar(self):
        """Prioritize the active workspace rather than an oversized catalog."""
        try:
            width = self.workspace_pane.winfo_width()
            if width > 100:
                self.workspace_pane.sashpos(0, min(320, max(260, width // 3)))
        except (tk.TclError, AttributeError):
            pass

    def _refresh_catalog(self):
        self._catalog_keys = filter_catalog(self.proposals, self.search_var.get())
        selected = self.browsed_slug
        self.catalog.delete(*self.catalog.get_children())
        for slug in self._catalog_keys:
            self.catalog.insert('', 'end', iid=slug, text=display_name(slug, self.proposals))
        if selected in self._catalog_keys:
            self.catalog.selection_set(selected)
            self.catalog.see(selected)
        self.count_var.set(f'{len(self._catalog_keys)} / {len(self.proposals)} Kristals')

    def _select_catalog(self, _event=None):
        if self.busy:
            return
        selected = self.catalog.selection()
        if not selected:
            return
        slug = selected[0]
        if slug == self.browsed_slug:
            return
        # A catalogue consultation is explicitly NOT a local canonical source inspection.
        # Never carry an article from the previous Kristal into the new context.
        self.article_path = None
        self.realizations_path = None
        self.preview_ready = False
        self.browsed_slug = slug
        self.kristal_details = None
        self._refresh_all()
        self.feedback.set('Proposition IA consultée · Aucune source locale ouverte')

    def _update_local_candidate(self):
        """Locate source by declared identity; opening state remains a user action."""
        self.local_candidate = None
        self.local_lookup_issue = None
        if self.locals_root is None:
            self.locals_status.set('Dossier locals à choisir')
        else:
            self.locals_status.set('Collection locale configurée')
        if not (self.browsed_slug and self.locals_root):
            return
        try:
            self.local_candidate = find_local_kristal(self.locals_root, self.browsed_slug)
        except (OSError, ValueError, ValidationError) as exc:
            self.local_lookup_issue = str(exc)

    def _model(self):
        return resolve_display(self.proposals, self.browsed_slug, self.kristal_details)

    def _refresh_all(self):
        self._update_local_candidate()
        model = self._model()
        title = model['title'] or 'Choisis un Kristal pour commencer'
        self.workspace_heading.set(title)
        if not model['slug']:
            sub = 'Sélectionne un Kristal à gauche, ou ouvre son dossier local.'
        elif model['has_local_source']:
            sub = 'Source locale ouverte en lecture seule · Composition IA en cours de revue'
        else:
            sub = ('Dossier local identifié · Clique sur « Ouvrir les sources » pour le consulter'
                   if self.local_candidate else 'Proposition consultée · Sources locales non ouvertes')
        self.workspace_sub.set(sub)
        for idx, painter in enumerate((self._draw_kristal, self._draw_composition,
                                       self._draw_preview, self._draw_publication)):
            page = self.pages[idx]
            page.clear()
            painter(page.body, model)
        self._update_actions()

    def _heading(self, parent, title: str, subtitle: str | None = None):
        ttk.Label(parent, text=title, style='Section.TLabel').pack(anchor='w', pady=(0, 5))
        if subtitle:
            # The section body is recreated on each selection.  Do not bind
            # its resize event to a soon-to-be-destroyed label: otherwise
            # Tkinter calls a stale widget when the next Kristal is selected.
            ttk.Label(parent, text=subtitle, foreground=MUTED,
                      wraplength=495, justify='left').pack(anchor='w', fill='x', pady=(0, 15))

    def _card(self, parent, title: str, description: str, *, tone: str = 'regular'):
        wrap = tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        wrap.pack(fill='x', pady=(0, 9))
        inside = tk.Frame(wrap, bg=WHITE, padx=15, pady=12)
        inside.pack(fill='x')
        color = BRAND if tone == 'good' else AMBER if tone == 'warn' else DARK
        tk.Label(inside, text=title, bg=WHITE, fg=color, font=('Segoe UI', 11, 'bold'),
                 anchor='w', justify='left').pack(anchor='w', fill='x')
        if description:
            label = tk.Label(inside, text=description, bg=WHITE, fg=MUTED,
                             font=('Segoe UI', 10), anchor='w', justify='left', wraplength=730)
            label.pack(anchor='w', pady=(5, 0), fill='x')
            inside.bind('<Configure>', lambda e, lbl=label: lbl.configure(wraplength=max(250, e.width - 15)))
        return inside

    def _button(self, parent, text, callback, *, primary=False, enabled=True):
        b = ttk.Button(parent, text=text, command=callback,
                       style='Primary.TButton' if primary else 'TButton')
        b.pack(side='left', padx=(0, 8), pady=(3, 7))
        b.configure(state='normal' if enabled and not self.busy else 'disabled')
        return b

    def _draw_kristal(self, body, m):
        self._heading(body, 'Découvrir le Kristal',
                      'Un point de départ simple : consulter son plan, ou ouvrir sa source canonique locale.')
        if not m['slug']:
            self._card(body, 'Choisis dans le catalogue',
                       'Utilise la recherche à gauche ou clique sur « Ouvrir un Kristal ».')
            return
        self._card(body, m['title'], 'Identifiant : ' + str(m['slug']))
        if m['has_local_source']:
            self._card(body, 'Sources locales ouvertes',
                       'Ce Kristal a été ouvert en lecture seule. Sa composition reste une proposition.', tone='good')
        elif self.local_candidate:
            self._card(body, 'Dossier local trouvé',
                       'L’identité déclarée correspond au Kristal sélectionné. Tu peux ouvrir ses sources en lecture seule.', tone='good')
        elif self.local_lookup_issue:
            self._card(body, 'Recherche du dossier à vérifier', self.local_lookup_issue, tone='warn')
        elif not self.locals_root:
            self._card(body, 'Indiquer la collection locale',
                       'Choisis une fois le dossier locals afin que Spek puisse retrouver les Kristals par leur identité.', tone='warn')
        else:
            self._card(body, 'Dossier local introuvable',
                       'Aucun dossier de cette collection ne déclare cet identifiant. Choisis un autre dossier locals ou ouvre manuellement le Kristal.', tone='warn')
        if m['has_structural_review']:
            self._card(body, 'Revue structurelle existante',
                       ('L’état local correspond à la source étudiée. L’exploration privée est disponible.'
                        if m['source_verified'] else
                        'Une étude structurelle existe ; ouvre la source locale correspondante pour vérifier son état.'),
                       tone='good' if m['source_verified'] else 'warn')
        else:
            self._card(body, 'Analyse approfondie à réaliser',
                       'Le plan actuel provient du rapport global. Ses parties canoniques restent à examiner.')
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(6, 0))
        self._button(actions, 'Voir sa composition', lambda: self.tabs.select(1), primary=True)
        if self.local_candidate:
            self._button(actions, 'Ouvrir les sources de ce Kristal', self.open_selected_sources)
        else:
            self._button(actions, 'Choisir un dossier local…', self.open_kristal)
        self._button(actions, 'Aperçu Wiki', lambda: self.tabs.select(2))

    def _draw_composition(self, body, m):
        count = len(m['sections'])
        self._heading(body, 'Plan documentaire proposé',
                      'Combinaison choisie par l’IA et inscrite au registre. Spek ne la devine pas et ne la valide pas automatiquement.')
        if not m['proposal']:
            self._card(body, 'Aucune composition consultée', 'Sélectionne un Kristal à gauche.')
            return
        self._card(body, f'{count} parties documentaires',
                   'Proposition éditoriale · À vérifier avant toute utilisation publique.', tone='warn')
        for index, sec in enumerate(m['sections'], start=1):
            description = template_label(sec['type'])
            if m['has_structural_review']:
                description += ' · Étude structurelle disponible, publication non approuvée'
            else:
                description += ' · Sources détaillées encore à examiner'
            self._card(body, f'{index:02d}  {sec["title"]}', description)
        self._card(body, 'Étape suivante',
                   'Vérifier chaque partie contre les assertions canoniques, sélectionner les faits autorisés, puis obtenir les formulations SemantiK.')

    def _draw_preview(self, body, m):
        self._heading(body, 'Aperçu du Wiki',
                      'Un plan documentaire n’est pas un texte. Seul SemantiK Architect réalise les phrases qui remplissent les templates.')
        if not m['slug']:
            self._card(body, 'Choisis un Kristal', 'Sélectionne d’abord un Kristal dans la liste à gauche.')
            return

        # A structural review does not grant publication permission. Lookup is
        # identity-only; the user must explicitly initiate source inspection.
        if m['source_verified']:
            structural_state = 'Les sources ouvertes correspondent à l’étude disponible.'
            structural_enabled = True
        elif m['has_structural_review'] and self.local_candidate:
            structural_state = 'Dossier local identifié. L’outil vérifiera la correspondance des sources avant de créer l’aperçu.'
            structural_enabled = True
        elif m['has_structural_review'] and not self.locals_root:
            structural_state = 'Indique le dossier locals pour que Spek retrouve la source de ce Kristal.'
            structural_enabled = False
        elif m['has_structural_review']:
            structural_state = ('L’état local ne correspond pas à l’étude disponible.' if m['has_local_source'] else
                                'La source correspondante n’a pas été trouvée dans locals.')
            structural_enabled = False
        else:
            structural_state = 'L’analyse structurelle détaillée de ce Kristal reste à réaliser.'
            structural_enabled = False
        self._card(body, '1 · Consulter le plan documentaire (sans phrases)', structural_state,
                   tone='good' if m['source_verified'] else 'regular')
        row = ttk.Frame(body)
        row.pack(fill='x', pady=(0, 17))
        if structural_enabled:
            self.private_preview_btn = self._button(
                row, 'Explorer la structure privée', self.explore_selected_structure, primary=True)
        else:
            # For the 122 Kristals without a detailed canonical review, a
            # disabled structural-preview button was misleading. Their plans
            # remain available in the Composition tab, but source inspection
            # cannot be represented as a verified structural review.
            self.private_preview_btn = None
            self._button(row, 'Voir le plan proposé', lambda: self.tabs.select(1), primary=True)
            if self.local_candidate:
                self._button(row, 'Ouvrir les sources trouvées', self.open_selected_sources)
            else:
                self._button(row, 'Choisir le dossier local…' if self.locals_root else 'Configurer locals…',
                             self.open_kristal if self.locals_root else self.choose_locals_root)

        ready = bool(self.article_path and self.realizations_path)
        self._card(body, '2 · Réaliser les phrases avec SemantiK',
                   ('Un article et ses formulations ont été chargés. Vérifie qu’ils concernent bien ce Kristal avant le rendu.' if ready else
                    'Il faut un article.json, des requêtes sémantiques explicites et un RuntimeSet GF/PGF utilisable. Spek ne transforme jamais automatiquement les triplets bruts en prose.'),
                   tone='good' if ready else 'regular')
        row2 = ttk.Frame(body)
        row2.pack(fill='x', pady=(0, 8))
        self._button(row2, 'Réaliser avec SemantiK…', self.realize_with_semantik, primary=True)
        self.render_btn = self._button(row2, 'Prévisualiser le Wiki', self.preview_wiki, enabled=ready)
        self._button(row2, 'Vérifier', lambda: self.run_compiler(False), enabled=ready)
        phrase_row = ttk.Frame(body)
        phrase_row.pack(fill='x', pady=(0, 10))
        self._button(phrase_row, 'Voir les formes demandées par Spek…', self.show_phrase_dialogue)
        if not ready:
            self._card(body, 'Texte non disponible',
                       'Le plan peut être consulté, mais un vrai Wiki exige des phrases SemantiK. '
                       'Aucun code brut ne sera utilisé comme texte de remplacement.', tone='warn')

        # Extra preparation actions are secondary rather than mandatory steps.
        options = ttk.Frame(body)
        options.pack(fill='x', pady=(3, 9))
        self.semantik_options_visible = tk.BooleanVar(value=False)
        details = ttk.Frame(body)
        def toggle_options():
            if self.semantik_options_visible.get():
                details.pack(fill='x', pady=(0, 10), after=options)
            else:
                details.pack_forget()
        ttk.Checkbutton(options, text='Options de préparation SemantiK',
                        variable=self.semantik_options_visible, command=toggle_options).pack(anchor='w')
        self._button(details, 'Charger article et formulations…', self.open_article)
        self._button(details, 'Importer des résultats SemantiK…', self.import_semantik)
        self._button(details, 'Préparer une correspondance…', self.prepare_semantik_mapping)
        self._button(details, 'Prévisualiser une composition récursive…', self.preview_recursive_composition)
        self._button(details, 'Auditer les mouvements rhétoriques…', self.audit_discourse_composition)
        self._card(body, 'Aperçus privés',
                   'Aucune de ces actions ne publie sur GitHub et ne remplace les autorisations C1 / C2 / C3.')

    def audit_discourse_composition(self):
        """Show declared discourse structure, not assertions or authorization."""
        if self.busy:
            return
        instance = filedialog.askopenfilename(parent=self,
            title='Choisir une composition récursive explicite pour audit',
            filetypes=[('Compositions JSON', '*.json')])
        if not instance:
            return
        try:
            from .composition.commands import load
            from .composition.discourse import discourse_audit
            report = discourse_audit(load(self.root_folder, Path(instance)))
            msg = (f"{report['templates_with_discourse_model']} modèles discursifs inclus\n"
                   f"{report['declared_relations_unverified']} relations déclarées à vérifier\n"
                   '0 transition créée automatiquement\n\n'
                   'Les mouvements définissent la lecture et les paragraphes.\n'
                   'Les phrases de liaison exigent une réalisation SemantiK explicite.\n'
                   'Cet audit ne certifie ni les faits, ni les relations, ni la publication.')
            messagebox.showinfo('Spek · Audit rhétorique privé', msg, parent=self)
        except (OSError, ValueError, ValidationError) as exc:
            self._error('Audit rhétorique', exc)

    def preview_recursive_composition(self):
        """Explicit vNext preview, no templates inferred from Kristal contents."""
        if self.busy:
            return
        instance = filedialog.askopenfilename(parent=self, title='Composition récursive explicitement préparée',
                   filetypes=[('Compositions JSON','*.json')])
        if not instance:
            return
        phrases = filedialog.askopenfilename(parent=self, title='Réalisations SemantiK déjà disponibles',
                  filetypes=[('Réalisations JSON','*.json')])
        if not phrases:
            return
        try:
            from .composition.commands import preview
            output=Path(tempfile.mkdtemp(prefix='spek-vnext-cible-'))
            output.rmdir()  # preview requires a new destination
            result=preview(self.root_folder,Path(instance),Path(phrases),self.lang_var.get(),output)
            webbrowser.open(Path(result['page']).as_uri())
            self.feedback.set('Composition récursive ouverte · aperçu privé, non publiable')
        except (OSError, ValueError, ValidationError) as exc:
            self._error('Composition récursive', exc)

    def _draw_publication(self, body, m):
        self._heading(body, 'État de préparation du Wiki',
                      'Un tableau de bord informatif. Les autorisations sont vérifiées par le pipeline externe, pas par cet atelier.')
        if m['proposal']:
            self._card(body, '1 · Plan documentaire proposé',
                       'Les sections sont définies, mais la composition IA n’est pas approuvée.', tone='warn')
        else:
            self._card(body, '1 · Plan documentaire manquant',
                       'Sélectionne une proposition dans le registre.', tone='warn')
        self._card(body, '2 · Sources et faits autorisés',
                   ('Revue structurelle consultable, mais aucune sélection de faits n’est approuvée.'
                    if m['source_verified'] else
                    'Revue des sources et sélection des assertions à effectuer.'), tone='warn')
        self._card(body, '3 · Formulations SemantiK',
                   ('Formulations chargées pour contrôle local ; qualification externe à confirmer.'
                    if self.realizations_path else 'Formulations linguistiques non chargées.'), tone='warn')
        self._card(body, '4 · Contrôles C1 / C2 / C3',
                   'Non vérifiés dans cet atelier. Les validations du Manager restent obligatoires.', tone='warn')
        self._card(body, '5 · Mise en ligne GitHub Wiki',
                   'Aucune publication automatique. Le dépôt public n’est pas modifié ici.')
        row = ttk.Frame(body)
        row.pack(fill='x', pady=(8, 0))
        self._button(row, 'Voir la procédure de publication', self.open_publishing_guide)
        self._button(row, 'Retour à la composition', lambda: self.tabs.select(1))

    def _update_actions(self):
        busy = self.busy
        self.language.configure(state='disabled' if busy else 'readonly')
        self.search.configure(state='disabled' if busy else 'normal')
        if self.browsed_slug:
            self.status_top.set('Aperçu et travail privés · Publication non autorisée')
        else:
            self.status_top.set('Sélectionne un Kristal · Aucune publication')
        # Buttons are rebuilt on state changes. Disable all while background jobs run.
        for attr in ('private_preview_btn', 'check_btn', 'render_btn'):
            btn = getattr(self, attr, None)
            if btn and btn.winfo_exists() and busy:
                btn.configure(state='disabled')

    def _error(self, title: str, exc: Exception | str):
        self.feedback.set('Action impossible · ' + str(exc)[:150])
        messagebox.showerror(title, str(exc), parent=self)

    def choose_locals_root(self):
        if self.busy:
            return
        selected = filedialog.askdirectory(parent=self, title='Choisir la collection de Kristals (dossier locals)',
                  initialdir=str(self.locals_root or self.root_folder.parent))
        if not selected:
            return
        try:
            folder = validate_locals_root(Path(selected))
            save_locals_root(folder)
            self.locals_root = folder
            # A newly chosen root cannot retroactively verify an old source.
            self.kristal_details = None
            self._refresh_all()
            self.feedback.set('Collection locale enregistrée · La recherche utilise les identités déclarées')
        except (OSError, ValueError, ValidationError) as exc:
            self._error('Configuration du dossier locals', exc)

    def _load_local_kristal(self, folder: Path, *, expected_slug: str | None = None):
        details = inspect_kristal(folder, self.root_folder)
        slug = details.get('identity')
        if not slug:
            raise ValidationError('Le Kristal ne déclare pas d’identifiant utilisable.')
        if expected_slug is not None and slug != expected_slug:
            raise ValidationError('Le dossier choisi ne correspond pas au Kristal sélectionné.')
        # Atomic UI change: never replace state with a mismatched Kristal.
        if slug != self.browsed_slug:
            self.article_path = None
            self.realizations_path = None
            self.preview_ready = False
        self.kristal_details = details
        self.browsed_slug = slug
        self.search_var.set('')
        self._refresh_catalog()
        self._refresh_all()
        self.feedback.set('Sources ouvertes en lecture seule · Aucune publication')

    def open_selected_sources(self):
        """Explicitly open the matched local source, not just a catalog entry."""
        if self.busy or not self.browsed_slug:
            return False
        self._update_local_candidate()
        if self.local_candidate is None:
            messagebox.showinfo('Sources introuvables',
                 'Choisis le dossier locals ou utilise « Ouvrir un Kristal… » pour sélectionner manuellement la source.', parent=self)
            return False
        try:
            self._load_local_kristal(self.local_candidate, expected_slug=self.browsed_slug)
            return True
        except (OSError, ValueError, ValidationError) as exc:
            self._error('Vérification des sources', exc)
            return False

    def open_kristal(self):
        if self.busy:
            return
        folder = filedialog.askdirectory(parent=self, title='Choisir le dossier du Kristal à consulter',
                                         initialdir=str(self.locals_root or self.root_folder.parent))
        if not folder:
            return
        try:
            self._load_local_kristal(Path(folder))
            self.tabs.select(0)
        except (ValueError, OSError, ValidationError) as exc:
            self._error('Ouverture du Kristal', exc)

    def explore_selected_structure(self):
        """One action: open exact sources when found, verify state, then inspect."""
        model = self._model()
        if not model['source_verified']:
            if not model['has_structural_review'] or not self.open_selected_sources():
                return
            model = self._model()
        if model['source_verified']:
            self.open_structural_preview()
        else:
            messagebox.showinfo('Sources à vérifier',
                'Le dossier a été ouvert, mais son état ne correspond pas à celui de l’étude. Aucun aperçu n’a été généré.',parent=self)

    def preview_wiki(self):
        """One action: ask for explicit article and SemantiK results if absent."""
        if self.busy:
            return
        if not (self.article_path and self.realizations_path):
            if not self.open_article():
                return
        self.run_compiler(True)

    def open_article(self):
        if self.busy:
            return False
        article = filedialog.askopenfilename(parent=self, title='Choisir article.json',
                                            filetypes=[('Fichiers JSON', '*.json')])
        if not article:
            return False
        realizations = filedialog.askopenfilename(parent=self,
                         title='Choisir les formulations réalisations.json',
                         initialdir=str(Path(article).parent), filetypes=[('Fichiers JSON', '*.json')])
        if not realizations:
            return False
        try:
            self.article_path, self.realizations_path = project_pair(Path(article), Path(realizations))
            self.preview_ready = False
            self._refresh_all()
            self.tabs.select(2)
            self.feedback.set('Projet chargé · Vérification locale recommandée')
            return True
        except (ValueError, OSError, ValidationError) as exc:
            self._error('Fichiers non admissibles', exc)
            return False

    def show_phrase_dialogue(self):
        """Visualiser la décision de forme prise par Spek pour chaque slot.

        Aucun Kristal n'est parcouru, aucun fait ni texte n'est généré.
        """
        article = self.article_path
        if article is None:
            selected = filedialog.askopenfilename(
                parent=self, title='Choisir un article Spek déjà composé (article.json)',
                initialdir=str(self.root_folder), filetypes=[('Fichiers JSON', '*.json')])
            if not selected:
                return
            article = Path(selected)
        try:
            from .slot_dialogue import from_files
            plan = from_files(article, self.root_folder / 'layouts', self.lang_var.get())
        except (OSError, ValueError, ValidationError) as exc:
            self._error('Formes de phrases', exc)
            return
        dialogue = tk.Toplevel(self)
        dialogue.title('Spek · Formes demandées à SemantiK')
        dialogue.geometry('850x525')
        dialogue.minsize(600, 350)
        ttk.Label(dialogue, text='Spek choisit la forme, SemantiK réalise la phrase',
                  font=('Segoe UI', 13, 'bold'), foreground=BRAND).pack(anchor='w', padx=15, pady=(15, 4))
        ttk.Label(dialogue, text='Ces prescriptions proviennent des slots du layout. Les faits, obligations et preuves restent définis ailleurs.',
                  wraplength=785, justify='left').pack(anchor='w', padx=15, pady=(0, 12))
        box = ttk.Frame(dialogue, padding=(12, 0, 12, 6))
        box.pack(fill='both', expand=True)
        tree = ttk.Treeview(box, columns=('champ','forme','blocs'), show='headings')
        tree.heading('champ', text='Champ du template')
        tree.heading('forme', text='Forme souhaitée')
        tree.heading('blocs', text='Type transmis à SemantiK')
        tree.column('champ', width=330)
        tree.column('forme', width=205)
        tree.column('blocs', width=210)
        bar = ttk.Scrollbar(box, command=tree.yview)
        tree.configure(yscrollcommand=bar.set)
        tree.pack(side='left', fill='both', expand=True)
        bar.pack(side='right', fill='y')
        for field in plan['fields'].values():
            loc = field['locations'][0]
            if loc['scope'] == 'slot':
                label = str(loc['section']) + ' / ' + str(loc['slot'])
            elif loc['scope'] == 'section':
                label = str(loc['section']) + ' / titre'
            else:
                label = 'Article / ' + str(loc['field']).replace('_key', '')
            tree.insert('', 'end', values=(label,
                field['intent'].replace('_', ' '), ', '.join(field['block_kinds'])))
        ttk.Label(dialogue, text=f"{len(plan['fields'])} champs · Aperçu privé · Aucune réalisation ni publication",
                  foreground=MUTED).pack(anchor='w', padx=15, pady=(0, 12))
        ttk.Button(dialogue, text='Fermer', command=dialogue.destroy).pack(anchor='e', padx=15, pady=(0, 12))

    def realize_with_semantik(self):
        """Exécute les requêtes explicites via le SDK officiel, puis importe les textes contrôlés."""
        if self.busy:
            return
        article = filedialog.askopenfilename(
            parent=self, title='Article Spek à remplir avec SemantiK (article.json)',
            initialdir=str(self.article_path.parent if self.article_path else self.root_folder),
            filetypes=[('Fichiers JSON', '*.json')])
        if not article:
            return
        mapping = filedialog.askopenfilename(
            parent=self, title='Correspondance avec les requêtes SemantiK (mapping.json)',
            initialdir=str(Path(article).parent), filetypes=[('Fichiers JSON', '*.json')])
        if not mapping:
            return
        architect = filedialog.askdirectory(
            parent=self, title='Dossier du dépôt SemantiK Architect (contient src/)',
            initialdir=str(self.root_folder.parent))
        if not architect:
            return
        runtime = Path(architect) / 'runtime'
        if not runtime.is_dir():
            chosen = filedialog.askdirectory(
                parent=self, title='Choisir le dossier RuntimeSets GF/PGF de SemantiK',
                initialdir=str(architect))
            if not chosen:
                return
            runtime = Path(chosen)
        snapshot = None
        try:
            import json
            source_obj = json.loads(Path(article).read_text(encoding='utf-8'))
            if source_obj.get('source', {}).get('origin') == 'kristal_v9':
                selected = filedialog.askopenfilename(
                    parent=self, title='État canonique v9 associé à la sélection',
                    initialdir=str(Path(article).parent), filetypes=[('Fichiers JSON', '*.json')])
                if not selected:
                    return
                snapshot = Path(selected)
        except (OSError, ValueError, AttributeError) as exc:
            self._error('Article illisible', exc)
            return
        from .semantik_execution import realize_mapping
        def action():
            return realize_mapping(Path(article), Path(mapping), Path(architect), Path(runtime),
                                  layouts=self.root_folder / 'layouts', state_snapshot=snapshot)
        def done(result):
            self.article_path = Path(article)
            self.realizations_path = Path(result['realizations'])
            self.lang_var.set(result['language'])
            self.preview_ready = False
            self.tabs.select(2)
            self.feedback.set('Phrases SemantiK reçues et vérifiées · Aperçu privé seulement')
            messagebox.showinfo('Réalisation SemantiK terminée',
                'Les phrases proviennent de SemantiK Architect et ont été contrôlées. '
                'Clique sur « Prévisualiser le Wiki ». Aucune publication n’est autorisée.',
                parent=self)
        self._run_background('Réalisation SemantiK', action, done)

    def prepare_semantik_mapping(self):
        if self.busy:
            return
        article = filedialog.askopenfilename(parent=self, title='Sélectionner article.json',
                                             initialdir=str(self.article_path.parent if self.article_path else self.root_folder),
                                             filetypes=[('Fichiers JSON', '*.json')])
        if not article:
            return
        target = filedialog.asksaveasfilename(parent=self, title='Enregistrer la correspondance à compléter',
                                              initialdir=str(Path(article).parent), initialfile='semantik-mapping.json',
                                              defaultextension='.json', filetypes=[('Fichiers JSON', '*.json')])
        if not target:
            return
        try:
            from .semantik_transfer import prepare_mapping
            result = prepare_mapping(Path(article), self.lang_var.get(), Path(target))
            self.feedback.set('Correspondance créée · À compléter avec les résultats SemantiK')
            messagebox.showinfo('Correspondance créée',
                'Le fichier contient ' + str(result['required_keys']) + ' clés à associer. Aucune requête ni aucun fait n’a été inventé.', parent=self)
        except Exception as exc:
            self._error('Préparation impossible', exc)

    def import_semantik(self):
        if self.busy:
            return
        source = filedialog.askopenfilename(parent=self, title='Choisir article.json',
                     filetypes=[('Fichiers JSON', '*.json')])
        if not source:
            return
        mapping = filedialog.askopenfilename(parent=self, title='Choisir la correspondance SemantiK',
                     initialdir=str(Path(source).parent), filetypes=[('Fichiers JSON', '*.json')])
        if not mapping:
            return
        snapshot = None
        try:
            import json
            source_obj = json.loads(Path(source).read_text(encoding='utf-8'))
            if source_obj.get('source', {}).get('origin') == 'kristal_v9':
                snapshot = filedialog.askopenfilename(parent=self, title='Choisir le snapshot v9 associé',
                          initialdir=str(Path(source).parent), filetypes=[('Fichiers JSON', '*.json')])
                if not snapshot:
                    return
        except (OSError, ValueError, AttributeError) as exc:
            self._error('Article illisible', exc)
            return
        from .semantik_transfer import transfer
        out = Path(tempfile.mkdtemp(prefix='spek-semantik-prive-'))/'transfert'
        def action():
            return transfer(Path(source), Path(mapping), out, layouts=self.root_folder/'layouts',
                            state_snapshot=Path(snapshot) if snapshot else None)
        def done(result):
            self.article_path = Path(source)
            self.realizations_path = Path(result['realizations'])
            self.lang_var.set(result['language'])
            self.preview_ready = False
            self.tabs.select(2)
            messagebox.showinfo('Résultats importés',
                'Correspondance et provenance contrôlées. Les formulations restent privées et non qualifiées.', parent=self)
        self._run_background('Import SemantiK', action, done)

    def open_structural_preview(self):
        m = self._model()
        if not m['source_verified'] or not self.kristal_details or self.busy:
            messagebox.showinfo('Inspection privée non disponible',
                'Il faut une revue structurelle et un fichier local identique à celui qui a été étudié.', parent=self)
            return
        from .structural_preview import create_structural_preview
        folder = Path(self.kristal_details['folder'])
        def action():
            return create_structural_preview(self.root_folder, folder)
        def done(result):
            webbrowser.open(Path(result['page']).as_uri())
        self._run_background('Inspection privée', action, done)

    def run_compiler(self, build: bool):
        if self.busy or not (self.article_path and self.realizations_path):
            return
        def action():
            return execute_preview(self.root_folder, self.article_path,
                                   self.realizations_path, self.lang_var.get(), build=build)
        def done(result):
            if build:
                webbrowser.open(Path(result['page']).as_uri())
                self.feedback.set('Aperçu HTML ouvert dans le navigateur · Non publié')
            else:
                self.preview_ready = True
                self.feedback.set('Vérification locale réussie · Publication non autorisée')
                messagebox.showinfo('Vérification locale',
                    'Le compilateur n’a signalé aucune erreur. Cette vérification ne vaut pas autorisation de publication.', parent=self)
        self._run_background('Prévisualisation' if build else 'Vérification', action, done)

    def _run_background(self, label, action, on_success):
        self.busy = True
        self.feedback.set(label + ' en cours…')
        self._refresh_all()
        def worker():
            try:
                result = action()
            except Exception as exc:
                self.after(0, lambda msg=str(exc): self._finish_task(label, None, msg, on_success))
            else:
                self.after(0, lambda res=result: self._finish_task(label, res, None, on_success))
        threading.Thread(target=worker, daemon=True).start()

    def _finish_task(self, label, result, error, on_success):
        self.busy = False
        self._refresh_all()
        if error:
            self._error(label + ' impossible', error)
        else:
            on_success(result)
            self._refresh_all()

    def open_publishing_guide(self):
        candidates = [
            self.root_folder/'docs'/'PIPELINE_KRISTAL_PUBLIC_GITHUB_WIKI_FR.md',
            self.root_folder/'docs'/'WIKI_PUBLISHING.md',
        ]
        target = next((p for p in candidates if p.is_file()), None)
        if not target:
            messagebox.showinfo('Documentation', 'La documentation de publication est absente.', parent=self)
            return
        webbrowser.open(target.as_uri())

    def open_advanced(self):
        launcher = self.root_folder/'Spek_Template_Manager.pyw'
        try:
            subprocess.Popen([sys.executable, str(launcher), '--advanced'], cwd=str(self.root_folder))
            self.feedback.set('Gestionnaire de templates ouvert dans une fenêtre distincte')
        except OSError as exc:
            self._error('Outils avancés', exc)

    def reload_catalog(self):
        try:
            registry = read_registry(self.root_folder)
            proposals = read_proposals(self.root_folder, registry)
            self.registry, self.proposals = registry, proposals
            if self.browsed_slug not in proposals:
                self.browsed_slug = None
                self.kristal_details = None
            self._refresh_catalog()
            self._refresh_all()
            self.feedback.set('Catalogue actualisé · Proposition seulement')
        except (OSError, ValueError, ValidationError) as exc:
            self._error('Actualisation du catalogue', exc)

    def show_help(self):
        messagebox.showinfo('Spek · Mode d’emploi',
            '1. KRISTAL : cherche un nom à gauche ou ouvre sa source locale.\n\n'
            '2. COMPOSITION : consulte les sections prescrites par l’IA. Aucun template n’est deviné ici.\n\n'
            '3. APERÇU WIKI : « Formes de phrases » montre comment Spek prescrit les formes par champ. « Réaliser avec SemantiK » transmet ces contraintes avec les requêtes préparées et un RuntimeSet disponible, puis « Prévisualiser le Wiki » affiche les phrases contrôlées.\n\n'
            '4. PUBLICATION : identifie les validations restantes C1/C2/C3. Ce programme ne publie rien.\n\n'
            'COMPOSITION RÉCURSIVE vNext : dans Options de préparation SemantiK, tu peux auditer les mouvements rhétoriques, puis prévisualiser une composition avec des réalisations explicites. Aucune transition ou assertion inventée.\n\n'
            'OUTILS AVANCÉS : bibliothèque, 27 layouts et édition JSON dans une fenêtre distincte.\n\n'
            'Choisis le dossier locals une fois dans la colonne de gauche. Raccourcis : Ctrl+O ouvrir un Kristal · Ctrl+L charger un article · F5 actualiser · F1 aide.',
            parent=self)
