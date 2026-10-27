import path from 'node:path';
import { ROOT, ajv, fail } from '../contracts.mjs';
import { readJson } from '../pack.mjs';
const names = {
  policy: 'reader-policy',
  manifest: 'runtime-pack-manifest',
  saRequest: 'communication_request',
  saResult: 'communication_result',
};
const validators = Object.fromEntries(
  Object.entries(names).map(([key, name]) => [
    key,
    ajv.compile(readJson(path.join(ROOT, 'contracts/upstream', name + '.schema.json'))),
  ]),
);
export function upstream(kind, data) {
  if (!validators[kind](data))
    fail('UPSTREAM_CONTRACT_INVALID', `${kind}: ${ajv.errorsText(validators[kind].errors)}`, 422);
  return data;
}
export async function fetchJson(
  url,
  {
    method = 'GET',
    body,
    headers = {},
    timeoutMs = 10000,
    maxBytes = 8 * 1024 * 1024,
    fetchImpl = fetch,
  } = {},
) {
  let r;
  try {
    r = await fetchImpl(url, {
      method,
      headers: { ...headers, ...(body ? { 'Content-Type': 'application/json' } : {}) },
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(timeoutMs),
      redirect: 'error',
    });
  } catch {
    fail('UPSTREAM_UNAVAILABLE', 'Le service externe est indisponible ou a dépassé le délai.', 503);
  }
  const chunks = [];
  let size = 0;
  try {
    for await (const chunk of r.body) {
      size += chunk.length;
      if (size > maxBytes) fail('UPSTREAM_LIMIT', 'Réponse externe trop grande.', 502);
      chunks.push(chunk);
    }
  } catch (e) {
    if (e.code) throw e;
    fail('UPSTREAM_UNAVAILABLE', 'Lecture externe interrompue.', 503);
  }
  let value;
  try {
    value = JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    fail('UPSTREAM_CONTRACT_INVALID', 'Réponse externe non JSON.', 502);
  }
  if (!r.ok)
    fail(
      'UPSTREAM_REJECTED',
      String(
        value.message_safe || value.error?.message || value.code || `Service HTTP ${r.status}`,
      ),
      502,
    );
  return value;
}
export function serviceUrl(raw) {
  let u;
  try {
    u = new URL(raw);
  } catch {
    fail('INVALID_CONFIG', 'URL de service invalide.');
  }
  if (!['http:', 'https:'].includes(u.protocol) || u.username || u.password)
    fail('INVALID_CONFIG', 'URL HTTP(S) sans credentials requise.');
  return u;
}
