<script>
  export let selection;
  export let registry;
  export let labels;
  export let depth = 0;
  const types = { human: 'Personnes', work: 'Œuvres', place: 'Lieux', concept: 'Concepts' };
  function filterLabel(f) {
    const relation = registry.find((r) => r.id === f.relation)?.label.fr || f.relation;
    const ops = {
      exists: 'renseigné',
      missing_in_view: 'absent de la vue',
      in: 'parmi',
      none_of: 'aucune valeur parmi',
      overlaps: 'chevauche',
    };
    return (
      relation +
      ' · ' +
      ops[f.op] +
      ' ' +
      (f.values
        ? f.values.map((v) => labels[v.id] || v.value || v.id).join(', ')
        : f.interval
          ? `${f.interval.from}–${f.interval.to}`
          : '')
    );
  }
</script>

<div class={`query-branch query-depth-${Math.min(depth, 3)}`}>
  <div class="query-node">
    <span class="node-dot"></span><strong
      >{types[selection.entityType] || selection.entityType}</strong
    >{#if selection.ids}<span class="subtle"
        >{selection.ids.map((id) => labels[id] || id).join(', ')}</span
      >{/if}
  </div>
  {#each selection.filters as f}<div class="query-condition">{filterLabel(f)}</div>{/each}
  {#each selection.links as link}<div class="query-link">
      <span>{registry.find((r) => r.id === link.relation)?.label.fr || link.relation} →</span
      ><svelte:self selection={link.target} {registry} {labels} depth={depth + 1} />
    </div>{/each}
</div>
