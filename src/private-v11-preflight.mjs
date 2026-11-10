/**
 * Opt-in OFFLINE preflight for a derived Framework-v11 reading view.
 *
 * Neither the demo HTTP service nor catalog.mjs imports this module.
 * Inspecting bytes here does NOT approve semantics, publication or a website.
 */
import { createHash } from 'node:crypto';
import { readFileSync, lstatSync } from 'node:fs';
import { resolve } from 'node:path';

export const VIEW_PROFILE = 'kristal.integration.read-view/v11.0-draft.1';
export const MAX_VIEW_BYTES = 8 * 1024 * 1024;
const HASH = /^[a-f0-9]{64}$/;
const ENTITY = /^KQ[1-9][0-9]*$/;
const PROPERTY = /^KP[1-9][0-9]*$/;
const ASSERTION = /^KA[1-9][0-9]*$/;
const SOURCE = /^KS[1-9][0-9]*$/;
const LOCALE = /^[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*$/;
const DATATYPES = new Set(['string', 'boolean', 'integer', 'number', 'date', 'dateTime', 'uri']);
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const fail = message => { throw new Error('PRIVATE_V11_REJECTED: ' + message); };

/** This is a consumer-side structural/integrity guard, NOT Framework validation. */
export function inspectDerivedView(view, sourceDigests) {
  if (!object(view) || view.profile !== VIEW_PROFILE || view.derived_only !== true)
    fail('read-only derived v11 profile required');
  if (!object(view.source) || view.source.framework_version !== '11.0.0-draft.4'
      || typeof view.source.namespace_id !== 'string' || !view.source.namespace_id
      || typeof view.source.graph_id !== 'string' || !view.source.graph_id)
    fail('unverified Framework source identity');
  if (!LOCALE.test(view.requested_locale ?? '')) fail('invalid requested locale');
  if (!object(sourceDigests)) fail('four source digests are required');
  for (const name of ['graph', 'registry', 'crosswalk', 'catalog']) {
    const expected = view.source[name + '_sha256'];
    if (!HASH.test(expected ?? '') || !HASH.test(sourceDigests[name] ?? '')
        || expected !== sourceDigests[name]) fail('canonical input digest mismatch: ' + name);
  }
  if (!Array.isArray(view.presentation) || view.presentation.length > 50000
      || !Array.isArray(view.assertions) || view.assertions.length > 50000
      || !object(view.coverage_counts)) fail('invalid or unbounded read inventories');
  const actual = { direct: 0, fallback: 0, missing: 0 };
  const known = new Set();
  for (const item of view.presentation) {
    if (!object(item) || !['entity', 'property'].includes(item.kind)
        || !(item.kind === 'entity' ? ENTITY : PROPERTY).test(item.semantic_id ?? '')
        || known.has(item.semantic_id)) fail('invalid or repeated semantic identity');
    known.add(item.semantic_id);
    const lex = item.lexical;
    if (!object(lex) || !Object.hasOwn(actual, lex.status)) fail('invalid lexical status');
    if (lex.status === 'missing') {
      if (Object.hasOwn(lex, 'term') || Object.hasOwn(lex, 'effective_locale'))
        fail('missing lexeme must not be represented as a translation');
    } else if (typeof lex.term !== 'string' || !lex.term.trim()
        || typeof lex.layer_id !== 'string' || !lex.layer_id
        || !LOCALE.test(lex.effective_locale ?? '')
        || ((lex.status === 'direct') !== (lex.effective_locale === view.requested_locale)))
      fail('lexical term without matching locale or provenance');
    if (item.accepted_external_exact !== undefined) {
      const ext = item.accepted_external_exact;
      if (!object(ext) || ext.system !== 'wikidata'
          || !(item.kind === 'entity' ? /^Q[1-9][0-9]*$/ : /^P[1-9][0-9]*$/).test(ext.id ?? ''))
        fail('external identifier is not an exact Wikidata crosswalk');
    }
    actual[lex.status]++;
  }
  if (Object.keys(view.coverage_counts).sort().join('|') !== Object.keys(actual).sort().join('|')
      || Object.keys(actual).some(key => actual[key] !== view.coverage_counts[key]))
    fail('lexical coverage count mismatch');
  const seen = new Set();
  for (const a of view.assertions) {
    if (!object(a) || !ASSERTION.test(a.id ?? '') || seen.has(a.id)
        || !ENTITY.test(a.subject ?? '') || !PROPERTY.test(a.predicate ?? '')
        || !known.has(a.subject) || !known.has(a.predicate)) fail('invalid assertion identity or references');
    seen.add(a.id);
    if (!Array.isArray(a.sources) || a.sources.some(s => !SOURCE.test(s))) fail('invalid source references');
    if (!validObject(a.object, known)) fail('invalid typed assertion object');
    if (a.qualifiers !== undefined && (!Array.isArray(a.qualifiers) || a.qualifiers.some(q =>
      !object(q) || !PROPERTY.test(q.predicate ?? '') || !known.has(q.predicate)
      || !validObject(q.object, known)))) fail('invalid assertion qualifiers');
  }
  return {
    format: 'encyklopedia.private-v11-preflight/1.0', status: 'STRUCTURALLY_VERIFIED_NOT_PUBLIC',
    source_view_profile: VIEW_PROFILE,
    namespace_id: view.source.namespace_id, graph_id: view.source.graph_id,
    requested_locale: view.requested_locale,
    counts: { identities: known.size, assertions: seen.size, lexical: actual },
    derived_only: true, framework_validation_performed: false,
    canonical_authority_claimed: false, publication_authorized: false,
    limits: 'Consumer structural and input-byte integrity only. No Framework validation, rights review, independent qualification, or public serving permission.'
  };
}

function validObject(value, known) {
  if (!object(value)) return false;
  if (value.kind === 'entity') return ENTITY.test(value.id ?? '') && known.has(value.id);
  return value.kind === 'literal' && DATATYPES.has(value.datatype) && Object.hasOwn(value, 'value');
}

function safeBytes(file, max) {
  const path = resolve(file);
  const st = lstatSync(path);
  if (!st.isFile() || st.isSymbolicLink() || st.size < 1 || st.size > max)
    fail('missing, linked or oversized input: ' + path);
  return readFileSync(path);
}

/** Offline-only file preflight: requires ALL original four source files. */
export function inspectFile(viewFile, paths) {
  const bytes = safeBytes(viewFile, MAX_VIEW_BYTES);
  const digest = createHash('sha256').update(bytes).digest('hex');
  let view;
  try { view = JSON.parse(bytes.toString('utf8')); }
  catch { fail('derived view is not JSON'); }
  const hashes = {};
  for (const name of ['graph', 'registry', 'crosswalk', 'catalog']) {
    if (!paths?.[name]) fail('missing canonical input: ' + name);
    hashes[name] = createHash('sha256').update(safeBytes(paths[name], 64 * 1024 * 1024)).digest('hex');
  }
  return { ...inspectDerivedView(view, hashes), input_view_sha256: digest };
}
