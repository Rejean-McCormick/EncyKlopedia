#!/usr/bin/env python3
"""Inventaire UNESCO/SKOS en lecture seule, pour la préparation Kristalizer.

Ce programme n'écrit ni dans la source TTL, ni dans Wikidata, ni dans des Kristals.
Il préserve les URI officielles UNESCO et laisse les correspondances P3916 à
une phase ultérieure, alimentée par des déclarations Wikidata vérifiables.

Dépendance : python -m pip install rdflib>=7
Exemple : python unesco_inventory.py --ttl C:/.../unesco-thesaurus.ttl --out C:/.../UNESCO/INVENTAIRE
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import RDF, SKOS, DCTERMS

UNESCO = Namespace('http://vocabularies.unesco.org/ontology#')
ISO = Namespace('http://purl.org/iso25964/skos-thes#')
BASE = 'http://vocabularies.unesco.org/thesaurus/'
LANGS = ('fr', 'en', 'es', 'ru', 'ar')
RELATIONS = {
    'broader': SKOS.broader,
    'narrower': SKOS.narrower,
    'related': SKOS.related,
    'exactMatch': SKOS.exactMatch,
    'closeMatch': SKOS.closeMatch,
    'broadMatch': SKOS.broadMatch,
    'narrowMatch': SKOS.narrowMatch,
    'relatedMatch': SKOS.relatedMatch,
}


def uri_id(uri):
    return str(uri).removeprefix(BASE) if str(uri).startswith(BASE) else str(uri)


def rank(uri):
    id_ = uri_id(uri)
    m = re.fullmatch(r'([a-zA-Z]+)(\d+)', id_)
    return (m.group(1), int(m.group(2))) if m else (id_, -1)


def literals(g, subj, prop):
    """Retourne uniquement les vrais littéraux, regroupés par langue.

    Certains exports RDF placent une URI (URIRef) sous skos:definition ;
    une URI ne possède pas l'attribut .language et ne doit pas être
    confondue avec une définition rédigée. Les références sont conservées
    séparément par non_literal_values().
    """
    result = defaultdict(list)
    for value in g.objects(subj, prop):
        if not isinstance(value, Literal):
            continue
        lang = value.language or 'und'
        val = str(value)
        if val not in result[lang]:
            result[lang].append(val)
    return {key: sorted(vals) for key, vals in sorted(result.items())}


def non_literal_values(g, subj, prop):
    """Préserve les URI et noeuds RDF qui ne sont pas du texte."""
    result = []
    for value in g.objects(subj, prop):
        if isinstance(value, Literal):
            continue
        kind = 'URIRef' if isinstance(value, URIRef) else 'BNode' if isinstance(value, BNode) else type(value).__name__
        result.append({'kind': kind, 'value': str(value)})
    return sorted(result, key=lambda item: (item['kind'], item['value']))


def first_or_empty(items):
    return items[0] if items else ''


def scalar(g, subj, pred):
    return first_or_empty(sorted(str(obj) for obj in g.objects(subj, pred)))


def list_to_semicolon(items):
    return ';'.join(sorted(set(items)))


def save_csv(file, fieldnames, rows):
    with file.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description='Inventaire UNESCO RDF/SKOS, sans modification des données sources.')
    ap.add_argument('--ttl', type=Path, required=True, help='Téléchargement Turtle officiel UNESCO')
    ap.add_argument('--out', type=Path, required=True, help='Dossier de sortie, distinct des sources')
    args = ap.parse_args()
    inp, out = args.ttl.expanduser().resolve(), args.out.expanduser().resolve()
    if not inp.is_file():
        ap.error(f'Fichier introuvable : {inp}')
    if inp == out or inp.parent == out or inp.is_relative_to(out):
        ap.error('La sortie doit être distincte du fichier source et de son dossier.')
    out.mkdir(parents=True, exist_ok=True)

    print(f'Lecture RDF : {inp}', flush=True)
    graph = Graph()
    graph.parse(inp.as_posix(), format='turtle')
    concepts = sorted(set(graph.subjects(RDF.type, SKOS.Concept)), key=rank)
    domains = sorted(set(graph.subjects(RDF.type, UNESCO.Domain)), key=rank)
    micros = sorted(set(graph.subjects(RDF.type, UNESCO.MicroThesaurus)), key=rank)

    membership = defaultdict(set)
    micro_to_domain = defaultdict(set)
    for micro in micros:
        for concept in graph.objects(micro, SKOS.member):
            membership[concept].add(micro)
        for parent in graph.objects(micro, ISO.superGroup):
            micro_to_domain[micro].add(parent)
    for domain in domains:
        for micro in graph.objects(domain, ISO.subGroup):
            micro_to_domain[micro].add(domain)

    group_rows = []
    for kind, group_items in [('domain', domains), ('microthesaurus', micros)]:
        for group in group_items:
            ls = literals(graph, group, SKOS.prefLabel)
            parent_ids = sorted(uri_id(x) for x in micro_to_domain[group]) if kind == 'microthesaurus' else []
            group_rows.append({
                'type': kind,
                'id': uri_id(group), 'uri': str(group),
                'label_fr': first_or_empty(ls.get('fr', [])),
                'label_en': first_or_empty(ls.get('en', [])),
                'parent_domain_ids': list_to_semicolon(parent_ids),
                'members_count': len(set(graph.objects(group, SKOS.member))),
            })
    save_csv(out / 'groupes.csv',
             ['type', 'id', 'uri', 'label_fr', 'label_en', 'parent_domain_ids', 'members_count'],
             group_rows)

    relation_rows = []
    for concept in concepts:
        for rel, pred in RELATIONS.items():
            for dest in graph.objects(concept, pred):
                relation_rows.append({'source_id': uri_id(concept), 'relation': rel,
                                      'target_id_or_uri': uri_id(dest),
                                      'source_uri': str(concept), 'target_uri': str(dest)})
    relation_rows.sort(key=lambda r: (r['source_id'], r['relation'], r['target_id_or_uri']))
    save_csv(out / 'relations.csv',
             ['source_id', 'relation', 'target_id_or_uri', 'source_uri', 'target_uri'], relation_rows)

    concept_rows = []
    non_literal_counts = Counter()
    jsonl = out / 'concepts.jsonl'
    with jsonl.open('w', encoding='utf-8') as f:
        for concept in concepts:
            cid = uri_id(concept)
            prefs = literals(graph, concept, SKOS.prefLabel)
            alts = literals(graph, concept, SKOS.altLabel)
            micro_ids = sorted(uri_id(m) for m in membership[concept])
            domain_ids = sorted({uri_id(d) for m in membership[concept] for d in micro_to_domain[m]})
            non_literals = {}
            for name, prop in [('preferred_labels', SKOS.prefLabel),
                               ('alternate_labels', SKOS.altLabel),
                               ('scope_notes', SKOS.scopeNote),
                               ('definitions', SKOS.definition)]:
                refs = non_literal_values(graph, concept, prop)
                if refs:
                    non_literals[name] = refs
                    non_literal_counts[name] += len(refs)
            obj = {
                'source': 'UNESCO Thesaurus',
                'source_uri': str(concept),
                'unesco_id': cid,           # Wikidata P3916 : format concept123
                'wikidata_property': 'P3916',
                'wikidata_qid': None,       # Aucune correspondance inventée
                'preferred_labels': prefs,
                'alternate_labels': alts,
                'scope_notes': literals(graph, concept, SKOS.scopeNote),
                'definitions': literals(graph, concept, SKOS.definition),
                'non_literal_values': non_literals,
                'microthesaurus_ids': micro_ids,
                'domain_ids': domain_ids,
                'broader': sorted(uri_id(x) for x in graph.objects(concept, SKOS.broader)),
                'narrower': sorted(uri_id(x) for x in graph.objects(concept, SKOS.narrower)),
                'related': sorted(uri_id(x) for x in graph.objects(concept, SKOS.related)),
                'modified': scalar(graph, concept, DCTERMS.modified),
                'status': 'source_only_not_canonical',
            }
            f.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + '\n')
            concept_rows.append({
                'unesco_id': cid, 'uri': str(concept),
                'label_fr': first_or_empty(prefs.get('fr', [])),
                'label_en': first_or_empty(prefs.get('en', [])),
                'microthesaurus_ids': list_to_semicolon(micro_ids),
                'domain_ids': list_to_semicolon(domain_ids),
                'broader_ids': list_to_semicolon(obj['broader']),
                'related_ids': list_to_semicolon(obj['related']),
                'qid_p3916': '', 'status': obj['status'],
            })
    save_csv(out / 'concepts.csv',
             ['unesco_id', 'uri', 'label_fr', 'label_en', 'microthesaurus_ids',
              'domain_ids', 'broader_ids', 'related_ids', 'qid_p3916', 'status'], concept_rows)

    # RDF publication metadata (not an assertion about when we downloaded the file)
    scheme = URIRef('http://vocabularies.unesco.org/thesaurus')
    scheme_modification = scalar(graph, scheme, DCTERMS.modified)
    counts = Counter(r['relation'] for r in relation_rows)
    manifest = {
        'stage': 'UNESCO_inventory_only', 'canonical_promotion': False,
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_file': str(inp), 'source_size_bytes': inp.stat().st_size,
        'source_sha256': hashlib.sha256(inp.read_bytes()).hexdigest(),
        'source_concept_scheme_modified': scheme_modification,
        'triples': len(graph), 'concepts': len(concepts),
        'domains': len(domains), 'microthesauri': len(micros),
        'relationships_by_type': dict(sorted(counts.items())),
        'concepts_without_microthesaurus': len([c for c in concepts if not membership[c]]),
        'wikidata_mapping_status': 'not_started_requires_P3916_claim_source',
        'non_literal_values_by_property': dict(sorted(non_literal_counts.items())),
        'output_files': ['groupes.csv', 'concepts.csv', 'concepts.jsonl', 'relations.csv', 'manifest.json'],
    }
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('Inventaire terminé (aucune modification des sources).')
    for key in ['triples', 'domains', 'microthesauri', 'concepts', 'concepts_without_microthesaurus']:
        print(f'  {key}: {manifest[key]}')
    print(f'  sortie: {out}')


if __name__ == '__main__':
    main()
