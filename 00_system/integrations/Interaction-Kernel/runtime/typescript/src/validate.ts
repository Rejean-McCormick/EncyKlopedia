import type { InteractionEnvelope } from './types.js';

export class IKError extends Error {
  constructor(public readonly code: string, message: string, public readonly retryable: boolean | null = false) { super(message); }
}

export interface ProfileDescriptor { id: string; version: string; class: 'command'|'query'|'event'; source_systems?: string[]; target_systems?: string[]; delivery: { durability: 'ephemeral'|'durable'; idempotency: 'optional'|'required'|'forbidden'; ordering?: 'none'|'subject'|'profile-defined' }; authority?: { required?: boolean; accepted_kinds?: string[] }; }

export function validateEnvelopeCore(envelope: InteractionEnvelope, profile: ProfileDescriptor): void {
  if (envelope.specversion !== 'ik/1.1') throw new IKError('IK_UNSUPPORTED_PROTOCOL', envelope.specversion);
  if (!['command','query','event'].includes(envelope.class)) throw new IKError('IK_INVALID_ENVELOPE','unknown class');
  if ((envelope.class === 'command' || envelope.class === 'query') && !envelope.target) throw new IKError('IK_INVALID_ENVELOPE','target is required');
  if (profile.id !== envelope.profile.id || profile.version !== envelope.profile.version) throw new IKError('IK_UNKNOWN_PROFILE','profile mismatch');
  if (profile.class !== envelope.class) throw new IKError('IK_INVALID_ENVELOPE','class does not match profile');
  if (profile.source_systems?.length && !profile.source_systems.includes(envelope.source.system)) throw new IKError('IK_UNAUTHORIZED','source system is not allowed');
  if (profile.target_systems?.length && envelope.target && !profile.target_systems.includes(envelope.target.system)) throw new IKError('IK_TARGET_NOT_FOUND','target system is not allowed');
  if (profile.delivery.idempotency === 'required' && !envelope.idempotency_key) throw new IKError('IK_INVALID_ENVELOPE','idempotency_key is required');
  if (profile.authority?.required && !envelope.authority) throw new IKError('IK_UNAUTHORIZED','authority is required');
  if (envelope.authority && profile.authority?.accepted_kinds?.length && !profile.authority.accepted_kinds.includes(envelope.authority.kind)) throw new IKError('IK_UNAUTHORIZED','authority kind is not accepted');
}
