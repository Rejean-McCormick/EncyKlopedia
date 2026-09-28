#!/usr/bin/env python3
"""Expand selected Wikidata relations from a first-level signature pull.

Level semantics are deliberately alternating:
  level 1 = root objects (the curated people/QIDs)
  level 2 = relation markers on root objects
  level 3 = values/target objects reached through selected relation markers
  level 4 = relation markers on level-3 objects
  level 5 = values/target objects reached from level-3 objects
  ...

At relation-marker levels, ALL top-level properties are recorded as signatures, but
only the user-selected property IDs are followed to the next object/value level.
Selected relation values are stored in this phase by design; phase-1 remains
property-presence-only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# Import the already-tested network/entity helpers from phase 1.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import pull_wikidata_relation_signatures as base  # noqa: E402


def selected_claim_values(entity: dict[str, Any], pid: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for st in (entity.get("claims") or {}).get(pid, []):
        snak = st.get("mainsnak") or {}
        row: dict[str, Any] = {
            "snaktype": snak.get("snaktype"),
            "datatype": snak.get("datatype"),
            "rank": st.get("rank", "normal"),
        }
        if snak.get("snaktype") != "value":
            row["value_kind"] = snak.get("snaktype", "unknown")
            out.append(row)
            continue
        dv = snak.get("datavalue") or {}
        value = dv.get("value")
        dtype = dv.get("type")
        row["value_kind"] = dtype
        if isinstance(value, dict) and "id" in value:
            row["target_qid"] = value.get("id")
        else:
            # Explicit phase-2 selection authorizes value retrieval. Preserve JSON value.
            row["value"] = value
        out.append(row)
    return out


def load_roots(qid_map_path: Path, limit: int = 0) -> list[tuple[str, str]]:
    qmap = json.loads(qid_map_path.read_text(encoding="utf-8"))
    items = sorted((str(k), str(v)) for k, v in qmap.items())
    return items[:limit] if limit else items


def hydrate_labels(qids: set[str], sleep: float) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for batch in base.batched(sorted(qids), 50):
        ents = base.get_entities(batch, "labels|descriptions", "en|fr")
        for qid, e in ents.items():
            labels = e.get("labels") or {}
            descriptions = e.get("descriptions") or {}
            out[qid] = {
                "qid": qid,
                "label_en": labels.get("en", {}).get("value"),
                "label_fr": labels.get("fr", {}).get("value"),
                "description_en": descriptions.get("en", {}).get("value"),
                "description_fr": descriptions.get("fr", {}).get("value"),
            }
        time.sleep(sleep)
    return out


def read_phase1_statement_upper_bound(sig_path: Path, pids: set[str]) -> tuple[int, int]:
    roots = 0
    statements = 0
    if not sig_path.exists():
        return 0, 0
    with sig_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            roots += 1
            rels = rec.get("relations") or {}
            for pid in pids:
                statements += int((rels.get(pid) or {}).get("statement_count", 0))
    return roots, statements


def estimate(qid_map_path: Path, signatures_path: Path, pids: set[str], levels: int, sleep: float, sample_roots: int) -> dict[str, Any]:
    roots = load_roots(qid_map_path)
    nroots, exact_first_edges = read_phase1_statement_upper_bound(signatures_path, pids)
    roots_count = nroots or len(roots)
    sample = roots[: min(sample_roots, len(roots))]
    if not sample:
        return {"roots": 0, "selected_properties": sorted(pids), "levels": levels}

    # Sample first selected-value layer to estimate duplicate rate and recursive branching.
    sample_entities: dict[str, dict[str, Any]] = {}
    for batch in base.batched([qid for _, qid in sample], 50):
        sample_entities.update(base.get_entities(batch, "claims"))
        time.sleep(sleep)

    sample_edges = 0
    sample_targets: set[str] = set()
    for _, qid in sample:
        e = sample_entities.get(qid, {})
        for pid in pids:
            vals = selected_claim_values(e, pid)
            sample_edges += len(vals)
            sample_targets.update(v["target_qid"] for v in vals if v.get("target_qid"))

    edge_per_root = sample_edges / max(1, len(sample))
    target_per_edge = len(sample_targets) / max(1, sample_edges)
    estimated_first_edges = exact_first_edges if exact_first_edges else round(edge_per_root * roots_count)
    estimated_first_unique_targets = round(estimated_first_edges * target_per_edge)

    layers: list[dict[str, Any]] = [
        {"level": 1, "kind": "object", "estimated_count": roots_count, "basis": "qid-map/phase1"},
        {"level": 2, "kind": "relation_marker", "selected_properties": len(pids), "estimated_selected_statements": estimated_first_edges, "basis": "phase1 statement_count" if exact_first_edges else "sample"},
    ]
    if levels >= 3:
        layers.append({"level": 3, "kind": "object_or_value", "estimated_unique_item_targets": estimated_first_unique_targets, "estimated_edges": estimated_first_edges, "basis": f"sample {len(sample)} roots"})

    # Estimate deeper selected-relation branching from a capped sample of first-hop item targets.
    current_estimated_objects = estimated_first_unique_targets
    current_sample_targets = sorted(sample_targets)[: min(30, len(sample_targets))]
    next_edge_per_object = None
    next_target_per_edge = None
    if levels >= 4 and current_sample_targets:
        target_entities: dict[str, dict[str, Any]] = {}
        for batch in base.batched(current_sample_targets, 50):
            target_entities.update(base.get_entities(batch, "claims"))
            time.sleep(sleep)
        marker_counts = [len(base.first_level_signature(target_entities.get(q, {}))) for q in current_sample_targets]
        avg_markers = sum(marker_counts) / max(1, len(marker_counts))
        layers.append({"level": 4, "kind": "relation_marker", "estimated_total_markers": round(current_estimated_objects * avg_markers), "avg_markers_per_object": round(avg_markers, 2), "basis": f"sample {len(current_sample_targets)} target objects"})

        selected_edges = 0
        selected_targets: set[str] = set()
        for q in current_sample_targets:
            e = target_entities.get(q, {})
            for pid in pids:
                vals = selected_claim_values(e, pid)
                selected_edges += len(vals)
                selected_targets.update(v["target_qid"] for v in vals if v.get("target_qid"))
        next_edge_per_object = selected_edges / max(1, len(current_sample_targets))
        next_target_per_edge = len(selected_targets) / max(1, selected_edges)

    level = 5
    while level <= levels:
        if level % 2 == 1:  # object/value layer
            if next_edge_per_object is None:
                est_edges = 0
                est_objs = 0
            else:
                est_edges = round(current_estimated_objects * next_edge_per_object)
                est_objs = round(est_edges * (next_target_per_edge or 0.0))
            current_estimated_objects = est_objs
            layers.append({"level": level, "kind": "object_or_value", "estimated_unique_item_targets": est_objs, "estimated_edges": est_edges, "basis": "recursive sample branching"})
        else:
            # We cannot know full marker cardinality without sampling each new layer. Reuse level-4 average as a coarse estimate.
            avg = layers[3].get("avg_markers_per_object", 0) if len(layers) > 3 else 0
            layers.append({"level": level, "kind": "relation_marker", "estimated_total_markers": round(current_estimated_objects * avg), "avg_markers_per_object": avg, "basis": "level-4 sampled marker density"})
        level += 1

    # Very rough on-disk estimate: edges ~180 B; node/signature marker rows ~110 B per marker.
    edge_total = sum(int(x.get("estimated_edges", 0)) for x in layers)
    marker_total = sum(int(x.get("estimated_total_markers", 0)) for x in layers)
    disk_bytes = edge_total * 180 + marker_total * 110 + roots_count * 220
    return {
        "roots": roots_count,
        "selected_properties": sorted(pids),
        "levels": levels,
        "sample_roots": len(sample),
        "exact_first_selected_statements": exact_first_edges,
        "layers": layers,
        "rough_output_bytes": disk_bytes,
        "rough_output_mib": round(disk_bytes / (1024 * 1024), 2),
        "warning": "Estimate only. Wikidata branching and duplicate targets can vary strongly by property and historical period.",
    }


def run_expansion(qid_map_path: Path, pids: set[str], levels: int, outdir: Path, sleep: float, limit: int) -> dict[str, Any]:
    outdir.mkdir(parents=True, exist_ok=True)
    roots = load_roots(qid_map_path, limit)

    nodes: dict[str, dict[str, Any]] = {qid: {"qid": qid, "root_seed_keys": [key], "first_seen_level": 1} for key, qid in roots}
    for key, qid in roots:
        nodes.setdefault(qid, {"qid": qid, "root_seed_keys": [], "first_seen_level": 1})
        if key not in nodes[qid].setdefault("root_seed_keys", []):
            nodes[qid]["root_seed_keys"].append(key)

    edges: list[dict[str, Any]] = []
    signatures_by_level: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
    frontier = {qid for _, qid in roots}
    seen_object_levels: dict[str, int] = {qid: 1 for qid in frontier}

    # level 2 markers and onward. Each odd level fetches values from selected markers; each even level records signatures.
    relation_level = 2
    while relation_level <= levels and frontier:
        entities: dict[str, dict[str, Any]] = {}
        for batch in base.batched(sorted(frontier), 50):
            entities.update(base.get_entities(batch, "labels|claims", "en|fr"))
            print(f"level {relation_level}: fetched {len(batch)} objects")
            time.sleep(sleep)

        # Record all relation markers on these objects.
        for qid in sorted(frontier):
            e = entities.get(qid, {})
            sig = base.first_level_signature(e)
            signatures_by_level[relation_level].append({
                "level": relation_level,
                "qid": qid,
                "relation_count": len(sig),
                "relations": sig,
            })

        if relation_level + 1 > levels:
            break

        next_frontier: set[str] = set()
        value_level = relation_level + 1
        for qid in sorted(frontier):
            e = entities.get(qid, {})
            for pid in sorted(pids):
                for idx, val in enumerate(selected_claim_values(e, pid)):
                    edge = {
                        "source_qid": qid,
                        "property_id": pid,
                        "relation_level": relation_level,
                        "value_level": value_level,
                        "statement_index": idx,
                        **val,
                    }
                    edges.append(edge)
                    tq = val.get("target_qid")
                    if tq:
                        next_frontier.add(tq)
                        if tq not in seen_object_levels:
                            seen_object_levels[tq] = value_level
                            nodes[tq] = {"qid": tq, "root_seed_keys": [], "first_seen_level": value_level}
        frontier = next_frontier
        relation_level += 2

    # Labels are useful for the graph map; they are metadata for explicitly selected targets.
    labels = hydrate_labels(set(nodes), sleep)
    for qid, meta in nodes.items():
        meta.update(labels.get(qid, {}))

    with (outdir / "graph.nodes.jsonl").open("w", encoding="utf-8") as f:
        for qid in sorted(nodes):
            f.write(json.dumps(nodes[qid], ensure_ascii=False, sort_keys=True) + "\n")
    with (outdir / "graph.edges.jsonl").open("w", encoding="utf-8") as f:
        for edge in edges:
            f.write(json.dumps(edge, ensure_ascii=False, sort_keys=True) + "\n")
    with (outdir / "node.relation-signatures.jsonl").open("w", encoding="utf-8") as f:
        for level in sorted(signatures_by_level):
            for rec in signatures_by_level[level]:
                f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")

    manifest = {
        "schema_version": "koa-wikidata-selected-relation-expansion/v0.3.1",
        "generated_at": base.utcnow(),
        "levels": levels,
        "level_semantics": "1 object, 2 relation marker, 3 object/value, 4 relation marker, ...",
        "selected_properties": sorted(pids),
        "root_count": len(roots),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "values_stored": True,
        "note": "Only explicitly selected properties are followed. All property markers are recorded on visited item objects.",
    }
    (outdir / "expansion-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--qid-map", required=True)
    ap.add_argument("--signatures", default=None, help="phase-1 people.relation-signatures.jsonl; used for better estimates")
    ap.add_argument("--property", action="append", dest="properties", default=[])
    ap.add_argument("--properties-file", default=None, help="JSON list or object with selected_properties")
    ap.add_argument("--levels", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--sleep", type=float, default=0.75)
    ap.add_argument("--contact", default=base.DEFAULT_CONTACT, help="email ou URL de contact pour le User-Agent Wikimedia")
    ap.add_argument("--max-retries", type=int, default=8)
    ap.add_argument("--backoff-base", type=float, default=2.0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--estimate-only", action="store_true")
    ap.add_argument("--sample-roots", type=int, default=12)
    args = ap.parse_args()
    base.configure_http(contact=args.contact, max_retries=args.max_retries, backoff_base=args.backoff_base)

    pids = set(args.properties)
    if args.properties_file:
        obj = json.loads(Path(args.properties_file).read_text(encoding="utf-8"))
        if isinstance(obj, list):
            pids.update(map(str, obj))
        elif isinstance(obj, dict):
            pids.update(map(str, obj.get("selected_properties") or []))
    pids = {p for p in pids if p.startswith("P") and p[1:].isdigit()}
    if not pids:
        raise SystemExit("No selected Wikidata properties. Use --property Pxxx or --properties-file.")
    if args.levels < 2:
        raise SystemExit("--levels must be >= 2. Level 1=object, level 2=relation marker.")

    qid_map = Path(args.qid_map)
    outdir = Path(args.out)
    if args.estimate_only:
        signatures = Path(args.signatures) if args.signatures else outdir.parent / "people.relation-signatures.jsonl"
        info = estimate(qid_map, signatures, pids, args.levels, args.sleep, args.sample_roots)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return

    result = run_expansion(qid_map, pids, args.levels, outdir, args.sleep, args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
