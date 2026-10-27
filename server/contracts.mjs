import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import Ajv from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import { AppError, fail } from './errors.mjs';
export { AppError, fail } from './errors.mjs';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const ajv = new Ajv({ allErrors: true, strict: false, allowUnionTypes: true });
addFormats(ajv);

const schemas = new Map();
for (const file of fs.readdirSync(path.join(ROOT, 'contracts')).filter((name) => name.endsWith('.schema.json'))) {
  const schema = JSON.parse(fs.readFileSync(path.join(ROOT, 'contracts', file), 'utf8'));
  const name = file.replace(/\.schema\.json$/, '');
  schemas.set(name, schema);
  if (schema.$id) ajv.addSchema(schema, schema.$id);
}

const validators = new Map();
for (const [name, schema] of schemas) validators.set(name, ajv.compile(schema));

export function validate(name, value, { code = 'INVALID_QUERY', status = 400 } = {}) {
  const fn = validators.get(name);
  if (!fn) fail('INTERNAL_ERROR', `Schéma inconnu: ${name}`, 500);
  if (!fn(value)) {
    const details = fn.errors.slice(0, 8).map((error) => ({
      path: error.instancePath || '/', keyword: error.keyword, message: error.message,
    }));
    fail(code, `${name}: ${details.slice(0, 3).map((e) => `${e.path} ${e.message}`).join('; ')}`, status, { validation: details });
  }
  return value;
}

export function schemaVersion(name) {
  const schema = schemas.get(name);
  const id = schema?.$id || '';
  const match = id.match(/:([0-9]+(?:\.[0-9]+)*)$/);
  return match?.[1] || null;
}

export function publicSchemaVersions() {
  const names = ['query-spec','lens','exploration-state','result-set','constellation-response','navigation-hints','navigation-plan','navigation-projection','renderer-registry'];
  return Object.fromEntries(names.filter((name) => schemas.has(name)).map((name) => [name, schemaVersion(name)]));
}

export { ajv };
