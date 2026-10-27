import { upstream } from './upstream.mjs';
import { fail } from '../contracts.mjs';
import { canonical } from '../pack.mjs';
const own = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
const contains = (list, value) => list.includes(value);
const partial = (value, pattern) =>
  Object.entries(pattern).every(([k, v]) => v === null || value?.[k] === v);
const authorityId = (a) => (typeof a === 'string' ? a : a?.authority_channel_id);
export function policySupport(document) {
  upstream('policy', document);
  const reasons = [],
    p = document.policy;
  if (p.scope_filter?.language_priority?.length || p.scope_filter?.jurisdiction_priority?.length)
    reasons.push('Priorités linguistiques ou juridictionnelles non prises en charge.');
  if (document.rendering?.max_summary_length)
    reasons.push('Limite de résumé non prise en charge par le profil structuré.');
  if (document.extensions && Object.keys(document.extensions).length)
    reasons.push('Extensions de politique non interprétées.');
  if (document.rendering?.show_labels === false)
    reasons.push('Les labels épistémiques doivent rester visibles.');
  const query = document.query || {};
  if (query.default_ordering && !['stable'].includes(query.default_ordering))
    reasons.push('Ordre épistémique non pris en charge : ' + query.default_ordering);
  if (query.conflict_behavior === 'authority_precedence')
    reasons.push('La précédence d’autorité requiert un profil de classement explicite.');
  if (document.federation?.composition_strategy === 'authority_precedence')
    reasons.push('Composition par précédence non déclarée.');
  for (const r of p.custom_rules || []) {
    if (!['assertion'].includes(r.target || 'assertion'))
      reasons.push('Cible de règle non prise en charge : ' + r.rule_id);
    if (
      !r.condition ||
      !Object.keys(r.condition).every((k) => ['field', 'op', 'value'].includes(k)) ||
      !['eq', 'in', 'exists'].includes(r.condition.op) ||
      ![
        'status',
        'certainty',
        'validationStatus',
        'validatedAs',
        'authority',
        'recognitionStatus',
        'artifactStatus',
        'scope.domain',
        'scope.language',
        'scope.jurisdiction',
      ].includes(r.condition.field)
    )
      reasons.push('Condition de règle non prise en charge : ' + r.rule_id);
  }
  // Profiles with caller choice/review are supported through an explicit hold, never an automatic choice.
  return { available: reasons.length === 0, reasons };
}
export function normalizeKristalPolicy(doc) {
  const support = policySupport(doc);
  return {
    id: doc.reader_policy_id,
    label: doc.name || doc.reader_policy_id,
    description: doc.description || doc.mode,
    profile: 'konstellation.kristal-reader.v1',
    showLabels: true,
    statuses: ['*'],
    certainties: ['*'],
    validationStatuses: ['*'],
    validatedAs: ['*'],
    authorities: ['*'],
    requireSources: false,
    document: doc,
    support,
  };
}
export function evaluatePolicy(wrapper, a, pack) {
  if (wrapper.profile !== 'konstellation.kristal-reader.v1') return { visible: true, labels: [] };
  const d = wrapper.document,
    p = d.policy,
    labels = [],
    m = pack.integration?.metadata || {};
  if (!wrapper.support.available)
    fail('UNSUPPORTED_POLICY', wrapper.support.reasons.join(' '), 422);
  const unavailable = (reason) => fail('POLICY_UNEVALUABLE', reason, 422);
  if (d.offline?.allow_offline_use === false)
    return unavailable('Cette politique interdit l’utilisation hors ligne.');
  if (d.offline?.require_local_integrity_check !== false && !m.integrityVerified)
    return unavailable('Vérification locale d’intégrité manquante.');
  if (d.offline?.require_signature_check && !m.signaturesVerified)
    return unavailable('Signature vérifiée requise.');
  if (m.stale && d.offline?.allow_stale_packs !== true)
    return unavailable('Le pack est signalé périmé.');
  if (d.offline?.max_staleness_seconds !== undefined) {
    if (!Number.isFinite(m.stalenessSeconds))
      return unavailable('Âge de révocation du pack non attesté.');
    if (m.stalenessSeconds > d.offline.max_staleness_seconds) return { visible: false };
  }
  if (d.mode === 'reference_only' && a.artifactStatus !== 'reference') return { visible: false };
  if (d.mode === 'validated_only' && a.validationStatus !== 'validated') return { visible: false };
  if (d.mode === 'high_certainty_only' && !['high', 'established'].includes(a.certainty))
    return { visible: false };
  const checks = [
    ['artifact_statuses', a.artifactStatus || m.artifactStatus],
    ['assertion_statuses', a.status],
    ['validation_statuses', a.validationStatus],
    ['recognition_statuses', a.recognitionStatus],
    ['certainty_levels', a.certainty],
    ['validated_as', a.validatedAs],
  ];
  const defaultBlocked = {
    artifact_statuses: ['revoked'],
    assertion_statuses: ['retracted'],
    validation_statuses: ['revoked'],
    recognition_statuses: ['revoked'],
  };
  for (const [key, value] of checks) {
    const allowed = p['allowed_' + key],
      blocked = p['blocked_' + key] ?? defaultBlocked[key] ?? [];
    if (value === undefined && (allowed?.length || blocked.length))
      return unavailable('Métadonnée requise manquante : ' + key);
    if (contains(blocked, value)) return { visible: false };
    // Explicit empty allow lists deny everything. Omitted lists add no restriction.
    if (own(p, 'allowed_' + key) && !contains(allowed, value)) return { visible: false };
  }
  const flags = [
    [
      'include_disputed',
      a.status === 'disputed' ||
        a.validationStatus === 'disputed' ||
        a.recognitionStatus === 'disputed',
    ],
    ['include_rejected', a.status === 'rejected' || a.validationStatus === 'rejected'],
    [
      'include_revoked',
      a.artifactStatus === 'revoked' ||
        a.validationStatus === 'revoked' ||
        a.recognitionStatus === 'revoked',
    ],
    ['include_deprecated', a.artifactStatus === 'deprecated'],
    ['include_fictional', a.validatedAs === 'fictional_corpus'],
    ['include_mythological', a.validatedAs === 'mythological_corpus'],
    ['include_symbolic', a.validatedAs === 'symbolic_model'],
    ['include_speculative', a.certainty === 'speculative'],
    ['include_unknown_certainty', a.certainty === 'unknown'],
  ];
  for (const [flag, applies] of flags) if (applies && p[flag] !== true) return { visible: false };
  const af = p.authority_filter || {};
  if ((af.blocked_authority_channels || []).map(authorityId).includes(a.authority))
    return { visible: false };
  if (
    own(af, 'allowed_authority_channels') &&
    !af.allowed_authority_channels.map(authorityId).includes(a.authority)
  )
    return { visible: false };
  if (a.recognitionStatus === 'revoked' && af.allow_revoked_authorities !== true)
    return { visible: false };
  if (
    a.recognitionStatus === 'conditionally_recognized' &&
    af.allow_conditionally_recognized_authorities !== true
  )
    return { visible: false };
  if (
    af.allow_unrecognized_authority_channels !== true &&
    !['recognized', 'conditionally_recognized'].includes(a.recognitionStatus)
  )
    return { visible: false };
  if (p.require_authority_channel && (!a.authority || a.authority === 'authority:unspecified'))
    return unavailable('Autorité requise.');
  if (p.require_traceability !== false && !(a.sourceRefs?.length || a.provenanceRefs?.length))
    return unavailable('Traçabilité requise.');
  if (p.require_evidence && !a.evidenceRefs?.length) return unavailable('Evidence requise.');
  if (p.require_validation_policy_ref && !a.validationPolicyRef)
    return unavailable('Politique de validation requise.');
  if (d.scope && !partial(a.scope, d.scope)) return { visible: false };
  const sf = p.scope_filter || {};
  if (
    sf.blocked_domains?.includes(a.scope.domain) ||
    (sf.blocked_scopes || []).some((s) => partial(a.scope, s))
  )
    return { visible: false };
  if (own(sf, 'allowed_domains') && !sf.allowed_domains.includes(a.scope.domain))
    return { visible: false };
  if (own(sf, 'allowed_scopes') && !sf.allowed_scopes.some((s) => partial(a.scope, s)))
    return { visible: false };
  const rev = d.revocation || {};
  if (
    (rev.exclude_revoked_artifacts !== false && a.artifactStatus === 'revoked') ||
    (rev.exclude_revoked_assertions !== false && a.validationStatus === 'revoked') ||
    (rev.exclude_revoked_authority_channels !== false && a.recognitionStatus === 'revoked')
  )
    return { visible: false };
  if (rev.exclude_revoked_keys !== false && m.revokedKeys === true) return { visible: false };
  if (d.lineage?.require_lineage && !a.lineage) return unavailable('Lineage requis.');
  if (d.lineage?.allow_forks === false && a.lineage?.isFork) return { visible: false };
  if (
    d.lineage?.allow_unrecognized_forks !== true &&
    a.lineage?.isFork &&
    a.lineage?.recognized !== true
  )
    return { visible: false };
  const fed = d.federation || {};
  if (m.federations?.length) {
    if (fed.allow_federated_sources === false) return { visible: false };
    const id = (x) => x.artifact_id || x.id || x.uri;
    if ((fed.blocked_federations || []).some((x) => m.federations.includes(id(x))))
      return { visible: false };
    if (
      own(fed, 'allowed_federations') &&
      m.federations.some((x) => !fed.allowed_federations.map(id).includes(x))
    )
      return { visible: false };
  }
  if (fed.allow_disagreement === false && (a.conflictsWith?.length || a.status === 'disputed'))
    return { visible: false };
  for (const rule of p.custom_rules || []) {
    const c = rule.condition,
      v = c.field.split('.').reduce((x, k) => x?.[k], a);
    const matches =
      c.op === 'exists'
        ? v !== undefined
        : c.op === 'eq'
          ? canonical(v) === canonical(c.value)
          : Array.isArray(c.value) && c.value.some((x) => canonical(x) === canonical(v));
    if (!matches) continue;
    if (rule.effect === 'block' || rule.effect === 'downgrade_visibility')
      return { visible: false };
    if (['require_user_choice', 'require_review'].includes(rule.effect))
      fail('POLICY_REVIEW_REQUIRED', rule.description || rule.rule_id, 422);
    if (rule.effect === 'label') labels.push(rule.label || rule.rule_id);
    // allow never overrides mandatory exclusions or denied access.
  }
  return { visible: true, labels };
}
export function enforcePolicySet(wrapper, assertions) {
  if (wrapper.profile !== 'konstellation.kristal-reader.v1') return assertions;
  const q = wrapper.document.query || {};
  if (
    q.allow_cross_scope_queries !== true &&
    new Set(assertions.map((a) => canonical(a.scope))).size > 1
  )
    fail('POLICY_SCOPE_REQUIRED', 'Cette politique exige une portée unique.', 422);
  if (
    q.allow_cross_authority_queries !== true &&
    new Set(assertions.map((a) => a.authority)).size > 1
  )
    fail('POLICY_AUTHORITY_REQUIRED', 'Cette politique exige une autorité unique.', 422);
  const ids = new Set(assertions.map((a) => a.id));
  const conflict = (a) =>
    (a.conflictsWith || []).some((id) => ids.has(id)) || a.status === 'disputed';
  if (q.conflict_behavior === 'require_reader_choice' && assertions.some(conflict))
    fail(
      'POLICY_REVIEW_REQUIRED',
      'La politique requiert un choix explicite face à une divergence.',
      422,
    );
  if (q.conflict_behavior === 'exclude_conflict') return assertions.filter((a) => !conflict(a));
  if (q.conflict_behavior === 'mark_disputed')
    return assertions.map((a) =>
      conflict(a) ? { ...a, readerLabels: [...(a.readerLabels || []), 'disputed_in_view'] } : a,
    );
  return assertions;
}
