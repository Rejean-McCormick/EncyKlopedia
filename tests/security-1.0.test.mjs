import test from 'node:test';
import assert from 'node:assert/strict';
import { parseAuthConfig, authenticate, requireScope } from '../server/auth.mjs';
import { loadConfig, cspFor } from '../server/config.mjs';

const request = (authorization = '') => ({ headers: { authorization } });

test('shared/public profiles fail closed without authentication or explicit anonymous read-only', () => {
  assert.throws(() => loadConfig({ KONSTELLATION_DEPLOYMENT_PROFILE: 'shared' }), { code: 'INVALID_CONFIG' });
  assert.doesNotThrow(() => loadConfig({ KONSTELLATION_DEPLOYMENT_PROFILE: 'shared', KONSTELLATION_ANONYMOUS_READONLY: 'true' }));
});

test('multi-principal token configuration preserves roles and scopes', () => {
  const token = '0123456789abcdef0123456789abcdef';
  const config = loadConfig({
    KONSTELLATION_DEPLOYMENT_PROFILE: 'shared',
    KONSTELLATION_AUTH_TOKENS: JSON.stringify({
      [token]: { id: 'reader-1', roles: ['public', 'research'], scopes: ['read', 'metrics'] },
    }),
  });
  const principal = authenticate(request(`Bearer ${token}`), config);
  assert.equal(principal.id, 'reader-1');
  assert.deepEqual(principal.roles, ['public', 'research']);
  assert.deepEqual(principal.scopes, ['metrics', 'read']);
  assert.doesNotThrow(() => requireScope(principal, 'read'));
  assert.throws(() => requireScope(principal, 'sa'), { code: 'ACCESS_DENIED' });
  assert.throws(() => authenticate(request('Bearer definitely-wrong-token'), config), { code: 'ACCESS_DENIED' });
});

test('legacy single token remains supported but is not required by the 1.0 contract', () => {
  const principals = parseAuthConfig({
    KONSTELLATION_AUTH_TOKEN: '0123456789abcdef0123456789abcdef',
    KONSTELLATION_AUTH_PRINCIPAL: 'legacy',
    KONSTELLATION_ROLES: 'public,research',
    KONSTELLATION_AUTH_SCOPES: 'read,metrics',
  });
  assert.equal(principals.length, 1);
  assert.equal(principals[0].principal.id, 'legacy');
  assert.deepEqual(principals[0].principal.roles, ['public', 'research']);
});

test('public profile emits a CSP without unsafe-inline', () => {
  const config = loadConfig({
    KONSTELLATION_DEPLOYMENT_PROFILE: 'public',
    KONSTELLATION_ANONYMOUS_READONLY: 'true',
  });
  assert(!cspFor(config).includes("'unsafe-inline'"));
});

test('local profile has an explicit local principal and admin scope', () => {
  const config = loadConfig({ KONSTELLATION_DEPLOYMENT_PROFILE: 'local', KONSTELLATION_ROLES: 'private,public' });
  const principal = authenticate(request(), config);
  assert.equal(principal.id, 'local-user');
  assert.deepEqual(principal.roles, ['private', 'public']);
  assert(principal.scopes.includes('admin'));
});
