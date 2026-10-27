import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { ROOT, ajv, fail } from '../server/contracts.mjs';
import { readJson, canonical, hash, validatePack } from '../server/pack.mjs';
import { importKristalV6State, isKristalV6State } from '../server/integrations/kristal-v6.mjs';
const upstreamSchema = readJson(
  path.join(ROOT, 'contracts/upstream/structured-epistemic-state.schema.json'),
);
const validateState = ajv.compile(upstreamSchema);
export function sourceIdentity(ref) {
  return (
    ref.external_id ||
    ref.iri ||
    (ref.qid ? 'wikidata:' + ref.qid : ref.pid ? 'wikidata-property:' + ref.pid : null)
  );
}
export function importState(state, config, inputSha256 = 'not-provided') {
  if (!validateState(state)) fail('INVALID_KRISTAL_STATE', ajv.errorsText(validateState.errors));
  if (!config || !Array.isArray(config.entities) || !config.relationMappings || !config.registry)
    fail('INVALID_MAPPING', 'Explicit entities, registry and relationMappings required.');
  // Schema validation is not epistemic validation or signature verification.
  if (state.content_hash) {
    const excluded = state.hash_target_policy?.exclude_fields;
    if (
      !Array.isArray(excluded) ||
      canonical([...excluded].sort()) !== canonical(['content_hash', 'signatures', 'state_id'])
    )
      fail(
        'UNSUPPORTED_HASH_POLICY',
        'Only the declared state_id/content_hash/signatures exclusion profile is supported.',
      );
    const payload = Object.fromEntries(
      Object.entries(state).filter(([k]) => !excluded.includes(k)),
    );
    const expected = state.content_hash.value.replace(/^sha256:/, '');
    if (createHash('sha256').update(canonical(payload)).digest('hex') !== expected)
      fail('INTEGRITY_MISMATCH', 'Structured state content_hash does not match.');
  }
  const entityBySource = new Map(config.entities.map((e) => [e.sourceKey, e]));
  if (entityBySource.size !== config.entities.length)
    fail('INVALID_MAPPING', 'Duplicate source identity.');
  const sources = new Map(
    (state.source_refs || []).map((s) => [s.source_id || s.source_url || s.content_hash?.value, s]),
  );
  const normalizedSources = new Map();
  function sourceId(s) {
    const key = s.source_id || s.source_url || s.content_hash?.value;
    if (!key) fail('INVALID_MAPPING', 'Source lacks identity.');
    const id = hash({ source: key });
    normalizedSources.set(id, {
      id,
      title: s.title || key,
      description: s.publisher || '',
      ...(s.source_url ? { url: s.source_url } : {}),
      upstream: s,
    });
    return id;
  }
  for (const s of sources.values()) sourceId(s);
  const relations = new Map(config.registry.relations.map((r) => [r.id, r]));
  const assertions = state.assertions.map((a) => {
    const st = a.statement,
      subject = entityBySource.get(sourceIdentity(st.subject));
    const mapped = config.relationMappings[sourceIdentity(st.predicate)];
    const relation = relations.get(mapped);
    if (!subject || !relation)
      fail(
        'UNMAPPED_ASSERTION',
        `Explicit mapping missing for ${a.assertion_id}. No assertions were silently skipped.`,
      );
    if (st.qualifiers?.length)
      fail(
        'UNSUPPORTED_QUALIFIERS',
        `Qualified assertion ${a.assertion_id} requires a dedicated adapter recipe.`,
      );
    let value;
    if (st.object.kind === 'item' && relation.valueKind === 'entity') {
      const target = entityBySource.get(sourceIdentity(st.object.value));
      if (!target) fail('UNMAPPED_ASSERTION', 'Object entity is not mapped.');
      value = target.id;
    } else if (st.object.kind === 'string' && relation.valueKind === 'string')
      value = st.object.value;
    else if (
      st.object.kind === 'quantity' &&
      relation.valueKind === 'integer' &&
      Number.isSafeInteger(st.object.value.amount) &&
      !st.object.value.unit_qid &&
      !st.object.value.unit_label
    )
      value = st.object.value.amount;
    else
      fail('UNSUPPORTED_VALUE', `Value kind ${st.object.kind} needs an explicit adapter recipe.`);
    const sourceRefs = [
      ...new Set(
        (a.evidence_refs || []).filter((e) => e.source_ref).map((e) => sourceId(e.source_ref)),
      ),
    ];
    return {
      id: a.assertion_id,
      subject: subject.id,
      relation: mapped,
      value,
      status: a.assertion_status,
      certainty: a.certainty_level,
      validationStatus: a.validation?.validation_status || 'not_evaluated',
      validatedAs: a.validated_as || a.validation?.validated_as || 'unknown',
      authority: a.validation?.authority_channel?.authority_channel_id || 'authority:unspecified',
      scope: a.scope,
      sourceRefs,
      conflictsWith: a.conflicts_with || [],
      upstreamContractRef: upstreamSchema.$id,
      upstreamPayload: a,
    };
  });
  const pack = {
    schemaVersion: '0.3',
    title: config.title || 'Kristal · projection locale',
    description:
      config.description ||
      'Import explicite d’un Structured Epistemic State v5. Les labels épistémiques sont conservés.',
    synthetic: config.synthetic === true,
    registry: config.registry,
    entities: config.entities.map(({ sourceKey, ...e }) => e),
    assertions,
    sources: [...normalizedSources.values()],
    policies: config.policies,
    ...(config.navigationHints ? { navigationHints: config.navigationHints } : {}),
    importRecord: {
      inputSha256,
      stateId: state.state_id,
      artifactStatus: state.artifact_status,
      importer: 'konstellation-ses-subset:0.3.0',
      mappingHash: hash(config),
      signatureVerification: 'not-performed',
      upstreamState: state,
    },
  };
  return validatePack(pack);
}

export function importAnyState(state, config, inputSha256 = 'not-provided') {
  if (isKristalV6State(state)) return importKristalV6State(state, config || {}, inputSha256);
  return importState(state, config, inputSha256);
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  const [input, mapping, output] = process.argv.slice(2);
  if (!input || !mapping || !output) {
    console.error('Usage: npm run pack:import -- state.json mapping-or-config.json output.pack.json');
    process.exitCode = 1;
  } else {
    try {
      if (fs.existsSync(output))
        fail('OUTPUT_EXISTS', 'Choose a new output path; existing packs are immutable.');
      const bytes = fs.readFileSync(input);
      const pack = importAnyState(
        JSON.parse(bytes),
        readJson(mapping),
        createHash('sha256').update(bytes).digest('hex'),
      );
      fs.writeFileSync(output, JSON.stringify(pack, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
      console.log(
        JSON.stringify(
          {
            output,
            datasetRef: hash(pack),
            assertions: pack.assertions.length,
            signatureVerification: 'not-performed',
          },
          null,
          2,
        ),
      );
    } catch (e) {
      console.error(e.code || 'IMPORT_FAILED', e.message);
      process.exitCode = 1;
    }
  }
}
