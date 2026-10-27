import test from 'node:test';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import assert from 'node:assert/strict';
import { validate, publicSchemaVersions } from '../server/contracts.mjs';
import { rendererCatalog } from '../server/navigation/planner.mjs';
import { StructuralProfiler } from '../server/navigation/profiler.mjs';
import { buildNavigationPlan } from '../server/navigation/planner.mjs';

test('public 1.0 schemas are registered', () => {
  const versions = publicSchemaVersions();
  for (const id of ['navigation-plan','navigation-projection','renderer-registry','navigation-hints','exploration-state']) {
    assert.equal(versions[id], '1.0');
  }
});

test('controlled renderer registry validates as a public 1.0 contract', () => {
  assert.doesNotThrow(() => validate('renderer-registry', rendererCatalog()));
  assert(rendererCatalog().every((renderer) => renderer.accessibilityFallback && renderer.supportsKeyboard));
});

test('NavigationPlan 1.0 validates and remains explicitly derived', () => {
  const pack = {
    registry:{entityTypes:['node'],relations:[{id:'dep',label:{fr:'dépend de',en:'depends on'},domain:['node'],range:'node',valueKind:'entity',operators:['exists']}]},
    entities:[{id:'a',type:'node',label:'A'},{id:'b',type:'node',label:'B'}], sources:[],
    assertions:[{id:'x',subject:'a',relation:'dep',value:'b',sourceRefs:[]}],
    navigationHints:{schemaVersion:'1.0',affordances:{dependency:1}},
  };
  const profiler = new StructuralProfiler(pack);
  const plan = buildNavigationPlan({profiler,query:{selection:{entityType:'node'}},lens:null});
  assert.doesNotThrow(()=>validate('navigation-plan',plan));
  assert.equal(plan.derived,true);
  assert.equal(plan.semantics,'navigation-affordances-not-kristal-authority');
});

test('navigationHints rejects executable or unknown renderer payloads', () => {
  assert.throws(() => validate('navigation-hints', {
    schemaVersion:'1.0',
    affordances:{network:1},
    component:'https://example.invalid/renderer.js',
  }));
});


const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

const projectionRequirements = {
  'timeline-lineage': 'items',
  tree: 'roots',
  dag: 'acyclic',
  flow: 'transitions',
  'causal-feedback': 'cycles',
  matrix: 'cells',
  'state-flow': 'semantics',
  traceability: 'edges',
  multiscale: 'memberships',
  spatial: 'points',
};

test('all specialized projection fixtures satisfy the strict 1.0 DTO contract', () => {
  for (const [kind] of Object.entries(projectionRequirements)) {
    const value = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', `${kind}.json`), 'utf8'));
    assert.equal(value.projectionKind, kind);
    assert.doesNotThrow(() => validate('navigation-projection', value));
  }
});

test('projection DTO rejects family-shaped payloads missing renderer-required fields', () => {
  for (const [kind, requiredField] of Object.entries(projectionRequirements)) {
    const value = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', `${kind}.json`), 'utf8'));
    delete value[requiredField];
    assert.throws(() => validate('navigation-projection', value), undefined, `${kind} must require ${requiredField}`);
  }
});

test('projection DTO validates internal item shapes, not only top-level arrays', () => {
  const flow = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'flow.json'), 'utf8'));
  delete flow.transitions[0].conditional;
  assert.throws(() => validate('navigation-projection', flow));

  const matrix = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'matrix.json'), 'utf8'));
  delete matrix.cells[0].dimensionId;
  assert.throws(() => validate('navigation-projection', matrix));

  const spatial = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'spatial.json'), 'utf8'));
  spatial.points[0].lat = 181;
  assert.throws(() => validate('navigation-projection', spatial));
});


test('projection DTO binds each projection family to its controlled renderer and recipe set', () => {
  const dag = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'dag.json'), 'utf8'));
  dag.rendererId = 'spatial';
  assert.throws(() => validate('navigation-projection', dag));

  const tree = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'tree.json'), 'utf8'));
  tree.recipeId = 'proofs';
  assert.throws(() => validate('navigation-projection', tree));
});

test('projection DTO rejects raw upstream metadata and unknown top-level fields', () => {
  const state = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'state-flow.json'), 'utf8'));
  state.records[0].actionability.policy_refs = ['secret:policy'];
  assert.throws(() => validate('navigation-projection', state));

  const timeline = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'timeline-lineage.json'), 'utf8'));
  timeline.links[0].value.source_artifacts = ['secret:artifact'];
  assert.throws(() => validate('navigation-projection', timeline));

  const flow = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'flow.json'), 'utf8'));
  flow.unboundedRawPayload = { surprise: true };
  assert.throws(() => validate('navigation-projection', flow));
});

test('projection DTO enforces value-state semantics for public valuations and conditions', () => {
  const state = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'state-flow.json'), 'utf8'));
  state.records[0].valuations[0] = { dimension:'phase', value_semantics:'state', value_state:'unknown', value:'must-not-leak' };
  assert.throws(() => validate('navigation-projection', state));

  const flow = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'flow.json'), 'utf8'));
  flow.transitions[0].conditions[0] = { kind:'valuation', dimension:'eligibility', state:'unknown', value:true };
  assert.throws(() => validate('navigation-projection', flow));
});

test('state-flow action-context projection must retain the non-authority safety semantic', () => {
  const state = JSON.parse(fs.readFileSync(path.join(ROOT, 'examples', 'projections', 'state-flow.json'), 'utf8'));
  state.recipeId = 'action-context';
  state.semantics = 'derived-navigation-projection';
  assert.throws(() => validate('navigation-projection', state));
  state.semantics = 'actionability-is-not-execution-authority';
  assert.doesNotThrow(() => validate('navigation-projection', state));
});
