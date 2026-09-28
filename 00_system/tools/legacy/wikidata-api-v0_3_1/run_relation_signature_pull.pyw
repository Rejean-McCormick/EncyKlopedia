from __future__ import annotations

import csv
import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "Wikidata Relation Explorer — kOA"
BASE_DIR = Path(__file__).resolve().parent
PULL_SCRIPT = BASE_DIR / "scripts" / "pull_wikidata_relation_signatures.py"
EXPAND_SCRIPT = BASE_DIR / "scripts" / "expand_wikidata_relations.py"
DEFAULT_REGISTRY = BASE_DIR / "config" / "intellectuals.seed.snapshot.json"
DEFAULT_OUT = BASE_DIR / "output"
DEFAULT_QID_MAP = DEFAULT_OUT / "qid-map.json"
DEFAULT_SIGNATURES = DEFAULT_OUT / "people.relation-signatures.jsonl"
DEFAULT_CATALOG = DEFAULT_OUT / "relations.catalog.csv"


class PullApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1120x780")
        self.minsize(900, 650)

        self.proc: subprocess.Popen[str] | None = None
        self.proc_mode = ""
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.selected_pids: set[str] = set()
        self.relation_rows: list[dict[str, str]] = []
        self.sort_pop_desc = True

        self.registry_var = tk.StringVar(value=str(DEFAULT_REGISTRY))
        self.qid_map_var = tk.StringVar(value=str(DEFAULT_QID_MAP) if DEFAULT_QID_MAP.exists() else "")
        self.out_var = tk.StringVar(value=str(DEFAULT_OUT))
        self.sleep_var = tk.StringVar(value="0.75")
        self.limit_var = tk.StringVar(value="0")
        self.sample_var = tk.StringVar(value="6")
        self.semantic_only_var = tk.BooleanVar(value=False)
        self.contact_var = tk.StringVar(value=os.environ.get("KOA_WIKIMEDIA_CONTACT", ""))
        self.status_var = tk.StringVar(value="Prêt")
        self.depth_var = tk.IntVar(value=3)
        self.relation_filter_var = tk.StringVar(value="")
        self.semantic_filter_var = tk.BooleanVar(value=False)
        self.selection_var = tk.StringVar(value="0 relation sélectionnée")

        self._build_ui()
        self.after(100, self._drain_log_queue)
        if DEFAULT_CATALOG.exists():
            self.after(250, self._load_relations)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=10)
        root.pack(fill="both", expand=True)
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        self.nb = ttk.Notebook(root)
        self.nb.grid(row=0, column=0, sticky="nsew")
        self.pull_tab = ttk.Frame(self.nb, padding=10)
        self.rel_tab = ttk.Frame(self.nb, padding=10)
        self.nb.add(self.pull_tab, text="1 · Pull niveau 1")
        self.nb.add(self.rel_tab, text="2 · Explorer / étendre")
        self._build_pull_tab()
        self._build_rel_tab()

        bottom = ttk.Frame(root)
        bottom.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(bottom, textvariable=self.status_var).pack(side="left")
        ttk.Button(bottom, text="Ouvrir output", command=self._open_output).pack(side="right")

    def _build_pull_tab(self) -> None:
        t = self.pull_tab
        t.columnconfigure(1, weight=1)
        t.rowconfigure(8, weight=1)

        ttk.Label(t, text="Registre source").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(t, textvariable=self.registry_var).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(t, text="Parcourir…", command=self._choose_registry).grid(row=0, column=2)

        ttk.Label(t, text="QID map (optionnel / reprise)").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(t, textvariable=self.qid_map_var).grid(row=1, column=1, sticky="ew", padx=8)
        ttk.Button(t, text="Parcourir…", command=self._choose_qid_map).grid(row=1, column=2)

        ttk.Label(t, text="Dossier de sortie").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(t, textvariable=self.out_var).grid(row=2, column=1, sticky="ew", padx=8)
        ttk.Button(t, text="Parcourir…", command=self._choose_out).grid(row=2, column=2)

        ttk.Label(t, text="Contact Wikimedia (email ou URL)").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(t, textvariable=self.contact_var).grid(row=3, column=1, sticky="ew", padx=8)
        ttk.Label(t, text="recommandé pour le User-Agent").grid(row=3, column=2, sticky="w")

        opts = ttk.Frame(t)
        opts.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(8, 4))
        ttk.Label(opts, text="Pause API (s)").pack(side="left")
        ttk.Entry(opts, textvariable=self.sleep_var, width=7).pack(side="left", padx=(6, 16))
        ttk.Label(opts, text="Limite (0=toutes)").pack(side="left")
        ttk.Entry(opts, textvariable=self.limit_var, width=7).pack(side="left", padx=(6, 16))
        ttk.Label(opts, text="Échantillon estimation").pack(side="left")
        ttk.Entry(opts, textvariable=self.sample_var, width=7).pack(side="left", padx=(6, 16))
        ttk.Checkbutton(opts, text="Matrice sémantique seulement", variable=self.semantic_only_var).pack(side="left")

        buttons = ttk.Frame(t)
        buttons.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(8, 6))
        self.estimate_pull_btn = ttk.Button(buttons, text="Estimer taille N1", command=self._estimate_pull)
        self.estimate_pull_btn.pack(side="left")
        self.start_btn = ttk.Button(buttons, text="Lancer le pull N1", command=self._start_pull)
        self.start_btn.pack(side="left", padx=8)
        self.stop_btn = ttk.Button(buttons, text="Arrêter", command=self._stop, state="disabled")
        self.stop_btn.pack(side="left")
        ttk.Button(buttons, text="Effacer log", command=self._clear_log).pack(side="left", padx=8)

        ttk.Label(
            t,
            text="N1 ne stocke aucune valeur de claim : seulement les propriétés présentes, leur type, rang et nombre de statements.",
        ).grid(row=6, column=0, columnspan=3, sticky="w", pady=(4, 6))

        ttk.Separator(t).grid(row=7, column=0, columnspan=3, sticky="ew", pady=4)
        self.log = tk.Text(t, wrap="word", state="disabled")
        self.log.grid(row=8, column=0, columnspan=3, sticky="nsew")
        scroll = ttk.Scrollbar(t, orient="vertical", command=self.log.yview)
        scroll.grid(row=8, column=3, sticky="ns")
        self.log.configure(yscrollcommand=scroll.set)

    def _build_rel_tab(self) -> None:
        t = self.rel_tab
        t.columnconfigure(0, weight=1)
        t.rowconfigure(2, weight=1)
        top = ttk.Frame(t)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(top, text="Charger relations.catalog.csv", command=self._load_relations).pack(side="left")
        ttk.Button(top, text="Trier par popularité", command=self._sort_popularity).pack(side="left", padx=6)
        ttk.Button(top, text="Sélectionner sémantiques", command=self._select_semantic).pack(side="left")
        ttk.Button(top, text="Tout décocher", command=self._clear_selection).pack(side="left", padx=6)
        ttk.Label(top, textvariable=self.selection_var).pack(side="right")

        filt = ttk.Frame(t)
        filt.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        ttk.Label(filt, text="Filtre").pack(side="left")
        e = ttk.Entry(filt, textvariable=self.relation_filter_var, width=30)
        e.pack(side="left", padx=6)
        e.bind("<KeyRelease>", lambda _e: self._render_relations())
        ttk.Checkbutton(filt, text="Afficher seulement semantic_relation", variable=self.semantic_filter_var, command=self._render_relations).pack(side="left")

        frame = ttk.Frame(t)
        frame.grid(row=2, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        cols = ("sel", "pid", "label_fr", "label_en", "class", "people", "coverage", "statements")
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
        headings = {
            "sel": "✓", "pid": "PID", "label_fr": "Relation (FR)", "label_en": "Relation (EN)",
            "class": "Classe", "people": "Personnes", "coverage": "Couverture %", "statements": "Statements",
        }
        widths = {"sel": 38, "pid": 70, "label_fr": 210, "label_en": 210, "class": 130, "people": 85, "coverage": 90, "statements": 90}
        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w" if c in {"label_fr", "label_en", "class"} else "center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        ys = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        ys.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=ys.set)
        self.tree.bind("<Button-1>", self._tree_click)
        self.tree.bind("<Double-1>", self._tree_double_click)

        exp = ttk.LabelFrame(t, text="Expansion des relations cochées", padding=8)
        exp.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(exp, text="Niveaux").pack(side="left")
        ttk.Spinbox(exp, from_=2, to=11, textvariable=self.depth_var, width=5).pack(side="left", padx=(6, 12))
        ttk.Label(exp, text="1=objet · 2=relation · 3=cible · 4=relations de la cible · 5=cibles suivantes …").pack(side="left")
        self.estimate_expand_btn = ttk.Button(exp, text="Estimer sélection", command=self._estimate_expansion)
        self.estimate_expand_btn.pack(side="right")
        self.expand_btn = ttk.Button(exp, text="Étendre sélection", command=self._start_expansion)
        self.expand_btn.pack(side="right", padx=8)

        ttk.Label(
            t,
            text="Phase 2 : contrairement au pull N1, les valeurs des relations explicitement cochées sont conservées afin de construire le graphe.",
        ).grid(row=4, column=0, sticky="w", pady=(6, 4))

        rel_log_frame = ttk.LabelFrame(t, text="Estimation / expansion", padding=4)
        rel_log_frame.grid(row=5, column=0, sticky="ew")
        rel_log_frame.columnconfigure(0, weight=1)
        self.rel_log = tk.Text(rel_log_frame, wrap="word", state="disabled", height=9)
        self.rel_log.grid(row=0, column=0, sticky="ew")
        rel_scroll = ttk.Scrollbar(rel_log_frame, orient="vertical", command=self.rel_log.yview)
        rel_scroll.grid(row=0, column=1, sticky="ns")
        self.rel_log.configure(yscrollcommand=rel_scroll.set)

    def _choose_registry(self) -> None:
        p = filedialog.askopenfilename(title="Choisir le registre JSON", initialdir=str(BASE_DIR / "config"), filetypes=[("JSON", "*.json"), ("Tous", "*.*")])
        if p:
            self.registry_var.set(p)

    def _choose_qid_map(self) -> None:
        p = filedialog.askopenfilename(title="Choisir qid-map.json", initialdir=str(Path(self.out_var.get() or DEFAULT_OUT)), filetypes=[("JSON", "*.json"), ("Tous", "*.*")])
        if p:
            self.qid_map_var.set(p)

    def _choose_out(self) -> None:
        p = filedialog.askdirectory(title="Choisir le dossier de sortie", initialdir=str(DEFAULT_OUT))
        if p:
            self.out_var.set(p)
            q = Path(p) / "qid-map.json"
            if q.exists():
                self.qid_map_var.set(str(q))

    def _validated_common(self) -> tuple[Path, Path, Path | None, float, int, int] | None:
        registry = Path(self.registry_var.get().strip())
        out = Path(self.out_var.get().strip())
        qid_text = self.qid_map_var.get().strip()
        qid = Path(qid_text) if qid_text else None
        if not PULL_SCRIPT.exists() or not EXPAND_SCRIPT.exists():
            messagebox.showerror("Scripts introuvables", f"Attendus :\n{PULL_SCRIPT}\n{EXPAND_SCRIPT}")
            return None
        if not registry.exists():
            messagebox.showerror("Registre introuvable", str(registry)); return None
        if qid is not None and not qid.exists():
            qid = None
        try:
            sleep = float(self.sleep_var.get()); limit = int(self.limit_var.get()); sample = int(self.sample_var.get())
            if sleep < 0 or limit < 0 or sample < 1: raise ValueError
        except ValueError:
            messagebox.showerror("Valeurs invalides", "sleep >= 0, limite >= 0, échantillon >= 1."); return None
        out.mkdir(parents=True, exist_ok=True)
        return registry, out, qid, sleep, limit, sample

    def _python_for_subprocess(self) -> str:
        exe = Path(sys.executable)
        if exe.name.lower() == "pythonw.exe":
            p = exe.with_name("python.exe")
            if p.exists(): return str(p)
        return str(exe)

    def _estimate_pull(self) -> None:
        v = self._validated_common()
        if not v: return
        registry, out, qid, sleep, _limit, sample = v
        cmd = [self._python_for_subprocess(), "-u", str(PULL_SCRIPT), "--registry", str(registry), "--out", str(out), "--sleep", str(sleep), "--estimate-only", "--sample-size", str(sample)]
        contact = self.contact_var.get().strip()
        if contact: cmd.extend(["--contact", contact])
        if qid: cmd.extend(["--qid-map", str(qid)])
        self._launch(cmd, "estimate_pull", "Estimation N1 en cours…")

    def _start_pull(self) -> None:
        v = self._validated_common()
        if not v: return
        registry, out, qid, sleep, limit, _sample = v
        cmd = [self._python_for_subprocess(), "-u", str(PULL_SCRIPT), "--registry", str(registry), "--out", str(out), "--sleep", str(sleep), "--limit", str(limit)]
        contact = self.contact_var.get().strip()
        if contact: cmd.extend(["--contact", contact])
        if qid: cmd.extend(["--qid-map", str(qid)])
        if self.semantic_only_var.get(): cmd.append("--semantic-matrix-only")
        self._launch(cmd, "pull", "Pull N1 en cours…")

    def _catalog_path(self) -> Path:
        return Path(self.out_var.get().strip()) / "relations.catalog.csv"

    def _load_relations(self) -> None:
        p = self._catalog_path()
        if not p.exists():
            messagebox.showinfo("Catalogue absent", f"Lance d’abord le pull N1.\n\nFichier attendu :\n{p}")
            return
        with p.open(encoding="utf-8-sig", newline="") as f:
            self.relation_rows = list(csv.DictReader(f))
        self.relation_rows.sort(key=lambda r: (-int(r.get("people_with_relation") or 0), r.get("property_id") or ""))
        self.sort_pop_desc = True
        self._render_relations()
        self.status_var.set(f"{len(self.relation_rows)} marqueurs de relation chargés")

    def _render_relations(self) -> None:
        if not hasattr(self, "tree"): return
        for iid in self.tree.get_children(): self.tree.delete(iid)
        needle = self.relation_filter_var.get().strip().casefold()
        semantic_only = self.semantic_filter_var.get()
        for r in self.relation_rows:
            if semantic_only and r.get("relation_class") != "semantic_relation": continue
            hay = " ".join([r.get("property_id", ""), r.get("label_fr", ""), r.get("label_en", ""), r.get("relation_class", "")]).casefold()
            if needle and needle not in hay: continue
            pid = r.get("property_id", "")
            self.tree.insert("", "end", iid=pid, values=("☑" if pid in self.selected_pids else "☐", pid, r.get("label_fr", ""), r.get("label_en", ""), r.get("relation_class", ""), r.get("people_with_relation", ""), r.get("coverage_pct", ""), r.get("total_statements", "")))
        self._update_selection_label()

    def _tree_click(self, event: tk.Event) -> None:
        if self.tree.identify_region(event.x, event.y) != "cell": return
        row = self.tree.identify_row(event.y); col = self.tree.identify_column(event.x)
        if row and col == "#1": self._toggle_pid(row)

    def _tree_double_click(self, event: tk.Event) -> None:
        row = self.tree.identify_row(event.y)
        if row: self._toggle_pid(row)

    def _toggle_pid(self, pid: str) -> None:
        if pid in self.selected_pids: self.selected_pids.remove(pid)
        else: self.selected_pids.add(pid)
        if self.tree.exists(pid):
            vals = list(self.tree.item(pid, "values")); vals[0] = "☑" if pid in self.selected_pids else "☐"; self.tree.item(pid, values=vals)
        self._update_selection_label()

    def _update_selection_label(self) -> None:
        n = len(self.selected_pids)
        self.selection_var.set(f"{n} relation{'s' if n != 1 else ''} sélectionnée{'s' if n != 1 else ''}")

    def _sort_popularity(self) -> None:
        self.sort_pop_desc = True
        self.relation_rows.sort(key=lambda r: (-int(r.get("people_with_relation") or 0), r.get("property_id") or ""))
        self._render_relations()

    def _select_semantic(self) -> None:
        self.selected_pids.update(r["property_id"] for r in self.relation_rows if r.get("relation_class") == "semantic_relation" and r.get("property_id"))
        self._render_relations()

    def _clear_selection(self) -> None:
        self.selected_pids.clear(); self._render_relations()

    def _write_selected(self, out: Path) -> Path:
        p = out / "selected-relations.json"
        p.write_text(json.dumps({"selected_properties": sorted(self.selected_pids), "levels": int(self.depth_var.get())}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return p

    def _expansion_cmd(self, estimate: bool) -> list[str] | None:
        v = self._validated_common()
        if not v: return None
        _registry, out, qid, sleep, limit, sample = v
        qid = qid or (out / "qid-map.json")
        if not qid.exists():
            messagebox.showerror("QID map absent", "Le pull N1 doit produire qid-map.json avant l’expansion."); return None
        if not self.selected_pids:
            messagebox.showinfo("Aucune relation", "Coche au moins un marqueur de relation à suivre."); return None
        levels = int(self.depth_var.get())
        if levels < 2:
            messagebox.showerror("Niveaux", "Le minimum est 2 : objet + marqueur de relation."); return None
        selected_file = self._write_selected(out)
        exp_out = out / "expansion"
        cmd = [self._python_for_subprocess(), "-u", str(EXPAND_SCRIPT), "--qid-map", str(qid), "--signatures", str(out / "people.relation-signatures.jsonl"), "--properties-file", str(selected_file), "--levels", str(levels), "--out", str(exp_out), "--sleep", str(sleep), "--sample-roots", str(sample)]
        contact = self.contact_var.get().strip()
        if contact: cmd.extend(["--contact", contact])
        if limit: cmd.extend(["--limit", str(limit)])
        if estimate: cmd.append("--estimate-only")
        return cmd

    def _estimate_expansion(self) -> None:
        cmd = self._expansion_cmd(True)
        if cmd: self._launch(cmd, "estimate_expand", "Estimation de l’expansion…")

    def _start_expansion(self) -> None:
        cmd = self._expansion_cmd(False)
        if cmd: self._launch(cmd, "expand", "Expansion en cours…")

    def _launch(self, cmd: list[str], mode: str, status: str) -> None:
        if self.proc and self.proc.poll() is None:
            messagebox.showinfo("Processus actif", "Un processus Wikidata est déjà en cours."); return
        self.proc_mode = mode
        self._append_log("\n$ " + subprocess.list2cmdline(cmd) + "\n\n", mode=mode)
        self.status_var.set(status)
        self._set_running(True)
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" and hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            self.proc = subprocess.Popen(cmd, cwd=str(BASE_DIR), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1, creationflags=creationflags)
        except Exception as exc:
            self.status_var.set("Échec de lancement"); self._set_running(False); messagebox.showerror("Erreur", str(exc)); return
        threading.Thread(target=self._read_process_output, daemon=True).start()

    def _set_running(self, running: bool) -> None:
        state = "disabled" if running else "normal"
        for b in (self.start_btn, self.estimate_pull_btn, self.expand_btn, self.estimate_expand_btn):
            b.configure(state=state)
        self.stop_btn.configure(state="normal" if running else "disabled")

    def _read_process_output(self) -> None:
        assert self.proc is not None
        if self.proc.stdout is not None:
            for line in self.proc.stdout: self.log_queue.put(line)
        code = self.proc.wait()
        self.log_queue.put(f"\n[process exited with code {code}]\n")
        self.log_queue.put(("__DONE_OK__" if code == 0 else "__DONE_ERROR__") + ":" + self.proc_mode)

    def _drain_log_queue(self) -> None:
        try:
            while True:
                item = self.log_queue.get_nowait()
                if item.startswith("__DONE_OK__:"):
                    mode = item.split(":", 1)[1]
                    self.status_var.set("Terminé")
                    self._set_running(False)
                    if mode == "pull":
                        q = Path(self.out_var.get().strip()) / "qid-map.json"
                        if q.exists(): self.qid_map_var.set(str(q))
                        self._load_relations(); self.nb.select(self.rel_tab)
                    elif mode == "expand":
                        self.status_var.set("Expansion terminée — fichiers dans output/expansion")
                elif item.startswith("__DONE_ERROR__:"):
                    self.status_var.set("Terminé avec erreur"); self._set_running(False)
                else:
                    self._append_log(item, mode=self.proc_mode)
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _append_log(self, text: str, mode: str | None = None) -> None:
        widget = self.rel_log if mode in {"estimate_expand", "expand"} and hasattr(self, "rel_log") else self.log
        widget.configure(state="normal"); widget.insert("end", text); widget.see("end"); widget.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log.configure(state="normal"); self.log.delete("1.0", "end"); self.log.configure(state="disabled")

    def _stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            try: self.proc.terminate(); self.status_var.set("Arrêt demandé…")
            except Exception as exc: messagebox.showerror("Erreur", str(exc))

    def _open_output(self) -> None:
        out = Path(self.out_var.get().strip()); out.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt": os.startfile(str(out))  # type: ignore[attr-defined]
            elif sys.platform == "darwin": subprocess.Popen(["open", str(out)])
            else: subprocess.Popen(["xdg-open", str(out)])
        except Exception as exc: messagebox.showerror("Impossible d’ouvrir", str(exc))

    def _on_close(self) -> None:
        if self.proc and self.proc.poll() is None:
            if not messagebox.askyesno("Quitter", "Un pull est en cours. L’arrêter et quitter ?"): return
            try: self.proc.terminate()
            except Exception: pass
        self.destroy()


if __name__ == "__main__":
    app = PullApp()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    app.mainloop()
