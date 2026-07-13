"""Filtering and sorting model for document lists."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .models import DesktopDocument, DocumentStatus


class DocumentSortField(str, Enum):
    TITLE = "title"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"
    SOURCE = "source"


@dataclass(frozen=True)
class DocumentFilter:
    workspace_id: str | None = None
    statuses: tuple[DocumentStatus, ...] = field(default_factory=tuple)
    tags: tuple[str, ...] = field(default_factory=tuple)
    source: str | None = None
    text: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    sort_by: DocumentSortField = DocumentSortField.UPDATED_AT
    descending: bool = True

    def matches(self, document: DesktopDocument) -> bool:
        if self.workspace_id and document.workspace_id != self.workspace_id:
            return False
        if self.statuses and document.status not in self.statuses:
            return False
        if self.source and document.source != self.source:
            return False
        if self.tags and not set(self.tags).issubset(set(document.tags)):
            return False
        if self.created_from and document.created_at < self.created_from:
            return False
        if self.created_to and document.created_at > self.created_to:
            return False
        if self.text:
            haystack = " ".join([
                document.title,
                document.source,
                " ".join(document.tags),
                " ".join(str(v) for v in document.metadata.values()),
            ]).lower()
            if self.text.lower() not in haystack:
                return False
        return True


def apply_document_filter(documents: list[DesktopDocument], document_filter: DocumentFilter) -> list[DesktopDocument]:
    filtered = [document for document in documents if document_filter.matches(document)]
    key_name = document_filter.sort_by.value
    return sorted(filtered, key=lambda doc: getattr(doc, key_name), reverse=document_filter.descending)
