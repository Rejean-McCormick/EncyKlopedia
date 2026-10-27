<script>
  export let data;
  export let inspect = () => {};
  const WIDTH = 900, HEIGHT = 460, PAD = 44;
  function layout(points) {
    const rows = (points || []).filter((point) => Number.isFinite(point.lat) && Number.isFinite(point.long)).slice(0, 240);
    if (!rows.length) return { points: [], width: WIDTH, height: HEIGHT };
    const lats = rows.map((point) => point.lat), longs = rows.map((point) => point.long);
    const minLat = Math.min(...lats), maxLat = Math.max(...lats), minLong = Math.min(...longs), maxLong = Math.max(...longs);
    const latSpan = Math.max(0.000001, maxLat - minLat), longSpan = Math.max(0.000001, maxLong - minLong);
    return { width: WIDTH, height: HEIGHT, points: rows.map((point) => ({ ...point, x: PAD + ((point.long - minLong) / longSpan) * (WIDTH - PAD * 2), y: HEIGHT - PAD - ((point.lat - minLat) / latSpan) * (HEIGHT - PAD * 2) })), minLat, maxLat, minLong, maxLong };
  }
  $: plot = layout(data.points || []);
  const clip = (text, size = 22) => String(text || '').length > size ? `${String(text).slice(0, size - 1)}…` : String(text || '');
  function open(point) { if (point.entity?.id) inspect(point.entity.id); }
  function keyOpen(event, point) { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(point); } }
</script>

<div class="renderer-stack" data-renderer="spatial">
  {#if plot.points.length}
    <div class="spatial-canvas"><svg viewBox={`0 0 ${plot.width} ${plot.height}`} role="img" aria-label="Distribution spatiale des points visibles">
      {#each [0,1,2,3,4] as step}<line class="spatial-grid" x1={PAD} y1={PAD + step * ((HEIGHT - PAD * 2) / 4)} x2={WIDTH - PAD} y2={PAD + step * ((HEIGHT - PAD * 2) / 4)} /><line class="spatial-grid" x1={PAD + step * ((WIDTH - PAD * 2) / 4)} y1={PAD} x2={PAD + step * ((WIDTH - PAD * 2) / 4)} y2={HEIGHT - PAD} />{/each}
      {#each plot.points as point}<g class="spatial-point" role="button" tabindex="0" aria-label={`Inspecter ${point.label || point.entity?.label || point.entity?.id} · ${point.lat}, ${point.long}`} on:click={() => open(point)} on:keydown={(event) => keyOpen(event, point)}><circle cx={point.x} cy={point.y} r="6"><title>{point.label || point.entity?.label} · {point.lat}, {point.long}</title></circle>{#if plot.points.length <= 40}<text x={point.x + 9} y={point.y + 4}>{clip(point.label || point.entity?.label || '')}</text>{/if}</g>{/each}
      <text class="spatial-axis" x={PAD} y={HEIGHT - 12}>{plot.minLong?.toFixed?.(2)}°</text><text class="spatial-axis" x={WIDTH - PAD} y={HEIGHT - 12} text-anchor="end">{plot.maxLong?.toFixed?.(2)}°</text><text class="spatial-axis" x="8" y={HEIGHT - PAD}>{plot.minLat?.toFixed?.(2)}°</text><text class="spatial-axis" x="8" y={PAD}>{plot.maxLat?.toFixed?.(2)}°</text>
    </svg></div>
  {/if}
  {#if data.places?.length}<details open={!plot.points.length}><summary>Lieux reliés sans coordonnées ({data.places.length})</summary><div class="renderer-stack compact-stack">{#each data.places as row}<div class="renderer-edge"><button on:click={() => inspect(row.entity.id)}>{row.entity.label}</button><span>→</span><button on:click={() => inspect(row.place.id)}>{row.place.label}</button><small>{row.relationLabel}</small></div>{/each}</div></details>{/if}
  {#if !(plot.points.length || data.places?.length)}<p class="empty-renderer">Aucune localisation visible.</p>{/if}
</div>
