import { randomBytes, createHmac, timingSafeEqual } from 'node:crypto';
import { validate, fail } from './contracts.mjs';
import { validatePack, compare, hash, canonical, canRead } from './pack.mjs';
import { projectConstellation } from './navigation/projector.mjs';
import { StructuralProfiler } from './navigation/profiler.mjs';
import { buildNavigationPlan, rendererCatalog } from './navigation/planner.mjs';
import { projectAdaptiveNavigation } from './navigation/projection.mjs';
import { increment } from './observability.mjs';
import { versionInfo } from './version.mjs';
import {
  normalizeKristalPolicy,
  evaluatePolicy,
  enforcePolicySet,
} from './integrations/reader-policy.mjs';
export class Engine {
  constructor(
    pack,
    {
      roles = ['public'],
      secret = randomBytes(32),
      maxOperations = 2000000,
      deadlineMs = 3000,
      cacheSize = 64,
    } = {},
  ) {
    this.pack = structuredClone(validatePack(pack));
    pack = this.pack;
    pack.policies = pack.policies.map((p) =>
      p.profile === 'konstellation.kristal-reader.v1' ? normalizeKristalPolicy(p.document) : p,
    );
    this.roles = [...roles].sort(compare);
    this.secret = secret;
    this.limits = { maxOperations, deadlineMs, maxDepth: 3, maxFilters: 32, maxLinks: 16 };
    this.cacheSize = cacheSize;
    this.cache = new Map();
    this.relations = new Map(pack.registry.relations.map((r) => [r.id, r]));
    this.entities = new Map(
      pack.entities.filter((e) => canRead(e, this.roles)).map((e) => [e.id, e]),
    );
    this.sources = new Map(
      pack.sources.filter((s) => canRead(s, this.roles)).map((s) => [s.id, s]),
    );
    this.referencedEntityIds = new Set();
    for (const assertion of pack.assertions) {
      if (this.entities.has(assertion.subject)) this.referencedEntityIds.add(assertion.subject);
      const relation = this.relations.get(assertion.relation);
      if (relation?.valueKind === 'entity' && this.entities.has(assertion.value)) this.referencedEntityIds.add(assertion.value);
    }
    this.policies = new Map(pack.policies.map((p) => [hash(p), p]));
    this.baseContext = {
      datasetRef: hash(pack),
      registryRef: hash(pack.registry),
      executionProfileRef: hash({
        adapter: 'konstellation-reader:1.0.0',
        limits: this.limits,
        canonicalization: 'sorted-keys-json-v1',
      }),
    };
    this.accessRef = hash(this.roles);
    // Structural introspection is computed once from the normalized pack. It is
    // domain-neutral: Kristal-specific affordances emerge from types, relations
    // and assertion topology rather than hard-coded domain names.
    this.profiler = new StructuralProfiler(this.pack);
    this.policyProfilerCache = new Map();
    this.scopeCache = new Map();
  }
  visibleProfiler(context) {
    const key = `${context.readerPolicyRef}|${this.accessRef}`;
    if (this.policyProfilerCache.has(key)) { increment('navigation_profile_cache_total',{result:'hit'}); return this.policyProfilerCache.get(key); }
    increment('navigation_profile_cache_total',{result:'miss'});
    const state = this.scope(context);
    const visibleSourceIds = new Set();
    for (const assertion of state.assertions.values()) {
      for (const id of [...(assertion.sourceRefs || []), ...(assertion.evidenceRefs || []), ...(assertion.provenanceRefs || [])])
        if (this.sources.has(id)) visibleSourceIds.add(id);
    }
    const visibleRelationIds = new Set();
    for (const assertion of state.assertions.values()) {
      visibleRelationIds.add(assertion.relation);
      const relation = this.relations.get(assertion.relation);
      if (relation?.inverseOf) visibleRelationIds.add(relation.inverseOf);
    }
    const visibleEntityTypes = [...new Set([...state.entityIds].map((id) => this.entities.get(id)?.type).filter(Boolean))].sort(compare);
    const scopedPack = {
      ...this.pack,
      registry: {
        ...this.pack.registry,
        entityTypes: visibleEntityTypes,
        relations: this.pack.registry.relations.filter((relation) => visibleRelationIds.has(relation.id)),
      },
      entities: [...state.entityIds].map((id) => this.entities.get(id)).filter(Boolean),
      sources: [...visibleSourceIds].map((id) => this.sources.get(id)).filter(Boolean),
      assertions: [...state.assertions.values()],
      integration: {
        ...(this.pack.integration || {}),
        metadata: {
          ...(this.pack.integration?.metadata || {}),
          structuralSummary: undefined,
        },
      },
    };
    const profiler = new StructuralProfiler(scopedPack, { policyScoped: true, trustStructuralSummary: false });
    this.policyProfilerCache.set(key, profiler);
    return profiler;
  }

  context(
    policyRef = [...this.policies].find(([, p]) => p.support?.available !== false)?.[0] ||
      [...this.policies.keys()][0],
  ) {
    return { ...this.baseContext, readerPolicyRef: policyRef };
  }
  tick(state) {
    if (++state.operations > this.limits.maxOperations)
      fail('BUDGET_EXCEEDED', 'Le budget de calcul est dépassé. Affinez la sélection.', 422);
    if ((state.operations & 255) === 0 && Date.now() > state.deadline)
      fail('TIMEOUT', 'Le calcul a dépassé le délai autorisé.', 503);
  }
  scope(context) {
    for (const [k, v] of Object.entries(this.baseContext))
      if (context?.[k] !== v)
        fail(
          'CONTEXT_UNAVAILABLE',
          'Le corpus, le registre ou le profil enregistré n’est plus disponible.',
          409,
        );
    const policy = this.policies.get(context.readerPolicyRef);
    if (!policy) fail('CONTEXT_UNAVAILABLE', 'Politique de lecture inconnue.', 409);
    if (policy.support?.available === false)
      fail('UNSUPPORTED_POLICY', policy.support.reasons.join(' '), 422);

    const cacheKey = `${context.readerPolicyRef}|${this.accessRef}`;
    const cached = this.scopeCache.get(cacheKey);
    if (cached) {
      increment('policy_scope_cache_total', { result: 'hit' });
      return { ...cached, operations: 0, deadline: Date.now() + this.limits.deadlineMs };
    }
    increment('policy_scope_cache_total', { result: 'miss' });

    const state = {
      policy,
      operations: 0,
      deadline: Date.now() + this.limits.deadlineMs,
      index: new Map(),
      assertions: new Map(),
      entityIds: new Set(),
      assertionsByEntity: new Map(),
      entityIdsByType: new Map(),
    };
    const candidates = [];
    const allowed = (list, value) => list.includes('*') || list.includes(value);
    for (const a of this.pack.assertions) {
      this.tick(state);
      const rel = this.relations.get(a.relation);
      if (
        !canRead(a, this.roles) ||
        !this.entities.has(a.subject) ||
        (rel.valueKind === 'entity' && !this.entities.has(a.value))
      )
        continue;
      if (
        !allowed(policy.statuses, a.status) ||
        !allowed(policy.certainties, a.certainty) ||
        !allowed(policy.validationStatuses, a.validationStatus) ||
        !allowed(policy.validatedAs, a.validatedAs) ||
        !allowed(policy.authorities, a.authority)
      )
        continue;
      if (policy.domain && policy.domain !== a.scope.domain) continue;
      if (
        policy.requireSources &&
        (!a.sourceRefs.length || a.sourceRefs.some((id) => !this.sources.has(id)))
      )
        continue;
      // Never expose provenance or a raw payload referencing access-restricted source metadata.
      if (a.sourceRefs.some((id) => !this.sources.has(id))) continue;
      const evaluated = evaluatePolicy(policy, a, this.pack);
      if (evaluated.visible)
        candidates.push(evaluated.labels?.length ? { ...a, readerLabels: evaluated.labels } : a);
    }
    for (const a of enforcePolicySet(policy, candidates)) {
      const rel = this.relations.get(a.relation);
      state.assertions.set(a.id, a);
      state.entityIds.add(a.subject);
      if (rel.valueKind === 'entity' && this.entities.has(a.value)) state.entityIds.add(a.value);
      const attach = (entityId) => {
        const list = state.assertionsByEntity.get(entityId) || [];
        list.push(a);
        state.assertionsByEntity.set(entityId, list);
      };
      attach(a.subject);
      if (rel.valueKind === 'entity' && this.entities.has(a.value) && a.value !== a.subject) attach(a.value);
      for (const qualifier of a.qualifiers || []) {
        const item = qualifier?.object?.kind === 'item' ? qualifier.object.value : null;
        const qid = item && typeof item === 'object' ? item.external_id || item.id : null;
        if (qid && this.entities.has(qid)) state.entityIds.add(qid);
      }
      const put = (subject, relation, value) => {
        const k = subject + '|' + relation;
        const list = state.index.get(k) || [];
        list.push({ assertion: a, value });
        state.index.set(k, list);
      };
      put(a.subject, a.relation, a.value);
      if (rel.inverseOf) put(a.value, rel.inverseOf, a.subject);
    }
    for (const id of this.entities.keys()) if (!this.referencedEntityIds.has(id)) state.entityIds.add(id);
    for (const id of state.entityIds) {
      const type = this.entities.get(id)?.type;
      if (!type) continue;
      const ids = state.entityIdsByType.get(type) || [];
      ids.push(id);
      state.entityIdsByType.set(type, ids);
    }
    for (const ids of state.entityIdsByType.values()) ids.sort(compare);

    const snapshot = {
      policy: state.policy,
      index: state.index,
      assertions: state.assertions,
      entityIds: state.entityIds,
      assertionsByEntity: state.assertionsByEntity,
      entityIdsByType: state.entityIdsByType,
    };
    this.scopeCache.set(cacheKey, snapshot);
    return { ...snapshot, operations: 0, deadline: Date.now() + this.limits.deadlineMs };
  }
  check(q) {
    validate('query-spec', q);
    for (const [k, v] of Object.entries(this.baseContext))
      if (q.context[k] !== v) fail('CONTEXT_UNAVAILABLE', 'Contexte sauvegardé indisponible.', 409);
    if (!this.policies.has(q.context.readerPolicyRef))
      fail('CONTEXT_UNAVAILABLE', 'Politique indisponible.', 409);

    // Validation is performed against the same policy-scoped snapshot used by
    // evaluation. This prevents an existence oracle where a hidden entity ID or
    // relation behaves differently from a genuinely unknown one.
    const scoped = this.scope(q.context);
    const visibleRelations = new Set();
    for (const assertion of scoped.assertions.values()) {
      visibleRelations.add(assertion.relation);
      const relation = this.relations.get(assertion.relation);
      if (relation?.inverseOf) visibleRelations.add(relation.inverseOf);
    }

    let filters = 0,
      links = 0;
    const walk = (s, depth = 0) => {
      if (depth > 3) fail('BUDGET_EXCEEDED', 'Trois traversées maximum.', 422);
      if (!scoped.entityIdsByType.has(s.entityType))
        fail('TYPE_MISMATCH', 'Type indisponible.');
      for (const id of s.ids || [])
        if (!scoped.entityIds.has(id) || this.entities.get(id)?.type !== s.entityType)
          fail('TYPE_MISMATCH', 'Sélection d’identités indisponible.');
      filters += s.filters.length;
      links += s.links.length;
      const resolve = (id) => {
        const r = this.relations.get(id);
        if (!r || !visibleRelations.has(id)) fail('UNKNOWN_RELATION', 'Relation indisponible.');
        if (!this.relationCapability(id).available)
          fail('UNSUPPORTED_CAPABILITY', this.relationCapability(id).reason, 422);
        if (!r.domain.includes(s.entityType))
          fail('TYPE_MISMATCH', 'Relation incompatible avec le type sélectionné.');
        return r;
      };
      for (const f of s.filters) {
        const r = resolve(f.relation);
        if (!this.relationCapability(r.id).operators.includes(f.op))
          fail('UNSUPPORTED_CAPABILITY', 'Opérateur non pris en charge.');
        for (const v of f.values || []) {
          if (v.kind !== r.valueKind) fail('TYPE_MISMATCH', 'Type de valeur incorrect.');
          if (
            v.kind === 'entity' &&
            (!scoped.entityIds.has(v.id) || this.entities.get(v.id)?.type !== r.range)
          )
            fail('TYPE_MISMATCH', 'Valeur indisponible.');
        }
        if (
          f.op === 'overlaps' &&
          (f.interval.from > f.interval.to ||
            !Number.isSafeInteger(f.interval.from) ||
            !Number.isSafeInteger(f.interval.to))
        )
          fail('INVALID_QUERY', 'Intervalle invalide.');
      }
      for (const l of s.links) {
        const r = resolve(l.relation);
        if (r.valueKind !== 'entity' || l.target.entityType !== r.range)
          fail('TYPE_MISMATCH', 'Pivot incompatible.');
        walk(l.target, depth + 1);
      }
    };
    walk(q.selection);
    if (filters > 32 || links > 16 || Buffer.byteLength(canonical(q)) > 65536)
      fail('BUDGET_EXCEEDED', 'Requête trop grande.', 422);
    return scoped;
  }
  values(id, relation, state) {
    this.tick(state);
    return state.index.get(id + '|' + relation) || [];
  }
  testFilter(f, entries, state) {
    const matches = entries.filter((e) => {
      this.tick(state);
      if (f.op === 'in' || f.op === 'none_of')
        return f.values.some((v) => (v.kind === 'entity' ? v.id : v.value) === e.value);
      if (f.op === 'overlaps') {
        const v = e.value;
        return (
          v.startMax !== null &&
          v.endMin !== null &&
          v.startMax <= f.interval.to &&
          v.endMin >= f.interval.from
        );
      }
      return true;
    });
    if (f.op === 'missing_in_view' || f.op === 'none_of')
      return { ok: matches.length === 0, entries: [] };
    return { ok: matches.length > 0, entries: matches.slice(0, 1) };
  }
  witness(path, a, kind) {
    return {
      criterionPath: path,
      kind: kind || (a?.ruleRef ? 'derivation' : 'assertion'),
      assertionRefs: a ? [a.id] : [],
      sourceRefs: a ? a.sourceRefs : [],
      ...(a?.ruleRef ? { ruleRef: a.ruleRef } : {}),
    };
  }
  match(id, s, state, path = '/selection') {
    this.tick(state);
    const entity = this.entities.get(id);
    if (!entity || !state.entityIds.has(id) || entity.type !== s.entityType || (s.ids && !s.ids.includes(id))) return null;
    const witnesses = [];
    for (let i = 0; i < s.filters.length; i++) {
      const f = s.filters[i],
        found = this.testFilter(f, this.values(id, f.relation, state), state);
      if (!found.ok) return null;
      witnesses.push(
        this.witness(
          `${path}/filters/${i}`,
          found.entries[0]?.assertion,
          found.entries.length ? undefined : 'absence_in_view',
        ),
      );
    }
    for (let i = 0; i < s.links.length; i++) {
      const l = s.links[i];
      let matched = false;
      for (const e of this.values(id, l.relation, state)) {
        this.tick(state);
        const nested = this.match(e.value, l.target, state, `${path}/links/${i}/target`);
        if (nested) {
          witnesses.push(this.witness(`${path}/links/${i}`, e.assertion), ...nested);
          matched = true;
          break;
        }
      }
      if (!matched) return null;
    }
    return witnesses;
  }
  all(q, state) {
    const rows = [];
    for (const id of state.entityIdsByType?.get(q.selection.entityType) || [...state.entityIds].sort(compare)) {
      const witnesses = this.match(id, q.selection, state);
      if (witnesses) rows.push({ entityId: id, witnesses, witnessesComplete: true });
    }
    return rows;
  }
  identity(q) {
    return hash({ context: q.context, selection: q.selection });
  }
  sign(payload) {
    const body = Buffer.from(canonical(payload)).toString('base64url');
    return body + '.' + createHmac('sha256', this.secret).update(body).digest('base64url');
  }
  cursor(token, key) {
    try {
      if (typeof token !== 'string' || token.length > 2048) throw Error();
      const [body, sig, ...rest] = token.split('.');
      if (rest.length) throw Error();
      const expected = createHmac('sha256', this.secret).update(body).digest();
      const actual = Buffer.from(sig, 'base64url');
      if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) throw Error();
      const p = JSON.parse(Buffer.from(body, 'base64url'));
      if (p.key !== key || !Number.isSafeInteger(p.offset) || p.offset < 0) throw Error();
      return p.offset;
    } catch {
      fail('CURSOR_MISMATCH', 'Curseur expiré ou incompatible avec cette requête.', 409);
    }
  }
  evaluate(q, state = null) {
    const key = hash({ q, access: this.accessRef });
    let computed = this.cache.get(key);
    if (computed) increment('query_cache_total',{result:'hit'});
    if (!computed) {
      increment('query_cache_total',{result:'miss'});
      state ||= this.scope(q.context);
      computed = { rows: this.all(q, state), state };
      if (this.cacheSize) {
        this.cache.set(key, computed);
        while (this.cache.size > this.cacheSize) this.cache.delete(this.cache.keys().next().value);
      }
    }
    return { key, computed };
  }
  query(q, cursor = null) {
    this.check(q);
    const maxLimit = this.policies.get(q.context.readerPolicyRef)?.document?.query?.max_limit;
    if (maxLimit && q.pageSize > maxLimit)
      fail('POLICY_LIMIT', 'Taille de page supérieure à la politique.', 422);
    const { key, computed } = this.evaluate(q);
    const offset = cursor ? this.cursor(cursor, key) : 0;
    const rows = computed.rows.slice(offset, offset + q.pageSize);
    const assertionIds = new Set(rows.flatMap((r) => r.witnesses.flatMap((w) => w.assertionRefs)));
    const view = (a) => this.viewAssertion(a, computed.state);
    return {
      schemaVersion: '0.2',
      context: q.context,
      queryIdentity: this.identity(q),
      evaluation: 'complete',
      rows,
      assertions: [...assertionIds].map((id) => view(computed.state.assertions.get(id))),
      nextCursor:
        offset + q.pageSize < computed.rows.length
          ? this.sign({ key, offset: offset + q.pageSize })
          : null,
      total: { kind: 'exact', value: computed.rows.length },
    };
  }
  viewAssertion(a, state) {
    // Imported raw payloads remain in the pack for audit; only policy-visible,
    // normalized metadata crosses the API.
    const { upstreamPayload, roles, conflictsWith, derivedFrom, evidenceRefs, provenanceRefs, supersedes, ...safe } = a;
    const visibleRef = (id) => state.assertions.has(id) || this.sources.has(id);
    return {
      assertionRef: a.id,
      upstreamContractRef: a.upstreamContractRef || 'konstellation.normalized-assertion:0.3',
      payload: {
        ...safe,
        derivedFrom: (derivedFrom || []).filter(visibleRef),
        evidenceRefs: (evidenceRefs || []).filter(visibleRef),
        provenanceRefs: (provenanceRefs || []).filter(visibleRef),
        supersedes: (supersedes || []).filter((id) => state.assertions.has(id)),
        conflictsWith: (conflictsWith || []).filter((id) => state.assertions.has(id)),
      },
    };
  }
  facets(q, ids) {
    this.check(q);
    if (!Array.isArray(ids) || ids.length > 32 || ids.some((id) => typeof id !== 'string'))
      fail('INVALID_QUERY', 'Liste de facettes invalide.');
    const state = this.scope(q.context),
      schema = this.visibleSchema(q.context),
      result = {};
    for (const id of ids) {
      const r = this.relations.get(id);
      if (!r || !schema.relationIds.has(id) || !r.domain.includes(q.selection.entityType))
        fail('UNKNOWN_RELATION', 'Facette indisponible.');
      if (!this.relationCapability(id).available) {
        result[id] = this.relationCapability(id);
        continue;
      }
      const s = { ...q.selection, filters: q.selection.filters.filter((f) => f.relation !== id) },
        counts = new Map();
      let present = 0,
        missing = 0;
      for (const eid of state.entityIdsByType?.get(q.selection.entityType) || state.entityIds) {
        if (!this.match(eid, s, state)) continue;
        const entries = this.values(eid, id, state);
        if (entries.length) present++;
        else missing++;
        const seen = new Set();
        for (const e of entries) {
          this.tick(state);
          const k = canonical(e.value);
          if (!seen.has(k)) {
            seen.add(k);
            const x = counts.get(k) || { value: e.value, count: 0 };
            x.count++;
            counts.set(k, x);
          }
        }
      }
      result[id] = {
        available: true,
        present,
        missing,
        kind: 'exact',
        values: [...counts.values()].sort((a, b) =>
          compare(canonical(a.value), canonical(b.value)),
        ),
      };
    }
    return result;
  }
  entity(id, context) {
    const state = this.scope(context);
    const e = this.entities.get(id);
    if (!e || !state.entityIds.has(id)) fail('NOT_FOUND', 'Entité indisponible.', 404);
    const assertions = (state.assertionsByEntity.get(id) || []).map((a) => this.viewAssertion(a, state));
    return {
      entity: this.publicEntity(e),
      assertions,
      sources: [...new Set(assertions.flatMap((a) => a.payload.sourceRefs))].map((id) =>
        this.publicSource(this.sources.get(id)),
      ),
    };
  }
  constellation(request, lenses) {
    if (!request || typeof request !== 'object' || Array.isArray(request))
      fail('INVALID_QUERY', 'Requête de constellation invalide.');
    const state = this.scope(request.context);
    const schema = this.visibleSchema(request.context);
    return projectConstellation(this, state, this.visibleLenses(lenses, schema), request);
  }
  navigationPlan(request, lenses) {
    if (!request || typeof request !== 'object' || Array.isArray(request) || !request.query)
      fail('INVALID_QUERY', 'Contexte de navigation invalide.');
    this.check(request.query);
    const visibleState = this.scope(request.query.context);
    const scopedLenses = this.visibleLenses(lenses, this.visibleSchema(request.query.context));
    const lens = scopedLenses.find((item) => item.id === request.lensRef) || null;
    if (!lens || lens.rootType !== request.query.selection.entityType) fail('INVALID_QUERY', 'Lens indisponible ou incompatible avec la sélection.', 422);
    const selectedEntity = request.selectedEntityId ? this.entities.get(request.selectedEntityId) : null;
    if (request.selectedEntityId && (!selectedEntity || !visibleState.entityIds.has(request.selectedEntityId)))
      fail('NOT_FOUND', 'Entité de navigation indisponible.', 404);
    const profiler = this.visibleProfiler(request.query.context);
    const evaluated = selectedEntity ? null : this.evaluate(request.query, visibleState).computed;
    const resultEntityIds = evaluated ? evaluated.rows.slice(0, 512).map((row) => row.entityId) : null;
    const resultSize = Number.isFinite(request.resultSize) ? request.resultSize : evaluated?.rows.length ?? null;
    return validate('navigation-plan', buildNavigationPlan({ profiler, query: request.query, lens, selectedEntity, resultSize, resultEntityIds }));
  }
  navigationProjection(request, lenses) {
    if (!request?.query?.context) fail('INVALID_QUERY', 'Contexte de navigation invalide.');
    const scopedLenses = this.visibleLenses(lenses, this.visibleSchema(request.query.context));
    return projectAdaptiveNavigation(this, request, scopedLenses);
  }
  evidence(ids, context) {
    if (!Array.isArray(ids) || ids.length > 100 || ids.some((id) => typeof id !== 'string'))
      fail('INVALID_QUERY', 'Références invalides.');
    const state = this.scope(context);
    return ids.map((id) => {
      const a = state.assertions.get(id);
      if (!a) fail('NOT_FOUND', 'Assertion indisponible.', 404);
      return this.viewAssertion(a, state);
    });
  }
  publicEntity(e) {
    const { roles, ...rest } = e;
    return rest;
  }
  publicSource(s) {
    const { roles, ...rest } = s;
    return rest;
  }
  relationCapability(id) {
    return (
      this.pack.integration?.capabilities?.relations?.[id] || {
        available: true,
        operators: this.relations.get(id)?.operators || [],
        reason: null,
      }
    );
  }
  migrateExplorationState(input, lenses) {
    validate('exploration-state', input);
    const ensureLensVisible = (state) => {
      const scopedLenses = this.visibleLenses(lenses, this.visibleSchema(state.query.context));
      const lensOk = scopedLenses.some((lens) => lens.id === state.lensRef && lens.rootType === state.query.selection.entityType) ||
        state.lensRef === `type:${state.query.selection.entityType}` && scopedLenses.some((lens) => lens.rootType === state.query.selection.entityType);
      if (!lensOk) fail('INVALID_QUERY', 'Lens indisponible.');
    };
    if (input.schemaVersion === '1.0') {
      ensureLensVisible(input);
      return { migrated: false, state: input, warnings: [] };
    }
    const recipeId = input.navigation?.recipeId || (input.view === 'constellation' || input.view === 'graph' ? 'constellation' : input.view === 'table' ? 'table' : 'catalogue');
    const mode = input.navigation?.mode || 'adaptive';
    const state = {
      schemaVersion: '1.0',
      query: input.query,
      lensRef: input.lensRef,
      readerPolicyRef: input.query.context.readerPolicyRef,
      focus: input.selectedEntityId ? { kind: 'entity', id: input.selectedEntityId } : null,
      navigation: { mode, recipeId },
      history: {},
    };
    ensureLensVisible(state);
    validate('exploration-state', state);
    return { migrated: true, state, warnings: ['ExplorationState 0.2 migré vers 1.0 sans modifier QuerySpec.'] };
  }

  visibleSchema(context) {
    const state = this.scope(context);
    const relationIds = new Set();
    const qualifierIds = new Set();
    for (const assertion of state.assertions.values()) {
      relationIds.add(assertion.relation);
      const relation = this.relations.get(assertion.relation);
      if (relation?.inverseOf) relationIds.add(relation.inverseOf);
      for (const qualifier of assertion.qualifiers || []) {
        const id = qualifier?.predicate?.external_id || qualifier?.predicate?.id;
        if (id) qualifierIds.add(id);
      }
    }
    const entityTypes = [...new Set([...state.entityIds].map((id) => this.entities.get(id)?.type).filter(Boolean))].sort(compare);
    const visibleTypeSet = new Set(entityTypes);
    const relations = this.pack.registry.relations.filter((relation) => relationIds.has(relation.id));
    const registry = { ...this.pack.registry, entityTypes, relations };
    return { state, relationIds, qualifierIds, visibleTypeSet, registry };
  }

  visibleLenses(lenses, schema) {
    const { relationIds, qualifierIds, visibleTypeSet } = schema;
    return (lenses || []).filter((lens) => visibleTypeSet.has(lens.rootType)).map((lens) => {
      const constellation = lens.constellation ? {
        ...lens.constellation,
        groups: (lens.constellation.groups || []).map((group) => {
          const allowed = group.source.kind === 'relations' ? relationIds : qualifierIds;
          const ids = group.source.ids.filter((id) => allowed.has(id));
          return ids.length ? { ...group, source: { ...group.source, ids } } : null;
        }).filter(Boolean),
      } : undefined;
      return {
        ...lens,
        facets: (lens.facets || []).filter((facet) => relationIds.has(facet.relation)),
        pivots: (lens.pivots || []).filter((id) => relationIds.has(id)),
        ...(constellation ? { constellation } : {}),
      };
    });
  }

  bootstrap(lenses, context = this.context()) {
    const visibleProfiler = this.visibleProfiler(context);
    const catalog = validate('renderer-registry', rendererCatalog());
    const schema = this.visibleSchema(context);
    const visibleLenses = this.visibleLenses(lenses, schema);
    return {
      version: versionInfo().version,
      title: this.pack.title,
      description: this.pack.description,
      synthetic: this.pack.synthetic,
      ...(this.pack.integration?.adapter === 'kristal-local-v10' ? {
        readingNotice: {
          heading: 'Lecture locale dérivée',
          text: this.pack.integration.viewKind === 'derived-node-edge-graph'
            ? 'Exploration d’un graphe dérivé non canonique. Les correspondances et assertions restent attribuées, non vérifiées comme vérités du domaine.'
            : 'Exploration structurelle des états et artefacts déclarés, sans qualification de leur contenu.'
        }
      } : {}),
      presentation: {typeLabels: this.pack.integration?.presentation?.typeLabels || {},
        featuredTypes: this.pack.integration?.presentation?.featuredTypes || []},
      context,
      registry: schema.registry,
      lenses: visibleLenses,
      entities: [...schema.state.entityIds].map((id) => this.publicEntity(this.entities.get(id))).filter(Boolean),
      policies: [...this.policies].map(([ref, p]) => ({
        ref,
        id: p.id,
        label: p.label,
        description: p.description,
        available: p.support?.available !== false,
        reasons: p.support?.reasons || [],
        defaultPageSize: Math.min(
          24,
          p.document?.query?.default_limit || 24,
          p.document?.query?.max_limit || 100,
        ),
        maxPageSize: Math.min(100, p.document?.query?.max_limit || 100),
      })),
      limits: this.limits,
      structuralProfile: visibleProfiler.global,
      navigation: {
        schemaVersion: '1.0',
        adaptive: true,
        vocabulary: 'navigation-affordances',
        canonicalTruth: 'upstream-kristal',
        rendererCatalog: catalog,
      },
      capabilities: {
        filters: true,
        pivots: true,
        evidence: true,
        adaptiveNavigation: true,
        sa: false,
        packAdapter: this.pack.integration?.adapter || 'normalized-json-v1',
        relations: Object.fromEntries(
          [...schema.relationIds].filter((id) => this.relations.has(id)).map((id) => [id, this.relationCapability(id)]),
        ),
      },
    };
  }
}
