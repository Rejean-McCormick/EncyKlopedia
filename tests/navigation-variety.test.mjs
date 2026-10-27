import { test } from 'node:test';
import assert from 'node:assert/strict';
import { StructuralProfiler } from '../server/navigation/profiler.mjs';
import { buildNavigationPlan } from '../server/navigation/planner.mjs';

const ops = ['exists', 'missing_in_view', 'in', 'none_of'];
function relation(id, label, valueKind = 'entity') {
  return { id, label: { fr: label, en: label }, domain: ['node'], range: valueKind === 'entity' ? 'node' : 'value', valueKind, operators: ops };
}
function pack(relations, edges = []) {
  return {
    registry: { entityTypes: ['node'], relations },
    sources: [],
    assertions: edges.map(([id, subject, relationId, value]) => ({ id, subject, relation: relationId, value, sourceRefs: [] })),
  };
}
function viewIds(input) {
  const profiler = new StructuralProfiler(input);
  return buildNavigationPlan({ profiler, query: { selection: { entityType: 'node' } }, lens: null }).views.map((view) => view.id);
}

test('representative Math structure exposes proof and dependency navigation', () => {
  const ids = viewIds(pack([
    relation('math:proof_dependency', 'proof dependency'),
    relation('math:pedagogical_prerequisite', 'pedagogical prerequisite'),
    relation('math:proves', 'proves'),
  ]));
  assert(ids.includes('proofs'));
  assert(ids.includes('dependencies'));
  assert(ids.includes('path'));
});

test('representative HumanBody causal cycle exposes feedback navigation', () => {
  const ids = viewIds(pack([
    relation('humanbody:increases', 'increases'),
    relation('humanbody:decreases', 'decreases'),
    relation('humanbody:source_scale', 'source scale', 'integer'),
  ], [
    ['a1', 'a', 'humanbody:increases', 'b'],
    ['a2', 'b', 'humanbody:decreases', 'a'],
  ]));
  assert(ids.includes('feedback'));
});

test('representative HistoryTech structure exposes chronology and lineage dependency', () => {
  const ids = viewIds(pack([
    relation('historytech:historical_occurrence', 'historical occurrence'),
    relation('historytech:chronology', 'chronology', 'integer'),
    relation('historytech:derived_from', 'derived from'),
  ]));
  assert(ids.includes('timeline'));
  assert(ids.includes('dependencies'));
});

test('representative ScolQc structure exposes conditional path navigation', () => {
  const ids = viewIds(pack([
    relation('education-quebec:may_access_dep_program', 'may access DEP program'),
    relation('education-quebec:has_particular_admission_requirements', 'admission requirements'),
    relation('education-quebec:transition_contract', 'transition contract'),
  ]));
  assert(ids.includes('path'));
});

test('representative HospitalOps structure exposes workflow navigation', () => {
  const ids = viewIds(pack([
    relation('hospitalops:workflow_template', 'workflow template', 'string'),
    relation('hospitalops:resource_capability_template', 'resource capability template', 'string'),
  ]));
  assert(ids.includes('path'));
});

test('representative Power structure exposes multidimensional comparison', () => {
  const ids = viewIds(pack([
    relation('power:has_metric', 'has metric', 'integer'),
    relation('power:dimension_value', 'dimension value', 'integer'),
    relation('power:part_of', 'part of'),
  ]));
  assert(ids.includes('dimensions'));
});

test('deep dependency DAG is profiled without recursive stack exhaustion', () => {
  const dep = relation('bench:depends_on', 'depends on');
  const assertions = Array.from({ length: 15000 }, (_, i) => ({
    id: `deep:${i}`, subject: `n:${i}`, relation: dep.id, value: `n:${i + 1}`, sourceRefs: [],
  }));
  const input = { registry: { entityTypes: ['node'], relations: [dep] }, sources: [], assertions };
  const profiler = new StructuralProfiler(input);
  const plan = buildNavigationPlan({ profiler, query: { selection: { entityType: 'node' } }, lens: null });
  assert(plan.views.some((view) => view.id === 'dependencies'));
});
