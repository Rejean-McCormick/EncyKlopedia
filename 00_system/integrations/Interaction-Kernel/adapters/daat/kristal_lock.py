from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path

EXPECTED_COMMIT='af703bf02ee04a69a5f2ad6694fa8b8e56ae2b19'
EXPECTED_SCHEMA_SET='sha256:7a94a1e8a91d5c5267b73b7f1e98977faa548324bc937bb491cd08d49fdc8c92'

@dataclass(frozen=True)
class KristalLock:
    version: str; git_tag: str; git_commit: str; canonicalization_profile: str; schema_set_digest: str

def load_and_verify(path: str | Path) -> KristalLock:
    value=json.loads(Path(path).read_text(encoding='utf-8'))
    if value.get('format')!='kristal.consumer-lock/v1': raise ValueError('unexpected Kristal lock format')
    if value['version']!='5.0.0-rc.1' or value['git_tag']!='v5.0.0-rc.1': raise ValueError('unexpected Kristal release')
    if value['git_commit']!=EXPECTED_COMMIT: raise ValueError('Kristal commit pin mismatch')
    if value['schema_set_digest']!=EXPECTED_SCHEMA_SET: raise ValueError('Kristal schema-set digest mismatch')
    if value['canonicalization_profile']!='kristal.v5:jcs-rfc8785': raise ValueError('Kristal canonicalization profile mismatch')
    return KristalLock(value['version'],value['git_tag'],value['git_commit'],value['canonicalization_profile'],value['schema_set_digest'])
