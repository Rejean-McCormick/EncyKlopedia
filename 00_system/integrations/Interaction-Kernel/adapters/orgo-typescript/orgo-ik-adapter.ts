import type { InteractionEnvelope } from '../../runtime/typescript/src/types.js';

export interface OrgoIntegrationOperation {
  id: string; organization_id: string; provider: string; operation: string; subject_type: string; subject_id: string; request_metadata: unknown; correlation_id: string;
}

export function operationToIkEnvelope(operation: OrgoIntegrationOperation, route: { profileId: string; profileVersion: string; targetSystem: string; targetWorld?: string | null }): InteractionEnvelope {
  return {
    specversion:'ik/1.1', id:operation.id, class:'command', time:new Date().toISOString(),
    profile:{id:route.profileId,version:route.profileVersion},
    source:{system:'orgo',organization:operation.organization_id},
    target:{system:route.targetSystem,organization:operation.organization_id,world:route.targetWorld ?? null},
    subject:{type:operation.subject_type,id:operation.subject_id},
    operation:operation.operation,
    correlation_id:operation.correlation_id,
    idempotency_key:`${operation.organization_id}:${operation.id}`,
    data:operation.request_metadata,
    artifact_refs:[],
  };
}

export function decisionCommandToSignalInput(envelope: InteractionEnvelope): { source: string; external_reference: string; idempotency_key: string; correlation_id: string; request: unknown } {
  if (envelope.profile.id !== 'governance.decision.execute' || envelope.class !== 'command') throw new Error('unsupported inbound profile');
  if (!envelope.idempotency_key) throw new Error('idempotency_key required');
  return {
    source:'konnaxion',
    external_reference:envelope.subject.id,
    idempotency_key:envelope.idempotency_key,
    correlation_id:envelope.correlation_id ?? envelope.id,
    request:{ profile:envelope.profile, subject:envelope.subject, authority:envelope.authority, data:envelope.data, artifact_refs:envelope.artifact_refs ?? [] },
  };
}
