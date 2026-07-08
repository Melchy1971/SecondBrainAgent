"""Bulk operations for document center."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .document_repository import DocumentRepository
from .models import DocumentStatus


class DocumentActionType(str, Enum):
    REINDEX = "REINDEX"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    MOVE_WORKSPACE = "MOVE_WORKSPACE"
    ADD_TAGS = "ADD_TAGS"
    REMOVE_TAGS = "REMOVE_TAGS"
    EXPORT_METADATA = "EXPORT_METADATA"


@dataclass(frozen=True)
class DocumentActionResult:
    action: DocumentActionType
    affected: int
    failed: dict[str, str]
    payload: dict[str, Any]


class DocumentActionExecutor:
    def __init__(self, repository: DocumentRepository) -> None:
        self.repository = repository

    def execute(self, action: DocumentActionType, document_ids: list[str], **kwargs: Any) -> DocumentActionResult:
        failed: dict[str, str] = {}
        affected = 0
        exported: list[dict[str, Any]] = []
        for document_id in document_ids:
            try:
                document = self.repository.require(document_id)
                if action == DocumentActionType.DELETE:
                    self.repository.delete(document_id)
                elif action == DocumentActionType.ARCHIVE:
                    self.repository.save(document.with_update(status=DocumentStatus.ARCHIVED))
                elif action == DocumentActionType.REINDEX:
                    self.repository.save(document.with_update(status=DocumentStatus.INDEXING))
                elif action == DocumentActionType.MOVE_WORKSPACE:
                    workspace_id = kwargs.get("workspace_id")
                    if not workspace_id:
                        raise ValueError("workspace_id is required")
                    self.repository.save(document.with_update(workspace_id=workspace_id))
                elif action == DocumentActionType.ADD_TAGS:
                    tags = tuple(document.tags) + tuple(kwargs.get("tags", ()))
                    self.repository.save(document.with_update(tags=tags))
                elif action == DocumentActionType.REMOVE_TAGS:
                    remove = set(kwargs.get("tags", ()))
                    self.repository.save(document.with_update(tags=tuple(t for t in document.tags if t not in remove)))
                elif action == DocumentActionType.EXPORT_METADATA:
                    exported.append(document.to_dict())
                else:
                    raise ValueError(f"unsupported action: {action}")
                affected += 1
            except Exception as exc:  # deliberate bulk isolation
                failed[document_id] = str(exc)
        return DocumentActionResult(action=action, affected=affected, failed=failed, payload={"documents": exported})
