#!/usr/bin/env node
// Build an explicit, disclosure-minimized Discovery 3.3 catalog from named local files.
// Never searches workspaces, never posts data, and does not produce an access grant.
import fs from 'node:fs';
import path from 'node:path';
import { projectKitDiscovery, DISCOVERY_FORMAT } from '../server/integrations/discovery.mjs';

function readJson(file, max = 256 * 1024) {
  const absolute = path.resolve(file);
  const st = fs.lstatSync(absolute);
  if (!st.isFile() || st.isSymbolicLink() || st.size > max) throw new Error('Unsafe or oversized input file.');
  return JSON.parse(fs.readFileSync(absolute, 'utf8'));
}
function main(args) {
  if (args.length < 3 || args[0] !== '--output' || !args[1] || args.slice(2).some(x => x.startsWith('--'))) {
    console.error('Usage: node scripts/project-discovery.mjs --output PRIVATE_CATALOG.json PATH/kristal.discovery.json [...more...]');
    process.exitCode = 2;return;
  }
  const target = path.resolve(args[1]);
  if (fs.existsSync(target)) throw new Error('Refusing to overwrite an existing catalog.');
  const entries = [], seen = new Set();
  for (const input of args.slice(2)) {
    if (path.basename(input) !== 'kristal.discovery.json') throw new Error('Only explicitly selected kristal.discovery.json inputs are supported.');
    const d = readJson(input);
    const parent = path.dirname(path.resolve(input));
    let profile = null;
    const profileFile = path.join(parent,'derived','reader-profile.json');
    if (fs.existsSync(profileFile)) profile = readJson(profileFile);
    const projected = projectKitDiscovery(d, profile);
    if (seen.has(projected.state_ref)) throw new Error('Duplicate state_ref in discovery inputs.');
    seen.add(projected.state_ref); entries.push(projected);
  }
  const doc = {format:DISCOVERY_FORMAT, entries:entries.sort((a,b)=>a.state_ref.localeCompare(b.state_ref, 'en'))};
  // The output itself can contain sensitive metadata. It is private and local only.
  const bytes = Buffer.from(JSON.stringify(doc,null,2)+'\n');
  const fd = fs.openSync(target,'wx',0o600);
  try {fs.writeFileSync(fd,bytes); } finally { fs.closeSync(fd); }
  console.log(`Created local-only catalog (${entries.length} entries). Configure KONSTELLATION_DISCOVERY_CATALOG only after checking disclosure policy.`);
}
try { main(process.argv.slice(2)); }
catch (error) {console.error(`Discovery catalog refused: ${error.message}`);process.exitCode=1;}
