// Local-only, opt-in projection of Manager's *unratified* operational export.
// The separate policy is operator supplied: Manager records do NOT carry ACLs.
import { createHash } from 'node:crypto';
import { fail } from '../errors.mjs';

export const MANAGER_LOCAL_FORMAT = 'kristal.manager-local-inventory/0.1-candidate';
export const MANAGER_POLICY_FORMAT = 'konstellation.manager-access-policy/0.1';
const sha = /^sha256:[0-9a-f]{64}$/;
const own = (x, k) => Object.prototype.hasOwnProperty.call(x, k);
const obj = (x) => x !== null && typeof x === 'object' && !Array.isArray(x);
const text = (x, max = 512) => typeof x === 'string' && x.length > 0 && x.length <= max && !/[\x00-\x1f\x7f]/.test(x);
const principals = (x) => Array.isArray(x) && x.length <= 32 && x.every(v => text(v, 128));
const strictKeys = (x, keys) => Object.keys(x).every(k => keys.includes(k));
const OPERATIONAL = new Set(['BLOCKED','ATTENTION_REQUIRED','LOCAL_CHECKS_PASSED','LOCAL_STRUCTURE_ONLY']);
const FRAMEWORK = new Set(['VERIFIED','FAILED','NOT_EVALUATED']);
const DISCOVERY = new Set(['absent','incomplete','invalid','stale','consistent_unverified','verified_registered_sources']);
const allowedRecords = ['title','slug','state_ref','workspace_format','native_kind','profile',
  'readiness','state_source','state_commitment','state_conflict','hosted_network_baseline',
  'portable_ai_enabled','ai_entrypoint_present','ai_manifest_present','registered_artifacts',
  'availability','qualification','publication','archetype','identity_collision',
  'discovery','operational_result','framework_state_verification'];

export function validateManagerInventory(doc) {
  if (!obj(doc) || doc.format !== MANAGER_LOCAL_FORMAT || doc.mode !== 'local-read-only' ||
    doc.semantic_authority !== false || doc.validated_domain_facts !== false ||
    !Array.isArray(doc.records) || doc.records.length > 1000 || doc.record_count !== doc.records.length ||
    !strictKeys(doc, ['format','mode','generated_at','identity_rule','semantic_authority',
      'validated_domain_facts','record_count','records','warnings']))
    fail('FLEET_EXPORT_INVALID', 'Unsupported or malformed Manager inventory.', 422);
  for (const row of doc.records) {
    if (!obj(row) || !strictKeys(row, allowedRecords) ||
        (row.state_ref != null && !text(row.state_ref)) ||
        (row.state_commitment != null && !sha.test(row.state_commitment)) ||
        (row.title != null && !text(row.title, 200)) ||
        (row.slug != null && !text(row.slug, 160)) ||
        (row.readiness != null && !text(row.readiness, 80)) ||
        (row.operational_result != null && !OPERATIONAL.has(row.operational_result)) ||
        (row.framework_state_verification != null && !FRAMEWORK.has(row.framework_state_verification)) ||
        (row.discovery != null && (!obj(row.discovery) || !DISCOVERY.has(row.discovery.status))))
      fail('FLEET_EXPORT_INVALID', 'Invalid Manager record or sensitive local path.', 422);
  }
  return doc.records;
}

export function validateManagerAccessPolicy(doc) {
  if (!obj(doc) || doc.format !== MANAGER_POLICY_FORMAT ||
    !strictKeys(doc, ['format','grants']) || !Array.isArray(doc.grants) || doc.grants.length > 1000)
    fail('FLEET_POLICY_INVALID', 'Invalid Manager access policy.', 422);
  const seen = new Set();
  for (const row of doc.grants) {
    if (!obj(row) || !strictKeys(row, ['state_ref','state_commitment','allowed_principals','allowed_roles']) ||
        !text(row.state_ref) || (row.state_commitment != null && !sha.test(row.state_commitment)) ||
        !principals(row.allowed_principals) || !principals(row.allowed_roles))
      fail('FLEET_POLICY_INVALID', 'Invalid Manager access grant.', 422);
    const key = JSON.stringify([row.state_ref,row.state_commitment ?? null]);
    if (seen.has(key)) fail('FLEET_POLICY_INVALID', 'Duplicate Manager access grant.', 422);
    seen.add(key);
  }
  return doc.grants;
}

export function projectManagerInventory(records, grants) {
  // Never join/authorize by slug or title, and never resolve duplicate identities.
  const counts = new Map();
  for (const r of records) if (r.state_ref) counts.set(r.state_ref, (counts.get(r.state_ref) || 0) + 1);
  const policy = new Map(grants.map(g => [JSON.stringify([g.state_ref,g.state_commitment ?? null]), g]));
  const ready = (v) => ({READY:'not_checked', MIGRATE:'not_ready', AUXILIARY:'unavailable',
    'STATE CONFLICT':'blocked', 'IDENTITY COLLISION':'blocked', 'STATE-ONLY':'not_ready'}[v] || 'unknown');
  return records.flatMap(row => {
    if (!row.state_ref || counts.get(row.state_ref) !== 1 || row.identity_collision || row.state_conflict) return [];
    const grant = policy.get(JSON.stringify([row.state_ref,row.state_commitment ?? null]));
    if (!grant || (!grant.allowed_principals.length && !grant.allowed_roles.length)) return [];
    const id = createHash('sha256').update(JSON.stringify([row.state_ref,row.state_commitment ?? null])).digest('hex').slice(0,24);
    return [{id, title: row.title || row.slug || row.state_ref, visibility:'private',
      readiness:ready(row.readiness), availability: row.availability === 'local' ? 'available' : 'unknown',
      allowed_principals: grant.allowed_principals, allowed_roles: grant.allowed_roles,
      state_ref:row.state_ref, ...(row.state_commitment ? {state_commitment:row.state_commitment} : {}),
      ...(row.operational_result ? {operational_result:row.operational_result} : {}),
      ...(row.discovery?.status ? {discovery_status:row.discovery.status} : {}),
      ...(row.framework_state_verification ? {framework_state_verification:row.framework_state_verification} : {}),
      // Manager 0.1 explicitly exports UNDECLARED; do not infer an Arketype classification.
      ...(row.archetype && row.archetype !== 'UNDECLARED' ? {archetype:row.archetype} : {})}];
  });
}
