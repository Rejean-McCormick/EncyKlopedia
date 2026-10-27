<script>
  export let data;
  export let inspect = () => {};
  $: byId = Object.fromEntries((data.nodes || []).map((node) => [node.id, node]));
  function open(node) { if (node?.entityId) inspect(node.entityId); }
</script>

<div class="renderer-stack" data-renderer="traceability" role="list" aria-label="Traçabilité visible">
  {#each data.edges || [] as edge}
    {@const source = byId[edge.source]}
    {@const target = byId[edge.target]}
    <div class="renderer-edge trace-edge" data-kind={edge.kind} role="listitem">
      {#if source?.entityId}<button on:click={() => open(source)}>{source.label || edge.source}</button>{:else}<span>{source?.label || edge.source}</span>{/if}
      <span aria-hidden="true">→</span>
      {#if target?.entityId}<button on:click={() => open(target)}>{target.label || edge.target}</button>{:else}<span>{target?.label || edge.target}</span>{/if}
      <small>{edge.kind}</small>
    </div>
  {:else}<p class="empty-renderer">Aucune trace visible dans cette policy.</p>{/each}
</div>
