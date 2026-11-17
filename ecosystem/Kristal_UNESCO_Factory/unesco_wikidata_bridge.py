#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jointure UNESCO (inventaire) <-> Wikidata P3916 (export CSV).

Lecture seule: inventaire UNESCO, export WDQS et index EncyK. Ecrit uniquement
ses propres fichiers dans un dossier de sortie distinct des entrees.

Ne promeut ni correspondances canoniques ni assertions Kristal.
Aucune requete reseau: l'export CSV est telecharge separement et fige.

Exemple:
    python unesco_wikidata_bridge.py --inventory .../INVENTAIRE \
      --claims .../wikidata-p3916.csv --index D:/EncyKlopedia/.../wikidata.compact.sqlite \
      --out .../JOINTURE_P3916
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

CID = re.compile(r'^concept[1-9]\d*$')
QID = re.compile(r'^Q[1-9]\d*$')
KNOWN_ENDPOINT = 'https://query.wikidata.org/sparql'
SPARQL = 'SELECT ?item ?unescoId WHERE { ?item <http://www.wikidata.org/prop/direct/P3916> ?unescoId . }'


def hash_file(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def write_csv(path, rows, keys):
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def parse_qid(value):
    raw = str(value or '').strip()
    if QID.fullmatch(raw): return raw
    u = urlparse(raw)
    if (u.scheme in ('http', 'https') and u.hostname == 'www.wikidata.org'
            and (u.path.startswith('/entity/') or u.path.startswith('/wiki/'))):
        qid = unquote(u.path.rsplit('/', 1)[-1])
        return qid if QID.fullmatch(qid) else None
    return None


def parse_cid(value):
    raw = str(value or '').strip()
    return raw if CID.fullmatch(raw) else None


def read_inventory(folder):
    manifest_path = folder / 'manifest.json'
    p = folder / 'concepts.csv'
    if not (p.is_file() and manifest_path.is_file()):
        raise ValueError('Inventaire UNESCO incomplet: concepts.csv ou manifest.json absent.')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    if manifest.get('stage') != 'UNESCO_inventory_only':
        raise ValueError('Manifest UNESCO inattendu; pas un inventaire officiel en lecture seule.')
    concepts = {}
    with p.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        required = {'unesco_id', 'uri', 'label_fr', 'label_en'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError('Colonnes obligatoires absentes de concepts.csv.')
        for row in reader:
            cid = str(row.get('unesco_id', '')).strip()
            if not CID.fullmatch(cid):
                raise ValueError('Identifiant UNESCO incorrect dans concepts.csv: ' + repr(cid))
            if cid in concepts: raise ValueError('Identifiant UNESCO en double: ' + cid)
            concepts[cid] = row
    if len(concepts) != manifest.get('concepts'):
        raise ValueError(f"Inventaire incoherent: {len(concepts)} concepts contre {manifest.get('concepts')} dans le manifeste.")
    return manifest, concepts, p


def read_claims(path):
    values = defaultdict(set)
    invalid = []
    total = 0
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        item_field = next((x for x in ('item', 'qid', 'wikidata_qid') if x in fields), None)
        id_field = next((x for x in ('unescoId', 'unesco_id', 'unescoID') if x in fields), None)
        if item_field is None or id_field is None:
            raise ValueError('Colonnes export P3916 non reconnues. Attendu: item,unescoId.')
        for row in reader:
            total += 1
            qid = parse_qid(row.get(item_field))
            cid = parse_cid(row.get(id_field))
            if not qid or not cid:
                invalid.append({'row': total + 1, 'item': row.get(item_field, ''),
                                'unescoId': row.get(id_field, ''), 'reason': 'malformed_qid_or_unesco_id'})
                continue
            values[cid].add(qid)
    if total == 0:
        raise ValueError('Export P3916 vide. Refus de conclure a zero correspondances.')
    if not values:
        raise ValueError('Aucune correspondance P3916 valide dans cet export.')
    return values, invalid, total


def open_index(index):
    """Le schéma EncyK canonique contient entity, mais pas de valeur texte P3916."""
    if index is None: return None
    if not index.is_file(): raise ValueError('Index SQLite introuvable: ' + str(index))
    con = sqlite3.connect(index.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        con.row_factory = sqlite3.Row
        cols = {r['name'] for r in con.execute('PRAGMA table_info(entity)')}
        expected = {'id', 'wid', 'label_fr', 'label_en'}
        if not expected.issubset(cols):
            raise ValueError('Schema index EncyK inattendu: table entity / colonnes absentes.')
        return con
    except Exception:
        con.close()
        raise


def local_entity(con, qid):
    if con is None:
        return 'NOT_CHECKED', '', ''
    n = int(qid[1:])  # Index EncyK: les entites Q ont id = entier de QID
    r = con.execute('SELECT wid,label_fr,label_en FROM entity WHERE id=?', (n,)).fetchone()
    if not r or r['wid'] != qid: return 'NOT_IN_LOCAL_INDEX', '', ''
    return 'FOUND_IN_LOCAL_INDEX', r['label_fr'] or '', r['label_en'] or ''


def ensure_output(out, inputs):
    out = out.resolve()
    for src in inputs:
        if src and (out == src.resolve() or out.is_relative_to(src.resolve())):
            raise ValueError('La sortie ne peut pas se trouver dans une entree: ' + str(src))
    out.mkdir(parents=True, exist_ok=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Jointure non destructive UNESCO-Wikidata par P3916.')
    ap.add_argument('--inventory', type=Path, required=True, help='Dossier inventaire UNESCO, contenant concepts.csv et manifest.json')
    ap.add_argument('--claims', type=Path, required=True, help='Export CSV SELECT ?item ?unescoId depuis WDQS')
    ap.add_argument('--index', type=Path, help='Index local EncyK facultatif, en lecture seule')
    ap.add_argument('--out', type=Path, required=True, help='Dossier de sortie, DISTINCT des sources')
    args = ap.parse_args(argv)
    inv, claims, out, idx = args.inventory.expanduser(), args.claims.expanduser(), args.out.expanduser(), args.index.expanduser() if args.index else None
    if not claims.is_file(): ap.error('Export P3916 introuvable: ' + str(claims))
    if not inv.is_dir(): ap.error('Inventaire UNESCO introuvable: ' + str(inv))
    try:
        ensure_output(out, [inv, claims, idx])
        manifest, concepts, concepts_path = read_inventory(inv)
        pairs, invalid, total = read_claims(claims)
        con = open_index(idx)
        try:
            reverse = defaultdict(set)
            for cid, qids in pairs.items():
                for qid in qids: reverse[qid].add(cid)
            statuses = Counter()
            claims_sha256 = hash_file(claims)
            rows = []
            for cid, c in sorted(concepts.items(), key=lambda item: int(item[0][7:])):
                qids = sorted(pairs.get(cid, set()), key=lambda x: int(x[1:]))
                multi_qids = any(len(reverse[qid]) > 1 for qid in qids)
                if not qids:
                    status, selected = 'NO_P3916_MAPPING', ''
                elif len(qids) != 1 or multi_qids:
                    status, selected = 'REVIEW_AMBIGUOUS_P3916', ''
                else:
                    status, selected = 'SINGLE_P3916_CANDIDATE', qids[0]
                check, fr, en = local_entity(con, selected) if selected else ('NOT_CHECKED', '', '')
                row = {
                    'unesco_id': cid,
                    'unesco_uri': c['uri'],
                    'label_fr': c['label_fr'], 'label_en': c['label_en'],
                    'wikidata_qid_candidate': selected,
                    'all_p3916_qids': ';'.join(qids),
                    'status': status,
                    'local_index_status': check,
                    'local_label_fr': fr, 'local_label_en': en,
                    'source_property': 'P3916',
                    'evidence_url': ('https://www.wikidata.org/wiki/' + selected) if selected else '',
                    'canonical_promotion': 'false',
                }
                rows.append(row); statuses[status] += 1
            extras = []
            for cid, qids in sorted(pairs.items(), key=lambda item: int(item[0][7:])):
                if cid not in concepts:
                    for qid in sorted(qids): extras.append({'unesco_id':cid, 'wikidata_qid':qid, 'reason':'P3916_NOT_IN_THIS_UNESCO_VERSION'})
            conflicts = [r for r in rows if r['status'] == 'REVIEW_AMBIGUOUS_P3916']
            write_csv(out / 'crosswalk_candidates.csv', rows, list(rows[0]))
            write_csv(out / 'review_ambiguous.csv', conflicts, list(rows[0]))
            write_csv(out / 'wikidata_ids_outside_unesco.csv', extras, ['unesco_id','wikidata_qid','reason'])
            write_csv(out / 'invalid_p3916_rows.csv', invalid, ['row','item','unescoId','reason'])
            with (out / 'kristal_candidates.jsonl').open('w', encoding='utf-8') as f:
                for row in rows:
                    if row['status'] != 'SINGLE_P3916_CANDIDATE': continue
                    info = {
                        'unesco_id': row['unesco_id'], 'unesco_uri': row['unesco_uri'],
                        'wikidata_qid_candidate': row['wikidata_qid_candidate'],
                        'link_status': row['status'], 'wikidata_property': 'P3916',
                        'p3916_export_sha256': claims_sha256,
                        'local_index_status': row['local_index_status'],
                        'status': 'source_candidate_not_canonical',
                    }
                    f.write(json.dumps(info, ensure_ascii=False, sort_keys=True) + '\n')
            report = {
                'stage': 'UNESCO_Wikidata_P3916_candidates',
                'canonical_promotion': False,
                'generated_at_utc': datetime.now(timezone.utc).isoformat(),
                'input_unesco_manifest_sha256': hash_file(inv / 'manifest.json'),
                'input_unesco_concepts_sha256': hash_file(concepts_path),
                'input_p3916_csv_sha256': claims_sha256,
                'wikidata_source': 'WDQS / P3916 direct statements',
                'wikidata_export_query': SPARQL,
                'wdqs_endpoint': KNOWN_ENDPOINT,
                'input_index_path': str(idx.resolve()) if idx else None,
                'index_role': 'labels_and_presence_only_not_P3916_proof',
                'unesco_concepts_total': len(concepts),
                'p3916_export_rows_total': total,
                'p3916_valid_pair_count': sum(len(qids) for qids in pairs.values()),
                'p3916_invalid_rows': len(invalid),
                'p3916_identifiers_not_in_unesco': len({x['unesco_id'] for x in extras}),
                'status_counts': dict(sorted(statuses.items())),
                'matched_local_index_count': sum(r['local_index_status'] == 'FOUND_IN_LOCAL_INDEX' for r in rows),
                'outputs': ['crosswalk_candidates.csv','review_ambiguous.csv','wikidata_ids_outside_unesco.csv',
                            'invalid_p3916_rows.csv','kristal_candidates.jsonl','manifest_p3916.json'],
            }
            (out / 'manifest_p3916.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            print('Jointure non destructive terminee.')
            for key in ('unesco_concepts_total', 'p3916_export_rows_total', 'p3916_identifiers_not_in_unesco', 'p3916_invalid_rows', 'matched_local_index_count'):
                print(f'  {key}: {report[key]}')
            for key, n in sorted(statuses.items()): print(f'  {key}: {n}')
            print('  sortie:', out)
        finally:
            if con is not None: con.close()
    except (ValueError, sqlite3.Error, OSError, UnicodeError, csv.Error) as exc:
        print('ERREUR:', exc, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
