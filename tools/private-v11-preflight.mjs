#!/usr/bin/env node
/** Read-only, local private preflight. Never imports into the public server. */
import { inspectFile } from '../src/private-v11-preflight.mjs';
const names = ['view', 'graph', 'registry', 'crosswalk', 'catalog'];
const argv = process.argv.slice(2);
if (argv.length !== 2 * names.length || names.some((name, idx) => argv[idx * 2] !== '--' + name)) {
  console.error('Usage: node tools/private-v11-preflight.mjs --view VIEW --graph GRAPH --registry REGISTRY --crosswalk CROSSWALK --catalog CATALOG');
  process.exit(2);
}
try {
  const paths = Object.fromEntries(names.map((name, idx) => [name, argv[idx * 2 + 1]]));
  const result = inspectFile(paths.view, paths);
  console.log(JSON.stringify(result, null, 2));
} catch (error) {
  console.error(String(error?.message || error));
  process.exitCode = 2;
}
