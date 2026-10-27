import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const dataDir = path.join(ROOT, 'data');
const localPack = path.join(dataDir, 'biblical.pack.local.json');
const bundledPack = path.join(dataDir, 'biblical.pack.json');
const demoPack = path.join(dataDir, 'demo.pack.json');
const updater = path.join(ROOT, 'scripts', 'update-biblical-corpus.mjs');

function readPack(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch { return null; }
}

function stats(file) {
  const pack = readPack(file);
  if (!pack || pack.schemaVersion !== '0.3' || !Array.isArray(pack.entities)) return null;
  const count = (type) => pack.entities.filter((e) => e.type === type).length;
  return { pack, people: count('person'), works: count('work'), concepts: count('concept'), traditions: count('tradition') };
}

function usableBiblical(file) {
  const s = stats(file);
  return Boolean(s && s.works >= 100 && s.concepts >= 5 && s.traditions >= 3 && s.people >= 20);
}

function report(file, prefix = 'Corpus Playwright') {
  const s = stats(file);
  if (!s) return;
  console.log(`${prefix}: ${file}`);
  console.log(`  ${s.people} personnes · ${s.works} œuvres · ${s.concepts} concepts · ${s.traditions} traditions`);
  if (s.people >= 3000) console.log('  BibleData complet détecté.');
  else console.log('  Corpus biblique de base détecté (BibleData complet facultatif).');
}

fs.mkdirSync(dataDir, { recursive: true });

if (usableBiblical(localPack)) {
  report(localPack);
  process.exit(0);
}

if (!fs.existsSync(demoPack)) {
  console.error(`[ERREUR] Pack de base introuvable: ${demoPack}`);
  console.error('Le test attend data\\demo.pack.json dans la racine de Konstellation.');
  process.exit(2);
}

if (!fs.existsSync(updater) || !fs.existsSync(path.join(dataDir, 'biblical-seed.json'))) {
  if (usableBiblical(bundledPack)) {
    fs.copyFileSync(bundledPack, localPack);
    report(localPack, 'Corpus Playwright copié depuis le pack fourni');
    process.exit(0);
  }
  console.error('[ERREUR] Les fichiers de génération du Biblical Graph sont absents.');
  process.exit(3);
}

console.log('Préparation du corpus Playwright à partir de data\\demo.pack.json…');
let run = spawnSync(process.execPath, [updater, `--base=${demoPack}`, '--output=data/biblical.pack.local.json'], {
  cwd: ROOT,
  stdio: 'inherit',
  env: process.env,
});

if (run.status !== 0 || !usableBiblical(localPack)) {
  console.warn('Import en ligne incomplet; tentative avec le corpus biblique hors ligne…');
  run = spawnSync(process.execPath, [updater, '--offline', `--base=${demoPack}`, '--output=data/biblical.pack.local.json'], {
    cwd: ROOT,
    stdio: 'inherit',
    env: process.env,
  });
}

if (!usableBiblical(localPack)) {
  if (usableBiblical(bundledPack)) {
    fs.copyFileSync(bundledPack, localPack);
  } else {
    console.error('[ERREUR] Impossible de produire un corpus biblique utilisable pour Playwright.');
    process.exit(run.status || 4);
  }
}

report(localPack);
