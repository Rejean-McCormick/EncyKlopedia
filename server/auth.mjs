import { timingSafeEqual } from 'node:crypto';
import { fail } from './errors.mjs';

function safeEqual(a, b) {
  const aa = Buffer.from(String(a || ''));
  const bb = Buffer.from(String(b || ''));
  return aa.length === bb.length && aa.length > 0 && timingSafeEqual(aa, bb);
}
function normalizePrincipal(value, fallbackId) {
  const principal = value && typeof value === 'object' ? value : {};
  const id = String(principal.id || fallbackId || '').trim();
  if (!/^[A-Za-z0-9._:@-]{1,128}$/.test(id)) fail('INVALID_CONFIG', 'Identifiant principal invalide.', 500);
  const roles = [...new Set((Array.isArray(principal.roles) ? principal.roles : ['public']).map(String).map((x) => x.trim()).filter(Boolean))].sort();
  const scopes = [...new Set((Array.isArray(principal.scopes) ? principal.scopes : ['read']).map(String).map((x) => x.trim()).filter(Boolean))].sort();
  if (!roles.length || roles.some((role) => !/^[A-Za-z0-9._:@-]{1,128}$/.test(role))) fail('INVALID_CONFIG', 'Rôles principal invalides.', 500);
  if (!scopes.length || scopes.some((scope) => !/^[A-Za-z0-9._:-]{1,128}$/.test(scope))) fail('INVALID_CONFIG', 'Scopes principal invalides.', 500);
  return Object.freeze({ id, roles, scopes });
}

export function parseAuthConfig(env = process.env) {
  const principals = [];
  const raw = env.KONSTELLATION_AUTH_TOKENS;
  if (raw) {
    let parsed;
    try { parsed = JSON.parse(raw); } catch { fail('INVALID_CONFIG', 'KONSTELLATION_AUTH_TOKENS doit être un objet JSON.', 500); }
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) fail('INVALID_CONFIG', 'KONSTELLATION_AUTH_TOKENS invalide.', 500);
    for (const [token, value] of Object.entries(parsed)) {
      if (typeof token !== 'string' || token.length < 16 || token.length > 4096) fail('INVALID_CONFIG', 'Token d’authentification invalide.', 500);
      principals.push({ token, principal: normalizePrincipal(value, `token-${principals.length + 1}`) });
    }
  }
  if (env.KONSTELLATION_AUTH_TOKEN) {
    if (env.KONSTELLATION_AUTH_TOKEN.length < 16 || env.KONSTELLATION_AUTH_TOKEN.length > 4096) fail('INVALID_CONFIG', 'KONSTELLATION_AUTH_TOKEN invalide.', 500);
    principals.push({
      token: env.KONSTELLATION_AUTH_TOKEN,
      principal: normalizePrincipal({
        id: env.KONSTELLATION_AUTH_PRINCIPAL || 'legacy-token',
        roles: (env.KONSTELLATION_ROLES || 'public').split(','),
        scopes: (env.KONSTELLATION_AUTH_SCOPES || 'read,metrics,sa').split(','),
      }, 'legacy-token'),
    });
  }
  return principals;
}

export function authenticate(req, config) {
  const auth = String(req.headers.authorization || '');
  const token = auth.startsWith('Bearer ') ? auth.slice(7) : '';
  if (token) {
    for (const entry of config.authPrincipals || []) if (safeEqual(token, entry.token)) return entry.principal;
    fail('ACCESS_DENIED', 'Jeton d’authentification invalide.', 401);
  }
  if (config.deploymentProfile === 'local') return config.localPrincipal;
  if (config.anonymousReadonly) return Object.freeze({ id: 'anonymous', roles: ['public'], scopes: ['read'] });
  fail('ACCESS_DENIED', 'Authentification requise.', 401);
}

export function requireScope(principal, scope) {
  if (!principal?.scopes?.includes(scope) && !principal?.scopes?.includes('admin')) fail('ACCESS_DENIED', 'Scope insuffisant.', 403);
}
