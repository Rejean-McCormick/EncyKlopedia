// Noncanonical, bounded, local metadata projections from Authoring Kit 3.3.
// No workspace scans; metadata has no access/publish/activation authority.
import { fail } from '../errors.mjs';
export const DISCOVERY_FORMAT = 'konstellation.discovery-projections/0.1';
export const KIT_DISCOVERY_FORMAT = 'kristal.discovery/1.0';
export const AUTHORITY = 'noncanonical_derived_metadata_not_access_or_publication_authority';
const sha = /^sha256:[0-9a-f]{64}$/;
const obj = v => v !== null && typeof v === 'object' && !Array.isArray(v);
const safe = (v, n=180) => typeof v === 'string' && v.length>0 && v.length<=n && !/[\x00-\x1f\x7f]/.test(v);
const fieldsOnly = (v, keys) => Object.keys(v).every(key => keys.includes(key));
const classifications = ['arketype_version','primary_archetype','supporting_archetypes','secondary_usages',
  'primary_usage','usage_slug','usage_family','domain','arketype_origin_slug','classification_source'];
const optionalClass = (x) => {
  if(!obj(x)) return false;
  return fieldsOnly(x,classifications) && Object.entries(x).every(([key,v]) => ['supporting_archetypes','secondary_usages'].includes(key)
    ? Array.isArray(v) && v.length<=8 && v.every(a => safe(a,80))
    : v===null || safe(v,120));
};

export function projectKitDiscovery(d, profile = null) {
  if (!obj(d) || d.format !== KIT_DISCOVERY_FORMAT || d.authority !== AUTHORITY ||
    !safe(d.state_ref,512) || !sha.test(d.source_fingerprint) || !obj(d.classification) ||
    !obj(d.data_layout) || d.data_layout.inventory_ref !== 'derived/reader-inventory.json' ||
    !safe(d.data_layout.organization,80) || !obj(d.reader) ||
    d.reader.hints_ref !== 'derived/reader-profile.json' || !safe(d.reader.profile,160) ||
    !obj(d.size) || !['tiny','small','medium','large','massive'].includes(d.size.class) ||
    !Number.isSafeInteger(d.size.tracked_local_bytes) || d.size.tracked_local_bytes<0 ||
    !['partial','measured_referenced_local_files'].includes(d.size.completeness))
    fail('DISCOVERY_INVALID','Unsupported Authoring Kit discovery metadata.',422);
  let accessPattern;
  if (profile !== null) {
    if (!obj(profile) || profile.format !== 'kristal.reader-profile/1.0' ||
      profile.configuration_status !== 'advisory_only' || profile.state_ref !== d.state_ref ||
      profile.source_fingerprint !== d.source_fingerprint || !safe(profile.access_pattern,100))
      fail('DISCOVERY_INVALID','Stale or incompatible reader profile.',422);
    accessPattern = profile.access_pattern;
  }
  const classification = Object.fromEntries(Object.entries(d.classification).filter(([k,v]) => classifications.includes(k) && v !== null));
  if (!optionalClass(classification)) fail('DISCOVERY_INVALID', 'Unsafe declared classification.',422);
  return {state_ref:d.state_ref, source_fingerprint:d.source_fingerprint,
    classification,
    organization:d.data_layout.organization, reader_profile:d.reader.profile,
    ...(accessPattern ? {access_pattern:accessPattern} : {}),
    size_class:d.size.class, tracked_local_bytes:d.size.tracked_local_bytes,
    measurement_completeness:d.size.completeness};
}
export function validateDiscoveryCatalog(doc) {
  const keys = ['state_ref','source_fingerprint','classification','organization','reader_profile',
    'access_pattern','size_class','tracked_local_bytes','measurement_completeness'];
  if (!obj(doc) || doc.format !== DISCOVERY_FORMAT || !fieldsOnly(doc,['format','entries']) ||
    !Array.isArray(doc.entries) || doc.entries.length > 1000) fail('DISCOVERY_INVALID','Invalid discovery catalog.',422);
  const seen = new Set();
  for (const d of doc.entries) {
    if (!obj(d) || !fieldsOnly(d,keys) || !safe(d.state_ref,512) || seen.has(d.state_ref) ||
      !sha.test(d.source_fingerprint) || !optionalClass(d.classification) || !safe(d.organization,80) ||
      !safe(d.reader_profile,160) || (d.access_pattern !== undefined && !safe(d.access_pattern,100)) ||
      !['tiny','small','medium','large','massive'].includes(d.size_class) ||
      !Number.isSafeInteger(d.tracked_local_bytes) || d.tracked_local_bytes<0 ||
      !['partial','measured_referenced_local_files'].includes(d.measurement_completeness))
      fail('DISCOVERY_INVALID','Malformed or duplicate discovery entry.',422);
    seen.add(d.state_ref);
  }
  return doc.entries;
}
export function enrichAuthorizedFleet(items, catalog) {
  const byRef = new Map(catalog.map(d=>[d.state_ref,d]));
  return items.map(item => {
    // Only annotated local Manager entries, after ACL filtering. Hosted entries are never inferred.
    const d = item.source === 'local_manager_preview' && item.stateRef ? byRef.get(item.stateRef) : null;
    if (!d) return item;
    return {...item, discovery: {
      classification:d.classification, organization:d.organization, readerProfile:d.reader_profile,
      ...(d.access_pattern ? {accessPattern:d.access_pattern} : {}),
      sizeClass:d.size_class, trackedLocalBytes:d.tracked_local_bytes,
      completeness:d.measurement_completeness, verification:'declared_noncanonical',
    }};
  });
}
