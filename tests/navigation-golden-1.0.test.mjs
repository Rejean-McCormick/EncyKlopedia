import { test } from 'node:test';
import assert from 'node:assert/strict';
import { StructuralProfiler } from '../server/navigation/profiler.mjs';
import { buildNavigationPlan } from '../server/navigation/planner.mjs';

const ops = ['exists', 'missing_in_view', 'in', 'none_of'];
const relation = (id, label, valueKind = 'entity') => ({
  id,
  label: { fr: label, en: label },
  domain: ['node'],
  range: valueKind === 'entity' ? 'node' : 'value',
  valueKind,
  operators: ops,
});
const pack = (relations, edges = [], navigationHints = undefined) => ({
  registry: { entityTypes: ['node'], relations },
  entities: [
    { id: 'a', type: 'node', label: 'A' },
    { id: 'b', type: 'node', label: 'B' },
    { id: 'c', type: 'node', label: 'C' },
  ],
  sources: [],
  assertions: edges.map(([id, subject, relationId, value, extra = {}]) => ({
    id, subject, relation: relationId, value, sourceRefs: [], ...extra,
  })),
  ...(navigationHints ? { navigationHints } : {}),
});
function planFor(input) {
  const profiler = new StructuralProfiler(input);
  return buildNavigationPlan({ profiler, query: { selection: { entityType: 'node' } }, lens: null });
}
const ids = (plan) => new Set(plan.views.map((view) => view.id));

const cases = [
  {
    name: 'Math-like',
    input: pack([
      relation('math:proof_dependency', 'proof dependency'),
      relation('math:proves', 'proves'),
      relation('math:pedagogical_prerequisite', 'pedagogical prerequisite'),
    ]),
    positive: ['proofs', 'dependencies', 'path'],
    negative: ['timeline', 'spatial', 'feedback'],
  },
  {
    name: 'HumanBody-like',
    input: pack([
      relation('humanbody:increases', 'increases'),
      relation('humanbody:decreases', 'decreases'),
      relation('humanbody:source_scale', 'source scale', 'integer'),
      relation('humanbody:target_scale', 'target scale', 'integer'),
    ], [
      ['h1', 'a', 'humanbody:increases', 'b'],
      ['h2', 'b', 'humanbody:decreases', 'a'],
    ]),
    positive: ['feedback', 'multiscale'],
    negative: ['proofs', 'timeline', 'spatial'],
  },
  {
    name: 'HistoryTech-like',
    input: pack([
      relation('historytech:historical_occurrence', 'historical occurrence'),
      relation('historytech:chronology', 'chronology', 'integer'),
      relation('historytech:derived_from', 'derived from'),
    ]),
    positive: ['timeline', 'evolution', 'dependencies'],
    negative: ['proofs', 'feedback', 'spatial'],
  },
  {
    name: 'ScolQc-like',
    input: pack([
      relation('education-quebec:may_transition_to', 'may transition to'),
      relation('education-quebec:has_particular_admission_requirements', 'admission requirements'),
    ]),
    positive: ['path'],
    negative: ['proofs', 'timeline', 'feedback'],
  },
  {
    name: 'HospitalOps-like',
    input: pack([
      relation('hospitalops:workflow_template', 'workflow template', 'string'),
      relation('hospitalops:resource_capability_template', 'resource capability template', 'string'),
    ]),
    positive: ['path'],
    negative: ['proofs', 'timeline', 'feedback'],
  },
  {
    name: 'Power-like',
    input: pack([
      relation('power:has_metric', 'has metric', 'integer'),
      relation('power:dimension_value', 'dimension value', 'integer'),
      relation('power:part_of', 'part of'),
    ]),
    positive: ['dimensions'],
    negative: ['proofs', 'timeline', 'feedback'],
  },
  {
    name: 'Catho-like',
    input: pack([
      relation('catho:supports_position', 'supports position'),
      relation('catho:opposes_position', 'opposes position'),
      relation('catho:conflicts_with', 'conflicts with'),
    ], [
      ['c1', 'a', 'catho:supports_position', 'b', { sourceRefs: ['source:1'], provenanceRefs: ['prov:1'] }],
      ['c2', 'b', 'catho:conflicts_with', 'c', { conflictsWith: ['c1'] }],
    ]),
    positive: ['arguments', 'divergences', 'traceability'],
    negative: ['proofs', 'timeline', 'feedback', 'spatial'],
  },
  {
    name: 'Generic-minimal',
    input: pack([
      relation('generic:related_to', 'related to'),
    ], [
      ['g1', 'a', 'generic:related_to', 'b'],
    ]),
    positive: ['catalogue', 'constellation', 'table'],
    negative: ['proofs', 'timeline', 'feedback', 'path', 'dimensions', 'spatial'],
  },
];

for (const fixture of cases) {
  test(`golden navigation: ${fixture.name} has expected positive and negative affordances`, () => {
    const viewIds = ids(planFor(fixture.input));
    for (const recipe of fixture.positive) assert.ok(viewIds.has(recipe), `${fixture.name}: expected ${recipe}`);
    for (const recipe of fixture.negative) assert.ok(!viewIds.has(recipe), `${fixture.name}: did not expect ${recipe}`);
  });
}

test('1.0 hints can strengthen a reusable affordance without introducing renderer code', () => {
  const input = pack([
    relation('custom:occurs_at', 'occurs at', 'integer'),
  ], [], {
    schemaVersion: '1.0',
    affordances: { temporal: { score: 1, reason: 'canonical chronology projection available' } },
    preferredRecipes: ['timeline'],
    recipeLabels: { timeline: 'Trajectoire' },
  });
  const plan = planFor(input);
  const timeline = plan.views.find((view) => view.id === 'timeline');
  assert.ok(timeline);
  assert.equal(timeline.rendererId, 'timeline-lineage');
  assert.equal(timeline.label, 'Trajectoire');
  assert.equal(plan.derived, true);
  assert.equal(plan.semantics, 'navigation-affordances-not-kristal-authority');
});

test('policy-scoped profiler never exposes presentation hints to the planner', () => {
  const input = pack([
    relation('secret:occurred_at', 'occurred at', 'interval'),
  ], [
    ['s1', 'a', 'secret:occurred_at', { startMin: 2026, startMax: 2026, endMin: 2026, endMax: 2026, calendar: 'proleptic-gregorian-astronomical' }],
  ], {
    schemaVersion: '1.0',
    affordances: { temporal: { score: 1, reason: 'SECRET declared reason' } },
    preferredRecipes: ['timeline'],
    recipeLabels: { timeline: 'SECRET timeline label' },
  });
  const profiler = new StructuralProfiler(input, { policyScoped: true });
  assert.deepEqual(profiler.hintsFor('node'), {});
  const plan = buildNavigationPlan({ profiler, query: { selection: { entityType: 'node' } }, lens: null });
  assert.ok(plan.views.some((view) => view.id === 'timeline'));
  assert.ok(!JSON.stringify(plan).includes('SECRET timeline label'));
  assert.ok(!JSON.stringify(plan).includes('SECRET declared reason'));
});
