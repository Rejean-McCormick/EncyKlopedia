#!/usr/bin/env python3
"""Audit en lecture seule des données et du code d'EncyKlopedia.

Aucune opération SQL d'écriture, migration, réparation, copie ou restauration.
Les seuls fichiers produits sont les rapports dans --output (TEMP par défaut via le .ps1).
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import time
from typing import Any

EXPECTED_DATA = [
    ("Catalogue UNESCO v25 (CRITIQUE)", "80_search_indexes/EncyKlopedia/catalogue_global_unesco_wikipedia_v25.sqlite", "sqlite"),
    ("Inventaire catégories Wikipédia v26", "80_search_indexes/EncyKlopedia/inventaire_categories_wikipedia_v26.sqlite", "sqlite"),
    ("Découverte des articles reliés v28", "30_working/decouverte_articles_relies_v28/DECOUVERTE_ARTICLES_RELIES_V28.sqlite", "sqlite"),
    ("Cumul privé Kristal v27", "30_working/production_kristals_v27/KRISTAL_CUMULATIF_PRIVE_V27.sqlite", "sqlite"),
    ("Station de production v30", "30_working/poste_chatgpt_v30/station_v30.sqlite", "sqlite"),
    ("Snapshots du catalogue v25", "30_working/catalogue_global_unesco_wikipedia_v25/snapshots", "directory"),
]
EXPECTED_CODE = [
    ("Lanceur poste ChatGPT v30", "LANCER_POSTE_CHATGPT_V30.ps1", "file"),
    ("Moteur poste ChatGPT v30", "tools/unesco_pilot/poste_chatgpt_v30.py", "file"),
]
DB_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".db3"}
PY_SUFFIXES = {".py", ".pyw"}
EXCLUDED_CODE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}
MAX_CHECK_SECONDS = 120.0
MAX_FULL_CHECK_BYTES = 2 * 1024 ** 3


def pretty(n: int) -> str:
    value = float(n)
    for unit in ("o", "Kio", "Mio", "Gio", "Tio"):
        if abs(value) < 1024 or unit == "Tio":
            return f"{value:.1f} {unit}" if unit != "o" else f"{int(value)} o"
        value /= 1024
    return str(n)


def scan_directory(root: Path, *, code: bool) -> tuple[list[dict], list[dict], list[dict], dict]:
    databases: list[dict] = []
    sides: list[dict] = []
    sources: list[dict] = []
    count_files = 0
    total_size = 0
    failures = []
    if not root.is_dir():
        return databases, sides, sources, {"files": 0, "bytes": 0, "errors": [f"Dossier introuvable : {root}"]}
    for base, dirs, files in os.walk(root, followlinks=False, onerror=lambda e: failures.append(str(e))):
        if code:
            dirs[:] = [x for x in dirs if x not in EXCLUDED_CODE_DIRS]
        for filename in files:
            p = Path(base) / filename
            try:
                if p.is_symlink():
                    continue
                st = p.stat()
            except OSError as exc:
                failures.append(f"{p}: {exc}")
                continue
            count_files += 1
            total_size += st.st_size
            low = filename.lower()
            if p.suffix.lower() in DB_SUFFIXES:
                databases.append({"path": str(p), "bytes": st.st_size, "mtime": st.st_mtime})
            if low.endswith((".sqlite-wal", ".sqlite3-wal", ".db-wal", ".db3-wal", ".sqlite-shm", ".sqlite3-shm", ".db-shm", ".db3-shm")):
                sides.append({"path": str(p), "bytes": st.st_size, "base": str(p)[:-4], "kind": low[-3:]})
            if code and p.suffix.lower() in PY_SUFFIXES:
                sources.append({"path": str(p), "bytes": st.st_size})
    return databases, sides, sources, {"files": count_files, "bytes": total_size, "errors": failures[:30]}


def check_db(row: dict, *, full: bool) -> dict:
    path = Path(row["path"])
    result: dict[str, Any] = dict(row)
    result["check"] = "integrity_check" if full else "quick_check"
    result["wal_bytes"] = (Path(str(path) + "-wal").stat().st_size
                           if Path(str(path) + "-wal").exists() else None)
    result["status"] = "INDETERMINE"
    result["details"] = ""
    try:
        with path.open("rb") as handle:
            header = handle.read(16)
        if header != b"SQLite format 3\x00":
            result["status"] = "NON_SQLITE"
            result["details"] = "En-tête non SQLite; ce fichier peut être un autre format .db"
            return result
        if path.stat().st_size < 100:
            result["status"] = "SUSPECT"
            result["details"] = "Fichier SQLite anormalement petit"
            return result
        t0 = time.monotonic()
        conn = sqlite3.connect(path.absolute().as_uri() + "?mode=ro", uri=True, timeout=3.0)
        try:
            conn.execute("PRAGMA query_only=ON")
            def progress() -> int:
                return int(time.monotonic() - t0 > MAX_CHECK_SECONDS)
            conn.set_progress_handler(progress, 20_000)
            pragma = "PRAGMA integrity_check(1)" if full else "PRAGMA quick_check(1)"
            value = conn.execute(pragma).fetchone()
            result["elapsed_s"] = round(time.monotonic() - t0, 2)
            if value and str(value[0]).lower() == "ok":
                result["status"] = "OK"
                result["details"] = "ok"
            else:
                result["status"] = "CORROMPU"
                result["details"] = str(value[0]) if value else "Aucun résultat"
        finally:
            conn.close()
    except Exception as exc:
        msg = str(exc)
        result["status"] = "INTERROMPU" if "interrupted" in msg.lower() else "ERREUR"
        result["details"] = msg[:700]
    return result


def test_python(row: dict) -> dict:
    out = dict(row)
    path = Path(row["path"])
    try:
        with path.open("rb") as f:
            data = f.read()
        if len(data) > 12 * 1024 * 1024:
            out["status"] = "IGNORÉ"
            out["details"] = "Fichier source > 12 Mio"
        else:
            ast.parse(data, filename=str(path))
            out["status"] = "OK"
    except Exception as exc:
        out["status"] = "ERREUR_SYNTAXE"
        out["details"] = str(exc)[:500]
    return out


def snapshots_info(path: Path) -> dict:
    out = {"path": str(path), "exists": path.is_dir(), "last": []}
    if not path.is_dir():
        return out
    try:
        children = sorted((x for x in path.iterdir() if x.is_dir()), key=lambda x: x.name, reverse=True)
        for d in children[:3]:
            files = []
            for sub, _dirs, fnames in os.walk(d):
                for f in fnames:
                    p = Path(sub) / f
                    try:
                        st = p.stat()
                    except OSError:
                        continue
                    files.append({"file": str(p.relative_to(d)), "bytes": st.st_size})
            full_db = [f for f in files if Path(f["file"]).suffix.lower() in DB_SUFFIXES]
            out["last"].append({"snapshot": d.name, "files": len(files), "sqlite_copies": full_db})
    except OSError as e:
        out["error"] = str(e)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description="Audit EncyKlopedia, sans modifier les fichiers de production")
    p.add_argument("--data", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    data = Path(args.data)
    repo = Path(args.repo)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    start = datetime.now(timezone.utc).isoformat()
    print(f"\n=== AUDIT ENCYKLOPEDIA / {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===", flush=True)
    print("Aucun traitement EncyKlopedia, aucune réparation ni migration.", flush=True)
    critical = []
    for label, rel, kind in EXPECTED_DATA:
        path = data / Path(rel)
        exists = path.is_dir() if kind == "directory" else path.is_file()
        row = {"name": label, "path": str(path), "kind": kind, "exists": exists}
        if exists and kind == "sqlite":
            row["bytes"] = path.stat().st_size
        critical.append(row)
        print(f"{'OK      ' if exists else 'MANQUANT '} {label}: {path}", flush=True)
    for label, rel, kind in EXPECTED_CODE:
        path = repo / Path(rel)
        exists = path.is_file()
        critical.append({"name": label, "path": str(path), "kind": kind, "exists": exists})
        print(f"{'OK      ' if exists else 'MANQUANT '} {label}: {path}", flush=True)

    print("\nInventaire des fichiers sur D:\\EncyKlopedia (peut prendre du temps)...", flush=True)
    data_dbs, data_sides, _ignore, data_stats = scan_directory(data, code=False)
    print(f"{data_stats['files']} fichiers, {len(data_dbs)} bases potentielles. Total inventorié : {pretty(data_stats['bytes'])}.", flush=True)
    print("Inventaire et analyse syntaxique des scripts Python du dépôt...", flush=True)
    repo_dbs, repo_sides, sources, repo_stats = scan_directory(repo, code=True)
    python_results = [test_python(src) for src in sources]
    syntax_errors = [r for r in python_results if r["status"] == "ERREUR_SYNTAXE"]
    print(f"{len(python_results)} scripts Python examinés, {len(syntax_errors)} erreurs de syntaxe.", flush=True)

    dbs = {d["path"].lower(): d for d in data_dbs + repo_dbs}
    expected_sqlite = {str(data / Path(rel)).lower() for _, rel, kind in EXPECTED_DATA if kind == "sqlite"}
    ordered = sorted(dbs.values(), key=lambda d: (d["path"].lower() not in expected_sqlite, -d["bytes"], d["path"]))
    checks = []
    print(f"\nContrôle de cohérence de {len(ordered)} bases SQLite potentielles :", flush=True)
    for idx, entry in enumerate(ordered, 1):
        critical_db = entry["path"].lower() in expected_sqlite
        use_full = critical_db and entry["bytes"] <= MAX_FULL_CHECK_BYTES
        print(f"[{idx}/{len(ordered)}] {Path(entry['path']).name} ({pretty(entry['bytes'])}) : ", end="", flush=True)
        res = check_db(entry, full=use_full)
        print(f"{res['status']} [{res['check']}] {res['details'][:150]}", flush=True)
        checks.append(res)

    sides = data_sides + repo_sides
    orphan_sides = [x for x in sides if not Path(x["base"]).exists()]
    snaps = snapshots_info(data / "30_working/catalogue_global_unesco_wikipedia_v25/snapshots")
    try:
        usage = {str(root): {"free": shutil.disk_usage(root).free, "total": shutil.disk_usage(root).total}
                 for root in (data, repo) if root.exists()}
    except OSError:
        usage = {}
    report: dict[str, Any] = {
        "created_utc": start,
        "data_root": str(data),
        "repo_root": str(repo),
        "note": "Audit logique, pas de comparaison avec une sauvegarde de référence. Les bases non-SQLite et les données sources volumineuses ne sont pas intégralement hachées.",
        "critical_files": critical,
        "data_inventory": data_stats,
        "repo_inventory": repo_stats,
        "disk_usage": usage,
        "sqlite_checks": checks,
        "sqlite_sidecars": sides,
        "orphan_sidecars": orphan_sides,
        "python_source_results": python_results,
        "snapshots": snaps,
    }
    json_path = out_dir / "rapport_integrite_encyklopedia.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    missing = [r for r in critical if not r["exists"]]
    failed = [r for r in checks if r["status"] in ("CORROMPU", "ERREUR", "INTERROMPU", "SUSPECT")]
    not_sqlite = [r for r in checks if r["status"] == "NON_SQLITE"]
    passed = [r for r in checks if r["status"] == "OK"]
    lines = [
        "RAPPORT D'INTEGRITE ENCYKLOPEDIA — LECTURE SEULE",
        "Date UTC : " + start,
        f"Racine données : {data}",
        f"Racine code : {repo}",
        "",
        f"Fichiers essentiels manquants : {len(missing)}",
        *[f"  MANQUANT : {r['name']} — {r['path']}" for r in missing],
        f"SQLite vérifiés OK : {len(passed)} / {len(checks)}",
        f"SQLite en erreur ou suspects : {len(failed)}",
        *[f"  {r['status']} : {r['path']} — {r['details']}" for r in failed],
        f"Autres fichiers .db non-SQLite : {len(not_sqlite)}",
        *[f"  NON SQLITE : {r['path']}" for r in not_sqlite],
        f"Fichiers WAL/SHM sans base principale : {len(orphan_sides)}",
        *[f"  ORPHELIN : {r['path']} ({pretty(r['bytes'])})" for r in orphan_sides],
        f"Scripts Python analysés : {len(python_results)}",
        f"Scripts Python avec erreur : {len(syntax_errors)}",
        *[f"  ERREUR SYNTAXE : {r['path']} — {r.get('details', '')}" for r in syntax_errors],
        f"Erreurs d'inventaire de fichiers : {len(data_stats['errors']) + len(repo_stats['errors'])}",
        *[f"  INVENTAIRE : {e}" for e in data_stats["errors"] + repo_stats["errors"]],
        "",
        "SNAPSHOTS RECENTS :",
        *[f"  {x['snapshot']} : {x['files']} fichiers, {len(x['sqlite_copies'])} copie(s) SQLite" for x in snaps.get("last", [])],
        "",
        "IMPORTANT : ce contrôle ne prouve pas l'intégrité des archives de 100 Go ni des fichiers non-SQLite sans référence de hachage.",
        "IMPORTANT : un SQLite OK n'implique pas que le catalogue manquant soit restauré.",
        f"Rapport JSON complet : {json_path}",
    ]
    text_path = out_dir / "rapport_integrite_encyklopedia.txt"
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines), flush=True)
    print("\nAucune base EncyKlopedia n'a été modifiée par le script (aucune commande SQL d'écriture).", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nAudit interrompu volontairement. Aucun changement des bases demandé.", file=sys.stderr)
        raise SystemExit(130)
