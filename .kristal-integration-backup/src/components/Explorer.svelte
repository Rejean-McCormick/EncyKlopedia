<script>
  import { onMount, tick } from 'svelte';
  import Communication from './Communication.svelte';
  import Astrolabe from './Astrolabe.svelte';
  import QueryTree from './QueryTree.svelte';
  import ConstellationView from './ConstellationView.svelte';
  import AdaptiveProjectionView from './AdaptiveProjectionView.svelte';
  let boot = null,
    query = null,
    lensId = '',
    view = 'list',
    result = null,
    facets = {},
    busy = true,
    error = '',
    notice = '',
    selected = null,
    detail = null,
    detailBusy = false,
    navigationPlan = null,
    navigationRecipe = 'catalogue',
    navigationPinned = false,
    authToken = '',
    authRequired = false,
    kristal = '',
    kristalSelectable = false,
    kristals = [],
    switchingKristal = false;
  let search = '',
    history = [],
    future = [],
    saved = [],
    saveName = '',
    showSaved = false,
    showQuery = false,
    showSource = false,
    epochFrom = '',
    epochTo = '',
    queryController,
    detailController,
    navigationController,
    revision = 0,
    currentCursor = null;
  let jsonInput = '',
    importInput,
    libraryFile,
    selectedIds = [],
    constellationPath = [],
    satelliteLimit = 8;
  const typeLabels = {};
  function humanizeType(value) {
    const text = String(value || '')
      .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
      .replace(/[_:./-]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
    return text ? text.charAt(0).toUpperCase() + text.slice(1) : '';
  }
  function typeLabel(type) {
    return typeLabels[type] || boot?.structuralProfile?.entityTypeLabels?.[type] || humanizeType(type);
  }
  const capabilityLabels = {
    temporal: 'temporel', hierarchy: 'hiérarchique', dependency: 'dépendances', sequence: 'séquentiel',
    stateMachine: 'états', conditionalTransition: 'transitions', causal: 'causal', cycle: 'cyclique',
    proof: 'preuves', argumentation: 'argumentatif', multidimensional: 'multidimensionnel',
    multiScale: 'multi-échelle', multiplex: 'multiplexe', spatial: 'spatial', quantitative: 'quantitatif',
    provenance: 'provenance', evidential: 'preuves/sources', versioned: 'versionné', resourceAllocation: 'ressources',
  };
  function capabilityLabel(id) {
    return capabilityLabels[id] || humanizeType(id).toLowerCase();
  }
  const statusLabels = {
    sourced: 'Sourcée',
    validated: 'Validée',
    disputed: 'Contestée',
    hypothesis: 'Hypothèse',
    claimed: 'Déclarée',
    reviewed: 'Révisée',
    rejected: 'Rejetée',
    retracted: 'Rétractée',
    superseded: 'Remplacée',
  };
  $: relations = boot?.registry.relations || [];
  $: lens = boot?.lenses.find((l) => l.id === lensId);
  $: currentFacets =
    lens && query && lens.rootType === query.selection.entityType
      ? lens.facets
      : relations
          .filter((r) => r.domain.includes(query?.selection.entityType))
          .map((r) => ({
            relation: r.id,
            widget: r.valueKind === 'interval' ? 'year-range' : 'entity-picker',
          }));
  function normalizeSearch(value) {
    return String(value || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[_–—-]+/g, ' ')
      .replace(/[^a-z0-9\s]/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }
  function personKey(entity) {
    return entity?.type === 'person' ? normalizeSearch(entity.label) : '';
  }
  $: duplicatePersonLabels = (boot?.entities || []).reduce((counts, entity) => {
    const key = personKey(entity);
    if (key) counts[key] = (counts[key] || 0) + 1;
    return counts;
  }, {});
  function displayEntityLabel(entity, counts = duplicatePersonLabels) {
    if (!entity) return '';
    const duplicated = entity.type === 'person' && counts[personKey(entity)] > 1;
    return duplicated && entity.disambiguation
      ? `${entity.label} — ${entity.disambiguation}`
      : entity.label;
  }
  function entityTypeLabel(entity) {
    return typeLabel(entity?.type) || entity?.type;
  }
  function catalogScore(entity, rawQuery, counts = duplicatePersonLabels) {
    const q = normalizeSearch(rawQuery);
    if (!q) return 0;
    const label = normalizeSearch(entity.label);
    const display = normalizeSearch(displayEntityLabel(entity, counts));
    const aliases = (entity.aliases || []).map(normalizeSearch);
    const description = normalizeSearch(entity.description);
    if (label === q) return 160;
    if (aliases.some((alias) => alias === q)) return 150;
    if (display.includes(q)) return 125;
    if (label.startsWith(q)) return 115;
    if (label.includes(q)) return 105;
    if (aliases.some((alias) => alias.includes(q))) return 95;
    if (description.includes(q)) return 65;
    return 0;
  }
  $: labelMap = Object.fromEntries((boot?.entities || []).map((e) => [e.id, displayEntityLabel(e, duplicatePersonLabels)]));
  $: entityMap = Object.fromEntries((boot?.entities || []).map((e) => [e.id, e]));
  $: catalogRanked = search.trim()
    ? (boot?.entities || [])
        .map((entity) => ({ entity, score: catalogScore(entity, search, duplicatePersonLabels) }))
        .filter((item) => item.score > 0)
        .sort((a, b) =>
          b.score - a.score ||
          displayEntityLabel(a.entity, duplicatePersonLabels).localeCompare(displayEntityLabel(b.entity, duplicatePersonLabels), 'fr') ||
          a.entity.id.localeCompare(b.entity.id),
        )
    : [];
  $: catalogMatchTotal = catalogRanked.length;
  $: catalogMatches = catalogRanked.slice(0, 12);
  $: rows = (result?.rows || []).filter((row) => {
    if (!search.trim()) return true;
    const entity = entityMap[row.entityId];
    return catalogScore(entity || { id: row.entityId, label: labelMap[row.entityId] || row.entityId }, search, duplicatePersonLabels) > 0;
  });
  $: pivots = relations.filter(
    (r) =>
      r.domain.includes(query?.selection.entityType) &&
      r.valueKind === 'entity' &&
      boot?.capabilities?.relations?.[r.id]?.available !== false,
  );
  $: omitted =
    query?.selection.filters.filter((f) => !currentFacets.some((x) => x.relation === f.relation)) ||
    [];
  $: activeCount = countFilters(query?.selection);
  $: if (query) jsonInput = JSON.stringify(query, null, 2);
  $: policy = boot?.policies.find((p) => p.ref === query?.context.readerPolicyRef);
  $: currentNavigationView = navigationPlan?.views?.find((item) => item.id === navigationRecipe) || null;
  $: navigationCapabilities = Object.entries(navigationPlan?.profile?.affordances || {})
    .sort((a, b) => b[1].score - a[1].score)
    .slice(0, 4);
  function countFilters(s) {
    return s
      ? s.filters.length +
          (s.ids ? 1 : 0) +
          s.links.reduce((n, l) => n + 1 + countFilters(l.target), 0)
      : 0;
  }
  const clone = (x) => JSON.parse(JSON.stringify(x));
  const isOpaqueRef = (value) => /^sha256:[0-9a-f]{64}$/i.test(String(value || ''));
  const sourceTitle = (sid) => {
    const title = detail?.sources?.find((s) => s.id === sid)?.title;
    if (title) return title;
    return isOpaqueRef(sid) ? 'Source documentée' : sid;
  };
  async function api(path, body, signal) {
    const headers = body === undefined ? {} : { 'Content-Type': 'application/json' };
    if (authToken) headers.Authorization = `Bearer ${authToken}`;
    if (kristal) headers['X-Konstellation-Kristal'] = kristal;
    const r = await fetch('/api/' + path, {
      method: body === undefined ? 'GET' : 'POST',
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
    const j = await r.json();
    if (!r.ok) { const e = Error(j.error?.message || 'La requête a échoué.'); e.status = r.status; e.code = j.error?.code; throw e; }
    return j;
  }
  async function bootstrapForPolicy(readerPolicyRef) {
    const suffix = readerPolicyRef ? `?readerPolicyRef=${encodeURIComponent(readerPolicyRef)}` : '';
    return api(`bootstrap${suffix}`);
  }
  async function refreshBootstrap(readerPolicyRef) {
    const nextBoot = await bootstrapForPolicy(readerPolicyRef);
    boot = nextBoot;
    return nextBoot;
  }
  function initializeExploration(nextBoot) {
    const nextLensId = nextBoot.lenses[0]?.id || `type:${nextBoot.registry.entityTypes[0]}`;
    const firstLens = nextBoot.lenses.find((l) => l.id === nextLensId);
    const entityType = firstLens?.rootType || nextBoot.registry.entityTypes[0];
    if (!entityType) throw Error('Ce Kristal ne contient aucun type exploratoire visible.');
    boot = nextBoot;
    lensId = nextLensId;
    query = {
      schemaVersion: '0.2',
      context: nextBoot.context,
      selection: { entityType, filters: [], links: [] },
      order: 'entity_id_asc',
      pageSize:
        boot.policies.find((p) => p.ref === boot.context.readerPolicyRef)?.defaultPageSize || 24,
    };
    result = null;
    facets = {};
    history = [];
    future = [];
    search = '';
    selected = null;
    detail = null;
    selectedIds = [];
    constellationPath = [];
    navigationPlan = null;
    navigationRecipe = 'catalogue';
    navigationPinned = false;
    currentCursor = null;
    syncDates();
  }
  async function changeKristal(next) {
    if (!kristalSelectable || !next || next === kristal || switchingKristal) return;
    const target = kristals.find((item) => item.id === next && item.available);
    if (!target) throw Error('Ce Kristal n’est pas disponible dans la collection.');
    const previous = kristal;
    queryController?.abort();
    detailController?.abort();
    navigationController?.abort();
    revision++;
    switchingKristal = true;
    busy = true;
    error = '';
    notice = '';
    kristal = next;
    try {
      const nextBoot = await api('bootstrap');
      initializeExploration(nextBoot);
      try { localStorage.setItem('konstellation.kristal.v1', kristal); } catch {}
      await run();
      notice = `Kristal « ${target.label} » chargé.`;
    } catch (e) {
      kristal = previous;
      error = e.message;
      busy = false;
    } finally {
      switchingKristal = false;
    }
  }
  const FACET_BATCH_SIZE = 32;
  async function loadFacets(queryValue, relationIds, signal) {
    const ids = [...new Set((relationIds || []).filter(Boolean))];
    const merged = {};
    for (let i = 0; i < ids.length; i += FACET_BATCH_SIZE) {
      const relations = ids.slice(i, i + FACET_BATCH_SIZE);
      Object.assign(merged, await api('facets', { query: queryValue, relations }, signal));
    }
    return merged;
  }
  function rendererView(rendererId) {
    if (rendererId === 'table') return 'table';
    if (rendererId === 'constellation') return 'constellation';
    if (rendererId === 'list') return 'list';
    return 'adaptive';
  }
  function applyNavigationRecipe(recipe, pin = true) {
    if (!recipe) return;
    navigationRecipe = recipe.id;
    navigationPinned = pin;
    view = rendererView(recipe.rendererId || recipe.renderer);
    if (view === 'constellation' && selected && !constellationPath.length)
      constellationPath = [{ focus: { kind: 'entity', id: selected }, groupId: null, label: labelMap[selected] || selected }];
  }
  function fallbackAdaptive() {
    const currentRendererId = currentNavigationView?.rendererId;
    const renderer = boot?.navigation?.rendererCatalog?.find((item) => item.id === currentRendererId);
    const fallbackRendererId = renderer?.accessibilityFallback || 'table';
    const fallbackView =
      navigationPlan?.views?.find((item) => item.rendererId === fallbackRendererId) ||
      navigationPlan?.views?.find((item) => item.id === 'table') ||
      navigationPlan?.views?.find((item) => item.id === 'catalogue');
    if (fallbackView) applyNavigationRecipe(fallbackView, true);
    else view = fallbackRendererId === 'list' ? 'list' : 'table';
  }
  async function loadNavigationPlan(queryValue = query, selectedValue = selected) {
    navigationController?.abort();
    navigationController = new AbortController();
    const signal = navigationController.signal;
    try {
      const nextPlan = await api('navigation/plan', {
        query: queryValue,
        lensRef: lensId,
        selectedEntityId: selectedValue || null,
        resultSize: !selectedValue && result?.total?.kind === 'exact' ? result.total.value : null,
      }, signal);
      navigationPlan = nextPlan;
      const current = nextPlan.views.find((item) => item.id === navigationRecipe);
      const chosen = current || nextPlan.views.find((item) => item.id === nextPlan.primaryRecipeId) || nextPlan.views[0];
      applyNavigationRecipe(chosen, navigationPinned && !!current);
    } catch (e) {
      if (e.name !== 'AbortError') {
        navigationPlan = {
          views: [
            { id: 'catalogue', label: 'Liste', rendererId: 'list', icon: '▤', reason: 'Vue générique' },
            { id: 'table', label: 'Tableau', rendererId: 'table', icon: '▦', reason: 'Vue générique' },
            { id: 'constellation', label: 'Constellation', rendererId: 'constellation', icon: '◈', reason: 'Vue générique' },
          ],
          primaryRecipeId: 'catalogue',
          profile: { affordances: {} },
        };
      }
    }
  }
  function state() {
    return {
      schemaVersion: '1.0',
      ...(kristal ? { kristalRef: kristal } : {}),
      query: clone(query),
      lensRef: lensId,
      readerPolicyRef: query.context.readerPolicyRef,
      focus: selected ? { kind: 'entity', id: selected } : null,
      navigation: { recipeId: navigationRecipe, mode: navigationPinned ? 'pinned' : 'adaptive' },
      history: { openQuery: showQuery, constellationPath: clone(constellationPath), satelliteLimit },
    };
  }
  function syncDates() {
    const f = query.selection.filters.find((f) => f.op === 'overlaps');
    epochFrom = f?.interval.from ?? '';
    epochTo = f?.interval.to ?? '';
  }
  function resetDetail() {
    selected = null;
    detail = null;
    detailController?.abort();
    selectedIds = [];
  }
  async function run(cursor = null) {
    queryController?.abort();
    queryController = new AbortController();
    const signal = queryController.signal,
      current = ++revision;
    busy = true;
    currentCursor = cursor;
    error = '';
    await tick();
    if (current !== revision) return;
    const ids = currentFacets.map((f) => f.relation);
    try {
      const data = await api('query', { query, cursor }, signal);
      if (current !== revision) return;
      result = data;
      if (!cursor) {
        try {
          const f = await loadFacets(query, ids, signal);
          if (current === revision) facets = f;
        } catch (e) {
          if (e.name !== 'AbortError' && current === revision) {
            facets = {};
            notice = 'Résultats disponibles. Compteurs indisponibles : ' + e.message;
          }
        }
      }
      if (current === revision) await loadNavigationPlan(query, selected);
    } catch (e) {
      if (e.name !== 'AbortError' && current === revision) {
        error = e.message;
        result = null;
        facets = {};
      }
    } finally {
      if (current === revision) busy = false;
    }
  }
  async function commit(next, options = {}) {
    history = [...history.slice(-99), options.historyState || state()];
    future = [];
    query = next;
    result = null;
    if (options.lens) lensId = options.lens;
    resetDetail();
    constellationPath = [];
    search = '';
    facets = {};
    syncDates();
    await run();
  }
  async function restore(input, record = true) {
    const previousKristal = kristal;
    const previousBoot = boot;
    const previousState = record && query ? state() : null;
    const targetKristal = input?.kristalRef;
    try {
      if (targetKristal && targetKristal !== kristal) {
        const target = kristals.find((item) => item.id === targetKristal && item.available);
        if (!target) throw Error(`Le Kristal « ${targetKristal} » de cette exploration n’est pas disponible.`);
        kristal = targetKristal;
        boot = await api('bootstrap');
      }
      const validation = await api('validate-state', input);
      const s = validation.state || input;
      if (record) {
        history = [...history.slice(-99), previousState || state()];
        future = [];
      }
      if (kristal !== previousKristal) {
        try { localStorage.setItem('konstellation.kristal.v1', kristal); } catch {}
      }
    if (!boot || boot.context?.readerPolicyRef !== s.query?.context?.readerPolicyRef)
      await refreshBootstrap(s.query?.context?.readerPolicyRef);
    query = clone(s.query);
    lensId = boot?.lenses.some((item) => item.id === s.lensRef && item.rootType === query.selection.entityType)
      ? s.lensRef
      : boot?.lenses.find((item) => item.rootType === query.selection.entityType)?.id || `type:${query.selection.entityType}`;
    navigationRecipe = s.navigation?.recipeId || 'catalogue';
    navigationPinned = s.navigation?.mode === 'pinned';
    view = navigationRecipe === 'constellation' ? 'constellation' : navigationRecipe === 'table' ? 'table' : navigationRecipe === 'catalogue' ? 'list' : 'adaptive';
    constellationPath = clone(s.history?.constellationPath || []);
    satelliteLimit = s.history?.satelliteLimit || 8;
    showQuery = Boolean(s.history?.openQuery);
    resetDetail();
    syncDates();
    await run();
      if (s.focus?.kind === 'entity' && s.focus.id) await inspect(s.focus.id);
    } catch (e) {
      kristal = previousKristal;
      boot = previousBoot;
      throw e;
    }
  }
  async function undo() {
    if (!history.length) return;
    const prev = history.at(-1);
    future = [...future, state()];
    history = history.slice(0, -1);
    await restore(prev, false);
  }
  async function redo() {
    if (!future.length) return;
    const next = future.at(-1);
    history = [...history, state()];
    future = future.slice(0, -1);
    await restore(next, false);
  }
  async function changeLens(id) {
    const nextLens = boot.lenses.find((l) => l.id === id);
    if (nextLens.rootType !== query.selection.entityType) {
      notice =
        'Cette perspective ouvre une nouvelle sélection de ' +
        (typeLabel(nextLens.rootType) || nextLens.rootType).toLowerCase() +
        '. Votre parcours reste accessible avec Retour.';
      const next = clone(query);
      next.selection = { entityType: nextLens.rootType, filters: [], links: [] };
      await commit(next, { lens: id });
    } else {
      history = [...history.slice(-99), state()];
      future = [];
      lensId = id;
      constellationPath = [];
      navigationPinned = false;
      await run();
    }
  }
  async function changePolicy(ref) {
    const previousState = state();
    const nextBoot = await refreshBootstrap(ref);
    const next = clone(query);
    next.context = clone(nextBoot.context);
    next.pageSize = Math.min(
      next.pageSize,
      nextBoot.policies.find((p) => p.ref === ref)?.maxPageSize || 100,
    );
    if (!nextBoot.registry.entityTypes.includes(next.selection.entityType)) {
      const fallbackLens = nextBoot.lenses[0];
      const fallbackType = fallbackLens?.rootType || nextBoot.registry.entityTypes[0];
      if (!fallbackType) throw Error('Aucun type visible pour cette politique de lecture.');
      next.selection = { entityType: fallbackType, filters: [], links: [] };
      lensId = fallbackLens?.id || `type:${fallbackType}`;
      notice = 'La sélection précédente n’est pas visible avec cette politique. Konstellation a ouvert le premier espace disponible.';
    } else if (!nextBoot.lenses.some((item) => item.id === lensId && item.rootType === next.selection.entityType)) {
      lensId = nextBoot.lenses.find((item) => item.rootType === next.selection.entityType)?.id || `type:${next.selection.entityType}`;
    }
    await commit(next, { historyState: previousState });
  }
  function relation(id) {
    return relations.find((r) => r.id === id);
  }
  function openConstellation() {
    const recipe = navigationPlan?.views?.find((item) => item.id === 'constellation') || { id: 'constellation', rendererId: 'constellation' };
    applyNavigationRecipe(recipe, true);
  }
  function filterFor(id) {
    return query.selection.filters.find((f) => f.relation === id);
  }
  async function setFilter(id, filter) {
    const next = clone(query);
    next.selection.filters = next.selection.filters.filter((f) => f.relation !== id);
    if (filter) next.selection.filters.push(filter);
    await commit(next);
  }
  async function toggleValue(id, value) {
    const old = filterFor(id);
    const values = old?.values ? clone(old.values) : [];
    const kind = relation(id).valueKind;
    const term = kind === 'entity' ? { kind, id: value } : { kind, value };
    const key = JSON.stringify(term),
      at = values.findIndex((v) => JSON.stringify(v) === key);
    if (at >= 0) values.splice(at, 1);
    else values.push(term);
    await setFilter(
      id,
      values.length ? { relation: id, op: old?.op === 'none_of' ? 'none_of' : 'in', values } : null,
    );
  }
  async function changeOperator(id, op) {
    const old = filterFor(id);
    if (!op) return setFilter(id, null);
    if (op === 'exists' || op === 'missing_in_view') return setFilter(id, { relation: id, op });
    if (old?.values?.length) return setFilter(id, { relation: id, op, values: old.values });
    notice = 'Choisissez d’abord une valeur pour ce filtre.';
  }
  async function applyYears(id) {
    if (epochFrom === '' || epochTo === '') {
      notice = 'Renseignez les deux bornes de la période.';
      return;
    }
    await setFilter(id, {
      relation: id,
      op: 'overlaps',
      interval: {
        from: Number(epochFrom),
        to: Number(epochTo),
        calendar: 'proleptic-gregorian-astronomical',
      },
      match: 'definite',
    });
  }
  async function pivot(id, ids = null) {
    const r = relation(id);
    if (!r.inverseOf) {
      notice = 'Ce pivot requiert une relation inverse déclarée.';
      return;
    }
    const next = clone(query);
    const target = ids
      ? { entityType: r.domain[0], ids, filters: [], links: [] }
      : clone(query.selection);
    next.selection = {
      entityType: r.range,
      filters: [],
      links: [{ relation: r.inverseOf, target }],
    };
    const nextLens = boot.lenses.find((l) => l.rootType === r.range)?.id || 'type:' + r.range;
    showQuery = true;
    await commit(next, { lens: nextLens });
  }
  async function navigateFromAstrolabe(entity) {
    if (!entity?.id || !entity?.type) return;
    const next = clone(query);
    next.selection = { entityType: entity.type, ids: [entity.id], filters: [], links: [] };
    const nextLens = boot.lenses.find((l) => l.rootType === entity.type)?.id || 'type:' + entity.type;
    view = 'list';
    navigationRecipe = 'catalogue';
    navigationPinned = false;
    showQuery = false;
    await commit(next, { lens: nextLens });
    await tick();
    document.querySelector('.workspace')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async function inspect(id) {
    detailController?.abort();
    detailController = new AbortController();
    selected = id;
    detail = null;
    detailBusy = true;
    try {
      const value = await api('entity', { id, context: query.context }, detailController.signal);
      if (selected === id) {
        detail = value;
        await loadNavigationPlan(query, id);
      }
    } catch (e) {
      if (e.name !== 'AbortError') error = e.message;
    } finally {
      if (selected === id) detailBusy = false;
    }
  }
  function remember() {
    try {
      const name = saveName.trim() || 'Exploration du ' + new Date().toLocaleDateString('fr');
      saved = [{ id: crypto.randomUUID(), name, state: state() }, ...saved].slice(0, 40);
      localStorage.setItem('konstellation.saved.v1', JSON.stringify(saved));
      saveName = '';
      notice = 'Exploration enregistrée dans ce navigateur.';
    } catch {
      error = 'Le stockage local est indisponible. Utilisez Exporter.';
    }
  }
  function removeSaved(id) {
    saved = saved.filter((s) => s.id !== id);
    try {
      localStorage.setItem('konstellation.saved.v1', JSON.stringify(saved));
    } catch {
      error = 'Impossible de mettre à jour le stockage local.';
    }
  }
  function download() {
    const blob = new Blob([JSON.stringify(state(), null, 2)], { type: 'application/json' }),
      url = URL.createObjectURL(blob),
      a = document.createElement('a');
    a.href = url;
    a.download = 'konstellation-exploration.json';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  async function importFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      if (file.size > 65536) throw Error('Fichier limité à 64 Kio.');
      await restore(JSON.parse(await file.text()));
      notice = 'Exploration restaurée.';
    } catch (e) {
      error = e.message;
    }
    e.target.value = '';
  }
  async function share() {
    try {
      const bytes = new TextEncoder().encode(JSON.stringify(state()));
      const value = btoa(String.fromCharCode(...bytes));
      if (value.length > 12000)
        throw Error('Exploration trop longue pour un lien. Utilisez Exporter.');
      const url = location.origin + location.pathname + '#exploration=' + encodeURIComponent(value);
      await navigator.clipboard.writeText(url);
      notice = 'Lien copié. Le Kristal sélectionné est conservé dans l’exploration.';
    } catch (e) {
      error = e.message;
    }
  }
  async function editQuery() {
    try {
      const next = JSON.parse(jsonInput);
      const s = state();
      s.query = next;
      await api('validate-state', s);
      await commit(next);
      notice = 'Requête validée et exécutée.';
    } catch (e) {
      error = e.message;
    }
  }
  function filterSummary(f) {
    const r = relation(f.relation)?.label.fr || f.relation;
    if (f.interval) return `${r} : ${f.interval.from}–${f.interval.to}`;
    if (f.values)
      return `${r} ${f.op === 'none_of' ? 'exclut' : ':'} ${f.values.map((v) => labelMap[v.id] || v.value || v.id).join(', ')}`;
    return r + ' · ' + (f.op === 'exists' ? 'renseigné' : 'absent de la vue');
  }
  function humanValue(a) {
    if (relation(a.relation)?.valueKind === 'interval') {
      const v = a.value;
      return `${v.startMin ?? '?'}–${v.endMax ?? '?'}`;
    }
    return labelMap[a.value] || String(a.value);
  }
  const scopeLabels = { domain: 'Domaine', subdomain: 'Sous-domaine', language: 'Langue', time_window: 'Période documentaire' };
  function qualifierLabel(q) {
    return q?.predicate?.label || q?.predicate?.external_id || 'Qualificatif';
  }
  function qualifierValue(q) {
    const value = q?.object?.value;
    if (value && typeof value === 'object') return value.label || value.external_id || value.id || JSON.stringify(value);
    return String(value ?? '—').replaceAll('_', ' ');
  }
  function pick(id) {
    selectedIds = selectedIds.includes(id)
      ? selectedIds.filter((x) => x !== id)
      : [...selectedIds, id];
  }
  function errorGuard(fn) {
    return async (...args) => {
      try {
        await fn(...args);
      } catch (e) {
        error = e.message;
      }
    };
  }
  onMount(() => {
    let alive = true;
    (async () => {
      try {
        authToken = sessionStorage.getItem('konstellation.auth.token') || '';
        const collection = await api('kristals');
        kristalSelectable = Boolean(collection.selectable);
        kristals = Array.isArray(collection.items) ? collection.items : [];
        if (kristalSelectable) {
          let remembered = '';
          try { remembered = localStorage.getItem('konstellation.kristal.v1') || ''; } catch {}
          kristal = kristals.some((item) => item.id === remembered && item.available)
            ? remembered
            : collection.current || collection.defaultKristal || kristals.find((item) => item.available)?.id || '';
        }
        boot = await api('bootstrap');
        if (!alive) return;
        initializeExploration(boot);
        try {
          const v = JSON.parse(localStorage.getItem('konstellation.saved.v1') || '[]');
          saved = Array.isArray(v)
            ? v.filter((x) => typeof x.name === 'string' && x.state).slice(0, 40)
            : [];
        } catch {
          saved = [];
        }
        if (location.hash.startsWith('#exploration=')) {
          try {
            const encoded = decodeURIComponent(location.hash.slice(13));
            if (encoded.length > 16000) throw Error('Lien trop long.');
            const data = JSON.parse(
              new TextDecoder().decode(Uint8Array.from(atob(encoded), (c) => c.charCodeAt(0))),
            );
            await restore(data, false);
          } catch (e) {
            const message = 'Lien non restauré : ' + e.message;
            await run();
            error = message;
          }
        } else await run();
      } catch (e) {
        authRequired = e.status === 401;
        error = authRequired ? '' : e.message;
        busy = false;
      }
    })();
    return () => {
      alive = false;
      queryController?.abort();
      detailController?.abort();
      navigationController?.abort();
    };
  });
</script>

<svelte:head><title>Konstellation — Explorer les idées</title></svelte:head>
<div class="app-shell">
  <header class="topbar">
    <a href="/" class="brand">
      <img src="/brand-logo.svg" alt="" class="brand-logo" aria-hidden="true" />
      <span>Konstellation<small>DES ÉTOILES POUR S’ORIENTER</small></span>
    </a>
    <nav aria-label="Navigation principale">
      <a class="active" href="/">Explorer</a><a href="#astrolabe">Astrolabe</a><button
        class:active={showSaved}
        on:click={() => (showSaved = !showSaved)}
        >Mes explorations <span class="nav-count">{saved.length}</span></button
      ><button on:click={() => (showSource = !showSource)}>À propos du corpus</button>
    </nav>
    <span class="local-indicator"><i></i> {boot?.principal?.id || 'Espace local'}</span>
  </header>
  {#if !boot || !query}<main class="loading-screen">
      <div class="brand-mark"><img src="/brand-logo.svg" alt="Konstellation" class="loading-logo" /></div>
      <h1>Ouvrir de nouvelles perspectives.</h1>
      {#if authRequired}
        <p>Cette instance Konstellation requiert une authentification.</p>
        <form class="auth-form" on:submit|preventDefault={() => { sessionStorage.setItem('konstellation.auth.token', authToken.trim()); location.reload(); }}>
          <label>Jeton d’accès<input type="password" bind:value={authToken} autocomplete="current-password" required /></label>
          <button class="button primary" type="submit">Ouvrir Konstellation</button>
        </form>
      {:else}
        <p>{error || 'Chargement du corpus et des relations…'}</p>
        {#if error}<button on:click={() => location.reload()}>Réessayer</button>{/if}
      {/if}
    </main>
  {:else}
    <main>
      <section class="intro">
        <div>
          <div class="eyebrow">EXPLORATEUR DE CONNAISSANCES <span> / </span> {boot.title}</div>
          <h1>Explorez la structure des connaissances<span>.</span></h1>
          <p>Konstellation détecte les formes du Kristal et propose les parcours, vues et comparaisons les plus pertinents.</p>
        </div>
        <div class="intro-actions">
          <button class="button subtle-button" on:click={share}>↗ Partager</button><button
            class="button primary"
            on:click={() => (showSaved = true)}>＋ Enregistrer</button
          >
        </div>
      </section>
      <Astrolabe entities={boot.entities} corpusTitle={boot.title} onNavigate={errorGuard(navigateFromAstrolabe)} />
      {#if boot.synthetic}<div class="demo-banner">
          <span class="tiny-star">✦</span><strong>Corpus de démonstration</strong><span
            >Notices illustratives et relations synthétiques. Aucune validation historique
            revendiquée.</span
          >
        </div>{/if}
      {#if error}<div role="alert" class="alert error">
          <span>{error}</span><button aria-label="Fermer l’erreur" on:click={() => (error = '')}
            >×</button
          >
        </div>{/if}
      {#if notice}<div role="status" class="alert notice">
          <span>{notice}</span><button
            aria-label="Fermer la notification"
            on:click={() => (notice = '')}>×</button
          >
        </div>{/if}
      {#if showSource}<section class="utility-panel">
          <div>
            <h2>Un corpus, des perspectives</h2>
            <p>{boot.description}</p>
            <p>
              Les résultats respectent la politique de lecture choisie. Une assertion sourcée n’est
              pas automatiquement validée. Les sources et statuts restent inspectables.
            </p>
            <p>
              Adaptateur : {boot.capabilities.packAdapter}. Communication : {boot.communication
                ?.available
                ? 'service disponible'
                : boot.communication?.reason || 'non configurée'}.
              {#each boot.policies.filter((p) => p.available === false) as p}<br />{p.label} : {p.reasons.join(
                  ' ',
                )}{/each}
            </p>
          </div>
          <button
            class="close"
            aria-label="Fermer les informations"
            on:click={() => (showSource = false)}>×</button
          >
        </section>{/if}
      {#if showSaved}<section class="utility-panel saved-panel">
          <div class="saved-header">
            <h2>Mes explorations</h2>
            <p>Enregistrées sur cet appareil. Exportez un fichier pour les conserver ailleurs.</p>
            <div class="save-form">
              <input
                aria-label="Nom de l’exploration"
                placeholder="Donnez un nom à ce parcours"
                bind:value={saveName}
              /><button class="button primary" on:click={remember}>Enregistrer ici</button><button
                class="button"
                on:click={download}>Exporter JSON</button
              ><button class="button" on:click={() => importInput.click()}>Importer</button><input
                hidden
                type="file"
                accept=".json,application/json"
                bind:this={importInput}
                on:change={importFile}
              />
            </div>
          </div>
          <button
            class="close"
            aria-label="Fermer les explorations"
            on:click={() => (showSaved = false)}>×</button
          >
          <div class="saved-list">
            {#each saved as item}<div>
                <button on:click={errorGuard(() => restore(item.state))}
                  >{item.name}<small
                    >{typeLabel(item.state.query?.selection?.entityType) || 'Exploration'}</small
                  ></button
                ><button aria-label={'Supprimer ' + item.name} on:click={() => removeSaved(item.id)}
                  >×</button
                >
              </div>{:else}<p class="subtle">Vos prochaines pistes commencent ici.</p>{/each}
          </div>
        </section>{/if}
      <section class="context-bar" aria-label="Contexte de lecture">
        {#if kristalSelectable}<label
          ><span class="context-icon">✦</span><span
            ><small>KRISTAL</small><select
              aria-label="Kristal"
              value={kristal}
              disabled={switchingKristal || busy}
              on:change={(e) => changeKristal(e.target.value)}
              >{#each kristals as item}<option value={item.id} disabled={!item.available}
                  >{item.label}{item.available ? '' : ' — indisponible'}</option
                >{/each}</select
            ></span
          ></label
        >{/if}<label
          ><span class="context-icon">◈</span><span
            ><small>PERSPECTIVE</small><select
              aria-label="Perspective"
              value={lensId}
              on:change={(e) => changeLens(e.target.value)}
              >{#if !boot.lenses.some((l) => l.id === lensId)}<option value={lensId}
                  >{typeLabel(query.selection.entityType)}</option
                >{/if}{#each boot.lenses as l}<option value={l.id}>{l.label.fr}</option
                >{/each}</select
            ></span
          ></label
        ><label
          ><span class="context-icon">◉</span><span
            ><small>POLITIQUE DE LECTURE</small><select
              aria-label="Politique de lecture"
              value={query.context.readerPolicyRef}
              on:change={(e) => changePolicy(e.target.value)}
              >{#each boot.policies as p}<option value={p.ref} disabled={p.available === false}
                  >{p.label}{p.available === false ? ' — indisponible' : ''}</option
                >{/each}</select
            ></span
          ></label
        >
        <div class="context-end">
          <span>{boot.entities.length} entités au catalogue</span><span class="version-pill"
            >CORPUS ÉPINGLÉ</span
          >
        </div>
      </section>
      <Communication
        {query}
        cursor={currentCursor}
        entityId={selected}
        capabilities={boot.communication}
        disabled={busy || !!error}
        {authToken}
        {kristal}
      />
      <div class="workspace">
        <aside class="filters-panel" aria-label="Filtres">
          <div class="panel-heading">
            <h2>Affiner la sélection</h2>
            <button
              class="text-button"
              on:click={() => {
                const next = clone(query);
                next.selection = { entityType: query.selection.entityType, filters: [], links: [] };
                commit(next);
              }}>Réinitialiser</button
            >
          </div>
          <p class="panel-caption">Les facettes viennent de votre perspective.</p>
          {#each currentFacets as facet}
            {@const r = relation(facet.relation)}{@const f = filterFor(
              facet.relation,
            )}{@const data = facets[facet.relation]}
            <section class="facet">
              <div class="facet-title">
                <h3>{r.label.fr}</h3>
                {#if f}<button
                    class="clear-facet"
                    aria-label={'Effacer ' + r.label.fr}
                    on:click={() => setFilter(r.id, null)}>×</button
                  >{:else}<span>⌄</span>{/if}
              </div>
              {#if boot.capabilities?.relations?.[r.id]?.available === false}<p class="hint">
                  {boot.capabilities.relations[r.id].reason}
                </p>
              {:else if r.valueKind === 'interval'}<p class="hint">
                  Période de vie · chevauchement certain
                </p>
                <div class="year-inputs">
                  <label
                    >De<input
                      type="number"
                      aria-label="Année de début"
                      bind:value={epochFrom}
                      placeholder="300"
                    /></label
                  ><span>—</span><label
                    >À<input
                      type="number"
                      aria-label="Année de fin"
                      bind:value={epochTo}
                      placeholder="500"
                    /></label
                  >
                </div>
                <button class="apply-period" on:click={() => applyYears(r.id)}
                  >Appliquer la période →</button
                >
              {:else}<select
                  class="operator"
                  aria-label={'Opérateur ' + r.label.fr}
                  value={f?.op || ''}
                  on:change={(e) => changeOperator(r.id, e.target.value)}
                  ><option value="">Toutes les valeurs</option
                  >{#if r.operators.includes('in')}<option value="in"
                      >Correspond à une valeur</option
                    ><option value="none_of">Exclut ces valeurs</option>{/if}<option value="exists"
                    >Relation renseignée</option
                  ><option value="missing_in_view">Absente de cette vue</option></select
                >
                <div class="facet-values">
                  {#each data?.values?.slice(0, 100) || [] as option}{@const checked =
                      f?.values?.some((v) => (v.id ?? v.value) === option.value)}<label
                      class:checked
                      ><input
                        type="checkbox"
                        {checked}
                        on:change={() => toggleValue(r.id, option.value)}
                      /><span>{labelMap[option.value] || option.value}</span><small
                        >{option.count}</small
                      ></label
                    >{:else}<p class="hint">
                      {busy ? 'Calcul des facettes…' : 'Aucune valeur dans la sélection.'}
                    </p>{/each}
                </div>
              {/if}
              {#if data?.available}<div class="facet-footer">
                  <span>{data.present} renseignés</span><span>{data.missing} absents de la vue</span
                  >
                </div>{/if}
            </section>
          {/each}
          <div class="filter-note">
            <span>◎</span>
            <p>
              Un filtre absent de la perspective reste actif et visible au-dessus des résultats.
            </p>
          </div>
        </aside>
        <section class="results-panel" aria-label="Résultats">
          <div class="journey-toolbar">
            <div class="history-controls">
              <button
                aria-label="Revenir"
                disabled={!history.length || busy}
                on:click={errorGuard(undo)}>←</button
              ><button
                aria-label="Rétablir"
                disabled={!future.length || busy}
                on:click={errorGuard(redo)}>→</button
              >
            </div>
            <div class="breadcrumb">
              <span>Explorer</span><span>/</span><strong
                >{typeLabel(query.selection.entityType) || query.selection.entityType}</strong
              >{#if query.selection.links.length}<span class="pivot-tag"
                  >via {query.selection.links.length} relation</span
                >{/if}
            </div>
            <button
              class="text-button"
              on:click={() => {
                showQuery = !showQuery;
                jsonInput = JSON.stringify(query, null, 2);
              }}>{showQuery ? 'Masquer' : 'Voir'} la requête ↗</button
            >
          </div>
          {#if showQuery}<div class="query-panel">
              <div class="eyebrow">VOTRE PARCOURS</div>
              <QueryTree selection={query.selection} registry={relations} labels={labelMap} />
              <details>
                <summary>QuerySpec · inspecter ou modifier</summary><textarea
                  aria-label="QuerySpec JSON"
                  value={jsonInput || JSON.stringify(query, null, 2)}
                  on:input={(e) => (jsonInput = e.target.value)}
                  spellcheck="false"></textarea><button class="button" on:click={editQuery}
                  >Valider et exécuter</button
                >
              </details>
            </div>{/if}
          {#if activeCount}<div class="active-filters">
              {#if query.selection.ids}<span class="filter-chip"
                  >{query.selection.ids.length} identités sélectionnées</span
                >{/if}{#each query.selection.filters as f}<button
                  class="filter-chip"
                  on:click={() => setFilter(f.relation, null)}
                  >{filterSummary(f)} <span>×</span></button
                >{/each}{#each query.selection.links as link}<span class="filter-chip linked"
                  >↳ {relation(link.relation)?.label.fr} satisfait la sélection précédente</span
                >{/each}
            </div>{/if}
          {#if omitted.length}<p class="hidden-filters-note">
              {omitted.length} critère(s) actif(s) proviennent d’une autre perspective.
            </p>{/if}
          <div class="results-heading">
            <div>
              <div class="eyebrow">
                {query.selection.links.length ? 'UN NOUVEAU POINT DE VUE' : 'VOTRE SÉLECTION'}
              </div>
              <h2>
                {typeLabel(query.selection.entityType) || query.selection.entityType}<span
                  class="result-count">{result?.total.value ?? '—'}</span
                >
              </h2>
              <p>{busy ? 'Mise à jour de la sélection…' : policy?.description}</p>
            </div>
            <div class="view-switch adaptive-switch" aria-label="Affichage">
              {#if navigationPlan?.views?.length}
                {#each navigationPlan.views as item}
                  <button
                    class:active={navigationRecipe === item.id}
                    class:recommended={navigationPlan.primaryRecipeId === item.id && navigationRecipe !== item.id}
                    aria-pressed={navigationRecipe === item.id}
                    title={item.reason || item.description}
                    on:click={() => applyNavigationRecipe(item, true)}>{item.icon} <span>{item.label}</span></button
                  >
                {/each}
              {:else}
                <button class:active={view === 'list'} aria-pressed={view === 'list'} on:click={() => (view = 'list')}>▤ <span>Liste</span></button>
                <button class:active={view === 'table'} aria-pressed={view === 'table'} on:click={() => (view = 'table')}>▦ <span>Tableau</span></button>
                <button class:active={view === 'constellation' || view === 'graph'} aria-pressed={view === 'constellation' || view === 'graph'} on:click={openConstellation}>◈ <span>Constellation</span></button>
              {/if}
            </div>
          </div>
          {#if navigationPlan}
            <div class="navigation-signals" aria-label="Affordances structurelles détectées">
              <span class="navigation-mode">✦ Navigation adaptative · affordances</span>
              {#each navigationCapabilities as capability}
                <span class="capability-chip" title={(capability[1].evidence || []).join(' · ')}>{capabilityLabel(capability[0])}</span>
              {/each}
              {#if currentNavigationView?.reason}<small>{currentNavigationView.reason}</small>{/if}
            </div>
          {/if}
          <div class="results-actions">
            <label class="search-input"
              ><span>⌕</span><input
                aria-label="Chercher dans le corpus"
                bind:value={search}
                placeholder="Chercher dans le corpus…"
                autocomplete="off"
              /></label
            ><select
              aria-label="Explorer une relation"
              value=""
              on:change={(e) => {
                if (e.target.value) pivot(e.target.value, selectedIds.length ? selectedIds : null);
              }}
              ><option value=""
                >Explorer {selectedIds.length
                  ? selectedIds.length + ' sélectionnés'
                  : 'toute la sélection'} →</option
              >{#each pivots.filter((r) => r.inverseOf) as r}<option value={r.id}
                  >{r.label.fr}</option
                >{/each}</select
            >
          </div>
          {#if search.trim()}
            <div class="catalog-search-results" aria-live="polite">
              <div class="catalog-search-head">
                <strong>Dans tout le corpus</strong>
                <span>{catalogMatchTotal} résultat{catalogMatchTotal > 1 ? 's' : ''}</span>
              </div>
              {#if catalogMatches.length}
                <div class="catalog-search-grid">
                  {#each catalogMatches as item}
                    <button on:click={() => { search = ''; navigateFromAstrolabe(item.entity); }}>
                      <small>{entityTypeLabel(item.entity)}</small>
                      <strong>{displayEntityLabel(item.entity)}</strong>
                      {#if item.entity.description}<span>{item.entity.description}</span>{/if}
                    </button>
                  {/each}
                </div>
              {:else}
                <p>Aucune entité du corpus ne correspond à « {search} ».</p>
              {/if}
            </div>
          {/if}
          {#if selectedIds.length}<div class="selection-bar">
              {selectedIds.length} entités cochées
              <button on:click={() => (selectedIds = [])}>Tout désélectionner</button>
            </div>{/if}
          <div class="results-body" aria-busy={busy}>
            {#if !result && !busy}<div class="empty-state">
                <span>◎</span>
                <h3>La sélection n’a pas pu être évaluée.</h3>
                <p>Corrigez la requête ou restaurez un contexte disponible.</p>
              </div>
            {:else if result && rows.length === 0}<div class="empty-state">
                <span>◌</span>
                <h3>Aucune correspondance dans cette vue.</h3>
                <p>Essayez d’élargir un filtre ou de changer la politique de lecture.</p>
              </div>
            {:else if view === 'adaptive' && currentNavigationView}<AdaptiveProjectionView
                {query}
                lensRef={lensId}
                recipe={currentNavigationView}
                selectedEntityId={selected}
                inspect={(id) => inspect(id)}
                fallback={fallbackAdaptive}
                {authToken}
                {kristal}
              />
            {:else if view === 'constellation' || view === 'graph'}<ConstellationView
                {rows}
                labels={labelMap}
                rootLabel={typeLabel(query.selection.entityType) || query.selection.entityType}
                context={query.context}
                lensRef={lensId}
                bind:path={constellationPath}
                bind:limit={satelliteLimit}
                inspect={(id) => inspect(id)}
                {authToken}
                {kristal}
              />
            {:else if view === 'table'}<div class="table-wrap">
                <table>
                  <thead
                    ><tr
                      ><th>Entité</th><th>Type</th><th>Témoins de filtre</th><th>Inspecter</th></tr
                    ></thead
                  ><tbody
                    >{#each rows as row}<tr class:selected={selected === row.entityId}
                        ><td>{labelMap[row.entityId]}</td><td
                          >{typeLabel(query.selection.entityType)}</td
                        ><td>{row.witnesses.length}</td><td
                          ><button class="text-button" on:click={() => inspect(row.entityId)}
                            >Sources →</button
                          ></td
                        ></tr
                      >{/each}</tbody
                  >
                </table>
              </div>
            {:else}<div class="entity-list">
                {#each rows as row, i}{@const entity = entityMap[row.entityId]}
                  <article class:selected={selected === row.entityId}>
                    <label class="row-checkbox"
                      ><input
                        type="checkbox"
                        aria-label={'Sélectionner ' + (labelMap[row.entityId] || entity?.label)}
                        checked={selectedIds.includes(row.entityId)}
                        on:change={() => pick(row.entityId)}
                      /></label
                    ><button class="entity-main" on:click={() => inspect(row.entityId)}
                      ><span class={'entity-avatar avatar-' + (i % 4)}
                        >{entity?.label
                          ?.split(' ')
                          .map((x) => x[0])
                          .slice(0, 2)
                          .join('')}</span
                      ><span class="entity-copy"
                        ><strong>{labelMap[row.entityId] || entity?.label || row.entityId}</strong><small
                          >{entity?.description || typeLabel(entity?.type)}</small
                        ></span
                      ></button
                    >
                    <div class="entity-meta">
                      <span
                        >{row.witnesses.length
                          ? row.witnesses.length + ' témoin' + (row.witnesses.length > 1 ? 's' : '')
                          : 'Dans le catalogue'}</span
                      ><button
                        aria-label={'Inspecter ' + (labelMap[row.entityId] || entity?.label)}
                        on:click={() => inspect(row.entityId)}>↗</button
                      >
                    </div>
                  </article>{/each}
              </div>{/if}
          </div>
          <footer class="results-footer">
            <span
              >{rows.length} affichés sur {result?.total.value ?? '—'} · ordre stable par identifiant</span
            >
            <div>
              <button
                class="text-button"
                disabled={busy}
                on:click={() => {
                  selectedIds = [];
                  run();
                }}>Première page</button
              ><button
                class="button"
                disabled={!result?.nextCursor || busy}
                on:click={() => {
                  selectedIds = [];
                  run(result.nextCursor);
                }}>Suivante →</button
              >
            </div>
          </footer>
        </section>
        {#if selected}<aside class="inspector" aria-label="Inspecteur d’entité">
            <div class="panel-heading">
              <span class="eyebrow">REGARDER DE PLUS PRÈS</span><button
                class="close"
                aria-label="Fermer l’inspecteur"
                on:click={resetDetail}>×</button
              >
            </div>
            <div class="inspector-hero">
              <div class="entity-avatar large">{(labelMap[selected] || '?').slice(0, 1)}</div>
              <h2>{labelMap[selected]}</h2>
              <p>{entityMap[selected]?.description}</p>
            </div>
            {#if detailBusy}<p>Lecture des assertions…</p>{:else if detail}<div
                class="inspector-pivots"
              >
                {#each relations.filter((r) => r.domain.includes(detail.entity.type) && r.inverseOf) as r}<button
                    class="button"
                    on:click={() => pivot(r.id, [selected])}>{r.label.fr} →</button
                  >{/each}
              </div>
              {#if result?.rows.find((r) => r.entityId === selected)?.witnesses.length}<details
                  class="match-proof"
                >
                  <summary>Pourquoi cette correspondance ?</summary
                  >{#each result.rows.find((r) => r.entityId === selected).witnesses as w}<p>
                      <code>{w.criterionPath}</code>
                    </p>
                    {#if w.kind === 'absence_in_view'}<p>
                        Aucune valeur correspondante dans cette vue complètement évaluée.
                      </p>{:else}<p>
                        {w.assertionRefs.length > 1
                          ? `${w.assertionRefs.length} assertions documentées soutiennent cette correspondance.`
                          : 'Une assertion documentée soutient cette correspondance.'}
                      </p>{/if}{/each}
                </details>{/if}
              <h3>Assertions visibles <span>{detail.assertions.length}</span></h3>
              <p class="hint">Chaque statut décrit une assertion, pas la personne entière.</p>
              {#each detail.assertions as a}<div class="assertion-card">
                  <div class="assertion-heading">
                    <span>{relation(a.payload.relation)?.label.fr}</span><span
                      class:disputed={a.payload.status === 'disputed'}
                      class="status-pill">{statusLabels[a.payload.status] || a.payload.status}</span
                    >
                  </div>
                  <strong
                    >{a.payload.subject === selected
                      ? humanValue(a.payload)
                      : labelMap[a.payload.subject]}</strong
                  ><small
                    >Certitude : {a.payload.certainty} · Validation : {a.payload
                      .validationStatus}</small
                  >{#if a.payload.conflictsWith?.length}<p class="conflict-note">
                      Une divergence est présente dans cette vue.
                    </p>{/if}
                  <details>
                    <summary>Provenance et détails</summary>
                    <p>Autorité : {a.payload.authority}</p>
                    {#if a.payload.scope}<dl class="detail-list scope-list">
                        {#each Object.entries(a.payload.scope) as [key, value]}<div><dt>{scopeLabels[key] || key.replaceAll('_', ' ')}</dt><dd>{value}</dd></div>{/each}
                      </dl>{/if}
                    <p>Validée comme : {a.payload.validatedAs}</p>
                    {#if a.payload.recognitionStatus}<p>
                        Reconnaissance : {a.payload.recognitionStatus}
                      </p>{/if}
                    {#if a.payload.artifactStatus}<p>
                        Statut du corpus : {a.payload.artifactStatus}
                      </p>{/if}
                    {#each a.payload.readerLabels || [] as label}<p>{label}</p>{/each}
                    {#if a.payload.qualifiers?.length}<dl class="detail-list qualifier-list">
                        {#each a.payload.qualifiers as qualifier}<div><dt>{qualifierLabel(qualifier)}</dt><dd>{qualifierValue(qualifier)}</dd></div>{/each}
                      </dl>{/if}
                    {#if a.payload.lineage}<p>Lineage : {JSON.stringify(a.payload.lineage)}</p>{/if}
                    {#each a.payload.sourceRefs as sid}<p class="source-ref">
                        ↗ {sourceTitle(sid)}
                      </p>{/each}{#if a.payload.ruleRef && !isOpaqueRef(a.payload.ruleRef)}<p>
                        Dérivation : {a.payload.ruleRef}
                      </p>{/if}
                  </details>
                </div>{:else}<p>Aucune assertion visible sous cette politique.</p>{/each}{/if}
          </aside>{/if}
      </div>
      <footer class="page-footer">
        <span class="footer-brand"><img src="/brand-logo.svg" alt="" aria-hidden="true" />Relier. Comprendre. Explorer.</span><span>Requêtes explicites · Sources préservées · v0.5</span>
      </footer>
    </main>
  {/if}
</div>
