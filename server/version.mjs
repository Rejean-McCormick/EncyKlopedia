import fs from 'node:fs';
import path from 'node:path';
import { ROOT, publicSchemaVersions } from './contracts.mjs';
import { hash } from './pack.mjs';

const pkg = JSON.parse(fs.readFileSync(path.join(ROOT, 'package.json'), 'utf8'));
let releaseManifest = null;
try {
  const candidate = JSON.parse(fs.readFileSync(path.join(ROOT, 'RELEASE-MANIFEST.json'), 'utf8'));
  if (candidate?.schemaVersion === '1.0' && candidate?.release === pkg.version) releaseManifest = candidate;
} catch {
  releaseManifest = null;
}

export function versionInfo(engine = null, { exposeCorpusIdentity = false } = {}) {
  return {
    version: pkg.version,
    buildId: process.env.KONSTELLATION_BUILD_ID || process.env.GIT_COMMIT || 'development',
    artifactSha256: process.env.KONSTELLATION_ARTIFACT_SHA256 || null,
    sourceManifestSha256: releaseManifest?.contentSha256 || null,
    sourceFileCount: releaseManifest?.fileCount || null,
    schemaVersions: publicSchemaVersions(),
    ...(engine && exposeCorpusIdentity ? {
      corpus: {
        datasetRef: engine.baseContext.datasetRef,
        registryRef: engine.baseContext.registryRef,
        fingerprint: hash({ datasetRef: engine.baseContext.datasetRef, registryRef: engine.baseContext.registryRef }),
      },
    } : {}),
  };
}
