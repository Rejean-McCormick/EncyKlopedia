import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const docs = path.join(root, 'docs');
const markdown = [];
function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.name.endsWith('.md')) markdown.push(full);
  }
}
walk(docs);
const problems = [];
let checkedLinks = 0;
for (const file of markdown) {
  const text = fs.readFileSync(file, 'utf8');
  if (text.includes('\0')) problems.push(`${path.relative(root,file)}: NUL byte`);
  const re = /\[[^\]]*\]\(([^)]+)\)/g;
  for (const match of text.matchAll(re)) {
    let target = match[1].trim();
    if (!target || /^(?:https?:|mailto:|#)/i.test(target)) continue;
    target = target.split('#')[0].split('?')[0];
    if (!target) continue;
    checkedLinks++;
    const resolved = path.resolve(path.dirname(file), decodeURIComponent(target));
    if (!fs.existsSync(resolved)) problems.push(`${path.relative(root,file)} -> ${target}`);
  }
}
console.log(JSON.stringify({schemaVersion:'1.0',markdownFiles:markdown.length,checkedLocalLinks:checkedLinks,problems},null,2));
if (problems.length) process.exitCode=1;
