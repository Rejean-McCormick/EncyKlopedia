import copy, json, unittest
from _paths import CONTRACTS, TCK
from interaction_kernel.admission import AdmissionPipeline
from interaction_kernel.errors import IKError
from interaction_kernel.validator import ContractValidator

class Authn:
    def authenticate(self, ctx): return 'principal:test'
class Authz:
    def authorize(self, principal, envelope): return None
class Store:
    def __init__(self): self.values={}
    def lookup(self, *, scope, key): return self.values.get((scope,key))
    def reserve(self, *, scope, key, fingerprint, interaction_id): self.values[(scope,key)]={'fingerprint':fingerprint,'interaction_id':interaction_id}

class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.store=Store(); self.pipe=AdmissionPipeline(ContractValidator(CONTRACTS),Authn(),Authz(),self.store)
        self.env=copy.deepcopy(json.loads((TCK/'fingerprint/vectors.json').read_text())['vectors'][0]['envelope'])
    def test_first_then_replay(self):
        first=self.pipe.admit(self.env,{})
        second=self.pipe.admit(self.env,{})
        self.assertFalse(first.replay); self.assertTrue(second.replay)
    def test_divergent_replay_conflicts(self):
        self.pipe.admit(self.env,{})
        other=copy.deepcopy(self.env); other['data']['decision_revision']='rev-4'
        with self.assertRaises(IKError) as ctx: self.pipe.admit(other,{})
        self.assertEqual(ctx.exception.code,'IK_IDEMPOTENCY_CONFLICT')
