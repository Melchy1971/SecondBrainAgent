from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PrivacyMode(str, Enum):
    OFF = "off"
    STRICT = "strict"


class SecretPolicy(str, Enum):
    REDACT = "redact"
    REFERENCE_ONLY = "reference_only"
    BLOCK_EXPORT = "block_export"


class SettingsAuditAction(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    EXPORTED = "exported"
    IMPORTED = "imported"
    PRIVACY_CHANGED = "privacy_changed"


@dataclass(frozen=True)
class SecretReference:
    ref: str

    def __post_init__(self) -> None:
        if not self.ref.startswith("secret://"):
            raise ValueError("secret reference must start with secret://")

    def public_value(self) -> str:
        return self.ref


@dataclass(frozen=True)
class SanitizationResult:
    payload: dict[str, Any]
    redacted_keys: tuple[str, ...] = ()
    blocked_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class SettingsAuditEntry:
    action: SettingsAuditAction
    key: str
    actor: str = "system"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    before: Any = None
    after: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "key": self.key,
            "actor": self.actor,
            "timestamp": self.timestamp.isoformat(),
            "before": self.before,
            "after": self.after,
            "metadata": dict(self.metadata),
        }
