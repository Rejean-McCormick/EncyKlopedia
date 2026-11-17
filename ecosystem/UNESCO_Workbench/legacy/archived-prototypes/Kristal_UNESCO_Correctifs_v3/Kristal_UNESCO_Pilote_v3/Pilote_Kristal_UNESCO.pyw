# -*- coding: utf-8 -*-
"""GUI locale v3 pour le pilote Kristal/Spek/SemantiK/GF, pas de publication."""
from __future__ import annotations
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser
from gf_setup import discover_gf, import_official_zip, probe_gf, probe_existing_pgf, DOWNLOAD_PAGE, private_tool_root
from project_paths import KRISTAL_ROOT, SEMANTIK_PROJECT, default_python, runtime_paths, resolve_semantik_project
from pilot import run_pilot, find_latest_run

KRISTAL_DEFAULT = str(KRISTAL_ROOT)
SA_DEFAULT = str(SEMANTIK_PROJECT)

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Kristal UNESCO — Spek / SemantiK / GF — Pilote v3')
        self.geometry('1080x880')
        self.minsize(960, 740)
        self.q = queue.Queue()
        self.cancel_flag = threading.Event()
        self.busy = False
        self.last_zip: str | None = None
        self.vars = {
            'Kristal': tk.StringVar(value=KRISTAL_DEFAULT),
            'SemantiK': tk.StringVar(value=SA_DEFAULT),
            'RUN (automatique)': tk.StringVar(value=''),
            'Python PGF': tk.StringVar(value=default_python()),
            'PGF FR existant': tk.StringVar(value=runtime_paths(SEMANTIK_PROJECT)['pgf_fr']),
            'GF.exe': tk.StringVar(value=''),
            'Concept': tk.StringVar(value='concept10'),
            'Sortie': tk.StringVar(value=str(Path.home() / 'Downloads')),
        }
        self.both = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value='Chemins SemantiK/PGF préremplis. Tester le runtime existant et, séparément, le compilateur GF.')
        self._build()
        self.after(100, self.poll)

    def _build(self):
        top = ttk.Frame(self, padding=15)
        top.pack(fill='x')
        ttk.Label(top, text='Kristal · UNESCO · Spek · SemantiK · GF',
                  font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        ttk.Label(top, text='Pilote privé, lecture seule des dépôts. Aucune publication ni activation de RuntimeSet.',
                  foreground='#536073').pack(anchor='w', pady=(3, 10))
        frame = ttk.Frame(top)
        frame.pack(fill='x')
        for row, name in enumerate(self.vars):
            ttk.Label(frame, text=name, width=24).grid(row=row, column=0, sticky='w', pady=4)
            ent = ttk.Entry(frame, textvariable=self.vars[name], width=76)
            ent.grid(row=row, column=1, sticky='ew', padx=4, pady=4)
            if name != 'Concept':
                ttk.Button(frame, text='…', width=4, command=lambda n=name: self.choose(n)).grid(row=row, column=2)
        frame.columnconfigure(1, weight=1)

        step = ttk.LabelFrame(top, text='1. Runtime SemantiK existant (PGF ≠ compilateur)', padding=8)
        step.pack(fill='x', pady=(12, 7))
        actions = ttk.Frame(step)
        actions.pack(fill='x')
        self.gf_buttons = []
        runtime_btn = ttk.Button(actions, text='Vérifier PGF existant (Python pgf)', command=self.verify_existing_pgf)
        runtime_btn.pack(side='left', padx=(0, 8))
        self.gf_buttons.append(runtime_btn)
        ttk.Label(step, text='Artefact Konstellation français : permet de contrôler le backend python-pgf; ne compile pas la grammaire UNESCO.',
                  wraplength=970, foreground='#536073').pack(anchor='w', pady=(7, 0))

        compiler_frame = ttk.LabelFrame(top, text='2. Compilateur gf.exe (nécessaire à la grammaire UNESCO)', padding=8)
        compiler_frame.pack(fill='x', pady=(7, 7))
        actions = ttk.Frame(compiler_frame)
        actions.pack(fill='x')
        for label, function in [
            ('Rechercher GF', self.auto_find),
            ('Vérifier GF', self.verify_gf),
            ('Page officielle GF', lambda: webbrowser.open(DOWNLOAD_PAGE)),
            ('Importer ZIP GF officiel…', self.import_zip),
        ]:
            b = ttk.Button(actions, text=label, command=function)
            b.pack(side='left', padx=(0, 8))
            self.gf_buttons.append(b)
        ttk.Label(compiler_frame, text='Le chemin gf.exe reste vide : aucune preuve d’un compilateur présent dans les dépôts. Si absent, utiliser le ZIP officiel. '
                           'Le dossier privé utilisé est ' + str(private_tool_root()),
                  wraplength=950, foreground='#536073').pack(anchor='w', pady=(7, 0))

        run_frame = ttk.LabelFrame(top, text='3. Exécution contrôlée', padding=8)
        run_frame.pack(fill='x', pady=5)
        row = ttk.Frame(run_frame)
        row.pack(fill='x')
        ttk.Checkbutton(row, text='Français + anglais (décocher : français seul)', variable=self.both).pack(side='left')
        ttk.Button(row, text='Dernier RUN', command=self.detect_run).pack(side='right')
        buttons = ttk.Frame(run_frame)
        buttons.pack(fill='x', pady=(8, 0))
        self.launch = ttk.Button(buttons, text='Compiler GF + tester concept10', command=self.start)
        self.launch.pack(side='left')
        self.cancel = ttk.Button(buttons, text='Annuler', command=self.stop, state='disabled')
        self.cancel.pack(side='left', padx=7)
        ttk.Button(buttons, text='Ouvrir Téléchargements', command=self.open_output).pack(side='left')
        ttk.Label(top, textvariable=self.status, foreground='#263b74', wraplength=940).pack(anchor='w', pady=(7, 0))
        logs = ttk.Frame(self, padding=(15, 5, 15, 15))
        logs.pack(fill='both', expand=True)
        ttk.Label(logs, text='Journal en direct', font=('Segoe UI', 11, 'bold')).pack(anchor='w', pady=(5, 5))
        inner = ttk.Frame(logs)
        inner.pack(fill='both', expand=True)
        self.log = tk.Text(inner, wrap='word', bg='#111827', fg='#d8ecff',
                           insertbackground='white', font=('Consolas', 10), state='disabled')
        scroll = ttk.Scrollbar(inner, orient='vertical', command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        self.append('v3 : chemins PGF / adaptateur SemantiK vérifiés; gf.exe reste distinct du PGF.\n')

    def append(self, msg):
        self.log.configure(state='normal')
        self.log.insert('end', str(msg).rstrip() + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def choose(self, name):
        if self.busy:
            return
        if name in ('GF.exe', 'Python PGF', 'PGF FR existant'):
            x = filedialog.askopenfilename(title='Sélectionner '+name, filetypes=[('Fichiers Python, GF ou PGF', '*.exe *.pgf'), ('Tous', '*.*')])
        else:
            x = filedialog.askdirectory(title='Choisir ' + name)
        if x:
            self.vars[name].set(x)

    def _submit(self, job):
        if self.busy:
            return
        self.busy = True
        self.cancel_flag.clear()
        self.launch.configure(state='disabled')
        self.cancel.configure(state='normal')
        for button in self.gf_buttons:
            button.configure(state='disabled')
        threading.Thread(target=self._worker, args=(job,), daemon=True).start()

    def _worker(self, job):
        try:
            job()
        except Exception as exc:
            self.q.put(('error', type(exc).__name__ + ' : ' + str(exc)))
        finally:
            self.q.put(('idle', None))

    def verify_existing_pgf(self):
        python = self.vars['Python PGF'].get().strip()
        pgf = self.vars['PGF FR existant'].get().strip()
        self.status.set('Contrôle du PGF précompilé via le Python sélectionné (10 secondes maximum)…')
        self._submit(lambda: self.q.put(('pgf_verified', probe_existing_pgf(python, pgf))))

    def auto_find(self):
        self.status.set('Recherche GF dans les emplacements connus…')
        self._submit(lambda: self.q.put(('found', discover_gf(self.vars['GF.exe'].get().strip() or '', self.vars['SemantiK'].get().strip()))))

    def verify_gf(self):
        path = self.vars['GF.exe'].get().strip()
        self.status.set('Vérification du compilateur GF, délai maximal 8 secondes…')
        def job():
            gf, attempts = discover_gf(path, self.vars['SemantiK'].get().strip())
            self.q.put(('attempts', attempts))
            if gf is None:
                raise ValueError('gf.exe introuvable. Télécharger GF Windows via la page officielle.')
            result = probe_gf(gf)
            self.q.put(('verify', result))
        self._submit(job)

    def import_zip(self):
        archive = filedialog.askopenfilename(title='ZIP GF Windows téléchargé du site officiel',
                                             filetypes=[('Archives ZIP', '*.zip')])
        if not archive:
            return
        if not messagebox.askyesno('Importer GF', 'Importer ce ZIP dans ton dossier AppData privé ?\n\n'
                                'Aucun programme ne sera lancé pendant l’import.\n'
                                'N’utilise qu’une archive issue du site GF officiel.'):
            return
        self.status.set('Vérification et extraction locale de GF…')
        self._submit(lambda: self.q.put(('installed', str(import_official_zip(archive)))))

    def detect_run(self):
        try:
            r = find_latest_run(Path(self.vars['Kristal'].get().strip()))
            self.vars['RUN (automatique)'].set(str(r))
            self.append('RUN trouvé : ' + str(r))
        except Exception as exc:
            messagebox.showwarning('RUN', str(exc))

    def start(self):
        v = {k: x.get().strip().strip('"') for k, x in self.vars.items()}
        langs = ('fr', 'en') if self.both.get() else ('fr',)
        self.status.set('Pilote en cours; pas de publication. Compilation GF bornée à 45 secondes/langue.')
        def job():
            k = Path(v['Kristal'])
            sa = Path(v['SemantiK'])
            sa = resolve_semantik_project(sa)
            run = Path(v['RUN (automatique)']) if v['RUN (automatique)'] else find_latest_run(k)
            archive = run_pilot(run, k / 'Kristal_UNESCO_Factory', sa, Path(v['Sortie']),
                                cid=v['Concept'], langs=langs, gf_executable=v['GF.exe'],
                                existing_pgf=v['PGF FR existant'], pgf_python=v['Python PGF'],
                                callback=lambda x: self.q.put(('log', x)),
                                is_cancelled=self.cancel_flag.is_set)
            result = json.loads(archive.with_suffix('').joinpath('report.json').read_text(encoding='utf-8'))
            self.q.put(('done', (str(archive), result['status'])))
        self._submit(job)

    def stop(self):
        if self.busy:
            self.cancel_flag.set()
            self.append('Annulation demandée. Une compilation GF en cours dispose d’un délai de 45 secondes.')

    def open_output(self):
        path = Path(self.vars['Sortie'].get().strip())
        if not path.is_dir():
            messagebox.showwarning('Dossier', 'Dossier introuvable : ' + str(path))
            return
        if os.name == 'nt':
            os.startfile(str(path))
        else:
            subprocess.Popen(['xdg-open', str(path)])

    def poll(self):
        try:
            while True:
                kind, value = self.q.get_nowait()
                if kind == 'pgf_verified':
                    self.append('Runtime SemantiK : ' + json.dumps(value, ensure_ascii=False))
                    if value['loaded']:
                        self.status.set('PGF Konstellation chargé avec python-pgf. Cela ne compile PAS la grammaire UNESCO.')
                    else:
                        self.status.set('PGF Konstellation non chargé : ' + value.get('error', 'inconnu'))
                elif kind == 'log':
                    self.append(value)
                elif kind == 'found':
                    gf, attempts = value
                    self.append('Recherche GF :\n  ' + '\n  '.join(attempts))
                    if gf:
                        self.vars['GF.exe'].set(gf)
                        self.append('GF trouvé : ' + gf)
                        self.status.set('GF détecté. Clique sur « Vérifier GF » puis lance le pilote.')
                    else:
                        self.status.set('Compilateur gf.exe non trouvé ; le PGF existant reste distinct.')
                        self.append('GF absent dans les emplacements recherchés.')
                elif kind == 'attempts':
                    self.append('Recherche GF : ' + ' | '.join(value))
                elif kind == 'verify':
                    self.vars['GF.exe'].set(value['executable'])
                    self.append('GF : ' + json.dumps(value, ensure_ascii=False))
                    if value['usable']:
                        self.status.set('gf.exe répond. Le pilote peut tenter une compilation réelle.')
                    else:
                        self.status.set('GF trouvé mais test de version non concluant. Voir journal.')
                elif kind == 'installed':
                    self.vars['GF.exe'].set(value)
                    self.append('Archive GF importée dans : ' + value)
                    self.status.set('GF importé. Clique sur « Vérifier GF » puis lance le pilote.')
                elif kind == 'done':
                    self.last_zip, status = value
                    self.append('ZIP produit : ' + self.last_zip)
                    self.status.set('Statut final : ' + status)
                    messagebox.showinfo('Diagnostic GF / Spek', 'Statut : ' + status + '\n\nZIP : ' + self.last_zip)
                elif kind == 'error':
                    self.append('ERREUR : ' + value)
                    self.status.set('Erreur : ' + value)
                    messagebox.showerror('Pilote', value)
                elif kind == 'idle':
                    self.busy = False
                    self.launch.configure(state='normal')
                    self.cancel.configure(state='disabled')
                    for b in self.gf_buttons:
                        b.configure(state='normal')
        except queue.Empty:
            pass
        self.after(100, self.poll)


if __name__ == '__main__':
    try:
        Application().mainloop()
    except Exception as exc:
        try:
            messagebox.showerror('Échec interface', repr(exc))
        except Exception:
            pass
