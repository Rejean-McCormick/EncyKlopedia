/**
 * Controlled renderer registry. Kristals may select recipes through declarative
 * affordances, but executable renderers always come from this registry.
 */
export const RENDERERS = Object.freeze({
  list: {
    id: 'list', supportedRecipes: ['catalogue'], requiresAffordances: [], benefitsFrom: ['classification'], projectionKind: 'rows',
    maxRecommendedItems: 200, truncationStrategy: 'page', lodStrategy: 'pagination', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: false,
    cost: 0.12,
  },
  table: {
    id: 'table', supportedRecipes: ['table'], requiresAffordances: [], benefitsFrom: ['quantitative', 'multidimensional'], projectionKind: 'rows',
    maxRecommendedItems: 500, truncationStrategy: 'page', lodStrategy: 'pagination-virtualization', accessibilityFallback: 'list', supportsKeyboard: true, supportsExport: false,
    cost: 0.16,
  },
  constellation: {
    id: 'constellation', supportedRecipes: ['constellation', 'arguments'], requiresAffordances: [], benefitsFrom: ['network', 'argumentation'], projectionKind: 'neighborhood',
    maxRecommendedItems: 120, truncationStrategy: 'bounded-neighborhood', lodStrategy: 'expand-on-demand', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: false,
    cost: 0.36,
  },
  'timeline-lineage': {
    id: 'timeline-lineage', supportedRecipes: ['timeline', 'evolution'], requiresAffordances: [], benefitsFrom: ['temporal', 'lineage', 'succession', 'versioned'], projectionKind: 'timeline-lineage',
    maxRecommendedItems: 400, truncationStrategy: 'page-events', lodStrategy: 'temporal-aggregation', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: true,
    cost: 0.3,
  },
  tree: {
    id: 'tree', supportedRecipes: ['hierarchy'], requiresAffordances: ['hierarchy'], benefitsFrom: ['multiScale', 'hierarchy'], projectionKind: 'tree',
    maxRecommendedItems: 500, truncationStrategy: 'bounded-depth', lodStrategy: 'expand-branches', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: true,
    cost: 0.32,
  },
  'dag-proof': {
    id: 'dag-proof', supportedRecipes: ['dependencies', 'proofs'], requiresAffordances: [], benefitsFrom: ['dependency', 'proof', 'argumentation'], projectionKind: 'dag',
    maxRecommendedItems: 500, truncationStrategy: 'bounded-dag', lodStrategy: 'expand-neighborhood', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: true,
    cost: 0.42,
  },
  'flow-path': {
    id: 'flow-path', supportedRecipes: ['path'], requiresAffordances: [], benefitsFrom: ['sequence', 'stateMachine', 'conditionalTransition'], projectionKind: 'flow',
    maxRecommendedItems: 400, truncationStrategy: 'bounded-flow', lodStrategy: 'expand-path', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: true,
    cost: 0.36,
  },
  'causal-feedback': {
    id: 'causal-feedback', supportedRecipes: ['feedback'], requiresAffordances: ['causal', 'cycle'], benefitsFrom: ['signedCausal', 'sequence'], projectionKind: 'causal-feedback',
    maxRecommendedItems: 320, truncationStrategy: 'bounded-cycle-neighborhood', lodStrategy: 'expand-cycle', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: true,
    cost: 0.48,
  },
  'matrix-profile': {
    id: 'matrix-profile', supportedRecipes: ['dimensions'], requiresAffordances: ['multidimensional'], benefitsFrom: ['quantitative', 'classification'], projectionKind: 'matrix',
    maxRecommendedItems: 200, truncationStrategy: 'page-dimensions', lodStrategy: 'aggregate-columns', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: true,
    cost: 0.34,
  },
  'state-flow': {
    id: 'state-flow', supportedRecipes: ['states', 'action-context'], requiresAffordances: [], benefitsFrom: ['stateful', 'eventStream', 'actionability'], projectionKind: 'state-flow',
    maxRecommendedItems: 350, truncationStrategy: 'page-records', lodStrategy: 'group-state', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: true,
    cost: 0.34,
  },
  traceability: {
    id: 'traceability', supportedRecipes: ['traceability', 'divergences'], requiresAffordances: [], benefitsFrom: ['evidential', 'provenance', 'conflict', 'succession'], projectionKind: 'traceability',
    maxRecommendedItems: 500, truncationStrategy: 'bounded-trace', lodStrategy: 'expand-trace', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: true,
    cost: 0.38,
  },
  'multiscale-layer': {
    id: 'multiscale-layer', supportedRecipes: ['multiscale'], requiresAffordances: ['multiScale'], benefitsFrom: ['multiplex', 'hierarchy', 'network'], projectionKind: 'multiscale',
    maxRecommendedItems: 500, truncationStrategy: 'bounded-layers', lodStrategy: 'semantic-zoom', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: true,
    cost: 0.4,
  },
  spatial: {
    id: 'spatial', supportedRecipes: ['spatial'], requiresAffordances: ['spatial'], benefitsFrom: ['temporal', 'classification'], projectionKind: 'spatial',
    maxRecommendedItems: 500, truncationStrategy: 'page-features', lodStrategy: 'spatial-cluster', accessibilityFallback: 'table', supportsKeyboard: true, supportsExport: true,
    cost: 0.4,
  },
});

export function rendererDefinition(id) {
  return RENDERERS[id] || null;
}

export function rendererForRecipe(recipeId) {
  return Object.values(RENDERERS).find((renderer) => renderer.supportedRecipes.includes(recipeId)) || null;
}

export function rendererCatalog() {
  return Object.values(RENDERERS).map((renderer) => ({ ...renderer }));
}

export function resolveRenderer(id) {
  const renderer = rendererDefinition(id);
  if (renderer) return renderer;
  return RENDERERS.table;
}
