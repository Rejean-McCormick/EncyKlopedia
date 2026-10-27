import fs from 'node:fs';
import path from 'node:path';
import { createHash, verify } from 'node:crypto';
import { parquetReadObjects, parquetMetadataAsync } from 'hyparquet';
import { compressors } from 'hyparquet-compressors';
import { readJson, canonical, hash, validatePack } from '../pack.mjs';
import { fail } from '../contracts.mjs';
import { upstream, fetchJson, serviceUrl } from './upstream.mjs';
import { normalizeKristalPolicy } from './reader-policy.mjs';
import { importKristalV6State } from './kristal-v6.mjs';
import { listGithubKristals, loadGithubKristal } from './kristal-v10.mjs';
import { listLocalV10, loadLocalV10 } from './kristal-local-v10.mjs';
import { listLocalCatalog, loadLocalCatalog, loadNeutralCatalog } from './local-catalog.mjs';
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const hex = (x) => String(x || '').replace(/^sha256:/, '');
function safeFile(root, name) {
  if (typeof name !== 'string' || path.isAbsolute(name) || name.split(/[\\/]/).includes('..'))
    fail('PACK_PATH_INVALID', 'Chemin de pack non relatif.', 422);
  const base = fs.realpathSync(root),
    file = fs.realpathSync(path.resolve(base, name));
  if (!file.startsWith(base + path.sep)) fail('PACK_PATH_INVALID', 'Fichier hors du pack.', 422);
  return file;
}
function field(row, key) {
  if (!key) return undefined;
  return key.split('.').reduce((v, k) => v?.[k], row);
}
function toJson(value) {
  if (typeof value === 'bigint') {
    const n = Number(value);
    if (!Number.isSafeInteger(n)) fail('UNSUPPORTED_VALUE', 'Entier hors précision JSON.', 422);
    return n;
  }
  if (Array.isArray(value)) return value.map(toJson);
  if (value && typeof value === 'object')
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, toJson(v)]));
  return value;
}
export function mapRows(rows, layout, catalog, config, manifest) {
  const ids = new Set(catalog.entities.map((e) => e.id));
  const relations = new Map(catalog.registry.relations.map((r) => [r.id, r]));
  const columns = layout.columns;
  const required = [
    'id',
    'subject',
    'relation',
    'value',
    'status',
    'certainty',
    'validationStatus',
    'validatedAs',
    'authority',
    'recognitionStatus',
    'scope',
    'sourceRefs',
  ];
  if (!columns || required.some((k) => typeof columns[k] !== 'string'))
    fail('INVALID_CONFIG', 'Mapping explicite des colonnes épistémiques requis.', 422);
  return rows.map((raw) => {
    const row = toJson(raw),
      a = {};
    for (const [key, col] of Object.entries(columns)) {
      let v = field(row, col);
      if (layout.jsonColumns?.includes(key) && typeof v === 'string') {
        try {
          v = JSON.parse(v);
        } catch {
          fail('PACK_ROW_INVALID', 'Colonne JSON invalide : ' + key, 422);
        }
      }
      if (v !== undefined && v !== null) a[key] = v;
    }
    for (const key of required)
      if (a[key] === undefined) fail('PACK_ROW_INVALID', 'Métadonnée absente : ' + key, 422);
    const originalRelation = a.relation;
    a.relation = config.relationMappings?.[a.relation];
    if (!relations.has(a.relation))
      fail('UNMAPPED_ASSERTION', 'Prédicat non mappé : ' + originalRelation, 422);
    a.subject = config.entityMappings?.[a.subject] || a.subject;
    if (!ids.has(a.subject)) fail('UNMAPPED_ASSERTION', 'Sujet absent du catalogue.', 422);
    if (relations.get(a.relation).valueKind === 'entity') {
      a.value = config.entityMappings?.[a.value] || a.value;
      if (!ids.has(a.value)) fail('UNMAPPED_ASSERTION', 'Objet absent du catalogue.', 422);
    }
    if (a.qualifiers?.length && !layout.qualifiersPreserved)
      fail(
        'UNSUPPORTED_QUALIFIERS',
        'Le mapping doit déclarer la conservation des qualificatifs.',
        422,
      );
    return {
      ...a,
      artifactStatus: manifest.source_artifact_status,
      upstreamContractRef: manifest.query_contract_ref.contract_id,
      upstreamPayload: row,
    };
  });
}
function buildPack(config, catalog, manifest, assertions, policies, metadata) {
  const mapped = [...new Set(Object.values(config.relationMappings || {}))];
  const available = new Set(mapped);
  for (const r of catalog.registry.relations)
    if (r.inverseOf && available.has(r.inverseOf)) available.add(r.id);
  const capabilities = {
    relations: Object.fromEntries(
      catalog.registry.relations.map((r) => [
        r.id,
        {
          available: available.has(r.id),
          operators: available.has(r.id) ? r.operators : [],
          reason: available.has(r.id) ? null : 'Aucun mapping de lecture pour cette relation.',
        },
      ]),
    ),
  };
  return validatePack({
    ...catalog,
    schemaVersion: '0.3',
    assertions,
    policies,
    ...((config.navigationHints || catalog.navigationHints)
      ? { navigationHints: config.navigationHints || catalog.navigationHints }
      : {}),
    integration: {
      adapter: config.adapter,
      runtimePackId: manifest.runtime_pack_id,
      sourceExchangeId: manifest.source_exchange_ref.exchange_id,
      manifestHash: hash(manifest),
      contractId: manifest.query_contract_ref.contract_id,
      capabilities,
      metadata: { artifactStatus: manifest.source_artifact_status, ...metadata },
    },
  });
}
export async function loadKristalDirectory(config, base) {
  const root = path.resolve(base, config.directory || '.');
  const manifestBytes = fs.readFileSync(safeFile(root, config.manifest));
  if (sha(manifestBytes) !== hex(config.manifestSha256))
    fail('PACK_INTEGRITY_FAILED', 'Empreinte du manifeste incorrecte.', 422);
  const manifest = upstream('manifest', JSON.parse(manifestBytes));
  if (manifest.build.compile_status !== 'succeeded')
    fail('PACK_NOT_READY', 'Pack compilé partiellement ou en échec.', 422);
  const files = new Map();
  let total = 0;
  const maxBytes = config.maxBytes || 256 * 1024 * 1024;
  for (const item of manifest.files) {
    if (files.has(item.path))
      fail('PACK_INTEGRITY_FAILED', 'Fichier dupliqué dans le manifeste.', 422);
    const filename = safeFile(root, item.path),
      stat = fs.statSync(filename);
    total += stat.size;
    if (total > maxBytes || stat.size !== item.size_bytes)
      fail('PACK_INTEGRITY_FAILED', 'Taille de fichier incorrecte ou budget dépassé.', 422);
    const bytes = fs.readFileSync(filename);
    if (sha(bytes) !== item.sha256)
      fail('PACK_INTEGRITY_FAILED', 'Empreinte de fichier incorrecte : ' + item.path, 422);
    files.set(item.path, { ...item, bytes });
  }
  let signaturesVerified = false;
  if (config.signatures) {
    const exclusions = config.signatures.excludeFields;
    if (
      !Array.isArray(exclusions) ||
      !exclusions.includes('signatures') ||
      exclusions.some((k) => !['signatures', 'integrity'].includes(k))
    )
      fail(
        'INVALID_CONFIG',
        'Cible de signature explicite requise (champs racine signatures/integrity).',
      );
    const target = Buffer.from(
      canonical(
        Object.fromEntries(Object.entries(manifest).filter(([k]) => !exclusions.includes(k))),
      ),
    );
    if (!manifest.signatures?.length) fail('PACK_SIGNATURE_INVALID', 'Signature absente.', 422);
    for (const signature of manifest.signatures) {
      const key = config.signatures.publicKeys?.[signature.key_id];
      if (
        signature.alg !== 'ed25519' ||
        !key ||
        !verify(null, target, key, Buffer.from(signature.signature, 'base64'))
      )
        fail('PACK_SIGNATURE_INVALID', 'Signature non vérifiable avec les clés configurées.', 422);
    }
    signaturesVerified = true;
  }
  if (manifest.integrity.manifest_hash) {
    const excludes = config.manifestHashExcludeFields;
    if (
      !Array.isArray(excludes) ||
      !excludes.includes('integrity') ||
      excludes.some((k) => !['integrity', 'signatures'].includes(k))
    )
      fail('UNSUPPORTED_HASH_PROFILE', 'Profil de cible du hash de manifeste requis.', 422);
    if (
      hex(
        hash(Object.fromEntries(Object.entries(manifest).filter(([k]) => !excludes.includes(k)))),
      ) !== hex(manifest.integrity.manifest_hash)
    )
      fail('PACK_INTEGRITY_FAILED', 'Hash logique du manifeste incorrect.', 422);
  }
  if (manifest.integrity.pack_hash) {
    if (!config.containerFile)
      fail(
        'PACK_INTEGRITY_FAILED',
        'Le conteneur original est requis pour vérifier pack_hash.',
        422,
      );
    const bytes = fs.readFileSync(safeFile(root, config.containerFile));
    if (sha(bytes) !== hex(manifest.integrity.pack_hash))
      fail('PACK_INTEGRITY_FAILED', 'Hash du conteneur incorrect.', 422);
  }
  const jsonFile = (name) => {
    const f = files.get(name);
    if (!f) fail('INVALID_CONFIG', 'Fichier non couvert par le manifeste : ' + name, 422);
    return JSON.parse(f.bytes);
  };
  const catalog = jsonFile(config.catalog);
  const policies = [];
  for (const f of files.values())
    if (f.role === 'reader_policy') {
      const doc = JSON.parse(f.bytes);
      if (!manifest.reader_policy_refs.some((ref) => hex(ref.hash) === f.sha256))
        fail(
          'PACK_POLICY_MISMATCH',
          'La politique n’est pas liée par son hash dans le manifeste.',
          422,
        );
      policies.push(normalizeKristalPolicy(doc));
    }
  if (!policies.length) fail('PACK_POLICY_MISMATCH', 'Aucune politique de lecture vérifiée.', 422);
  const declared = new Set(config.rows?.map((l) => l.file));
  if (!declared.size) fail('INVALID_CONFIG', 'Disposition des tables requise.', 422);
  for (const f of files.values())
    if (f.role === 'parquet_data' && !declared.has(f.path))
      fail('UNMAPPED_TABLE', 'Table Parquet non mappée : ' + f.path, 422);
  const assertions = [];
  let count = 0;
  const maxRows = config.maxRows || 100000;
  for (const layout of config.rows) {
    const f = files.get(layout.file);
    if (!f) fail('INVALID_CONFIG', 'Table absente du manifeste.', 422);
    let rows;
    if (layout.format === 'parquet') {
      const file = f.bytes.buffer.slice(
        f.bytes.byteOffset,
        f.bytes.byteOffset + f.bytes.byteLength,
      );
      const meta = await parquetMetadataAsync(file);
      if (Number(meta.num_rows) + count > maxRows)
        fail('PACK_LIMIT', 'Limite de lignes dépassée.', 422);
      rows = await parquetReadObjects({ file, compressors });
    } else if (layout.format === 'json') {
      rows = JSON.parse(f.bytes);
      if (!Array.isArray(rows)) fail('PACK_ROW_INVALID', 'Table JSON attendue.', 422);
    } else fail('UNSUPPORTED_STORAGE_PROFILE', 'Format de table non supporté.', 422);
    count += rows.length;
    if (count > maxRows) fail('PACK_LIMIT', 'Limite de lignes dépassée.', 422);
    assertions.push(...mapRows(rows, layout, catalog, config, manifest));
  }
  return buildPack(config, catalog, manifest, assertions, policies, {
    integrityVerified: true,
    signaturesVerified,
    manifestByteHash: sha(manifestBytes),
    ...Object.fromEntries(
      Object.entries(config.attestation || {}).filter(([k]) =>
        ['stale', 'stalenessSeconds', 'revokedKeys', 'federations'].includes(k),
      ),
    ),
  });
}
export async function loadKristalHttp(config, base, { fetchImpl = fetch } = {}) {
  const manifest = upstream('manifest', readJson(path.resolve(base, config.manifest)));
  if (hex(hash(manifest)) !== hex(config.manifestSha256))
    fail('PACK_INTEGRITY_FAILED', 'Hash canonique du manifeste HTTP incorrect.', 422);
  if (manifest.build.compile_status !== 'succeeded')
    fail('PACK_NOT_READY', 'Pack non compilé.', 422);
  const catalogBytes = fs.readFileSync(path.resolve(base, config.catalog));
  if (
    !manifest.files.some(
      (f) => f.sha256 === sha(catalogBytes) && f.size_bytes === catalogBytes.length,
    )
  )
    fail('PACK_INTEGRITY_FAILED', 'Catalogue absent du manifeste vérifié.', 422);
  const catalog = JSON.parse(catalogBytes);
  const docs = (config.policies || []).map((p) => {
    const bytes = fs.readFileSync(path.resolve(base, p.file));
    if (
      sha(bytes) !== hex(p.sha256) ||
      !manifest.reader_policy_refs.some((r) => hex(r.hash) === sha(bytes))
    )
      fail('PACK_POLICY_MISMATCH', 'Hash de politique incorrect.', 422);
    return normalizeKristalPolicy(JSON.parse(bytes));
  });
  if (docs.length !== 1 || docs[0].document.reader_policy_id !== config.readerPolicyId)
    fail('INVALID_CONFIG', 'La projection HTTP doit épingler exactement une politique.');
  const endpoint = serviceUrl(config.queryUrl).href,
    rows = [],
    seen = new Set();
  let cursor = null,
    offset = 0;
  const mode = config.pagingMode || 'CURSOR';
  if (!['CURSOR', 'OFFSET'].includes(mode)) fail('INVALID_CONFIG', 'Mode de pagination invalide.');
  const maxRows = config.maxRows || 100000,
    maxPages = config.maxPages || 1000;
  let completed = false;
  for (let page = 0; page < maxPages; page++) {
    const body = {
      contract_id: manifest.query_contract_ref.contract_id,
      projection: 'assertions',
      pattern: { s: null, p: null, o: null },
      filters: { reader_policy_id: config.readerPolicyId },
      paging: {
        mode,
        limit: config.pageSize || 500,
        ...(mode === 'CURSOR' ? { cursor } : { offset }),
      },
      include: {
        labels: true,
        provenance: true,
        validation: true,
        recognition: true,
        certainty: true,
        scope: true,
      },
    };
    const response = await fetchJson(endpoint, {
      method: 'POST',
      body,
      fetchImpl,
      timeoutMs: config.timeoutMs || 10000,
      headers:
        config.tokenEnv && process.env[config.tokenEnv]
          ? { Authorization: 'Bearer ' + process.env[config.tokenEnv] }
          : {},
    });
    if (
      response.contract_id !== body.contract_id ||
      response.runtime_pack_id !== manifest.runtime_pack_id ||
      response.source_exchange_id !== manifest.source_exchange_ref.exchange_id ||
      response.projection !== 'assertions' ||
      response.reader_policy_id !== config.readerPolicyId
    )
      fail('UPSTREAM_CONTEXT_MISMATCH', 'Identité de projection Kristal différente.', 502);
    if (
      response.diagnostics?.truncated !== false ||
      response.diagnostics?.filters_applied_before_paging !== true ||
      !Array.isArray(response.results) ||
      typeof response.paging?.has_more !== 'boolean'
    )
      fail('UPSTREAM_INCOMPLETE', 'Complétude de la projection non attestée.', 502);
    rows.push(...response.results);
    if (rows.length > maxRows) fail('PACK_LIMIT', 'Projection HTTP trop grande.', 422);
    if (!response.paging.has_more) {
      completed = true;
      break;
    }
    if (!response.results.length) fail('UPSTREAM_INCOMPLETE', 'Pagination sans progression.', 502);
    if (mode === 'CURSOR') {
      const next = response.paging.next_cursor;
      if (typeof next !== 'string' || !next || seen.has(next))
        fail('UPSTREAM_INCOMPLETE', 'Curseur répété ou absent.', 502);
      seen.add(next);
      cursor = next;
    } else offset += response.results.length;
  }
  if (!completed) fail('PACK_LIMIT', 'Projection interrompue avant complétude.', 422);
  const assertions = mapRows(rows, config.layout, catalog, config, manifest);
  // A service response is not proof that local pack bytes or signatures were verified.
  // Such requirements need directory loading, not a fabricated boolean from a remote response.
  return buildPack(config, catalog, manifest, assertions, docs, {
    integrityVerified: false,
    signaturesVerified: false,
    projectionPolicy: config.readerPolicyId,
    projectionHash: hash(rows),
  });
}

function loadKristalV6Path(config, filename) {
  const stat = fs.statSync(filename);
  const maxBytes = config.maxBytes || 256 * 1024 * 1024;
  if (!stat.isFile()) fail('INVALID_CONFIG', 'Le kristal_state v6 doit être un fichier.', 422);
  if (stat.size > maxBytes) fail('PACK_LIMIT', 'Kristal v6 dépasse la taille admise.', 422);
  const bytes = fs.readFileSync(filename);
  const digest = sha(bytes);
  if (config.stateSha256 && digest !== hex(config.stateSha256))
    fail('PACK_INTEGRITY_FAILED', 'Empreinte du kristal_state v6 incorrecte.', 422);
  let state;
  try { state = JSON.parse(bytes); }
  catch { fail('INVALID_KRISTAL_STATE', 'JSON kristal_state v6 invalide.', 422); }
  return importKristalV6State(state, config, digest);
}

export async function loadKristalV6File(config, base) {
  const root = path.resolve(base, config.directory || '.');
  if (typeof config.state !== 'string') fail('INVALID_CONFIG', 'Fichier kristal_state v6 requis.');
  return loadKristalV6Path(config, safeFile(root, config.state));
}

function collectionKey(value) {
  return String(value || '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/^kristal[-_ ]*/i, '')
    .replace(/[^a-z0-9]+/g, '');
}

function stateFilesInDomain(domain) {
  const candidates = [];
  const roots = [
    path.join(domain, 'knowledge-base', 'corpus'),
    path.join(domain, 'knowledge-base'),
  ];
  for (const root of roots) {
    if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) continue;
    for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
      if (!entry.isFile() || !entry.name.endsWith('.kristal-state.json')) continue;
      const filename = fs.realpathSync(path.join(root, entry.name));
      if (!filename.startsWith(domain + path.sep))
        fail('PACK_PATH_INVALID', 'État Kristal hors du domaine.', 422);
      candidates.push(filename);
    }
    if (candidates.length) break;
  }
  return [...new Set(candidates)].sort();
}

function resolveKristalCollectionEntry(config, base) {
  const root = fs.realpathSync(path.resolve(base, config.directory || '.'));
  if (typeof config.state === 'string') {
    const filename = safeFile(root, config.state);
    const rel = path.relative(root, filename).split(path.sep);
    const domainDirectory = rel[0] === (config.domainsDirectory || 'domains') ? rel[1] : path.basename(path.dirname(filename));
    return { filename, domainDirectory };
  }
  if (typeof config.kristal !== 'string' || !config.kristal.trim())
    fail('INVALID_CONFIG', 'Nom de Kristal requis pour kristal-kollection-v1.', 422);
  const domainsPath = path.join(root, config.domainsDirectory || 'domains');
  if (!fs.existsSync(domainsPath) || !fs.statSync(domainsPath).isDirectory())
    fail('KRISTAL_NOT_FOUND', 'Répertoire domains de la collection introuvable.', 422);
  const domains = fs.realpathSync(domainsPath);
  if (!domains.startsWith(root + path.sep))
    fail('PACK_PATH_INVALID', 'Répertoire domains hors de la collection.', 422);
  const wanted = collectionKey(config.kristal);
  const matches = fs.readdirSync(domains, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && collectionKey(entry.name) === wanted)
    .map((entry) => path.join(domains, entry.name));
  if (matches.length !== 1)
    fail(
      'KRISTAL_NOT_FOUND',
      matches.length ? `Kristal ambigu: ${config.kristal}` : `Kristal introuvable: ${config.kristal}`,
      422,
    );
  const domain = fs.realpathSync(matches[0]);
  const states = stateFilesInDomain(domain);
  if (states.length !== 1)
    fail('KRISTAL_NOT_FOUND', `Un unique kristal_state était attendu; trouvé: ${states.length}.`, 422);
  return { filename: states[0], domainDirectory: path.basename(domain) };
}

export function resolveKristalCollectionState(config, base) {
  return resolveKristalCollectionEntry(config, base).filename;
}

export async function loadKristalCollection(config, base) {
  const { filename, domainDirectory } = resolveKristalCollectionEntry(config, base);
  const inferredTitle = domainDirectory.replace(/^Kristal-/, '').replace(/[-_]+/g, ' ');
  const pack = loadKristalV6Path(
    {
      ...config,
      compatibilityMode: config.compatibilityMode || 'collection',
      title: config.title || `Kristal · ${inferredTitle}`,
    },
    filename,
  );
  pack.integration = {
    ...pack.integration,
    adapter: 'kristal-kollection-v1',
    collection: {
      kristal: config.kristal || domainDirectory,
      domainDirectory,
      stateFile: path.basename(filename),
    },
  };
  return pack;
}

export function listKristalCollection(config, base) {
  const root = fs.realpathSync(path.resolve(base, config.directory || '.'));
  const domainsPath = path.join(root, config.domainsDirectory || 'domains');
  if (!fs.existsSync(domainsPath) || !fs.statSync(domainsPath).isDirectory())
    fail('KRISTAL_NOT_FOUND', 'Répertoire domains de la collection introuvable.', 422);
  const domains = fs.realpathSync(domainsPath);
  if (!domains.startsWith(root + path.sep))
    fail('PACK_PATH_INVALID', 'Répertoire domains hors de la collection.', 422);
  return fs.readdirSync(domains, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => {
      const domain = fs.realpathSync(path.join(domains, entry.name));
      if (!domain.startsWith(domains + path.sep))
        fail('PACK_PATH_INVALID', 'Domaine Kristal hors de la collection.', 422);
      const states = stateFilesInDomain(domain);
      const id = entry.name.replace(/^Kristal[-_ ]*/i, '') || entry.name;
      const label = id.replace(/[-_]+/g, ' ').replace(/\s+/g, ' ').trim();
      const available = states.length === 1;
      return {
        id,
        label,
        domainDirectory: entry.name,
        available,
        ...(available ? { stateFile: path.basename(states[0]) } : {
          reason: states.length ? `${states.length} états Kristal trouvés.` : 'Aucun état *.kristal-state.json lisible.',
        }),
      };
    })
    .sort((a, b) => a.label.localeCompare(b.label, 'fr'));
}

export function listIntegrationKristals(file) {
  const config = readJson(file);
  if (!['kristal-kollection-v1', 'kristal-github-collection-v10', 'kristal-local-v10', 'kristal-local-catalog-v10'].includes(config.adapter))
    return { selectable: false, defaultKristal: null, items: [] };
  const base = path.dirname(path.resolve(file));
  const items = config.adapter === 'kristal-github-collection-v10'
    ? listGithubKristals(config, base) : config.adapter === 'kristal-local-v10'
      ? listLocalV10(config, base) : config.adapter === 'kristal-local-catalog-v10'
        ? listLocalCatalog(config,base) : listKristalCollection(config, base);
  const available = items.filter((item) => item.available);
  const configured = available.find((item) => collectionKey(item.id) === collectionKey(config.kristal));
  return {
    selectable: true,
    requiresSelection: config.adapter === 'kristal-local-catalog-v10',
    defaultKristal: config.adapter === 'kristal-local-catalog-v10' ? null : configured?.id || available[0]?.id || null,
    items,
  };
}

export async function loadIntegrationKristal(file, kristal, options) {
  const config = readJson(file), base = path.dirname(path.resolve(file));
  if (config.adapter === 'kristal-github-collection-v10')
    return validatePack(loadGithubKristal({ ...config, kristal }, base));
  if (config.adapter === 'kristal-local-catalog-v10')
    return validatePack(loadLocalCatalog(config,base,kristal));
  if (config.adapter === 'kristal-local-v10') {
    if (kristal !== 'local-v10') fail('KRISTAL_NOT_FOUND', 'Sélection locale inconnue.', 422);
    return validatePack(loadLocalV10(config, base));
  }
  if (config.adapter !== 'kristal-kollection-v1')
    fail('UNSUPPORTED_ADAPTER', 'Le backend configuré n’est pas une Kristal-Kollection.', 422);
  return loadKristalCollection({ ...config, kristal, title: undefined }, base, options);
}

export async function loadIntegration(file, options) {
  const config = readJson(file),
    base = path.dirname(path.resolve(file));
  if (config.adapter === 'kristal-github-collection-v10') return validatePack(loadGithubKristal(config, base));
  if (config.adapter === 'kristal-local-catalog-v10') return validatePack(loadNeutralCatalog(base));
  if (config.adapter === 'kristal-local-v10') return validatePack(loadLocalV10(config, base));
  if (config.adapter === 'kristal-runtime-pack-v1') return loadKristalDirectory(config, base);
  if (config.adapter === 'kristal-http-query-v1') return loadKristalHttp(config, base, options);
  if (config.adapter === 'kristal-state-v6') return loadKristalV6File(config, base);
  if (config.adapter === 'kristal-kollection-v1') return loadKristalCollection(config, base);
  fail('UNSUPPORTED_ADAPTER', 'Adaptateur Kristal inconnu.');
}
