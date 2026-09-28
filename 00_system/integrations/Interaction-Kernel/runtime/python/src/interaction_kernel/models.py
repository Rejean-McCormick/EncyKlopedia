from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def new_receipt(*, interaction_id: str, source: dict[str, Any], status: str, retryable: bool = False, code: str | None = None, external_reference: str | None = None, data: dict[str, Any] | None = None, target: dict[str, Any] | None = None, correlation_id: str | None = None) -> dict[str, Any]:
    receipt = {
        "specversion": "ik/1.1", "record_type": "receipt", "id": str(uuid4()), "time": utc_now(),
        "interaction_id": interaction_id, "source": source, "status": status, "code": code,
        "retryable": retryable, "external_reference": external_reference, "data": data or {},
        "correlation_id": correlation_id,
    }
    if target is not None:
        receipt["target"] = target
    return receipt
