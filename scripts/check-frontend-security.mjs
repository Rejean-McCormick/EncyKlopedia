import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const roots = [path.join(ROOT, 'src')];
const files = [];
function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full);
    else if (entry.isFile() && ['.svelte', '.astro', '.js', '.mjs', '.css'].includes(path.extname(entry.name))) files.push(full);
  }
}
for (const root of roots) walk(root);

const rules = [
  { id: 'raw-html', re: /\{@html\b|\b(?:innerHTML|outerHTML)\s*=|insertAdjacentHTML\s*\(/, detail: 'raw HTML sinks are forbidden in frontend source' },
  { id: 'dynamic-code', re: /\beval\s*\(|\bnew\s+Function\s*\(/, detail: 'dynamic JavaScript evaluation is forbidden' },
  { id: 'inline-style-attr', re: /\sstyle(?:=|:)/, detail: 'inline style attributes/directives are forbidden by public CSP' },
];
const problems = [];
for (const file of files) {
  const rel = path.relative(ROOT, file).replaceAll(path.sep, '/');
  const text = fs.readFileSync(file, 'utf8');
  for (const rule of rules) if (rule.re.test(text)) problems.push({ file: rel, kind: rule.id, detail: rule.detail });
  if (file.endsWith('.astro')) {
    for (const match of text.matchAll(/<script\b([^>]*)>/gi)) {
      if (!/\bsrc\s*=/.test(match[1])) problems.push({ file: rel, kind: 'astro-inline-script', detail: 'inline client scripts in .astro are forbidden; use bundled modules' });
    }
  }
  if (file.endsWith('.css') && /@import\s+(?:url\()?['"]?https?:\/\//i.test(text)) {
    problems.push({ file: rel, kind: 'remote-css-import', detail: 'remote CSS imports are forbidden' });
  }
}
const astroConfig = fs.readFileSync(path.join(ROOT, 'astro.config.mjs'), 'utf8');
if (!/inlineStylesheets\s*:\s*['"]never['"]/.test(astroConfig)) {
  problems.push({ file: 'astro.config.mjs', kind: 'astro-inline-stylesheets', detail: 'build.inlineStylesheets must remain "never" for public CSP' });
}
console.log(JSON.stringify({ schemaVersion: '1.0', files: files.length, problems }, null, 2));
if (problems.length) process.exitCode = 1;
