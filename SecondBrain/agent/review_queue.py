from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ReviewCategory(StrEnum):
    LOW_CONFIDENCE_CLASSIFICATION = "low_confidence_classification"
    SENSITIVE_DOCUMENT = "sensitive_document"
    FAILED_IMPORT = "failed_import"
    RISKY_AGENT_ACTION = "risky_agent_action"
    CONNECTOR_PERMISSION_CHANGE = "connector_permission_change"
    DELETE_REQUEST = "delete_request"


class QueueStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass(frozen=True, slots=True)
class ReviewItem:
    item_id: str
    category: ReviewCategory
    title: str
    reason: str
    payload: dict[str, Any]
    status: QueueStatus = QueueStatus.PENDING
    workspace_id: str | None = None
    created_at: str = field(default_factory=_utc_now)
    updated_at: str | None = None
    decided_by: str | None = None
    decision_note: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["category"] = self.category.value
        value["status"] = self.status.value
        return value


@dataclass(frozen=True, slots=True)
class ApprovalItem(ReviewItem):
    plan_id: str = ""
    step_id: str = ""
    tool_name: str = ""
    risk_level: str = "high"


class ReviewApprovalQueue:
    """Durable queue with atomic snapshots and append-only decision audit."""

    def __init__(self, runtime_dir: str | Path) -> None:
        self.root = Path(runtime_dir).resolve() / "review_approval"
        self.items_file = self.root / "items.json"
        self.audit_file = self.root / "decisions.jsonl"
        self._lock = threading.RLock()
        self.root.mkdir(parents=True, exist_ok=True)

    def create_review(
        self,
        *,
        category: ReviewCategory | str,
        title: str,
        reason: str,
        payload: dict[str, Any] | None = None,
        workspace_id: str | None = None,
    ) -> ReviewItem:
        item = ReviewItem(
            item_id=str(uuid4()),
            category=ReviewCategory(category),
            title=title,
            reason=reason,
            payload=dict(payload or {}),
            workspace_id=workspace_id,
        )
        self._append(item)
        return item

    def create_approval(
        self,
        *,
        category: ReviewCategory | str,
        title: str,
        reason: str,
        plan_id: str,
        step_id: str,
        tool_name: str,
        payload: dict[str, Any] | None = None,
        risk_level: str = "high",
        workspace_id: str | None = None,
    ) -> ApprovalItem:
        item = ApprovalItem(
            item_id=str(uuid4()),
            category=ReviewCategory(category),
            title=title,
            reason=reason,
            payload=dict(payload or {}),
            workspace_id=workspace_id,
            plan_id=plan_id,
            step_id=step_id,
            tool_name=tool_name,
            risk_level=risk_level,
        )
        self._append(item)
        return item

    def list(self, *, status: QueueStatus | str | None = None) -> list[dict[str, Any]]:
        rows = self._read_all()
        if status is not None:
            expected = QueueStatus(status).value
            rows = [row for row in rows if row.get("status") == expected]
        return sorted(rows, key=lambda row: str(row.get("created_at", "")), reverse=True)

    def get(self, item_id: str) -> dict[str, Any] | None:
        return next((row for row in self._read_all() if row.get("item_id") == item_id), None)

    def decide(
        self,
        item_id: str,
        decision: QueueStatus | str,
        *,
        actor: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        target = QueueStatus(decision)
        if target not in {QueueStatus.APPROVED, QueueStatus.REJECTED, QueueStatus.DEFERRED}:
            raise ValueError(f"invalid_queue_decision:{target.value}")
        with self._lock:
            rows = self._read_all_unlocked()
            match = next((row for row in rows if row.get("item_id") == item_id), None)
            if match is None:
                raise KeyError(f"queue_item_not_found:{item_id}")
            if match.get("status") not in {QueueStatus.PENDING.value, QueueStatus.DEFERRED.value}:
                raise ValueError(f"queue_item_already_decided:{item_id}:{match.get('status')}")
            match["status"] = target.value
            match["updated_at"] = _utc_now()
            match["decided_by"] = actor
            match["decision_note"] = note
            self._write_all_unlocked(rows)
            self._append_audit_unlocked(match, target)
            return dict(match)

    def approve(self, item_id: str, *, actor: str, note: str | None = None) -> dict[str, Any]:
        return self.decide(item_id, QueueStatus.APPROVED, actor=actor, note=note)

    def reject(self, item_id: str, *, actor: str, note: str | None = None) -> dict[str, Any]:
        return self.decide(item_id, QueueStatus.REJECTED, actor=actor, note=note)

    def defer(self, item_id: str, *, actor: str, note: str | None = None) -> dict[str, Any]:
        return self.decide(item_id, QueueStatus.DEFERRED, actor=actor, note=note)

    def _append(self, item: ReviewItem) -> None:
        with self._lock:
            rows = self._read_all_unlocked()
            rows.append(item.to_dict())
            self._write_all_unlocked(rows)

    def _read_all(self) -> list[dict[str, Any]]:
        with self._lock:
            return self._read_all_unlocked()

    def _read_all_unlocked(self) -> list[dict[str, Any]]:
        if not self.items_file.exists():
            return []
        try:
            value = json.loads(self.items_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError("review_queue_corrupt") from exc
        return [dict(row) for row in value] if isinstance(value, list) else []

    def _write_all_unlocked(self, rows: Iterable[dict[str, Any]]) -> None:
        temporary = self.items_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(list(rows), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        temporary.replace(self.items_file)

    def _append_audit_unlocked(self, item: dict[str, Any], decision: QueueStatus) -> None:
        record = {
            "event": "queue_decision",
            "item_id": item.get("item_id"),
            "category": item.get("category"),
            "decision": decision.value,
            "actor": item.get("decided_by"),
            "note": item.get("decision_note"),
            "timestamp": item.get("updated_at"),
            "plan_id": item.get("plan_id"),
            "step_id": item.get("step_id"),
            "tool_name": item.get("tool_name"),
        }
        with self.audit_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
