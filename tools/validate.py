"""Offline design validation; synthetic reference evaluator, not a Kristal reader."""
import copy
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
def read(path):
    return json.loads((ROOT / path).read_text())

SCHEMAS = {p.stem.removesuffix('.schema'): json.loads(p.read_text())
           for p in (ROOT / 'contracts').glob('*.json')}
SCHEMA_REGISTRY = Registry()
for _schema in SCHEMAS.values():
    if _schema.get('$id'):
        SCHEMA_REGISTRY = SCHEMA_REGISTRY.with_resource(_schema['$id'], Resource.from_contents(_schema))
REGISTRY = read('examples/registry.json')
RELATIONS = {r['id']: r for r in REGISTRY['relations']}
TYPES = set(REGISTRY['entityTypes'])

def shape(kind, value):
    Draft202012Validator(SCHEMAS[kind], registry=SCHEMA_REGISTRY).validate(value)

def validate_query(q):
    shape('query-spec', q)
    if q['context']['registryRef'] != REGISTRY['registryRef']:
        raise ValueError('CONTEXT_UNAVAILABLE')
    totals = {'filters': 0, 'links': 0}
    def walk(s, depth=0):
        if depth > 3:
            raise ValueError('BUDGET_EXCEEDED: depth')
        if s['entityType'] not in TYPES:
            raise ValueError('TYPE_MISMATCH')
        totals['filters'] += len(s['filters'])
        totals['links'] += len(s['links'])
        for f in s['filters']:
            r = RELATIONS.get(f['relation'])
            if r is None:
                raise ValueError('UNKNOWN_RELATION')
            if s['entityType'] not in r['domain']:
                raise ValueError('TYPE_MISMATCH')
            if f['op'] not in r['operators']:
                raise ValueError('UNSUPPORTED_CAPABILITY')
            if any(v['kind'] != r['valueKind'] for v in f.get('values', [])):
                raise ValueError('TYPE_MISMATCH: value')
            if f['op'] == 'overlaps' and f['interval']['from'] > f['interval']['to']:
                raise ValueError('INVALID_QUERY: interval')
        for link in s['links']:
            r = RELATIONS.get(link['relation'])
            if r is None:
                raise ValueError('UNKNOWN_RELATION')
            if (r['valueKind'] != 'entity' or s['entityType'] not in r['domain']
                    or link['target']['entityType'] != r['range']):
                raise ValueError('TYPE_MISMATCH: link')
            walk(link['target'], depth + 1)
    walk(q['selection'])
    if totals['filters'] > 32 or totals['links'] > 16:
        raise ValueError('BUDGET_EXCEEDED: size')
    if len(json.dumps(q).encode()) > 65536:
        raise ValueError('BUDGET_EXCEEDED: bytes')


def evaluate(selection, entities, assertions):
    """Set semantics on complete tiny fixtures. Visibility is synthetic, not a Reader Policy implementation."""
    def values(eid, relation):
        inverse = RELATIONS[relation].get('inverseOf')
        out = []
        for a in assertions:
            if not a['visible']:
                continue
            if a['subject'] == eid and a['relation'] == relation:
                out.append(a['value'])
            elif inverse and a['relation'] == inverse and a['value'] == eid:
                out.append(a['subject'])
        return out
    def matches(eid, s):
        if entities[eid] != s['entityType'] or ('ids' in s and eid not in s['ids']):
            return False
        for f in s['filters']:
            vals = values(eid, f['relation'])
            op = f['op']
            wanted = [v.get('id', v.get('value')) for v in f.get('values', [])]
            if op == 'exists': ok = bool(vals)
            elif op == 'missing_in_view': ok = not vals
            elif op == 'in': ok = any(v in wanted for v in vals)
            elif op == 'none_of': ok = not any(v in wanted for v in vals)
            elif op == 'overlaps':
                # Exact fixture intervals only; uncertain temporal normalization belongs to the real adapter.
                ok = any(v[0] is not None and v[1] is not None and
                         v[0] <= f['interval']['to'] and v[1] >= f['interval']['from'] for v in vals)
            else: raise ValueError(op)
            if not ok: return False
        for link in s['links']:
            if not any(v in entities and matches(v, link['target']) for v in values(eid, link['relation'])):
                return False
        return True
    return sorted(eid for eid in entities if matches(eid, selection))


def main():
    checks = 0
    for s in SCHEMAS.values():
        Draft202012Validator.check_schema(s)
        checks += 1
    shape('relation-registry', REGISTRY)
    assert len(RELATIONS) == len(REGISTRY['relations'])
    for r in RELATIONS.values():
        assert set(r['domain']) <= TYPES
        if r['valueKind'] == 'entity': assert r['range'] in TYPES
        if 'inverseOf' in r:
            inverse = RELATIONS[r['inverseOf']]
            assert inverse.get('inverseOf') == r['id']
            assert inverse['range'] in r['domain'] and r['range'] in inverse['domain']
    checks += 1
    for p in (ROOT / 'examples/lenses').glob('*.json'):
        lens = json.loads(p.read_text()); shape('lens', lens)
        assert lens['rootType'] in TYPES
        for f in lens['facets']:
            r = RELATIONS[f['relation']]
            assert lens['rootType'] in r['domain']
            if f['widget'] == 'year-range': assert r['valueKind'] == 'interval'
            if f['widget'] == 'entity-picker': assert r['valueKind'] == 'entity'
        for rel in lens['pivots']:
            assert lens['rootType'] in RELATIONS[rel]['domain']
            assert RELATIONS[rel]['valueKind'] == 'entity'
        checks += 1
    for p in (ROOT / 'examples/queries').glob('*.json'):
        validate_query(json.loads(p.read_text())); checks += 1
    shape('exploration-state', read('examples/exploration.json')); checks += 1

    # Navigation Projection 1.0: every controlled family has a positive fixture,
    # and the public DTO rejects renderer/recipe mismatches and raw upstream metadata.
    projection_requirements = {
        'timeline-lineage': 'items', 'tree': 'roots', 'dag': 'acyclic', 'flow': 'transitions',
        'causal-feedback': 'cycles', 'matrix': 'cells', 'state-flow': 'semantics',
        'traceability': 'edges', 'multiscale': 'memberships', 'spatial': 'points',
    }
    projection_fixtures = {}
    for kind, required in projection_requirements.items():
        fixture = read(f'examples/projections/{kind}.json')
        assert fixture['projectionKind'] == kind
        shape('navigation-projection', fixture); checks += 1
        projection_fixtures[kind] = fixture
        bad_projection = copy.deepcopy(fixture); bad_projection.pop(required)
        try: shape('navigation-projection', bad_projection)
        except __import__('jsonschema').ValidationError: checks += 1
        else: raise AssertionError(f'Projection {kind} accepted without {required}')

    bad_projection = copy.deepcopy(projection_fixtures['dag']); bad_projection['rendererId'] = 'spatial'
    try: shape('navigation-projection', bad_projection)
    except __import__('jsonschema').ValidationError: checks += 1
    else: raise AssertionError('DAG accepted with spatial renderer')

    bad_projection = copy.deepcopy(projection_fixtures['tree']); bad_projection['recipeId'] = 'proofs'
    try: shape('navigation-projection', bad_projection)
    except __import__('jsonschema').ValidationError: checks += 1
    else: raise AssertionError('Tree accepted with proof recipe')

    bad_projection = copy.deepcopy(projection_fixtures['state-flow'])
    bad_projection['records'][0]['actionability']['policy_refs'] = ['secret:policy']
    try: shape('navigation-projection', bad_projection)
    except __import__('jsonschema').ValidationError: checks += 1
    else: raise AssertionError('Projection exposed raw actionability policy refs')

    bad_projection = copy.deepcopy(projection_fixtures['timeline-lineage'])
    bad_projection['links'][0]['value']['source_artifacts'] = ['secret:artifact']
    try: shape('navigation-projection', bad_projection)
    except __import__('jsonschema').ValidationError: checks += 1
    else: raise AssertionError('Projection exposed raw lineage artifact refs')

    bad_projection = copy.deepcopy(projection_fixtures['flow']); bad_projection['raw'] = {'secret': True}
    try: shape('navigation-projection', bad_projection)
    except __import__('jsonschema').ValidationError: checks += 1
    else: raise AssertionError('Projection accepted unknown top-level payload')

    result = read('examples/result.json'); shape('result-set', result)
    evidence = {a['assertionRef'] for a in result['assertions']}
    for row in result['rows']:
        for w in row['witnesses']:
            assert set(w['assertionRefs']) <= evidence
            if w['kind'] == 'derivation': assert 'ruleRef' in w
    checks += 1
    people = read('examples/queries/people.json')
    bad = []
    def mutation(fn):
        q = copy.deepcopy(people); fn(q); bad.append(q)
    mutation(lambda q: q['selection']['filters'][0].update(op='not_equals'))
    mutation(lambda q: q['selection']['filters'][0].update(relation='unknown'))
    mutation(lambda q: q['selection']['filters'][0].update(relation='author'))
    mutation(lambda q: q['selection']['filters'][1]['interval'].update(to=200))
    mutation(lambda q: q.update(pageSize=101))
    mutation(lambda q: q.update(hiddenFilter=True))
    mutation(lambda q: q['selection']['filters'][0].update(values=[]))
    mutation(lambda q: q['selection']['filters'][0].update(values=[{'kind':'integer','value':2}]))
    mutation(lambda q: q['context'].pop('readerPolicyRef'))
    mutation(lambda q: q['selection']['filters'][0].update(op='exists'))  # unexpected values forbidden
    q = copy.deepcopy(people)
    for i in range(4):
        typ = 'work' if q['selection']['entityType'] == 'human' else 'human'
        rel = 'author' if typ == 'work' else 'authored_work'
        q['selection'] = {'entityType':typ,'filters':[], 'links':[{'relation':rel,'target':q['selection']}]}
    bad.append(q)
    for q in bad:
        try: validate_query(q)
        except (ValueError, __import__('jsonschema').ValidationError): checks += 1
        else: raise AssertionError('Invalid query accepted')

    entities = {}; assertions = []
    def add(subject, relation, value, visible=True):
        assertions.append({'subject':subject,'relation':relation,'value':value,'visible':visible})
    for i in range(120):
        person = f'fixture:p{i:03}'; work = f'fixture:w{i:03}'
        entities[person] = 'human'; entities[work] = 'work'
        add(person, 'field_of_work', 'fixture:philosophy'); add(person, 'lifespan', [350,430])
        add(work, 'author', person)
    all_people = evaluate(people['selection'], entities, assertions)
    all_works = evaluate(read('examples/queries/works.json')['selection'], entities, assertions)
    assert len(all_people) == 120 and len(all_people[:people['pageSize']]) == 50
    assert len(all_works) == 120 and 'fixture:w119' in all_works; checks += 2
    add('fixture:w000', 'author', 'fixture:p001')
    assert len(evaluate(read('examples/queries/works.json')['selection'], entities, assertions)) == 120; checks += 1
    s = {'entityType':'human','filters':[{'relation':'movement','op':'none_of','values':[{'kind':'entity','id':'fixture:X'}]}],'links':[]}
    add('fixture:p000','movement','fixture:X'); add('fixture:p000','movement','fixture:Y')
    add('fixture:p001','movement','fixture:X',False)
    got = evaluate(s,entities,assertions)
    assert 'fixture:p000' not in got and 'fixture:p001' in got; checks += 1
    s['filters'] = [{'relation':'movement','op':'missing_in_view'}]
    assert 'fixture:p001' in evaluate(s,entities,assertions); checks += 1
    add('fixture:p000','movement','fixture:Y')
    s['filters'] = [{'relation':'movement','op':'in','values':[{'kind':'entity','id':'fixture:Y'}]}]
    assert evaluate(s,entities,assertions) == ['fixture:p000']; checks += 1
    entities['fixture:unknown_end'] = 'human'; add('fixture:unknown_end','field_of_work','fixture:philosophy'); add('fixture:unknown_end','lifespan',[350,None])
    assert 'fixture:unknown_end' not in evaluate(people['selection'],entities,assertions); checks += 1
    # Correlation: one author satisfies the field, a different one satisfies the time. Neither satisfies both.
    entities.update({'fixture:split_work':'work','fixture:left':'human','fixture:right':'human'})
    add('fixture:left','field_of_work','fixture:philosophy'); add('fixture:left','lifespan',[900,950])
    add('fixture:right','field_of_work','fixture:other'); add('fixture:right','lifespan',[350,430])
    add('fixture:split_work','author','fixture:left'); add('fixture:split_work','author','fixture:right')
    assert 'fixture:split_work' not in evaluate(read('examples/queries/works.json')['selection'],entities,assertions); checks += 1
    print(f'PASS — {checks} checks; schemas/examples, semantic rejection and synthetic set/pivot tests.')
    print('Not verified: real Kristal Reader Policies, backend/projection, cursor/cache/ACL, SA, UI, performance.')

if __name__ == '__main__':
    main()
