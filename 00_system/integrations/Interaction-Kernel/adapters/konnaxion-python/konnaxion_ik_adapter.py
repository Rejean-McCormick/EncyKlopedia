from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Protocol
from uuid import uuid4

class DurableEmissionPort(Protocol):
    def persist(self, envelope: Mapping[str, Any]) -> None: ...

@dataclass(frozen=True)
class DecisionRecordView:
    decision_id: str
    revision: str
    artifact_id: str
    artifact_digest: str
    organization: str
    world: str | None = None
    effective_at: str | None = None


def decision_execute_envelope(record: DecisionRecordView, *, target_organization: str, target_world: str | None = None) -> dict[str, Any]:
    now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
    return {
      'specversion':'ik/1.1','id':str(uuid4()),'class':'command','time':now,
      'profile':{'id':'governance.decision.execute','version':'1.0.0'},
      'source':{'system':'konnaxion','organization':record.organization,'world':record.world},
      'target':{'system':'orgo','organization':target_organization,'world':target_world},
      'subject':{'type':'decision','id':record.decision_id},
      'correlation_id':f'decision:{record.decision_id}',
      'idempotency_key':f'decision:{record.decision_id}:{record.revision}:orgo:execute:v1',
      'authority':{'kind':'governance-mandate','claims':[f'authority://konnaxion/decision/{record.decision_id}']},
      'data':{'decision_revision':record.revision,'effective_at':record.effective_at},
      'artifact_refs':[{'owner':{'system':'konnaxion','organization':record.organization},'artifact_type':'konnaxion.decision_record','artifact_id':record.artifact_id,'version':record.revision,'integrity':{'algorithm':'sha256','digest':record.artifact_digest}}],
      'response':{'acceptance_receipt':True,'final_receipt':True},
    }


def impact_publish_to_legacy_request(envelope: Mapping[str, Any], *, operation_id: str | None = None) -> dict[str, Any]:
    if envelope.get('profile') != {'id':'accountability.impact.publish','version':'1.0.0'}:
        raise ValueError('wrong profile')
    if envelope.get('class') != 'command': raise ValueError('impact publish must be command')
    source=envelope['source']; subject=envelope['subject']; data=dict(envelope.get('data') or {})
    organization=source.get('organization')
    if not organization: raise ValueError('source.organization is required for legacy bridge')
    return {
      'operation_id': operation_id or str(uuid4()),
      'organization_id': organization,
      'operation':'publish',
      'idempotency_key':envelope['idempotency_key'],
      'correlation_id':envelope.get('correlation_id') or envelope['id'],
      'subject':{'type':subject['type'],'id':subject['id']},
      'input':data,
    }
