/** Strict local-only HTTP integration with Kompiler 0.7.0-alpha.3.
 * No command execution, semantic rewriting, cache sharing or state publication.
 */
import { fail } from '../errors.mjs';

export function safeKompilerEndpoint(env = process.env) {
  const raw = env.KONSTELLATION_KOMPILER_URL;
  if (!raw) return null;
  let u;
  try { u = new URL(raw); } catch { fail('INVALID_CONFIG', 'URL Kompiler invalide.', 500); }
  if (u.protocol !== 'http:' || !['127.0.0.1', 'localhost', '[::1]'].includes(u.hostname)
      || u.username || u.password || u.search || u.hash || (u.pathname !== '/' && u.pathname !== '')) {
    fail('INVALID_CONFIG', 'Kompiler doit être une API HTTP locale, sans chemin ni identifiants.', 500);
  }
  return u.origin;
}

export class KompilerBridge {
  constructor({ url = safeKompilerEndpoint(), token = process.env.KONSTELLATION_KOMPILER_TOKEN || '',
    fetcher = fetch, timeoutMs = 8500, maxBytes = 2_000_000 } = {}) {
    this.url = url;
    this.token = token;
    this.fetcher = fetcher;
    this.timeoutMs = timeoutMs;
    this.maxBytes = maxBytes;
  }
  async request(method, endpoint, data) {
    if (!this.url) fail('UPSTREAM_UNAVAILABLE', 'Kompiler non configuré.', 503);
    const allowed = {
      'GET /v1/capabilities': true,
      'POST /v1/queries/validate': true,
      'POST /v1/runs': true,
      'POST /v1/projections/v6': true,
    };
    if (!allowed[`${method} ${endpoint}`]) fail('ACCESS_DENIED', 'Opération Kompiler interdite.', 403);
    const headers = { Accept: 'application/json' };
    if (data !== undefined) headers['Content-Type'] = 'application/json';
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    let response;
    try {
      response = await this.fetcher(this.url + endpoint, {
        method, headers, redirect: 'error', signal: AbortSignal.timeout(this.timeoutMs),
        ...(data === undefined ? {} : { body: JSON.stringify(data) }),
      });
    } catch {
      fail('UPSTREAM_UNAVAILABLE', 'Kompiler inaccessible ou délai dépassé.', 502);
    }
    if (!response.headers.get('content-type')?.toLowerCase().includes('application/json'))
      fail('UPSTREAM_INVALID', 'Réponse non JSON de Kompiler.', 502);
    const length = Number(response.headers.get('content-length') || 0);
    if (length > this.maxBytes) fail('UPSTREAM_LIMIT', 'Réponse Kompiler trop volumineuse.', 502);
    // Stream with a strict byte bound even if content-length is omitted/untrusted.
    const reader = response.body?.getReader();
    if (!reader) fail('UPSTREAM_INVALID', 'Réponse vide de Kompiler.', 502);
    const pieces = []; let used = 0;
    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        used += value.byteLength;
        if (used > this.maxBytes) { await reader.cancel(); fail('UPSTREAM_LIMIT', 'Réponse Kompiler trop volumineuse.', 502); }
        pieces.push(value);
      }
    } finally { reader.releaseLock(); }
    let json;
    try { json = JSON.parse(new TextDecoder().decode(Buffer.concat(pieces))); }
    catch { fail('UPSTREAM_INVALID', 'JSON Kompiler invalide.', 502); }
    if (!response.ok) fail('UPSTREAM_ERROR', `Kompiler a refusé l’opération (HTTP ${response.status}).`, response.status === 401 || response.status === 403 ? 502 : 422,
      { upstreamCode: String(json?.code || json?.error?.code || 'UNKNOWN').slice(0, 80) });
    return json;
  }
  capabilities() { return this.request('GET', '/v1/capabilities'); }
  validate(plan) { return this.request('POST', '/v1/queries/validate', plan); }
  run(plan) { return this.request('POST', '/v1/runs', plan); }
  projection(pack, surfaceId) {
    return this.request('POST', '/v1/projections/v6', {
      context_pack: pack, ...(surfaceId ? { surface_id: surfaceId } : {}), recipe_id: 'recipe:konstellation-bridge',
    });
  }
}
