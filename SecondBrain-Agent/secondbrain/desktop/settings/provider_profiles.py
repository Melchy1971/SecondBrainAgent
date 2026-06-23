from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProviderKind(str, Enum):
    EMBEDDING = "embedding"
    LLM = "llm"
    OCR = "ocr"
    STORAGE = "storage"
    CONNECTOR = "connector"


@dataclass(frozen=True)
class ProviderField:
    key: str
    field_type: str = "string"
    required: bool = False
    default: Any = None
    choices: tuple[Any, ...] = ()
    secret: bool = False
    min_value: float | None = None
    max_value: float | None = None


@dataclass
class ProviderProfile:
    profile_id: str
    kind: ProviderKind
    provider: str
    enabled: bool = True
    values: dict[str, Any] = field(default_factory=dict)

    def copy(self) -> "ProviderProfile":
        return ProviderProfile(
            profile_id=self.profile_id,
            kind=self.kind,
            provider=self.provider,
            enabled=self.enabled,
            values=dict(self.values),
        )


@dataclass(frozen=True)
class ProviderDefinition:
    kind: ProviderKind
    provider: str
    fields: tuple[ProviderField, ...]
    label: str = ""

    def defaults(self) -> dict[str, Any]:
        return {field.key: field.default for field in self.fields if field.default is not None}


@dataclass(frozen=True)
class ProviderValidationIssue:
    profile_id: str
    key: str
    code: str
    message: str
    severity: str = "error"
