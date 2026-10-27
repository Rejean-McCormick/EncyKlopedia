import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { listKristalCollection, loadKristalCollection, resolveKristalCollectionState } from '../server/integrations/kristal.mjs';
import { importKristalV6State } from '../server/integrations/kristal-v6.mjs';

function collectionState() {
  return {
    schema_version: '6.0',
    artifact_type: 'kristal_state',
    artifact_status: 'reference',
    created_at: '2026-10-03T00:00:00Z',
    applicability: { domain: 'time' },
    assertions: [
      {
        assertion_id: 'dup',
        assertion_status: 'reviewed',
        record_role: 'reference_identifier',
        statement: {
          subject: { kind: 'item', id: 'urn:test:a', value: { label: 'A' } },
          predicate: 'has_literal',
          object: { kind: 'literal', value: true },
        },
      },
      {
        assertion_id: 'dup',
        assertion_status: 'reviewed',
        record_role: 'reference_identifier',
        statement: {
          subject: { kind: 'item', id: 'urn:test:b', value: { label: 'B' } },
          predicate: 'has_value',
          object: { kind: 'value', value: 1.5 },
        },
      },
      {
        assertion_id: 'json-value',
        assertion_status: 'reviewed',
        record_role: 'reference_identifier',
        statement: {
          subject: { kind: 'item', id: 'urn:test:a' },
          predicate: 'has_json',
          object: { kind: 'json', value: { b: 2, a: 1 } },
        },
      },
    ],
    content_hash: { algorithm: 'sha256', value: '0'.repeat(64) },
  };
}

test('collection compatibility mode accepts field/role variants while strict v6 still rejects them', () => {
  const state = collectionState();
  assert.throws(() => importKristalV6State(state), { code: 'INVALID_KRISTAL_STATE' });
  const pack = importKristalV6State(state, { compatibilityMode: 'collection' });
  assert.equal(pack.importRecord.validationProfile, 'collection-compatible-v6');
  assert.equal(pack.importRecord.identityVerified, false);
  assert(pack.importRecord.compatibilityWarnings.some((w) => w.code === 'KRISTAL_V6_COMPATIBILITY_PROFILE'));
  assert(pack.importRecord.compatibilityWarnings.some((w) => w.code === 'CONTENT_HASH_MISMATCH'));
  assert.equal(new Set(pack.assertions.map((a) => a.id)).size, pack.assertions.length);
  assert.equal(pack.importRecord.projectionWarnings[0].code, 'DUPLICATE_ASSERTION_ID');
  assert.equal(pack.assertions.find((a) => a.sourceValueKind === 'json').value, '{"a":1,"b":2}');
});

test('collection adapter discovers both corpus and direct knowledge-base kristal_state layouts', async (t) => {
  const root = fs.mkdtempSync(path.resolve('test-kollection-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const domain = path.join(root, 'domains', 'Kristal-Time', 'knowledge-base');
  fs.mkdirSync(domain, { recursive: true });
  const stateFile = path.join(domain, 'time.kristal-state.json');
  fs.writeFileSync(stateFile, JSON.stringify(collectionState()));

  assert.equal(
    resolveKristalCollectionState({ directory: root, kristal: 'time' }, process.cwd()),
    fs.realpathSync(stateFile),
  );
  const pack = await loadKristalCollection({ directory: root, kristal: 'Kristal-Time' }, process.cwd());
  assert.equal(pack.integration.adapter, 'kristal-kollection-v1');
  assert.equal(pack.integration.collection.domainDirectory, 'Kristal-Time');
  assert.equal(pack.assertions.length, 3);
  assert.equal(pack.entities.find((e) => e.upstreamRef === 'urn:test:a').label, 'A');
});


test('collection catalogue exposes readable Kristals and disables domains without a state', (t) => {
  const root = fs.mkdtempSync(path.resolve('test-kollection-list-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const readable = path.join(root, 'domains', 'Kristal-Time', 'knowledge-base', 'corpus');
  const unavailable = path.join(root, 'domains', 'Kristal-Empty', 'knowledge-base');
  fs.mkdirSync(readable, { recursive: true });
  fs.mkdirSync(unavailable, { recursive: true });
  fs.writeFileSync(path.join(readable, 'time.kristal-state.json'), JSON.stringify(collectionState()));

  const items = listKristalCollection({ directory: root }, process.cwd());
  assert.deepEqual(items.map(({ id, available }) => ({ id, available })), [
    { id: 'Empty', available: false },
    { id: 'Time', available: true },
  ]);
  assert.match(items[0].reason, /Aucun état/);
  assert.equal(items[1].stateFile, 'time.kristal-state.json');
});
