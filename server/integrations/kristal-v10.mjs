// Kristal v10 GitHub collection reader. Purely derived operational navigation.
// No code execution, host-identity promotion, or semantic assertion synthesis.
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fail } from '../errors.mjs';

const FORMATS = Object.freeze({
  index: 'kristal.github-collection-index/1.0',
  sync: 'kristal.github-sync-manifest/1.0',
});
const DIGEST = /^sha256:[0-9a-f]{64}$/;
const sha = (bytes) => 'sha256:' + createHash('sha256').update(bytes).digest('hex');
const isObject = (x) => x !== null && typeof x === 'object' && !Array.isArray(x);
const utf8Compare = (a, b) => Buffer.compare(Buffer.from(a, 'utf8'), Buffer.from(b, 'utf8'));
const compareCodePoint = (a, b) => {
  const aa = Array.from(a, (c) => c.codePointAt(0));
  const bb = Array.from(b, (c) => c.codePointAt(0));
  for (let i = 0; i < Math.min(aa.length, bb.length); i++) if (aa[i] !== bb[i]) return aa[i] - bb[i];
  return aa.length - bb.length;
};
function stableJson(x) {
  if (x === null || typeof x === 'boolean' || typeof x === 'string') return JSON.stringify(x);
  if (typeof x === 'number' && Number.isFinite(x)) return JSON.stringify(x);
  if (Array.isArray(x)) return '[' + x.map(stableJson).join(',') + ']';
  if (isObject(x)) return '{' + Object.keys(x).sort(compareCodePoint).map((k) => JSON.stringify(k) + ':' + stableJson(x[k])).join(',') + '}';
  fail('V10_CONTRACT_INVALID', 'Valeur non représentable dans le canon JSON v10.', 422);
}
const hashJson = (x) => sha(Buffer.from(stableJson(x), 'utf8'));
function requireValid(condition, label) {
  if (!condition) fail('V10_CONTRACT_INVALID', label, 422);
}
function safeRel(value) {
  return typeof value === 'string' && value.length > 0 && !value.includes('\\') &&
    !value.includes(':') && !path.posix.isAbsolute(value) &&
    value.split('/').every((part) => part !== '' && part !== '.' && part !== '..');
}
function safeSlug(value) {
  return typeof value === 'string' && /^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(value) &&
    value !== '.' && value !== '..';
}
function safePath(root, relative, { file = true } = {}) {
  requireValid(safeRel(relative), 'Chemin relatif v10 dangereux.');
  let current = fs.realpathSync(root);
  for (const part of relative.split('/')) {
    current = path.join(current, part);
    let stat;
    try { stat = fs.lstatSync(current); }
    catch { fail('V10_FILE_MISSING', `Fichier v10 absent : ${relative}`, 422); }
    requireValid(!stat.isSymbolicLink(), `Lien symbolique interdit : ${relative}`);
  }
  const stat = fs.statSync(current);
  requireValid(file ? stat.isFile() : stat.isDirectory(), `Type de ressource v10 incorrect : ${relative}`);
  return current;
}
function jsonAt(root, rel, max = 8 * 1024 * 1024) {
  const file = safePath(root, rel);
  requireValid(fs.statSync(file).size <= max, `Document v10 trop volumineux : ${rel}`);
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch { fail('V10_CONTRACT_INVALID', `JSON invalide : ${rel}`, 422); }
}
const commitmentOk = (c) => isObject(c) && c.profile === 'kristal.state-commitment/jcs-sha256-v1' && DIGEST.test(c.digest);
const sameCommitment = (a, b) => commitmentOk(a) && commitmentOk(b) && a.profile === b.profile && a.digest === b.digest;
function sortedUniqueFiles(rows) {
  requireValid(Array.isArray(rows) && rows.length > 0, 'Liste v10 de fichiers absente.');
  let last = '';
  const items = new Map();
  for (const row of rows) {
    requireValid(isObject(row) && safeRel(row.path) && typeof row.role === 'string' && row.role.length > 0 &&
      Number.isSafeInteger(row.size) && row.size >= 0 && DIGEST.test(row.sha256), 'Fichier de manifeste v10 invalide.');
    requireValid(!last || utf8Compare(last, row.path) < 0, 'Chemins v10 non triés ou dupliqués.');
    last = row.path;
    items.set(row.path, row);
  }
  return items;
}
export function verifyCollectionIndex(index) {
  requireValid(isObject(index) && index.format === FORMATS.index && Array.isArray(index.kristals), 'Index GitHub v10 invalide.');
  requireValid(index.count === index.kristals.length && DIGEST.test(index.index_digest), 'Compteurs/digest de l’index v10 invalides.');
  const seen = new Set(), refs = new Set(); let last = null;
  for (const row of index.kristals) {
    requireValid(isObject(row) && safeSlug(row.slug) && row.path === `kristals/${row.slug}` &&
      row.entrypoint === `${row.path}/AI_START_HERE.md` && typeof row.title === 'string' && row.title.length > 0 &&
      typeof row.state_ref === 'string' && row.state_ref.length > 0 && sameCommitment(row.state_logical_commitment, row.state_logical_commitment) &&
      DIGEST.test(row.surface_digest) && ['file_count', 'total_bytes', 'materialization_object_count'].every((k) => Number.isSafeInteger(row[k]) && row[k] >= 0),
      'Entrée d’index v10 invalide.');
    requireValid(!seen.has(row.slug) && (last === null || utf8Compare(last, row.slug) < 0), 'Index v10 non trié ou dupliqué.');
    requireValid(!refs.has(row.state_ref), 'state_ref dupliqué dans la collection v10.');
    seen.add(row.slug); refs.add(row.state_ref); last = row.slug;
  }
  requireValid(hashJson({ format: index.format, kristals: index.kristals }) === index.index_digest,
    'Empreinte de l’index GitHub v10 incorrecte.');
  return index;
}
export function listGithubKristals(config, base) {
  const root = path.resolve(base, config.directory || '.');
  const index = verifyCollectionIndex(jsonAt(root, 'kristals/index.json'));
  return index.kristals.map((row) => ({
    id: row.slug, label: row.title, available: true, domainDirectory: row.path,
    stateRef: row.state_ref, stateCommitment: row.state_logical_commitment.digest,
  }));
}
function verifyManifest(sync, slug, expectedIndexEntry) {
  requireValid(isObject(sync) && sync.format === FORMATS.sync && sync.slug === slug &&
    sync.target_root === `kristals/${slug}` && sync.entrypoint === 'AI_START_HERE.md' &&
    typeof sync.state_ref === 'string' && sync.state_ref.length > 0 && commitmentOk(sync.state_logical_commitment) &&
    DIGEST.test(sync.surface_digest) && isObject(sync.policy) &&
    ['derived_read_surface', 'sync_is_not_publication', 'activation_is_separate', 'materialization_blobs_are_not_implicitly_copied'].every((k) => sync.policy[k] === true),
    'Manifeste de synchronisation v10 invalide.');
  const files = sortedUniqueFiles(sync.files);
  requireValid(sync.file_count === files.size && sync.total_bytes === [...files.values()].reduce((n, r) => n + r.size, 0) &&
    Number.isSafeInteger(sync.materialization_object_count) && sync.materialization_object_count >= 0,
    'Statistiques des fichiers v10 incohérentes.');
  requireValid(!files.has('.kristal/sync-manifest.json'), 'Le manifeste de synchronisation ne peut pas être auto-référencé.');
  for (const needed of ['AI_MANIFEST.json', 'AI_START_HERE.md', 'ai/INDEX.json', 'state/state-snapshot.json'])
    requireValid(files.has(needed), `Ressource v10 requise absente du manifeste : ${needed}`);
  if (expectedIndexEntry) requireValid(expectedIndexEntry.state_ref === sync.state_ref &&
    sameCommitment(expectedIndexEntry.state_logical_commitment, sync.state_logical_commitment) &&
    expectedIndexEntry.surface_digest === sync.surface_digest && expectedIndexEntry.file_count === sync.file_count &&
    expectedIndexEntry.total_bytes === sync.total_bytes && expectedIndexEntry.materialization_object_count === sync.materialization_object_count,
    'Index GitHub et manifeste v10 divergents.');
  return files;
}
function verifyFiles(root, prefix, entries, maxFiles, maxBytes) {
  requireValid(entries.size <= maxFiles, 'Nombre de fichiers v10 au-delà du budget.');
  let consumed = 0;
  for (const [rel, entry] of entries) {
    const file = safePath(root, `${prefix}/${rel}`);
    const size = fs.statSync(file).size;
    requireValid(size === entry.size, `Taille incorrecte : ${rel}`);
    consumed += size;
    requireValid(consumed <= maxBytes, 'Budget de lecture v10 dépassé.');
    requireValid(sha(fs.readFileSync(file)) === entry.sha256, `Empreinte SHA-256 incorrecte : ${rel}`);
  }
  // Exact manager-owned subtree: undeclared files and symlinks are rejected.
  const allowed = new Set([...entries.keys(), '.kristal/sync-manifest.json']);
  function walk(dir, rel = '') {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const child = rel ? `${rel}/${e.name}` : e.name;
      const stat = fs.lstatSync(path.join(dir, e.name));
      requireValid(!stat.isSymbolicLink(), `Symlink non déclaré : ${child}`);
      if (stat.isDirectory()) walk(path.join(dir, e.name), child);
      else requireValid(stat.isFile() && allowed.has(child), `Fichier v10 non déclaré : ${child}`);
    }
  }
  walk(safePath(root, prefix, { file: false }));
}
function projectionDigest(sync, index) {
  return hashJson({
    format: 'kristal.github-read-surface/1.0', slug: sync.slug,
    state_ref: sync.state_ref, state_logical_commitment: sync.state_logical_commitment,
    entrypoint: sync.entrypoint,
    files: sync.files.map((row) => ({ path: row.path, role: row.role, size: row.size, sha256: row.sha256 })),
    materialization_objects: index.materialization_blobs || [],
  });
}
export function inspectGithubKristal(config, base) {
  const root = path.resolve(base, config.directory || '.');
  const slug = config.kristal;
  requireValid(safeSlug(slug), 'Slug Kristal v10 requis.');
  const collection = verifyCollectionIndex(jsonAt(root, 'kristals/index.json'));
  const row = collection.kristals.find((x) => x.slug === slug);
  requireValid(row, `Kristal absent de l'index : ${slug}`);
  const prefix = `kristals/${slug}`;
  const sync = jsonAt(root, `${prefix}/.kristal/sync-manifest.json`);
  const files = verifyManifest(sync, slug, row);
  const maxFiles = config.maxFiles ?? 4096;
  const maxBytes = config.maxBytes ?? 128 * 1024 * 1024;
  requireValid(Number.isSafeInteger(maxFiles) && maxFiles > 0 && Number.isSafeInteger(maxBytes) && maxBytes > 0,
    'Budgets v10 invalides.');
  verifyFiles(root, prefix, files, maxFiles, maxBytes);
  const aiManifest = jsonAt(root, `${prefix}/AI_MANIFEST.json`);
  const aiIndex = jsonAt(root, `${prefix}/ai/INDEX.json`);
  const state = jsonAt(root, `${prefix}/state/state-snapshot.json`);
  requireValid(aiManifest.format === 'kristal.portable-ai/1.0' && aiIndex.format === 'kristal.ai-index/1.0' &&
    state.artifact_type === 'kristal_state_snapshot' && state.schema_version === '9.0',
    'Profils AI/v9 de la surface non supportés.');
  requireValid(Array.isArray(aiManifest.read_order) &&
    aiManifest.read_order.every((name) => files.has(name)), 'Fichier de lecture AI non déclaré.');
  requireValid(aiManifest.state_snapshot === undefined ||
    aiManifest.state_snapshot === 'state/state-snapshot.json', 'Pointeur State Snapshot AI incohérent.');
  for (const item of [aiManifest, aiIndex]) requireValid(item.state_ref === sync.state_ref &&
    sameCommitment(item.state_logical_commitment, sync.state_logical_commitment), 'État AI v10 incohérent.');
  requireValid(state.state_ref === sync.state_ref && sameCommitment(state.logical_commitment, sync.state_logical_commitment),
    'State Snapshot v9 divergent.');
  requireValid(Array.isArray(state.members) && Array.isArray(state.references) && Array.isArray(aiIndex.files),
    'State Snapshot/Index incomplets.');
  for (const item of aiIndex.files) {
    requireValid(isObject(item) && safeRel(item.path) && files.has(item.path), 'Fichier de l’index AI non déclaré.');
    const declared = files.get(item.path);
    requireValid(item.sha256 === declared.sha256 && item.size === declared.size,
      'Index AI et manifeste de synchronisation divergents.');
  }
  requireValid(Array.isArray(aiIndex.materialization_blobs) &&
    aiIndex.materialization_blobs.length === sync.materialization_object_count,
    'Matérialisations de la surface incohérentes.');
  requireValid(projectionDigest(sync, aiIndex) === sync.surface_digest,
    'Empreinte de la surface v10 incorrecte.');
  return { slug, title: sync.title, sync, state, files: [...files.values()], aiIndex,
    checks: { byteDigestsVerified: true, syncAndIndexConsistent: true, semanticCommitmentVerified: false,
      signaturesVerified: false, publicationVerified: false, activationVerified: false } };
}
const refId = (prefix, value) => `${prefix}:${sha(Buffer.from(value)).slice(7, 31)}`;
export function toNavigationPack(checked, maxMembers = 4096) {
  const { slug, title, sync, state, files } = checked;
  requireValid(Number.isSafeInteger(maxMembers) && maxMembers >= 0 && state.members.length <= maxMembers,
    'Trop de membres v9 pour la projection de navigation.');
  const stateId = refId('state', sync.state_ref);
  const sourceId = refId('source', `${slug}:${sync.surface_digest}`);
  const memberIds = new Set();
  const entities = [{ id: stateId, type: 'hosted_state', label: title || slug,
    description: `Navigation dérivée ; état ${sync.state_ref} ; engagement déclaré ${sync.state_logical_commitment.digest}` }];
  const assertions = [];
  const emit = (relation, value, index) => assertions.push({
    id: `view:${index}`, subject: stateId, relation, value,
    status: 'unspecified', certainty: 'unspecified', validationStatus: 'not_evaluated',
    validatedAs: 'unknown', authority: 'authority:unspecified', scope: { domain: 'hosting' },
    sourceRefs: [sourceId], derivedProjection: true,
  });
  let counter = 0;
  for (const row of state.members) {
    requireValid(isObject(row) && typeof row.artifact_id === 'string' && row.artifact_id &&
      isObject(row.logical_commitment) && DIGEST.test(row.logical_commitment.digest),
      'Membre v9 invalide.');
    const id = refId('artifact', row.artifact_id);
    requireValid(!memberIds.has(id), 'Membre v9 dupliqué.');
    memberIds.add(id);
    entities.push({ id, type: 'logical_artifact', label: row.artifact_id.slice(0, 300),
      description: `Membre déclaré du State Snapshot, engagement ${row.logical_commitment.digest}` });
    emit('has_member', id, ++counter);
  }
  for (const row of files) {
    const id = refId('file', `${slug}/${row.path}`);
    entities.push({ id, type: 'hosted_file', label: row.path.slice(0, 300),
      description: `Fichier dérivé (${row.role}) ; ${row.size} octets ; ${row.sha256}` });
    emit('lists_file', id, ++counter);
  }
  const rel = (id, fr, range) => ({ id, label: { fr, en: fr }, domain: ['hosted_state'],
    range, valueKind: 'entity', operators: ['exists', 'in', 'none_of'] });
  return {
    schemaVersion: '0.3', synthetic: true, title: `Kristal v10 · ${title || slug}`,
    description: 'Vue opérationnelle dérivée et non normative : fichiers hébergés et membres v9 déclarés. Pas une projection sémantique ni une validation épistémique.',
    registry: { schemaVersion: '0.2', registryRef: 'konstellation:kristal-v10-navigation-1',
      entityTypes: ['hosted_state', 'logical_artifact', 'hosted_file'],
      relations: [rel('has_member', 'Membre déclaré', 'logical_artifact'), rel('lists_file', 'Fichier de la surface synchronisée', 'hosted_file')] },
    entities, assertions,
    sources: [{ id: sourceId, title: `Surface synchronisée ${slug}`, description: `SHA-256 ${sync.surface_digest}; navigation seulement` }],
    policies: [{ id: 'view:derived', label: 'Navigation dérivée v10',
      description: 'Affiche uniquement la topologie technique de la surface vérifiée ; aucune autorité sémantique.',
      profile: 'konstellation.normalized-reader.v1', showLabels: true,
      statuses: ['unspecified'], certainties: ['*'], validationStatuses: ['*'],
      validatedAs: ['*'], authorities: ['*'], requireSources: true }],
    integration: { adapter: 'kristal-github-collection-v10', slug, stateRef: sync.state_ref,
      declaredStateCommitment: sync.state_logical_commitment,
      surfaceDigest: sync.surface_digest, checks: checked.checks, viewKind: 'derived-hosting-navigation' },
  };
}
export function loadGithubKristal(config, base) {
  return toNavigationPack(inspectGithubKristal(config, base), config.maxMembers ?? 4096);
}
