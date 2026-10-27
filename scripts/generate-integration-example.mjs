import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { parquetWriteBuffer } from 'hyparquet-writer';
import { loadPack, hash } from '../server/pack.mjs';
import { upstream } from '../server/integrations/upstream.mjs';
const dir = path.resolve('examples/integrations/runtime-pack');
fs.mkdirSync(dir, { recursive: true });
const sha = (x) => createHash('sha256').update(x).digest('hex');
const write = (name, data) => {
  const bytes = Buffer.isBuffer(data) ? data : Buffer.from(JSON.stringify(data, null, 2) + '\n');
  fs.writeFileSync(path.join(dir, name), bytes);
  return { path: name, sha256: sha(bytes), size_bytes: bytes.length };
};
const demo = loadPack();
const { assertions, policies, ...catalog } = demo;
catalog.title = 'Konstellation · pack Parquet de démonstration';
const policy = {
  schema_version: '5.0',
  artifact_type: 'reader_policy',
  reader_policy_id: 'reader_policy:konstellation:demo',
  name: 'Recherche · labels conservés',
  mode: 'research',
  created_at: '2026-09-26T00:00:00Z',
  policy: {
    include_disputed: true,
    include_speculative: true,
    include_unknown_certainty: true,
    authority_filter: {
      allow_unrecognized_authority_channels: true,
      allow_conditionally_recognized_authorities: true,
    },
  },
  query: {
    allow_cross_scope_queries: true,
    allow_cross_authority_queries: true,
    default_ordering: 'stable',
    conflict_behavior: 'preserve_disagreement',
  },
  offline: { require_local_integrity_check: false },
  fallback_behavior: 'error',
};
upstream('policy', policy);
const rows = assertions.map((a) => ({ ...a, recognitionStatus: 'under_review' }));
const keys = [...new Set(rows.flatMap(Object.keys))];
const jsonColumns = keys.filter((k) => rows.some((a) => a[k] !== null && typeof a[k] === 'object'));
// Values vary by relation: encode this column as JSON as well.
if (!jsonColumns.includes('value')) jsonColumns.push('value');
const parquet = Buffer.from(
  parquetWriteBuffer({
    columnData: keys.map((name) => ({
      name,
      type: 'STRING',
      data: rows.map((a) =>
        a[name] === undefined
          ? null
          : jsonColumns.includes(name)
            ? JSON.stringify(a[name])
            : String(a[name]),
      ),
    })),
    rowGroupSize: 100,
  }),
);
const files = [
  { ...write('catalog.json', catalog), role: 'metadata' },
  { ...write('reader-policy.json', policy), role: 'reader_policy' },
  { ...write('assertions.parquet', parquet), role: 'parquet_data' },
];
const manifest = {
  schema_version: '5.0',
  artifact_type: 'runtime_pack_manifest',
  runtime_pack_id: hash(rows),
  runtime_pack_version: '5.0.0',
  created_at: '2026-09-26T00:00:00Z',
  source_exchange_ref: { exchange_id: hash(demo), artifact_type: 'working_exchange' },
  source_artifact_status: 'working',
  compiler: { name: 'konstellation-example-writer', version: '0.4.0' },
  build: {
    build_id: 'konstellation:example:0.4.0',
    deterministic: true,
    canonicalization_profile: 'kristal.v5:jcs-rfc8785',
    canonicalization_version: '1',
    config_hash: hash({ version: '0.4.0' }),
    compile_status: 'succeeded',
  },
  policies: {
    data_ordering: { policy: 'qid_pid_statement_id_asc' },
    row_grouping: { policy: 'fixed_rows_100k' },
    membership_filter: { kind: 'none' },
    bitmap: { format: 'roaring_run_optimized', run_optimize: true },
  },
  reader_policy_refs: [
    {
      id: 'sha256:' + files[1].sha256,
      artifact_type: 'reader_policy',
      hash: 'sha256:' + files[1].sha256,
    },
  ],
  query_contract_ref: {
    contract_id: 'kristal.v5:query-contract:offline-core',
    contract_version: '1',
  },
  files,
  integrity: { hash_alg: 'sha256' },
};
upstream('manifest', manifest);
const m = write('manifest.json', manifest);
const layout = {
  file: 'assertions.parquet',
  format: 'parquet',
  columns: Object.fromEntries(keys.map((k) => [k, k])),
  jsonColumns,
  qualifiersPreserved: true,
};
const config = {
  adapter: 'kristal-runtime-pack-v1',
  directory: 'runtime-pack',
  manifest: 'manifest.json',
  manifestSha256: m.sha256,
  catalog: 'catalog.json',
  rows: [layout],
  relationMappings: Object.fromEntries(
    [...new Set(rows.map((a) => a.relation))].map((id) => [id, id]),
  ),
};
fs.writeFileSync(
  'examples/integrations/kristal-directory.json',
  JSON.stringify(config, null, 2) + '\n',
);
fs.writeFileSync(
  'examples/integrations/kristal-http.json',
  JSON.stringify(
    {
      ...config,
      adapter: 'kristal-http-query-v1',
      manifest: 'runtime-pack/manifest.json',
      manifestSha256: hash(manifest),
      catalog: 'runtime-pack/catalog.json',
      rows: undefined,
      directory: undefined,
      queryUrl: 'http://127.0.0.1:8082/query',
      readerPolicyId: policy.reader_policy_id,
      policies: [{ file: 'runtime-pack/reader-policy.json', sha256: files[1].sha256 }],
      layout,
      pageSize: 100,
    },
    null,
    2,
  ) + '\n',
);
console.log('Generated pinned synthetic Parquet example:', rows.length, 'assertions');
