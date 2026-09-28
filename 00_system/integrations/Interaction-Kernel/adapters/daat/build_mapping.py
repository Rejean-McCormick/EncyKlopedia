from __future__ import annotations
from typing import Any, Mapping, Protocol

class MappingProfile(Protocol):
    id: str
    version: str
    def map_export(self, manifest: Mapping[str, Any]) -> Mapping[str, Any]: ...

class KristalNativeClient(Protocol):
    def compile(self, structured_input: Mapping[str, Any], *, requested_outputs: list[str]) -> list[Mapping[str, Any]]: ...


def execute_build(envelope: Mapping[str, Any], manifest: Mapping[str, Any], mapping: MappingProfile, kristal: KristalNativeClient) -> list[Mapping[str, Any]]:
    if envelope['profile'] != {'id':'kristal.build.request','version':'1.0.0'}: raise ValueError('unsupported profile')
    if envelope['target']['system'] != 'daat': raise ValueError('Da’at must be the IK receiver')
    if envelope['data']['mapping_profile'] != f'{mapping.id}/{mapping.version}': raise ValueError('mapping profile mismatch')
    structured_input = mapping.map_export(manifest)
    return kristal.compile(structured_input, requested_outputs=list(envelope['data']['requested_outputs']))
