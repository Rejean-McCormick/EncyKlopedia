import type { InteractionEnvelope } from './types.js';
import { sha256Jcs } from './jcs.js';

export const FINGERPRINT_PROFILE = 'ik.request-fingerprint/jcs-rfc8785+sha256/v1' as const;
const SEMANTIC_FIELDS = ['class','profile','source','target','subject','operation','authority','data_schema','data','governance','artifact_refs','evidence'] as const;

export function semanticProjection(envelope: InteractionEnvelope): Record<string, unknown> {
  const source = envelope as unknown as Record<string, unknown>;
  const result: Record<string, unknown> = {};
  for (const key of SEMANTIC_FIELDS) if (Object.prototype.hasOwnProperty.call(source, key)) result[key] = source[key];
  return result;
}

export async function requestFingerprint(envelope: InteractionEnvelope): Promise<string> {
  return 'sha256:' + await sha256Jcs(semanticProjection(envelope));
}
