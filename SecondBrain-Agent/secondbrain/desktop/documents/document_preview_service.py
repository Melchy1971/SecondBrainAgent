"""Repository-backed document preview service."""
from __future__ import annotations

from .document_preview import DocumentPreviewViewModel, build_document_preview
from .document_repository import DocumentRepository


class DocumentPreviewNotFoundError(LookupError):
    """Raised when a preview is requested for an unknown document."""


class DocumentPreviewService:
    def __init__(self, repository: DocumentRepository) -> None:
        self.repository = repository

    def get_preview(self, document_id: str, *, max_chars: int = 2000, max_lines: int = 80) -> DocumentPreviewViewModel:
        document = self.repository.get(document_id)
        if document is None:
            raise DocumentPreviewNotFoundError(f"document not found: {document_id}")
        return build_document_preview(document, max_chars=max_chars, max_lines=max_lines)
