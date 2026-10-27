<script>
  export let data;
  export let inspect = () => {};
  const MAX_VISUAL_NODES = 80;
  const clip = (text, size = 24) => String(text || '').length > size ? `${String(text).slice(0, size - 1)}…` : String(text || '');

  function layout(nodes, edges) {
    const sourceNodes = (nodes || []).slice(0, MAX_VISUAL_NODES);
    const ids = new Set(sourceNodes.map((node) => node.id));
    const graphEdges = (edges || []).filter((edge) => ids.has(edge.source) && ids.has(edge.target));
    const incoming = new Map(sourceNodes.map((node) => [node.id, 0]));
    const outgoing = new Map(sourceNodes.map((node) => [node.id, []]));
    for (const edge of graphEdges) {
      incoming.set(edge.target, (incoming.get(edge.target) || 0) + 1);
      outgoing.get(edge.source)?.push(edge.target);
    }
    const level = new Map();
    const queue = sourceNodes.filter((node) => (incoming.get(node.id) || 0) === 0).map((node) => node.id);
    for (const id of queue) level.set(id, 0);
    let cursor = 0;
    while (cursor < queue.length) {
      const id = queue[cursor++];
      for (const target of outgoing.get(id) || []) {
        level.set(target, Math.max(level.get(target) || 0, (level.get(id) || 0) + 1));
        incoming.set(target, (incoming.get(target) || 1) - 1);
        if (incoming.get(target) === 0) queue.push(target);
      }
    }
    for (const node of sourceNodes) if (!level.has(node.id)) level.set(node.id, 0);
    const groups = new Map();
    for (const node of sourceNodes) {
      const l = level.get(node.id) || 0;
      const rows = groups.get(l) || [];
      rows.push(node); groups.set(l, rows);
    }
    const maxLevel = Math.max(0, ...groups.keys());
    const maxRows = Math.max(1, ...[...groups.values()].map((rows) => rows.length));
    const width = Math.max(680, 180 + maxLevel * 190);
    const height = Math.max(260, 90 + maxRows * 78);
    const positions = new Map();
    for (const [l, rows] of groups) rows.forEach((node, index) => positions.set(node.id, {
      ...node,
      x: 90 + l * 190,
      y: 55 + index * 78,
    }));
    return { nodes: [...positions.values()], edges: graphEdges, positions, width, height, clipped: (nodes || []).length > sourceNodes.length };
  }

  $: graph = layout(data.nodes || [], data.edges || []);
  $: byId = Object.fromEntries((data.nodes || []).map((node) => [node.id, node]));
  function keyInspect(event, id) { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); inspect(id); } }
</script>

<div class="renderer-stack" data-renderer="dag-proof">
  <div class="renderer-summary"><span>{data.acyclic ? 'DAG acyclique' : 'Cycle détecté'}</span><span>{data.edges?.length || 0} dépendance(s)</span></div>
  {#if graph.nodes.length}
    <div class="structural-canvas" aria-label="Graphe de dépendances visible">
      <svg viewBox={`0 0 ${graph.width} ${graph.height}`} role="img" aria-label="Dépendances et preuves">
        <defs><marker id="dag-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" /></marker></defs>
        {#each graph.edges as edge}
          {@const source = graph.positions.get(edge.source)}
          {@const target = graph.positions.get(edge.target)}
          {#if source && target}<line class="graph-link" x1={source.x + 62} y1={source.y} x2={target.x - 62} y2={target.y} marker-end="url(#dag-arrow)"><title>{edge.relationLabel || edge.kind}</title></line>{/if}
        {/each}
        {#each graph.nodes as node}
          <g class="graph-node" role="button" tabindex="0" aria-label={`Inspecter ${node.label || node.id}`} on:click={() => inspect(node.id)} on:keydown={(event) => keyInspect(event, node.id)}>
            <rect x={node.x - 62} y={node.y - 23} width="124" height="46" rx="9" />
            <text x={node.x} y={node.y - 2} text-anchor="middle">{clip(node.label || node.id, 20)}</text>
            <text class="graph-node-type" x={node.x} y={node.y + 14} text-anchor="middle">{clip(node.type || '', 18)}</text>
          </g>
        {/each}
      </svg>
    </div>
    {#if graph.clipped}<p class="hint">Aperçu visuel limité à {MAX_VISUAL_NODES} nœuds; le DTO complet reste disponible via le détail/export.</p>{/if}
  {:else}<p class="empty-renderer">Aucune dépendance visible.</p>{/if}
  <details>
    <summary>Liste accessible des dépendances</summary>
    <div class="renderer-stack compact-stack">{#each data.edges || [] as edge}<div class="renderer-edge"><button on:click={() => inspect(edge.source)}>{byId[edge.source]?.label || edge.source}</button><span>→</span><button on:click={() => inspect(edge.target)}>{byId[edge.target]?.label || edge.target}</button><small>{edge.kind} · {edge.relationLabel}</small></div>{/each}</div>
  </details>
  {#if data.cycles?.length}<details><summary>Cycles détectés</summary>{#each data.cycles as cycle}<p>{cycle.map((id) => byId[id]?.label || id).join(' → ')}</p>{/each}</details>{/if}
</div>
