from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

@dataclass(frozen=True)
class ActivationResult:
    status: str
    active_artifact_id: str | None
    rollback_artifact_id: str | None = None
    data: Mapping[str, Any] | None = None

class RuntimePackActivationPort(Protocol):
    def verify(self, artifact_ref: Mapping[str, Any]) -> None: ...
    def stage(self, artifact_ref: Mapping[str, Any]) -> ActivationResult: ...
    def activate(self, artifact_ref: Mapping[str, Any]) -> ActivationResult: ...
    def rollback(self, artifact_id: str) -> ActivationResult: ...

# Deployment rule: when kOA-Linux is present, this port is implemented by the
# platform and Konnaxion does not maintain a second authoritative activation state.
