import json, unittest
from _paths import TCK
from interaction_kernel.fingerprint import request_fingerprint, semantic_projection

class FingerprintTests(unittest.TestCase):
    def test_vectors(self):
        doc=json.loads((TCK/'fingerprint'/'vectors.json').read_text(encoding='utf-8'))
        for vector in doc['vectors']:
            with self.subTest(vector=vector['id']):
                self.assertEqual(request_fingerprint(vector['envelope']), vector['expected_fingerprint'])
                self.assertEqual(semantic_projection(vector['envelope']), vector['expected_projection'])

    def test_transport_fields_do_not_change_fingerprint(self):
        doc=json.loads((TCK/'fingerprint'/'vectors.json').read_text(encoding='utf-8'))
        base=dict(doc['vectors'][0]['envelope'])
        changed=dict(base, id='different-id', time='2030-01-01T00:00:00Z', correlation_id='different', trace={'traceparent':'00-abc','tracestate':None})
        self.assertEqual(request_fingerprint(base), request_fingerprint(changed))
