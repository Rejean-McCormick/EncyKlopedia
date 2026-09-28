#!/usr/bin/env python3
"""Pull first-level Wikidata relation signatures for a curated registry.

The output intentionally DOES NOT store claim values.  For each resolved item, it
stores only the properties that occur as top-level claims (plus safe metadata such
as datatype and statement count). Qualifiers and reference properties are not
included because they are not first-level relations of the person/item.

Two phases:
  1. Resolve seed names to Wikidata QIDs conservatively (unless a qid-map is supplied).
  2. Fetch claims in batches and reduce each entity to a relation/property signature.

Wikidata endpoints used:
  - Action API: wbsearchentities, wbgetentities

Example:
  python scripts/pull_wikidata_relation_signatures.py \
      --registry config/intellectuals.seed.snapshot.json \
      --out output

Resume / pin identity resolution:
  python scripts/pull_wikidata_relation_signatures.py \
      --registry config/intellectuals.seed.snapshot.json \
      --qid-map output/qid-map.json \
      --out output
"""
from __future__ import annotations

import argparse
import csv
import email.utils
import gzip
import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

API = "https://www.wikidata.org/w/api.php"
APP_VERSION = "0.3.1"
DEFAULT_CONTACT = os.environ.get("KOA_WIKIMEDIA_CONTACT", "").strip()
USER_AGENT = f"kOA-HistoricalRegistry/{APP_VERSION} ({DEFAULT_CONTACT or 'local research tool'}) Python-urllib"
MAX_RETRIES = 8
BACKOFF_BASE = 2.0
MAXLAG = 5

# These are NOT filters. They are only named groups for later coverage summaries.
FOCUS_GROUPS = {
    "identity_and_type": ["P31", "P21", "P1559", "P735", "P734"],
    "chronology": ["P569", "P570", "P1317"],
    "geography": ["P19", "P20", "P27", "P495", "P551"],
    "intellectual_context": ["P101", "P106", "P135", "P140", "P1142", "P737"],
    "works_bridge": ["P800"],
    "education_and_affiliation": ["P69", "P108", "P463"],
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip()
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        dt = email.utils.parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0.0, (dt - datetime.now(timezone.utc)).total_seconds())
    except Exception:
        return None


def configure_http(*, contact: str | None = None, max_retries: int | None = None, backoff_base: float | None = None) -> None:
    global USER_AGENT, MAX_RETRIES, BACKOFF_BASE
    if contact is not None:
        contact = contact.strip()
        USER_AGENT = f"kOA-HistoricalRegistry/{APP_VERSION} ({contact or 'local research tool'}) Python-urllib"
    if max_retries is not None:
        MAX_RETRIES = max(1, int(max_retries))
    if backoff_base is not None:
        BACKOFF_BASE = max(0.5, float(backoff_base))


def http_json(params: dict[str, Any], *, timeout: int = 40, retries: int | None = None) -> dict[str, Any]:
    """GET JSON from Wikidata with gzip handling, maxlag, and 429/503 backoff."""
    params = dict(params)
    params.setdefault("maxlag", MAXLAG)
    qs = urllib.parse.urlencode(params, doseq=True)
    url = f"{API}?{qs}"
    retry_count = retries if retries is not None else MAX_RETRIES
    last: Exception | None = None

    for attempt in range(retry_count):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Api-User-Agent": USER_AGENT,
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                content_encoding = (resp.headers.get("Content-Encoding") or "").lower()
                if "gzip" in content_encoding or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                payload = json.loads(raw.decode("utf-8"))

                # maxlag is normally a JSON API error (often HTTP 200). Treat it as retryable.
                err = payload.get("error") if isinstance(payload, dict) else None
                if isinstance(err, dict) and err.get("code") == "maxlag":
                    wait = max(5.0, BACKOFF_BASE * (2 ** attempt))
                    print(f"[Wikidata maxlag] pause {wait:.1f}s avant reprise ({attempt+1}/{retry_count})", file=sys.stderr, flush=True)
                    time.sleep(wait)
                    continue
                return payload

        except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
            last = exc
            if exc.code not in {429, 503} or attempt + 1 >= retry_count:
                raise
            retry_after = _retry_after_seconds(exc.headers.get("Retry-After") if exc.headers else None)
            wait = max(retry_after or 5.0, BACKOFF_BASE * (2 ** attempt))
            # Cap a single sleep but remain deliberately conservative.
            wait = min(wait, 300.0)
            print(f"[HTTP {exc.code}] Wikidata demande de ralentir; pause {wait:.1f}s ({attempt+1}/{retry_count})", file=sys.stderr, flush=True)
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:  # pragma: no cover - network dependent
            last = exc
            if attempt + 1 >= retry_count:
                raise
            wait = min(max(2.0, BACKOFF_BASE * (2 ** attempt)), 120.0)
            print(f"[réseau] {exc}; nouvelle tentative dans {wait:.1f}s ({attempt+1}/{retry_count})", file=sys.stderr, flush=True)
            time.sleep(wait)

    assert last is not None
    raise last


def batched(xs: list[str], n: int) -> Iterable[list[str]]:
    for i in range(0, len(xs), n):
        yield xs[i : i + n]


def normalize_name(s: str | None) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.casefold()
    s = re.sub(r"[^\w]+", " ", s, flags=re.UNICODE)
    return " ".join(s.split())


def claims_values(entity: dict[str, Any], pid: str) -> list[Any]:
    out: list[Any] = []
    for claim in entity.get("claims", {}).get(pid, []):
        snak = claim.get("mainsnak", {})
        if snak.get("snaktype") != "value":
            continue
        dv = snak.get("datavalue") or {}
        if "value" in dv:
            out.append(dv["value"])
    return out


def year_from_time(v: Any) -> int | None:
    if not isinstance(v, dict):
        return None
    t = v.get("time")
    if not isinstance(t, str):
        return None
    m = re.match(r"^([+-])(\d+)-", t)
    if not m:
        return None
    y = int(m.group(2))
    return -y if m.group(1) == "-" else y


def entity_names(entity: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for obj in entity.get("labels", {}).values():
        if obj.get("value"):
            out.add(normalize_name(obj["value"]))
    for arr in entity.get("aliases", {}).values():
        for obj in arr:
            if obj.get("value"):
                out.add(normalize_name(obj["value"]))
    return {x for x in out if x}


def get_entities(ids: list[str], props: str, languages: str | None = None) -> dict[str, dict[str, Any]]:
    if not ids:
        return {}
    params: dict[str, Any] = {
        "action": "wbgetentities",
        "ids": "|".join(ids),
        "props": props,
        "format": "json",
        "formatversion": 2,
    }
    if languages:
        params["languages"] = languages
        params["languagefallback"] = 1
    payload = http_json(params)
    entities = payload.get("entities", {})
    if isinstance(entities, list):
        return {e.get("id"): e for e in entities if e.get("id")}
    return entities


def search_entities(name: str, language: str, limit: int = 8) -> list[dict[str, Any]]:
    payload = http_json({
        "action": "wbsearchentities",
        "search": name,
        "language": language,
        "uselang": language,
        "type": "item",
        "limit": limit,
        "format": "json",
        "formatversion": 2,
    })
    return payload.get("search", [])


@dataclass
class Resolution:
    qid: str | None
    confidence: str
    score: float | None
    candidates: list[dict[str, Any]]


def score_candidate(seed: dict[str, Any], hit: dict[str, Any], ent: dict[str, Any]) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    wanted = normalize_name(seed.get("display_name"))
    names = entity_names(ent)
    if wanted and wanted in names:
        score += 60
        reasons.append("exact_name_or_alias")
    elif wanted and normalize_name(hit.get("label")) == wanted:
        score += 45
        reasons.append("exact_search_label")

    seed_birth = (seed.get("chronology") or {}).get("birth_year")
    wd_births = [year_from_time(v) for v in claims_values(ent, "P569")]
    wd_births = [x for x in wd_births if x is not None]
    wd_birth = wd_births[0] if wd_births else None
    if isinstance(seed_birth, int) and isinstance(wd_birth, int):
        diff = abs(seed_birth - wd_birth)
        approx = bool((seed.get("chronology") or {}).get("approximate"))
        tol = 25 if approx or seed_birth < 0 else 3
        if diff == 0:
            score += 30
            reasons.append("birth_year_exact")
        elif diff <= tol:
            score += max(5, 25 - diff)
            reasons.append(f"birth_year_close:{diff}")
        elif diff > max(100, tol * 4):
            score -= 50
            reasons.append(f"birth_year_conflict:{diff}")

    p31 = {v.get("id") for v in claims_values(ent, "P31") if isinstance(v, dict)}
    kind = seed.get("representation_kind", "")
    if kind in {"historical_person", "historical_religious_figure", "living_person_reference"} and "Q5" in p31:
        score += 8
        reasons.append("instance_human")
    if hit.get("match", {}).get("type") == "alias":
        score += 2
        reasons.append("matched_alias")
    return score, reasons


def _score_hits(seed: dict[str, Any], hits: dict[str, dict[str, Any]], sleep: float) -> list[dict[str, Any]]:
    candidate_ids = list(hits)[:16]
    entities: dict[str, dict[str, Any]] = {}
    for batch in batched(candidate_ids, 50):
        entities.update(get_entities(batch, "labels|aliases|claims", "en|fr|mul"))
        time.sleep(sleep)
    scored: list[dict[str, Any]] = []
    for qid in candidate_ids:
        ent = entities.get(qid, {})
        score, reasons = score_candidate(seed, hits[qid], ent)
        scored.append({
            "qid": qid,
            "score": score,
            "label": hits[qid].get("label"),
            "description": hits[qid].get("description"),
            "reasons": reasons,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def _resolution_from_scored(scored: list[dict[str, Any]]) -> Resolution:
    if not scored:
        return Resolution(None, "unresolved", None, [])
    best = scored[0]
    second = scored[1] if len(scored) > 1 else None
    gap = best["score"] - second["score"] if second else math.inf
    if best["score"] >= 70 and gap >= 12:
        return Resolution(best["qid"], "high", best["score"], scored[:5])
    if best["score"] >= 55 and gap >= 20:
        return Resolution(best["qid"], "medium", best["score"], scored[:5])
    return Resolution(None, "ambiguous", best["score"], scored[:5])


def resolve(seed: dict[str, Any], sleep: float) -> Resolution:
    """Resolve conservatively while minimizing wbsearchentities calls.

    Search one language first and only pay for the second language when the first pass
    is not decisive. This substantially reduces request volume for bulk runs.
    """
    display = seed["display_name"]
    # French first for names containing diacritics; English otherwise.
    primary, secondary = (("fr", "en") if any(ord(ch) > 127 for ch in display) else ("en", "fr"))
    hits: dict[str, dict[str, Any]] = {}
    for hit in search_entities(display, primary):
        hits.setdefault(hit["id"], hit)
    time.sleep(sleep)
    first = _resolution_from_scored(_score_hits(seed, hits, sleep))
    if first.qid:
        return first

    # Fallback language only for unresolved / ambiguous cases.
    for hit in search_entities(display, secondary):
        hits.setdefault(hit["id"], hit)
    time.sleep(sleep)
    return _resolution_from_scored(_score_hits(seed, hits, sleep))


def first_level_signature(entity: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Reduce entity claims to presence metadata; never return a claim value."""
    out: dict[str, dict[str, Any]] = {}
    for pid, statements in sorted((entity.get("claims") or {}).items()):
        datatypes: set[str] = set()
        snaktypes: Counter[str] = Counter()
        ranks: Counter[str] = Counter()
        for st in statements:
            main = st.get("mainsnak") or {}
            if main.get("datatype"):
                datatypes.add(main["datatype"])
            snaktypes[main.get("snaktype", "unknown")] += 1
            ranks[st.get("rank", "normal")] += 1
        out[pid] = {
            "present": True,
            "statement_count": len(statements),
            "datatypes_seen": sorted(datatypes),
            "snaktypes": dict(sorted(snaktypes.items())),
            "ranks": dict(sorted(ranks.items())),
        }
    return out


def property_catalog(pids: list[str], sleep: float) -> dict[str, dict[str, Any]]:
    cat: dict[str, dict[str, Any]] = {}
    for batch in batched(sorted(pids), 50):
        ents = get_entities(batch, "labels|descriptions|datatype", "en|fr")
        for pid, e in ents.items():
            labels = e.get("labels") or {}
            descriptions = e.get("descriptions") or {}
            en = labels.get("en", {}).get("value")
            fr = labels.get("fr", {}).get("value")
            cat[pid] = {
                "property_id": pid,
                "label_en": en,
                "label_fr": fr,
                "description_en": descriptions.get("en", {}).get("value"),
                "description_fr": descriptions.get("fr", {}).get("value"),
                "datatype": e.get("datatype"),
            }
        time.sleep(sleep)
    return cat


def relation_class(datatype: str | None) -> str:
    if datatype in {"wikibase-item", "wikibase-property", "wikibase-lexeme", "wikibase-form", "wikibase-sense"}:
        return "semantic_relation"
    if datatype == "external-id":
        return "external_identifier"
    if datatype in {"commonsMedia", "url", "geo-shape", "tabular-data", "musical-notation"}:
        return "media_or_locator"
    return "literal_attribute"


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)


def estimate_pull(registry_path: Path, qid_map_path: Path | None, sleep: float, sample_size: int, checkpoint_path: Path | None = None) -> dict[str, Any]:
    """Estimate phase-1 network/output size by querying a small sample only.

    This is intentionally an estimate, not a quota promise. It samples actual Wikidata
    responses, computes relation density and serialized signature size, then projects to
    the full registry. No output files are written.
    """
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    seeds: list[dict[str, Any]] = list(registry.get("records") or [])
    total = len(seeds)
    if not seeds:
        return {"seed_count": 0, "sample_count": 0}

    qid_map: dict[str, str] = {}
    if qid_map_path and qid_map_path.exists():
        qid_map.update(json.loads(qid_map_path.read_text(encoding="utf-8")))

    n = min(max(1, sample_size), total)
    # Spread the sample across the registry instead of only sampling the first historical period.
    if n == total:
        sample = seeds
    else:
        idxs = sorted({round(i * (total - 1) / max(1, n - 1)) for i in range(n)})
        sample = [seeds[i] for i in idxs]

    resolved: list[tuple[dict[str, Any], str]] = []
    unresolved = 0
    request_like_units = 0
    for seed in sample:
        key = seed["key"]
        qid = qid_map.get(key)
        if qid:
            resolved.append((seed, qid))
            continue
        res = resolve(seed, sleep)
        request_like_units += 2  # usually one search + one candidate hydration; fallback may add two more
        if res.qid:
            resolved.append((seed, res.qid))
            qid_map[key] = res.qid
            if checkpoint_path:
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                checkpoint_path.write_text(json.dumps(qid_map, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            unresolved += 1

    entities: dict[str, dict[str, Any]] = {}
    qids = [q for _, q in resolved]
    for batch in batched(qids, 50):
        entities.update(get_entities(batch, "labels|claims", "en|fr"))
        request_like_units += 1
        time.sleep(sleep)

    relation_counts: list[int] = []
    jsonl_sizes: list[int] = []
    pids: set[str] = set()
    for seed, qid in resolved:
        e = entities.get(qid, {})
        sig = first_level_signature(e)
        relation_counts.append(len(sig))
        pids.update(sig)
        synthetic = {
            "seed_key": seed.get("key"),
            "seed_display_name": seed.get("display_name"),
            "qid": qid,
            "relation_count": len(sig),
            "relations": sig,
        }
        jsonl_sizes.append(len((json.dumps(synthetic, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")))

    resolved_sample = len(resolved)
    resolve_rate = resolved_sample / max(1, len(sample))
    projected_resolved = round(total * resolve_rate)
    avg_rel = sum(relation_counts) / max(1, len(relation_counts))
    avg_jsonl = sum(jsonl_sizes) / max(1, len(jsonl_sizes))
    projected_signature_bytes = round(avg_jsonl * projected_resolved)
    projected_matrix_cells = round(projected_resolved * max(1, len(pids)))
    # Dense CSV is roughly 2 bytes/cell plus headers/identity fields for 0/1 cells and commas.
    projected_matrix_bytes = projected_matrix_cells * 2 + projected_resolved * 80 + len(pids) * 8
    projected_catalog_bytes = max(1, len(pids)) * 180
    projected_disk = projected_signature_bytes + projected_matrix_bytes + projected_catalog_bytes

    # Approximate request count from actual algorithm: unresolved-name resolution dominates.
    pinned_full = sum(1 for s in seeds if s.get("key") in qid_map)
    need_resolution = total - pinned_full
    est_api_calls = need_resolution * 3 + math.ceil(projected_resolved / 50) + math.ceil(max(1, len(pids)) / 50)

    return {
        "seed_count": total,
        "sample_count": len(sample),
        "sample_resolved": resolved_sample,
        "sample_unresolved": unresolved,
        "projected_resolved": projected_resolved,
        "avg_first_level_relations": round(avg_rel, 2),
        "sample_unique_properties": len(pids),
        "estimated_api_calls": est_api_calls,
        "estimated_output_bytes": projected_disk,
        "estimated_output_mib": round(projected_disk / (1024 * 1024), 2),
        "estimated_signature_jsonl_mib": round(projected_signature_bytes / (1024 * 1024), 2),
        "estimated_matrix_mib": round(projected_matrix_bytes / (1024 * 1024), 2),
        "warning": "Projection from a small live sample; ancient/mythic and modern records can have very different relation density.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registry", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--qid-map", default=None, help="JSON mapping seed_key -> QID; unresolved names are searched if absent")
    ap.add_argument("--sleep", type=float, default=0.75, help="pause minimale entre appels API; 0.75s recommandé")
    ap.add_argument("--contact", default=DEFAULT_CONTACT, help="email ou URL de contact pour le User-Agent Wikimedia")
    ap.add_argument("--max-retries", type=int, default=8, help="reprises sur HTTP 429/503")
    ap.add_argument("--backoff-base", type=float, default=2.0, help="base du backoff exponentiel en secondes")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--semantic-matrix-only", action="store_true", help="matrix contains only entity-valued properties")
    ap.add_argument("--estimate-only", action="store_true", help="query a sample and estimate phase-1 size; write no pull outputs")
    ap.add_argument("--sample-size", type=int, default=12, help="number of registry records sampled by --estimate-only")
    args = ap.parse_args()
    configure_http(contact=args.contact, max_retries=args.max_retries, backoff_base=args.backoff_base)

    if not args.contact:
        print("[note] Ajoute --contact email-ou-URL pour un User-Agent Wikimedia pleinement identifiable.", file=sys.stderr, flush=True)

    if args.estimate_only:
        outdir = Path(args.out)
        outdir.mkdir(parents=True, exist_ok=True)
        checkpoint = Path(args.qid_map) if args.qid_map else (outdir / "qid-map.json")
        info = estimate_pull(
            Path(args.registry),
            checkpoint if checkpoint.exists() else None,
            args.sleep,
            args.sample_size,
            checkpoint_path=checkpoint,
        )
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    registry = json.loads(Path(args.registry).read_text(encoding="utf-8"))
    seeds: list[dict[str, Any]] = list(registry.get("records") or [])
    if args.limit:
        seeds = seeds[: args.limit]
    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)

    qid_map: dict[str, str] = {}
    if args.qid_map and Path(args.qid_map).exists():
        qid_map.update(json.loads(Path(args.qid_map).read_text(encoding="utf-8")))

    seed_by_key = {s["key"]: s for s in seeds}
    checkpoint_path = outdir / "qid-map.json"
    unresolved: list[dict[str, Any]] = []
    resolution_meta: dict[str, dict[str, Any]] = {}
    for i, seed in enumerate(seeds, 1):
        key = seed["key"]
        if key in qid_map:
            resolution_meta[key] = {"confidence": "pinned", "score": None, "candidates": []}
            continue
        res = resolve(seed, args.sleep)
        if res.qid:
            qid_map[key] = res.qid
            checkpoint_path.write_text(json.dumps(qid_map, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            resolution_meta[key] = {"confidence": res.confidence, "score": res.score, "candidates": res.candidates}
            print(f"[{i}/{len(seeds)}] resolve {key} -> {res.qid} ({res.confidence})", flush=True)
        else:
            unresolved.append({
                "seed_key": key,
                "display_name": seed.get("display_name"),
                "representation_kind": seed.get("representation_kind"),
                "chronology": seed.get("chronology"),
                "resolution": {"confidence": res.confidence, "score": res.score, "candidates": res.candidates},
            })
            print(f"[{i}/{len(seeds)}] unresolved {key}", flush=True)
        time.sleep(args.sleep)

    # Pull all resolved items in API batches. No claim values are retained in outputs.
    entities: dict[str, dict[str, Any]] = {}
    qids = sorted({qid_map[k] for k in seed_by_key if k in qid_map})
    for batch in batched(qids, 50):
        entities.update(get_entities(batch, "labels|claims", "en|fr"))
        print(f"fetched {len(batch)} items")
        time.sleep(args.sleep)

    records: list[dict[str, Any]] = []
    all_pids: set[str] = set()
    for key, qid in sorted(qid_map.items()):
        if key not in seed_by_key:
            continue
        e = entities.get(qid)
        if not e or e.get("missing"):
            unresolved.append({"seed_key": key, "display_name": seed_by_key[key].get("display_name"), "qid": qid, "reason": "missing_entity"})
            continue
        signature = first_level_signature(e)
        all_pids.update(signature)
        labels = e.get("labels") or {}
        records.append({
            "schema_version": "koa-wikidata-first-level-relations/v0.3.1",
            "seed_key": key,
            "seed_display_name": seed_by_key[key].get("display_name"),
            "qid": qid,
            "wikidata_label_en": labels.get("en", {}).get("value"),
            "wikidata_label_fr": labels.get("fr", {}).get("value"),
            "revision": e.get("lastrevid"),
            "modified": e.get("modified"),
            "resolution": resolution_meta.get(key, {"confidence": "qid_map"}),
            "relation_count": len(signature),
            "relations": signature,
            "source": {"provider": "Wikidata", "retrieved_at": utcnow()},
        })

    cat = property_catalog(sorted(all_pids), args.sleep)
    # Add relation class without looking at claim values.
    for pid, meta in cat.items():
        meta["relation_class"] = relation_class(meta.get("datatype"))

    # Aggregate coverage.
    coverage = Counter()
    statement_counts = Counter()
    for rec in records:
        for pid, sig in rec["relations"].items():
            coverage[pid] += 1
            statement_counts[pid] += int(sig.get("statement_count", 0))

    relation_rows = []
    denom = len(records) or 1
    for pid in sorted(all_pids, key=lambda p: (-coverage[p], int(p[1:]) if p[1:].isdigit() else 10**12)):
        m = cat.get(pid, {"property_id": pid, "label_en": None, "label_fr": None, "datatype": None})
        relation_rows.append({
            "property_id": pid,
            "label_en": m.get("label_en"),
            "label_fr": m.get("label_fr"),
            "datatype": m.get("datatype"),
            "relation_class": m.get("relation_class") or relation_class(m.get("datatype")),
            "people_with_relation": coverage[pid],
            "coverage_pct": round(100.0 * coverage[pid] / denom, 3),
            "total_statements": statement_counts[pid],
        })

    # JSONL signatures.
    with (outdir / "people.relation-signatures.jsonl").open("w", encoding="utf-8") as f:
        for rec in records:
            # enrich each relation with property metadata but still no values
            enriched = dict(rec)
            enriched["relations"] = {
                pid: {**sig, **{k: v for k, v in cat.get(pid, {}).items() if k != "property_id"}}
                for pid, sig in rec["relations"].items()
            }
            f.write(json.dumps(enriched, ensure_ascii=False, sort_keys=True) + "\n")

    # Dense boolean matrix. Good for clustering / heatmaps / coverage analysis.
    matrix_pids = sorted(all_pids, key=lambda p: int(p[1:]) if p[1:].isdigit() else 10**12)
    if args.semantic_matrix_only:
        matrix_pids = [p for p in matrix_pids if cat.get(p, {}).get("relation_class") == "semantic_relation"]
    matrix_fields = ["seed_key", "display_name", "qid"] + matrix_pids
    with (outdir / "people.relation-presence-matrix.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=matrix_fields)
        w.writeheader()
        for rec in records:
            row = {"seed_key": rec["seed_key"], "display_name": rec["seed_display_name"], "qid": rec["qid"]}
            present = set(rec["relations"])
            row.update({pid: 1 if pid in present else 0 for pid in matrix_pids})
            w.writerow(row)

    write_csv(
        outdir / "relations.catalog.csv",
        relation_rows,
        ["property_id", "label_en", "label_fr", "datatype", "relation_class", "people_with_relation", "coverage_pct", "total_statements"],
    )

    # Focus group coverage is a convenience summary, never a filter of the raw pull.
    focus_rows = []
    for group, pids in FOCUS_GROUPS.items():
        for pid in pids:
            m = cat.get(pid, {})
            focus_rows.append({
                "group": group,
                "property_id": pid,
                "label_en": m.get("label_en"),
                "label_fr": m.get("label_fr"),
                "people_with_relation": coverage.get(pid, 0),
                "coverage_pct": round(100.0 * coverage.get(pid, 0) / denom, 3),
            })
    write_csv(outdir / "focus-relations.coverage.csv", focus_rows, ["group", "property_id", "label_en", "label_fr", "people_with_relation", "coverage_pct"])

    Path(outdir / "qid-map.json").write_text(json.dumps(qid_map, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (outdir / "unresolved.jsonl").open("w", encoding="utf-8") as f:
        for x in unresolved:
            f.write(json.dumps(x, ensure_ascii=False, sort_keys=True) + "\n")

    manifest = {
        "schema_version": "koa-wikidata-relation-signature-run/v0.3.1",
        "generated_at": utcnow(),
        "registry_key": registry.get("registry_key"),
        "seed_count": len(seeds),
        "resolved_count": len(records),
        "unresolved_count": len(unresolved),
        "unique_first_level_properties": len(all_pids),
        "semantics": {
            "first_level": "Only top-level claim properties in entity.claims are recorded.",
            "values_stored": False,
            "qualifier_properties_stored": False,
            "reference_properties_stored": False,
            "statement_counts_stored": True,
            "property_datatypes_stored": True,
            "property_labels_stored": True,
        },
        "notes": [
            "The raw pull is intentionally property-presence oriented; no claim values are emitted.",
            "External identifiers are kept in the raw catalogue but classified separately from semantic relations.",
            "Focus groups are summaries only and never restrict ingestion.",
        ],
    }
    (outdir / "run-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"resolved": len(records), "unresolved": len(unresolved), "properties": len(all_pids)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
