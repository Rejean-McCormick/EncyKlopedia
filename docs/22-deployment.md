# Déploiement — Konstellation 1.0

## 1. Prérequis de release

- Node.js `>=24.15.0` ;
- `package-lock.json` commité ;
- `npm ci` ;
- tests Node + Vitest ;
- build Astro/Svelte ;
- Playwright ;
- benchmark complet ;
- artefact immutable avec build id/checksum.

## 2. Profils

### Local single-user

```bash
KONSTELLATION_DEPLOYMENT_PROFILE=local npm start
```

Bind par défaut : `127.0.0.1`. Le principal local reçoit les scopes administratifs du processus local.

### LAN / Shared

```bash
export KONSTELLATION_DEPLOYMENT_PROFILE=shared
export HOST=0.0.0.0
export KONSTELLATION_ALLOWED_HOSTS=konstellation.internal.example
export KONSTELLATION_AUTH_TOKENS='{...}'
npm start
```

Utiliser TLS via reverse proxy/gateway. Ne pas utiliser `*` pour `KONSTELLATION_ALLOWED_HOSTS` sans justification.

### Public

Le profil `public` active la CSP stricte. Utiliser TLS/gateway, gestion de secrets, rate limiting externe si nécessaire et threat model qualifié.

Un accès anonyme de lecture nécessite un opt-in explicite :

```bash
KONSTELLATION_ANONYMOUS_READONLY=true
```

## 3. Variables principales

| Variable | Rôle |
|---|---|
| `KONSTELLATION_DEPLOYMENT_PROFILE` | `local`, `lan`, `shared`, `public` |
| `HOST` / `PORT` | écoute HTTP |
| `KONSTELLATION_ALLOWED_HOSTS` | allowlist Host |
| `KONSTELLATION_AUTH_TOKENS` | map token -> principal/roles/scopes |
| `KONSTELLATION_AUTH_TOKEN` | compatibilité token unique |
| `KONSTELLATION_ANONYMOUS_READONLY` | opt-in read-only sans auth |
| `KONSTELLATION_RATE_LIMIT_PER_MINUTE` | rate limit processus |
| `KONSTELLATION_CURSOR_SECRET` | secret HMAC stable pour cursors |
| `KONSTELLATION_PACK` | pack normalisé |
| `KONSTELLATION_LENSES` | dossier de Lens explicites |
| `KONSTELLATION_BACKEND_CONFIG` | adaptateur backend |
| `KONSTELLATION_SA_CONFIG` | intégration SA |
| `KONSTELLATION_BUILD_ID` | identifiant build exposé par version API |
| `KONSTELLATION_EXPOSE_CORPUS_IDENTITY` | opt-in identité corpus sur `/api/version` |

## 4. Release gate

```bash
npm ci
npm run release:preflight
npm run release:check
```

`release:prepare` génère le SBOM puis le manifest source déterministe. `release:check` vérifie lockfile, manifest/SBOM synchronisés, exécute tests Node, Vitest, build, Playwright et benchmark complet. Il doit être vert avant publication du tag final 1.0.0.

## 5. Readiness

`/api/ready` n’est disponible qu’après construction de l’Engine, validation du pack, registry, policies et Lens. Le scope policy par défaut et le StructuralProfiler visible sont préchauffés avant l’ouverture du trafic ; `scopeIndexReady` et `navigationProfileReady` doivent être vrais. Un corpus/config invalide doit empêcher le service de démarrer plutôt que produire une dégradation silencieuse.

## 6. Rollback

Restaurer ensemble code, lockfile/build, schémas, configuration, corpus compatible, policies et Lens/hints. Un changement de contexte/fingerprint invalide naturellement les cursors incompatibles.

## 7. Sauvegardes

Sauvegarder séparément le Kristal canonique, configuration, policies, Lens/hints et explorations utilisateur ayant une valeur métier. Le normalized pack et les projections ne remplacent jamais le canon. Procédure complète : [runbooks/BACKUP-RESTORE.md](runbooks/BACKUP-RESTORE.md).

## 8. CI de référence

Les workflows GitHub Actions de référence utilisent Node 24.15.0, `npm ci`, installent Chromium Playwright, régénèrent SBOM/manifest et exigent `npm run release:check`. Le workflow de tag produit un bundle qualifié accompagné de son SHA-256.
