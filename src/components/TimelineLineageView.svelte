<script>
  export let data;
  export let inspect = () => {};
  const label = (item) => item.entity?.label || item.entity?.id || item.id;
  const when = (item) => item.start == null
    ? (item.temporalLabel || 'date inconnue')
    : (item.end == null || item.end === item.start ? String(item.start) : `${item.start} – ${item.end}`);
  $: items = [...(data.items || [])].sort((a, b) => (a.start ?? Number.MAX_SAFE_INTEGER) - (b.start ?? Number.MAX_SAFE_INTEGER) || label(a).localeCompare(label(b), 'fr'));
</script>

<div class="renderer-stack" data-renderer="timeline-lineage">
  <div class="adaptive-timeline" role="list" aria-label="Chronologie visible">
    {#each items as item}
      <div role="listitem">
        <button class="timeline-entry" aria-label={`Inspecter ${label(item)} · ${when(item)} · ${item.relationLabel}`} on:click={() => item.entity?.id && inspect(item.entity.id)}>
          <span class="timeline-date">{when(item)}</span>
          <span class="timeline-dot" aria-hidden="true"></span>
          <span class="timeline-copy"><strong>{label(item)}</strong><small>{item.relationLabel}</small></span>
        </button>
      </div>
    {:else}
      <p class="empty-renderer">Aucun repère temporel visible.</p>
    {/each}
  </div>
  {#if data.links?.length}
    <details>
      <summary>{data.links.length} lien(s) de lignée/succession</summary>
      <ul>{#each data.links as link}<li>{link.kind} · {link.from || link.assertionRef} → {link.to || 'lignée déclarée'}</li>{/each}</ul>
    </details>
  {/if}
</div>
