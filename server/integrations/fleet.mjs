// KNAV experimental, opt-in consumer of an explicitly supplied Manager inventory export.
// This is NOT a ratified inter-project contract and does not scan canonical workspaces.
import fs from 'node:fs';
import path from 'node:path';
import { fail } from '../errors.mjs';
import { MANAGER_LOCAL_FORMAT, validateManagerInventory, validateManagerAccessPolicy, projectManagerInventory } from './manager-adapter.mjs';
import { validateDiscoveryCatalog, enrichAuthorizedFleet } from './discovery.mjs';

export const FLEET_PREVIEW_FORMAT = 'konstellation.manager-inventory-preview/0.1';
const ID = /^[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}$/;
const SHA = /^sha256:[0-9a-f]{64}$/;
const READY = new Set(['unknown', 'not_checked', 'not_ready', 'ready', 'blocked', 'unavailable']);
const AVAILABILITY = new Set(['unknown', 'available', 'unavailable']);
const OPERATIONAL = new Set(['BLOCKED','ATTENTION_REQUIRED','LOCAL_CHECKS_PASSED','LOCAL_STRUCTURE_ONLY']);
const DISCOVERY = new Set(['absent','incomplete','invalid','stale','consistent_unverified','verified_registered_sources']);
const FRAMEWORK = new Set(['VERIFIED','FAILED','NOT_EVALUATED']);
const hasOwn = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
const validText = (value, max = 200) => typeof value === 'string' && value.length > 0 && value.length <= max && !/[\x00-\x1f\x7f]/.test(value);
const listOf = (value) => Array.isArray(value) && value.length <= 32 && value.every((item) => validText(item, 128));
const isObject = (value) => value && typeof value === 'object' && !Array.isArray(value);

export function validateFleetExport(doc) {
  if (!isObject(doc) || doc.format !== FLEET_PREVIEW_FORMAT || !Array.isArray(doc.entries) || doc.entries.length > 1000)
    fail('FLEET_EXPORT_INVALID', 'Unsupported or oversized Manager preview export.', 422);
  const seen = new Set();
  return doc.entries.map((entry) => {
    if (!isObject(entry) || !ID.test(entry.id || '') || !validText(entry.title) ||
        !['private', 'public'].includes(entry.visibility) ||
        !READY.has(entry.readiness) || !AVAILABILITY.has(entry.availability) ||
        !listOf(entry.allowed_principals) || !listOf(entry.allowed_roles) ||
        (entry.state_ref !== undefined && !validText(entry.state_ref, 512)) ||
        (entry.state_commitment !== undefined && !SHA.test(entry.state_commitment)) ||
        (entry.archetype !== undefined && !validText(entry.archetype, 100)) ||
        (entry.operational_result !== undefined && !OPERATIONAL.has(entry.operational_result)) ||
        (entry.discovery_status !== undefined && !DISCOVERY.has(entry.discovery_status)) ||
        (entry.framework_state_verification !== undefined && !FRAMEWORK.has(entry.framework_state_verification)) ||
        seen.has(entry.id)) fail('FLEET_EXPORT_INVALID', 'Invalid or duplicate Manager preview entry.', 422);
    // Reject fields that could contain filesystem paths, tokens, source payloads,
    // or implicitly claim verification, authority or publication.
    const fields = new Set(['id', 'title', 'visibility', 'readiness', 'availability',
      'allowed_principals', 'allowed_roles', 'state_ref', 'state_commitment', 'archetype',
      'operational_result','discovery_status','framework_state_verification']);
    if (Object.keys(entry).some((key) => !fields.has(key)))
      fail('FLEET_EXPORT_INVALID', 'Unexpected Manager preview entry field.', 422);
    seen.add(entry.id);
    return entry;
  });
}

export function readPrivateJsonFile(file, { maxBytes = 1024 * 1024 } = {}) {
  const absolute = path.resolve(file);
  let stat;
  try { stat = fs.lstatSync(absolute); }
  catch { fail('FLEET_EXPORT_UNAVAILABLE', 'Configured local metadata file is unavailable.', 503); }
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > maxBytes)
    fail('FLEET_EXPORT_INVALID', 'Local metadata must be a regular bounded non-symlink file.', 422);
  try { return JSON.parse(fs.readFileSync(absolute, 'utf8')); }
  catch { fail('FLEET_EXPORT_INVALID', 'Local metadata is not valid JSON.', 422); }
}

export function readFleetExport(file, policyFile = null) {
  if (!file) return [];
  const doc = readPrivateJsonFile(file);
  if (doc?.format === MANAGER_LOCAL_FORMAT) {
    const records = validateManagerInventory(doc);
    if (!policyFile) fail('FLEET_POLICY_REQUIRED', 'Explicit local Manager access policy required.', 403);
    const policy = validateManagerAccessPolicy(readPrivateJsonFile(policyFile));
    return validateFleetExport({format:FLEET_PREVIEW_FORMAT, entries:projectManagerInventory(records,policy)});
  }
  if (!isObject(doc) || Object.keys(doc).some((key) => !['format', 'entries'].includes(key)))
    fail('FLEET_EXPORT_INVALID', 'Unexpected inventory export field.', 422);
  return validateFleetExport(doc);
}

export function readDiscoveryCatalog(file) {
  return file ? validateDiscoveryCatalog(readPrivateJsonFile(file, {maxBytes:256*1024})) : [];
}

export function fleetForPrincipal(principal, entries, collection = null, discoveryCatalog = []) {
  if (!principal?.scopes?.includes('read') && !principal?.scopes?.includes('admin'))
    fail('ACCESS_DENIED', 'Read scope required.', 403);
  const local = entries
    .filter((entry) => entry.allowed_principals.includes(principal.id) ||
      entry.allowed_roles.some((role) => principal.roles.includes(role)))
    .map((entry) => ({
      key: `local:${entry.id}`, source: 'local_manager_preview', id: entry.id,
      title: entry.title, availability: entry.availability, readiness: entry.readiness,
      verification: 'declared_only', viewKind: 'inventory_only', openable: false,
      ...(entry.state_ref ? { stateRef: entry.state_ref } : {}),
      ...(entry.state_commitment ? { stateCommitment: entry.state_commitment } : {}),
      ...(entry.archetype ? { archetype: entry.archetype } : {}),
      ...(entry.operational_result ? { managerAssessment: {
        result: entry.operational_result,
        discovery: entry.discovery_status || 'not_checked',
        frameworkState: entry.framework_state_verification || 'NOT_EVALUATED',
        authority: 'operational_observation_only',
      }} : {}),
    }));
  const hosted = (collection?.items || []).map((item) => ({
    key: `reader:${item.id}`, source: collection?.source === 'kristal-github-collection-v10'
      ? 'github_v10_checkout' : ['kristal-local-v10','kristal-local-catalog-v10'].includes(collection?.source)
      ? 'local_v10_reader' : 'legacy_reader',
    id: item.id, title: item.label, availability: item.available ? 'available' : 'unavailable',
    readiness: 'unknown', verification: collection?.source === 'kristal-github-collection-v10'
      ? 'index_only' : ['kristal-local-v10','kristal-local-catalog-v10'].includes(collection?.source)
      ? 'checked_on_open' : 'not_checked',
    viewKind: collection?.source === 'kristal-github-collection-v10' ? 'technical_hosting'
      : ['kristal-local-v10','kristal-local-catalog-v10'].includes(collection?.source) ? 'local_v10_derived' : 'legacy',
    openable: Boolean(item.available),
    ...(item.available ? { readerId: item.id } : {}),
    ...(item.stateRef ? { stateRef: item.stateRef } : {}),
    ...(item.stateCommitment ? { stateCommitment: item.stateCommitment } : {}),
  }));
  // No joining on title, slug or state_ref: local and hosted observations remain separate.
  return { format: 'konstellation.fleet-view/0.1', experimental: true,
    items: enrichAuthorizedFleet([...local, ...hosted], discoveryCatalog).sort((a, b) => a.title.localeCompare(b.title, 'en') || a.key.localeCompare(b.key)) };
}
