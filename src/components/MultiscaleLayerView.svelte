<script>
  export let data;
  export let inspect = () => {};
  $: byLayer = (data.memberships || []).reduce((map, item) => { (map[item.layerId] ??= []).push(item.entityId); return map; }, {});
  $: byId = Object.fromEntries((data.nodes || []).map((node) => [node.id, node]));
  $: layerById = Object.fromEntries((data.layers || []).map((layer) => [layer.id, layer]));
</script>

<div class="renderer-stack" data-renderer="multiscale-layer">
  <div class="scale-board" role="list" aria-label="Couches et échelles visibles">
    {#each data.layers || [] as layer}
      <section class="scale-column" role="listitem">
        <header><small>{layer.axis}</small><strong>{layer.label}</strong><span>{new Set(byLayer[layer.id] || []).size}</span></header>
        <div class="scale-members">{#each [...new Set(byLayer[layer.id] || [])] as id}<button on:click={() => inspect(id)}>{byId[id]?.label || id}</button>{/each}</div>
      </section>
    {:else}<p class="empty-renderer">Aucune couche/échelle explicite visible.</p>{/each}
  </div>
  {#if data.crossLinks?.length}<details><summary>{data.crossLinks.length} lien(s) entre couches/échelles</summary><div class="renderer-stack compact-stack">{#each data.crossLinks as link}<div class="renderer-edge"><button on:click={() => inspect(link.source)}>{byId[link.source]?.label || link.source}</button><span>↔</span><button on:click={() => inspect(link.target)}>{byId[link.target]?.label || link.target}</button><small>{link.relationLabel || `${layerById[link.sourceLayer]?.label || ''} → ${layerById[link.targetLayer]?.label || ''}`}</small></div>{/each}</div></details>{/if}
</div>
