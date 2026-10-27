const AFFORDANCES = [
  'network',
  'temporal',
  'hierarchy',
  'dependency',
  'sequence',
  'stateMachine',
  'conditionalTransition',
  'causal',
  'signedCausal',
  'cycle',
  'spatial',
  'multiScale',
  'multiplex',
  'proof',
  'argumentation',
  'multidimensional',
  'quantitative',
  'evidential',
  'provenance',
  'versioned',
  'eventStream',
  'resourceAllocation',
  'classification',
  'conflict',
  'succession',
  'lineage',
  'actionability',
  'stateful',
];

const PATTERNS = {
  temporal: /\b(time|date|dated|year|years|epoch|period|temporal|chronolog|before|after|preced|followed|occurrence|effective|start|end|duration|timeline|history|historical|temps|date|annee|année|periode|période|chronolog|avant|apres|après)\b/i,
  hierarchy: /\b(parent|child|part of|contains|contain|subtype|supertype|broader|narrower|hierarch|level|layer|scale|section|branch|component|member of|belongs to|niveau|couche|echelle|échelle|partie|compose|composé)\b/i,
  dependency: /\b(depends|dependency|prereq|prerequisite|requires|required|uses|derived from|derivation|input|basis|supports|depends on|dependance|dépendance|prerequis|prérequis|requis|derive|dérive)\b/i,
  sequence: /\b(next|previous|preced|follow|step|stage|sequence|path|pathway|flow|transition|route|phase|workflow|etape|étape|parcours|chemin|flux|transition)\b/i,
  stateMachine: /\b(state|status|workflow|step|stage|transition|current step|phase|etat|état|statut|etape|étape)\b/i,
  conditionalTransition: /\b(condition|conditional|eligible|eligibility|admission|requirement|prereq|prerequisite|may transition|can transition|allowed|condition|admiss|prerequis|prérequis|exigence|peut passer|transition)\b/i,
  causal: /\b(cause|causal|influence|affect|effect|lead to|trigger|enable|inhibit|activate|regulate|mechanism|stimulate|suppress|cause|influence|effet|declenche|déclenche|active|inhibe|regule|régule|mecanisme|mécanisme)\b/i,
  signedCausal: /\b(positive|negative|activate|activation|inhibit|inhibition|stimulate|suppress|increase|increases|decrease|decreases|upreg|downreg|positif|negatif|négatif|active|inhibe|stimule|augmente|diminue)\b/i,
  spatial: /\b(place|location|located|region|country|city|geo|latitude|longitude|coordinate|map|spatial|lieu|localisation|region|région|pays|ville|carte|spatial)\b/i,
  multiScale: /\b(scale|layer|cross scale|cross layer|system|subsystem|molecular|cell|cellular|tissue|organ|organism|niveau|couche|echelle|échelle|systeme|système|cellule|tissu|organe)\b/i,
  proof: /\b(proof|prove|theorem|lemma|proposition|axiom|corollary|counterexample|refutation|demonstration|formal|preuve|theoreme|théorème|lemme|proposition|axiome|corollaire|contre exemple|contre-exemple|refutation|réfutation|demonstration|démonstration)\b/i,
  argumentation: /\b(argument|claim|position|question|debate|support|oppose|agreement|disagreement|convergen|divergen|doctrine|thesis|assertion|argument|position|question|debat|débat|soutient|oppose|convergen|divergen|doctrine|these|thèse)\b/i,
  multidimensional: /\b(dimension|axis|profile|criterion|criteria|score|index|metric|measure|value dimension|dimension|axe|profil|critere|critère|score|indice|metrique|métrique|mesure)\b/i,
  versioned: /\b(version|revision|revised|effective|valid from|valid to|supersed|edition|version|revision|révision|effectif|valide depuis|remplace|édition)\b/i,
  eventStream: /\b(event|occurrence|observation|recorded at|created at|effective at|event|événement|occurrence|observation|cree le|créé le)\b/i,
  resourceAllocation: /\b(resource|capacity|capability|booking|reservation|allocation|role|staff|bed|slot|resource|ressource|capacite|capacité|reservation|réservation|allocation|role|rôle)\b/i,
  classification: /\b(type|class|category|taxonomy|kind|family|group|classification|type|classe|categorie|catégorie|taxonomie|famille|groupe)\b/i,
  conflict: /\b(conflict|conflicts|dispute|contradict|oppos|divergen|conflit|contredit|contradiction|divergen)\b/i,
  succession: /\b(supersed|replace|revision|successor|predecessor|remplace|successeur|prédécesseur|revision|révision)\b/i,
  lineage: /\b(lineage|derived from|derivation|origin|ancestor|descendant|lignée|derive|dérive|origine|ancêtre|descendant)\b/i,
  actionability: /\b(action|decision|review|approval|manual|automatic|prohibited|action|décision|revision humaine|révision humaine|approbation|manuel|automatique|interdit)\b/i,
  stateful: /\b(state|status|phase|condition|etat|état|statut|phase|condition)\b/i,
};

function normalized(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[_:./-]+/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .toLowerCase();
}

export function humanizeIdentifier(value) {
  const text = String(value || '')
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_:./-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : '';
}

function relationText(relation) {
  return normalized([
    relation.id,
    relation.label?.fr,
    relation.label?.en,
    relation.range,
    ...(relation.domain || []),
  ].join(' '));
}

function typeText(types) {
  return normalized((types || []).join(' '));
}

function scoreFrom(weight) {
  return Math.max(0, Math.min(1, Math.round(weight * 100) / 100));
}

function emptyScores() {
  return Object.fromEntries(AFFORDANCES.map((id) => [id, { score: 0, evidence: [] }]));
}

function add(scores, capability, amount, evidence) {
  const target = scores[capability];
  if (!target) return;
  target.score = scoreFrom(target.score + amount);
  if (evidence && !target.evidence.includes(evidence) && target.evidence.length < 8)
    target.evidence.push(evidence);
}

function tagRelation(relation) {
  const tags = new Set();
  const text = relationText(relation);
  if (relation.valueKind === 'entity') tags.add('network');
  if (relation.valueKind === 'interval') tags.add('temporal');
  if (relation.valueKind === 'integer') tags.add('quantitative');
  for (const [capability, pattern] of Object.entries(PATTERNS))
    if (pattern.test(text)) tags.add(capability);
  if (tags.has('signedCausal')) tags.add('causal');
  if (tags.has('stateMachine') && tags.has('sequence')) tags.add('conditionalTransition');
  return [...tags];
}

function relationEvidence(relation) {
  return relation.label?.fr || relation.label?.en || humanizeIdentifier(relation.id);
}

function detectDirectedCycle(assertionsByRelation, relationById, relationTags, allowedTypes = null) {
  const interesting = new Set(
    Object.entries(relationTags)
      .filter(([, tags]) => tags.some((tag) => ['causal', 'sequence', 'dependency', 'hierarchy'].includes(tag)))
      .map(([id]) => id),
  );
  if (!interesting.size) return false;
  const adjacency = new Map();
  let edges = 0;
  for (const relationId of interesting) {
    const relation = relationById.get(relationId);
    if (!relation || relation.valueKind !== 'entity') continue;
    if (allowedTypes && !relation.domain.some((type) => allowedTypes.has(type))) continue;
    for (const assertion of assertionsByRelation.get(relationId) || []) {
      if (edges >= 50000) break;
      const list = adjacency.get(assertion.subject) || [];
      list.push(assertion.value);
      adjacency.set(assertion.subject, list);
      edges += 1;
    }
    if (edges >= 50000) break;
  }
  if (!edges) return false;
  // Iterative DFS avoids call-stack exhaustion on very deep DAGs while keeping
  // the same bounded inspection budget. state: 1 = visiting, 2 = complete.
  const state = new Map();
  let inspected = 0;
  for (const start of adjacency.keys()) {
    if (state.get(start) === 2) continue;
    if (++inspected > 20000) return false;
    state.set(start, 1);
    const stack = [{ node: start, index: 0, neighbors: adjacency.get(start) || [] }];
    while (stack.length) {
      const frame = stack[stack.length - 1];
      if (frame.index >= frame.neighbors.length) {
        state.set(frame.node, 2);
        stack.pop();
        continue;
      }
      const next = frame.neighbors[frame.index++];
      const nextState = state.get(next) || 0;
      if (nextState === 1) return true;
      if (nextState === 2) continue;
      if (++inspected > 20000) return false;
      state.set(next, 1);
      stack.push({ node: next, index: 0, neighbors: adjacency.get(next) || [] });
    }
  }
  return false;
}


function structuralSummary(pack) {
  return pack.integration?.metadata?.structuralSummary || pack.importRecord?.structuralSummary || null;
}

function totalObjectValues(object) {
  return Object.values(object || {}).reduce((sum, value) => sum + (Number(value) || 0), 0);
}

function axisCapabilities(axis) {
  const text = normalized(axis);
  const tags = [];
  for (const [capability, pattern] of Object.entries(PATTERNS)) if (pattern.test(text)) tags.push(capability);
  if (/\b(scale|layer|niveau|couche|echelle)\b/i.test(text)) tags.push('multiScale');
  if (/\b(time|date|year|period|phase|effective|temps|annee|date|periode)\b/i.test(text)) tags.push('temporal');
  if (/\b(place|location|geo|lat|lon|region|lieu|localisation)\b/i.test(text)) tags.push('spatial');
  return [...new Set(tags)];
}

function applyV6StructuralSummary(scores, pack) {
  const summary = structuralSummary(pack);
  if (!summary || typeof summary !== 'object') return;
  for (const axis of Object.keys(summary.coordinateAxes || {})) {
    for (const capability of axisCapabilities(axis)) add(scores, capability, 0.32, `coordonnée v6: ${axis}`);
  }
  const semantics = summary.valuationSemantics || {};
  const quantitative = ['scalar', 'ordinal', 'probability', 'distribution', 'vector', 'interval']
    .reduce((sum, key) => sum + (semantics[key] || 0), 0);
  if (quantitative) add(scores, 'quantitative', Math.min(0.9, 0.35 + Math.log10(quantitative + 1) * 0.22), `${quantitative} valuations quantitatives v6`);
  if ((semantics.temporal || 0) > 0) add(scores, 'temporal', 0.58, `${semantics.temporal} valuations temporelles v6`);
  if ((semantics.state || 0) > 0) add(scores, 'stateful', 0.62, `${semantics.state} valuations d’état v6`);
  const dimensions = Object.keys(summary.valuationDimensions || {}).length;
  if (dimensions >= 2) add(scores, 'multidimensional', Math.min(0.95, 0.3 + Math.log10(dimensions + 1) * 0.3), `${dimensions} dimensions de valuation v6`);
  const roles = summary.recordRoles || {};
  if ((roles.observed_state || 0) > 0) {
    add(scores, 'stateful', 0.42, `${roles.observed_state} états observés v6`);
    if (scores.temporal.score >= 0.25) add(scores, 'eventStream', 0.35, 'états observés contextualisés dans le temps');
  }
  const decisionAction = (roles.decision || 0) + (roles.action || 0) + (roles.organizational_rule || 0) + (roles.authoritative_constraint || 0);
  if (decisionAction) add(scores, 'actionability', Math.min(0.92, 0.35 + Math.log10(decisionAction + 1) * 0.24), `${decisionAction} enregistrements de décision/action/règle`);
  if ((roles.structural_record || 0) > 0) add(scores, 'classification', 0.22, 'enregistrements structurels v6');
  const actionable = Object.entries(summary.actionabilityModes || {}).filter(([mode]) => mode !== 'not_applicable').reduce((sum, [, count]) => sum + count, 0);
  if (actionable) add(scores, 'actionability', Math.min(1, 0.48 + Math.log10(actionable + 1) * 0.2), `${actionable} assertions avec actionabilité explicite`);
  if (summary.conflicts) add(scores, 'conflict', Math.min(0.95, 0.52 + Math.log10(summary.conflicts + 1) * 0.18), `${summary.conflicts} liens de conflit v6`);
  if (summary.supersedes) {
    add(scores, 'succession', Math.min(0.95, 0.52 + Math.log10(summary.supersedes + 1) * 0.18), `${summary.supersedes} liens de succession v6`);
    add(scores, 'versioned', 0.28, 'succession explicite par supersedes');
  }
  if (summary.lineage) {
    add(scores, 'lineage', Math.min(0.95, 0.5 + Math.log10(summary.lineage + 1) * 0.2), `${summary.lineage} assertions avec lineage v6`);
    add(scores, 'versioned', 0.22, 'lineage explicite v6');
  }
  if (summary.evidenceRefs) add(scores, 'evidential', Math.min(0.98, 0.4 + Math.log10(summary.evidenceRefs + 1) * 0.2), `${summary.evidenceRefs} références d’évidence v6`);
  if (summary.provenanceRefs || (pack.integration?.metadata?.provenanceCount || 0)) add(scores, 'provenance', 0.6, 'provenance v6 explicite');
}


function valuesFromCoordinates(assertion) {
  if (Array.isArray(assertion.coordinates)) return assertion.coordinates;
  if (assertion.coordinates && typeof assertion.coordinates === 'object')
    return Object.entries(assertion.coordinates).map(([axis, value]) => ({ axis, value }));
  return [];
}

function emptyMetadataCounts() {
  return {
    stateful: 0, actionability: 0, conflict: 0, succession: 0, lineage: 0,
    evidential: 0, provenance: 0, temporal: 0, spatial: 0, multiScale: 0,
    quantitative: 0, multidimensional: new Set(), eventStream: 0,
  };
}

function accumulateAssertionMetadata(counts, assertion) {
  const actionRoles = new Set(['decision', 'action', 'organizational_rule', 'authoritative_constraint']);
  const stateRoles = new Set(['observed_state', 'derived_state']);
  const eventRoles = new Set(['event', 'observation', 'measurement']);
  if (stateRoles.has(assertion.recordRole)) counts.stateful++;
  if (eventRoles.has(assertion.recordRole)) counts.eventStream++;
  if (actionRoles.has(assertion.recordRole) || (assertion.actionability?.mode && assertion.actionability.mode !== 'not_applicable')) counts.actionability++;
  counts.conflict += (assertion.conflictsWith || []).length;
  counts.succession += (assertion.supersedes || []).length;
  if (assertion.lineage) counts.lineage++;
  counts.evidential += (assertion.evidenceRefs || []).length + (assertion.sourceRefs || []).length;
  counts.provenance += (assertion.provenanceRefs || []).length;
  for (const coordinate of valuesFromCoordinates(assertion)) {
    for (const affordance of axisCapabilities(coordinate.axis)) counts[affordance] = (counts[affordance] || 0) + 1;
  }
  for (const valuation of assertion.valuations || []) {
    if (valuation.dimension) counts.multidimensional.add(valuation.dimension);
    if (valuation.value_semantics === 'temporal') counts.temporal++;
    if (valuation.value_semantics === 'state') counts.stateful++;
    if (['scalar','ordinal','probability','distribution','vector','interval'].includes(valuation.value_semantics)) counts.quantitative++;
  }
  return counts;
}

function mergeMetadataCounts(target, source) {
  if (!source) return target;
  for (const [key, value] of Object.entries(source)) {
    if (key === 'multidimensional') for (const item of value || []) target.multidimensional.add(item);
    else target[key] = (target[key] || 0) + (Number(value) || 0);
  }
  return target;
}

function applyAssertionMetadataSignals(scores, relevantRelations, assertionsByRelation, metadataStatsByRelation = null) {
  const ids = new Set(relevantRelations.map((relation) => relation.id));
  const counts = emptyMetadataCounts();
  if (metadataStatsByRelation) {
    for (const relationId of ids) mergeMetadataCounts(counts, metadataStatsByRelation.get(relationId));
  } else {
    for (const relationId of ids) for (const assertion of assertionsByRelation.get(relationId) || []) accumulateAssertionMetadata(counts, assertion);
  }
  const addCount = (id, count, base, label) => {
    if (!count) return;
    add(scores, id, Math.min(0.95, base + Math.log10(count + 1) * 0.18), `${count} ${label}`);
  };
  addCount('stateful', counts.stateful, 0.38, 'états visibles');
  addCount('eventStream', counts.eventStream, 0.30, 'événements visibles');
  addCount('actionability', counts.actionability, 0.40, 'conditions d’action visibles');
  addCount('conflict', counts.conflict, 0.45, 'conflits visibles');
  addCount('succession', counts.succession, 0.44, 'successions visibles');
  addCount('lineage', counts.lineage, 0.44, 'lignées visibles');
  addCount('evidential', counts.evidential, 0.30, 'références d’évidence/source visibles');
  addCount('provenance', counts.provenance, 0.36, 'références de provenance visibles');
  addCount('temporal', counts.temporal, 0.38, 'repères temporels visibles');
  addCount('spatial', counts.spatial, 0.34, 'coordonnées spatiales visibles');
  addCount('multiScale', counts.multiScale, 0.34, 'coordonnées d’échelle visibles');
  addCount('quantitative', counts.quantitative, 0.34, 'valuations quantitatives visibles');
  if (counts.multidimensional.size >= 2)
    add(scores, 'multidimensional', Math.min(0.95, 0.42 + Math.log10(counts.multidimensional.size + 1) * 0.22), `${counts.multidimensional.size} dimensions visibles`);
}
function normalizeCapabilityScore(value) {
  if (value === true) return 1;
  if (value === false || value === null || value === undefined) return null;
  if (typeof value === 'number' && Number.isFinite(value)) return Math.max(0, Math.min(1, value));
  if (typeof value === 'object' && value && typeof value.score === 'number' && Number.isFinite(value.score))
    return Math.max(0, Math.min(1, value.score));
  return null;
}

function applyDeclaredAffordances(scores, hints, { requireObserved = false } = {}) {
  if (!hints || typeof hints !== 'object') return;
  const declared = { ...(hints.capabilities || {}), ...(hints.affordances || {}) };
  for (const [capability, value] of Object.entries(declared)) {
    if (!AFFORDANCES.includes(capability)) continue;
    if (requireObserved && scores[capability].score <= 0) continue;
    const score = normalizeCapabilityScore(value);
    if (score === null) continue;
    // Declared structure is authoritative positive evidence. It can strengthen
    // inference without making a weak/missing declaration erase observed data.
    if (score > scores[capability].score) scores[capability].score = scoreFrom(score);
    const evidence = typeof value === 'object' && typeof value.reason === 'string'
      ? value.reason
      : 'affordance déclarée pour Konstellation';
    if (!scores[capability].evidence.includes(evidence) && scores[capability].evidence.length < 8)
      scores[capability].evidence.unshift(evidence);
  }
}

function declaredRelationCapabilities(hints) {
  const output = new Map();
  if (!hints || typeof hints !== 'object') return output;
  const declared = { ...(hints.relationCapabilities || {}), ...(hints.relationAffordances || {}) };
  for (const [relationId, capabilities] of Object.entries(declared)) {
    if (!Array.isArray(capabilities)) continue;
    output.set(relationId, capabilities.filter((id) => AFFORDANCES.includes(id)));
  }
  return output;
}

function hintsForEntityType(hints, entityType) {
  if (!hints || typeof hints !== 'object') return null;
  if (!entityType) return hints;
  const local = hints.entityTypes?.[entityType];
  if (!local || typeof local !== 'object') return hints;
  return {
    ...hints,
    ...local,
    capabilities: { ...(hints.capabilities || {}), ...(local.capabilities || {}) },
    affordances: { ...(hints.affordances || {}), ...(local.affordances || {}) },
    relationCapabilities: {
      ...(hints.relationCapabilities || {}),
      ...(local.relationCapabilities || {}),
    },
    relationAffordances: {
      ...(hints.relationAffordances || {}),
      ...(local.relationAffordances || {}),
    },
  };
}

function summarize(pack, relations, relationTags, entityTypes, assertionStatsByRelation, assertionsByRelation, relationById, declaredHints = null, options = {}) {
  const scores = emptyScores();
  const relevantTypeSet = new Set(entityTypes || pack.registry.entityTypes || []);
  const relevantRelations = relations.filter((relation) =>
    relation.domain.some((type) => relevantTypeSet.has(type)),
  );
  const entityRelations = relevantRelations.filter((r) => r.valueKind === 'entity');
  const intervalRelations = relevantRelations.filter((r) => r.valueKind === 'interval');
  const integerRelations = relevantRelations.filter((r) => r.valueKind === 'integer');
  if (entityRelations.length) add(scores, 'network', Math.min(1, 0.45 + entityRelations.length * 0.045), `${entityRelations.length} relations entre entités`);
  if (intervalRelations.length) add(scores, 'temporal', Math.min(1, 0.65 + intervalRelations.length * 0.06), `${intervalRelations.length} relations temporelles explicites`);
  if (integerRelations.length) add(scores, 'quantitative', Math.min(0.9, 0.45 + integerRelations.length * 0.05), `${integerRelations.length} mesures entières`);

  for (const relation of relevantRelations) {
    const tags = relationTags[relation.id] || [];
    for (const tag of tags) {
      if (tag === 'network') continue;
      const base = relation.valueKind === 'interval' && tag === 'temporal' ? 0.4 : 0.38;
      add(scores, tag, base, relationEvidence(relation));
    }
  }

  const relevantTypes = [...relevantTypeSet];
  const typesText = typeText(relevantTypes);
  for (const [capability, pattern] of Object.entries(PATTERNS))
    if (pattern.test(typesText)) add(scores, capability, 0.4, `types: ${relevantTypes.slice(0, 6).join(', ')}`);

  const sourceCount = (pack.sources || []).length;
  let assertionCount = 0;
  let sourcedCount = 0;
  for (const relation of relevantRelations) {
    const stats = assertionStatsByRelation.get(relation.id);
    if (!stats) continue;
    assertionCount += stats.count;
    sourcedCount += stats.sourced;
  }
  if (assertionCount) {
    const ratio = sourcedCount / assertionCount;
    if (ratio > 0.2) add(scores, 'evidential', Math.min(1, 0.3 + ratio * 0.65), `${Math.round(ratio * 100)} % des assertions sont sourcées`);
    if (sourceCount && ratio > 0.1) add(scores, 'provenance', Math.min(1, 0.35 + ratio * 0.55), `${sourceCount} sources disponibles`);
  }

  if (entityRelations.length >= 5) add(scores, 'multiplex', Math.min(0.92, 0.35 + entityRelations.length * 0.045), `${entityRelations.length} familles relationnelles`);
  if (scores.multiScale.score >= 0.45 && scores.network.score >= 0.5) add(scores, 'multiplex', 0.18, 'structure multi-échelle et relationnelle');
  if (scores.temporal.score >= 0.45 && scores.eventStream.score >= 0.25) add(scores, 'eventStream', 0.25, 'événements associés à une structure temporelle');
  if (scores.stateMachine.score >= 0.4 && scores.conditionalTransition.score >= 0.25) add(scores, 'conditionalTransition', 0.28, 'transitions conditionnelles dans un workflow');
  if (scores.multidimensional.score >= 0.3 && scores.quantitative.score >= 0.3) add(scores, 'multidimensional', 0.25, 'dimensions accompagnées de mesures');
  if (scores.causal.score >= 0.35 && scores.signedCausal.score >= 0.25) add(scores, 'signedCausal', 0.18, 'causalité directionnelle signée');
  if (detectDirectedCycle(assertionsByRelation, relationById, relationTags, relevantTypeSet)) add(scores, 'cycle', 0.82, 'cycle dirigé détecté dans les relations structurantes');

  applyAssertionMetadataSignals(scores, relevantRelations, assertionsByRelation, options.metadataStatsByRelation || null);
  if (options.trustStructuralSummary !== false) applyV6StructuralSummary(scores, pack);
  // A Reader Policy is a confidentiality boundary. Pack-level declared scores
  // and free-text reasons may summarize hidden records and therefore must not
  // influence a policy-scoped plan. Relation affordance mappings remain usable
  // only for relation definitions that have visible assertions (filtered above).
  if (options.policyScoped !== true) applyDeclaredAffordances(scores, declaredHints);
  return scores;
}

export class StructuralProfiler {
  constructor(pack, options = {}) {
    this.pack = pack;
    this.options = options;
    this.relations = pack.registry.relations || [];
    this.relationById = new Map(this.relations.map((relation) => [relation.id, relation]));
    this.assertionsByRelation = new Map();
    this.assertionStatsByRelation = new Map();
    this.metadataStatsByRelation = new Map();
    for (const assertion of pack.assertions || []) {
      const rows = this.assertionsByRelation.get(assertion.relation) || [];
      rows.push(assertion);
      this.assertionsByRelation.set(assertion.relation, rows);
      const stats = this.assertionStatsByRelation.get(assertion.relation) || { count: 0, sourced: 0 };
      stats.count += 1;
      if ((assertion.sourceRefs || []).length) stats.sourced += 1;
      this.assertionStatsByRelation.set(assertion.relation, stats);
      const metadata = this.metadataStatsByRelation.get(assertion.relation) || emptyMetadataCounts();
      accumulateAssertionMetadata(metadata, assertion);
      this.metadataStatsByRelation.set(assertion.relation, metadata);
    }
    this.assertionsByEntity = new Map();
    for (const assertion of pack.assertions || []) {
      const relation = this.relationById.get(assertion.relation);
      for (const id of [assertion.subject, ...(relation?.valueKind === 'entity' ? [assertion.value] : [])]) {
        const rows = this.assertionsByEntity.get(id) || [];
        rows.push(assertion);
        this.assertionsByEntity.set(id, rows);
      }
    }
    this.declaredHints = pack.navigationHints || pack.integration?.navigationHints || null;
    const declaredRelationTags = declaredRelationCapabilities(this.declaredHints);
    this.relationTags = Object.fromEntries(
      this.relations.map((relation) => [
        relation.id,
        [...new Set([...tagRelation(relation), ...(declaredRelationTags.get(relation.id) || [])])],
      ]),
    );
    this.entityTypeLabels = Object.fromEntries(
      (pack.registry.entityTypes || []).map((type) => [type, humanizeIdentifier(type)]),
    );
    this.global = this.#profile(null);
    this.byType = new Map();
    this.byFocus = new Map();
  }

  #profile(entityType) {
    const entityTypes = entityType ? [entityType] : this.pack.registry.entityTypes;
    const relationVisible = (relation) => this.options.policyScoped !== true || (this.assertionStatsByRelation.get(relation.id)?.count || 0) > 0;
    const relevantRelations = (entityType
      ? this.relations.filter((r) => r.domain.includes(entityType) || r.range === entityType)
      : this.relations).filter(relationVisible);
    const localHints = hintsForEntityType(this.declaredHints, entityType);
    const localDeclaredRelationTags = declaredRelationCapabilities(localHints);
    const localRelationTags = Object.fromEntries(
      relevantRelations.map((relation) => [
        relation.id,
        [...new Set([
          ...(this.relationTags[relation.id] || []),
          ...(localDeclaredRelationTags.get(relation.id) || []),
        ])],
      ]),
    );
    const scores = summarize(
      this.pack,
      relevantRelations,
      localRelationTags,
      entityTypes,
      this.assertionStatsByRelation,
      this.assertionsByRelation,
      this.relationById,
      localHints,
      { ...this.options, metadataStatsByRelation: this.metadataStatsByRelation },
    );
    return {
      schemaVersion: '1.0',
      scope: entityType ? 'entity-type' : 'pack',
      entityType,
      entityTypeLabels: this.entityTypeLabels,
      affordances: scores,
      relationTags: localRelationTags,
      stats: {
        entityTypes: entityTypes.length,
        relations: relevantRelations.length,
        entityRelations: relevantRelations.filter((r) => r.valueKind === 'entity').length,
        temporalRelations: relevantRelations.filter((r) => r.valueKind === 'interval').length,
      },
    };
  }

  forType(entityType) {
    if (!entityType) return this.global;
    if (!this.byType.has(entityType)) this.byType.set(entityType, this.#profile(entityType));
    return this.byType.get(entityType);
  }

  tagsForRelation(id, entityType = null) {
    const declared = declaredRelationCapabilities(hintsForEntityType(this.declaredHints, entityType));
    return [...new Set([...(this.relationTags[id] || []), ...(declared.get(id) || [])])];
  }

  relationsFor(capability, entityType = null) {
    return this.relations.filter((relation) => {
      if (this.options.policyScoped === true && !(this.assertionStatsByRelation.get(relation.id)?.count > 0)) return false;
      if (entityType && !relation.domain.includes(entityType) && relation.range !== entityType) return false;
      return this.tagsForRelation(relation.id, entityType).includes(capability);
    });
  }



  forResultSet(entityIds, entityType = null) {
    const ids = new Set((entityIds || []).filter((id) => typeof id === 'string'));
    if (!ids.size) return this.forType(entityType);
    const key = `result|${entityType || ''}|${[...ids].sort().join(',')}`;
    if (this.byFocus.has(key)) return this.byFocus.get(key);
    const assertions = [];
    const seen = new Set();
    for (const id of ids) for (const assertion of this.assertionsByEntity.get(id) || []) {
      if (!seen.has(assertion.id)) { seen.add(assertion.id); assertions.push(assertion); }
    }
    if (!assertions.length) return this.forType(entityType);
    const byRelation = new Map(); const stats = new Map();
    for (const assertion of assertions) {
      const rows = byRelation.get(assertion.relation) || []; rows.push(assertion); byRelation.set(assertion.relation, rows);
      const row = stats.get(assertion.relation) || { count: 0, sourced: 0 }; row.count++; if ((assertion.sourceRefs || []).length) row.sourced++; stats.set(assertion.relation, row);
    }
    const relationIds = new Set(byRelation.keys()); const relations = this.relations.filter((relation) => relationIds.has(relation.id));
    const scores = summarize({ ...this.pack, assertions }, relations, this.relationTags, entityType ? [entityType] : this.pack.registry.entityTypes, stats, byRelation, this.relationById, hintsForEntityType(this.declaredHints, entityType), { ...this.options, trustStructuralSummary: false });
    const profile = { schemaVersion: '1.0', scope: 'result-set', entityType, entityTypeLabels: this.entityTypeLabels, affordances: scores, relationTags: Object.fromEntries(relations.map((relation) => [relation.id, this.relationTags[relation.id] || []])), stats: { assertions: assertions.length, relations: relations.length, entities: ids.size } };
    this.byFocus.set(key, profile); return profile;
  }

  forFocus(entityId, entityType = null) {
    const key = `${entityType || ''}|${entityId}`;
    if (this.byFocus.has(key)) return this.byFocus.get(key);
    const assertions = this.assertionsByEntity.get(entityId) || [];
    if (!assertions.length) return this.forType(entityType);
    const relationIds = new Set(assertions.map((assertion) => assertion.relation));
    const relations = this.relations.filter((relation) => relationIds.has(relation.id));
    const byRelation = new Map();
    const stats = new Map();
    for (const assertion of assertions) {
      const rows = byRelation.get(assertion.relation) || [];
      rows.push(assertion); byRelation.set(assertion.relation, rows);
      const row = stats.get(assertion.relation) || { count: 0, sourced: 0 };
      row.count++; if ((assertion.sourceRefs || []).length) row.sourced++;
      stats.set(assertion.relation, row);
    }
    const localHints = hintsForEntityType(this.declaredHints, entityType);
    const scores = summarize(
      { ...this.pack, assertions }, relations, this.relationTags,
      entityType ? [entityType] : this.pack.registry.entityTypes,
      stats, byRelation, this.relationById, localHints,
      { ...this.options, trustStructuralSummary: false },
    );
    const profile = {
      schemaVersion: '1.0', scope: 'focus', entityType,
      entityTypeLabels: this.entityTypeLabels, affordances: scores,
      relationTags: Object.fromEntries(relations.map((relation) => [relation.id, this.relationTags[relation.id] || []])),
      stats: { assertions: assertions.length, relations: relations.length },
    };
    this.byFocus.set(key, profile);
    return profile;
  }

  hintsFor(entityType = null) {
    const hints = hintsForEntityType(this.declaredHints, entityType);
    if (!hints || typeof hints !== 'object') return null;
    // Reader Policy is a confidentiality boundary. Presentation-oriented hints
    // can contain domain labels or preferences that reveal hidden structure even
    // when the underlying assertions/relations are correctly filtered. In a
    // policy-scoped profiler we therefore fail closed: declared affordances and
    // relation mappings may strengthen *observed* structure during profiling,
    // but planner-facing labels/preferences are never exposed.
    if (this.options.policyScoped === true) return {};
    return hints;
  }
}

export { AFFORDANCES, AFFORDANCES as CAPABILITIES };
