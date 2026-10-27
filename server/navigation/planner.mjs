import { humanizeIdentifier } from './profiler.mjs';
import { rendererDefinition, rendererForRecipe, rendererCatalog as registryCatalog } from './registry.mjs';

const RECIPE_DEFINITIONS = [
  { id: 'catalogue', label: 'Liste', rendererId: 'list', icon: '▤', always: true, baseScore: 0.50, description: 'Parcourir les éléments correspondant à la sélection.' },
  { id: 'constellation', label: 'Constellation', rendererId: 'constellation', icon: '◈', always: true, anyOf: ['network'], baseScore: 0.34, description: 'Explorer une sélection et, lorsqu’elles existent, ses relations et voisinages.' },
  { id: 'timeline', label: 'Chronologie', rendererId: 'timeline-lineage', icon: '↦', requires: ['temporal'], baseScore: 0.62, description: 'Explorer les repères temporels explicites.' },
  { id: 'hierarchy', label: 'Hiérarchie', rendererId: 'tree', icon: '⌄', requires: ['hierarchy'], baseScore: 0.60, description: 'Parcourir une structure parent/enfant ou de composition.' },
  { id: 'dependencies', label: 'Dépendances', rendererId: 'dag-proof', icon: '⇢', requires: ['dependency'], baseScore: 0.68, description: 'Comprendre prérequis, dépendances et dérivations.' },
  { id: 'path', label: 'Parcours', rendererId: 'flow-path', icon: '→', anyOf: ['sequence', 'stateMachine', 'conditionalTransition'], baseScore: 0.64, description: 'Suivre un processus, une séquence ou des transitions conditionnelles.' },
  { id: 'feedback', label: 'Boucles', rendererId: 'causal-feedback', icon: '⟳', requires: ['causal', 'cycle'], baseScore: 0.72, description: 'Comprendre les boucles causales explicites.' },
  { id: 'proofs', label: 'Preuves', rendererId: 'dag-proof', icon: '∴', requires: ['proof'], baseScore: 0.75, description: 'Explorer propositions, preuves, réfutations et dépendances formelles.' },
  { id: 'arguments', label: 'Positions', rendererId: 'constellation', icon: '◇', requires: ['argumentation'], baseScore: 0.66, description: 'Comparer arguments, positions et relations discursives.' },
  { id: 'dimensions', label: 'Comparer', rendererId: 'matrix-profile', icon: '▦', requires: ['multidimensional'], baseScore: 0.58, description: 'Comparer des éléments selon des dimensions et mesures.' },
  { id: 'states', label: 'États', rendererId: 'state-flow', icon: '◌', anyOf: ['stateful', 'eventStream'], baseScore: 0.61, description: 'Explorer états observés, phases et changements.' },
  { id: 'evolution', label: 'Évolution', rendererId: 'timeline-lineage', icon: '↝', anyOf: ['lineage', 'succession', 'versioned'], baseScore: 0.63, description: 'Suivre lignée, révisions et successions explicites.' },
  { id: 'divergences', label: 'Divergences', rendererId: 'traceability', icon: '≠', requires: ['conflict'], baseScore: 0.64, description: 'Examiner les conflits et désaccords explicites.' },
  { id: 'traceability', label: 'Traçabilité', rendererId: 'traceability', icon: '⌁', anyOf: ['evidential', 'provenance'], baseScore: 0.57, description: 'Suivre évidence, provenance et sources sans les confondre.' },
  { id: 'action-context', label: 'Décisions & action', rendererId: 'state-flow', icon: '◎', requires: ['actionability'], baseScore: 0.56, description: 'Comprendre conditions et rôles d’action sans déduire une permission.' },
  { id: 'multiscale', label: 'Échelles', rendererId: 'multiscale-layer', icon: '⊕', requires: ['multiScale'], baseScore: 0.64, description: 'Changer d’échelle ou de couche en préservant les liens transversaux.' },
  { id: 'spatial', label: 'Espace', rendererId: 'spatial', icon: '⌖', requires: ['spatial'], baseScore: 0.60, description: 'Explorer positions, lieux et régions explicites.' },
  { id: 'table', label: 'Tableau', rendererId: 'table', icon: '▦', always: true, baseScore: 0.28, description: 'Comparer les résultats sous forme tabulaire.' },
];

const RELATION_AFFORDANCES = {
  timeline: ['temporal'], hierarchy: ['hierarchy'], dependencies: ['dependency'],
  path: ['conditionalTransition', 'stateMachine', 'sequence'], feedback: ['signedCausal', 'causal'],
  proofs: ['proof', 'dependency'], arguments: ['argumentation'], evolution: ['lineage', 'succession', 'versioned'],
  divergences: ['conflict'], traceability: ['evidential', 'provenance'], states: ['stateful', 'eventStream'],
  'action-context': ['actionability'], multiscale: ['multiScale', 'multiplex'], spatial: ['spatial'],
  dimensions: ['multidimensional', 'quantitative'],
};

function affordance(profile, id) {
  return profile.affordances?.[id]?.score ?? profile.capabilities?.[id]?.score ?? 0;
}

function recipeScore(recipe, profile, rendererBudgetRatio = 0) {
  if (!recipe.always) {
    const required = recipe.requires || [];
    if (required.some((id) => affordance(profile, id) < 0.35)) return 0;
    if (recipe.anyOf && !recipe.anyOf.some((id) => affordance(profile, id) >= 0.35)) return 0;
  }
  const ids = [...(recipe.requires || []), ...(recipe.anyOf || [])];
  const strength = ids.length ? Math.max(...ids.map((id) => affordance(profile, id))) : 0;
  const average = ids.length ? ids.reduce((sum, id) => sum + affordance(profile, id), 0) / ids.length : 0;
  const cost = rendererDefinition(recipe.rendererId)?.cost || 0.2;
  const costPenalty = Math.min(0.16, rendererBudgetRatio * cost * 0.2);
  return Math.max(0, Math.min(1, recipe.baseScore + strength * 0.23 + average * 0.12 - costPenalty));
}

function reasonFor(recipe, profile) {
  const ids = [...(recipe.requires || []), ...(recipe.anyOf || [])];
  const evidence = ids.flatMap((id) => profile.affordances?.[id]?.evidence || profile.capabilities?.[id]?.evidence || [])
    .filter((value, index, all) => all.indexOf(value) === index).slice(0, 3);
  return evidence.length ? evidence.join(' · ') : recipe.description;
}

function relationIdsFor(recipe, profiler, entityType) {
  const ids = [];
  for (const affordanceId of RELATION_AFFORDANCES[recipe.id] || []) {
    for (const relation of profiler.relationsFor(affordanceId, entityType)) {
      if (!ids.includes(relation.id)) ids.push(relation.id);
    }
  }
  return ids.slice(0, 32);
}

function contextualActions(profile) {
  const actions = [];
  const push = (id, label, cap, recipeId = null) => {
    if (affordance(profile, cap) >= 0.4) actions.push({ id, label, affordance: cap, ...(recipeId ? { recipeId } : {}) });
  };
  push('trace-provenance', 'Tracer les sources', 'provenance', 'traceability');
  push('change-scale', 'Changer d’échelle', 'multiScale', 'multiscale');
  push('inspect-cycle', 'Examiner une boucle', 'cycle', 'feedback');
  push('compare-dimensions', 'Comparer les dimensions', 'multidimensional', 'dimensions');
  push('inspect-resources', 'Voir les capacités et ressources', 'resourceAllocation', 'states');
  push('inspect-versions', 'Comparer les versions', 'versioned', 'evolution');
  push('inspect-conflicts', 'Examiner les divergences', 'conflict', 'divergences');
  push('inspect-actionability', 'Examiner les conditions d’action', 'actionability', 'action-context');
  push('inspect-spatial', 'Explorer dans l’espace', 'spatial', 'spatial');
  return actions.slice(0, 8);
}

function profileFor(profiler, entityType, selectedEntity, resultEntityIds = null) {
  if (selectedEntity?.id && typeof profiler.forFocus === 'function') return profiler.forFocus(selectedEntity.id, entityType);
  if (Array.isArray(resultEntityIds) && resultEntityIds.length && typeof profiler.forResultSet === 'function') return profiler.forResultSet(resultEntityIds, entityType);
  return profiler.forType(entityType);
}

export function buildNavigationPlan({ profiler, query, lens, selectedEntity = null, resultSize = null, resultEntityIds = null }) {
  const entityType = selectedEntity?.type || query.selection.entityType;
  const profile = profileFor(profiler, entityType, selectedEntity, resultEntityIds);
  const hints = profiler.hintsFor?.(entityType) || null;
  const preferredRecipes = new Set(Array.isArray(hints?.preferredRecipes) ? hints.preferredRecipes : []);
  const recipeLabels = hints?.recipeLabels && typeof hints.recipeLabels === 'object' ? hints.recipeLabels : {};
  const rendererBudgetRatio = Number.isFinite(resultSize) && resultSize > 0 ? Math.min(4, resultSize / 500) : 0;

  const scored = RECIPE_DEFINITIONS.map((recipe) => {
    const base = recipeScore(recipe, profile, rendererBudgetRatio);
    const score = base > 0 ? Math.min(1, base + (preferredRecipes.has(recipe.id) ? 0.08 : 0)) : 0;
    return { recipe, score };
  }).filter(({ score }) => score > 0).map(({ recipe, score }) => ({
    id: recipe.id,
    label: typeof recipeLabels[recipe.id] === 'string' ? recipeLabels[recipe.id] : recipe.label,
    rendererId: recipe.rendererId,
    icon: recipe.icon,
    score: Math.round(score * 100) / 100,
    description: recipe.description,
    reason: reasonFor(recipe, profile),
    relationIds: relationIdsFor(recipe, profiler, entityType),
  }));

  const specialized = scored.filter((view) => !['catalogue', 'table', 'constellation'].includes(view.id))
    .sort((a, b) => b.score - a.score || a.label.localeCompare(b.label, 'fr')).slice(0, 6);
  const generic = ['catalogue', 'table', 'constellation'].map((id) => scored.find((view) => view.id === id)).filter(Boolean);
  const views = [...specialized, ...generic];
  const primary = views[0] || { id: 'catalogue', label: 'Liste', rendererId: 'list', icon: '▤', score: 0.5, relationIds: [], reason: 'Vue générique', description: 'Parcourir la sélection.' };
  const affordances = Object.fromEntries(Object.entries(profile.affordances || profile.capabilities || {})
    .filter(([, value]) => value.score >= 0.25).sort((a, b) => b[1].score - a[1].score).slice(0, 20));

  return {
    schemaVersion: '1.0', mode: 'adaptive', derived: true,
    semantics: 'navigation-affordances-not-kristal-authority',
    scope: { kind: selectedEntity ? 'focus' : 'selection', entityType, ...(selectedEntity ? { focusEntityId: selectedEntity.id } : {}) },
    entityType,
    entityTypeLabel: profiler.entityTypeLabels[entityType] || humanizeIdentifier(entityType),
    lensRef: lens?.id || `type:${query.selection.entityType}`,
    lensLabel: lens?.label?.fr || profiler.entityTypeLabels[query.selection.entityType] || humanizeIdentifier(query.selection.entityType),
    primaryRecipeId: primary.id,
    views,
    actions: contextualActions({ affordances }),
    profile: { schemaVersion: '1.0', scope: profile.scope, entityType: profile.entityType, affordances },
  };
}

export function recipeDefinition(id) { return RECIPE_DEFINITIONS.find((recipe) => recipe.id === id) || null; }
export function rendererCatalog() {
  const renderers = registryCatalog();
  return renderers.map((renderer) => ({ ...renderer, recipes: renderer.supportedRecipes.map((id) => {
    const recipe = recipeDefinition(id); return recipe ? { id, label: recipe.label, description: recipe.description } : { id };
  }) }));
}
export { rendererForRecipe };
