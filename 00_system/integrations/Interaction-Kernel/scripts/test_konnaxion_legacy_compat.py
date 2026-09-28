from __future__ import annotations
import importlib.util
import sys
from pathlib import Path
from uuid import UUID

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path('/mnt/data/ik_build/src/konnaxion/backend/konnaxion/ethikos/orgo_bridge_contract.py')
ADAPTER=ROOT/'adapters/konnaxion-python/konnaxion_ik_adapter.py'

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

legacy=load('kx_legacy_contract',SOURCE)
adapter=load('kx_ik_adapter',ADAPTER)
envelope={
 'specversion':'ik/1.1','id':'01J00000000000000000000999','class':'command','time':'2026-09-14T12:00:00Z',
 'profile':{'id':'accountability.impact.publish','version':'1.0.0'},
 'source':{'system':'orgo','organization':'60f51ca2-c845-45aa-bc7e-2c62e53dfc5a'},
 'target':{'system':'konnaxion','organization':'60f51ca2-c845-45aa-bc7e-2c62e53dfc5a','world':'main'},
 'subject':{'type':'case','id':'fc305c81-afad-4b3a-8adb-b3668ad70d72'},
 'idempotency_key':'60f51ca2-c845-45aa-bc7e-2c62e53dfc5a:6b8c5523-096e-4fc0-b6a9-be644240b497',
 'correlation_id':'corr.uckk.A014.D009',
 'data':{'artifact_type':'impact_update','external_reference':'impact:UCKK-A014:day30:v1','demo_id':'uckk-pedagogy-pilot-a014','checkpoint':'day_30','synthetic':True,'epistemic_status':'synthetic_demo_fixture','summary':{'workload_imbalance_reports':6,'peer_rubric_clarification_requests':2,'policy_changes':0},'authority_note':'operational observation only; does not modify UCKK-D009'},
 'artifact_refs':[]
}
operation_id='6b8c5523-096e-4fc0-b6a9-be644240b497'
request=adapter.impact_publish_to_legacy_request(envelope,operation_id=operation_id)
parsed=legacy.validate_publish_request(request,idempotency_header=request['idempotency_key'],correlation_header=request['correlation_id'])
assert parsed['artifact_type']=='impact_update'
assert parsed['external_reference']=='impact:UCKK-A014:day30:v1'
assert str(UUID(request['operation_id']))==operation_id
print('Konnaxion legacy bridge compatibility: PASS')
