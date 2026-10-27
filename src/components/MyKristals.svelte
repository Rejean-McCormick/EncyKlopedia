<script>
  // KNAV experimental fleet browser: all search/facets are client-side over
  // the already authorized response from GET /api/fleet.
  export let visible = false;
  export let items = [];
  export let opening = false;
  export let hasCurrent = false;
  export let onOpen = async () => {};
  export let onExploreCurrent = () => {};
  let search = '';
  let source = 'all';
  let availability = 'all';
  let selected = null;
  const lower = (text) => String(text || '').toLocaleLowerCase();
  $: filtered = items.filter((item) => {
    const q = lower(search.trim());
    return (source === 'all' || item.source === source) &&
      (availability === 'all' || item.availability === availability) &&
      (!q || [item.title, item.stateRef, item.archetype, item.id, item.discovery?.classification?.primary_archetype, item.discovery?.classification?.primary_usage].some((value) => lower(value).includes(q)));
  });
  $: if (selected && !filtered.some((item) => item.key === selected.key)) selected = null;
</script>

<section class="fleet" hidden={!visible} aria-label="My Kristals">
  <header class="fleet-heading">
    <div>
      <span class="fleet-eyebrow">KRISTAL NETWORK · READ ONLY</span>
      <h1>Mes Kristals<span class="fleet-accent">.</span></h1>
      <p>Choisissez un Kristal local pour l’ouvrir dans Konstellation. Un inventaire ne prouve pas sa publication ni sa qualification.</p>
    </div>
    {#if hasCurrent}<button class="button" on:click={onExploreCurrent}>Explorer le Kristal ouvert →</button>{/if}
  </header>
  <div class="fleet-disclaimer" role="status">
    Local Manager inventory requires explicit authorization. Authoring Kit Discovery 3.3 is advisory metadata only; it does not prove qualification, publication or a usable reader. Hosted index metadata is not a publication receipt.
  </div>
  <div class="fleet-filters">
    <label>Search Kristals<input aria-label="Search Kristals" type="search" bind:value={search} placeholder="Name, state reference, archetype or usage" /></label>
    <label>Source<select aria-label="Kristal source" bind:value={source}>
      <option value="all">All permitted sources</option>
      <option value="local_manager_preview">Local Manager inventory</option>
      <option value="github_v10_checkout">GitHub v10 checkout</option>
      <option value="local_v10_reader">Local Kristal v10 reader</option>
      <option value="legacy_reader">Legacy reader</option>
    </select></label>
    <label>Availability<select aria-label="Kristal availability" bind:value={availability}>
      <option value="all">All states</option><option value="available">Available</option>
      <option value="unavailable">Unavailable</option><option value="unknown">Unknown</option>
    </select></label>
  </div>
  <p class="fleet-count">{filtered.length} visible {filtered.length === 1 ? 'entry' : 'entries'} · Counts reflect only permitted inventory</p>
  <div class="fleet-layout">
    <div class="fleet-grid" aria-label="Permitted Kristals">
      {#each filtered as item (item.key)}
        <button class="fleet-card" class:selected={selected?.key === item.key} on:click={() => (selected = item)} aria-label={'Inspect ' + item.title}>
          <span class="fleet-card-top"><span class="fleet-type">{item.source === 'local_manager_preview' ? 'LOCAL INVENTORY' : item.source === 'github_v10_checkout' ? 'GITHUB V10' : item.source === 'local_v10_reader' ? 'LOCAL V10 READER' : 'LEGACY READER'}</span><span class="fleet-indicator">{item.availability}</span></span>
          <strong>{item.title}</strong>
          <span class="fleet-ref">{item.stateRef || 'State reference not supplied'}</span>
          <span class="fleet-card-bottom">{item.openable ? 'Reader configured' : 'Inventory only'} · {item.readiness.replaceAll('_', ' ')}</span>
        </button>
      {:else}
        <div class="fleet-empty">No permitted entries match these filters. Unknown or missing inventory is not evidence of absence.</div>
      {/each}
    </div>
    <aside class="fleet-detail" aria-label="Kristal properties">
      {#if selected}
        <span class="fleet-eyebrow">ENTRY PROPERTIES</span>
        <h2>{selected.title}</h2>
        <dl>
          <dt>Source</dt><dd>{selected.source.replaceAll('_', ' ')}</dd>
          <dt>Reference</dt><dd>{selected.stateRef || 'Not supplied'}</dd>
          <dt>State commitment</dt><dd>{selected.stateCommitment || 'Not supplied'}</dd>
          <dt>Availability</dt><dd>{selected.availability}</dd>
          <dt>Readiness (declared)</dt><dd>{selected.readiness.replaceAll('_', ' ')}</dd>
          <dt>Verification</dt><dd>{selected.verification.replaceAll('_', ' ')}</dd>
          {#if selected.managerAssessment}
            <dt>Manager (local)</dt><dd>{selected.managerAssessment.result.replaceAll('_', ' ')}</dd>
            <dt>Discovery (Manager)</dt><dd>{selected.managerAssessment.discovery.replaceAll('_', ' ')}</dd>
            <dt>Framework state (Manager)</dt><dd>{selected.managerAssessment.frameworkState.replaceAll('_', ' ')}</dd>
          {/if}
          <dt>View</dt><dd>{selected.viewKind.replaceAll('_', ' ')}</dd>
          <dt>Archetype (declared)</dt><dd>{selected.discovery?.classification?.primary_archetype || selected.archetype || 'Unknown'}</dd>
          {#if selected.discovery}
            <dt>Usage Arketype (declared)</dt><dd>{selected.discovery.classification?.primary_usage || 'Not declared'}</dd>
            <dt>Data organization</dt><dd>{selected.discovery.organization}</dd>
            <dt>Reader recommendation</dt><dd>{selected.discovery.readerProfile}</dd>
            {#if selected.discovery.accessPattern}<dt>Suggested access</dt><dd>{selected.discovery.accessPattern}</dd>{/if}
            <dt>Measured registered bytes</dt><dd>{selected.discovery.trackedLocalBytes.toLocaleString()} ({selected.discovery.sizeClass}; {selected.discovery.completeness.replaceAll('_',' ')})</dd>
            <dt>Discovery status</dt><dd>Declared, noncanonical, not independently verified</dd>
          {/if}
        </dl>
        {#if selected.openable}
          <button class="button primary" disabled={opening} on:click={() => onOpen(selected.readerId)}>{opening ? 'Ouverture…' : 'Ouvrir dans l’explorateur →'}</button>
          <p class="fleet-detail-note">The reader validates its own payload when opened. The result may be a technical hosting view.</p>
        {:else}<p class="fleet-detail-note">No authorized compatible reader is configured for this entry. Manager inventory access does not grant canonical content access.</p>{/if}
      {:else}
        <h2>Choisir un Kristal</h2><p>Sélectionnez une entrée pour connaître ses propriétés et l’ouvrir avec un lecteur compatible.</p>
      {/if}
    </aside>
  </div>
</section>
