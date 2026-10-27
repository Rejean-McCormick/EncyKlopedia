import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { ROOT, validate, fail } from './contracts.mjs';
export const compare = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
export function canonical(x) {
  if (Array.isArray(x)) return '[' + x.map(canonical).join(',') + ']';
  if (x && typeof x === 'object')
    return (
      '{' +
      Object.keys(x)
        .sort(compare)
        .map((k) => JSON.stringify(k) + ':' + canonical(x[k]))
        .join(',') +
      '}'
    );
  return JSON.stringify(x);
}
export const hash = (x) => 'sha256:' + createHash('sha256').update(canonical(x)).digest('hex');
export const readJson = (p) => JSON.parse(fs.readFileSync(p, 'utf8'));
export const canRead = (item, roles) => !item.roles || item.roles.some((r) => roles.includes(r));
const sid = (x) => typeof x === 'string' && /^[a-zA-Z][a-zA-Z0-9_.:-]*$/.test(x);
function need(condition, message) {
  if (!condition) fail('INVALID_PACK', message);
}
export function validatePack(pack) {
  need(
    pack &&
      pack.schemaVersion === '0.3' &&
      Array.isArray(pack.entities) &&
      Array.isArray(pack.assertions) &&
      Array.isArray(pack.policies) &&
      pack.policies.length > 0,
    'Unsupported pack structure',
  );
  validate('relation-registry', pack.registry);
  if (pack.navigationHints) validate('navigation-hints', pack.navigationHints);
  need(
    typeof pack.title === 'string' &&
      typeof pack.description === 'string' &&
      typeof pack.synthetic === 'boolean',
    'Pack metadata required',
  );
  const types = new Set(pack.registry.entityTypes),
    relations = new Map(pack.registry.relations.map((r) => [r.id, r]));
  need(relations.size === pack.registry.relations.length, 'Duplicate relation IDs');
  const rolesValid = (x) =>
    !x.roles || (Array.isArray(x.roles) && x.roles.length > 0 && x.roles.every(sid));
  for (const r of relations.values()) {
    need(
      r.domain.every((t) => types.has(t)),
      'Invalid relation domain',
    );
    if (r.valueKind === 'entity') need(types.has(r.range), 'Invalid entity range');
    if (r.inverseOf) {
      const inv = relations.get(r.inverseOf);
      need(
        inv && inv.inverseOf === r.id && inv.range === r.domain[0] && inv.domain.includes(r.range),
        'Invalid inverse relation',
      );
    }
  }
  const entities = new Map();
  for (const e of pack.entities) {
    need(
      sid(e.id) &&
        types.has(e.type) &&
        typeof e.label === 'string' &&
        e.label.length <= 300 &&
        rolesValid(e) &&
        !entities.has(e.id),
      'Invalid or duplicate entity',
    );
    entities.set(e.id, e);
  }
  need(Array.isArray(pack.sources), 'Sources required');
  const sources = new Set();
  for (const s of pack.sources) {
    need(
      sid(s.id) && typeof s.title === 'string' && rolesValid(s) && !sources.has(s.id),
      'Invalid source',
    );
    sources.add(s.id);
  }
  const assertions = new Set();
  for (const a of pack.assertions) {
    need(
      sid(a.id) && !assertions.has(a.id) && entities.has(a.subject) && rolesValid(a),
      'Invalid assertion identity',
    );
    assertions.add(a.id);
    const r = relations.get(a.relation);
    need(r && r.domain.includes(entities.get(a.subject).type), 'Assertion domain mismatch');
    if (r.valueKind === 'entity')
      need(
        entities.has(a.value) && entities.get(a.value).type === r.range,
        'Assertion range mismatch',
      );
    if (r.valueKind === 'string') need(typeof a.value === 'string', 'String value required');
    if (r.valueKind === 'integer') need(Number.isSafeInteger(a.value), 'Integer required');
    if (r.valueKind === 'interval') {
      need(
        a.value &&
          ['startMin', 'startMax', 'endMin', 'endMax'].every(
            (k) => a.value[k] === null || Number.isSafeInteger(a.value[k]),
          ),
        'Interval bounds required',
      );
      const v = a.value;
      need(
        (v.startMin === null || v.startMax === null || v.startMin <= v.startMax) &&
          (v.endMin === null || v.endMax === null || v.endMin <= v.endMax) &&
          (v.startMin === null || v.endMax === null || v.startMin <= v.endMax),
        'Inconsistent interval',
      );
      need(
        typeof a.ruleRef === 'string' && Array.isArray(a.derivedFrom),
        'Derived interval needs rule and input references',
      );
    }
    need(
      [
        'hypothesis',
        'claimed',
        'sourced',
        'disputed',
        'reviewed',
        'validated',
        'rejected',
        'retracted',
        'superseded',
        'unspecified',
      ].includes(a.status),
      'Assertion status required',
    );
    need(
      typeof a.certainty === 'string' &&
        typeof a.validationStatus === 'string' &&
        typeof a.validatedAs === 'string' &&
        typeof a.authority === 'string' &&
        a.scope &&
        typeof a.scope.domain === 'string',
      'Epistemic metadata required',
    );
    need(
      Array.isArray(a.sourceRefs) && a.sourceRefs.every((s) => sources.has(s)),
      'Unknown source',
    );
  }
  const policyIds = new Set();
  for (const p of pack.policies) {
    const allowedKeys = new Set([
      'id',
      'label',
      'description',
      'profile',
      'showLabels',
      'statuses',
      'certainties',
      'validationStatuses',
      'validatedAs',
      'authorities',
      'requireSources',
      'domain',
      ...(p.profile === 'konstellation.kristal-reader.v1' ? ['document', 'support'] : []),
    ]);
    need(
      Object.keys(p).every((k) => allowedKeys.has(k)),
      'Unsupported policy field: refusing to ignore visibility rules',
    );
    need(sid(p.id) && !policyIds.has(p.id) && typeof p.label === 'string', 'Policy identity');
    policyIds.add(p.id);
    need(
      ['konstellation.normalized-reader.v1', 'konstellation.kristal-reader.v1'].includes(
        p.profile,
      ) && p.showLabels === true,
      'Unsupported policy profile',
    );
    for (const k of ['statuses', 'certainties', 'validationStatuses', 'validatedAs', 'authorities'])
      need(
        Array.isArray(p[k]) && p[k].every((x) => typeof x === 'string'),
        'Explicit policy lists required',
      );
    need(typeof p.requireSources === 'boolean', 'requireSources must be explicit');
  }
  return pack;
}
export function loadPack(file) {
  if (!file) file = process.env.KONSTELLATION_PACK || path.join(ROOT, 'data/demo.pack.json');
  return validatePack(readJson(file));
}
