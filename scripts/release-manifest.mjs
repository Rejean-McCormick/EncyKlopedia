import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TARGET = path.join(ROOT, 'RELEASE-MANIFEST.json');
const CHECK = process.argv.includes('--check');
const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));

const EXCLUDED_DIRS = new Set([
  '.git', '.astro', '.cache', '.tmp', 'node_modules', 'dist', 'coverage',
  'test-results', 'playwright-report', '__pycache__', '.venv', 'venv',
  '.backup-constellation-motion-20260928-172932',
]);
const EXCLUDED_FILES = new Set(['RELEASE-MANIFEST.json']);

function sha256(buffer) {
  return createHash('sha256').update(buffer).digest('hex');
}

function walk(dir, prefix = '') {
  const rows = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    if (entry.name.startsWith('.backup-') || EXCLUDED_DIRS.has(entry.name)) continue;
    const rel = prefix ? `${prefix}/${entry.name}` : entry.name;
    if (entry.isDirectory()) rows.push(...walk(path.join(dir, entry.name), rel));
    else if (entry.isFile() && !EXCLUDED_FILES.has(rel)) {
      const bytes = fs.readFileSync(path.join(dir, entry.name));
      rows.push({ path: rel.replaceAll('\\', '/'), sha256: sha256(bytes), size: bytes.length });
    }
  }
  return rows;
}

const files = walk(ROOT);
const contentSha256 = sha256(Buffer.from(files.map((f) => `${f.sha256}  ${f.size}  ${f.path}\n`).join(''), 'utf8'));
const manifest = {
  schemaVersion: '1.0',
  release: pkg.version,
  profile: 'konstellation-multi-version-adaptive-navigation',
  canonicalTruth: 'upstream-kristal-state',
  navigationPlanSchema: '1.0',
  projectionSchema: '1.0',
  fileCount: files.length,
  contentSha256,
  files,
};
const rendered = `${JSON.stringify(manifest, null, 2)}\n`;

if (CHECK) {
  if (!fs.existsSync(TARGET)) {
    console.error('RELEASE-MANIFEST.json absent. Exécuter npm run release:manifest.');
    process.exit(1);
  }
  const current = fs.readFileSync(TARGET, 'utf8');
  if (current !== rendered) {
    console.error('RELEASE-MANIFEST.json n’est pas synchronisé avec le tree source.');
    process.exit(1);
  }
  console.log(`release manifest OK (${manifest.fileCount} files, ${manifest.contentSha256})`);
} else {
  fs.writeFileSync(TARGET, rendered);
  console.log(`wrote RELEASE-MANIFEST.json (${manifest.fileCount} files, ${manifest.contentSha256})`);
}
