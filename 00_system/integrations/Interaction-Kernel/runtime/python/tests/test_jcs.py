import copy, hashlib, json, unittest
from _paths import TCK
from interaction_kernel.jcs import canonicalize

def remove_pointer(doc, pointer):
    parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer.lstrip("/").split("/")]
    parent = doc
    for p in parts[:-1]: parent = parent[int(p)] if isinstance(parent, list) else parent[p]
    last = parts[-1]
    if isinstance(parent, list): parent.pop(int(last))
    else: parent.pop(last, None)

class JCSTests(unittest.TestCase):
    def test_kristal_vectors(self):
        vectors = json.loads((TCK / "jcs" / "vectors.json").read_text(encoding="utf-8"))["vectors"]
        for vector in vectors:
            with self.subTest(vector=vector["id"]):
                value = copy.deepcopy(vector["input"])
                for pointer in vector.get("content_boundary", {}).get("exclude_json_pointers", []): remove_pointer(value, pointer)
                actual = canonicalize(value)
                self.assertEqual(actual, vector["expected_canonical"])
                self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(), vector["expected_sha256_hex"])
