# Lot 1 — Reproducible CI install (2026-10-27)

The CI `fast` job now **always** runs `npm ci`. Missing or drifting `package-lock.json` is a hard failure, never a fallback to mutable `npm install`.

The locked dependency graph and Node >=24.15.0 requirement are preserved. No runtime server, renderer, access-policy, public profile, or publication code changed.

Run under Node.js >=24.15.0:

```sh
npm ci
npm test
npm run test:ui
npm run build
npm run test:e2e:smoke
```

This patch is not a release-qualification result; E2E and production deployment remain separate gates.
