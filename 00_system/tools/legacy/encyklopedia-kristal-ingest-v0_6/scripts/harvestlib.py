from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

OFFSETS = {"Q": 0, "P": 1_000_000_000, "L": 2_000_000_000}


def find_root(start: str | Path | None = None) -> Path:
    p = Path(start or __file__).resolve()
    if p.is_file():
        p = p.parent
    for cand in [p, *p.parents]:
        if (cand / "MANIFEST.json").exists() and (cand / "10_sources").exists() and (cand / "30_working").exists():
            return cand
    raise RuntimeError("Racine EncyKlopedia introuvable")


def encode_wid(wid: str | None) -> int | None:
    if not wid or len(wid) < 2:
        return None
    p = wid[0].upper()
    if p not in OFFSETS or not wid[1:].isdigit():
        return None
    return OFFSETS[p] + int(wid[1:])


def decode_wid(n: int | None) -> str | None:
    if n is None:
        return None
    n = int(n)
    if n >= OFFSETS["L"]:
        return f"L{n-OFFSETS['L']}"
    if n >= OFFSETS["P"]:
        return f"P{n-OFFSETS['P']}"
    return f"Q{n}"


def load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8-sig"))


def save_json(path: str | Path, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, p)


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> int:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with p.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            n += 1
    return n


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    out = []
    with p.open(encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def sha256_file(path: str | Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_run_id(prefix: str = "harvest") -> str:
    return datetime.now().strftime(f"{prefix}_%Y%m%d_%H%M%S")


def relpath(path: str | Path, root: str | Path) -> str:
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except Exception:
        return str(Path(path))


def open_db(path: str | Path, read_only: bool = True) -> sqlite3.Connection:
    p = Path(path).resolve()
    if read_only:
        c = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    else:
        c = sqlite3.connect(p)
    c.row_factory = sqlite3.Row
    return c


def db_meta(c: sqlite3.Connection) -> dict[str, str]:
    try:
        return {r["key"]: r["value"] for r in c.execute("SELECT key,value FROM meta")}
    except sqlite3.DatabaseError:
        return {}


def assert_db_ready(c: sqlite3.Connection, allow_partial: bool = False) -> dict[str, str]:
    m = db_meta(c)
    needed = {"entity", "name", "claim_presence", "entity_edge", "chronology"}
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = needed - tables
    if missing:
        raise RuntimeError(f"Index SQLite incomplet: tables manquantes {sorted(missing)}")
    if not allow_partial and m.get("complete") not in {"1", "true", "True"}:
        raise RuntimeError("Index Wikidata non marqué complete=1. Termine le build ou active allow_partial explicitement.")
    return m


def load_registry(path: str | Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    obj = load_json(path, {})
    if isinstance(obj, dict):
        return obj, list(obj.get("records") or [])
    return {"schema_version": "unknown"}, list(obj or [])


def load_qid_map(path: str | Path) -> dict[str, dict[str, Any]]:
    obj = load_json(path, {}) or {}
    out: dict[str, dict[str, Any]] = {}
    for k, v in obj.items():
        if isinstance(v, str):
            out[k] = {"qid": v}
        elif isinstance(v, dict):
            out[k] = v
    return out


def qid_rows(registry: list[dict[str, Any]], qmap: dict[str, dict[str, Any]]) -> list[tuple[dict[str, Any], str, dict[str, Any]]]:
    out = []
    for seed in registry:
        m = qmap.get(seed.get("key"), {})
        qid = m.get("qid")
        if qid:
            out.append((seed, qid, m))
    return out


def entity(c: sqlite3.Connection, eid: int | None) -> dict[str, Any]:
    if eid is None:
        return {}
    r = c.execute("SELECT * FROM entity WHERE id=?", (eid,)).fetchone()
    if not r:
        return {"wid": decode_wid(eid), "label_fr": None, "label_en": None, "label_mul": None, "kind": None}
    return dict(r)


def aliases(c: sqlite3.Connection, eid: int, max_aliases: int = 80) -> list[dict[str, str]]:
    rows = c.execute(
        "SELECT lang,name_kind,value FROM name WHERE entity_id=? ORDER BY lang,name_kind,value LIMIT ?",
        (eid, max_aliases),
    ).fetchall()
    return [{"lang": r["lang"], "kind": "label" if r["name_kind"] == 0 else "alias", "value": r["value"]} for r in rows]


def chronology(c: sqlite3.Connection, eid: int) -> list[dict[str, Any]]:
    return [
        {"property_id": f"P{r['property_id']}", "year": r["year"], "precision": r["precision"]}
        for r in c.execute("SELECT property_id,year,precision FROM chronology WHERE subject_id=? ORDER BY property_id,year", (eid,))
    ]


def relation_presence(c: sqlite3.Connection, eid: int) -> list[dict[str, Any]]:
    return [
        {
            "property_id": f"P{r['property_id']}",
            "datatype": r["datatype"],
            "statement_count": r["statement_count"],
            "preferred_count": r["preferred_count"],
            "normal_count": r["normal_count"],
            "deprecated_count": r["deprecated_count"],
        }
        for r in c.execute("SELECT * FROM claim_presence WHERE subject_id=? ORDER BY property_id", (eid,))
    ]


def pid_num(pid: str | int) -> int:
    if isinstance(pid, int):
        return pid
    if not (pid.startswith("P") and pid[1:].isdigit()):
        raise ValueError(pid)
    return int(pid[1:])


def relation_edges(c: sqlite3.Connection, subject_eid: int, relations: dict[str, str]) -> list[dict[str, Any]]:
    if not relations:
        return []
    pnums = [pid_num(p) for p in relations]
    qs = ",".join("?" * len(pnums))
    out = []
    for r in c.execute(
        f"SELECT subject_id,property_id,target_id,statement_count,best_rank FROM entity_edge WHERE subject_id=? AND property_id IN ({qs}) ORDER BY property_id,target_id",
        [subject_eid, *pnums],
    ):
        target = entity(c, r["target_id"])
        pid = f"P{r['property_id']}"
        out.append({
            "property_id": pid,
            "role": relations.get(pid),
            "target_wid": decode_wid(r["target_id"]),
            "target_label_fr": target.get("label_fr"),
            "target_label_en": target.get("label_en"),
            "statement_count": r["statement_count"],
            "best_rank": r["best_rank"],
        })
    return out


def reverse_edges(c: sqlite3.Connection, target_eid: int, relations: dict[str, str], limit: int = 0) -> list[dict[str, Any]]:
    if not relations:
        return []
    pnums = [pid_num(p) for p in relations]
    qs = ",".join("?" * len(pnums))
    sql = f"SELECT subject_id,property_id,target_id,statement_count,best_rank FROM entity_edge WHERE target_id=? AND property_id IN ({qs}) ORDER BY property_id,subject_id"
    params: list[Any] = [target_eid, *pnums]
    if limit:
        sql += " LIMIT ?"
        params.append(limit)
    out = []
    for r in c.execute(sql, params):
        subject = entity(c, r["subject_id"])
        pid = f"P{r['property_id']}"
        out.append({
            "property_id": pid,
            "role": relations.get(pid),
            "source_wid": decode_wid(r["subject_id"]),
            "source_label_fr": subject.get("label_fr"),
            "source_label_en": subject.get("label_en"),
            "statement_count": r["statement_count"],
            "best_rank": r["best_rank"],
        })
    return out


def object_record(c: sqlite3.Connection, wid: str, describe_relations: dict[str, str], include_presence: bool = True) -> dict[str, Any]:
    eid = encode_wid(wid)
    e = entity(c, eid)
    if not e:
        return {"wid": wid}
    out = {
        "wid": wid,
        "kind": e.get("kind"),
        "labels": {"fr": e.get("label_fr"), "en": e.get("label_en"), "mul": e.get("label_mul")},
        "descriptions": {"fr": e.get("description_fr"), "en": e.get("description_en")},
        "aliases": aliases(c, eid),
        "relations": relation_edges(c, eid, describe_relations),
    }
    if include_presence:
        out["available_relations"] = relation_presence(c, eid)
    return out


def files_manifest(base: Path, names: list[str]) -> list[dict[str, Any]]:
    rows = []
    for name in names:
        p = base / name
        if p.exists() and p.is_file():
            rows.append({"path": name.replace("\\", "/"), "bytes": p.stat().st_size, "sha256": sha256_file(p)})
    return rows


def copy_snapshot(src_dir: Path, dst_dir: Path, files: list[str]) -> None:
    dst_dir.mkdir(parents=True, exist_ok=False)
    for name in files:
        s = src_dir / name
        if s.exists():
            d = dst_dir / name
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
