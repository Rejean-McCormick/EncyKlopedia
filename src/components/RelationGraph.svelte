<script>
  export let rows = [];
  export let selected = null;
  export let detail = null;
  export let labels = {};
  export let relations = [];
  export let rootLabel = 'Sélection';
  export let inspect;
  $: neighbors = detail
    ? detail.assertions
        .filter((a) => relations.find((r) => r.id === a.payload.relation)?.valueKind === 'entity')
        .map((a) => ({
          id: a.payload.subject === selected ? a.payload.value : a.payload.subject,
          relation:
            relations.find((r) => r.id === a.payload.relation)?.label.fr || a.payload.relation,
          status: a.payload.status,
        }))
    : rows.map((r) => ({ id: r.entityId, relation: 'correspondance', status: '' }));
  $: nodes = [
    ...new Map(neighbors.filter((n) => n.id !== selected).map((n) => [n.id, n])).values(),
  ].slice(0, 12);
  $: center = detail ? labels[selected] : rootLabel;
  function xy(i, n) {
    const angle = (i * 2 * Math.PI) / Math.max(n, 1) - Math.PI / 2;
    return { x: 350 + 245 * Math.cos(angle), y: 220 + 165 * Math.sin(angle) };
  }
  function shorten(s, n = 24) {
    return s?.length > n ? s.slice(0, n - 1) + '…' : s;
  }
</script>

<div class="graph-view">
  <svg
    class="graph-canvas"
    viewBox="0 0 700 440"
    role="img"
    aria-label={detail ? 'Relations visibles de ' + center : 'Entités de la page courante'}
  >
    {#each nodes as n, i}{@const p = xy(i, nodes.length)}<line
        x1="350"
        y1="220"
        x2={p.x}
        y2={p.y}
      /><text class="edge-label" x={(350 + p.x) / 2} y={(220 + p.y) / 2 - 5} text-anchor="middle"
        >{shorten(n.relation, 16)}</text
      >{/each}
    <circle class="center" cx="350" cy="220" r="49" /><text x="350" y="223" text-anchor="middle"
      >{shorten(center, 19)}</text
    >
    {#each nodes as n, i}{@const p = xy(i, nodes.length)}<g
        role="button"
        tabindex="0"
        aria-label={'Inspecter ' + labels[n.id]}
        on:click={() => inspect(n.id)}
        on:keydown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            inspect(n.id);
          }
        }}
        ><circle cx={p.x} cy={p.y} r="17" /><text x={p.x} y={p.y + 34} text-anchor="middle"
          >{shorten(labels[n.id] || n.id)}</text
        ><title>{labels[n.id]} · {n.relation}{n.status ? ' · ' + n.status : ''}</title></g
      >{/each}
  </svg>
  <p class="hint">
    {detail
      ? 'Relations visibles, limitées à 12 voisins. Les statuts et sources figurent dans l’inspecteur.'
      : 'Vue de la sélection, limitée à 12 entités de cette page. Cliquez sur une entité pour explorer ses relations.'}
  </p>
  {#if detail}<button class="button" on:click={() => inspect(null)}>Revenir à la sélection</button
    >{/if}
</div>
