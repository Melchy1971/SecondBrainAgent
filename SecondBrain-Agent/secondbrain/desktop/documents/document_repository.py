"""In-memory repository for desktop document center."""
from __future__ import annotations

from collections.abc import Iterable

from .models import DesktopDocument


class DocumentRepository:
    def __init__(self, documents: Iterable[DesktopDocument] | None = None) -> None:
        self._documents: dict[str, DesktopDocument] = {}
        for document in documents or ():
            self.save(document)

    def save(self, document: DesktopDocument) -> DesktopDocument:
        if not document.document_id:
            raise ValueError("document_id is required")
        if not document.workspace_id:
            raise ValueError("workspace_id is required")
        self._documents[document.document_id] = document
        return document

    def get(self, document_id: str) -> DesktopDocument | None:
        return self._documents.get(document_id)

    def require(self, document_id: str) -> DesktopDocument:
        document = self.get(document_id)
        if document is None:
            raise KeyError(f"document not found: {document_id}")
        return document

    def delete(self, document_id: str) -> bool:
        return self._documents.pop(document_id, None) is not None

    def list(self) -> list[DesktopDocument]:
        return list(self._documents.values())

    def count(self) -> int:
        return len(self._documents)
