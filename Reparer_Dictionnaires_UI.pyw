# -*- coding: utf-8 -*-
"""EncyKlopedia v0.3: reparation ciblee de sources UniMorph no_data.

Double-click on Windows with Python 3.10+ (Tkinter). No external dependencies.
Code stays on C:, only derived candidate index on D: is modified.
"""
from __future__ import annotations

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

TITLE = 'EncyKlopedia | Réparer les sources UniMorph'
DEFAULT_ROOT = r'D:\EncyKlopedia'
SUBDIR = Path('30_working/lexical/harvester/index-v1')
INDEXER = Path(__file__).resolve().parent / 'tools' / 'dictionary-harvester' / 'lexical_indexer.py'


class RepairUI:
    def __init__(self, window):
        self.win = window
        self.win.title(TITLE)
        self.win.geometry('1030x695')
        self.win.minsize(775, 540)
        self.rootvar = tk.StringVar(value=os.environ.get('ENCYK_DATA_ROOT', DEFAULT_ROOT))
        self.status = tk.StringVar(value='Prêt — diagnostic en lecture seule.')
        self.events = queue.Queue()
        self.process = None
        self.worker = None
        self.stopping = False
        self._build()
        self.win.after(70, self.inspect)
        self.win.after(100, self._drain)
        self.win.protocol('WM_DELETE_WINDOW', self._close)

    def _build(self):
        outer = ttk.Frame(self.win, padding=14)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='Réparation ciblée — archives UniMorph', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        ttk.Label(outer, text='194 sources terminées préservées • aucune archive source modifiée • index candidat seulement').pack(anchor='w', pady=(0, 10))
        r = ttk.Frame(outer)
        r.pack(fill='x', pady=3)
        ttk.Label(r, text='Données sur D:').pack(side='left')
        self.root_entry = ttk.Entry(r, textvariable=self.rootvar)
        self.root_entry.pack(side='left', fill='x', expand=True, padx=7)
        ttk.Button(r, text='Parcourir', command=self.browse).pack(side='left')
        self.inspect_btn = ttk.Button(r, text='Actualiser', command=self.inspect)
        self.inspect_btn.pack(side='left', padx=(6, 0))
        bar = ttk.Frame(outer)
        bar.pack(fill='x', pady=(9, 10))
        self.repair_btn = ttk.Button(bar, text='Réparer uniquement les sources no_data', command=self.repair)
        self.repair_btn.pack(side='left')
        self.stop_btn = ttk.Button(bar, text='Interrompre (checkpoint conservé)', command=self.stop, state='disabled')
        self.stop_btn.pack(side='left', padx=9)
        ttk.Button(bar, text='Ouvrir le rapport', command=self.open_report).pack(side='left')
        self.progress = ttk.Progressbar(bar, mode='indeterminate', length=175)
        self.progress.pack(side='right')
        ttk.Label(outer, textvariable=self.status, foreground='#356b79').pack(anchor='w', pady=(0, 8))
        cols = ('langue', 'etat', 'archive', 'lignes', 'entrees')
        self.table = ttk.Treeview(outer, columns=cols, show='headings', height=13)
        labels = ('Langue', 'Statut index', 'Taille ZIP (Mo)', 'Lignes parcourues', 'Lignes acceptées')
        widths = (95, 140, 150, 150, 165)
        for col, label, width in zip(cols, labels, widths):
            self.table.heading(col, text=label)
            self.table.column(col, width=width, anchor='center')
        self.table.pack(fill='both', expand=True)
        scrollbar = ttk.Scrollbar(self.table, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        ttk.Label(outer, text='Journal (lecture en flux, réparable après interruption) :').pack(anchor='w', pady=(10, 2))
        logcontainer = ttk.Frame(outer)
        logcontainer.pack(fill='both', expand=True)
        self.log = tk.Text(logcontainer, height=9, wrap='word', font=('Consolas', 10), state='disabled')
        self.log.pack(side='left', fill='both', expand=True)
        sb = ttk.Scrollbar(logcontainer, command=self.log.yview)
        sb.pack(side='right', fill='y')
        self.log.configure(yscrollcommand=sb.set)
        ttk.Label(outer, text='Les droits des sources, la réconciliation diK et la publication restent non approuvés.').pack(anchor='w', pady=(8, 0))

    def _append(self, message):
        self.log.configure(state='normal')
        self.log.insert('end', message.rstrip() + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def browse(self):
        folder = filedialog.askdirectory(initialdir=self.rootvar.get() if Path(self.rootvar.get()).is_dir() else None)
        if folder:
            self.rootvar.set(folder)
            self.inspect()

    def _paths(self):
        root = Path(self.rootvar.get()).resolve()
        return root, root / SUBDIR / 'lexical.sqlite3'

    def inspect(self):
        if self.worker is not None and self.worker.is_alive():
            return
        self.table.delete(*self.table.get_children())
        root, db = self._paths()
        if not INDEXER.is_file():
            self.status.set('Module lexical_indexer.py absent : extraire tout l’overlay sur C:.')
            self.repair_btn.configure(state='disabled')
            return
        if not db.is_file():
            self.status.set('Index SQLite absent : ' + str(db))
            self.repair_btn.configure(state='disabled')
            return
        try:
            con = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True, timeout=3)
            try:
                rows = con.execute('''SELECT edition,status,size_bytes,cursor_lines,accepted
                    FROM source_files WHERE kind='unimorph' AND status != 'complete' ORDER BY edition''').fetchall()
                complete = con.execute("SELECT COUNT(*) FROM source_files WHERE status='complete'").fetchone()[0]
            finally:
                con.close()
            for edition, state, bytes_, cursor, accepted in rows:
                self.table.insert('', 'end', values=(edition, state, f'{bytes_ / 1000000:.2f}', f'{cursor:,}', f'{accepted:,}'))
            self.status.set(f'{len(rows)} sources UniMorph à contrôler; {complete} sources déjà complètes conservées.')
            self.repair_btn.configure(state='normal' if rows else 'disabled')
        except (OSError, sqlite3.Error) as exc:
            self.status.set(f'Impossible de lire l’index : {exc}')
            self.repair_btn.configure(state='disabled')

    def repair(self):
        if self.worker and self.worker.is_alive(): return
        root, db = self._paths()
        if not db.is_file():
            messagebox.showerror(TITLE, 'Index SQLite introuvable; réparation annulée.')
            return
        if not messagebox.askyesno(TITLE, 'Réparer seulement les sources UniMorph non terminées ?\n\nLes archives resteront intactes. L’index SQLite candidat sera mis à jour sur D:.'):
            return
        self.stopping = False
        self.repair_btn.configure(state='disabled')
        self.inspect_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.progress.start(15)
        self.status.set('Réparation en cours : voir le journal.')
        self._append('=== Réparation ciblée lancée ===')
        self.worker = threading.Thread(target=self._work, args=(str(root),), daemon=True)
        self.worker.start()

    def _work(self, root):
        exe = Path(sys.executable)
        if os.name == 'nt' and exe.name.lower() == 'pythonw.exe':
            candidate = exe.with_name('python.exe')
            if candidate.is_file(): exe = candidate
        cmd = [str(exe), '-u', str(INDEXER), 'repair', '--data-root', root]
        try:
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            text=True, encoding='utf-8', errors='replace',
                                            bufsize=1, creationflags=flags)
            for line in self.process.stdout:
                self.events.put(('log', line.rstrip()))
            result = self.process.wait()
            self.events.put(('done', result))
        except Exception as exc:
            self.events.put(('error', str(exc)))
        finally:
            self.process = None

    def _drain(self):
        while True:
            try: kind, data = self.events.get_nowait()
            except queue.Empty: break
            if kind == 'log': self._append(data)
            elif kind in ('done', 'error'):
                self.progress.stop()
                self.inspect_btn.configure(state='normal')
                self.stop_btn.configure(state='disabled')
                if kind == 'error':
                    self.status.set('Erreur de lancement : ' + data)
                else:
                    self.status.set('Réparation terminée : ' + ('OK' if data == 0 else f'code {data}. Vérifier le journal.'))
                self._append('=== ' + ('Erreur : ' + data if kind == 'error' else f'Processus terminé (code {data})') + ' ===')
                self.win.after(200, self.inspect)
        self.win.after(125, self._drain)

    def stop(self):
        if self.process and self.process.poll() is None:
            self._append('Arrêt demandé; checkpoints SQLite antérieurs conservés.')
            self.process.terminate()
            self.stop_btn.configure(state='disabled')
            self.stopping = True

    def open_report(self):
        root, _db = self._paths()
        file = root / SUBDIR / 'RAPPORT_LEXICAL.md'
        if not file.is_file():
            messagebox.showinfo(TITLE, 'Rapport non encore disponible.')
        elif os.name == 'nt':
            os.startfile(str(file))
        else:
            messagebox.showinfo(TITLE, str(file))

    def _close(self):
        if self.worker and self.worker.is_alive():
            messagebox.showwarning(TITLE, 'Une réparation est active. Utiliser « Interrompre (checkpoint conservé) » avant de fermer.')
            return
        self.win.destroy()


def main():
    root = tk.Tk()
    ttk.Style(root).theme_use('clam')
    RepairUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
