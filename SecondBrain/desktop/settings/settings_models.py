from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class SettingType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    FLOAT = "float"
    CHOICE = "choice"
    SECRET_REF = "secret_ref"


class SettingCategory(str, Enum):
    GENERAL = "general"
    RAG = "rag"
    CONNECTORS = "connectors"
    DESKTOP = "desktop"
    SECURITY = "security"
    ADVANCED = "advanced"


@dataclass(frozen=True)
class SettingDefinition:
    key: str
    category: SettingCategory
    setting_type: SettingType
    default: Any
    label: str
    description: str = ""
    required: bool = False
    choices: tuple[Any, ...] = ()
    min_value: float | None = None
    max_value: float | None = None
    secret: bool = False


@dataclass
class SettingValue:
    key: str
    value: Any
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "user"


@dataclass(frozen=True)
class SettingValidationIssue:
    key: str
    code: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class SettingsSnapshot:
    values: dict[str, Any]
    categories: dict[str, list[str]]
    issues: list[SettingValidationIssue] = field(default_factory=list)
