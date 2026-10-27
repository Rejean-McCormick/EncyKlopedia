import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SRC = path.join(ROOT, 'src');
const files = [];
function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.isFile() && entry.name.endsWith('.svelte')) files.push(full);
  }
}
walk(SRC);

const problems = [];
const blockRe = /\{([#/])\s*(if|each|key)\b[^}]*\}/g;
for (const file of files) {
  const rel = path.relative(ROOT, file).replaceAll(path.sep, '/');
  const text = fs.readFileSync(file, 'utf8');
  const stack = [];
  for (const match of text.matchAll(blockRe)) {
    const [, direction, kind] = match;
    if (direction === '#') stack.push({ kind, offset: match.index });
    else {
      const open = stack.pop();
      if (!open || open.kind !== kind) problems.push({ file: rel, kind: 'svelte-block-order', detail: `unexpected {/${kind}}` });
    }
  }
  for (const open of stack) problems.push({ file: rel, kind: 'svelte-block-unclosed', detail: `{#${open.kind}} not closed` });

  for (const tag of ['script', 'svg']) {
    const opens = (text.match(new RegExp(`<${tag}(?:\\s|>)`, 'g')) || []).length;
    const closes = (text.match(new RegExp(`</${tag}>`, 'g')) || []).length;
    if (opens !== closes) problems.push({ file: rel, kind: 'tag-balance', detail: `${tag}: ${opens} open / ${closes} close` });
  }

  for (const match of text.matchAll(/<g\b([^>]*)role=["']button["']([^>]*)>/g)) {
    const attrs = `${match[1]} ${match[2]}`;
    if (!/tabindex=["']0["']/.test(attrs)) problems.push({ file: rel, kind: 'svg-keyboard', detail: 'SVG role=button missing tabindex=0' });
    if (!/aria-label=/.test(attrs)) problems.push({ file: rel, kind: 'svg-accessible-name', detail: 'SVG role=button missing aria-label' });
  }

  if (/<button\b[^>]*role=["']listitem["']/.test(text)) problems.push({ file: rel, kind: 'aria-role-override', detail: 'button must not be overridden with role=listitem' });
  if (/\sstyle(?:=|:)/.test(text)) problems.push({ file: rel, kind: 'csp-inline-style', detail: 'inline style attributes/directives are forbidden; use classes or SVG presentation attributes' });
}

const output = { schemaVersion: '1.0', files: files.length, problems };
console.log(JSON.stringify(output, null, 2));
if (problems.length) process.exitCode = 1;
