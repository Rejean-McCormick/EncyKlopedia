<script>
  import { normalizeTerm, rankOrientation, readableCode } from '../lib/semantic-display.mjs';
  export let entities = [];
  export let corpusTitle = '';
  export let preferredType = '';
  export let typeLabels = {};
  export let onNavigate = () => {};
  let term = '';

  const normalize = normalizeTerm;
  function humanize(value) { return typeLabels[value] || readableCode(value); }
  $: examples = (() => {
    const preferred = entities.filter(e => e?.type === preferredType && e.label?.length >= 5 && e.label.length <= 42);
    const pool = preferred.length ? preferred : entities.filter(e => e?.label && !['v9_state','v9_artifact'].includes(e.type) && e.label.length <= 42);
    // Diverse deterministic suggestions from the chosen category, never a random technical ID.
    return [...new Map(pool.filter(e=>!/^([PQ]\d+|urn:)/i.test(e.label))
      .map(e=>[normalize(e.label),e.label])).values()].slice(0,5);
  })();
  $: results = rankOrientation(entities, term, 16, preferredType);
  function surprise(){if(!entities.length)return;onNavigate(entities[Math.floor(Math.random()*entities.length)]);}
  function submit(){if(results[0])onNavigate(results[0].entity);}
</script>
<section class="astrolabe" id="astrolabe" data-testid="astrolabe" aria-labelledby="astrolabe-title">
  <div class="astrolabe-orbit" aria-hidden="true"><span class="orbit orbit-one"></span><span class="orbit orbit-two"></span><span class="astrolabe-star">✦</span></div>
  <div class="astrolabe-copy"><div class="eyebrow">ASTROLABE</div><h2 id="astrolabe-title">Donnez un mot. Trouvez un cap.</h2><p>Recherche d’orientation générique dans {corpusTitle || 'le Kristal courant'}. Elle recherche les noms et les alias des éléments disponibles, sans inventer de liens ni d’identités.</p>
    <form class="astrolabe-search" on:submit|preventDefault={submit}><span aria-hidden="true">⌖</span><input aria-label="Orienter l’Astrolabe" bind:value={term} placeholder={examples.length?`Ex. ${examples.slice(0,3).join(', ')}…`:'Chercher dans le Kristal…'} autocomplete="off"/><button class="button primary" type="submit" disabled={!results.length}>Prendre le cap →</button></form>
    <div class="astrolabe-examples" aria-label="Exemples de mots-clés">{#each examples as example}<button class:active={normalize(term)===normalize(example)} on:click={()=>term=example}>{example}</button>{/each}<button class="surprise" on:click={surprise}>✦ Cap au hasard</button></div>
  </div>
  {#if term.trim()}<div class="astrolabe-reading" data-testid="astrolabe-reading" aria-live="polite"><div class="astrolabe-reading-head"><div><small>LECTURE DE L’ASTROLABE</small><strong>{term}</strong></div><span class:direct={results.length} class:empty={!results.length} class="astrolabe-status">{results.length} piste{results.length>1?'s':''} affichée{results.length>1?'s':''}</span></div>
    {#if results.length}<div class="astrolabe-caps" data-testid="astrolabe-caps">{#each results.slice(0,12) as item}<button class="astrolabe-cap" data-entity-id={item.entity.id} data-entity-type={item.entity.type} on:click={()=>onNavigate(item.entity)}><span class="cap-mark" aria-hidden="true">✦</span><span class="cap-copy"><small>Correspondance · {humanize(item.entity.type)}</small><strong>{item.entity.label}</strong>{#if item.entity.description}<em>{item.entity.description}</em>{/if}</span><span class="cap-arrow" aria-hidden="true">→</span></button>{/each}</div>{:else}<p class="astrolabe-note">Aucun ancrage net dans le vocabulaire visible de ce Kristal.</p>{/if}
  </div>{/if}
</section>
