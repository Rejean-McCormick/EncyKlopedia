import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TARGET = path.join(ROOT, 'SBOM.cdx.json');
const CHECK = process.argv.includes('--check');
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));
const lockPath = path.join(ROOT, 'package-lock.json');
const hasLock = fs.existsSync(lockPath);
const lock = hasLock ? JSON.parse(fs.readFileSync(lockPath, 'utf8')) : null;

const bomRef = (name, version) => `pkg:npm/${encodeURIComponent(name)}@${version}`;
const components = [];
const dependencies = [];
const seen = new Set();

if (hasLock && lock?.packages) {
  for (const [location, meta] of Object.entries(lock.packages)) {
    if (!location || !meta?.name || !meta?.version) continue;
    const ref = bomRef(meta.name, meta.version);
    if (seen.has(ref)) continue;
    seen.add(ref);
    components.push({
      type: 'library', name: meta.name, version: meta.version, 'bom-ref': ref,
      ...(meta.license ? { licenses: [{ license: { name: String(meta.license) } }] } : {}),
      ...(meta.integrity ? { hashes: [{ alg: 'SHA-512', content: String(meta.integrity).replace(/^sha512-/, '') }] } : {}),
    });
  }
  const packageRefByLocation = new Map();
  for (const [location, meta] of Object.entries(lock.packages)) if (location && meta?.name && meta?.version) packageRefByLocation.set(location, bomRef(meta.name, meta.version));
  for (const [location, meta] of Object.entries(lock.packages)) {
    if (!location || !meta?.name || !meta?.version) continue;
    const refs = [];
    for (const dep of Object.keys(meta.dependencies || {})) {
      let cursor = location;
      let found = null;
      while (true) {
        const candidate = cursor ? `${cursor}/node_modules/${dep}` : `node_modules/${dep}`;
        if (packageRefByLocation.has(candidate)) { found = packageRefByLocation.get(candidate); break; }
        const idx = cursor.lastIndexOf('/node_modules/');
        if (idx < 0) { cursor = ''; if (packageRefByLocation.has(`node_modules/${dep}`)) found = packageRefByLocation.get(`node_modules/${dep}`); break; }
        cursor = cursor.slice(0, idx);
      }
      if (found) refs.push(found);
    }
    dependencies.push({ ref: bomRef(meta.name, meta.version), dependsOn: [...new Set(refs)].sort() });
  }
} else {
  for (const [name, version] of Object.entries({ ...(pkg.dependencies || {}), ...(pkg.devDependencies || {}) })) {
    const ref = bomRef(name, version);
    components.push({ type: 'library', name, version, 'bom-ref': ref, properties: [{ name: 'konstellation:resolution', value: 'direct-only-no-lockfile' }] });
  }
}

components.sort((a, b) => a['bom-ref'].localeCompare(b['bom-ref']));
dependencies.sort((a, b) => a.ref.localeCompare(b.ref));
const rootRef = bomRef(pkg.name, pkg.version);
const rootDeps = components.filter((c) => Object.hasOwn(pkg.dependencies || {}, c.name) || Object.hasOwn(pkg.devDependencies || {}, c.name)).map((c) => c['bom-ref']).sort();
const serialSeed = createHash('sha256').update(JSON.stringify({ name: pkg.name, version: pkg.version, components: components.map((c) => c['bom-ref']) })).digest('hex').slice(0, 32);
const bom = {
  bomFormat: 'CycloneDX', specVersion: '1.6', serialNumber: `urn:uuid:${serialSeed.slice(0,8)}-${serialSeed.slice(8,12)}-4${serialSeed.slice(13,16)}-8${serialSeed.slice(17,20)}-${serialSeed.slice(20,32)}`, version: 1,
  metadata: {
    component: { type: 'application', name: pkg.name, version: pkg.version, 'bom-ref': rootRef },
    properties: [
      { name: 'konstellation:lockfileComplete', value: String(hasLock) },
      { name: 'konstellation:nodeEngine', value: pkg.engines?.node || '' },
    ],
  },
  components,
  dependencies: [{ ref: rootRef, dependsOn: rootDeps }, ...dependencies],
};
const rendered = `${JSON.stringify(bom, null, 2)}\n`;

if (CHECK) {
  if (!fs.existsSync(TARGET) || fs.readFileSync(TARGET, 'utf8') !== rendered) {
    console.error('SBOM.cdx.json absent ou non synchronisé. Exécuter npm run release:sbom.');
    process.exit(1);
  }
  if (!hasLock) {
    console.error('SBOM incomplet : package-lock.json absent.');
    process.exit(1);
  }
  console.log(`SBOM OK (${components.length} composants)`);
} else {
  fs.writeFileSync(TARGET, rendered);
  console.log(`wrote SBOM.cdx.json (${components.length} composants; lockfileComplete=${hasLock})`);
}
