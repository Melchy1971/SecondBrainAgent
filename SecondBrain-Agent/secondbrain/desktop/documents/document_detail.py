"""Document detail view models for the desktop document center.

The detail layer is intentionally presentation-focused. It converts internal
``DesktopDocument`` objects into user-facing fields and removes technical or
sensitive metadata before the GUI renders it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Iterable

from .models import DesktopDocument, DocumentStatus


TECHNICAL_METADATA_KEYS = {
    "id",
    "document_id",
    "workspace_id",
    "owner_user_id",
    "owner_id",
    "user_id",
    "tenant_id",
    "internal_id",
    "trace_id",
    "correlation_id",
    "embedding_id",
    "vector_id",
    "chunk_id",
}

SENSITIVE_KEY_PARTS = (
    "secret",
    "token",
    "password",
    "passwd",
    "api_key",
    "apikey",
    "credential",
    "authorization",
)


@dataclass(frozen=True)
class DocumentDetailField:
    """Single user-facing field in the document detail view."""

    label: str
    value: str
    group: str = "details"


@dataclass(frozen=True)
class DocumentDetailViewModel:
    """Presentation model for a document detail screen.

    ``technical_reference`` is kept separate for internal routing/logging. It is
    not part of ``fields`` and should not be rendered as a visible detail row.
    """

    title: str
    status: str
    fields: tuple[DocumentDetailField, ...]
    tags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, str] = field(default_factory=dict)
    technical_reference: str | None = None

    def visible_labels(self) -> tuple[str, ...]:
        return tuple(field.label for field in self.fields)


def _format_datetime(value: datetime) -> str:
    return value.astimezone().strftime("%Y-%m-%d %H:%M")


def _format_status(status: DocumentStatus | str) -> str:
    raw = status.value if isinstance(status, DocumentStatus) else str(status)
    return raw.replace("_", " ").title()


def _is_hidden_metadata_key(key: str) -> bool:
    normalized = key.strip().lower()
    if not normalized:
        return True
    if normalized in TECHNICAL_METADATA_KEYS:
        return True
    if normalized.endswith("_id") or normalized.endswith("id") and normalized != "valid":
        return True
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def sanitize_metadata(metadata: dict[str, Any], *, max_value_length: int = 240) -> dict[str, str]:
    """Return metadata safe for display in the GUI.

    Hidden dependencies:
    - Internal identifiers remain available on the document object, but are not
      exposed as visible detail fields.
    - Secrets and token-like keys are dropped by key name. Values are never
      scanned heuristically to avoid false positives and unnecessary data leaks
      through logs/tests.
    """

    sanitized: dict[str, str] = {}
    for key, value in sorted(metadata.items(), key=lambda item: str(item[0]).lower()):
        display_key = str(key).strip()
        if _is_hidden_metadata_key(display_key):
            continue
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        if len(text) > max_value_length:
            text = text[: max_value_length - 1] + "…"
        sanitized[display_key] = text
    return sanitized


def build_document_detail(document: DesktopDocument, *, include_groups: Iterable[str] | None = None) -> DocumentDetailViewModel:
    """Build a user-facing detail model for ``document``.

    The function deliberately excludes ``document_id`` and ``workspace_id`` from
    visible fields. They are implementation details and caused prior release
    risks when shown in metadata cards.
    """

    allowed_groups = set(include_groups) if include_groups else None
    fields = (
        DocumentDetailField("Titel", document.title, "summary"),
        DocumentDetailField("Status", _format_status(document.status), "summary"),
        DocumentDetailField("Quelle", document.source, "summary"),
        DocumentDetailField("Erstellt", _format_datetime(document.created_at), "timeline"),
        DocumentDetailField("Aktualisiert", _format_datetime(document.updated_at), "timeline"),
    )
    if allowed_groups is not None:
        fields = tuple(field for field in fields if field.group in allowed_groups)

    return DocumentDetailViewModel(
        title=document.title,
        status=_format_status(document.status),
        fields=fields,
        tags=tuple(document.tags),
        metadata=sanitize_metadata(document.metadata),
        technical_reference=document.document_id,
    )
