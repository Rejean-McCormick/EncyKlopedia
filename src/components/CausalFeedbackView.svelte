<script>
  export let data;
  export let inspect = () => {};
  $: byId = Object.fromEntries((data.nodes || []).map((node) => [node.id, node]));
  const sign = (edge) => edge.sign > 0 ? '＋' : edge.sign < 0 ? '−' : '→';
  function cycleLayout(ids) {
    const unique = [...new Set(ids || [])].slice(0, 24); const cx = 300, cy = 200, radius = Math.max(90, Math.min(150, 55 + unique.length * 8));
    return unique.map((id, index) => ({ id, x: cx + Math.cos((index / Math.max(1, unique.length)) * Math.PI * 2 - Math.PI / 2) * radius, y: cy + Math.sin((index / Math.max(1, unique.length)) * Math.PI * 2 - Math.PI / 2) * radius }));
  }
  $: cycleNodes = cycleLayout(data.cycles?.[0] || []);
  $: cyclePositions = Object.fromEntries(cycleNodes.map((node) => [node.id, node]));
  $: cycleEdges = cycleNodes.length > 1 ? cycleNodes.map((node, index) => ({ source: node.id, target: cycleNodes[(index + 1) % cycleNodes.length].id })) : [];
  const clip = (text, size = 18) => String(text || '').length > size ? `${String(text).slice(0, size - 1)}…` : String(text || '');
  function keyInspect(event, id) { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); inspect(id); } }
</script>

<div class="renderer-stack" data-renderer="causal-feedback">
  {#if cycleNodes.length > 1}
    <div class="feedback-canvas"><svg viewBox="0 0 600 400" role="img" aria-label="Boucle causale principale">
      <defs><marker id="feedback-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" /></marker></defs>
      {#each cycleEdges as edge}{@const source = cyclePositions[edge.source]}{@const target = cyclePositions[edge.target]}<line class="graph-link" x1={source.x} y1={source.y} x2={target.x} y2={target.y} marker-end="url(#feedback-arrow)" />{/each}
      {#each cycleNodes as node}<g class="graph-node" role="button" tabindex="0" aria-label={`Inspecter ${byId[node.id]?.label || node.id}`} on:click={() => inspect(node.id)} on:keydown={(event) => keyInspect(event, node.id)}><circle cx={node.x} cy={node.y} r="34" /><text x={node.x} y={node.y + 4} text-anchor="middle">{clip(byId[node.id]?.label || node.id)}</text></g>{/each}
    </svg></div>
  {/if}
  {#if data.cycles?.length > 1}<div class="cycle-cards">{#each data.cycles.slice(1, 8) as cycle}<section class="renderer-card"><strong>Boucle</strong><p>{cycle.map((id) => byId[id]?.label || id).join(' → ')}</p></section>{/each}</div>{/if}
  <details open={!cycleNodes.length}><summary>Relations causales visibles</summary><div class="renderer-stack compact-stack">{#each data.edges || [] as edge}<div class="renderer-edge"><button on:click={() => inspect(edge.source)}>{byId[edge.source]?.label || edge.source}</button><span class="causal-sign">{sign(edge)}</span><button on:click={() => inspect(edge.target)}>{byId[edge.target]?.label || edge.target}</button><small>{edge.relationLabel}</small></div>{:else}<p class="empty-renderer">Aucune relation causale visible.</p>{/each}</div></details>
</div>
