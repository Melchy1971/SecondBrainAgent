"""Typed domain events shared by review, approval, and agent components."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, ClassVar, Mapping
from uuid import uuid4


_SENSITIVE_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "client_secret",
    "cookie",
    "credential",
    "credentials",
    "password",
    "passwd",
    "private_key",
    "secret",
    "token",
}
_INLINE_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(bearer)\s+[^\s,;]+"),
    re.compile(r"(?i)\b(password|passwd|token|secret|api[_-]?key)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def sanitize_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a detached, JSON-friendly structure without secret-bearing fields."""

    sanitized = _sanitize_value(dict(metadata or {}))
    return sanitized if isinstance(sanitized, dict) else {}


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for raw_key, item in value.items():
            key = str(raw_key)
            normalized = re.sub(r"[^a-z0-9]", "", key.strip().lower())
            if any(re.sub(r"[^a-z0-9]", "", sensitive) in normalized for sensitive in _SENSITIVE_KEYS):
                continue
            result[key] = _sanitize_value(item)
        return result
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        sanitized = value
        for pattern in _INLINE_SECRET_PATTERNS:
            sanitized = pattern.sub(_redact_match, sanitized)
        return sanitized
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def _redact_match(match: re.Match[str]) -> str:
    prefix = match.group(1) if match.lastindex else ""
    separator = " " if prefix.lower() == "bearer" else "=" if prefix else ""
    return f"{prefix}{separator}***" if prefix else "***"


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Immutable event envelope; subclasses define only their stable event type."""

    EVENT_TYPE: ClassVar[str] = "DomainEvent"

    event_id: str = field(default_factory=lambda: str(uuid4()))
    event_type: str = field(init=False)
    occurred_at: str = field(default_factory=_utc_now)
    workspace_id: str = ""
    actor: str = "system"
    correlation_id: str = ""
    causation_id: str = ""
    item_id: str = ""
    plan_id: str = ""
    step_id: str = ""
    category: str = ""
    sanitized_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_type", self.EVENT_TYPE)
        object.__setattr__(self, "sanitized_metadata", sanitize_metadata(self.sanitized_metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at,
            "workspace_id": self.workspace_id,
            "actor": self.actor,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "item_id": self.item_id,
            "plan_id": self.plan_id,
            "step_id": self.step_id,
            "category": self.category,
            "sanitized_metadata": sanitize_metadata(self.sanitized_metadata),
        }


@dataclass(frozen=True, kw_only=True)
class ApprovalRequested(DomainEvent):
    EVENT_TYPE: ClassVar[str] = "ApprovalRequested"


@dataclass(frozen=True, kw_only=True)
class ApprovalApproved(DomainEvent):
    EVENT_TYPE: ClassVar[str] = "ApprovalApproved"


@dataclass(frozen=True, kw_only=True)
class ApprovalRejected(DomainEvent):
    EVENT_TYPE: ClassVar[str] = "ApprovalRejected"


@dataclass(frozen=True, kw_only=True)
class ApprovalDeferred(DomainEvent):
    EVENT_TYPE: ClassVar[str] = "ApprovalDeferred"


@dataclass(frozen=True, kw_only=True)
class ReviewCreated(DomainEvent):
    EVENT_TYPE: ClassVar[str] = "ReviewCreated"


@dataclass(frozen=True, kw_only=True)
class ReviewResolved(DomainEvent):
    EVENT_TYPE: ClassVar[str] = "ReviewResolved"


@dataclass(frozen=True, kw_only=True)
class AgentPlanPaused(DomainEvent):
    EVENT_TYPE: ClassVar[str] = "AgentPlanPaused"


@dataclass(frozen=True, kw_only=True)
class AgentPlanResumed(DomainEvent):
    EVENT_TYPE: ClassVar[str] = "AgentPlanResumed"


@dataclass(frozen=True, kw_only=True)
class AgentPlanRejected(DomainEvent):
    EVENT_TYPE: ClassVar[str] = "AgentPlanRejected"


EVENT_TYPES: dict[str, type[DomainEvent]] = {
    event_type.EVENT_TYPE: event_type
    for event_type in (
        ApprovalRequested,
        ApprovalApproved,
        ApprovalRejected,
        ApprovalDeferred,
        ReviewCreated,
        ReviewResolved,
        AgentPlanPaused,
        AgentPlanResumed,
        AgentPlanRejected,
    )
}
