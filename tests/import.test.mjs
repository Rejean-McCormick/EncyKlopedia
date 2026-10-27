import { test } from 'node:test';
import assert from 'node:assert/strict';
import { importState } from '../scripts/import-kristal.mjs';
import { loadPack } from '../server/pack.mjs';
const scope = { domain: 'research' };
function fixture() {
  const p = loadPack();
  const state = {
    schema_version: '5.0',
    artifact_type: 'structured_epistemic_state',
    state_id: 'sha256:' + 'a'.repeat(64),
    artifact_status: 'working',
    created_at: '2026-09-26T12:00:00Z',
    created_by: { agent_id: 'test:creator' },
    scope,
    assertions: [
      {
        assertion_id: 'sha256:' + 'b'.repeat(64),
        statement: {
          subject: { external_id: 'input:person' },
          predicate: { external_id: 'input:field' },
          object: { kind: 'item', value: { external_id: 'input:philosophy' } },
        },
        assertion_status: 'hypothesis',
        certainty_level: 'low',
        scope,
      },
    ],
    provenance: [],
  };
  const config = {
    title: 'Import test',
    synthetic: true,
    registry: p.registry,
    entities: [
      { id: 'test:person', sourceKey: 'input:person', type: 'human', label: 'Person' },
      {
        id: 'test:philosophy',
        sourceKey: 'input:philosophy',
        type: 'concept',
        label: 'Philosophy',
      },
    ],
    relationMappings: { 'input:field': 'field_of_work' },
    policies: [{ ...p.policies[1], authorities: ['*'], requireSources: false }],
  };
  return { state, config };
}
test('SES import validates shape and preserves hypothesis, scope and raw upstream payload', () => {
  const { state, config } = fixture();
  const p = importState(state, config);
  assert.equal(p.assertions[0].status, 'hypothesis');
  assert.equal(p.assertions[0].certainty, 'low');
  assert.equal(p.assertions[0].validationStatus, 'not_evaluated');
  assert.deepEqual(p.assertions[0].upstreamPayload, state.assertions[0]);
  assert.equal(p.importRecord.signatureVerification, 'not-performed');
});
test('SES import rejects unmapped/qualified assertions and invalid hashes without partial export', () => {
  let { state, config } = fixture();
  delete config.relationMappings['input:field'];
  assert.throws(() => importState(state, config), { code: 'UNMAPPED_ASSERTION' });
  ({ state, config } = fixture());
  state.assertions[0].statement.qualifiers = [
    { predicate: { external_id: 'test:scope' }, object: { kind: 'string', value: 'qualified' } },
  ];
  assert.throws(() => importState(state, config), { code: 'UNSUPPORTED_QUALIFIERS' });
  ({ state, config } = fixture());
  state.content_hash = { alg: 'sha256', value: 'c'.repeat(64) };
  state.hash_target_policy = { exclude_fields: ['state_id', 'content_hash', 'signatures'] };
  assert.throws(() => importState(state, config), { code: 'INTEGRITY_MISMATCH' });
});
