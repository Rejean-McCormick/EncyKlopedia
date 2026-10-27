<script>
  import { onDestroy } from 'svelte';
  import TimelineLineageView from './TimelineLineageView.svelte';
  import TreeView from './TreeView.svelte';
  import DagProofView from './DagProofView.svelte';
  import FlowPathView from './FlowPathView.svelte';
  import CausalFeedbackView from './CausalFeedbackView.svelte';
  import MatrixProfileView from './MatrixProfileView.svelte';
  import StateFlowView from './StateFlowView.svelte';
  import TraceabilityView from './TraceabilityView.svelte';
  import MultiscaleLayerView from './MultiscaleLayerView.svelte';
  import SpatialView from './SpatialView.svelte';

  export let query;
  export let lensRef;
  export let recipe;
  export let selectedEntityId = null;
  export let inspect = () => {};
  export let fallback = () => {};
  export let authToken = '';
  export let kristal = '';

  let data = null, busy = false, error = '', controller, requestedKey = '', cursor = null;
  let nodeBudget = 280, edgeBudget = 420;

  const components = {
    'timeline-lineage': TimelineLineageView,
    tree: TreeView,
    'dag-proof': DagProofView,
    'flow-path': FlowPathView,
    'causal-feedback': CausalFeedbackView,
    'matrix-profile': MatrixProfileView,
    'state-flow': StateFlowView,
    traceability: TraceabilityView,
    'multiscale-layer': MultiscaleLayerView,
    spatial: SpatialView,
  };

  $: requestBase = query && recipe ? { query, lensRef, recipeId: recipe.id, selectedEntityId, kristal } : null;
  $: requestKey = requestBase ? JSON.stringify(requestBase) : '';
  $: if (requestKey && requestKey !== requestedKey) { cursor = null; nodeBudget = 280; edgeBudget = 420; load(requestKey, null); }
  $: Renderer = components[data?.rendererId] || components[recipe?.rendererId] || null;
  $: canExpand = Boolean(data?.truncated && !cursor && (nodeBudget < 1200 || edgeBudget < 2400));

  async function load(key, nextCursor) {
    controller?.abort(); controller = new AbortController(); requestedKey = key; busy = true; error = '';
    try {
      const { kristal: _kristal, ...request } = JSON.parse(key);
      const payload = { ...request, ...(nextCursor ? { cursor: nextCursor } : {}), pageSize: 160, nodeBudget, edgeBudget };
      const response = await fetch('/api/navigation/project', { method:'POST', headers:{'Content-Type':'application/json', ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}), ...(kristal ? { 'X-Konstellation-Kristal': kristal } : {})}, body:JSON.stringify(payload), signal:controller.signal });
      const value = await response.json();
      if (!response.ok) throw Error(value.error?.message || 'Projection adaptative indisponible.');
      if (requestedKey === key) { data = value; cursor = value.nextCursor || null; }
    } catch (e) { if (e.name !== 'AbortError' && requestedKey === key) error = e.message; }
    finally { if (requestedKey === key) busy = false; }
  }
  function expandDetail() {
    nodeBudget = Math.min(1200, nodeBudget * 2);
    edgeBudget = Math.min(2400, edgeBudget * 2);
    cursor = null;
    load(requestKey, null);
  }
  function exportProjection() {
    if (!data || typeof document === 'undefined') return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url; anchor.download = `konstellation-${recipe?.id || 'projection'}.json`; anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  onDestroy(() => controller?.abort());
</script>

<div class="adaptive-projection" aria-busy={busy} data-recipe={recipe?.id} data-renderer={recipe?.rendererId}>
  <div class="adaptive-projection-head">
    <div><small>NAVIGATION ADAPTATIVE</small><strong>{recipe?.label}</strong></div>
    <div class="adaptive-projection-actions">
      {#if data}<button class="text-button" on:click={exportProjection}>Exporter JSON</button>{/if}
      {#if recipe?.reason}<span title={recipe.reason}>Détecté depuis la structure visible</span>{/if}
    </div>
  </div>
  {#if error}
    <div class="constellation-message error" role="alert">{error}<p>La sélection et l’historique sont conservés.</p><button class="button" on:click={fallback}>Ouvrir le fallback accessible</button></div>
  {:else if busy && !data}
    <div class="adaptive-loading" role="status">Projection de la structure visible…</div>
  {:else if Renderer && data}
    <svelte:component this={Renderer} {data} {inspect} />
    {#if data.truncated}<p class="hint">Projection bornée pour préserver lisibilité et performance. {data.totalCandidates || 0} candidat(s) au total.</p>{/if}
    <div class="projection-pagination" aria-label="Niveau de détail de la projection">
      {#if cursor}<button class="button" disabled={busy} on:click={() => load(requestKey, cursor)}>{busy ? 'Chargement…' : 'Page suivante →'}</button>{/if}
      {#if canExpand}<button class="button" disabled={busy} on:click={expandDetail}>{busy ? 'Chargement…' : 'Afficher plus de détails'}</button>{/if}
      <button class="text-button" on:click={fallback}>Vue tabulaire accessible</button>
    </div>
  {:else if data}
    <div class="empty-state compact"><span>◇</span><h3>Renderer indisponible.</h3><p>La projection spécialisée ne peut pas être affichée ici.</p><button class="button" on:click={fallback}>Utiliser le fallback déclaré</button></div>
  {/if}
</div>
