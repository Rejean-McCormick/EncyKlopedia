<script>
  import { onDestroy, tick } from 'svelte';
  import { layoutConstellation, splitLabel } from '../lib/constellation/layout.js';
  import { portraitFor, orbitPreview } from '../lib/constellation/profile.mjs';
  export let rows = [];
  export let labels = {};
  export let entities = {};
  export let rootLabel = 'Sélection';
  export let context;
  export let lensRef;
  export let path = [];
  export let limit = 8;
  export let inspect = () => {};
  export let authToken = '';
  export let kristal = '';

  const VIEW_WIDTH = 1000;
  const VIEW_HEIGHT = 620;
  const BASE_CENTER_X = 500;
  const HISTORY_CENTER_X = 565;
  const CENTER_Y = 300;
  const HISTORY_X = 82;

  let data = null,
    busy = false,
    error = '',
    controller,
    requestedKey = '',
    resolvedKey = '',
    resolvedCenterKey = 'root',
    resolvedPathDepth = 0,
    hoveredKey = '',
    hoveredNode = null,
    preview = null,
    previewBusy = false,
    previewTimer,
    previewController,
    openPortrait = null,
    portraitCloseButton,
    portraitInvoker,
    portraitImageFailed = false;
  const previewCache = new Map();

  $: current = path.at(-1) || null;
  $: accessKey = JSON.stringify({ context, lensRef, kristal, authToken });
  let previousAccessKey = '';
  $: if (accessKey !== previousAccessKey) {
    previousAccessKey = accessKey;
    previewCache.clear();
    clearPreview();
  }
  $: requestKey = current
    ? JSON.stringify({ context, lensRef, focus: current.focus, groupId: current.groupId, limit, kristal, authToken })
    : '';
  $: if (requestKey && requestKey !== requestedKey) load(requestKey, path.length);

  $: rootSatellites = rows.slice(0, limit).map((r) => ({
    id: r.entityId,
    kind: 'entity',
    label: labels[r.entityId] || r.entityId,
    count: null,
    target: { focus: { kind: 'entity', id: r.entityId }, groupId: null },
    salience: null,
    evidence: null,
  }));
  $: rootModel = {
    center: { label: rootLabel, kind: 'group', description: 'Sélection courante' },
    satellites: rootSatellites,
    totalCandidates: rows.length,
    truncated: rows.length > rootSatellites.length,
  };
  $: if (!current) data = rootModel;

  $: model = data || rootModel;
  $: previousEntry = resolvedPathDepth > 1 ? path[resolvedPathDepth - 2] : null;
  $: centerX = previousEntry ? HISTORY_CENTER_X : BASE_CENTER_X;
  $: centerPortrait = current?.focus?.kind === 'entity' && !current.groupId ? portraitFor(entities[current.focus.id], labels[current.focus.id]) : null;
  $: previewPositioned = hoveredNode && preview ? orbitPreview(preview.satellites || [], hoveredNode, VIEW_WIDTH, VIEW_HEIGHT, 6, positioned.map((n) => ({ x:n.x, y:n.y, r:radius(n) }))) : [];
  $: positioned = layoutConstellation(
    model?.satellites || [],
    VIEW_WIDTH,
    VIEW_HEIGHT,
    centerX,
    CENTER_Y,
  );

  async function load(key, depth) {
    clearPreview();
    openPortrait = null;
    controller?.abort();
    requestedKey = key;
    controller = new AbortController();
    busy = true;
    error = '';
    try {
      const { kristal: _kristal, authToken: _authToken, ...payload } = JSON.parse(key);
      const response = await fetch('/api/constellation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}), ...(kristal ? { 'X-Konstellation-Kristal': kristal } : {}) },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      const value = await response.json();
      if (!response.ok) throw Error(value.error?.message || 'Constellation indisponible.');
      if (requestedKey === key) {
        data = value;
        resolvedKey = key;
        resolvedPathDepth = depth;
        resolvedCenterKey = JSON.stringify({ focus: payload.focus, groupId: payload.groupId });
      }
    } catch (e) {
      if (e.name !== 'AbortError' && requestedKey === key) error = e.message;
    } finally {
      if (requestedKey === key) busy = false;
    }
  }

  function portrait(node) {
    const focus = node?.target?.focus;
    return focus?.kind === 'entity' && !node.target.groupId
      ? portraitFor(entities[focus.id], labels[focus.id] || node.label)
      : null;
  }
  function clearPreview() {
    clearTimeout(previewTimer);
    previewController?.abort();
    previewController = null;
    hoveredKey = '';
    hoveredNode = null;
    preview = null;
    previewBusy = false;
  }
  function hidePreview(node) {
    if (hoveredKey === nodeKey(node)) clearPreview();
  }
  function showPreview(node) {
    if (!node?.target?.focus) return;
    const key = nodeKey(node);
    if (hoveredKey === key) return;
    clearPreview();
    hoveredKey = key;
    hoveredNode = node;
    const params = { context, lensRef, focus: node.target.focus, groupId: node.target.groupId, limit: 6, kristal };
    const requestAuthToken = authToken;
    const cacheKey = JSON.stringify({ params, accessKey });
    if (previewCache.has(cacheKey)) {
      preview = previewCache.get(cacheKey);
      return;
    }
    previewBusy = true;
    previewTimer = setTimeout(async () => {
      previewController = new AbortController();
      try {
        const { kristal: _kristal, ...payload } = params;
        const response = await fetch('/api/constellation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...(requestAuthToken ? { Authorization: `Bearer ${requestAuthToken}` } : {}), ...(kristal ? { 'X-Konstellation-Kristal': kristal } : {}) },
          body: JSON.stringify(payload),
          signal: previewController.signal,
        });
        if (!response.ok) throw Error('Aperçu indisponible');
        const value = await response.json();
        if (hoveredKey !== key || requestAuthToken !== authToken) return;
        if (previewCache.size >= 40) previewCache.delete(previewCache.keys().next().value);
        previewCache.set(cacheKey, value);
        preview = value;
      } catch (e) {
        if (e.name !== 'AbortError' && hoveredKey === key) preview = { satellites: [] };
      } finally {
        if (hoveredKey === key) previewBusy = false;
      }
    }, 140);
  }
  async function showPortrait(profile, event) {
    clearPreview();
    portraitInvoker = event?.currentTarget || null;
    portraitImageFailed = false;
    openPortrait = profile;
    await tick();
    portraitCloseButton?.focus();
  }
  function closePortrait() {
    openPortrait = null;
    if (portraitInvoker?.isConnected) portraitInvoker.focus();
    portraitInvoker = null;
  }
  function navigate(node) {
    clearPreview();
    openPortrait = null;
    const entry = { focus: node.target.focus, groupId: node.target.groupId, label: node.label };
    path = [...path, entry];
    if (entry.focus.kind === 'entity' && !entry.groupId) inspect(entry.focus.id);
  }

  function go(index) {
    clearPreview();
    openPortrait = null;
    const nextPath = index < 0 ? [] : path.slice(0, index + 1);
    const nextDepth = nextPath.length;
    path = nextPath;

    if (!nextDepth) {
      controller?.abort();
      requestedKey = '';
      resolvedKey = '';
      resolvedPathDepth = 0;
      resolvedCenterKey = 'root';
      busy = false;
      error = '';
      data = rootModel;
      return;
    }

    const entry = path.at(-1);
    if (entry?.focus.kind === 'entity' && !entry.groupId) inspect(entry.focus.id);
  }

  function radius(node) {
    if (node.kind === 'group') return 41;
    if (node.kind === 'source') return 34;
    return 31;
  }
  function nodeClass(node) {
    return `constellation-node kind-${node.kind}`;
  }
  function nodeKey(node) {
    return JSON.stringify({ id: node.id, kind: node.kind, target: node.target });
  }
  function onLimit(event) {
    clearPreview();
    limit = Number(event.currentTarget.value);
  }

  onDestroy(() => { controller?.abort(); clearPreview(); });
</script>

<div class="constellation-view" aria-busy={busy} on:keydown={(e) => { if (e.key === 'Escape') { clearPreview(); if(openPortrait) { e.preventDefault(); closePortrait(); } } }}>
  <div class="constellation-toolbar">
    <nav class="constellation-breadcrumb" aria-label="Chemin de constellation">
      <button on:click={() => go(-1)}>Sélection</button>
      {#each path as item, i}<span>›</span><button class:current={i === path.length - 1} on:click={() => go(i)}>{item.label}</button>{/each}
    </nav>
    <label class="satellite-limit">
      <span>Satellites <strong>{limit}</strong></span>
      <input aria-label="Nombre maximal de satellites" type="range" min="3" max="25" step="1" value={limit} on:input={onLimit} />
    </label>
  </div>

  {#if error}<div class="constellation-message error">{error}</div>
  {:else if model}
    <svg class:loading={busy} class="constellation-canvas" viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`} role="group" aria-label={'Constellation autour de ' + model.center.label}>
      {#if previousEntry}
        <path
          class="constellation-history-edge"
          d={`M ${HISTORY_X + 27} ${CENTER_Y} C 215 ${CENTER_Y}, ${centerX - 150} ${CENTER_Y}, ${centerX - 72} ${CENTER_Y}`}
          pathLength="1"
        />
      {/if}

      {#each positioned as node (nodeKey(node))}
        <line
          class="constellation-edge"
          x1={centerX}
          y1={CENTER_Y}
          x2={node.x}
          y2={node.y}
          pathLength="1"
        />
      {/each}

      {#if previousEntry}
        <g
          class="constellation-history-node"
          role="button"
          tabindex="0"
          aria-label={'Revenir à ' + previousEntry.label}
          transform={`translate(${HISTORY_X} ${CENTER_Y})`}
          on:click={() => go(resolvedPathDepth - 2)}
          on:keydown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              go(resolvedPathDepth - 2);
            }
          }}
        >
          <circle r="24" />
          <text class="history-mark" y="5" text-anchor="middle">‹</text>
          <text class="history-kicker" y="-35" text-anchor="middle">précédent</text>
          {#each splitLabel(previousEntry.label, 15) as line, i}<text class="history-label" y={44 + i * 16} text-anchor="middle">{line}</text>{/each}
          <title>Revenir à {previousEntry.label}</title>
        </g>
      {/if}

      <g class="constellation-center-frame" transform={`translate(${centerX} ${CENTER_Y})`}>
        {#key resolvedCenterKey}
          <g class="constellation-center constellation-center-motion">
            <circle r="76" />
            {#each splitLabel(model.center.label, 18) as line, i}<text y={-5 + i * 20} text-anchor="middle">{line}</text>{/each}
            {#if model.center.kind !== 'group'}<text class="node-kind" y="42" text-anchor="middle">{model.center.kind}</text>{/if}
          </g>
        {/key}
      </g>

      {#each positioned as node (nodeKey(node))}
        <g
          class={nodeClass(node)}
          role="button"
          tabindex="0"
          transform={`translate(${node.x} ${node.y})`}
          aria-label={'Explorer ' + node.label}
          on:mouseenter={() => showPreview(node)}
          on:mouseleave={() => hidePreview(node)}
          on:focus={() => showPreview(node)}
          on:blur={() => hidePreview(node)}
          on:click={() => navigate(node)}
          on:keydown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              navigate(node);
            }
          }}
        >
          <g class="constellation-node-motion">
            <circle r={radius(node)} />
            {#if node.count !== null}<text class="node-count" y="4" text-anchor="middle">{node.count}</text>{:else}<text class="node-mark" y="5" text-anchor="middle">{node.kind === 'source' ? '◫' : node.kind === 'group' ? '✦' : '•'}</text>{/if}
            {#each splitLabel(node.label) as line, i}<text class="node-label" y={radius(node) + 22 + i * 19} text-anchor="middle">{line}</text>{/each}
            <title>{node.label}{node.salience ? ` · score ${node.salience.score} · ${node.evidence.assertionCount} assertion(s)` : ''}</title>
          </g>
        </g>
      {/each}
      {#if centerPortrait}
        <g class="constellation-portrait-indicator" role="button" tabindex="0"
          aria-label={'Ouvrir la fiche de ' + centerPortrait.title}
          transform={`translate(${centerX + 57} ${CENTER_Y - 55})`}
          on:click={(e) => showPortrait(centerPortrait, e)}
          on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); showPortrait(centerPortrait, e); } }}>
          <circle r="13" /><text text-anchor="middle" y="4">i</text>
        </g>
      {/if}
      {#each positioned as node (nodeKey(node))}
        {#if portrait(node)}
          <g class="constellation-portrait-indicator" role="button" tabindex="0"
            aria-label={'Ouvrir la fiche de ' + node.label}
            transform={`translate(${node.x + radius(node) * 0.8} ${node.y - radius(node) * 0.8})`}
            on:click={(e) => showPortrait(portrait(node), e)}
            on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); showPortrait(portrait(node), e); } }}>
            <circle r="12" /><text text-anchor="middle" y="4">i</text>
          </g>
        {/if}
      {/each}
      {#if hoveredNode && (previewBusy || previewPositioned.length)}
        <g class="constellation-preview-overlay" aria-hidden="true">
          <circle class="constellation-preview-origin" cx={hoveredNode.x} cy={hoveredNode.y} r="47" />
          {#each previewPositioned as child, i (i)}
            <line x1={hoveredNode.x} y1={hoveredNode.y} x2={child.x} y2={child.y} />
            <g transform={`translate(${child.x} ${child.y})`}>
              <circle r="20" />
              <text class="preview-symbol" text-anchor="middle" y="4">{child.kind === 'group' ? '✦' : '•'}</text>
              {#each splitLabel(child.label, 13) as line, k}<text class="preview-label" text-anchor="middle" y={30 + k * 13}>{line}</text>{/each}
            </g>
          {/each}
          {#if previewBusy}<text class="preview-loading" x={hoveredNode.x} y={hoveredNode.y + 54} text-anchor="middle">Aperçu…</text>{/if}
        </g>
      {/if}
    </svg>
    {#if openPortrait}
      <section class="constellation-portrait-card" role="dialog" aria-modal="false" aria-label={'Fiche de ' + openPortrait.title}>
        <button class="portrait-close" bind:this={portraitCloseButton} aria-label="Fermer la fiche" on:click={closePortrait}>×</button>
        <div class="portrait-eyebrow">FICHE · {openPortrait.typeLabel}</div>
        <div class="portrait-visual">
          {#if openPortrait.image && !portraitImageFailed}<img src={openPortrait.image} loading="lazy" decoding="async" alt={'Illustration de ' + openPortrait.title} on:error={() => (portraitImageFailed = true)} />
          {:else}<span aria-hidden="true">{openPortrait.symbol}</span>{/if}
        </div>
        <h3>{openPortrait.title}</h3>
        {#if openPortrait.description}<p>{openPortrait.description}</p>{/if}
        {#each openPortrait.fields as field}<div class="portrait-field"><strong>{field.name}</strong><span>{field.value}</span></div>{/each}
        <p class="portrait-footnote">Informations déclarées dans le jeu de données.</p>
      </section>
    {/if}
    <div class="constellation-footer">
      <span>{model.satellites.length} satellite{model.satellites.length > 1 ? 's' : ''}{model.truncated ? ` sur ${model.totalCandidates}` : ''}</span>
      <span>{busy ? 'Transition vers le nouveau centre…' : 'Classement déterministe · sources et politique de lecture préservées'}</span>
    </div>
    {#if !current}<p class="hint constellation-hint">Cliquez sur une entité pour la placer au centre. Les niveaux suivants regroupent relations, thèmes et sources sans créer de nouvelles assertions.</p>{/if}
  {/if}
</div>
