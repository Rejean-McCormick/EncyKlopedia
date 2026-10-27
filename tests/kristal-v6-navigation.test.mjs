import test from 'node:test';
import assert from 'node:assert/strict';
import { StructuralProfiler } from '../server/navigation/profiler.mjs';
import { buildNavigationPlan, rendererCatalog } from '../server/navigation/planner.mjs';

function pack(overrides = {}) {
  return {
    schemaVersion: '0.3',
    title: 'v6 synthetic',
    description: 'synthetic',
    synthetic: true,
    registry: {
      schemaVersion: '0.2',
      registryRef: 'test',
      entityTypes: ['item'],
      relations: [
        {
          id: 'rel:link:entity',
          label: { fr: 'Lien', en: 'Link' },
          domain: ['item'],
          range: 'item',
          valueKind: 'entity',
          operators: ['exists'],
        },
      ],
    },
    entities: [{ id: 'item:a', type: 'item', label: 'A' }, { id: 'item:b', type: 'item', label: 'B' }],
    assertions: [{ id: 'assertion:a', subject: 'item:a', relation: 'rel:link:entity', value: 'item:b', sourceRefs: [] }],
    sources: [],
    policies: [],
    integration: {
      metadata: {
        structuralSummary: {
          assertionCount: 42,
          recordRoles: { observed_state: 8, decision: 3, action: 2, structural_record: 4 },
          actionabilityModes: { human_review: 5, manual: 2 },
          coordinateAxes: { effective_date: 7, scale: 9, location: 3 },
          valuationSemantics: { scalar: 10, probability: 2, temporal: 4, state: 6 },
          valuationDimensions: { risk: 10, health_state: 6, confidence: 2 },
          conflicts: 4,
          supersedes: 3,
          lineage: 5,
          evidenceRefs: 15,
          provenanceRefs: 9,
        },
        provenanceCount: 3,
      },
    },
    ...overrides,
  };
}

test('Kristal v6 structural metadata becomes navigation affordances', () => {
  const profiler = new StructuralProfiler(pack());
  const c = profiler.global.affordances;
  for (const id of ['temporal','quantitative','multidimensional','stateful','actionability','conflict','succession','lineage','evidential','provenance']) {
    assert.ok(c[id].score >= 0.35, `${id} should be detected; got ${c[id].score}`);
  }
  assert.ok(c.multiScale.score >= 0.3);
  assert.ok(c.spatial.score >= 0.3);
});

test('planner exposes v6-aware generic recipes without domain branches', () => {
  const p = pack({
    navigationHints: {
      schemaVersion: '0.1',
      capabilities: { actionability: 1 },
      preferredRecipes: ['action-context'],
    },
  });
  const profiler = new StructuralProfiler(p);
  const plan = buildNavigationPlan({
    profiler,
    query: {
      selection: { entityType: 'item' },
    },
    lens: null,
  });
  assert.equal(plan.schemaVersion, '1.0');
  assert.equal(plan.semantics, 'navigation-affordances-not-kristal-authority');
  assert.ok(plan.views.some((view) => view.id === 'action-context'));
  assert.ok(plan.profile.affordances.actionability.score >= 1);
});

test('renderer catalog includes lineage, conflict, traceability and state recipes', () => {
  const catalog = rendererCatalog();
  const recipes = new Set(catalog.flatMap((item) => item.supportedRecipes));
  for (const id of ['states','evolution','divergences','traceability','action-context']) assert.ok(recipes.has(id));
  const renderers = new Set(catalog.map((item) => item.id));
  for (const id of ['state-flow','timeline-lineage','traceability']) assert.ok(renderers.has(id));
});
