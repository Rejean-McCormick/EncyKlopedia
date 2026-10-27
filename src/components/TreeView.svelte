<script>
  export let data;
  export let inspect = () => {};
  let treeRoot;
  let activeIndex = 0;

  $: byId = Object.fromEntries((data.nodes || []).map((node) => [node.id, node]));
  $: rows = flatten(data.roots || [], data.edges || []);
  $: if (activeIndex >= rows.length) activeIndex = Math.max(0, rows.length - 1);

  function flatten(roots, edges) {
    const children = edges.reduce((map, edge) => { (map[edge.source] ??= []).push(edge); return map; }, {});
    const output = []; const visited = new Set();
    const walk = (id, depth, via = null, parentIndex = null) => {
      if (visited.has(id) || output.length >= 1200) return;
      visited.add(id);
      const index = output.length;
      output.push({ id, depth, via, parentIndex });
      for (const edge of children[id] || []) walk(edge.target, Math.min(depth + 1, 32), edge, index);
    };
    for (const root of roots) walk(root, 0);
    for (const node of data.nodes || []) if (!visited.has(node.id)) walk(node.id, 0);
    return output;
  }

  function focusIndex(index) {
    if (!rows.length) return;
    activeIndex = Math.max(0, Math.min(rows.length - 1, index));
    queueMicrotask(() => treeRoot?.querySelector(`[data-tree-index="${activeIndex}"]`)?.focus());
  }

  function keyTree(event, row, index) {
    if (event.key === 'ArrowDown') { event.preventDefault(); focusIndex(index + 1); }
    else if (event.key === 'ArrowUp') { event.preventDefault(); focusIndex(index - 1); }
    else if (event.key === 'Home') { event.preventDefault(); focusIndex(0); }
    else if (event.key === 'End') { event.preventDefault(); focusIndex(rows.length - 1); }
    else if (event.key === 'ArrowRight') {
      const next = rows[index + 1];
      if (next && next.depth > row.depth) { event.preventDefault(); focusIndex(index + 1); }
    } else if (event.key === 'ArrowLeft' && row.parentIndex != null) {
      event.preventDefault(); focusIndex(row.parentIndex);
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault(); inspect(row.id);
    }
  }
</script>

<div bind:this={treeRoot} class="renderer-stack" data-renderer="tree" role="tree" aria-label="Hiérarchie visible">
  {#each rows as row, index}
    <div
      class={`renderer-row tree-row tree-depth-${Math.min(row.depth, 12)}`}
      role="treeitem"
      tabindex={index === activeIndex ? 0 : -1}
      aria-level={row.depth + 1}
      aria-label={byId[row.id]?.label || row.id}
      data-tree-index={index}
      on:focus={() => activeIndex = index}
      on:click={() => inspect(row.id)}
      on:keydown={(event) => keyTree(event, row, index)}
    >
      <span class="renderer-key" aria-hidden="true">{row.depth ? '↳' : '◆'}</span>
      <span class="tree-label">{byId[row.id]?.label || row.id}</span>
      {#if row.via}<small>{row.via.relationLabel}</small>{/if}
    </div>
  {:else}<p class="empty-renderer">Aucune racine hiérarchique visible.</p>{/each}
</div>
