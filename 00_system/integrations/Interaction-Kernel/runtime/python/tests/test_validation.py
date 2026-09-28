import copy, json, unittest
from _paths import CONTRACTS, TCK
from interaction_kernel.errors import IKError
from interaction_kernel.validator import ContractValidator

class ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.validator=ContractValidator(CONTRACTS)

    def test_valid_command(self):
        env=json.loads((TCK/'fingerprint'/'vectors.json').read_text(encoding='utf-8'))['vectors'][0]['envelope']
        self.validator.validate_envelope(env)

    def test_command_requires_target(self):
        env=copy.deepcopy(json.loads((TCK/'fingerprint'/'vectors.json').read_text(encoding='utf-8'))['vectors'][0]['envelope'])
        env.pop('target')
        with self.assertRaises(IKError): self.validator.validate_envelope(env)

    def test_profile_requires_idempotency(self):
        env=copy.deepcopy(json.loads((TCK/'fingerprint'/'vectors.json').read_text(encoding='utf-8'))['vectors'][0]['envelope'])
        env.pop('idempotency_key')
        with self.assertRaises(IKError) as ctx: self.validator.validate_envelope(env)
        self.assertEqual(ctx.exception.code,'IK_INVALID_ENVELOPE')
