import importlib.util
import io
import json
import sys
import urllib.error
from pathlib import Path

P = Path(__file__).parents[1] / "scripts" / "pull_wikidata_relation_signatures.py"
spec = importlib.util.spec_from_file_location("pull_rate", P)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


def test_retry_after_seconds_numeric():
    assert m._retry_after_seconds("7") == 7.0


def test_http_json_retries_429(monkeypatch):
    calls = {"n": 0}
    waits = []

    class Headers(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    class Resp:
        headers = Headers({})
        def read(self):
            return json.dumps({"ok": True}).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    def fake_urlopen(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise urllib.error.HTTPError(
                "https://www.wikidata.org/w/api.php", 429, "Too Many Requests",
                Headers({"Retry-After": "1"}), io.BytesIO(b"")
            )
        return Resp()

    monkeypatch.setattr(m.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(m.time, "sleep", lambda seconds: waits.append(seconds))
    m.configure_http(max_retries=2, backoff_base=0.5)
    assert m.http_json({"action": "test"}) == {"ok": True}
    assert calls["n"] == 2
    assert waits and waits[0] >= 1.0
