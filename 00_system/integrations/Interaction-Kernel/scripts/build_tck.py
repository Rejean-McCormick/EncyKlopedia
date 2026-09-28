from __future__ import annotations
import importlib.util, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'runtime/python/src'))
from interaction_kernel.fingerprint import request_fingerprint, semantic_projection
src=json.loads((ROOT/'tck/fingerprint/cases.unresolved.json').read_text(encoding='utf-8'))
out={'format':'ik.request-fingerprint-vectors/1','profile':'ik.request-fingerprint/jcs-rfc8785+sha256/v1','vectors':[]}
for item in src['vectors']:
    env=item['envelope']
    out['vectors'].append({**item,'expected_projection':semantic_projection(env),'expected_fingerprint':request_fingerprint(env)})
(ROOT/'tck/fingerprint/vectors.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f"wrote {len(out['vectors'])} fingerprint vectors")
