from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
lock=json.loads((ROOT/'locks/kristal-v5.0.0-rc.1.lock.json').read_text())
up=ROOT/'locks/kristal-v5.0.0-rc.1-upstream'
release=json.loads((up/'kristal-release.json').read_text())
schemas=json.loads((up/'schema-set.manifest.json').read_text())
assert lock['format']=='kristal.consumer-lock/v1'
assert lock['version']==release['version']=='5.0.0-rc.1'
assert lock['git_tag']==release['git']['tag']=='v5.0.0-rc.1'
assert lock['git_commit']=='af703bf02ee04a69a5f2ad6694fa8b8e56ae2b19'
assert lock['canonicalization_profile']==release['canonicalization_profile']=='kristal.v5:jcs-rfc8785'
assert lock['schema_set_digest']==schemas['schema_set_digest']=='sha256:7a94a1e8a91d5c5267b73b7f1e98977faa548324bc937bb491cd08d49fdc8c92'
print('Kristal dependency lock: PASS')
