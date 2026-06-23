from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class UiSeverity(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    BLOCKED = "blocked"

class UiStateKind(str, Enum):
    EMPTY = "empty"
    LOADING = "loading"
    ERROR = "error"
    WARNING = "warning"
    READY = "ready"

@dataclass(frozen=True)
class AccessibilityHint:
    label: str
    role: str = "status"
    description: str = ""
    keyboard_shortcut: str | None = None
    live_region: str = "polite"

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "role": self.role,
            "description": self.description,
            "keyboard_shortcut": self.keyboard_shortcut,
            "live_region": self.live_region,
        }

@dataclass(frozen=True)
class UiState:
    kind: UiStateKind
    severity: UiSeverity
    title: str
    message: str
    recovery_action: str | None = None
    technical_detail: str | None = None
    hint: AccessibilityHint | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_blocking(self) -> bool:
        return self.severity in {UiSeverity.ERROR, UiSeverity.BLOCKED}

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "recovery_action": self.recovery_action,
            "technical_detail": self.technical_detail,
            "hint": self.hint.to_dict() if self.hint else None,
            "metadata": dict(self.metadata),
        }
