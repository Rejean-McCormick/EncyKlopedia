import test from 'node:test';
import assert from 'node:assert/strict';
import { Engine } from '../server/engine.mjs';
import { loadLenses } from '../server/index.mjs';

function pack() {
  return {
    schemaVersion: '0.3', title: 'Generic', description: 'Generic', synthetic: true,
    registry: {
      schemaVersion: '0.2', registryRef: 'generic', entityTypes: ['thing'],
      relations: [
        { id: 'parent', label: { fr: 'parent', en: 'parent' }, domain: ['thing'], range: 'thing', valueKind: 'entity', operators: ['exists', 'missing_in_view', 'in', 'none_of'] },
        { id: 'when', label: { fr: 'date', en: 'date' }, domain: ['thing'], range: 'interval', valueKind: 'interval', operators: ['exists', 'missing_in_view', 'overlaps'] },
      ],
    },
    entities: [{ id: 'a', type: 'thing', label: 'A' }, { id: 'b', type: 'thing', label: 'B' }],
    assertions: [], sources: [],
    policies: [{ id: 'all', label: 'All', description: 'All visible assertions', profile: 'konstellation.normalized-reader.v1', showLabels: true, statuses: ['*'], certainties: ['*'], validationStatuses: ['*'], validatedAs: ['*'], authorities: ['*'], requireSources: false }],
  };
}

test('unknown entity types receive a generic Lens without domain-specific defaults', () => {
  const engine = new Engine(pack());
  const lenses = loadLenses(engine, null);
  assert.equal(lenses.length, 1);
  assert.equal(lenses[0].id, 'type:thing');
  assert.equal(lenses[0].rootType, 'thing');
  assert(lenses[0].facets.some((facet) => facet.relation === 'parent' && facet.widget === 'entity-picker'));
  assert(lenses[0].facets.some((facet) => facet.relation === 'when' && facet.widget === 'year-range'));
  assert.deepEqual(lenses[0].constellation.groups, []);
});
