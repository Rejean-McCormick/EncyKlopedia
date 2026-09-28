function canonicalPrimitive(value: null | boolean | string | number): string {
  if (typeof value === 'number' && !Number.isFinite(value)) throw new Error('non-finite number is not valid I-JSON');
  const out = JSON.stringify(value);
  if (out === undefined) throw new Error('unsupported JSON primitive');
  return out;
}

/** RFC 8785 JCS: ECMAScript primitive serialization + UTF-16 key ordering. */
export function canonicalize(value: unknown): string {
  if (value === null || typeof value === 'boolean' || typeof value === 'string' || typeof value === 'number') return canonicalPrimitive(value);
  if (Array.isArray(value)) return '[' + value.map(canonicalize).join(',') + ']';
  if (typeof value === 'object') {
    const object = value as Record<string, unknown>;
    const keys = Object.keys(object).sort();
    return '{' + keys.map(k => JSON.stringify(k) + ':' + canonicalize(object[k])).join(',') + '}';
  }
  throw new Error(`unsupported JSON value: ${typeof value}`);
}

export async function sha256Jcs(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(canonicalize(value));
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(v => v.toString(16).padStart(2, '0')).join('');
}
