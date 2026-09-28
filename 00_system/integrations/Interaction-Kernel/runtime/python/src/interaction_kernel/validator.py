from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Mapping
from jsonschema import Draft202012Validator, FormatChecker, RefResolver
from .errors import IKError
from .profile_registry import ProfileRegistry

class ContractValidator:
    def __init__(self, contracts_root: str | Path, profiles: ProfileRegistry | None = None) -> None:
        self.root = Path(contracts_root)
        self.schemas = self.root / "schemas"
        self.profile_registry = profiles or ProfileRegistry.from_contracts(self.root)
        self._cache: dict[str, Draft202012Validator] = {}
        self._schema_store: dict[str, dict[str, Any]] = {}
        for schema_path in self.schemas.glob("*.json"):
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self._schema_store[schema_path.resolve().as_uri()] = schema
            self._schema_store[schema_path.name] = schema
            if isinstance(schema.get("$id"), str):
                self._schema_store[schema["$id"]] = schema

    def _validator(self, name: str) -> Draft202012Validator:
        if name not in self._cache:
            schema_path = self.schemas / name
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            resolver = RefResolver(base_uri=schema_path.resolve().as_uri(), referrer=schema, store=self._schema_store)
            self._cache[name] = Draft202012Validator(schema, resolver=resolver, format_checker=FormatChecker())
        return self._cache[name]

    def _validate(self, schema_name: str, value: Any) -> None:
        errors = sorted(self._validator(schema_name).iter_errors(value), key=lambda e: list(e.absolute_path))
        if errors:
            first = errors[0]
            path = ".".join(str(p) for p in first.absolute_path) or "$"
            raise IKError("IK_SCHEMA_VALIDATION_FAILED", f"{path}: {first.message}")

    def validate_envelope(self, envelope: Mapping[str, Any]) -> None:
        self._validate("envelope.schema.json", envelope)
        if envelope.get("specversion") != "ik/1.1":
            raise IKError("IK_UNSUPPORTED_PROTOCOL", str(envelope.get("specversion")))
        profile = envelope["profile"]
        registered = self.profile_registry.get(profile["id"], profile["version"])
        descriptor = registered.descriptor
        if envelope["class"] != descriptor["class"]:
            raise IKError("IK_INVALID_ENVELOPE", "class does not match profile")
        source_systems = descriptor.get("source_systems") or []
        if source_systems and envelope["source"]["system"] not in source_systems:
            raise IKError("IK_UNAUTHORIZED", "source system is not allowed by profile")
        target_systems = descriptor.get("target_systems") or []
        target = envelope.get("target")
        if target_systems and target and target["system"] not in target_systems:
            raise IKError("IK_TARGET_NOT_FOUND", "target system is not allowed by profile")
        delivery = descriptor["delivery"]
        if delivery["idempotency"] == "required" and not envelope.get("idempotency_key"):
            raise IKError("IK_INVALID_ENVELOPE", "idempotency_key is required by profile")
        auth = descriptor.get("authority", {})
        if auth.get("required") and not envelope.get("authority"):
            raise IKError("IK_UNAUTHORIZED", "authority is required by profile")
        if envelope.get("authority") and auth.get("accepted_kinds"):
            if envelope["authority"]["kind"] not in auth["accepted_kinds"]:
                raise IKError("IK_UNAUTHORIZED", "authority kind is not accepted by profile")
        payload_validator = Draft202012Validator(registered.payload_schema, format_checker=FormatChecker())
        payload_errors = sorted(payload_validator.iter_errors(envelope.get("data", {})), key=lambda e: list(e.absolute_path))
        if payload_errors:
            first = payload_errors[0]
            path = ".".join(str(p) for p in first.absolute_path) or "data"
            raise IKError("IK_SCHEMA_VALIDATION_FAILED", f"{path}: {first.message}")

    def validate_receipt(self, receipt: Mapping[str, Any]) -> None:
        self._validate("receipt.schema.json", receipt)

    def validate_query_result(self, result: Mapping[str, Any]) -> None:
        self._validate("query-result.schema.json", result)

    def validate_artifact_ref(self, artifact_ref: Mapping[str, Any]) -> None:
        self._validate("artifact-ref.schema.json", artifact_ref)

    def validate_export_manifest(self, manifest: Mapping[str, Any]) -> None:
        self._validate("export-manifest.schema.json", manifest)
