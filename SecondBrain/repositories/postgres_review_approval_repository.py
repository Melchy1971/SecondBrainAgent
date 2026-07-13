"""PostgreSQL-grade review/approval repository.

Uses parametrized SQL exclusively (named ``:param`` placeholders), an explicit
version column for optimistic compare-and-set, per-workspace isolation, unique
idempotency keys and indices on status/category/workspace/created_at. Row
locking (``SELECT ... FOR UPDATE``) is applied on PostgreSQL; the same SQL runs
against a SQLite test database (which serializes writes) for development tests.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, Mapping

from secondbrain.native.approval import (
    APPROVAL_SCHEMA,
    REVIEW_SCHEMA,
    ApprovalRequest,
    ReviewItem,
    _risk_is_idempotent,
    _stable_id,
    _utc_now,
    _VALID_APPROVAL_TRANSITIONS,
    _VALID_REVIEW_TRANSITIONS,
    DEFAULT_LEASE_SECONDS,
)
from datetime import datetime, timedelta, timezone

from .review_approval_repository import RepositoryConflict, RepositoryHealth

__all__ = ["PostgresReviewApprovalRepository"]

_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS review_approval_items (
        id TEXT PRIMARY KEY,
        item_type TEXT NOT NULL,
        status TEXT NOT NULL,
        category TEXT,
        workspace_id TEXT,
        version INTEGER NOT NULL DEFAULT 0,
        idempotency_key TEXT,
        created_at TEXT NOT NULL,
        data TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_ra_status ON review_approval_items(status)",
    "CREATE INDEX IF NOT EXISTS idx_ra_category ON review_approval_items(category)",
    "CREATE INDEX IF NOT EXISTS idx_ra_workspace ON review_approval_items(workspace_id)",
    "CREATE INDEX IF NOT EXISTS idx_ra_created ON review_approval_items(created_at)",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_ra_idem ON review_approval_items(idempotency_key)",
    """
    CREATE TABLE IF NOT EXISTS review_approval_audit (
        id TEXT PRIMARY KEY,
        item_id TEXT NOT NULL,
        seq INTEGER NOT NULL,
        event TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_ra_audit_item ON review_approval_audit(item_id)",
]


class PostgresReviewApprovalRepository:
    backend = "postgres"

    def __init__(self, executor: Any) -> None:
        self.executor = executor
        self.dialect = getattr(executor, "dialect", "postgresql")

    def ensure_schema(self) -> None:
        with self.executor.transaction() as tx:
            for statement in _SCHEMA:
                tx.execute(statement)

    # -- creation ---------------------------------------------------------

    def create_approval(
        self,
        *,
        command: str,
        intent: str,
        text: str,
        target: str = "",
        risk_level: str | None = None,
        reason: str | None = None,
        category: str = "risky_agent_action",
        plan_id: str = "",
        step_id: str = "",
        tool_name: str = "",
        payload: Mapping[str, Any] | None = None,
        workspace_id: str | None = None,
        step_state: str = "",
        review_id: str = "",
    ) -> dict[str, Any]:
        created_at = _utc_now()
        approval_id = _stable_id(command, intent, text, target, created_at)
        extra: dict[str, Any] = {}
        if risk_level is not None:
            extra["risk_level"] = risk_level
        if reason is not None:
            extra["reason"] = reason
        record = ApprovalRequest(
            schema=APPROVAL_SCHEMA,
            approval_id=approval_id,
            created_at=created_at,
            command=command,
            intent=intent,
            text=text,
            target=target,
            category=category,
            plan_id=plan_id,
            step_id=step_id,
            tool_name=tool_name,
            payload=dict(payload or {}),
            workspace_id=workspace_id,
            step_state=step_state,
            review_id=review_id,
            idempotency_key=_stable_id(command, intent, text, target),
            tool_idempotent=_risk_is_idempotent(risk_level if risk_level is not None else "write"),
            **extra,
        ).to_dict()
        self._insert(record, item_type="approval")
        return record

    def create_review(
        self,
        *,
        category: str,
        title: str,
        description: str = "",
        source: str = "",
        target: str = "",
        approval_id: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        created_at = _utc_now()
        review_id = _stable_id(category, title, source, target, approval_id, created_at)
        record = ReviewItem(
            schema=REVIEW_SCHEMA,
            review_id=review_id,
            created_at=created_at,
            category=category.strip().lower(),
            title=title,
            description=description,
            source=source,
            target=target,
            approval_id=approval_id,
            metadata=dict(metadata or {}),
        ).to_dict()
        self._insert(record, item_type="review")
        return record

    def _insert(self, record: Mapping[str, Any], *, item_type: str) -> None:
        item_id = str(record.get("approval_id") or record.get("review_id"))
        workspace = str(record.get("workspace_id") or (record.get("metadata") or {}).get("workspace_id") or "")
        idem = str(record.get("idempotency_key") or "") or None
        self.executor.execute(
            """
            INSERT INTO review_approval_items
                (id, item_type, status, category, workspace_id, version, idempotency_key, created_at, data)
            VALUES
                (:id, :item_type, :status, :category, :workspace_id, :version, :idempotency_key, :created_at, :data)
            """,
            {
                "id": item_id,
                "item_type": item_type,
                "status": str(record.get("status") or "pending"),
                "category": str(record.get("category") or ""),
                "workspace_id": workspace,
                "version": int(record.get("version") or 0),
                "idempotency_key": idem,
                "created_at": str(record.get("created_at") or _utc_now()),
                "data": json.dumps(dict(record), ensure_ascii=False),
            },
        )

    # -- reads ------------------------------------------------------------

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        rows = self.executor.execute(
            "SELECT data, status, version FROM review_approval_items WHERE id = :id",
            {"id": item_id},
        )
        if not rows:
            return None
        return self._materialize(rows[0])

    def list_items(
        self,
        *,
        item_type: str | None = None,
        status: str | None = None,
        workspace_id: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses = []
        params: dict[str, Any] = {}
        if item_type is not None:
            clauses.append("item_type = :item_type")
            params["item_type"] = item_type
        if status is not None:
            clauses.append("status = :status")
            params["status"] = status
        if workspace_id is not None:
            clauses.append("workspace_id = :workspace_id")
            params["workspace_id"] = workspace_id
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self.executor.execute(
            f"SELECT data, status, version FROM review_approval_items{where} ORDER BY created_at",
            params,
        )
        return [self._materialize(row) for row in rows]

    @staticmethod
    def _materialize(row: Any) -> dict[str, Any]:
        data = json.loads(row[0])
        data["status"] = row[1]
        data["version"] = int(row[2])
        return data

    # -- decisions --------------------------------------------------------

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
        actor = actor.strip()
        if not actor:
            raise ValueError("approval_actor_required")
        new_status = new_status.strip().lower()
        lock = " FOR UPDATE" if self.dialect not in {"sqlite", ""} else ""
        with self.executor.transaction() as tx:
            rows = tx.execute(
                f"SELECT data, status, version, item_type FROM review_approval_items WHERE id = :id{lock}",
                {"id": item_id},
            )
            if not rows:
                return None
            data = json.loads(rows[0][0])
            old_status = str(rows[0][1] or "pending").strip().lower()
            current_version = int(rows[0][2])
            item_type = str(rows[0][3])
            if expected_version is not None and int(expected_version) != current_version:
                raise RepositoryConflict(
                    f"review_approval_version_conflict:{item_id}:{expected_version}!={current_version}"
                )
            allowed_map = _VALID_APPROVAL_TRANSITIONS if item_type == "approval" else _VALID_REVIEW_TRANSITIONS
            if new_status not in allowed_map.get(old_status, frozenset()):
                raise ValueError(f"invalid_{item_type}_transition:{old_status}->{new_status}")
            timestamp = _utc_now()
            new_version = current_version + 1
            history = data.get("decision_audit")
            if not isinstance(history, list):
                history = []
            event = {
                "id": item_id,
                "old_status": old_status,
                "new_status": new_status,
                "actor": actor,
                "note": note,
                "timestamp": timestamp,
            }
            data.update(
                status=new_status,
                decision_note=note,
                decided_by=actor,
                decided_at=timestamp,
                version=new_version,
                decision_audit=[*history, event],
            )
            if new_status == "deferred":
                data["deferred_until"] = deferred_until
            tx.execute(
                "UPDATE review_approval_items SET status = :status, version = :version, data = :data WHERE id = :id",
                {"status": new_status, "version": new_version, "data": json.dumps(data, ensure_ascii=False), "id": item_id},
            )
            return data

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
        existing = self.list_audit_events(item_id)
        seq = len(existing) + 1
        self.executor.execute(
            """
            INSERT INTO review_approval_audit (id, item_id, seq, event, created_at)
            VALUES (:id, :item_id, :seq, :event, :created_at)
            """,
            {
                "id": uuid.uuid4().hex,
                "item_id": item_id,
                "seq": seq,
                "event": json.dumps(dict(event), ensure_ascii=False),
                "created_at": _utc_now(),
            },
        )
        return dict(event)

    def list_audit_events(self, item_id: str) -> list[dict[str, Any]]:
        rows = self.executor.execute(
            "SELECT event FROM review_approval_audit WHERE item_id = :id ORDER BY seq",
            {"id": item_id},
        )
        events = [json.loads(row[0]) for row in rows]
        if events:
            return events
        item = self.get_item(item_id)
        history = (item or {}).get("decision_audit")
        return list(history) if isinstance(history, list) else []

    # -- execution lease --------------------------------------------------

    def acquire_execution_lease(
        self,
        item_id: str,
        *,
        executor_id: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        executor_id = executor_id.strip() or "executor"
        lock = " FOR UPDATE" if self.dialect not in {"sqlite", ""} else ""
        with self.executor.transaction() as tx:
            rows = tx.execute(
                f"SELECT data, status, version FROM review_approval_items WHERE id = :id{lock}",
                {"id": item_id},
            )
            if not rows:
                raise KeyError(f"review_approval_item_not_found:{item_id}")
            data = json.loads(rows[0][0])
            old_status = str(rows[0][1] or "").strip().lower()
            current_version = int(rows[0][2])
            if expected_version is not None and int(expected_version) != current_version:
                raise RepositoryConflict(f"review_approval_version_conflict:{item_id}")
            if old_status not in {"approved", "recovery_required"}:
                raise RepositoryConflict(f"review_approval_not_executable:{item_id}:{old_status}")
            token = uuid.uuid4().hex
            lease = (datetime.now(timezone.utc) + timedelta(seconds=max(1, int(lease_seconds)))).isoformat(timespec="seconds")
            new_version = current_version + 1
            data.update(status="executing", execution_token=token, executor_id=executor_id, lease_expires_at=lease, version=new_version)
            tx.execute(
                "UPDATE review_approval_items SET status = :status, version = :version, data = :data WHERE id = :id",
                {"status": "executing", "version": new_version, "data": json.dumps(data, ensure_ascii=False), "id": item_id},
            )
            return data

    def release_execution_lease(
        self,
        item_id: str,
        *,
        execution_token: str,
        result_status: str = "completed",
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        result_status = result_status if result_status in {"completed", "executed", "failed"} else "completed"
        lock = " FOR UPDATE" if self.dialect not in {"sqlite", ""} else ""
        with self.executor.transaction() as tx:
            rows = tx.execute(
                f"SELECT data, status, version FROM review_approval_items WHERE id = :id{lock}",
                {"id": item_id},
            )
            if not rows:
                raise KeyError(f"review_approval_item_not_found:{item_id}")
            data = json.loads(rows[0][0])
            if str(rows[0][1]) != "executing":
                raise RepositoryConflict(f"review_approval_not_executing:{item_id}")
            if str(data.get("execution_token") or "") != execution_token:
                raise RepositoryConflict(f"execution_token_mismatch:{item_id}")
            current_version = int(rows[0][2])
            new_version = current_version + 1
            data.update(status=result_status, execution_token="", lease_expires_at="", version=new_version)
            tx.execute(
                "UPDATE review_approval_items SET status = :status, version = :version, data = :data WHERE id = :id",
                {"status": result_status, "version": new_version, "data": json.dumps(data, ensure_ascii=False), "id": item_id},
            )
            return data

    # -- migration target -------------------------------------------------

    def import_item(self, item: Mapping[str, Any], events: list[Mapping[str, Any]]) -> dict[str, Any]:
        record = dict(item)
        if events:
            record["decision_audit"] = [dict(event) for event in events]
        item_type = str(record.pop("item_type", "") or ("approval" if record.get("approval_id") else "review"))
        self._insert(record, item_type=item_type)
        for index, event in enumerate(events, start=1):
            self.executor.execute(
                """
                INSERT INTO review_approval_audit (id, item_id, seq, event, created_at)
                VALUES (:id, :item_id, :seq, :event, :created_at)
                """,
                {
                    "id": uuid.uuid4().hex,
                    "item_id": str(record.get("approval_id") or record.get("review_id")),
                    "seq": index,
                    "event": json.dumps(dict(event), ensure_ascii=False),
                    "created_at": _utc_now(),
                },
            )
        return record

    # -- health -----------------------------------------------------------

    def health(self) -> RepositoryHealth:
        healthy = True
        try:
            healthy = bool(self.executor.ping())
        except Exception:  # noqa: BLE001
            healthy = False
        return RepositoryHealth(
            backend=self.backend,
            healthy=healthy,
            degraded=False,
            detail=f"dialect={self.dialect}",
        )
