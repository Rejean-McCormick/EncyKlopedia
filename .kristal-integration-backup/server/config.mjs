import { fail } from './errors.mjs';
import { parseAuthConfig } from './auth.mjs';

const PROFILES = new Set(['local','lan','shared','public']);
export function loadConfig(env = process.env) {
  const deploymentProfile = env.KONSTELLATION_DEPLOYMENT_PROFILE || 'local';
  if (!PROFILES.has(deploymentProfile)) fail('INVALID_CONFIG', 'KONSTELLATION_DEPLOYMENT_PROFILE invalide.', 500);
  const host = env.HOST || (deploymentProfile === 'local' ? '127.0.0.1' : '0.0.0.0');
  const port = Number(env.PORT || 4321);
  if (!Number.isInteger(port) || port < 1 || port > 65535) fail('INVALID_CONFIG','PORT invalide.',500);
  const anonymousReadonly = env.KONSTELLATION_ANONYMOUS_READONLY === 'true' || env.KONSTELLATION_PUBLIC_READONLY === 'true';
  const authPrincipals = parseAuthConfig(env);
  if (deploymentProfile !== 'local' && !authPrincipals.length && !anonymousReadonly)
    fail('INVALID_CONFIG', 'Un principal authentifié ou KONSTELLATION_ANONYMOUS_READONLY=true est requis hors profil local.', 500);
  const defaultHosts = deploymentProfile === 'local' ? 'localhost,127.0.0.1,[::1]' : 'localhost,127.0.0.1,[::1]';
  const allowedHosts = (env.KONSTELLATION_ALLOWED_HOSTS || defaultHosts).split(',').map((x)=>x.trim()).filter(Boolean);
  if (!allowedHosts.length) fail('INVALID_CONFIG', 'KONSTELLATION_ALLOWED_HOSTS ne peut pas être vide.', 500);
  const rateLimitRaw = Number(env.KONSTELLATION_RATE_LIMIT_PER_MINUTE || 600);
  if (!Number.isFinite(rateLimitRaw)) fail('INVALID_CONFIG', 'KONSTELLATION_RATE_LIMIT_PER_MINUTE invalide.', 500);
  const rateLimitPerMinute = Math.max(30, Math.min(10000, rateLimitRaw));
  const exposeCorpusIdentity = env.KONSTELLATION_EXPOSE_CORPUS_IDENTITY === 'true';
  const localPrincipal = Object.freeze({
    id: env.KONSTELLATION_LOCAL_PRINCIPAL || 'local-user',
    roles: [...new Set((env.KONSTELLATION_ROLES || 'public').split(',').map((x)=>x.trim()).filter(Boolean))].sort(),
    scopes: ['read','metrics','sa','admin'],
  });
  return {
    deploymentProfile, host, port, anonymousReadonly, authPrincipals, localPrincipal,
    allowedHosts, rateLimitPerMinute, exposeCorpusIdentity, devOrigin: env.KONSTELLATION_DEV_ORIGIN || null,
  };
}
export function cspFor(config) {
  if (config.deploymentProfile === 'public') return "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'";
  return "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'";
}
