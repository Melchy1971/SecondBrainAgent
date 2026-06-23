"""Connector adapter contract and payload validation for SecondBrain.

This module defines the stable boundary between external connector adapters
(Gmail, Drive, local files, future APIs) and the internal sync pipeline.
Adapters should return normalized ``ConnectorItem`` objects only. Raw vendor
payloads must be converted before they enter indexing, audit, or RAG flows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Mapping, Protocol, runtime_checkable


class ConnectorErrorCode(str, Enum):
    """Stable connector error classes used by sync and observability."""

    AUTH_FAILED = "auth_failed"
    RATE_LIMITED = "rate_limited"
    TEMPORARY_UNAVAILABLE = "temporary_unavailable"
    PAYLOAD_INVALID = "payload_invalid"
    UNSUPPORTED_ITEM = "unsupported_item"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN = "unknown"


class ConnectorContractError(ValueError):
    """Raised when a connector payload violates the adapter contract."""

    def __init__(self, message: str, *, code: ConnectorErrorCode = ConnectorErrorCode.PAYLOAD_INVALID) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ConnectorItem:
    """Normalized item emitted by connector adapters.

    Required invariants:
    - ``external_id`` is stable for the source system.
    - ``source`` identifies the adapter, not the vendor payload type.
    - ``title`` and ``content`` are stripped strings.
    - ``updated_at`` is timezone-aware UTC.
    - ``content_hash`` changes when index-relevant text changes.
    """

    external_id: str
    source: str
    title: str
    content: str
    updated_at: datetime
    uri: str | None = None
    mime_type: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    content_hash: str | None = None

    def __post_init__(self) -> None:
        normalized_updated_at = _ensure_utc(self.updated_at)
        object.__setattr__(self, "updated_at", normalized_updated_at)

        title = _clean_text(self.title)
        content = _clean_text(self.content)
        external_id = _clean_text(self.external_id)
        source = _clean_text(self.source).lower()

        if not external_id:
            raise ConnectorContractError("ConnectorItem.external_id must not be empty")
        if not source:
            raise ConnectorContractError("ConnectorItem.source must not be empty")
        if not title and not content:
            raise ConnectorContractError("ConnectorItem requires title or content")

        object.__setattr__(self, "external_id", external_id)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "uri", _clean_optional(self.uri))
        object.__setattr__(self, "mime_type", _clean_optional(self.mime_type))

        if self.content_hash is None:
            object.__setattr__(self, "content_hash", compute_content_hash(title=title, content=content))
        elif not _clean_text(self.content_hash):
            raise ConnectorContractError("ConnectorItem.content_hash must not be blank when provided")


def compute_content_hash(*, title: str, content: str) -> str:
    """Return a deterministic hash for index-relevant item content."""

    payload = f"{_clean_text(title)}\n---\n{_clean_text(content)}".encode("utf-8")
    return sha256(payload).hexdigest()


@runtime_checkable
class ConnectorAdapter(Protocol):
    """Protocol every connector adapter must implement."""

    source: str

    def fetch_changed(self, cursor: str | None = None) -> list[ConnectorItem]:
        """Return changed items since cursor as normalized ConnectorItems."""
        ...


def normalize_item(payload: Mapping[str, Any], *, source: str) -> ConnectorItem:
    """Normalize a generic connector payload into a ``ConnectorItem``.

    Accepted aliases support current and likely adapter outputs without leaking
    vendor-specific field names into the sync pipeline.
    """

    external_id = _first(payload, "external_id", "id", "message_id", "file_id")
    title = _first(payload, "title", "subject", "name", default="")
    content = _first(payload, "content", "body", "text", "snippet", default="")
    updated_at_raw = _first(payload, "updated_at", "modified_at", "timestamp", default=None)

    if updated_at_raw is None:
        updated_at = datetime.now(timezone.utc)
    else:
        updated_at = parse_datetime(updated_at_raw)

    return ConnectorItem(
        external_id=str(external_id or ""),
        source=source,
        title=str(title or ""),
        content=str(content or ""),
        updated_at=updated_at,
        uri=_optional_str(_first(payload, "uri", "url", "web_url", default=None)),
        mime_type=_optional_str(_first(payload, "mime_type", "content_type", default=None)),
        metadata=dict(payload.get("metadata") or {}),
        content_hash=_optional_str(payload.get("content_hash")),
    )


def parse_datetime(value: Any) -> datetime:
    """Parse connector timestamps and normalize them to UTC."""

    if isinstance(value, datetime):
        return _ensure_utc(value)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            raise ConnectorContractError("timestamp must not be blank")
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise ConnectorContractError(f"invalid timestamp: {value!r}") from exc
        return _ensure_utc(parsed)
    raise ConnectorContractError(f"unsupported timestamp type: {type(value).__name__}")


def validate_adapter(adapter: Any) -> ConnectorAdapter:
    """Validate that an adapter implements the connector protocol."""

    if not isinstance(adapter, ConnectorAdapter):
        raise ConnectorContractError(
            "connector adapter must expose 'source' and fetch_changed(cursor=None)",
            code=ConnectorErrorCode.UNSUPPORTED_ITEM,
        )
    source = _clean_text(getattr(adapter, "source", ""))
    if not source:
        raise ConnectorContractError("connector adapter source must not be empty")
    return adapter


def _first(payload: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_optional(value: Any) -> str | None:
    cleaned = _clean_text(value)
    return cleaned or None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
