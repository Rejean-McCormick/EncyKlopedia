import { fail, validate } from '../contracts.mjs';
import { hash } from '../pack.mjs';
import { buildNavigationPlan } from './planner.mjs';
import { rendererDefinition } from './registry.mjs';

const int = (value, fallback, min, max) => Number.isInteger(value) ? Math.max(min, Math.min(max, value)) : fallback;
const unique = (values) => [...new Set(values.filter((value) => value !== null && value !== undefined))];
const relationLabel = (relation) => relation?.label?.fr || relation?.label?.en || relation?.id || '';
const publicNode = (engine, id) => {
  const entity = engine.entities.get(id);
  return entity ? { id, type: entity.type, label: entity.label, description: entity.description || '' } : null;
};
const coordinatesOf = (assertion) => Array.isArray(assertion.coordinates)
  ? assertion.coordinates
  : assertion.coordinates && typeof assertion.coordinates === 'object'
    ? Object.entries(assertion.coordinates).map(([axis, value]) => ({ axis, value }))
    : [];

const VALUE_SEMANTICS = new Set(['boolean','categorical','set','ordinal','scalar','interval','probability','distribution','vector','partial_order','state','temporal']);
const VALUE_STATES = new Set(['known','unknown','not_applicable','indeterminate','not_measured']);
const ACTIONABILITY_MODES = new Set(['automatic','human_review','human_decision','manual','prohibited','insufficient_information','not_applicable']);

function publicCoordinate(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || typeof value.axis !== 'string' || !value.axis.trim() || !Object.prototype.hasOwnProperty.call(value, 'value')) return null;
  const out = { axis: value.axis, value: value.value };
  if (typeof value.unit === 'string' && value.unit) out.unit = value.unit;
  return out;
}

function publicValuation(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || typeof value.dimension !== 'string' || !value.dimension.trim()) return null;
  if (!VALUE_SEMANTICS.has(value.value_semantics) || !VALUE_STATES.has(value.value_state)) return null;
  if (value.value_state === 'known' && !Object.prototype.hasOwnProperty.call(value, 'value')) return null;
  const out = { dimension: value.dimension, value_semantics: value.value_semantics, value_state: value.value_state };
  if (value.value_state === 'known') out.value = value.value;
  if (typeof value.unit === 'string' && value.unit) out.unit = value.unit;
  return out;
}

function publicActionability(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value) || !ACTIONABILITY_MODES.has(value.mode)) return null;
  const out = { mode: value.mode };
  if (typeof value.requires_human_validation === 'boolean') out.requires_human_validation = value.requires_human_validation;
  return out;
}

function publicLineage(value, state) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const out = {};
  if (typeof value.isFork === 'boolean') out.isFork = value.isFork;
  if (typeof value.recognized === 'boolean') out.recognized = value.recognized;
  const refs = Array.isArray(value.source_assertions) ? value.source_assertions : Array.isArray(value.sourceAssertions) ? value.sourceAssertions : [];
  const sourceAssertions = unique(refs.filter((ref) => typeof ref === 'string' && state.assertions.has(ref)));
  if (sourceAssertions.length) out.sourceAssertions = sourceAssertions.slice(0, 32);
  const transforms = Array.isArray(value.transforms) ? value.transforms : [];
  const transformTypes = unique(transforms.map((item) => item?.transform_type || item?.transformType).filter((item) => typeof item === 'string' && item));
  if (transformTypes.length) out.transformTypes = transformTypes.slice(0, 16);
  return Object.keys(out).length ? out : { present: true };
}

function transitionFromEdge(edge) {
  const valuations = Array.isArray(edge.valuations) ? edge.valuations : [];
  const coordinates = Array.isArray(edge.coordinates) ? edge.coordinates : [];
  const conditions = [
    ...valuations.map((v) => ({ kind: 'valuation', dimension: v.dimension, state: v.value_state, ...(v.value_state === 'known' ? { value: v.value } : {}) })),
    ...coordinates.map((c) => ({ kind: 'coordinate', axis: c.axis, value: c.value })),
  ].slice(0, 12);
  return {
    ...edge,
    conditional: /condition|eligible|admission|require|may|peut|si\b/i.test(edge.relationLabel || '') || conditions.length > 0,
    conditions,
  };
}

function common(engine, request, view, projectionKind, extra = {}) {
  const output = {
    schemaVersion: '1.0', projectionKind, recipeId: request.recipeId,
    rendererId: view.rendererId, derived: true,
    truncated: Boolean(extra.truncated), nextCursor: extra.nextCursor ?? null,
    totalCandidates: Number.isInteger(extra.totalCandidates) ? extra.totalCandidates : 0,
    explanation: { reason: view.reason, relationIds: view.relationIds || [] },
    ...extra,
  };
  return validate('navigation-projection', output);
}

function visibleRef(engine, state, id) {
  return state.assertions.has(id) || engine.sources.has(id);
}

function selectedIds(engine, request, limit = 500) {
  if (request.selectedEntityId) return [request.selectedEntityId];
  const evaluated = typeof engine.evaluate === 'function' ? engine.evaluate(request.query).computed : null;
  if (evaluated) return evaluated.rows.slice(0, limit).map((row) => row.entityId);
  return engine.query(request.query).rows.slice(0, limit).map((row) => row.entityId);
}

function budgets(request) {
  return {
    pageSize: int(request.pageSize, 160, 10, 500),
    nodeBudget: int(request.nodeBudget, 240, 25, 1200),
    edgeBudget: int(request.edgeBudget, 360, 25, 2400),
  };
}

function windowPage(engine, request, keyPayload, values, size) {
  const key = hash({ kind: 'navigation-projection', ...keyPayload, access: engine.accessRef });
  const offset = request.cursor ? engine.cursor(request.cursor, key) : 0;
  const page = values.slice(offset, offset + size);
  const nextOffset = offset + page.length;
  return {
    page,
    nextCursor: nextOffset < values.length ? engine.sign({ key, offset: nextOffset }) : null,
    truncated: nextOffset < values.length || offset > 0,
    totalCandidates: values.length,
    offset,
  };
}

function matchingPlanView(engine, request, lenses) {
  engine.check(request.query);
  const state = engine.scope(request.query.context); // policy before profiler/planner/projection
  const profiler = engine.visibleProfiler(request.query.context);
  const lens = lenses.find((item) => item.id === request.lensRef) || null;
  if (!lens || lens.rootType !== request.query.selection.entityType) fail('INVALID_QUERY', 'Lens indisponible ou incompatible avec la sélection.', 422);
  const selectedEntity = request.selectedEntityId ? engine.entities.get(request.selectedEntityId) : null;
  if (request.selectedEntityId && (!selectedEntity || !state.entityIds?.has(request.selectedEntityId))) fail('NOT_FOUND', 'Entité de navigation indisponible.', 404);
  const evaluated = selectedEntity ? null : engine.evaluate(request.query, state).computed;
  const resultEntityIds = evaluated ? evaluated.rows.slice(0, 512).map((row) => row.entityId) : null;
  const plan = buildNavigationPlan({ profiler, query: request.query, lens, selectedEntity, resultEntityIds, resultSize: evaluated?.rows.length ?? null });
  const view = plan.views.find((item) => item.id === request.recipeId);
  if (!view) fail('UNSUPPORTED_CAPABILITY', 'Cette recette de navigation n’est pas disponible dans ce contexte.', 422);
  const renderer = rendererDefinition(view.rendererId);
  if (!renderer || !renderer.supportedRecipes.includes(view.id)) fail('UNSUPPORTED_CAPABILITY', 'Renderer de navigation indisponible.', 422);
  return { state, profiler, plan, view, renderer };
}


function assertionsForEntities(state, entityIds, max = 10000) {
  const out = [];
  const seen = new Set();
  for (const entityId of entityIds) {
    for (const assertion of state.assertionsByEntity?.get(entityId) || []) {
      if (seen.has(assertion.id)) continue;
      seen.add(assertion.id); out.push(assertion);
      if (out.length >= max) return out;
    }
  }
  return out;
}

function graphData(engine, state, entityIds, relationIds, { edgeBudget = 2400, includeNeighborhood = true } = {}) {
  const selected = new Set(entityIds);
  const relationSet = new Set(relationIds);
  const nodes = new Map();
  const edges = [];
  const addNode = (id) => { const node = publicNode(engine, id); if (node) nodes.set(id, node); };
  entityIds.forEach(addNode);
  for (const assertion of assertionsForEntities(state, entityIds, edgeBudget * 8)) {
    if (edges.length >= edgeBudget * 4) break;
    if (!relationSet.has(assertion.relation)) continue;
    const relation = engine.relations.get(assertion.relation);
    if (relation?.valueKind !== 'entity') continue;
    if (includeNeighborhood && !selected.has(assertion.subject) && !selected.has(assertion.value)) continue;
    if (!includeNeighborhood && (!selected.has(assertion.subject) || !selected.has(assertion.value))) continue;
    addNode(assertion.subject); addNode(assertion.value);
    edges.push({
      id: assertion.id, source: assertion.subject, target: assertion.value,
      relationId: assertion.relation, relationLabel: relationLabel(relation), status: assertion.status,
      sourceRefs: unique((assertion.sourceRefs || []).filter((id) => engine.sources.has(id))),
      recordRole: assertion.recordRole || null,
      valuations: (assertion.valuations || []).map(publicValuation).filter(Boolean).slice(0, 12),
      coordinates: coordinatesOf(assertion).map(publicCoordinate).filter(Boolean).slice(0, 12),
      conflictsWith: unique((assertion.conflictsWith || []).filter((id) => state.assertions.has(id))),
      supersedes: unique((assertion.supersedes || []).filter((id) => state.assertions.has(id))),
      lineage: publicLineage(assertion.lineage, state),
      actionability: publicActionability(assertion.actionability),
    });
  }
  return { nodes, edges };
}

function rootsAndTerminals(nodes, edges) {
  const incoming = new Map([...nodes.keys()].map((id) => [id, 0]));
  const outgoing = new Map([...nodes.keys()].map((id) => [id, 0]));
  for (const edge of edges) {
    incoming.set(edge.target, (incoming.get(edge.target) || 0) + 1);
    outgoing.set(edge.source, (outgoing.get(edge.source) || 0) + 1);
  }
  return {
    roots: [...nodes.keys()].filter((id) => (incoming.get(id) || 0) === 0),
    terminals: [...nodes.keys()].filter((id) => (outgoing.get(id) || 0) === 0),
  };
}

function cycleInfo(nodes, edges, limit = 24) {
  const adjacency = new Map();
  for (const edge of edges) {
    const rows = adjacency.get(edge.source) || []; rows.push(edge.target); adjacency.set(edge.source, rows);
  }
  const cycles = [];
  const seen = new Set();
  function walk(start, node, path, visiting) {
    if (cycles.length >= limit || path.length > 12) return;
    for (const next of adjacency.get(node) || []) {
      if (next === start && path.length >= 2) {
        const cycle = [...path, start];
        const canonical = [...cycle.slice(0, -1)].sort().join('|');
        if (!seen.has(canonical)) { seen.add(canonical); cycles.push(cycle); }
      } else if (!visiting.has(next)) {
        const nextVisiting = new Set(visiting); nextVisiting.add(next);
        walk(start, next, [...path, next], nextVisiting);
      }
    }
  }
  for (const id of nodes.keys()) { if (cycles.length >= limit) break; walk(id, id, [id], new Set([id])); }
  return cycles;
}

function intervalPoint(value) {
  if (Number.isSafeInteger(value)) return { start: value, end: value, label: String(value) };
  if (typeof value === 'string') {
    const match = value.match(/(?:^|[^0-9-])(-?\d{1,4})(?:[^0-9]|$)/);
    return match ? { start: Number(match[1]), end: Number(match[1]), label: value } : { start: null, end: null, label: value };
  }
  if (value && typeof value === 'object') {
    const rawStart = value.start ?? value.from ?? value.year ?? value.date ?? value.startMin ?? value.startMax ?? null;
    const rawEnd = value.end ?? value.to ?? value.year ?? value.date ?? value.endMax ?? value.endMin ?? rawStart;
    const year = (raw) => Number.isSafeInteger(raw) ? raw : typeof raw === 'string' && /-?\d{1,4}/.test(raw) ? Number(raw.match(/-?\d{1,4}/)[0]) : null;
    return { start: year(rawStart), end: year(rawEnd), label: String(rawStart ?? rawEnd ?? 'repère temporel') };
  }
  return { start: null, end: null, label: 'repère temporel' };
}

function timelineProjection(engine, state, profiler, request, view, entityIds, budget) {
  const items = [];
  const links = [];
  const seen = new Set();
  const temporalRelations = new Map();
  for (const relationId of view.relationIds) {
    const relation = engine.relations.get(relationId); if (relation) temporalRelations.set(relation.id, relation);
  }
  for (const relation of profiler.relationsFor('temporal', null)) temporalRelations.set(relation.id, relation);
  const add = (entityId, relation, entry, via = null) => {
    const point = relation.valueKind === 'interval'
      ? { start: entry.value.startMin ?? entry.value.startMax, end: entry.value.endMax ?? entry.value.endMin }
      : intervalPoint(entry.value);
    if (point.start === null && point.end === null && !point.label) return;
    const key = `${entityId}|${entry.assertion.id}`; if (seen.has(key)) return; seen.add(key);
    items.push({ id: key, entity: publicNode(engine, entityId), relationId: relation.id, relationLabel: relationLabel(relation), ...point, assertionRef: entry.assertion.id, ...(via ? { via } : {}) });
  };
  for (const id of entityIds) {
    for (const relation of temporalRelations.values()) {
      if (!relation.domain.includes(engine.entities.get(id)?.type)) continue;
      for (const entry of state.index.get(`${id}|${relation.id}`) || []) if (['interval','integer','string'].includes(relation.valueKind)) add(id, relation, entry);
    }
    for (const relation of profiler.relationsFor('temporal', engine.entities.get(id)?.type).filter((r) => r.valueKind === 'entity')) {
      for (const entry of state.index.get(`${id}|${relation.id}`) || []) {
        const target = engine.entities.get(entry.value); if (!target) continue;
        for (const temporal of profiler.relationsFor('temporal', target.type))
          for (const targetEntry of state.index.get(`${entry.value}|${temporal.id}`) || []) if (['interval','integer','string'].includes(temporal.valueKind)) add(entry.value, temporal, targetEntry, { entityId: id, relationId: relation.id, relationLabel: relationLabel(relation) });
      }
    }
  }
  const allowed = new Set(entityIds);
  for (const assertion of assertionsForEntities(state, entityIds, budget.edgeBudget * 8)) {
    if (!allowed.has(assertion.subject) && !(engine.relations.get(assertion.relation)?.valueKind === 'entity' && allowed.has(assertion.value))) continue;
    const temporalValues = [
      ...coordinatesOf(assertion).filter((c) => /\b(time|date|year|period|phase|effective|temps|annee|année|periode|période)\b/i.test(String(c.axis || ''))).map((c) => c.value),
      ...(assertion.valuations || []).filter((v) => v.value_semantics === 'temporal' && v.value_state !== 'unknown').map((v) => v.value),
    ];
    for (const raw of temporalValues) {
      const key = `v6:${assertion.id}:${JSON.stringify(raw)}`; if (seen.has(key)) continue; seen.add(key);
      const point = intervalPoint(raw);
      items.push({ id: key, entity: publicNode(engine, assertion.subject), relationId: assertion.relation, relationLabel: relationLabel(engine.relations.get(assertion.relation)), ...point, temporalLabel: point.label, assertionRef: assertion.id, derivedFrom: 'kristal-v6-temporal-metadata' });
    }
    if (request.recipeId === 'evolution') {
      for (const prior of assertion.supersedes || []) if (state.assertions.has(prior)) links.push({ kind: 'supersedes', from: assertion.id, to: prior });
      if (assertion.lineage) links.push({ kind: 'lineage', assertionRef: assertion.id, value: publicLineage(assertion.lineage, state) });
    }
  }
  items.sort((a,b) => (a.start ?? Infinity) - (b.start ?? Infinity) || (a.entity?.label || '').localeCompare(b.entity?.label || '', 'fr'));
  const page = windowPage(engine, request, { recipeId: request.recipeId, query: request.query, selected: request.selectedEntityId }, items, budget.pageSize);
  return common(engine, request, view, 'timeline-lineage', { items: page.page, links: links.slice(0, budget.edgeBudget), nextCursor: page.nextCursor, truncated: page.truncated || links.length > budget.edgeBudget, totalCandidates: items.length });
}

function treeProjection(engine, state, request, view, entityIds, budget) {
  const graph = graphData(engine, state, entityIds, view.relationIds, { edgeBudget: budget.edgeBudget });
  const edges = graph.edges.slice(0, budget.edgeBudget);
  const keep = new Set(edges.flatMap((edge) => [edge.source, edge.target])); entityIds.forEach((id) => keep.add(id));
  const nodes = [...graph.nodes.values()].filter((node) => keep.has(node.id)).slice(0, budget.nodeBudget);
  const nodeSet = new Set(nodes.map((node) => node.id));
  const boundedEdges = edges.filter((edge) => nodeSet.has(edge.source) && nodeSet.has(edge.target));
  const rt = rootsAndTerminals(new Map(nodes.map((node) => [node.id,node])), boundedEdges);
  return common(engine, request, view, 'tree', { nodes, edges: boundedEdges, roots: rt.roots, truncated: graph.edges.length > boundedEdges.length || graph.nodes.size > nodes.length, totalCandidates: graph.edges.length });
}

function dagProjection(engine, state, request, view, entityIds, budget) {
  const graph = graphData(engine, state, entityIds, view.relationIds, { edgeBudget: budget.edgeBudget });
  const nodes = [...graph.nodes.values()].slice(0, budget.nodeBudget); const nodeSet = new Set(nodes.map((node) => node.id));
  const edges = graph.edges.filter((edge) => nodeSet.has(edge.source) && nodeSet.has(edge.target)).slice(0, budget.edgeBudget).map((edge) => ({ ...edge, kind: /counter|contre|refut|réfut/i.test(edge.relationLabel) ? 'challenge' : /proof|prove|preuve|demon|démon/i.test(edge.relationLabel) ? 'proof' : 'dependency' }));
  const rt = rootsAndTerminals(new Map(nodes.map((node) => [node.id,node])), edges);
  const cycles = cycleInfo(new Map(nodes.map((node) => [node.id,node])), edges, 8);
  return common(engine, request, view, 'dag', { nodes, edges, roots: rt.roots, terminals: rt.terminals, acyclic: cycles.length === 0, cycles, truncated: graph.edges.length > edges.length || graph.nodes.size > nodes.length, totalCandidates: graph.edges.length });
}

function flowProjection(engine, state, request, view, entityIds, budget) {
  const graph = graphData(engine, state, entityIds, view.relationIds, { edgeBudget: budget.edgeBudget });
  const nodes = [...graph.nodes.values()].slice(0, budget.nodeBudget); const nodeSet = new Set(nodes.map((node) => node.id));
  const transitions = graph.edges.filter((edge) => nodeSet.has(edge.source) && nodeSet.has(edge.target)).slice(0, budget.edgeBudget).map(transitionFromEdge);
  const rt = rootsAndTerminals(new Map(nodes.map((node) => [node.id,node])), transitions);
  return common(engine, request, view, 'flow', { nodes, transitions, starts: rt.roots, terminals: rt.terminals, truncated: graph.edges.length > transitions.length || graph.nodes.size > nodes.length, totalCandidates: graph.edges.length });
}

function causalProjection(engine, state, request, view, entityIds, budget) {
  const graph = graphData(engine, state, entityIds, view.relationIds, { edgeBudget: budget.edgeBudget });
  const nodes = [...graph.nodes.values()].slice(0, budget.nodeBudget); const nodeSet = new Set(nodes.map((node) => node.id));
  const edges = graph.edges.filter((edge) => nodeSet.has(edge.source) && nodeSet.has(edge.target)).slice(0, budget.edgeBudget).map((edge) => {
    const text = edge.relationLabel.toLowerCase();
    const sign = /inhibit|suppress|decrease|negative|inhibe|diminue|négatif|negatif/.test(text) ? -1 : /activate|stimulat|increase|positive|active|augmente|positif/.test(text) ? 1 : 0;
    return { ...edge, sign };
  });
  const cycles = cycleInfo(new Map(nodes.map((node) => [node.id,node])), edges, 24);
  return common(engine, request, view, 'causal-feedback', { nodes, edges, cycles, truncated: graph.edges.length > edges.length || graph.nodes.size > nodes.length, totalCandidates: graph.edges.length });
}

function matrixProjection(engine, state, request, view, entityIds, budget) {
  const rows = entityIds.map((id) => publicNode(engine, id)).filter(Boolean).slice(0, Math.min(budget.pageSize, 100));
  const rowSet = new Set(rows.map((row) => row.id)); const columns = new Map(); const cells = [];
  for (const assertion of assertionsForEntities(state, [...rowSet], 20000)) {
    if (!rowSet.has(assertion.subject)) continue;
    const relation = engine.relations.get(assertion.relation);
    if (['integer','string'].includes(relation?.valueKind) && (view.relationIds.includes(relation.id) || /dimension|metric|measure|score|value|crit|axe|profil/i.test(relationLabel(relation)))) {
      columns.set(relation.id, { id: relation.id, label: relationLabel(relation), kind: relation.valueKind });
      cells.push({ entityId: assertion.subject, dimensionId: relation.id, value: assertion.value, assertionRef: assertion.id });
    }
    for (const valuation of assertion.valuations || []) {
      if (!valuation.dimension) continue;
      const id = `valuation:${valuation.dimension}`;
      columns.set(id, { id, label: valuation.dimension, kind: valuation.value_semantics || 'valuation', unit: valuation.unit || null });
      cells.push({ entityId: assertion.subject, dimensionId: id, value: valuation.value_state === 'known' ? valuation.value : valuation.value_state, assertionRef: assertion.id });
    }
  }
  const columnList = [...columns.values()].slice(0, 48); const allowedColumns = new Set(columnList.map((column) => column.id));
  const boundedCells = cells.filter((cell) => allowedColumns.has(cell.dimensionId)).slice(0, 2000);
  return common(engine, request, view, 'matrix', { rows, columns: columnList, cells: boundedCells, truncated: rows.length < entityIds.length || columnList.length < columns.size || boundedCells.length < cells.length, totalCandidates: cells.length });
}

function stateRecords(engine, state, entityIds, recipeId, limit) {
  const allowed = new Set(entityIds); const records = [];
  const actionRoles = new Set(['decision','action','organizational_rule','authoritative_constraint']);
  for (const assertion of assertionsForEntities(state, entityIds, limit * 16)) {
    const relation = engine.relations.get(assertion.relation);
    if (!allowed.has(assertion.subject) && !(relation?.valueKind === 'entity' && allowed.has(assertion.value))) continue;
    const valuations = assertion.valuations || []; const coordinates = coordinatesOf(assertion);
    const stateLike = ['observed_state','derived_state'].includes(assertion.recordRole) || valuations.some((v) => v.value_semantics === 'state') || coordinates.some((c) => /\b(state|status|phase|condition|etat|état|statut)\b/i.test(String(c.axis || '')));
    const actionLike = actionRoles.has(assertion.recordRole) || (assertion.actionability?.mode && assertion.actionability.mode !== 'not_applicable');
    if ((recipeId === 'states' && !stateLike) || (recipeId === 'action-context' && !actionLike)) continue;
    records.push({ assertionRef: assertion.id, entity: publicNode(engine, assertion.subject), relationId: assertion.relation, relationLabel: relationLabel(relation), status: assertion.status || null, recordRole: assertion.recordRole || null, actionability: publicActionability(assertion.actionability), valuations: valuations.map(publicValuation).filter(Boolean).slice(0,12), coordinates: coordinates.map(publicCoordinate).filter(Boolean).slice(0,12), sourceRefs: unique((assertion.sourceRefs || []).filter((id) => engine.sources.has(id))) });
    if (records.length >= limit * 4) break;
  }
  return records;
}

function stateFlowProjection(engine, state, profiler, request, view, entityIds, budget) {
  const records = stateRecords(engine, state, entityIds, request.recipeId, budget.pageSize);
  const relationIds = unique([...view.relationIds, ...profiler.relationsFor('stateMachine').map((r) => r.id), ...profiler.relationsFor('sequence').map((r) => r.id)]);
  const graph = graphData(engine, state, entityIds, relationIds, { edgeBudget: budget.edgeBudget });
  const page = windowPage(engine, request, { recipeId: request.recipeId, query: request.query, selected: request.selectedEntityId }, records, budget.pageSize);
  const transitions = graph.edges.slice(0, budget.edgeBudget).map(transitionFromEdge);
  return common(engine, request, view, 'state-flow', { records: page.page, transitions, semantics: request.recipeId === 'action-context' ? 'actionability-is-not-execution-authority' : 'derived-navigation-projection', nextCursor: page.nextCursor, truncated: page.truncated || graph.edges.length > transitions.length, totalCandidates: records.length });
}

function traceabilityProjection(engine, state, request, view, entityIds, budget) {
  const allowed = new Set(entityIds); const nodes = new Map(); const edges = [];
  const addNode = (id, type, label, meta = {}) => { if (!nodes.has(id)) nodes.set(id, { id, type, label: String(label ?? id), ...meta }); };
  for (const id of entityIds) { const entity = publicNode(engine,id); if (entity) addNode(`entity:${id}`,entity.type,entity.label,{kind:'entity',entityId:id}); }
  for (const assertion of assertionsForEntities(state, entityIds, budget.edgeBudget * 12)) {
    const relation = engine.relations.get(assertion.relation);
    if (!allowed.has(assertion.subject) && !(relation?.valueKind === 'entity' && allowed.has(assertion.value))) continue;
    const aId = `assertion:${assertion.id}`; addNode(aId,'assertion',relationLabel(relation),{kind:'assertion',assertionRef:assertion.id,status:assertion.status || null});
    addNode(`entity:${assertion.subject}`,engine.entities.get(assertion.subject)?.type || 'entity',engine.entities.get(assertion.subject)?.label || assertion.subject,{kind:'entity',entityId:assertion.subject});
    edges.push({ id:`subject:${assertion.id}`, source:`entity:${assertion.subject}`, target:aId, kind:'asserts' });
    for (const sourceId of assertion.sourceRefs || []) if (engine.sources.has(sourceId)) { addNode(`source:${sourceId}`,'source',engine.sources.get(sourceId).title || sourceId,{kind:'source',sourceRef:sourceId}); edges.push({id:`source:${assertion.id}:${sourceId}`,source:aId,target:`source:${sourceId}`,kind:'source'}); }
    for (const ref of assertion.evidenceRefs || []) if (visibleRef(engine,state,ref)) { const target = state.assertions.has(ref) ? `assertion:${ref}` : `source:${ref}`; const label = state.assertions.has(ref) ? relationLabel(engine.relations.get(state.assertions.get(ref).relation)) : engine.sources.get(ref)?.title || ref; addNode(target,state.assertions.has(ref)?'assertion':'source',label,{kind:state.assertions.has(ref)?'assertion':'source',reference:ref}); edges.push({id:`evidence:${assertion.id}:${ref}`,source:aId,target,kind:'evidence'}); }
    for (const ref of assertion.provenanceRefs || []) if (visibleRef(engine,state,ref)) { const target = state.assertions.has(ref) ? `assertion:${ref}` : `source:${ref}`; const label = state.assertions.has(ref) ? relationLabel(engine.relations.get(state.assertions.get(ref).relation)) : engine.sources.get(ref)?.title || ref; addNode(target,state.assertions.has(ref)?'assertion':'source',label,{kind:state.assertions.has(ref)?'assertion':'source',reference:ref}); edges.push({id:`provenance:${assertion.id}:${ref}`,source:aId,target,kind:'provenance'}); }
    if (request.recipeId === 'divergences') for (const ref of assertion.conflictsWith || []) if (state.assertions.has(ref)) { const target=`assertion:${ref}`; addNode(target,'assertion',relationLabel(engine.relations.get(state.assertions.get(ref).relation)),{kind:'assertion',assertionRef:ref}); edges.push({id:`conflict:${assertion.id}:${ref}`,source:aId,target,kind:'conflict'}); }
    if (edges.length >= budget.edgeBudget * 4) break;
  }
  const nodeList=[...nodes.values()].slice(0,budget.nodeBudget); const nodeSet=new Set(nodeList.map((node)=>node.id)); const edgeList=edges.filter((edge)=>nodeSet.has(edge.source)&&nodeSet.has(edge.target)).slice(0,budget.edgeBudget);
  return common(engine,request,view,'traceability',{nodes:nodeList,edges:edgeList,truncated:nodes.size>nodeList.length||edges.length>edgeList.length,totalCandidates:edges.length});
}

function multiscaleProjection(engine, state, profiler, request, view, entityIds, budget) {
  const selected = new Set(entityIds); const layers = new Map(); const memberships=[];
  for (const assertion of assertionsForEntities(state, entityIds, 12000)) {
    const relation=engine.relations.get(assertion.relation); if(!selected.has(assertion.subject)&&!(relation?.valueKind==='entity'&&selected.has(assertion.value))) continue;
    for(const c of coordinatesOf(assertion)) if(/\b(scale|layer|niveau|couche|echelle|échelle)\b/i.test(String(c.axis||''))){const value=String(c.value); const id=`${c.axis}:${value}`; layers.set(id,{id,axis:c.axis,label:value}); memberships.push({entityId:assertion.subject,layerId:id,assertionRef:assertion.id});}
  }
  const relationIds=unique([...view.relationIds,...profiler.relationsFor('multiScale').map((r)=>r.id),...profiler.relationsFor('multiplex').map((r)=>r.id)]);
  const graph=graphData(engine,state,entityIds,relationIds,{edgeBudget:budget.edgeBudget}); const nodes=[...graph.nodes.values()].slice(0,budget.nodeBudget); const nodeSet=new Set(nodes.map((n)=>n.id)); const crossLinks=graph.edges.filter((e)=>nodeSet.has(e.source)&&nodeSet.has(e.target)).slice(0,budget.edgeBudget);
  return common(engine,request,view,'multiscale',{layers:[...layers.values()].slice(0,64),memberships:memberships.slice(0,1200),nodes,crossLinks,truncated:graph.nodes.size>nodes.length||graph.edges.length>crossLinks.length||layers.size>64,totalCandidates:memberships.length+graph.edges.length});
}

function spatialProjection(engine, state, profiler, request, view, entityIds, budget) {
  const points=[]; const places=[]; const selected=new Set(entityIds);
  for(const id of entityIds){
    const values={};
    for(const assertion of state.assertionsByEntity?.get(id) || []){
      const relation=engine.relations.get(assertion.relation); if(assertion.subject!==id) continue;
      for(const c of coordinatesOf(assertion)){const axis=String(c.axis||'').toLowerCase(); if(/lat/.test(axis)) values.lat=Number(c.value); if(/lon|lng|longitude/.test(axis)) values.long=Number(c.value); if(/place|location|region|country|city|lieu|ville|pays/.test(axis)) values.label=String(c.value);}
      if(relation?.valueKind==='entity'&&profiler.tagsForRelation(relation.id,engine.entities.get(id)?.type).includes('spatial')&&engine.entities.has(assertion.value)) places.push({entity:publicNode(engine,id),place:publicNode(engine,assertion.value),relationId:relation.id,relationLabel:relationLabel(relation),assertionRef:assertion.id});
    }
    if(Number.isFinite(values.lat)&&Number.isFinite(values.long)) points.push({entity:publicNode(engine,id),lat:values.lat,long:values.long,label:values.label||engine.entities.get(id)?.label||id});
  }
  return common(engine,request,view,'spatial',{points:points.slice(0,budget.nodeBudget),places:places.slice(0,budget.edgeBudget),truncated:points.length>budget.nodeBudget||places.length>budget.edgeBudget,totalCandidates:points.length+places.length});
}

export function projectAdaptiveNavigation(engine, request, lenses) {
  if (!request || typeof request !== 'object' || Array.isArray(request) || !request.query || !request.recipeId) fail('INVALID_QUERY', 'Projection adaptative invalide.');
  const { state, profiler, view } = matchingPlanView(engine, request, lenses);
  const budget = budgets(request); const entityIds = selectedIds(engine, request, Math.max(budget.nodeBudget, budget.pageSize));
  switch (view.rendererId) {
    case 'timeline-lineage': return timelineProjection(engine,state,profiler,request,view,entityIds,budget);
    case 'tree': return treeProjection(engine,state,request,view,entityIds,budget);
    case 'dag-proof': return dagProjection(engine,state,request,view,entityIds,budget);
    case 'flow-path': return flowProjection(engine,state,request,view,entityIds,budget);
    case 'causal-feedback': return causalProjection(engine,state,request,view,entityIds,budget);
    case 'matrix-profile': return matrixProjection(engine,state,request,view,entityIds,budget);
    case 'state-flow': return stateFlowProjection(engine,state,profiler,request,view,entityIds,budget);
    case 'traceability': return traceabilityProjection(engine,state,request,view,entityIds,budget);
    case 'multiscale-layer': return multiscaleProjection(engine,state,profiler,request,view,entityIds,budget);
    case 'spatial': return spatialProjection(engine,state,profiler,request,view,entityIds,budget);
    default: fail('UNSUPPORTED_CAPABILITY','Cette projection est servie par une vue générique et ne nécessite pas /api/navigation/project.',422);
  }
}
