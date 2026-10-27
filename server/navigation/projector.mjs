import { canonical, compare } from '../pack.mjs';
import { fail, validate } from '../contracts.mjs';
import { NavigationIndex } from './index.mjs';
import { rankCandidates } from './salience.mjs';

const titleCase = (s) =>
  String(s || '')
    .replace(/^.*:/, '')
    .replace(/[_-]+/g, ' ')
    .replace(/\b\p{L}/gu, (m) => m.toUpperCase());


const entityLabel = (entity) =>
  entity?.disambiguation ? `${entity.label} — ${entity.disambiguation}` : entity?.label || '';

const humanize = (s) => {
  const value = String(s || '').replace(/[_-]+/g, ' ').trim();
  return value ? value[0].toLocaleUpperCase('fr') + value.slice(1) : value;
};

function relationLabel(relation) {
  if (!relation) return 'Relation';
  const raw = relation.label?.fr || relation.label?.en || relation.id;
  return /[_:]/.test(raw) ? humanize(raw.replace(/^.*:/, '')) : raw;
}

function linkedLabel(engine, values, fallback) {
  const types = [...new Set(values.map((id) => engine.entities.get(id)?.type).filter(Boolean))];
  if (types.length !== 1) return fallback;
  const type = types[0];
  const label = engine.profiler?.entityTypeLabels?.[type] || humanize(type);
  return `${label} · liés`;
}

const unique = (xs) => [...new Set(xs)];
const ids = (assertions) => assertions.map((a) => a.id);
const sourceIds = (assertions) => unique(assertions.flatMap((a) => a.sourceRefs || []));

function displayValue(value) {
  if (value && typeof value === 'object') {
    if (['startMin', 'startMax', 'endMin', 'endMax'].some((k) => k in value))
      return `${value.startMin ?? value.startMax ?? '?'}–${value.endMax ?? value.endMin ?? '?'}`;
    return canonical(value);
  }
  return String(value);
}

const entityIds = (engine, assertions) =>
  unique(
    assertions.flatMap((a) => {
      const r = engine.relations.get(a.relation);
      return r?.valueKind === 'entity' ? [a.subject, a.value] : [a.subject];
    }),
  );

function focusKey(focus) {
  if (focus.kind === 'entity' || focus.kind === 'source') return `${focus.kind}:${focus.id}`;
  if (focus.kind === 'qualifier') return `qualifier:${focus.predicate}:${focus.key}`;
  if (focus.kind === 'relation-value') return `relation-value:${focus.relation}:${focus.key}`;
  return 'unknown';
}

function resolveFocus(engine, index, focus) {
  if (!focus || typeof focus !== 'object') fail('INVALID_QUERY', 'Focus de constellation requis.');
  if (focus.kind === 'entity') {
    const entity = engine.entities.get(focus.id);
    if (!entity || !index.state.entityIds?.has(focus.id)) fail('NOT_FOUND', 'Entité de constellation indisponible.', 404);
    return { focus, id: focusKey(focus), kind: 'entity', label: entityLabel(entity), description: entity.description || '' };
  }
  if (focus.kind === 'source') {
    const source = engine.sources.get(focus.id);
    const sourceVisible = index.bySource.has(focus.id) || index.byQualifierItem.has(focus.id);
    if (!source || !sourceVisible) fail('NOT_FOUND', 'Source de constellation indisponible.', 404);
    return { focus, id: focusKey(focus), kind: 'source', label: source.title, description: source.description || '' };
  }
  if (focus.kind === 'qualifier') {
    const match = index.qualifierMatches(focus.predicate, focus.key)[0];
    if (!match) fail('NOT_FOUND', 'Valeur de qualificatif indisponible.', 404);
    return {
      focus,
      id: focusKey(focus),
      kind: 'concept',
      label: match.qualifier.label,
      description: match.qualifier.predicateLabel,
    };
  }
  if (focus.kind === 'relation-value') {
    const assertions = index.focusAssertions(focus);
    if (!assertions.length) fail('NOT_FOUND', 'Valeur de relation indisponible.', 404);
    const relation = engine.relations.get(focus.relation);
    const value = assertions.find((a) => canonical(a.value) === focus.key)?.value;
    return {
      focus,
      id: focusKey(focus),
      kind: 'value',
      label: displayValue(value),
      description: relation?.label?.fr || focus.relation,
    };
  }
  fail('INVALID_QUERY', 'Type de focus de constellation inconnu.');
}

function evidence(engine, assertions) {
  return {
    assertionRefs: unique(ids(assertions)).sort(compare),
    entityRefs: entityIds(engine, assertions).sort(compare),
    sourceRefs: sourceIds(assertions).sort(compare),
  };
}

function qualifierTarget(engine, q) {
  if (q.id && engine.entities.has(q.id)) return { focus: { kind: 'entity', id: q.id }, groupId: null };
  if (q.id && engine.sources.has(q.id)) return { focus: { kind: 'source', id: q.id }, groupId: null };
  return { focus: { kind: 'qualifier', predicate: q.predicate, key: q.key }, groupId: null };
}

function relationTarget(engine, relation, value) {
  if (relation.valueKind === 'entity' && engine.entities.has(value))
    return { focus: { kind: 'entity', id: value }, groupId: null };
  return {
    focus: { kind: 'relation-value', relation: relation.id, key: canonical(value) },
    groupId: null,
  };
}

function addCandidate(map, candidate, assertion, engine) {
  const current = map.get(candidate.id) || {
    ...candidate,
    evidence: { assertionRefs: [], entityRefs: [], sourceRefs: [] },
  };
  current.evidence.assertionRefs.push(assertion.id);
  current.evidence.entityRefs.push(assertion.subject);
  const rel = engine.relations.get(assertion.relation);
  if (rel?.valueKind === 'entity') current.evidence.entityRefs.push(assertion.value);
  current.evidence.sourceRefs.push(...(assertion.sourceRefs || []));
  current.evidence.assertionRefs = unique(current.evidence.assertionRefs);
  current.evidence.entityRefs = unique(current.evidence.entityRefs);
  current.evidence.sourceRefs = unique(current.evidence.sourceRefs);
  map.set(candidate.id, current);
}

function configuredCandidates(engine, index, focus, group) {
  const assertions = index.focusAssertions(focus);
  const map = new Map();
  if (group.source.kind === 'qualifiers') {
    for (const { assertion, qualifier } of index.qualifiers(assertions)) {
      if (!group.source.ids.includes(qualifier.predicate)) continue;
      const target = qualifierTarget(engine, qualifier);
      addCandidate(
        map,
        {
          id: ['entity', 'source'].includes(target.focus.kind) ? focusKey(target.focus) : `qual:${qualifier.predicate}:${qualifier.key}`,
          kind: qualifier.id && engine.sources.has(qualifier.id) ? 'source' : qualifier.id && engine.entities.has(qualifier.id) ? 'entity' : 'concept',
          label: humanize(qualifier.label),
          target,
          family: group.id,
          priority: group.priority ?? 0.8,
          directness: 1,
        },
        assertion,
        engine,
      );
    }
  } else if (group.source.kind === 'relations' && focus.kind === 'entity') {
    for (const relationId of group.source.ids) {
      const relation = engine.relations.get(relationId);
      for (const edge of index.relationEdges(focus.id, relationId)) {
        const a = edge.assertion;
        const value = edge.value;
        const target = relationTarget(engine, relation, value);
        addCandidate(
          map,
          {
            id: target.focus.kind === 'entity' ? focusKey(target.focus) : `rel:${relationId}:${canonical(value)}`,
            kind: relation?.valueKind === 'entity' ? 'entity' : 'value',
            label: relation?.valueKind === 'entity' ? entityLabel(engine.entities.get(value)) || String(value) : displayValue(value),
            target,
            family: group.id,
            priority: group.priority ?? 0.8,
            directness: 1,
          },
          a,
          engine,
        );
      }
    }
  }
  return [...map.values()];
}

function automaticGroupDefinitions(engine, index, focus, lens) {
  const assertions = index.focusAssertions(focus);
  const focusEntity = focus.kind === 'entity' ? engine.entities.get(focus.id) : null;
  const configured = focusEntity && lens?.rootType === focusEntity.type ? lens?.constellation?.groups || [] : [];
  const claimedRelations = new Set(
    configured.filter((g) => g.source.kind === 'relations').flatMap((g) => g.source.ids),
  );
  const claimedQualifiers = new Set(
    configured.filter((g) => g.source.kind === 'qualifiers').flatMap((g) => g.source.ids),
  );
  const groups = [...configured.map((g) => ({ ...g, configured: true }))];
  const qualifiers = new Map();
  for (const { qualifier } of index.qualifiers(assertions)) {
    if (claimedQualifiers.has(qualifier.predicate)) continue;
    if ((focus.kind === 'entity' || focus.kind === 'source') && qualifier.id === focus.id) continue;
    const item = qualifiers.get(qualifier.predicate) || {
      id: `q:${qualifier.predicate}`,
      label: {
        fr: qualifier.predicateLabel || titleCase(qualifier.predicate),
        en: qualifier.predicateLabel || titleCase(qualifier.predicate),
      },
      priority: qualifier.id && engine.sources.has(qualifier.id) ? 0.95 : qualifier.id && engine.entities.has(qualifier.id) ? 0.78 : 0.55,
      source: { kind: 'qualifiers', ids: [qualifier.predicate] },
      configured: false,
    };
    qualifiers.set(qualifier.predicate, item);
  }
  groups.push(...qualifiers.values());
  const directEntityAssertions = focus.kind === 'entity' ? index.byEntity.get(focus.id) || [] : [];
  const directEntityEdges = focus.kind === 'entity' ? index.entityEdges.get(focus.id) || [] : [];
  const qualifierBacklinks = focus.kind === 'entity' ? index.taggedMatches(focus.id).map((x) => x.assertion) : [];
  if (focus.kind === 'entity' && directEntityEdges.length) {
    const relationIds = unique(directEntityEdges.map((edge) => edge.relationId)).filter((id) => !claimedRelations.has(id));
    for (const id of relationIds) {
      const r = engine.relations.get(id);
      // Node type is presentation metadata, not a meaningful graph connection.
      // It remains available in the inspector and faceted query surface.
      if (!r || id.startsWith('v9:node_kind')) continue;
      groups.push({
        id: `r:${id}`,
        label: { fr: relationLabel(r), en: r.label?.en || relationLabel(r) },
        priority: r.valueKind === 'entity' ? 0.78 : 0.35,
        source: { kind: 'relations', ids: [id] },
        configured: false,
      });
    }
  }
  if (focus.kind !== 'entity' || (!directEntityAssertions.length && qualifierBacklinks.length)) {
    const subjects = unique(assertions.map((a) => a.subject)).filter((id) => engine.entities.has(id));
    const objects = unique(
      assertions.flatMap((a) => (engine.relations.get(a.relation)?.valueKind === 'entity' ? [a.value] : [])),
    ).filter((id) => engine.entities.has(id));
    if (subjects.length)
      groups.push({ id: 'participants:subjects', label: { fr: linkedLabel(engine, subjects, 'Sujets liés'), en: 'Related subjects' }, priority: 0.9, source: { kind: 'participants', role: 'subject' } });
    if (objects.length)
      groups.push({ id: 'participants:objects', label: { fr: linkedLabel(engine, objects, 'Éléments liés'), en: 'Related items' }, priority: 0.86, source: { kind: 'participants', role: 'object' } });
    const linked = new Set([...subjects, ...objects]);
    const network = new Map();
    for (const a of index.state.assertions.values()) {
      const r = engine.relations.get(a.relation);
      if (r?.valueKind !== 'entity' || !linked.has(a.subject) || !linked.has(a.value)) continue;
      if (assertions.some((x) => x.id === a.id)) continue;
      if (!network.has(a.relation))
        network.set(a.relation, {
          id: `network:${a.relation}`,
          label: { fr: relationLabel(r), en: r.label?.en || relationLabel(r) },
          priority: 0.82,
          source: { kind: 'network', relation: a.relation },
        });
    }
    groups.push(...network.values());
  }
  const sourceAlreadyRepresented = index.qualifiers(assertions).some(({ qualifier }) => qualifier.id && engine.sources.has(qualifier.id));
  if (focus.kind !== 'source' && sourceIds(assertions).length && !sourceAlreadyRepresented)
    groups.push({ id: 'sources', label: { fr: 'Sources', en: 'Sources' }, priority: 0.35, source: { kind: 'sources' } });
  return groups;
}

function contentForGroup(engine, index, focus, group) {
  if (group.source.kind === 'relations' || group.source.kind === 'qualifiers')
    return configuredCandidates(engine, index, focus, group);
  const assertions = index.focusAssertions(focus);
  const map = new Map();
  if (group.source.kind === 'sources') {
    for (const a of assertions)
      for (const sid of a.sourceRefs || []) {
        const source = engine.sources.get(sid);
        if (!source) continue;
        addCandidate(map, { id: `source:${sid}`, kind: 'source', label: source.title, target: { focus: { kind: 'source', id: sid }, groupId: null }, family: group.id, priority: group.priority, directness: 0.9 }, a, engine);
      }
  } else if (group.source.kind === 'participants') {
    for (const a of assertions) {
      const rel = engine.relations.get(a.relation);
      const value = group.source.role === 'subject' ? a.subject : rel?.valueKind === 'entity' ? a.value : null;
      if (!value || !engine.entities.has(value)) continue;
      addCandidate(map, { id: `entity:${value}`, kind: 'entity', label: entityLabel(engine.entities.get(value)), target: { focus: { kind: 'entity', id: value }, groupId: null }, family: group.id, priority: group.priority, directness: 0.85 }, a, engine);
    }
  } else if (group.source.kind === 'network') {
    const linked = new Set(entityIds(engine, assertions));
    for (const a of index.state.assertions.values()) {
      if (a.relation !== group.source.relation) continue;
      const rel = engine.relations.get(a.relation);
      if (rel?.valueKind !== 'entity' || !linked.has(a.subject) || !linked.has(a.value)) continue;
      for (const value of [a.subject, a.value]) {
        if (!engine.entities.has(value)) continue;
        addCandidate(map, { id: `entity:${value}`, kind: 'entity', label: entityLabel(engine.entities.get(value)), target: { focus: { kind: 'entity', id: value }, groupId: null }, family: group.id, priority: group.priority, directness: 0.7 }, a, engine);
      }
    }
  }
  return [...map.values()];
}

function groupCandidates(engine, index, focus, groups) {
  const out = [];
  for (const group of groups) {
    const members = contentForGroup(engine, index, focus, group);
    if (!members.length) continue;
    const assertions = index.uniqueAssertions(members.flatMap((m) => m.evidence.assertionRefs.map((id) => index.state.assertions.get(id))).filter(Boolean));
    out.push({
      id: `group:${group.id}`,
      kind: 'group',
      label: group.label.fr,
      count: members.length,
      target: { focus, groupId: group.id },
      family: group.id,
      priority: group.priority ?? 0.5,
      directness: 1,
      evidence: evidence(engine, assertions),
    });
  }
  return out;
}

function cleanCandidate(c) {
  return {
    id: c.id,
    kind: c.kind,
    label: c.label,
    count: c.count ?? null,
    target: c.target,
    salience: c.salience,
    evidence: {
      assertionCount: c.evidence?.assertionRefs?.length || 0,
      entityCount: c.evidence?.entityRefs?.length || 0,
      sourceCount: c.evidence?.sourceRefs?.length || 0,
    },
  };
}

export function projectConstellation(engine, state, lenses, request) {
  const lens = lenses.find((l) => l.id === request.lensRef) || null;
  if (request.lensRef && !lens && !String(request.lensRef).startsWith('type:'))
    fail('INVALID_QUERY', 'Perspective de constellation indisponible.');
  const configuredDefault = lens?.constellation?.defaultSatelliteCount || 8;
  const limit = request.limit === undefined ? configuredDefault : Number(request.limit);
  if (!Number.isInteger(limit) || limit < 3 || limit > 25)
    fail('INVALID_QUERY', 'Le nombre de satellites doit être compris entre 3 et 25.');
  const index = new NavigationIndex(engine, state);
  const center = resolveFocus(engine, index, request.focus);
  const groups = automaticGroupDefinitions(engine, index, request.focus, lens);
  let candidates;
  if (request.groupId) {
    const group = groups.find((g) => g.id === request.groupId);
    if (!group) fail('NOT_FOUND', 'Groupe de constellation indisponible.', 404);
    candidates = contentForGroup(engine, index, request.focus, group);
    center.kind = 'group';
    center.id = `group:${request.groupId}:${center.id}`;
    center.description = center.label;
    center.label = group.label.fr;
  } else candidates = groupCandidates(engine, index, request.focus, groups);
  const ranked = rankCandidates(candidates, limit);
  return validate('constellation-response', {
    schemaVersion: '0.1',
    context: request.context,
    focus: request.focus,
    groupId: request.groupId || null,
    center: { id: center.id, kind: center.kind, label: center.label, description: center.description || '' },
    satellites: ranked.map(cleanCandidate),
    limit,
    totalCandidates: candidates.length,
    truncated: candidates.length > ranked.length,
  });
}
