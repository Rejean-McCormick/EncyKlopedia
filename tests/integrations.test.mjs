import { test } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import path from 'node:path';
import { generateKeyPairSync, sign } from 'node:crypto';
import { Engine } from '../server/engine.mjs';
import { readJson, loadPack, hash, canonical } from '../server/pack.mjs';
import {
  loadIntegration,
  loadKristalDirectory,
  loadKristalHttp,
  mapRows,
} from '../server/integrations/kristal.mjs';
import {
  normalizeKristalPolicy,
  evaluatePolicy,
  policySupport,
} from '../server/integrations/reader-policy.mjs';
import {
  SemantikAdapter,
  buildCommunicationRequest,
  validateCommunicationResult,
} from '../server/integrations/semantik.mjs';
import { createServer } from '../server/index.mjs';
import fs from 'node:fs';
import { createHash } from 'node:crypto';
const base = path.resolve('examples/integrations');
const cfg = () => readJson(path.join(base, 'kristal-directory.json'));
const policy = () => readJson(path.join(base, 'runtime-pack/reader-policy.json'));
const query = (e) => ({
  schemaVersion: '0.2',
  context: e.context(),
  selection: { entityType: 'human', filters: [], links: [] },
  order: 'entity_id_asc',
  pageSize: 24,
});
const clone = structuredClone;
const resultFor = (request) => ({
  schema_version: '1.0',
  language: request.context.target_language,
  locale: request.context.target_locale,
  blocks: request.obligations.map((o, i) => ({
    block_id: 'b' + i,
    kind: 'utterance',
    text: 'Fixture de contrat ' + i,
    obligation_ids: [o.obligation_id],
  })),
  coverage: request.obligations.map((o, i) => ({
    obligation_id: o.obligation_id,
    block_ids: ['b' + i],
    realization_unit_ids: ['fixture:' + i],
  })),
  source_refs: [...new Set(request.obligations.flatMap((o) => o.source_refs || []))],
  runtime: {
    sa_version: 'fixture',
    runtime_set_id: 'fixture:runtime',
    sa_gf_contract_version: '1.0',
    capability_profile: 'konstellation-explorer-2',
  },
  deterministic_result_id: hash(request),
});
async function listen(t, handler) {
  const server = http.createServer(handler);
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  t.after(() => new Promise((r) => server.close(r)));
  return 'http://127.0.0.1:' + server.address().port;
}
async function body(req) {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  return JSON.parse(Buffer.concat(chunks));
}
const send = (res, data) => {
  res.setHeader('Content-Type', 'application/json');
  res.end(JSON.stringify(data));
};
test('real Parquet pack loads all assertions, hashes and native policies before query/facets', async () => {
  const p = await loadIntegration(path.join(base, 'kristal-directory.json'));
  assert.equal(p.assertions.length, 637);
  assert.equal(p.integration.metadata.integrityVerified, true);
  const e = new Engine(p),
    q = query(e);
  assert.equal(e.query(q).total.value, 132);
  assert.equal(e.scope(q.context).assertions.size, 637);
  assert.equal(e.bootstrap([]).capabilities.packAdapter, 'kristal-runtime-pack-v1');
  const relation = p.assertions[0].relation;
  assert.equal(e.facets(q, [relation])[relation].available, true);
  const detail = e.entity(p.assertions[0].subject, q.context);
  assert(detail.assertions.every((a) => !('upstreamPayload' in a.payload)));
});
test('pack rejects wrong pins, unmapped predicates, missing columns, row budgets and forged attestations', async () => {
  await assert.rejects(loadKristalDirectory({ ...cfg(), manifestSha256: '0'.repeat(64) }, base), {
    code: 'PACK_INTEGRITY_FAILED',
  });
  await assert.rejects(loadKristalDirectory({ ...cfg(), relationMappings: {} }, base), {
    code: 'UNMAPPED_ASSERTION',
  });
  const c = cfg();
  delete c.rows[0].columns.certainty;
  await assert.rejects(loadKristalDirectory(c, base), { code: 'INVALID_CONFIG' });
  await assert.rejects(loadKristalDirectory({ ...cfg(), maxRows: 2 }, base), {
    code: 'PACK_LIMIT',
  });
  const p = await loadKristalDirectory(
    { ...cfg(), attestation: { signaturesVerified: true } },
    base,
  );
  assert.equal(p.integration.metadata.signaturesVerified, false);
});
test('unmapped relations cannot turn missing_in_view into false knowledge', async () => {
  const p = await loadKristalDirectory(cfg(), base);
  const r = p.registry.relations[0];
  p.integration.capabilities.relations[r.id] = {
    available: false,
    operators: [],
    reason: 'Mapping absent',
  };
  const e = new Engine(p),
    q = query(e);
  q.selection.entityType = r.domain[0];
  q.selection.filters = [{ relation: r.id, op: 'missing_in_view' }];
  assert.throws(() => e.query(q), { code: 'UNSUPPORTED_CAPABILITY' });
  assert.equal(
    e.facets({ ...q, selection: { ...q.selection, filters: [] } }, [r.id])[r.id].available,
    false,
  );
});
test('native policy exclusions affect joins, sources and evidence consistently', async () => {
  const p = await loadKristalDirectory(cfg(), base),
    d = policy();
  d.policy.blocked_assertion_statuses = ['sourced'];
  p.policies = [normalizeKristalPolicy(d)];
  const e = new Engine(p),
    a = p.assertions.find((a) => a.status === 'sourced');
  assert(!e.scope(e.context()).assertions.has(a.id));
  assert.throws(() => e.evidence([a.id], e.context()), { code: 'NOT_FOUND' });
  assert(!e.entity(a.subject, e.context()).assertions.some((x) => x.assertionRef === a.id));
  d.policy.allowed_assertion_statuses = [];
  p.policies = [normalizeKristalPolicy(d)];
  assert.equal(new Engine(p).scope(new Engine(p).context()).assertions.size, 0);
});
test('native policy integrity, certainty modes, custom labels and unsupported priority fail explicitly', async () => {
  const p = await loadKristalDirectory(cfg(), base),
    a = p.assertions[0],
    d = policy();
  d.offline.require_signature_check = true;
  assert.throws(() => evaluatePolicy(normalizeKristalPolicy(d), a, p), {
    code: 'POLICY_UNEVALUABLE',
  });
  delete d.offline.require_signature_check;
  d.mode = 'high_certainty_only';
  assert.equal(
    evaluatePolicy(normalizeKristalPolicy(d), { ...a, certainty: 'low' }, p).visible,
    false,
  );
  d.mode = 'research';
  d.policy.custom_rules = [
    {
      rule_id: 'label-rule',
      condition: { field: 'status', op: 'eq', value: a.status },
      effect: 'label',
      label: 'Review label',
    },
  ];
  assert.deepEqual(evaluatePolicy(normalizeKristalPolicy(d), a, p).labels, ['Review label']);
  d.query.default_ordering = 'authority_then_certainty';
  assert.equal(policySupport(d).available, false);
  p.policies = [normalizeKristalPolicy(d)];
  const e = new Engine(p);
  assert.throws(() => e.query(query(e)), { code: 'UNSUPPORTED_POLICY' });
});
test('HTTP Kristal reads every page and rejects truncated, repeated or identity-shifted projections', async (t) => {
  const c = readJson(path.join(base, 'kristal-http.json')),
    manifest = readJson(path.join(base, c.manifest)),
    p = await loadKristalDirectory(cfg(), base);
  // The example layout declares JSON strings; the service can also return decoded values.
  const rows = p.assertions.map((a) => a.upstreamPayload);
  let mode = 'good',
    calls = 0;
  c.queryUrl = await listen(t, async (req, res) => {
    const b = await body(req);
    calls++;
    const offset = Number(b.paging.cursor || 0),
      items = rows.slice(offset, offset + 100);
    send(res, {
      contract_id: manifest.query_contract_ref.contract_id,
      runtime_pack_id: mode === 'identity' ? 'other' : manifest.runtime_pack_id,
      source_exchange_id: manifest.source_exchange_ref.exchange_id,
      projection: 'assertions',
      reader_policy_id: c.readerPolicyId,
      results: items,
      paging: {
        has_more: offset + 100 < rows.length,
        next_cursor: mode === 'repeat' ? '100' : String(offset + 100),
      },
      diagnostics: { truncated: mode === 'truncated', filters_applied_before_paging: true },
    });
  });
  const loaded = await loadKristalHttp(c, base);
  assert.equal(loaded.assertions.length, 637);
  assert.equal(calls, 7);
  assert.equal(new Engine(loaded).query(query(new Engine(loaded))).total.value, 132);
  for (const [m, code] of [
    ['truncated', 'UPSTREAM_INCOMPLETE'],
    ['repeat', 'UPSTREAM_INCOMPLETE'],
    ['identity', 'UPSTREAM_CONTEXT_MISMATCH'],
  ]) {
    mode = m;
    await assert.rejects(loadKristalHttp(c, base), { code });
  }
});
test('SA requests are schema-valid and preserve nested criteria, epistemic labels and source identity', () => {
  const e = new Engine(loadPack()),
    q = query(e);
  const first = e.pack.assertions[0];
  const req = buildCommunicationRequest(e, { query: q, action: 'entity', entityId: first.subject });
  assert.equal(req.capability_profile, 'konstellation-explorer-2');
  assert.deepEqual(req.supporting_context, []);
  assert(req.semantic_graph.statements.every((s) => !s.predicate_ref.startsWith('sa:')));
  assert(req.obligations.length > 2);
  assert(
    req.semantic_graph.statements.some(
      (s) => s.predicate_ref === 'konstellation:assertion-certainty',
    ),
  );
  assert(req.obligations.some((o) => o.source_refs.includes(first.id)));
  assert.equal(
    req.request_id,
    buildCommunicationRequest(e, { query: q, action: 'entity', entityId: first.subject })
      .request_id,
  );
  const page = e.query(q);
  const next = buildCommunicationRequest(e, { query: q, cursor: page.nextCursor, action: 'page' });
  const resultPage = next.semantic_graph.statements.find(
    (s) => s.predicate_ref === 'konstellation:result-page',
  );
  const members = next.semantic_graph.nodes.find(
    (n) =>
      n.id ===
      resultPage.arguments.find((a) => a.role_ref === 'konstellation-role:members').value_id,
  );
  assert.equal(members.members.length, 24);
});
test('SA response validation rejects lost obligations, false coverage, foreign runtime, sources and unassigned prose', () => {
  const e = new Engine(loadPack()),
    req = buildCommunicationRequest(e, {
      query: query(e),
      action: 'entity',
      entityId: e.pack.assertions[0].subject,
    }),
    c = { runtimeSetId: 'fixture:runtime' };
  const valid = resultFor(req);
  assert.equal(validateCommunicationResult(req, valid, c), valid);
  const cases = [
    (r) => r.coverage.pop(),
    (r) => (r.coverage[0].block_ids = ['missing']),
    (r) => (r.runtime.runtime_set_id = 'foreign'),
    (r) => (r.source_refs = []),
    (r) =>
      r.blocks.push({
        block_id: 'extra',
        kind: 'utterance',
        text: 'unassigned',
        obligation_ids: [],
      }),
  ];
  for (const change of cases) {
    const r = clone(valid);
    change(r);
    assert.throws(() => validateCommunicationResult(req, r, c));
  }
});
test('full application API discovers SA profile, validates request, renders and exports without service', async (t) => {
  const calls = [];
  const baseUrl = await listen(t, async (req, res) => {
    calls.push(req.url);
    if (req.url === '/ready')
      return send(res, {
        status: 'ready',
        runtime_sets: [{ runtime_set_id: 'fixture:runtime', valid: true }],
      });
    if (req.url === '/v1/capabilities')
      return send(res, {
        'fixture:runtime': {
          fr: {
            status: 'RELEASED',
            profiles: [{ profile_id: 'konstellation-explorer-2', status: 'RELEASED' }],
          },
        },
      });
    const b = await body(req);
    send(
      res,
      req.url === '/v1/validate-request' ? { valid: true, request_id: b.request_id } : resultFor(b),
    );
  });
  const e = new Engine(loadPack()),
    sa = new SemantikAdapter({
      baseUrl,
      runtimeSetId: 'fixture:runtime',
      capabilityProfile: 'konstellation-explorer-2',
      languages: ['fr'],
    });
  assert.equal((await sa.capabilities()).available, true);
  const app = createServer({ engine: e, semantik: sa });
  await new Promise((r) => app.listen(0, '127.0.0.1', r));
  t.after(() => new Promise((r) => app.close(r)));
  const response = await fetch('http://127.0.0.1:' + app.address().port + '/api/sa', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: query(e), action: 'page' }),
  });
  assert.equal(response.status, 200);
  assert((await response.json()).result.coverage.length > 0);
  assert(calls.includes('/v1/validate-request'));
  assert(calls.includes('/v1/render'));
  assert(new SemantikAdapter().request(e, { query: query(e) }).semantic_graph);
  await assert.rejects(
    new SemantikAdapter({ ...sa.config, capabilityProfile: 'unpublished-1' }).render(e, {
      query: query(e),
    }),
    { code: 'SA_UNAVAILABLE' },
  );
});
test('Ed25519 signatures and file bytes are checked; traversal and symlink escapes are refused', async (t) => {
  const root = fs.mkdtempSync(path.resolve('test-pack-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  fs.cpSync(path.join(base, 'runtime-pack'), root, { recursive: true });
  const c = { ...cfg(), directory: root };
  const manifest = readJson(path.join(root, 'manifest.json'));
  const { privateKey, publicKey } = generateKeyPairSync('ed25519');
  const signature = sign(null, Buffer.from(canonical(manifest)), privateKey).toString('base64');
  manifest.signatures = [
    { key_id: 'fixture-key', alg: 'ed25519', signature, created_at: '2026-09-26T00:00:00Z' },
  ];
  const write = () => {
    const bytes = Buffer.from(JSON.stringify(manifest));
    fs.writeFileSync(path.join(root, 'manifest.json'), bytes);
    c.manifestSha256 = createHash('sha256').update(bytes).digest('hex');
  };
  write();
  c.signatures = {
    excludeFields: ['signatures'],
    publicKeys: { 'fixture-key': publicKey.export({ type: 'spki', format: 'pem' }) },
  };
  assert.equal((await loadKristalDirectory(c, base)).integration.metadata.signaturesVerified, true);
  manifest.signatures[0].signature = Buffer.alloc(64).toString('base64');
  write();
  await assert.rejects(loadKristalDirectory(c, base), { code: 'PACK_SIGNATURE_INVALID' });
  delete c.signatures;
  fs.appendFileSync(path.join(root, 'catalog.json'), ' ');
  await assert.rejects(loadKristalDirectory(c, base), { code: 'PACK_INTEGRITY_FAILED' });
  await assert.rejects(loadKristalDirectory({ ...c, manifest: '../manifest.json' }, base), {
    code: 'PACK_PATH_INVALID',
  });
  fs.symlinkSync(path.join(base, 'runtime-pack/manifest.json'), path.join(root, 'escape.json'));
  await assert.rejects(loadKristalDirectory({ ...c, manifest: 'escape.json' }, base), {
    code: 'PACK_PATH_INVALID',
  });
});
