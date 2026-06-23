"""Application service for desktop document center."""
from __future__ import annotations

from .document_actions import DocumentActionExecutor, DocumentActionResult, DocumentActionType
from .document_events import DocumentEvent, DocumentEventBus, DocumentEventType
from .document_filters import DocumentFilter, apply_document_filter
from .document_repository import DocumentRepository
from .document_selection import DocumentSelection
from .models import DesktopDocument, DocumentStatus


class DocumentService:
    def __init__(self, repository: DocumentRepository | None = None, event_bus: DocumentEventBus | None = None) -> None:
        self.repository = repository or DocumentRepository()
        self.event_bus = event_bus or DocumentEventBus()
        self.selection = DocumentSelection()
        self.actions = DocumentActionExecutor(self.repository)

    def add_document(self, document: DesktopDocument) -> DesktopDocument:
        saved = self.repository.save(document)
        self.event_bus.publish(DocumentEvent(DocumentEventType.DOCUMENT_ADDED, saved.document_id, saved.to_dict()))
        return saved

    def update_status(self, document_id: str, status: DocumentStatus) -> DesktopDocument:
        document = self.repository.require(document_id).with_update(status=status)
        self.repository.save(document)
        self.event_bus.publish(DocumentEvent(DocumentEventType.DOCUMENT_UPDATED, document_id, {"status": status.value}))
        return document

    def list_documents(self, document_filter: DocumentFilter | None = None) -> list[DesktopDocument]:
        documents = self.repository.list()
        return apply_document_filter(documents, document_filter or DocumentFilter())

    def select(self, document_id: str) -> None:
        self.repository.require(document_id)
        self.selection.select(document_id)
        self.event_bus.publish(DocumentEvent(DocumentEventType.DOCUMENT_SELECTED, document_id))

    def bulk_execute(self, action: DocumentActionType, document_ids: list[str] | None = None, **kwargs) -> DocumentActionResult:
        ids = document_ids if document_ids is not None else self.selection.to_list()
        result = self.actions.execute(action, list(ids), **kwargs)
        event_type = DocumentEventType.DOCUMENT_REINDEXED if action == DocumentActionType.REINDEX else DocumentEventType.BULK_ACTION_EXECUTED
        self.event_bus.publish(DocumentEvent(event_type, payload={"action": action.value, "affected": result.affected, "failed": result.failed}))
        return result
