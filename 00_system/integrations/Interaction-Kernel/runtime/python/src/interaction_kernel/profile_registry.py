from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from .errors import IKError

@dataclass(frozen=True)
class RegisteredProfile:
    descriptor: dict[str, Any]
    payload_schema: dict[str, Any]
    root: Path

class ProfileRegistry:
    def __init__(self) -> None:
        self._profiles: dict[tuple[str, str], RegisteredProfile] = {}

    def register_directory(self, path: str | Path) -> RegisteredProfile:
        root = Path(path)
        descriptor = json.loads((root / "profile.json").read_text(encoding="utf-8"))
        payload_schema = json.loads((root / descriptor["payload_schema"]).read_text(encoding="utf-8"))
        key = (descriptor["id"], descriptor["version"])
        if key in self._profiles:
            raise IKError("IK_PROFILE_CONFLICT", f"profile already registered: {key}")
        registered = RegisteredProfile(descriptor, payload_schema, root)
        self._profiles[key] = registered
        return registered

    def get(self, profile_id: str, version: str) -> RegisteredProfile:
        try:
            return self._profiles[(profile_id, version)]
        except KeyError as exc:
            raise IKError("IK_UNKNOWN_PROFILE", f"unknown profile {profile_id}@{version}") from exc

    @classmethod
    def from_contracts(cls, contracts_root: str | Path) -> "ProfileRegistry":
        registry = cls()
        for p in sorted(Path(contracts_root).glob("profiles/*/*/*/profile.json")):
            registry.register_directory(p.parent)
        return registry
