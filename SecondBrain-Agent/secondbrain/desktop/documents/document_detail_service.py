"""Document detail service."""
from __future__ import annotations

from .document_detail import DocumentDetailViewModel, build_document_detail
from .document_repository import DocumentRepository


class DocumentDetailNotFound(KeyError):
    """Raised when a requested document detail cannot be built."""


class DocumentDetailService:
    """Loads documents from a repository and returns sanitized detail models."""

    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def get_detail(self, document_id: str) -> DocumentDetailViewModel:
        document = self.repository.get(document_id)
        if document is None:
            raise DocumentDetailNotFound(document_id)
        return build_document_detail(document)
