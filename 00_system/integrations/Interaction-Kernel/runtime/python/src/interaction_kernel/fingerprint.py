from __future__ import annotations
from typing import Any, Mapping
from .jcs import sha256_jcs

FINGERPRINT_PROFILE = "ik.request-fingerprint/jcs-rfc8785+sha256/v1"
_SEMANTIC_FIELDS = (
    "class", "profile", "source", "target", "subject", "operation", "authority",
    "data_schema", "data", "governance", "artifact_refs", "evidence",
)

def semantic_projection(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Return the deterministic semantic request projection.

    Deliberately excludes id/time/correlation/causation/trace/response/delivery metadata.
    Missing semantic fields are omitted rather than materialized as null.
    """
    return {key: envelope[key] for key in _SEMANTIC_FIELDS if key in envelope}

def request_fingerprint(envelope: Mapping[str, Any]) -> str:
    return "sha256:" + sha256_jcs(semantic_projection(envelope))
