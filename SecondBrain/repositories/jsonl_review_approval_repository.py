"""JSONL-backed review/approval repository (development fallback).

Delegates to the hardened native queues (atomic writes, file locking, backup
and optimistic version/CAS from the concurrency layer) so existing JSONL data
stays fully compatible. Marked *degraded* under a production profile.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from secondbrain.native.approval import (
    ApprovalConcurrencyError,
    ExecutionTokenError,
    NativeApprovalQueue,
    ReviewQueue,
)

from .review_approval_repository import RepositoryConflict, RepositoryHealth

__all__ = ["JsonlReviewApprovalRepository"]


class JsonlReviewApprovalRepository:
    backend = "jsonl"

    def __init__(self, project_root: str | Path = ".", *, production: bool = False) -> None:
        self.queue = NativeApprovalQueue(project_root)
        self.reviews = ReviewQueue(self.queue.project_root)
        self.production = bool(production)

    # -- creation ---------------------------------------------------------

    def create_approval(self, **fields: Any) -> dict[str, Any]:
        return self.queue.create(**fields)

    def create_review(self, **fields: Any) -> dict[str, Any]:
        return self.reviews.create(**fields)

    # -- reads ------------------------------------------------------------

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        approval = self.queue.get(item_id)
        if approval is not None:
            return approval
        return self.reviews.get(item_id)

    def list_items(
        self,
        *,
        item_type: str | None = None,
        status: str | None = None,
        workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        if item_type in (None, "approval"):
            items.extend(dict(row, item_type="approval") for row in self.queue.list())
        if item_type in (None, "review"):
            items.extend(dict(row, item_type="review") for row in self.reviews.list())
        if status is not None:
            items = [row for row in items if str(row.get("status")) == status]
        if workspace_id is not None:
            items = [row for row in items if self._workspace_of(row) == workspace_id]
        return items

    @staticmethod
    def _workspace_of(row: Mapping[str, Any]) -> str:
        workspace = row.get("workspace_id")
        if workspace is None and isinstance(row.get("metadata"), Mapping):
            workspace = row["metadata"].get("workspace_id")
        return str(workspace or "")

    # -- decisions --------------------------------------------------------

    def _target_queue(self, item_id: str):
        if self.queue.get(item_id) is not None:
            return self.queue
        if self.reviews.get(item_id) is not None:
            return self.reviews
        return None

    def update_status(
        self,
        item_id: str,
        new_status: str,
        *,
        actor: str,
        expected_version: int | None = None,
        note: str = "",
        deferred_until: str = "",
    ) -> dict[str, Any] | None:
        target = self._target_queue(item_id)
        if target is None:
            return None
        try:
            if target is self.queue:
                return self.queue.transition(
                    item_id,
                    new_status,
                    actor=actor,
                    note=note,
                    deferred_until=deferred_until,
                    expected_version=expected_version,
                )
            return self.reviews.transition(
                item_id,
                new_status,
                actor=actor,
                note=note,
                deferred_until=deferred_until,
            )
        except ApprovalConcurrencyError as exc:
            raise RepositoryConflict(str(exc)) from exc

    def compare_and_set_status(
        self,
        item_id: str,
        expected_version: int,
        new_status: str,
        *,
        actor: str,
        note: str = "",
        deferred_until: str = "",
    ) -> dict[str, Any]:
        updated = self.update_status(
            item_id,
            new_status,
            actor=actor,
            expected_version=expected_version,
            note=note,
            deferred_until=deferred_until,
        )
        if updated is None:
            raise KeyError(f"review_approval_item_not_found:{item_id}")
        return updated

    # -- audit ------------------------------------------------------------

    def append_audit_event(self, item_id: str, event: Mapping[str, Any]) -> dict[str, Any]:
        queue = self._target_queue(item_id)
        if queue is None:
            raise KeyError(f"review_approval_item_not_found:{item_id}")
        id_field = "approval_id" if queue is self.queue else "review_id"
        rows = queue._read_all()  # noqa: SLF001 - repository adapter over the native queue
        for row in rows:
            if row.get(id_field) == item_id:
                history = row.get("decision_audit")
                if not isinstance(history, list):
                    history = []
                row["decision_audit"] = [*history, dict(event)]
                queue._write_all(rows)  # noqa: SLF001
                return dict(row)
        raise KeyError(f"review_approval_item_not_found:{item_id}")

    def list_audit_events(self, item_id: str) -> list[dict[str, Any]]:
        item = self.get_item(item_id)
        if item is None:
            return []
        history = item.get("decision_audit")
        return list(history) if isinstance(history, list) else []

    # -- execution lease --------------------------------------------------

    def acquire_execution_lease(
        self,
        item_id: str,
        *,
        executor_id: str,
        lease_seconds: int = 300,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        try:
            return self.queue.begin_execution(
                item_id,
                executor_id=executor_id,
                lease_seconds=lease_seconds,
                expected_version=expected_version,
            )
        except ApprovalConcurrencyError as exc:
            raise RepositoryConflict(str(exc)) from exc

    def release_execution_lease(
        self,
        item_id: str,
        *,
        execution_token: str,
        result_status: str = "completed",
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        try:
            return self.queue.complete_execution(
                item_id,
                execution_token=execution_token,
                expected_version=expected_version,
                result_status=result_status,
            )
        except ApprovalConcurrencyError as exc:
            raise RepositoryConflict(str(exc)) from exc

    # -- migration target -------------------------------------------------

    def import_item(self, item: Mapping[str, Any], events: list[Mapping[str, Any]]) -> dict[str, Any]:
        record = dict(item)
        if events:
            record["decision_audit"] = [dict(event) for event in events]
        record.pop("item_type", None)
        if record.get("approval_id"):
            queue = self.queue
        elif record.get("review_id"):
            queue = self.reviews
        else:
            raise ValueError("unimportable_item_without_id")
        rows = queue._read_all()  # noqa: SLF001
        rows.append(record)
        queue._write_all(rows)  # noqa: SLF001
        return record

    # -- health -----------------------------------------------------------

    def health(self) -> RepositoryHealth:
        return RepositoryHealth(
            backend=self.backend,
            healthy=True,
            degraded=True if self.production else False,
            detail=(
                "jsonl backend is not production-grade; configure REVIEW_APPROVAL_BACKEND=postgres"
                if self.production
                else "jsonl development backend"
            ),
        )
