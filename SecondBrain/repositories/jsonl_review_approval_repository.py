"""JSONL-backed review/approval repository (development fallback).

Delegates to the hardened native queues (atomic writes, file locking, backup
and optimistic version/CAS from the concurrency layer) so existing JSONL data
stays fully compatible. Marked *degraded* under a production profile.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from secondbrain.native.approval import (
    ApprovalConcurrencyError,
    ApprovalQueueCorruptionError,
    ExecutionTokenError,
    NativeApprovalQueue,
    REVIEW_CATEGORIES,
    REVIEW_SCHEMA,
    ReviewItem,
    ReviewQueue,
    _FileLock,
    _VALID_REVIEW_TRANSITIONS,
    _sanitize_payload,
    _sanitize_text,
    _stable_id,
    _utc_now,
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
        category = str(fields.get("category") or "").strip().lower()
        if category not in REVIEW_CATEGORIES:
            raise ValueError(f"invalid_review_category:{category}")
        created_at = _utc_now()
        metadata = _sanitize_payload(dict(fields.get("metadata") or {}))
        record = ReviewItem(
            schema=REVIEW_SCHEMA,
            review_id=_stable_id(
                category,
                str(fields.get("title") or ""),
                str(fields.get("source") or ""),
                str(fields.get("target") or ""),
                str(fields.get("approval_id") or ""),
                created_at,
            ),
            created_at=created_at,
            category=category,
            title=_sanitize_text(str(fields.get("title") or "")),
            description=_sanitize_text(str(fields.get("description") or "")),
            source=_sanitize_text(str(fields.get("source") or "")),
            target=_sanitize_text(str(fields.get("target") or "")),
            approval_id=str(fields.get("approval_id") or ""),
            metadata=metadata if isinstance(metadata, dict) else {},
        ).to_dict()
        with _FileLock(self.reviews.path):
            rows = self._read_review_rows(repair=False)
            rows.append(record)
            self._write_review_rows(rows)
        return record

    # -- reads ------------------------------------------------------------

    def get_item(
        self, item_id: str, *, workspace_id: str | None = None
    ) -> dict[str, Any] | None:
        approval = self.queue.get(item_id)
        item = approval if approval is not None else next(
            (row for row in self._read_review_rows() if row.get("review_id") == item_id),
            None,
        )
        if item is not None and workspace_id is not None:
            return item if self._workspace_of(item) == workspace_id else None
        return item

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
            items.extend(dict(row, item_type="review") for row in self._read_review_rows())
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
        if any(row.get("review_id") == item_id for row in self._read_review_rows()):
            return self.reviews
        return None

    def _read_review_rows(self, *, repair: bool = True) -> list[dict[str, Any]]:
        rows = self.reviews._read_all()  # noqa: SLF001
        backup = self.reviews.path.with_name(self.reviews.path.name + ".bak")
        needs_recovery = any(row.get("status") == "invalid_json" for row in rows)
        needs_recovery = needs_recovery or (
            (not self.reviews.path.exists() or not rows)
            and bool(self._parse_review_path(backup))
        )
        if not needs_recovery:
            return rows
        recovered = self._parse_review_path(backup)
        if recovered is None:
            raise ApprovalQueueCorruptionError(
                f"review_queue_backup_corrupt:{self.reviews.path}"
            )
        if repair:
            with _FileLock(self.reviews.path):
                self._write_review_rows(recovered)
        return recovered

    @staticmethod
    def _parse_review_path(path: Path) -> list[dict[str, Any]] | None:
        if not path.exists():
            return None
        try:
            values = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except (OSError, json.JSONDecodeError):
            return None
        if not all(isinstance(value, dict) and value.get("review_id") for value in values):
            return None
        return [ReviewQueue._with_decision_defaults(value) for value in values]  # noqa: SLF001

    def _write_review_rows(self, rows: list[dict[str, Any]]) -> None:
        path = self.reviews.path
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f"{path.name}.{uuid4().hex}.tmp")
        backup = path.with_name(path.name + ".bak")
        backup_tmp = backup.with_name(f"{backup.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            with path.open("rb") as source, backup_tmp.open("wb") as destination:
                shutil.copyfileobj(source, destination)
                destination.flush()
                os.fsync(destination.fileno())
            os.replace(backup_tmp, backup)
        finally:
            temporary.unlink(missing_ok=True)
            backup_tmp.unlink(missing_ok=True)

    def update_status(
        self,
        item_id: str,
        new_status: str,
        *,
        actor: str,
        expected_version: int | None = None,
        note: str = "",
        deferred_until: str = "",
        workspace_id: str | None = None,
    ) -> dict[str, Any] | None:
        target = self._target_queue(item_id)
        if target is None:
            return None
        current = self.get_item(item_id, workspace_id=workspace_id)
        if workspace_id is not None and current is None:
            return None
        try:
            if target is self.queue:
                return self.queue.transition(
                    item_id,
                    new_status,
                    actor=actor,
                    note=note,
                    deferred_until=deferred_until,
                    step_state={
                        "approved": "approved",
                        "rejected": "rejected",
                        "deferred": "deferred",
                    }.get(new_status, ""),
                    expected_version=expected_version,
                )
            return self._transition_review(
                item_id,
                new_status,
                actor=actor,
                note=note,
                deferred_until=deferred_until,
                expected_version=expected_version,
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
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        updated = self.update_status(
            item_id,
            new_status,
            actor=actor,
            expected_version=expected_version,
            note=note,
            deferred_until=deferred_until,
            workspace_id=workspace_id,
        )
        if updated is None:
            raise KeyError(f"review_approval_item_not_found:{item_id}")
        return updated

    # -- audit ------------------------------------------------------------

    def _transition_review(
        self,
        item_id: str,
        new_status: str,
        *,
        actor: str,
        note: str,
        deferred_until: str,
        expected_version: int | None,
    ) -> dict[str, Any] | None:
        actor = actor.strip()
        if not actor:
            raise ValueError("approval_actor_required")
        with _FileLock(self.reviews.path):
            rows = self._read_review_rows(repair=False)
            for row in rows:
                if row.get("review_id") != item_id:
                    continue
                old_status = str(row.get("status") or "pending").strip().lower()
                current_version = int(row.get("version") or 0)
                if expected_version is not None and int(expected_version) != current_version:
                    raise RepositoryConflict(
                        f"review_approval_version_conflict:{item_id}:"
                        f"{expected_version}!={current_version}"
                    )
                if new_status not in _VALID_REVIEW_TRANSITIONS.get(old_status, frozenset()):
                    raise ValueError(f"invalid_review_transition:{old_status}->{new_status}")
                timestamp = _utc_now()
                history = row.get("decision_audit")
                if not isinstance(history, list):
                    history = []
                audit = {
                    "review_id": item_id,
                    "old_status": old_status,
                    "new_status": new_status,
                    "actor": actor,
                    "note": _sanitize_text(note),
                    "timestamp": timestamp,
                }
                row.update(
                    status=new_status,
                    previous_status=old_status,
                    updated_at=timestamp,
                    decision_note=_sanitize_text(note),
                    decided_by=actor,
                    decided_at=timestamp,
                    version=current_version + 1,
                    decision_audit=[*history, audit],
                )
                if new_status == "deferred":
                    row["deferred_until"] = deferred_until
                self._write_review_rows(rows)
                return dict(row)
        return None

    def append_audit_event(
        self,
        item_id: str,
        event: Mapping[str, Any],
        *,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        queue = self._target_queue(item_id)
        if queue is None:
            raise KeyError(f"review_approval_item_not_found:{item_id}")
        if workspace_id is not None and self.get_item(item_id, workspace_id=workspace_id) is None:
            raise KeyError(f"review_approval_item_not_found:{item_id}")
        id_field = "approval_id" if queue is self.queue else "review_id"
        with _FileLock(queue.path):
            rows = (
                queue._read_raw()  # noqa: SLF001 - native repository adapter
                if queue is self.queue
                else self._read_review_rows(repair=False)
            )
            for row in rows:
                if row.get(id_field) == item_id:
                    history = row.get("decision_audit")
                    if not isinstance(history, list):
                        history = []
                    safe_event = _sanitize_payload(dict(event))
                    row["decision_audit"] = [
                        *history,
                        safe_event if isinstance(safe_event, dict) else {},
                    ]
                    if queue is self.queue:
                        queue._write_all(rows)  # noqa: SLF001
                    else:
                        self._write_review_rows(rows)
                    return dict(row)
        raise KeyError(f"review_approval_item_not_found:{item_id}")

    def list_audit_events(
        self, item_id: str, *, workspace_id: str | None = None
    ) -> list[dict[str, Any]]:
        item = self.get_item(item_id, workspace_id=workspace_id)
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
        workspace_id: str | None = None,
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        if self.get_item(item_id, workspace_id=workspace_id) is None:
            raise KeyError(f"review_approval_item_not_found:{item_id}")
        try:
            return self.queue.begin_execution(
                item_id,
                executor_id=executor_id,
                lease_seconds=lease_seconds,
                expected_version=expected_version,
                idempotency_key=idempotency_key,
            )
        except ApprovalConcurrencyError as exc:
            raise RepositoryConflict(str(exc)) from exc

    def renew_execution_lease(
        self,
        item_id: str,
        *,
        execution_token: str,
        lease_seconds: int = 300,
        expected_version: int | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        current = self.get_item(item_id, workspace_id=workspace_id)
        if current is None:
            raise KeyError(f"review_approval_item_not_found:{item_id}")
        if expected_version is not None and int(current.get("version") or 0) != int(expected_version):
            raise RepositoryConflict(f"review_approval_version_conflict:{item_id}")
        try:
            return self.queue.heartbeat_execution(
                item_id,
                lease_id=execution_token,
                lease_seconds=lease_seconds,
            )
        except (ApprovalConcurrencyError, ExecutionTokenError) as exc:
            raise RepositoryConflict(str(exc)) from exc

    def release_execution_lease(
        self,
        item_id: str,
        *,
        execution_token: str,
        result_status: str = "completed",
        expected_version: int | None = None,
        workspace_id: str | None = None,
        result: Any = None,
    ) -> dict[str, Any]:
        if self.get_item(item_id, workspace_id=workspace_id) is None:
            raise KeyError(f"review_approval_item_not_found:{item_id}")
        try:
            return self.queue.complete_execution(
                item_id,
                execution_token=execution_token,
                expected_version=expected_version,
                result_status=result_status,
                result=result,
            )
        except (ApprovalConcurrencyError, ExecutionTokenError) as exc:
            raise RepositoryConflict(str(exc)) from exc

    def recover_stale_leases(
        self, *, now: datetime | None = None
    ) -> list[dict[str, Any]]:
        return self.queue.recover_stale_leases(now=now)

    # -- migration target -------------------------------------------------

    def _import_item(self, item: Mapping[str, Any], events: list[Mapping[str, Any]]) -> dict[str, Any]:
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
        with _FileLock(queue.path):
            rows = (
                queue._read_raw()  # noqa: SLF001
                if queue is self.queue
                else self._read_review_rows(repair=False)
            )
            id_field = "approval_id" if queue is self.queue else "review_id"
            if any(row.get(id_field) == record.get(id_field) for row in rows):
                return next(row for row in rows if row.get(id_field) == record.get(id_field))
            rows.append(record)
            if queue is self.queue:
                queue._write_all(rows)  # noqa: SLF001
            else:
                self._write_review_rows(rows)
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
