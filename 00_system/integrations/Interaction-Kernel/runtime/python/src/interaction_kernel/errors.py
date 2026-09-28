from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass
class IKError(Exception):
    code: str
    detail: str
    retryable: bool | None = False
    data: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"
