import { test } from 'node:test';
import assert from 'node:assert/strict';
import { Engine } from '../server/engine.mjs';
import { loadPack, hash, validatePack } from '../server/pack.mjs';
import { validate } from '../server/contracts.mjs';
const fixture = () => structuredClone(loadPack());
const base = (
  engine,
  selection = { entityType: 'human', filters: [], links: [] },
  pageSize = 50,
) => ({
  schemaVersion: '0.2',
  context: engine.context(),
  selection,
  order: 'entity_id_asc',
  pageSize,
});
const term = (id) => ({ kind: 'entity', id });
const only = (e, filters = [], ids) =>
  base(e, { entityType: 'human', filters, links: [], ...(ids ? { ids } : {}) });

test('stable context, result schema and reproducible order', () => {
  const a = new Engine(fixture()),
    b = new Engine(fixture());
  const q = base(a);
  assert.deepEqual(a.context(), b.context());
  const x = a.query(q);
  validate('result-set', x);
  assert.deepEqual(x.rows, b.query(q).rows);
  assert.equal(x.total.value, 132);
  assert.equal(x.rows.length, 50);
});
test('pivot evaluates the complete selection, not its page', () => {
  const e = new Engine(fixture());
  const q = base(e);
  assert.equal(e.query(q).rows.length, 50);
  const works = base(e, {
    entityType: 'work',
    filters: [],
    links: [{ relation: 'author', target: q.selection }],
  });
  assert.equal(e.query(works).total.value, 133);
});
test('all criteria must belong to the same related author', () => {
  const p = fixture();
  p.entities.push({ id: 'test:work', type: 'work', label: 'Split witnesses' });
  const a = p.assertions.find((a) => a.relation === 'author');
  p.assertions.push(
    { ...a, id: 'test:a1', subject: 'test:work', value: 'demo:p000' },
    { ...a, id: 'test:a2', subject: 'test:work', value: 'demo:p003' },
  );
  const e = new Engine(p);
  const q = base(e, {
    entityType: 'work',
    ids: ['test:work'],
    filters: [],
    links: [
      {
        relation: 'author',
        target: {
          entityType: 'human',
          filters: [
            { relation: 'movement', op: 'in', values: [term('demo:platonism')] },
            {
              relation: 'lifespan',
              op: 'overlaps',
              interval: { from: 1200, to: 1300, calendar: 'proleptic-gregorian-astronomical' },
              match: 'definite',
            },
          ],
          links: [],
        },
      },
    ],
  });
  assert.equal(e.query(q).total.value, 0);
});
test('policy applies before joins, facets, entity inspection and evidence', () => {
  const e = new Engine(fixture());
  const hidden = e.pack.assertions.find((a) => a.status === 'disputed');
  const q = only(e, [{ relation: 'movement', op: 'in', values: [term('demo:stoic')] }]);
  assert.equal(e.query(q).total.value, 1);
  assert(!e.entity('demo:p000', q.context).assertions.some((a) => a.assertionRef === hidden.id));
  assert.throws(() => e.evidence([hidden.id], q.context), { code: 'NOT_FOUND' });
  const f = e.facets(q, ['movement']);
  assert.equal(f.movement.values.find((v) => v.value === 'demo:stoic').count, 1);
  q.context.readerPolicyRef = [...e.policies.keys()][1];
  assert.equal(e.query(q).total.value, 2);
  assert(e.entity('demo:p000', q.context).assertions.some((a) => a.assertionRef === hidden.id));
});
test('conflict pointers do not reveal assertions excluded by policy', () => {
  const e = new Engine(fixture());
  const d = e.entity('demo:p000', e.context());
  assert(d.assertions.every((a) => a.payload.conflictsWith.length === 0));
  const all = e.entity('demo:p000', e.context([...e.policies.keys()][1]));
  assert(all.assertions.some((a) => a.payload.conflictsWith.length === 1));
});
test('none_of excludes a multivalued entity even when another value differs', () => {
  const e = new Engine(fixture());
  const q = only(
    e,
    [{ relation: 'field_of_work', op: 'none_of', values: [term('demo:philosophy')] }],
    ['demo:p000'],
  );
  assert.equal(e.query(q).total.value, 0);
});
test('missing is absence in the visible view; unknown interval is not infinite', () => {
  const e = new Engine(fixture());
  assert.equal(
    e.query(only(e, [{ relation: 'movement', op: 'missing_in_view' }], ['demo:p006'])).total.value,
    1,
  );
  const q = only(
    e,
    [
      {
        relation: 'lifespan',
        op: 'overlaps',
        interval: { from: 200, to: 400, calendar: 'proleptic-gregorian-astronomical' },
        match: 'definite',
      },
    ],
    ['demo:s000'],
  );
  assert.equal(e.query(q).total.value, 0);
});
test('facets remove their own filters, preserving other restrictions', () => {
  const e = new Engine(fixture());
  const q = only(
    e,
    [{ relation: 'field_of_work', op: 'in', values: [term('demo:philosophy')] }],
    ['demo:p000'],
  );
  const f = e.facets(q, ['field_of_work']);
  assert.equal(f.field_of_work.values.find((v) => v.value === 'demo:theology').count, 1);
  assert.equal(f.field_of_work.present, 1);
});
test('deduplication across multiple matching assertions', () => {
  const p = fixture();
  const a = p.assertions.find((a) => a.relation === 'field_of_work');
  p.assertions.push({ ...a, id: 'test:duplicate' });
  const e = new Engine(p);
  const q = only(
    e,
    [{ relation: 'field_of_work', op: 'in', values: [term('demo:philosophy')] }],
    [a.subject],
  );
  assert.equal(e.query(q).total.value, 1);
  assert.equal(
    e.facets(q, ['field_of_work']).field_of_work.values.find((v) => v.value === 'demo:philosophy')
      .count,
    1,
  );
});
test('pagination has no duplicates and cursor binds query, policy, size and access', () => {
  const e = new Engine(fixture(), { secret: 'test-secret' }),
    q = base(e);
  const first = e.query(q),
    second = e.query(q, first.nextCursor);
  assert.equal(new Set([...first.rows, ...second.rows].map((r) => r.entityId)).size, 100);
  assert.throws(() => e.query({ ...q, pageSize: 20 }, first.nextCursor), {
    code: 'CURSOR_MISMATCH',
  });
  const altered = structuredClone(q);
  altered.context.readerPolicyRef = [...e.policies.keys()][1];
  assert.throws(() => e.query(altered, first.nextCursor), { code: 'CURSOR_MISMATCH' });
  assert.throws(() => e.query(q, first.nextCursor + 'x'), { code: 'CURSOR_MISMATCH' });
  const other = new Engine(fixture(), { roles: ['public', 'admin'], secret: 'test-secret' });
  assert.throws(() => other.query(q, first.nextCursor), { code: 'CURSOR_MISMATCH' });
});
test('expired context is rejected rather than remapped', () => {
  const e = new Engine(fixture());
  const q = base(e);
  q.context.datasetRef = 'fixture:old';
  assert.throws(() => e.query(q), { code: 'CONTEXT_UNAVAILABLE' });
});
test('ACL applies to catalogue, assertion targets, facets, evidence, and sources', () => {
  const p = fixture();
  p.entities.find((x) => x.id === 'demo:p000').roles = ['admin'];
  const hidden = p.assertions.find((a) => a.subject === 'demo:p000');
  const e = new Engine(p);
  assert(!e.bootstrap([]).entities.some((x) => x.id === 'demo:p000'));
  assert.throws(() => e.entity('demo:p000', e.context()), { code: 'NOT_FOUND' });
  assert.throws(() => e.evidence([hidden.id], e.context()), { code: 'NOT_FOUND' });
  assert.equal(e.query(base(e)).total.value, 131);
  const w = base(e, {
    entityType: 'work',
    filters: [],
    links: [{ relation: 'author', target: { entityType: 'human', filters: [], links: [] } }],
  });
  assert.equal(e.query(w).total.value, 131);
});
test('unsupported operators, domain mismatch, malformed dates and excessive depth fail closed', () => {
  const e = new Engine(fixture());
  const bad = [];
  let q = base(e);
  q.selection.filters = [{ relation: 'author', op: 'exists' }];
  bad.push(q);
  q = base(e);
  q.selection.filters = [{ relation: 'movement', op: 'bogus' }];
  bad.push(q);
  q = base(e);
  q.selection.filters = [
    {
      relation: 'lifespan',
      op: 'overlaps',
      interval: { from: 500, to: 300, calendar: 'proleptic-gregorian-astronomical' },
      match: 'definite',
    },
  ];
  bad.push(q);
  q = base(e);
  q.selection.filters = [{ relation: 'not_known', op: 'exists' }];
  bad.push(q);
  q = base(e);
  for (let i = 0; i < 4; i++) {
    const type = q.selection.entityType === 'human' ? 'work' : 'human';
    q.selection = {
      entityType: type,
      filters: [],
      links: [{ relation: type === 'work' ? 'author' : 'authored_work', target: q.selection }],
    };
  }
  bad.push(q);
  for (const b of bad) assert.throws(() => e.query(b));
});
test('operation caps produce an error, never partial results or false absence', () => {
  const e = new Engine(fixture(), { maxOperations: 10 });
  assert.throws(() => e.query(base(e)), { code: 'BUDGET_EXCEEDED' });
  assert.throws(() => e.facets(base(e), ['movement']), { code: 'BUDGET_EXCEEDED' });
});
test('pack semantic integrity rejects duplicate IDs and unknown targets', () => {
  const p = fixture();
  p.entities.push(p.entities[0]);
  assert.throws(() => validatePack(p), { code: 'INVALID_PACK' });
  const x = fixture();
  x.assertions[0].value = 'unknown:id';
  assert.throws(() => validatePack(x), { code: 'INVALID_PACK' });
});
test('witnesses preserve statement identity, sources and derived rule', () => {
  const e = new Engine(fixture());
  const q = only(
    e,
    [
      {
        relation: 'lifespan',
        op: 'overlaps',
        interval: { from: 300, to: 500, calendar: 'proleptic-gregorian-astronomical' },
        match: 'definite',
      },
    ],
    ['demo:p000'],
  );
  const result = e.query(q);
  assert.equal(result.rows[0].witnesses[0].kind, 'derivation');
  assert.equal(result.rows[0].witnesses[0].ruleRef, 'demo:interval-v1');
  assert(result.assertions[0].payload.sourceRefs.length);
});

test('Reader Policy cannot leak hidden-only entities through query, bootstrap or entity endpoint', () => {
  const pack = fixture();
  const human = pack.entities.find((entity) => entity.type === 'human');
  const concept = pack.entities.find((entity) => entity.type === 'concept');
  const sourceRef = pack.assertions.find((a) => a.sourceRefs?.length)?.sourceRefs?.[0];
  const template = pack.assertions.find((a) => a.subject === human.id && a.relation === 'field_of_work') || pack.assertions[0];
  const hiddenId = 'human:policy-hidden-only';
  pack.entities.push({ ...human, id: hiddenId, label: 'Hidden by documented policy' });
  pack.assertions.push({
    ...template,
    id: 'assertion:policy-hidden-only',
    subject: hiddenId,
    relation: 'field_of_work',
    value: concept.id,
    status: 'disputed',
    sourceRefs: sourceRef ? [sourceRef] : template.sourceRefs,
  });
  const engine = new Engine(pack);
  const documented = [...engine.policies].find(([, policy]) => policy.id === 'demo:documented')?.[0];
  const research = [...engine.policies].find(([, policy]) => policy.id === 'demo:research')?.[0];
  const documentedContext = engine.context(documented);
  const researchContext = engine.context(research);
  const targeted = (context) => ({
    ...base(engine, { entityType: 'human', ids: [hiddenId], filters: [], links: [] }, 1),
    context,
  });
  // Hidden identifiers fail closed just like unavailable identities; the
  // permissive research policy can resolve the same identity explicitly.
  assert.throws(() => engine.query(targeted(documentedContext)), { code: 'TYPE_MISMATCH' });
  assert(!engine.bootstrap([], documentedContext).entities.some((entity) => entity.id === hiddenId));
  assert.throws(() => engine.entity(hiddenId, documentedContext), /Entité indisponible/);
  assert.equal(engine.query(targeted(researchContext)).rows[0]?.entityId, hiddenId);
  assert(engine.bootstrap([], researchContext).entities.some((entity) => entity.id === hiddenId));
});
