// Shared presentation model for Konstellation and Konstellation-Light.
// Never infer attributes from an entity label or fetch third-party portraits.
const FAMILIES = [
  ['person', 'Personne', /^(person|personne|human|author|individual|people|auteur)$/i, '♙'],
  ['place', 'Lieu', /^(place|location|lieu|city|town|country|region|territory|territoire|site|geographic_area)$/i, '⌖'],
  ['organization', 'Organisation', /^(organization|organisation|institution|societe|society)$/i, '▣'],
  ['work', 'Œuvre', /^(work|oeuvre|book|livre|publication)$/i, '▤'],
  ['event', 'Événement', /^(event|evenement|événement)$/i, '◷'],
];
export function profileFamily(kind) {
  return FAMILIES.find(([, , matcher]) => matcher.test(String(kind || ''))) || null;
}
export function hasPortrait(entity) {
  return !!entity && !!profileFamily(entity.type || entity.kind);
}
// The declared image must be a local raster asset. Encoded traversal and off-origin URLs
// are rejected, including percent-encoded backslashes/slashes and query fragments.
export function safePortraitUrl(value) {
  if (typeof value !== 'string' || value.length > 400 || /[\\\x00-\x20?#%]/.test(value)) return null;
  if (!(value.startsWith('/') && !value.startsWith('//')) && !value.startsWith('./')) return null;
  let decoded = value;
  try { for (let i = 0; i < 3; i++) decoded = decodeURIComponent(decoded); } catch { return null; }
  if (/[\\\x00-\x20?#]/.test(decoded) || decoded.startsWith('//') || decoded.includes('//')) return null;
  if (decoded.split('/').some(part => part === '..' || part === '.')) {
    // The leading './' is the only permitted dot path segment.
    if (!(decoded.startsWith('./') && decoded.slice(2).split('/').every(part => part !== '.' && part !== '..'))) return null;
  }
  if (!/\.(?:png|jpe?g|webp|avif|gif)$/i.test(decoded)) return null;
  return value;
}
export function portraitFor(entity, label = entity?.label) {
  const family = profileFamily(entity?.type || entity?.kind);
  if (!family) return null;
  const fields = [];
  const add = (name, value) => {
    if (typeof value === 'string' && value.trim()) fields.push({ name, value: value.trim().slice(0, 500) });
  };
  if (family[0] === 'person') {
    add('Naissance', entity.birthDate || entity.birth_date);
    add('Décès', entity.deathDate || entity.death_date);
    add('Activité', entity.occupation);
  } else if (family[0] === 'place') {
    add('Pays', entity.country);
    add('Région', entity.region);
    add('Coordonnées déclarées', entity.coordinates);
  } else if (family[0] === 'work') {
    add('Auteur / créateur', entity.creator);
    add('Date', entity.date);
  } else if (family[0] === 'event') {
    add('Date', entity.date);
  }
  add('Désambiguïsation', entity.disambiguation);
  add('Période', entity.period);
  add('Localisation', entity.location);
  if (Array.isArray(entity.aliases)) add('Autres noms', entity.aliases.filter(x => typeof x === 'string').slice(0, 6).join(' · '));
  add('Source déclarée', entity.source);
  const title = String(label || entity.label || entity.id || 'Élément').slice(0, 220);
  return {
    family: family[0], typeLabel: family[1], symbol: family[3], title,
    monogram: title.trim().slice(0, 1).toUpperCase() || family[3],
    description: typeof entity.description === 'string' ? entity.description.slice(0, 2000) : '',
    image: safePortraitUrl(entity.portraitUrl || entity.imageUrl || entity.image_url || entity.portrait),
    fields,
  };
}
// Greedy collision-aware placement of an ephemeral second ring. Deterministic and
// bounded: never changes graph entities, edges or navigation state.
export function orbitPreview(items, anchor, width, height, max = 6, obstacles = []) {
  const nodes = Array.isArray(items) ? items.slice(0, Math.max(0, Math.min(6, max))) : [];
  if (!nodes.length || !anchor || !Number.isFinite(anchor.x) || !Number.isFinite(anchor.y)) return [];
  const minX = 70, maxX = Math.max(minX, width - 70);
  const minY = 45, maxY = Math.max(minY, height - 60);
  const placed = [];
  const obstaclesClean = obstacles.filter(p => Number.isFinite(p.x) && Number.isFinite(p.y));
  const distances = (x, y, item) => Math.hypot(x - item.x, y - item.y);
  // Rotate from the outward-facing side to minimize intersections with the main graph.
  const outward = Math.atan2(anchor.y - height / 2, anchor.x - width / 2);
  for (const node of nodes) {
    let choice = null;
    for (const radius of [110, 140, 175, 205, 235]) {
      for (let j = 0; j < 32; j++) {
        const angle = outward + (j % 2 ? -1 : 1) * Math.ceil(j / 2) * Math.PI / 16;
        const x = anchor.x + radius * Math.cos(angle);
        const y = anchor.y + radius * Math.sin(angle);
        if (x < minX || x > maxX || y < minY || y > maxY) continue;
        const otherGap = Math.min(Infinity, ...placed.map(p => distances(x, y, p)));
        const graphGap = Math.min(Infinity, ...obstaclesClean.map(p => distances(x, y, p) - (p.r || 30)));
        const collision = Math.max(0, 94 - otherGap) * 22 + Math.max(0, 49 - graphGap) * 20;
        const radial = Math.abs(radius - 138) * 0.08;
        const score = collision + radial + j * 0.15;
        if (!choice || score < choice.score) choice = { x, y, score };
      }
    }
    if (choice) placed.push({ ...node, x: Math.round(choice.x), y: Math.round(choice.y) });
  }
  return placed;
}
