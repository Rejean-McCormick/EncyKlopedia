import { upstream, fetchJson, serviceUrl } from './upstream.mjs';
import { fail } from '../contracts.mjs';
import { hash } from '../pack.mjs';
const semantic = (id) => (id.includes(':') ? id : 'konstellation-entity:' + id);
export function buildCommunicationRequest(
  engine,
  { query, cursor = null, entityId = null, action = 'page', language = 'fr', locale = 'fr-CA' },
  config = {},
) {
  if (!['query', 'page', 'entity'].includes(action))
    fail('INVALID_QUERY', 'Action de communication inconnue.');
  if (typeof language !== 'string' || language.length < 2 || typeof locale !== 'string')
    fail('INVALID_QUERY', 'Langue invalide.');
  engine.check(query);
  engine.scope(query.context);
  const nodes = [],
    statements = [],
    obligations = [];
  let sequence = 0;
  const node = (kind, fields) => {
    const id = 'n' + ++sequence;
    nodes.push({ id, kind, ...fields });
    return id;
  };
  const literal = (value, datatype = 'string') => node('literal', { value, datatype });
  const entity = (id) =>
    node('entity_ref', {
      external_ref: semantic(id),
      labels: { [language]: engine.entities.get(id)?.label || id },
    });
  const concept = (ref) => node('concept_ref', { concept_ref: ref });
  const statement = (predicate, args, sources = []) => {
    const id = 's' + ++sequence;
    statements.push({
      id,
      predicate_ref: 'konstellation:' + predicate,
      arguments: Object.entries(args).map(([role, value_id]) => ({
        role_ref: 'konstellation-role:' + role,
        value_id,
      })),
      polarity: 'positive',
      source_refs: sources,
    });
    return id;
  };
  const obligation = (refs, sources = []) =>
    obligations.push({
      obligation_id: 'o' + ++sequence,
      semantic_refs: refs,
      force: 'PRESENT',
      ordering: 'FIXED',
      source_refs: sources,
    });
  const term = (kind, value) =>
    kind === 'entity'
      ? entity(value)
      : kind === 'integer'
        ? node('quantity', { value })
        : kind === 'interval'
          ? node('temporal', { temporal_kind: 'interval', value })
          : literal(value);
  function selection(s, path) {
    const id = node('entity_ref', { external_ref: 'konstellation-selection:' + path });
    const refs = [
      statement('selection-type', {
        selection: id,
        type: concept('konstellation-type:' + s.entityType),
      }),
    ];
    if (s.ids)
      refs.push(
        statement('selection-identities', {
          selection: id,
          values: node('collection', { members: s.ids.map(entity), ordering: 'FIXED' }),
        }),
      );
    for (const f of s.filters) {
      const args = { selection: id, relation: concept('konstellation-relation:' + f.relation) };
      if (f.values)
        args.values = node('collection', {
          members: f.values.map((v) => term(v.kind, v.id ?? v.value)),
          ordering: 'FIXED',
        });
      if (f.interval) {
        args.interval = term('interval', f.interval);
        args.match = concept('konstellation-match:' + f.match);
      }
      refs.push(statement('filter-' + f.op, args));
    }
    for (let i = 0; i < s.links.length; i++) {
      const l = s.links[i],
        target = selection(l.target, path + '-' + i);
      refs.push(
        statement('selection-link', {
          selection: id,
          relation: concept('konstellation-relation:' + l.relation),
          target,
        }),
      );
    }
    obligation(refs);
    return id;
  }
  const selectionNode = selection(query.selection, 'root');
  obligation([
    statement('read-context', {
      dataset: literal(query.context.datasetRef, 'artifact-reference'),
      policy: literal(query.context.readerPolicyRef, 'policy-reference'),
    }),
  ]);
  let assertions = [];
  if (action === 'page') {
    const result = engine.query(query, cursor);
    const collection = node('collection', {
      members: result.rows.map((r) => entity(r.entityId)),
      ordering: 'FIXED',
    });
    obligation([
      statement('result-page', {
        selection: selectionNode,
        members: collection,
        total: node('quantity', { value: result.total.value }),
        page_count: node('quantity', { value: result.rows.length }),
        has_more: literal(result.nextCursor !== null, 'boolean'),
      }),
    ]);
    assertions = result.assertions;
  } else if (action === 'entity') {
    if (typeof entityId !== 'string') fail('INVALID_QUERY', 'Identité d’entité requise.');
    const detail = engine.entity(entityId, query.context);
    assertions = detail.assertions;
    obligation([statement('inspected-entity', { entity: entity(entityId) })]);
  }
  if (assertions.length > (config.maxAssertions || 200))
    fail(
      'COMMUNICATION_LIMIT',
      'Trop d’assertions à communiquer; sélectionnez une portée plus petite.',
      422,
    );
  for (const entry of assertions) {
    const a = entry.payload,
      sources = [entry.assertionRef, ...a.sourceRefs];
    const ref = entity(entry.assertionRef);
    const r = engine.relations.get(a.relation);
    const refs = [
      statement(
        'reported-assertion',
        {
          assertion: ref,
          subject: entity(a.subject),
          relation: concept('konstellation-relation:' + a.relation),
          value: term(r.valueKind, a.value),
        },
        sources,
      ),
    ];
    for (const key of [
      'status',
      'certainty',
      'validationStatus',
      'validatedAs',
      'authority',
      'recognitionStatus',
      'artifactStatus',
      'scope',
      'qualifiers',
      'validationPolicyRef',
      'readerLabels',
      'conflictsWith',
      'ruleRef',
    ])
      if (a[key] !== undefined)
        refs.push(
          statement(
            'assertion-' + key,
            {
              assertion: ref,
              value: literal(a[key], typeof a[key] === 'object' ? 'json' : 'string'),
            },
            sources,
          ),
        );
    obligation(refs, sources);
  }
  const identity = hash({ query, cursor, entityId, action, language, locale, config });
  const request = {
    schema_version: '1.0',
    request_id: identity,
    semantic_graph: { graph_id: identity, nodes, statements },
    obligations,
    supporting_context: [],
    context: {
      target_language: language,
      target_locale: locale,
      channel: 'app',
      register: 'encyclopedic',
    },
    constraints: {
      allowed_block_kinds: ['utterance', 'notice', 'list', 'label_value', 'heading'],
      opening_policy: 'forbidden',
      closing_policy: 'forbidden',
      list_policy: 'allowed',
      output_format: 'structured',
    },
    capability_profile: config.capabilityProfile || 'konstellation-explorer-2',
    ...(config.runtimeSetId ? { runtime_selector: { runtime_set_id: config.runtimeSetId } } : {}),
  };
  upstream('saRequest', request);
  return request;
}
export function validateCommunicationResult(request, result, config) {
  upstream('saResult', result);
  if (
    result.language !== request.context.target_language ||
    (request.context.target_locale && result.locale !== request.context.target_locale) ||
    result.runtime.runtime_set_id !== config.runtimeSetId ||
    result.runtime.capability_profile !== request.capability_profile ||
    (config.saGfContractVersion &&
      result.runtime.sa_gf_contract_version !== config.saGfContractVersion)
  )
    fail('SA_RESULT_MISMATCH', 'Langue, profil ou runtime différent de la requête.', 502);
  const obligations = new Set(request.obligations.map((o) => o.obligation_id)),
    blocks = new Map();
  for (const b of result.blocks) {
    if (!request.constraints.allowed_block_kinds.includes(b.kind))
      fail('SA_RESULT_MISMATCH', 'Type de bloc non autorisé.', 502);
    if (blocks.has(b.block_id)) fail('SA_COVERAGE_INVALID', 'Identité de bloc dupliquée.', 502);
    blocks.set(b.block_id, b);
    const declared = [...b.obligation_ids, ...(b.items || []).flatMap((i) => i.obligation_ids)];
    if (!declared.length || declared.some((id) => !obligations.has(id)))
      fail('SA_COVERAGE_INVALID', 'Obligation inconnue dans la sortie.', 502);
  }
  const coverage = new Map();
  for (const c of result.coverage) {
    if (
      coverage.has(c.obligation_id) ||
      !obligations.has(c.obligation_id) ||
      !c.block_ids.length ||
      !c.realization_unit_ids.length
    )
      fail('SA_COVERAGE_INVALID', 'Couverture invalide.', 502);
    for (const id of c.block_ids) {
      const b = blocks.get(id);
      if (
        !b ||
        ![...b.obligation_ids, ...(b.items || []).flatMap((i) => i.obligation_ids)].includes(
          c.obligation_id,
        )
      )
        fail('SA_COVERAGE_INVALID', 'Bloc de couverture absent ou incohérent.', 502);
    }
    coverage.set(c.obligation_id, c);
  }
  if ([...obligations].some((id) => !coverage.has(id)))
    fail('SA_COVERAGE_INVALID', 'SA a omis une obligation.', 502);
  const requiredSources = new Set(request.obligations.flatMap((o) => o.source_refs || []));
  if ([...requiredSources].some((id) => !result.source_refs?.includes(id)))
    fail('SA_SOURCES_MISSING', 'SA a omis une référence source.', 502);
  return result;
}
export class SemantikAdapter {
  constructor(config = null, { fetchImpl = fetch } = {}) {
    this.config = config;
    this.fetchImpl = fetchImpl;
    if (config) {
      serviceUrl(config.baseUrl);
      if (
        !config.runtimeSetId ||
        !config.capabilityProfile ||
        !Array.isArray(config.languages) ||
        !config.languages.length
      )
        fail('INVALID_CONFIG', 'Runtime SA, profil et langues explicites requis.');
    }
  }
  async call(route, body) {
    const c = this.config;
    const base = c.baseUrl.endsWith('/') ? c.baseUrl : c.baseUrl + '/';
    return fetchJson(new URL(route, base), {
      method: body ? 'POST' : 'GET',
      body,
      fetchImpl: this.fetchImpl,
      timeoutMs: c.timeoutMs || 10000,
      headers:
        c.tokenEnv && process.env[c.tokenEnv]
          ? { Authorization: 'Bearer ' + process.env[c.tokenEnv] }
          : {},
    });
  }
  async capabilities() {
    if (!this.config)
      return {
        configured: false,
        available: false,
        reason: 'Aucun service SA configuré.',
        languages: [],
        requestExport: true,
      };
    const c = this.config;
    try {
      const caps = await this.call('v1/capabilities');
      const ready = await this.call('ready');
      const runtime = ready.runtime_sets?.find(
        (r) => r.runtime_set_id === c.runtimeSetId && r.valid === true,
      );
      const languages = c.languages.filter(
        (language) =>
          caps[c.runtimeSetId]?.[language]?.status === 'RELEASED' &&
          caps[c.runtimeSetId][language].profiles?.some(
            (p) => p.profile_id === c.capabilityProfile && p.status === 'RELEASED',
          ),
      );
      return {
        configured: true,
        available: !!runtime && languages.length > 0,
        languages,
        runtimeSetId: c.runtimeSetId,
        capabilityProfile: c.capabilityProfile,
        requestExport: true,
        reason: !runtime
          ? 'Runtime SA non validé.'
          : !languages.length
            ? 'Profil linguistique non publié.'
            : null,
      };
    } catch (e) {
      return {
        configured: true,
        available: false,
        reason: e.message,
        languages: [],
        requestExport: true,
      };
    }
  }
  request(engine, options) {
    return buildCommunicationRequest(engine, options, this.config || {});
  }
  async render(engine, options) {
    const request = this.request(engine, options),
      caps = await this.capabilities();
    if (!caps.available || !caps.languages.includes(request.context.target_language))
      fail('SA_UNAVAILABLE', caps.reason || 'Langue non publiée pour ce profil.', 503);
    const validation = await this.call('v1/validate-request', request);
    if (validation.valid !== true) fail('SA_REQUEST_REJECTED', 'SA a refusé la requête.', 422);
    const result = await this.call('v1/render', request);
    return {
      requestId: request.request_id,
      result: validateCommunicationResult(request, result, this.config),
    };
  }
}
