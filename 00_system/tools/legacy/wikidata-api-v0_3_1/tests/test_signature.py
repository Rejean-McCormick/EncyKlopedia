import importlib.util
import sys
from pathlib import Path

P = Path(__file__).parents[1] / "scripts" / "pull_wikidata_relation_signatures.py"
spec = importlib.util.spec_from_file_location("pull", P)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

def test_no_values_leak():
    entity = {
        "claims": {
            "P19": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datatype": "wikibase-item", "datavalue": {"value": {"id": "Q3012"}, "type": "wikibase-entityid"}}}],
            "P569": [{"rank": "normal", "mainsnak": {"snaktype": "value", "datatype": "time", "datavalue": {"value": {"time": "+1879-03-14T00:00:00Z"}, "type": "time"}}}],
        }
    }
    sig = m.first_level_signature(entity)
    assert set(sig) == {"P19", "P569"}
    assert sig["P19"]["datatypes_seen"] == ["wikibase-item"]
    assert "datavalue" not in repr(sig)
    assert "Q3012" not in repr(sig)
    assert "1879" not in repr(sig)

def test_http_json_handles_gzip(monkeypatch):
    import gzip
    import json

    payload = {"search": [{"id": "Q937"}]}
    compressed = gzip.compress(json.dumps(payload).encode("utf-8"))

    class Headers:
        def get(self, key, default=None):
            return "gzip" if key.lower() == "content-encoding" else default

    class Resp:
        headers = Headers()
        def read(self):
            return compressed
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    monkeypatch.setattr(m.urllib.request, "urlopen", lambda *a, **k: Resp())
    assert m.http_json({"action": "test"}) == payload
