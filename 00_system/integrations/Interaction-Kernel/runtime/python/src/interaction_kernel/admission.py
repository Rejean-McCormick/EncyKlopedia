from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from .errors import IKError
from .fingerprint import request_fingerprint
from .validator import ContractValidator

class IdentityAuthenticator(Protocol):
    def authenticate(self, transport_context: Mapping[str, Any]) -> str: ...

class AuthorityAuthorizer(Protocol):
    def authorize(self, principal: str, envelope: Mapping[str, Any]) -> None: ...

class IdempotencyStore(Protocol):
    def lookup(self, *, scope: str, key: str) -> Mapping[str, Any] | None: ...
    def reserve(self, *, scope: str, key: str, fingerprint: str, interaction_id: str) -> None: ...

@dataclass(frozen=True)
class AdmissionResult:
    principal: str
    fingerprint: str | None
    replay: bool
    prior: Mapping[str, Any] | None = None

class AdmissionPipeline:
    def __init__(self, validator: ContractValidator, authenticator: IdentityAuthenticator, authorizer: AuthorityAuthorizer, idempotency: IdempotencyStore) -> None:
        self.validator = validator
        self.authenticator = authenticator
        self.authorizer = authorizer
        self.idempotency = idempotency

    def admit(self, envelope: Mapping[str, Any], transport_context: Mapping[str, Any]) -> AdmissionResult:
        self.validator.validate_envelope(envelope)
        principal = self.authenticator.authenticate(transport_context)
        self.authorizer.authorize(principal, envelope)
        key = envelope.get("idempotency_key")
        if not key:
            return AdmissionResult(principal, None, False)
        fingerprint = request_fingerprint(envelope)
        scope = f"{envelope['target']['system']}:{envelope['profile']['id']}:{envelope['profile']['version']}"
        prior = self.idempotency.lookup(scope=scope, key=key)
        if prior:
            if prior.get("fingerprint") != fingerprint:
                raise IKError("IK_IDEMPOTENCY_CONFLICT", "same idempotency key with divergent semantic request")
            return AdmissionResult(principal, fingerprint, True, prior)
        self.idempotency.reserve(scope=scope, key=key, fingerprint=fingerprint, interaction_id=envelope["id"])
        return AdmissionResult(principal, fingerprint, False)
