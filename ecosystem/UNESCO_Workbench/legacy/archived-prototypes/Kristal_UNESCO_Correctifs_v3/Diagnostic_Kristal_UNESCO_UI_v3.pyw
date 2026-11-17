# -*- coding: utf-8 -*-
"""Diagnostic Kristal / UNESCO / Spek / SemantiK.

Interface Tkinter. Lecture seule des dossiers de projet ; aucune commande de projet
n'est executee. Les seuls fichiers crees sont dans le dossier temporaire et
le ZIP de diagnostic dans Telechargements.

Windows : double-cliquer sur ce fichier .pyw (Python avec Tkinter requis).
Pour afficher une eventuelle erreur de demarrage : py -3 ce_fichier.pyw
"""

from __future__ import annotations

import json
import os
import queue
import shutil
import sys
import tempfile
import threading
import time
import traceback
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

APP_VERSION = "3.0"
WIN_TITLE = "Kristal / UNESCO — Diagnostic (lecture seule)"
RUN_RELATIVE = (
    Path("Kristalizer/SORTIE/UNESCO/FABRIQUE"),
    Path("Kristal_UNESCO_Factory/SORTIE/UNESCO/FABRIQUE"),
    Path("SORTIE/UNESCO/FABRIQUE"),
)
RUN_REPORTS = (
    "RAPPORT_FINAL.json",
    "RAPPORT_INCIDENT.json",
    "fabrique.log",
    "01_INVENTAIRE/manifest.json",
    "02_WIKIDATA/JOINTURE/manifest_p3916.json",
    "02_WIKIDATA/FAITS_COMPLETS/reader_runtime.json",
    "02_WIKIDATA/FAITS_COMPLETS/manifest_full.json",
    "02_WIKIDATA/FAITS_COMPLETS/snapshot_indexe.jsonl.gz.reader.json",
    "07_DISCOURS/manifest_discourse.json",
)
SKIP_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", ".tox",
    ".mypy_cache", ".pytest_cache", "__pycache__", "node_modules",
    "dist", "build", "target", "coverage", ".next", ".cache",
    "SORTIE", "OUTPUT", "outputs", "data", "datasets", "tmp", "temp",
}
MAX_GF_ITEMS = 8000
MAX_GF_DEPTH = 7
MAX_GF_SECONDS = 12.0
MAX_GF_RESULTS = 500
MAX_COPY_FILE = 4 * 1024 * 1024
MAX_COPY_TOTAL = 20 * 1024 * 1024
COPY_CHUNK = 512 * 1024


class Cancelled(Exception):
    pass


def downloads_path() -> Path:
    """Prefer the Windows Downloads known folder, including redirected locations."""
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            ) as key:
                value, _ = winreg.QueryValueEx(
                    key, "{374DE290-123F-4565-9164-39C4925E467B}"
                )
                target = Path(os.path.expandvars(value)).expanduser()
                if target.is_dir():
                    return target
        except (OSError, ValueError, TypeError):
            pass

    for candidate in (Path.home() / "Downloads", Path.home() / "Téléchargements"):
        if candidate.is_dir():
            return candidate
    return Path.home() / "Downloads"


def info_about_path(label: str, path: Path) -> dict:
    """Stat only; never read the contents of a binary source or dump."""
    result = {"nom": label, "chemin": str(path), "existe": False,
              "type": None, "taille_octets": None, "modifie": None}
    try:
        item = path.stat()
        result["existe"] = True
        result["type"] = "dossier" if path.is_dir() else "fichier"
        if path.is_file():
            result["taille_octets"] = item.st_size
        result["modifie"] = datetime.fromtimestamp(item.st_mtime).isoformat(timespec="seconds")
    except OSError as exc:
        result["erreur"] = str(exc)
    return result


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def find_run(root: Path, explicit: str, check, note) -> Path | None:
    if explicit:
        target = Path(os.path.expandvars(os.path.expanduser(explicit.strip(' "'))))
        if target.is_dir():
            return target
        note(f"RUN demandé absent : {target}")
        return None

    candidates = []
    for suffix in RUN_RELATIVE:
        check()
        folder = root / suffix
        if not folder.is_dir():
            continue
        try:
            with os.scandir(folder) as it:
                for entry in it:
                    check()
                    try:
                        if entry.name.startswith("RUN-") and entry.is_dir(follow_symlinks=False):
                            candidates.append((entry.stat(follow_symlinks=False).st_mtime, Path(entry.path)))
                    except OSError:
                        continue
        except OSError as exc:
            note(f"Impossible de lister {folder}: {exc}")
    return max(candidates, default=(0, None))[1]


def collect_gf_files(roots: list[Path], check, note) -> tuple[list[dict], dict]:
    """Bounded nonrecursive-by-default DFS; skip symlinks and output/build trees."""
    found = []
    checked = 0
    cut_reason = None
    started = time.monotonic()
    stack = [(p, 0) for p in roots if p.is_dir()]
    while stack:
        check()
        if time.monotonic() - started >= MAX_GF_SECONDS:
            cut_reason = "limite de temps"
            break
        if checked >= MAX_GF_ITEMS:
            cut_reason = "limite d'entrées"
            break
        folder, depth = stack.pop()
        try:
            with os.scandir(folder) as it:
                for ent in it:
                    check()
                    checked += 1
                    if checked >= MAX_GF_ITEMS:
                        cut_reason = "limite d'entrées"
                        break
                    if time.monotonic() - started >= MAX_GF_SECONDS:
                        cut_reason = "limite de temps"
                        break
                    try:
                        if ent.is_symlink():
                            continue
                        if ent.is_dir(follow_symlinks=False):
                            if depth < MAX_GF_DEPTH and ent.name not in SKIP_DIRS:
                                stack.append((Path(ent.path), depth + 1))
                        elif ent.is_file(follow_symlinks=False):
                            if ent.name.lower().endswith((".gf", ".pgf")):
                                st = ent.stat(follow_symlinks=False)
                                found.append({
                                    "chemin": ent.path,
                                    "octets": st.st_size,
                                    "type": Path(ent.name).suffix.lower(),
                                })
                                if len(found) >= MAX_GF_RESULTS:
                                    cut_reason = "limite de résultats"
                                    break
                    except OSError:
                        continue
        except OSError as exc:
            note(f"Dossier GF inaccessible: {folder} ({exc})")
        if cut_reason:
            break
    return found, {"entrees_parcourues": checked,
                   "tronque": bool(cut_reason), "cause": cut_reason,
                   "duree_s": round(time.monotonic() - started, 2)}


class ReportBuilder:
    def __init__(self, config, events: queue.Queue, cancel: threading.Event):
        self.config = config
        self.events = events
        self.cancel = cancel
        self.bytes_copied = 0
        self.files_copied = 0
        self.stage: Path | None = None
        self.journal = None

    def check(self):
        if self.cancel.is_set():
            raise Cancelled("Annulé par l'utilisateur")

    def note(self, message: str):
        line = f"[{datetime.now():%H:%M:%S}] {message}"
        self.events.put(("log", line))
        if self.journal:
            self.journal.write(line + "\n")
            self.journal.flush()

    def status(self, message: str):
        self.events.put(("status", message))
        self.note(message)

    def copy_limited(self, source: Path, relative: str):
        self.check()
        try:
            if source.is_symlink():
                self.note(f"LIEN SYMBOLIQUE IGNORÉ : {relative}")
                return
            st = source.stat()
            if not source.is_file():
                self.note(f"ABSENT : {relative}")
                return
            if st.st_size > MAX_COPY_FILE:
                self.note(f"IGNORÉ (plus de 4 Mio) : {relative}")
                return
            if self.bytes_copied + st.st_size > MAX_COPY_TOTAL:
                self.note(f"IGNORÉ (budget total 20 Mio) : {relative}")
                return
            dest = self.stage / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as src, dest.open("wb") as out:
                while True:
                    self.check()
                    chunk = src.read(COPY_CHUNK)
                    if not chunk:
                        break
                    out.write(chunk)
            self.bytes_copied += st.st_size
            self.files_copied += 1
            self.note(f"Copié : {relative}")
        except Cancelled:
            raise
        except (OSError, ValueError) as exc:
            self.note(f"Lecture impossible : {relative} ({exc})")

    def execute(self):
        started = datetime.now()
        zip_path = None
        try:
            self.stage = Path(tempfile.mkdtemp(prefix="kristal-unesco-diagnostic-"))
            with (self.stage / "00-journal.txt").open("w", encoding="utf-8", newline="\n") as log:
                self.journal = log
                zip_path = self._gather(started)
        except Cancelled:
            self.events.put(("finished", ("cancelled", None, "Diagnostic annulé.")))
            return
        except Exception as exc:
            details = traceback.format_exc()
            self.events.put(("log", f"ERREUR : {exc}\n{details}"))
            # The log handle may already have been closed by the with statement.
            if self.stage:
                try:
                    with (self.stage / "00-journal.txt").open("a", encoding="utf-8") as log:
                        log.write(f"\nERREUR : {exc}\n{details}\n")
                    dest_dir = downloads_path()
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    error_zip = dest_dir / (
                        f"Kristal-UNESCO-ERREUR-{datetime.now():%Y%m%d-%H%M%S}-"
                        f"{uuid.uuid4().hex[:5]}.zip"
                    )
                    with zipfile.ZipFile(error_zip, "w", zipfile.ZIP_DEFLATED) as archive:
                        for source in self.stage.rglob("*"):
                            if source.is_file() and not source.is_symlink():
                                archive.write(source, source.relative_to(self.stage).as_posix())
                    self.events.put(("log", f"Archive d'erreur : {error_zip}"))
                except Exception as zip_exc:
                    self.events.put(("log", f"Archive d'erreur non créée : {zip_exc}"))
            self.events.put(("finished", ("error", None, str(exc))))
            return
        finally:
            self.journal = None
            if self.stage:
                try:
                    shutil.rmtree(self.stage)
                except OSError:
                    pass
        self.events.put(("finished", ("ok", str(zip_path), "Diagnostic terminé.")))

    def _gather(self, started):
        cfg = self.config
        kr, se, en = (Path(os.path.expandvars(os.path.expanduser(cfg[name])))
                      for name in ("Kristal", "SemantiK", "EncyKlopedia"))
        # Accept the confirmed nested SemantiK project and the parent workspace.
        sa = se if (se / "src/semantik_architect").is_dir() else se / "SemantiK_Architect"
        workspace = sa.parent
        self.status("Début : lecture seule des sources (aucun exécutable du projet lancé).")
        self.note(f"Racines : Kristal={kr} | SemantiK={se} | EncyKlopedia={en}")

        self.status("Recherche du dernier RUN…")
        run = find_run(kr, cfg.get("RUN", ""), self.check, self.note)
        self.note(f"RUN : {run if run else 'NON TROUVÉ'}")

        paths = {
            "Fabrique": kr / "Kristal_UNESCO_Factory",
            "Authoring Kit": kr / "Kristal-Authoring-Kit",
            "Framework": kr / "Kristal-Framework",
            "Kristalizer": kr / "Kristalizer",
            "Spek embarqué": kr / "Kristal_UNESCO_Factory/vendor/spek",
            "UNESCO Turtle": kr / "Sources/UNESCO/unesco-thesaurus.ttl",
            "SemantiK Architect": sa,
            "Runtime Orchestrator": workspace / "SemantiK_Runtime_Orchestrator",
            "PGF français Konstellation": Path(cfg["PGF FR"]),
            "Adaptateur Python PGF": sa / "src/semantik_architect/adapters/realization/gf/pgf_runtime.py",
            "Python PGF préféré": Path(cfg["Python PGF"]),
            "GF Wordbench (facultatif)": workspace / "GF_Wordbench",
            "EncyK SQLite": en / "30_working/wikidata/wikidata.compact.sqlite",
            "Index Skope": en / "30_working/wikidata-fast",
            "Dump Wikidata": en / "10_sources/wikidata/dumps/current",
            "Lecteur Python CP313": kr / ".factory_runtime/wikidata/reader-cp313/Scripts/python.exe",
        }
        # Le CSV d'origine P3916 n'était pas à l'ancien chemin supposé.
        # Les sorties de jointure, elles, sont attestées dans le RUN réel.
        if run:
            paths["Jointure P3916 (RUN)"] = run / "02_WIKIDATA/JOINTURE/crosswalk_candidates.csv"
            paths["Manifeste P3916 (RUN)"] = run / "02_WIKIDATA/JOINTURE/manifest_p3916.json"
        self.status("Contrôle des chemins…")
        metadata = []
        for label, p in paths.items():
            self.check()
            data = info_about_path(label, p)
            metadata.append(data)
            self.note(f"{'OK' if data['existe'] else 'ABSENT'} : {label}")
        write_json(self.stage / "01-chemins.json", metadata)

        self.status("Repérage des outils installés (sans les exécuter)…")
        tools = [{"outil": tool, "chemin": shutil.which(tool)}
                 for tool in ("py", "python", "pythonw", "gf", "git")]
        write_json(self.stage / "02-outils.json", tools)
        for tool in tools:
            self.note(f"{tool['outil']} : {tool['chemin'] or 'ABSENT DU PATH'}")

        self.status("Index Skope et dump Wikidata…")
        idx_home = en / "30_working/wikidata-fast"
        idx = []
        if idx_home.is_dir():
            try:
                with os.scandir(idx_home) as it:
                    for pos, entry in enumerate(it):
                        self.check()
                        if pos >= 100:
                            self.note("Index : limite de 100 sous-dossiers atteinte.")
                            break
                        if not entry.is_dir(follow_symlinks=False):
                            continue
                        for name in ("qid-locator.bin", "compression.bz2blocks.pkl",
                                     "compression.gzindex"):
                            p = Path(entry.path) / name
                            obj = info_about_path(f"{entry.name}/{name}", p)
                            if obj["existe"]:
                                idx.append(obj)
            except OSError as exc:
                self.note(f"Index illisibles : {exc}")
        write_json(self.stage / "03-index-skope.json", idx)
        self.note(f"Index repérés : {len(idx)}")

        dump_dir = en / "10_sources/wikidata/dumps/current"
        dumps = []
        if dump_dir.is_dir():
            try:
                with os.scandir(dump_dir) as it:
                    for pos, entry in enumerate(it):
                        self.check()
                        if pos >= 40:
                            break
                        if entry.is_file(follow_symlinks=False):
                            dumps.append(info_about_path(entry.name, Path(entry.path)))
            except OSError as exc:
                self.note(f"Dumps illisibles : {exc}")
        write_json(self.stage / "04-dumps.json", dumps)
        self.note(f"Dumps repérés : {len(dumps)}")

        self.status("Inventaire borné des grammaires GF/PGF…")
        gf, gf_stats = collect_gf_files(
            [sa, workspace / "SemantiK_Runtime_Orchestrator"],
            self.check, self.note,
        )
        write_json(self.stage / "05-grammaires.json", {"fichiers": gf, "statistiques": gf_stats})
        self.note(f"Grammaires GF/PGF : {len(gf)} | Entrées examinées : {gf_stats['entrees_parcourues']}")
        if gf_stats["tronque"]:
            self.note(f"Inventaire limité : {gf_stats['cause']}")

        self.status("Récupération bornée des rapports et journaux…")
        if cfg.get("copy_logs", True):
            self.copy_limited(kr / "Kristal_UNESCO_Factory/BOOTSTRAP_RUNTIME.log",
                              "logs/BOOTSTRAP_RUNTIME.log")

        validations = []
        if run:
            for rel in RUN_REPORTS:
                self.check()
                src = run / rel
                if src.suffix.lower() == ".json" and src.is_file():
                    try:
                        if src.stat().st_size <= MAX_COPY_FILE:
                            with src.open("r", encoding="utf-8-sig") as inp:
                                json.load(inp)
                            validations.append({"fichier": rel, "statut": "OK"})
                    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
                        validations.append({"fichier": rel, "statut": "ERREUR",
                                            "detail": str(exc)[:350]})
                        self.note(f"JSON invalide : {rel}")
                if cfg.get("copy_logs", True):
                    self.copy_limited(src, "run/" + rel)

            if cfg.get("copy_logs", True):
                logs_dir = run / "LOGS"
                if logs_dir.is_dir():
                    try:
                        with os.scandir(logs_dir) as it:
                            found_logs = sorted(
                                (Path(e.path) for e in it
                                 if e.is_file(follow_symlinks=False) and e.name.lower().endswith(".log")),
                                key=lambda p: p.name.lower(),
                            )[:20]
                        for p in found_logs:
                            self.copy_limited(p, "run/LOGS/" + p.name)
                    except OSError as exc:
                        self.note(f"Logs inaccessibles : {exc}")

            if cfg.get("copy_samples", True):
                for lang in ("fr", "en"):
                    for kind in ("instances", "dialogue"):
                        self.check()
                        folder = run / "07_DISCOURS" / kind / lang
                        if not folder.is_dir():
                            continue
                        try:
                            with os.scandir(folder) as it:
                                samples = sorted(
                                    (Path(e.path) for e in it if e.is_file(follow_symlinks=False)
                                     and e.name.lower().endswith(".json")),
                                    key=lambda p: p.name.lower(),
                                )
                            if samples:
                                self.copy_limited(samples[0],
                                                  f"run/EXEMPLES/{kind}/{lang}/{samples[0].name}")
                        except OSError as exc:
                            self.note(f"Exemples inaccessibles : {folder} ({exc})")
        write_json(self.stage / "06-validation-json.json", validations)
        self.note(f"Rapports JSON vérifiés : {len(validations)}")

        summary = {
            "version": APP_VERSION,
            "date": started.isoformat(timespec="seconds"),
            "mode": "lecture seule ; aucune commande du projet exécutée",
            "racines": {"Kristal": str(kr), "SemantiK": str(se), "EncyKlopedia": str(en)},
            "dernier_run": str(run) if run else None,
            "chemins_existants": sum(bool(x["existe"]) for x in metadata),
            "chemins_controles": len(metadata),
            "grammaires_trouvees": len(gf),
            "index_skope_trouves": len(idx),
            "dumps_trouves": len(dumps),
            "rapports_json_valides": sum(x["statut"] == "OK" for x in validations),
            "rapports_json_invalides": sum(x["statut"] == "ERREUR" for x in validations),
            "fichiers_sources_copies": self.files_copied,
            "octets_sources_copies": self.bytes_copied,
        }
        write_json(self.stage / "00-resume.json", summary)
        (self.stage / "LISEZ-MOI.txt").write_text(
            "DIAGNOSTIC KRISTAL / UNESCO\n\n"
            "Lecture seule du projet. Aucune compilation, commande Git, GF, Python du projet,\n"
            "generation ni publication n'a ete lancee.\n"
            "Inventaire de grammaires limite a 8000 entrees / 12 secondes / 500 resultats.\n"
            "Copies de rapports/logs limitees a 4 Mio par fichier et 20 Mio au total.\n"
            "Les chemins et les logs peuvent reveler des informations locales ou sensibles.\n"
            "VERIFIER L'ARCHIVE AVANT DE LA PARTAGER.\n",
            encoding="utf-8",
        )

        self.check()
        dest_dir = downloads_path()
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"Kristal-UNESCO-diagnostic-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:5]}.zip"
        tmp_zip = dest.with_suffix(".zip.part")
        self.status("Création de l'archive ZIP dans Téléchargements…")
        try:
            with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED,
                                 compresslevel=6) as archive:
                for dirpath, dirnames, filenames in os.walk(self.stage):
                    self.check()
                    for name in sorted(filenames):
                        self.check()
                        source = Path(dirpath) / name
                        archive.write(source, source.relative_to(self.stage).as_posix())
            self.check()
            tmp_zip.replace(dest)
        finally:
            if tmp_zip.exists():
                tmp_zip.unlink(missing_ok=True)
        self.note(f"ZIP créé : {dest}")
        return dest


class DiagnosticWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WIN_TITLE)
        self.root.geometry("1030x760")
        self.root.minsize(860, 620)
        self.events = queue.Queue()
        self.cancel = threading.Event()
        self.running = False
        self.last_zip = None
        self.vars = {
            "Kristal": tk.StringVar(value=r"C:\mycode\Kristal"),
            "SemantiK": tk.StringVar(value=r"C:\mycode\SemantiK_Architect\SemantiK_Architect"),
            "PGF FR": tk.StringVar(value=r"C:\mycode\SemantiK_Architect\SemantiK_Architect\runtime\konstellation-fr-3\grammar.pgf"),
            "Python PGF": tk.StringVar(value=str(Path.home() / "AppData/Local/Programs/Python/Python312/python.exe") if sys.platform == "win32" else sys.executable),
            "EncyKlopedia": tk.StringVar(value=r"D:\EncyKlopedia"),
            "RUN": tk.StringVar(value=""),
        }
        self.logs = tk.BooleanVar(value=True)
        self.samples = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Prêt — les chemins sont modifiables.")
        self._build()
        self.root.after(100, self._poll)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _build(self):
        style = ttk.Style(self.root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Kristal / UNESCO — diagnostic", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        ttk.Label(outer, text="Inventaire en lecture seule · aucun programme du projet n'est exécuté").pack(anchor="w", pady=(1, 14))

        area = ttk.LabelFrame(outer, text="Dossiers du projet", padding=(12, 10))
        area.pack(fill="x")
        area.columnconfigure(1, weight=1)
        for row, (name, label) in enumerate((
            ("Kristal", "Kristal"),
            ("SemantiK", "SemantiK (projet)"),
            ("PGF FR", "PGF FR existant"),
            ("Python PGF", "Python 3.12 PGF"),
            ("EncyKlopedia", "EncyKlopedia"),
            ("RUN", "RUN (facultatif)"),
        )):
            ttk.Label(area, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            ent = ttk.Entry(area, textvariable=self.vars[name])
            ent.grid(row=row, column=1, sticky="ew", pady=5)
            ttk.Button(area, text="Parcourir…", command=lambda n=name: self._browse(n)).grid(
                row=row, column=2, padx=(10, 0), pady=5)

        flags = ttk.Frame(outer)
        flags.pack(fill="x", pady=(10, 4))
        ttk.Checkbutton(flags, text="Inclure les rapports et logs (20 Mio max)", variable=self.logs).pack(side="left", padx=(0, 22))
        ttk.Checkbutton(flags, text="Exemples FR / EN", variable=self.samples).pack(side="left")

        controls = ttk.Frame(outer)
        controls.pack(fill="x", pady=(7, 5))
        self.btn_start = ttk.Button(controls, text="Lancer le diagnostic", command=self._start)
        self.btn_start.pack(side="left")
        self.btn_cancel = ttk.Button(controls, text="Annuler", command=self._cancel, state="disabled")
        self.btn_cancel.pack(side="left", padx=9)
        ttk.Button(controls, text="Ouvrir Téléchargements", command=self._open_downloads).pack(side="left", padx=(15, 0))
        self.bar = ttk.Progressbar(controls, mode="indeterminate", length=150)
        self.bar.pack(side="right", padx=8)
        ttk.Label(outer, textvariable=self.status_text).pack(anchor="w", pady=(6, 4))

        logframe = ttk.LabelFrame(outer, text="Journal en direct", padding=6)
        logframe.pack(fill="both", expand=True, pady=(4, 0))
        self.text = scrolledtext.ScrolledText(
            logframe, state="disabled", wrap="none", font=("Consolas", 9),
            background="#111827", foreground="#e5e7eb", insertbackground="#ffffff",
            borderwidth=0,
        )
        self.text.pack(fill="both", expand=True)
        ttk.Label(outer, text="Le ZIP peut contenir des chemins et des logs sensibles : vérifie-le avant de le partager.",
                  foreground="#555555").pack(anchor="w", pady=(8, 0))

    def _browse(self, key):
        current = self.vars[key].get().strip()
        initial = current if Path(current).is_dir() else str(Path.home())
        if key in ("PGF FR", "Python PGF"):
            chosen = filedialog.askopenfilename(title=f"Choisir {key}")
        else:
            chosen = filedialog.askdirectory(title=f"Choisir le dossier {key}", initialdir=initial)
        if chosen:
            self.vars[key].set(chosen)

    def _start(self):
        if self.running:
            return
        if not all(self.vars[k].get().strip() for k in ("Kristal", "SemantiK", "EncyKlopedia")):
            messagebox.showwarning("Chemins manquants", "Renseigne les trois dossiers racines.")
            return
        self.running = True
        self.cancel.clear()
        self.last_zip = None
        self.btn_start.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.bar.start(12)
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")
        cfg = {key: var.get().strip() for key, var in self.vars.items()}
        cfg.update({"copy_logs": self.logs.get(), "copy_samples": self.samples.get()})
        worker = ReportBuilder(cfg, self.events, self.cancel)
        threading.Thread(target=worker.execute, name="kristal-diagnostic", daemon=True).start()
        self.status_text.set("Diagnostic en cours…")

    def _cancel(self):
        if self.running:
            self.cancel.set()
            self.status_text.set("Annulation demandée…")
            self.btn_cancel.configure(state="disabled")

    def _poll(self):
        try:
            for _ in range(100):
                try:
                    kind, payload = self.events.get_nowait()
                except queue.Empty:
                    break
                if kind == "log":
                    self.text.configure(state="normal")
                    self.text.insert("end", payload + "\n")
                    self.text.see("end")
                    self.text.configure(state="disabled")
                elif kind == "status":
                    self.status_text.set(payload)
                elif kind == "finished":
                    outcome, path, detail = payload
                    self.running = False
                    self.bar.stop()
                    self.btn_start.configure(state="normal")
                    self.btn_cancel.configure(state="disabled")
                    self.status_text.set(detail if outcome != "ok" else f"Terminé : {path}")
                    if outcome == "ok":
                        self.last_zip = path
                        messagebox.showinfo("Diagnostic terminé", f"ZIP créé :\n{path}")
                    elif outcome == "error":
                        messagebox.showerror("Diagnostic interrompu", detail)
        finally:
            self.root.after(100, self._poll)

    def _open_downloads(self):
        path = downloads_path()
        path.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            else:
                messagebox.showinfo("Téléchargements", str(path))
        except OSError as exc:
            messagebox.showerror("Ouverture impossible", str(exc))

    def _close(self):
        if self.running:
            if not messagebox.askyesno(
                "Fermer le diagnostic", "Le diagnostic est en cours. L'annuler et fermer ?"
            ):
                return
            self.cancel.set()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    DiagnosticWindow().run()
