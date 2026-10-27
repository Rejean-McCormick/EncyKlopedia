import { test } from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { Engine } from '../server/engine.mjs';
import { loadPack, readJson } from '../server/pack.mjs';

const lenses = () => [
  readJson(path.resolve('examples/lenses/intellectual-history.json')),
  readJson(path.resolve('examples/lenses/sociodemography.json')),
  readJson(path.resolve('examples/lenses/catholic-intellectual-history.json')),
];

test('constellation ranks configured groups and enforces the 3-25 budget', () => {
  const engine = new Engine(loadPack());
  const context = engine.context();
  const focus = { kind: 'entity', id: 'demo:p000' };
  const result = engine.constellation(
    { focus, context, lensRef: 'intellectual-history', limit: 8 },
    lenses(),
  );
  assert.equal(result.schemaVersion, '0.1');
  assert(result.satellites.some((x) => x.label === 'Expertises'));
  assert(result.satellites.some((x) => x.label === 'Œuvres'));
  assert(result.satellites.length <= 8);
  assert.throws(
    () => engine.constellation({ focus, context, lensRef: 'intellectual-history', limit: 26 }, lenses()),
    { code: 'INVALID_QUERY' },
  );
});

test('qualifier navigation makes a theme a center without inventing an assertion', () => {
  const pack = loadPack();
  pack.entities.push({ id: 'demo:theme:libre-arbitre', type: 'concept', label: 'Libre arbitre' });
  const assertion = pack.assertions.find((a) => a.subject === 'demo:p000' && a.relation === 'field_of_work');
  assertion.qualifiers = [
    {
      predicate: { external_id: 'corpus:theme', label: 'Thème' },
      object: { kind: 'item', value: { external_id: 'demo:theme:libre-arbitre', label: 'libre arbitre' } },
    },
  ];
  const engine = new Engine(pack);
  const context = engine.context();
  const person = engine.constellation(
    { focus: { kind: 'entity', id: 'demo:p000' }, context, lensRef: 'type:human', limit: 8 },
    [],
  );
  // The generic type lens exposes qualifier groups by stable group id;
  // presentation labels are intentionally free to evolve.
  const themeGroup = person.satellites.find((x) => x.target.groupId === 'q:corpus:theme');
  assert(themeGroup);
  const themes = engine.constellation(
    { focus: themeGroup.target.focus, groupId: themeGroup.target.groupId, context, lensRef: 'type:human', limit: 8 },
    [],
  );
  const theme = themes.satellites.find((x) => x.label === 'Libre arbitre');
  assert(theme);
  const centered = engine.constellation(
    { focus: theme.target.focus, context, lensRef: 'type:human', limit: 8 },
    [],
  );
  assert.equal(centered.center.label, 'Libre arbitre');
  const relatedPeople = centered.satellites.find((x) => x.target.groupId === 'participants:subjects');
  assert(relatedPeople);
  const people = engine.constellation(
    { focus: theme.target.focus, groupId: relatedPeople.target.groupId, context, lensRef: 'type:human', limit: 8 },
    [],
  );
  assert(people.satellites.some((x) => x.label === 'Augustin d’Hippone'));
  assert.equal(engine.pack.assertions.length, pack.assertions.length);
});
