<script>
  export let data;
  export let inspect = () => {};
  const MAX_VISUAL_NODES = 70;
  const clip = (text, size = 22) => String(text || '').length > size ? `${String(text).slice(0, size - 1)}…` : String(text || '');
  const cond = (transition) => (transition.conditions || []).map((item) => item.kind === 'valuation' ? `${item.dimension}: ${String(item.value ?? item.state)}` : `${item.axis}: ${String(item.value)}`).join(' · ');

  function layout(nodes, transitions, starts) {
    const sourceNodes = (nodes || []).slice(0, MAX_VISUAL_NODES);
    const ids = new Set(sourceNodes.map((node) => node.id));
    const edges = (transitions || []).filter((edge) => ids.has(edge.source) && ids.has(edge.target));
    const outgoing = new Map(sourceNodes.map((node) => [node.id, []]));
    for (const edge of edges) outgoing.get(edge.source)?.push(edge.target);
    const level = new Map();
    const queue = (starts || []).filter((id) => ids.has(id));
    if (!queue.length && sourceNodes[0]) queue.push(sourceNodes[0].id);
    queue.forEach((id) => level.set(id, 0));
    for (let i = 0; i < queue.length; i++) {
      const id = queue[i];
      for (const target of outgoing.get(id) || []) if (!level.has(target)) { level.set(target, (level.get(id) || 0) + 1); queue.push(target); }
    }
    sourceNodes.forEach((node) => { if (!level.has(node.id)) level.set(node.id, 0); });
    const groups = new Map();
    for (const node of sourceNodes) { const l = level.get(node.id) || 0; const rows = groups.get(l) || []; rows.push(node); groups.set(l, rows); }
    const maxLevel = Math.max(0, ...groups.keys()); const maxRows = Math.max(1, ...[...groups.values()].map((rows) => rows.length));
    const width = Math.max(680, 180 + maxLevel * 190); const height = Math.max(260, 90 + maxRows * 78); const positions = new Map();
    for (const [l, rows] of groups) rows.forEach((node, index) => positions.set(node.id, { ...node, x: 90 + l * 190, y: 55 + index * 78 }));
    return { nodes: [...positions.values()], edges, positions, width, height, clipped: (nodes || []).length > sourceNodes.length };
  }
  $: graph = layout(data.nodes || [], data.transitions || [], data.starts || []);
  $: byId = Object.fromEntries((data.nodes || []).map((node) => [node.id, node]));
  function keyInspect(event, id) { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); inspect(id); } }
</script>

<div class="renderer-stack" data-renderer="flow-path">
  {#if graph.nodes.length}
    <div class="structural-canvas" aria-label="Parcours visible">
      <svg viewBox={`0 0 ${graph.width} ${graph.height}`} role="img" aria-label="Étapes et transitions">
        <defs><marker id="flow-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" /></marker></defs>
        {#each graph.edges as edge}
          {@const source = graph.positions.get(edge.source)}{@const target = graph.positions.get(edge.target)}
          {#if source && target}<line class:conditional={edge.conditional} class="graph-link" x1={source.x + 62} y1={source.y} x2={target.x - 62} y2={target.y} marker-end="url(#flow-arrow)"><title>{edge.relationLabel}{edge.conditional ? ` · ${cond(edge)}` : ''}</title></line>{/if}
        {/each}
        {#each graph.nodes as node}
          <g class="graph-node flow-node" role="button" tabindex="0" aria-label={`Inspecter ${node.label || node.id}`} on:click={() => inspect(node.id)} on:keydown={(event) => keyInspect(event, node.id)}>
            <rect x={node.x - 62} y={node.y - 23} width="124" height="46" rx="23" />
            <text x={node.x} y={node.y + 4} text-anchor="middle">{clip(node.label || node.id)}</text>
          </g>
        {/each}
      </svg>
    </div>
    {#if graph.clipped}<p class="hint">Aperçu limité à {MAX_VISUAL_NODES} étapes.</p>{/if}
  {:else}<p class="empty-renderer">Aucune transition visible.</p>{/if}
  <details><summary>Transitions et conditions</summary><div class="renderer-stack compact-stack">{#each data.transitions || [] as transition}<div class="renderer-edge flow-edge" class:conditional={transition.conditional}><button on:click={() => inspect(transition.source)}>{byId[transition.source]?.label || transition.source}</button><span>→</span><button on:click={() => inspect(transition.target)}>{byId[transition.target]?.label || transition.target}</button><small>{transition.relationLabel}{transition.conditional ? ' · conditionnelle' : ''}</small>{#if transition.conditions?.length}<p>{cond(transition)}</p>{/if}</div>{/each}</div></details>
</div>
