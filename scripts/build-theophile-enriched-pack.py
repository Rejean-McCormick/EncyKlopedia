#!/usr/bin/env python3
"""Build a standalone Konstellation pack from the enriched Théophile semantic corpus.

The script merges the local Biblical Graph pack with Théophile. It preserves sourced
claims and explicitly marks navigation projections as editorial/claimed.
"""
import argparse, collections, copy, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def infer_type(eid: str) -> str:
    prefixes = [
        ('urn:theophile:author:', 'author'),
        ('urn:theophile:position:', 'position'),
        ('urn:theophile:theme:', 'theme'),
        ('urn:theophile:editorial:question:', 'editorial'),
        ('urn:theophile:argument:', 'argument'),
        ('urn:theophile:doctrine:', 'doctrine'),
        ('doctrine:', 'doctrinal-status'),
    ]
    for prefix, kind in prefixes:
        if eid.startswith(prefix):
            return kind
    raise ValueError(f'Unknown Théophile entity type: {eid}')


def normalize_label(value: str) -> str:
    import unicodedata, re
    value = unicodedata.normalize('NFD', str(value or ''))
    value = ''.join(ch for ch in value if unicodedata.category(ch) != 'Mn').lower()
    return re.sub(r'[^a-z0-9]+', ' ', value).strip()


JOSEPH_DISAMBIGUATION_FR = {
    'Joseph_1': 'fils de Jacob et Rachel',
    'Joseph_2': 'père d’Igal',
    'Joseph_3': 'fils d’Asaph',
    'Joseph_4': 'descendant de Bani',
    'Joseph_5': 'fils de Shebaniah',
    'Joseph_6': 'époux de Marie · Mt 1,16',
    'Joseph_7': 'Joses · frère de Jésus',
    'Joseph_8': 'd’Arimathie',
    'Joseph_9': 'généalogie de Jésus · Lc 3,24',
    'Joseph_10': 'généalogie de Jésus · Lc 3,30',
    'Joseph_11': 'Barsabbas / Justus',
    'Joseph_12': 'Barnabé',
}

MARY_DISAMBIGUATION_FR = {
    'Mary_1': 'mère de Jésus',
    'Mary_2': 'Marie Madeleine',
    'Mary_3': 'sœur de Marthe',
    'Mary_4': 'de Clopas',
    'Mary_5': 'mère de Jean Marc',
    'Mary_6': 'de Rome · Rm 16,6',
}

def person_disambiguation(entity):
    key = entity.get('bibleDataId')
    if key in JOSEPH_DISAMBIGUATION_FR:
        return JOSEPH_DISAMBIGUATION_FR[key]
    if key in MARY_DISAMBIGUATION_FR:
        return MARY_DISAMBIGUATION_FR[key]
    aliases = []
    base = normalize_label(entity.get('label'))
    for alias in entity.get('aliases', []):
        if not isinstance(alias, str):
            continue
        cleaned = alias.strip()
        norm = normalize_label(cleaned)
        if not norm or norm == base or any(ord(ch) > 127 for ch in cleaned):
            continue
        if cleaned.lower() in {'son of david', 'king herod'}:
            continue
        aliases.append(cleaned)
    if aliases:
        # Named alternatives such as Barsabbas, Barnabas, Peter or Mark are the
        # most useful short disambiguators in a result list.
        aliases = sorted(set(aliases), key=lambda a: (len(a), a.lower()))
        return aliases[0][:120]
    description = (entity.get('description') or '').strip()
    return description[:160] if description else entity.get('bibleDataId', '')


def annotate_duplicate_people(entities):
    groups = collections.defaultdict(list)
    for entity in entities.values():
        if entity.get('type') == 'person':
            groups[normalize_label(entity.get('label'))].append(entity)
    for group in groups.values():
        if len(group) < 2:
            continue
        for entity in group:
            disambiguation = person_disambiguation(entity)
            if disambiguation:
                entity['disambiguation'] = disambiguation

def item_ref(value):
    if not isinstance(value, dict):
        return None
    return value.get('external_id') or value.get('id')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--semantic', default=str(ROOT / 'data/theophile.semantic.enriched.json'))
    ap.add_argument('--base', default=str(ROOT / 'data/biblical.pack.local.json'))
    ap.add_argument('--output', default=str(ROOT / 'data/theophile-biblical.enriched.pack.json'))
    args = ap.parse_args()

    sem = json.loads(Path(args.semantic).read_text(encoding='utf-8'))
    base = json.loads(Path(args.base).read_text(encoding='utf-8'))

    entities = {e['id']: copy.deepcopy(e) for e in base['entities']}

    def add_entity(ref):
        if not isinstance(ref, dict):
            return
        eid = item_ref(ref)
        if not eid or eid.startswith('urn:theophile:source:'):
            return
        try:
            etype = infer_type(eid)
        except ValueError:
            return
        label = ref.get('label') or eid
        entities.setdefault(eid, {'id': eid, 'type': etype, 'label': label, 'description': ''})

    # Subjects, objects and qualifier items become graph entities when they belong to
    # the Théophile entity namespace. This ensures all 99 themes are navigable.
    for a in sem['assertions']:
        st = a['statement']
        add_entity(st.get('subject'))
        if st.get('object', {}).get('kind') == 'item':
            add_entity(st['object'].get('value'))
        for q in st.get('qualifiers', []):
            if q.get('object', {}).get('kind') == 'item':
                add_entity(q['object'].get('value'))

    for a in sem['assertions']:
        st = a['statement']
        sid = item_ref(st.get('subject'))
        oid = item_ref(st.get('object', {}).get('value')) if st.get('object', {}).get('kind') == 'item' else None
        if sid in entities and st.get('predicate', {}).get('external_id') == 'corpus:reconstruction_argumentative':
            entities[sid]['description'] = a.get('natural_language_statement', {}).get('text', '')[:1200]
        if oid in entities and oid and oid.startswith('urn:theophile:argument:'):
            entities[oid]['description'] = a.get('natural_language_statement', {}).get('text', '')[:1200]
        if oid in entities and oid and oid.startswith('urn:theophile:position:'):
            entities[oid]['description'] = a.get('notes', '')[:1200]

    rel_examples = collections.defaultdict(list)
    for a in sem['assertions']:
        st = a['statement']
        if st.get('object', {}).get('kind') != 'item':
            continue
        sid, oid = item_ref(st['subject']), item_ref(st['object']['value'])
        rid = st['predicate'].get('external_id') or st['predicate'].get('id')
        rel_examples[rid].append((infer_type(sid), infer_type(oid), st['predicate'].get('label') or rid))

    relations = {r['id']: copy.deepcopy(r) for r in base['registry']['relations']}
    for rid, rows in sorted(rel_examples.items()):
        domains = sorted({x[0] for x in rows})
        ranges = sorted({x[1] for x in rows})
        if len(ranges) != 1:
            raise ValueError(f'{rid}: multiple entity ranges {ranges}')
        label = rows[0][2]
        relations[rid] = {
            'id': rid,
            'label': {'fr': label, 'en': label},
            'domain': domains,
            'range': ranges[0],
            'valueKind': 'entity',
            'operators': ['exists', 'missing_in_view', 'in', 'none_of'],
        }

    sources = {s['id']: copy.deepcopy(s) for s in base['sources']}
    for s in sem['source_refs']:
        sid = s['source_id']
        sources[sid] = {
            'id': sid,
            'title': s.get('title') or sid,
            'description': ('Source Théophile · ' + (s.get('publisher') or '')).strip(' ·'),
            **({'url': s['source_url']} if s.get('source_url') else {}),
        }

    assertions = {a['id']: copy.deepcopy(a) for a in base['assertions']}
    for a in sem['assertions']:
        st = a['statement']
        if st.get('object', {}).get('kind') != 'item':
            raise ValueError(f"Unsupported non-entity assertion {a.get('source_assertion_id')}")
        refs = []
        for e in a.get('evidence_refs', []):
            sr = e.get('source_ref', {}).get('source_id')
            if sr and sr not in refs:
                refs.append(sr)
        assertions[a['assertion_id']] = {
            'id': a['assertion_id'],
            'subject': item_ref(st['subject']),
            'relation': st['predicate']['external_id'],
            'value': item_ref(st['object']['value']),
            'status': a['assertion_status'],
            'certainty': a['certainty_level'],
            'validationStatus': a.get('validation', {}).get('validation_status', 'not_evaluated'),
            'validatedAs': a.get('validated_as', 'not_evaluated'),
            'authority': 'authority:theophile-editorial',
            'scope': a['scope'],
            'sourceRefs': refs,
            'qualifiers': st.get('qualifiers', []),
            'notes': a.get('notes', ''),
            **({'naturalLanguageStatement': a['natural_language_statement']} if a.get('natural_language_statement') else {}),
            'sourceAssertionId': a.get('source_assertion_id', ''),
        }

    pack = copy.deepcopy(base)
    pack['title'] = 'Corpus catholique Théophile v0.2.1 · Graphe biblique enrichi'
    pack['description'] = 'Corpus Théophile enrichi de liens question–position–thème–auteur, combiné au graphe biblique complet et à ses personnages, œuvres, rôles et relations.'
    pack['synthetic'] = False
    for etype in ['author', 'position', 'theme', 'editorial', 'argument', 'doctrine', 'doctrinal-status']:
        if etype not in pack['registry']['entityTypes']:
            pack['registry']['entityTypes'].append(etype)
    pack['registry']['entityTypes'] = sorted(pack['registry']['entityTypes'])
    pack['registry']['registryRef'] = 'konstellation:theophile-biblical-enriched-v1'
    pack['registry']['relations'] = sorted(relations.values(), key=lambda r: r['id'])
    annotate_duplicate_people(entities)
    pack['entities'] = sorted(entities.values(), key=lambda e: e['id'])
    pack['sources'] = sorted(sources.values(), key=lambda s: s['id'])
    pack['assertions'] = sorted(assertions.values(), key=lambda a: a['id'])

    for policy in pack['policies']:
        if 'authority:theophile-editorial' not in policy['authorities']:
            policy['authorities'].append('authority:theophile-editorial')

    authorities = sorted({'authority:theophile-editorial', *(a for p in pack['policies'] for a in p['authorities'])})
    exploration = {
        'id': 'theophile:exploration',
        'label': 'Exploration documentée + liens éditoriaux',
        'description': 'Affiche les positions sourcées et les relations éditoriales dérivées en conservant leurs statuts distincts.',
        'profile': 'konstellation.normalized-reader.v1',
        'showLabels': True,
        'statuses': ['sourced', 'reviewed', 'validated', 'hypothesis', 'claimed', 'disputed'],
        'certainties': ['*'],
        'validationStatuses': ['*'],
        'validatedAs': ['*'],
        'authorities': authorities,
        'requireSources': True,
    }
    pack['policies'] = [exploration] + [p for p in pack['policies'] if p['id'] != exploration['id']]

    Path(args.output).write_text(json.dumps(pack, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    counts = collections.Counter(e['type'] for e in pack['entities'] if e['id'].startswith('urn:theophile:') or e['id'].startswith('doctrine:'))
    print(f"Pack écrit: {args.output}")
    print(f"Entités: {len(pack['entities'])} · assertions: {len(pack['assertions'])} · relations: {len(pack['registry']['relations'])} · sources: {len(pack['sources'])}")
    print('Théophile:', dict(sorted(counts.items())))

if __name__ == '__main__':
    main()
