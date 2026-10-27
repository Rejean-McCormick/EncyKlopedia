import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from '../server/index.mjs';
import { Engine } from '../server/engine.mjs';
import { loadPack } from '../server/pack.mjs';

test('HTTP API serves working queries, validation and explicit SA unavailability', async (t) => {
  const server = createServer({ engine: new Engine(loadPack()) });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  t.after(() => new Promise((r) => server.close(r)));
  const url = `http://127.0.0.1:${server.address().port}`;
  const get = (path) => fetch(url + path),
    post = (path, value, headers = {}) =>
      fetch(url + path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...headers },
        body: JSON.stringify(value),
      });
  const boot = await (await get('/api/bootstrap')).json();
  assert.equal(boot.synthetic, true);
  assert(boot.lenses.length >= boot.registry.entityTypes.length);
  const lensRef = boot.lenses.find((lens) => lens.rootType === 'human')?.id || boot.lenses[0].id;
  const q = {
    schemaVersion: '0.2',
    context: boot.context,
    selection: { entityType: 'human', filters: [], links: [] },
    order: 'entity_id_asc',
    pageSize: 24,
  };
  const res = await post('/api/query', { query: q });
  assert.equal(res.status, 200);
  const result = await res.json();
  assert.equal(result.rows.length, 24);
  const constellation = await post('/api/constellation', {
    focus: { kind: 'entity', id: result.rows[0].entityId },
    context: q.context,
    lensRef,
    limit: 8,
  });
  assert.equal(constellation.status, 200);
  const constellationBody = await constellation.json();
  assert.equal(constellationBody.schemaVersion, '0.1');
  assert(constellationBody.satellites.length > 0);
  const navigation = await post('/api/navigation/plan', {
    query: q,
    lensRef,
    selectedEntityId: null,
  });
  assert.equal(navigation.status, 200);
  const navigationBody = await navigation.json();
  assert.equal(navigationBody.schemaVersion, '1.0');
  assert(navigationBody.views.some((view) => view.id === 'timeline'));
  assert(navigationBody.views.some((view) => view.id === 'constellation'));
  const timeline = await post('/api/navigation/project', {
    query: q,
    lensRef,
    recipeId: 'timeline',
    selectedEntityId: null,
  });
  assert.equal(timeline.status, 200);
  const timelineBody = await timeline.json();
  assert.equal(timelineBody.rendererId, 'timeline-lineage');
  assert.equal(timelineBody.projectionKind, 'timeline-lineage');
  assert(timelineBody.items.length > 0);
  assert.equal(
    (await post('/api/query', { query: q }, { Origin: 'https://untrusted.example' })).status,
    403,
  );
  assert.equal(
    (await post('/api/query', { query: q }, { 'Content-Type': 'text/plain' })).status,
    415,
  );
  assert.equal((await post('/api/sa', {query:q})).status, 503);
  assert.equal((await post('/api/query', { query: {} })).status, 400);
  assert.equal((await post('/api/query', { data: 'x'.repeat(70000) })).status, 413);
  assert.equal((await get('/api/nope')).status, 404);
  const state = {
    schemaVersion: '0.2',
    query: q,
    lensRef,
    view: 'list',
    selectedEntityId: null,
    openPanels: ['filters'],
    layout: [],
  };
  assert.equal((await post('/api/validate-state', state)).status, 200);
  state.query.context.readerPolicyRef = 'old';
  assert.equal((await post('/api/validate-state', state)).status, 409);
});
