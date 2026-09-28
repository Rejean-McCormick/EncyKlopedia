import type { InteractionEnvelope } from './types.js';
import { requestFingerprint } from './fingerprint.js';
import { IKError, type ProfileDescriptor, validateEnvelopeCore } from './validate.js';

export interface ContractValidationPort {
  validatePayload(profile: ProfileDescriptor, data: unknown): void | Promise<void>;
  validateArtifacts?(profile: ProfileDescriptor, envelope: InteractionEnvelope): void | Promise<void>;
}
export interface IdentityAuthenticator {
  authenticate(transportContext: Record<string, unknown>): string | Promise<string>;
}
export interface AuthorityAuthorizer {
  authorize(principal: string, envelope: InteractionEnvelope): void | Promise<void>;
}
export interface IdempotencyRecord { fingerprint: string; interactionId: string; receipt?: unknown; }
export interface IdempotencyStore {
  lookup(scope: string, key: string): IdempotencyRecord | undefined | Promise<IdempotencyRecord | undefined>;
  reserve(scope: string, key: string, record: IdempotencyRecord): void | Promise<void>;
}
export interface AdmissionResult { principal: string; fingerprint?: string; replay: boolean; prior?: IdempotencyRecord; }

export class AdmissionPipeline {
  constructor(
    private readonly contracts: ContractValidationPort,
    private readonly identity: IdentityAuthenticator,
    private readonly authority: AuthorityAuthorizer,
    private readonly idempotency: IdempotencyStore,
  ) {}

  async admit(envelope: InteractionEnvelope, profile: ProfileDescriptor, transportContext: Record<string, unknown>): Promise<AdmissionResult> {
    validateEnvelopeCore(envelope, profile);
    await this.contracts.validatePayload(profile, envelope.data ?? {});
    if (this.contracts.validateArtifacts) await this.contracts.validateArtifacts(profile, envelope);
    const principal=await this.identity.authenticate(transportContext);
    await this.authority.authorize(principal,envelope);
    const key=envelope.idempotency_key;
    if (!key) return {principal,replay:false};
    const fingerprint=await requestFingerprint(envelope);
    const target=envelope.target?.system ?? 'broadcast';
    const scope=`${target}:${envelope.profile.id}:${envelope.profile.version}`;
    const prior=await this.idempotency.lookup(scope,key);
    if (prior) {
      if (prior.fingerprint!==fingerprint) throw new IKError('IK_IDEMPOTENCY_CONFLICT','same idempotency key with divergent semantic request');
      return {principal,fingerprint,replay:true,prior};
    }
    await this.idempotency.reserve(scope,key,{fingerprint,interactionId:envelope.id});
    return {principal,fingerprint,replay:false};
  }
}
