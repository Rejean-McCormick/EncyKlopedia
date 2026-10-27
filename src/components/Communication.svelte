<script>
  export let query;
  export let cursor = null;
  export let entityId = null;
  export let capabilities = {};
  export let disabled = false;
  export let authToken = '';
  export let kristal = '';
  let action = 'query',
    language = 'fr',
    locale = 'fr-CA',
    busy = false,
    error = '',
    result = null,
    request = null,
    controller;
  const isOpaqueRef = (value) => /^sha256:[0-9a-f]{64}$/i.test(String(value || ''));
  $: visibleSourceRefs = (result?.source_refs || []).filter((ref) => !isOpaqueRef(ref));
  $: identity = JSON.stringify({ query, cursor, entityId, action, language, locale, kristal });
  $: if (identity) {
    controller?.abort();
    busy = false;
    result = null;
    request = null;
    error = '';
  }
  async function communicate(render) {
    const current = identity;
    controller?.abort();
    controller = new AbortController();
    busy = true;
    error = '';
    try {
      const response = await fetch(render ? '/api/sa' : '/api/sa/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}), ...(kristal ? { 'X-Konstellation-Kristal': kristal } : {}) },
        body: JSON.stringify({ query, cursor, entityId, action, language, locale }),
        signal: controller.signal,
      });
      const data = await response.json();
      if (current !== identity) return;
      if (!response.ok) throw Error(data.error?.message || 'Communication indisponible.');
      if (render) result = data.result;
      else request = data;
    } catch (e) {
      if (e.name !== 'AbortError' && current === identity) error = e.message;
    } finally {
      if (current === identity) busy = false;
    }
  }
  function download() {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(request, null, 2)], { type: 'application/json' }),
    );
    const a = document.createElement('a');
    a.href = url;
    a.download = 'konstellation-communication-request.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
</script>

<details class="communication">
  <summary>Expliquer cette exploration</summary>
  <p>
    La communication conserve les critères, le contexte de lecture et les statuts des assertions.
  </p>
  <div class="controls">
    <label
      >Portée<select aria-label="Portée de communication" bind:value={action}
        ><option value="query">Les critères</option><option value="page">La page affichée</option
        ><option value="entity" disabled={!entityId}>L’entité inspectée</option></select
      ></label
    >
    <label>Langue<input aria-label="Langue de communication" bind:value={language} /></label>
    <label>Locale<input aria-label="Locale de communication" bind:value={locale} /></label>
    <button
      disabled={busy || disabled || (action === 'entity' && !entityId)}
      on:click={() => communicate(false)}>Préparer la requête</button
    >
    <button
      disabled={busy ||
        disabled ||
        !capabilities?.available ||
        !capabilities?.languages?.includes(language) ||
        (action === 'entity' && !entityId)}
      on:click={() => communicate(true)}>Formuler avec SA</button
    >
  </div>
  {#if !capabilities?.available}<p>
      {capabilities?.reason ||
        'Aucun service SA configuré. La requête structurée peut être exportée.'}
    </p>{/if}
  {#if busy}<p role="status">Communication en cours…</p>{/if}
  {#if error}<p role="alert">{error}</p>{/if}
  {#if request}<button on:click={download}>Exporter CommunicationRequest</button>
    <details>
      <summary>Voir la requête structurée</summary>
      <pre>{JSON.stringify(request, null, 2)}</pre>
    </details>{/if}
  {#if result}<section aria-label="Formulation SA">
      {#each result.blocks as block}<div>
          {#if block.kind === 'list'}<ul>
              {#each block.items as item}<li>{item.text}</li>{/each}
            </ul>
          {:else if block.kind === 'label_value'}<p>
              <strong>{block.label}</strong> : {block.value}
            </p>
          {:else if block.kind === 'heading'}<h3>{block.text}</h3>
          {:else}<p>{block.text}</p>{/if}
        </div>{/each}
      <small
        >Runtime : {result.runtime.runtime_set_id} · {result.coverage.length} obligations couvertes</small
      >
      {#if visibleSourceRefs.length}<details>
        <summary>Références communiquées</summary>
        <ul>
          {#each visibleSourceRefs as ref}<li>{ref}</li>{/each}
        </ul>
      </details>{/if}
    </section>{/if}
</details>

<style>
  .communication {
    margin: 1rem 0;
    padding: 1.1rem;
    border: 1px solid #ddd8ce;
    border-radius: 12px;
    background: #fffdf8;
    color: #34453b;
  }
  summary {
    cursor: pointer;
    font-weight: 600;
    font-size: 15px;
    line-height: 1.45;
  }
  .communication > p,
  .communication section p,
  .communication li {
    font-size: 14px;
    line-height: 1.55;
  }
  .controls {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    align-items: end;
  }
  label {
    display: grid;
    gap: 0.3rem;
    font-size: 14px;
  }
  input,
  select,
  button {
    font: inherit;
    padding: 0.55rem;
    border: 1px solid #c8cfc6;
    border-radius: 6px;
    background: white;
  }
  input {
    width: 8rem;
  }
  button {
    cursor: pointer;
  }
  button:disabled {
    opacity: 0.5;
    cursor: default;
  }
  pre {
    max-height: 22rem;
    overflow: auto;
    font-size: 12px;
  }
  small {
    overflow-wrap: anywhere;
  }
</style>
