import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { StructuralProfiler } from '../server/navigation/profiler.mjs';
import { buildNavigationPlan } from '../server/navigation/planner.mjs';

function demoPack() {
  return JSON.parse(fs.readFileSync(new URL('../data/demo.pack.json', import.meta.url), 'utf8'));
}

test('structural profiler detects temporal, network and provenance affordances without a domain preset', () => {
  const profiler = new StructuralProfiler(demoPack());
  const profile = profiler.forType('human');
  assert(profile.affordances.temporal.score >= 0.8);
  assert(profile.affordances.network.score >= 0.5);
  assert(profile.affordances.provenance.score >= 0.5);
  assert.deepEqual(profiler.relationsFor('temporal', 'human').map((r) => r.id), ['lifespan']);
});

test('navigation planner keeps stable generic views while adding structural opportunities', () => {
  const profiler = new StructuralProfiler(demoPack());
  const plan = buildNavigationPlan({
    profiler,
    query: { selection: { entityType: 'human' } },
    lens: { id: 'intellectual-history', label: { fr: 'Histoire intellectuelle' } },
  });
  const ids = plan.views.map((view) => view.id);
  assert(ids.includes('timeline'));
  assert(ids.includes('catalogue'));
  assert(ids.includes('table'));
  assert(ids.includes('constellation'));
  assert.equal(plan.primaryRecipeId, 'timeline');
});

test('new structural families produce reusable recipes rather than domain-specific UIs', () => {
  const pack = demoPack();
  pack.registry.entityTypes.push('step', 'proof');
  pack.registry.relations.push(
    {
      id: 'depends_on', label: { fr: 'Dépend de', en: 'depends on' }, domain: ['proof'], range: 'proof',
      valueKind: 'entity', operators: ['exists', 'missing_in_view', 'in', 'none_of'],
    },
    {
      id: 'next_step', label: { fr: 'Étape suivante', en: 'next step' }, domain: ['step'], range: 'step',
      valueKind: 'entity', operators: ['exists', 'missing_in_view', 'in', 'none_of'],
    },
  );
  pack.entities.push(
    { id: 'test:proof:a', type: 'proof', label: 'Proof A', description: '' },
    { id: 'test:proof:b', type: 'proof', label: 'Proof B', description: '' },
    { id: 'test:step:a', type: 'step', label: 'Step A', description: '' },
    { id: 'test:step:b', type: 'step', label: 'Step B', description: '' },
  );
  const template = pack.assertions[0];
  pack.assertions.push(
    { ...template, id: 'test:dep', subject: 'test:proof:a', relation: 'depends_on', value: 'test:proof:b' },
    { ...template, id: 'test:next', subject: 'test:step:a', relation: 'next_step', value: 'test:step:b' },
  );
  const profiler = new StructuralProfiler(pack);
  const proofPlan = buildNavigationPlan({ profiler, query: { selection: { entityType: 'proof' } }, lens: null });
  const stepPlan = buildNavigationPlan({ profiler, query: { selection: { entityType: 'step' } }, lens: null });
  assert(proofPlan.views.some((view) => view.id === 'dependencies'));
  assert(proofPlan.views.some((view) => view.id === 'proofs'));
  assert(stepPlan.views.some((view) => view.id === 'path'));
});

test('declared navigation hints strengthen inference and customize reusable recipes', () => {
  const pack = demoPack();
  pack.registry.relations.push({
    id: 'custom:lineage',
    label: { fr: 'Relié à', en: 'relates to' },
    domain: ['human'],
    range: 'human',
    valueKind: 'entity',
    operators: ['exists', 'missing_in_view', 'in', 'none_of'],
  });
  pack.navigationHints = {
    schemaVersion: '0.1',
    capabilities: { temporal: { score: 0.95, reason: 'chronologie canonique disponible' } },
    relationCapabilities: { 'custom:lineage': ['temporal', 'dependency'] },
    preferredRecipes: ['timeline'],
    recipeLabels: { timeline: 'Trajectoire' },
  };
  const profiler = new StructuralProfiler(pack);
  const plan = buildNavigationPlan({ profiler, query: { selection: { entityType: 'human' } }, lens: null });
  const timeline = plan.views.find((view) => view.id === 'timeline');
  assert.ok(timeline);
  assert.equal(timeline.label, 'Trajectoire');
  assert.ok(timeline.relationIds.includes('custom:lineage'));
  assert.ok(profiler.global.affordances.temporal.score >= 0.95);
  assert.match(profiler.global.affordances.temporal.evidence.join(' '), /chronologie canonique/);
});
