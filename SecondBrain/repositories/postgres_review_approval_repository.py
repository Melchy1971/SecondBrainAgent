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
from contextlib import contextmanager
from typing import Any, Mapping

from secondbrain.native.approval import (
    APPROVAL_SCHEMA,
    REVIEW_SCHEMA,
    ApprovalRequest,
    ReviewItem,
    _risk_is_idempotent,
    _result_hash,
    _sanitize_payload,
    _sanitize_text,
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
        workspace_id TEXT NOT NULL,
        approval_id TEXT,
        plan_id TEXT,
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
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_ra_audit_seq ON review_approval_audit(item_id, seq)",
]


class PostgresReviewApprovalRepository:
    backend = "postgres"

    def __init__(self, executor: Any) -> None:
        self.executor = executor
        self.dialect = getattr(executor, "dialect", "postgresql")

    def ensure_schema(self) -> None:
        with self._transaction() as tx:
            for statement in _SCHEMA:
                tx.execute(statement)
            if self.dialect not in {"sqlite", ""}:
                tx.execute(
                    "ALTER TABLE review_approval_items ADD COLUMN IF NOT EXISTS approval_id TEXT"
                )
                tx.execute(
                    "ALTER TABLE review_approval_items ADD COLUMN IF NOT EXISTS plan_id TEXT"
                )
                tx.execute(
                    "UPDATE review_approval_items SET workspace_id = 'legacy' "
                    "WHERE workspace_id IS NULL OR workspace_id = ''"
                )
                tx.execute(
                    "ALTER TABLE review_approval_items ALTER COLUMN workspace_id SET NOT NULL"
                )
            tx.execute(
                "CREATE INDEX IF NOT EXISTS idx_ra_approval ON review_approval_items(approval_id)"
            )
            tx.execute(
                "CREATE INDEX IF NOT EXISTS idx_ra_plan ON review_approval_items(plan_id)"
            )

    @contextmanager
    def _transaction(self):
        """Keep row locks and mutations on the same production DB session."""

        database = getattr(self.executor, "database", None)
        if database is None:
            with self.executor.transaction() as tx:
                yield tx
            return

        from sqlalchemy import text  # pragma: no cover - production dependency

        class _SessionExecutor:
            def __init__(self, session: Any) -> None:
                self.session = session

            def execute(self, sql: str, params: Mapping[str, Any] | None = None):
                result = self.session.execute(text(sql), dict(params or {}))
                return [tuple(row) for row in result.fetchall()] if result.returns_rows else []

        with database.session() as session:  # pragma: no cover - production dependency
            yield _SessionExecutor(session)

    @staticmethod
    def _require_workspace(workspace_id: str | None) -> str:
        workspace = str(workspace_id or "").strip()
        if not workspace:
            raise ValueError("review_approval_workspace_id_required")
        return workspace

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
        idempotency_key: str = "",
        tool_idempotent: bool | None = None,
    ) -> dict[str, Any]:
        workspace = self._require_workspace(workspace_id)
        created_at = _utc_now()
        approval_id = _stable_id(command, intent, text, target, created_at)
        extra: dict[str, Any] = {}
        if risk_level is not None:
            extra["risk_level"] = risk_level
        if reason is not None:
            extra["reason"] = _sanitize_text(reason)
        record = ApprovalRequest(
            schema=APPROVAL_SCHEMA,
            approval_id=approval_id,
            created_at=created_at,
            command=command,
            intent=_sanitize_text(intent),
            text=_sanitize_text(text),
            target=_sanitize_text(target),
            category=category,
            plan_id=plan_id,
            step_id=step_id,
            tool_name=tool_name,
            payload=_sanitize_payload(dict(payload or {})),
            workspace_id=workspace,
            step_state=step_state,
            review_id=review_id,
            idempotency_key=idempotency_key or _stable_id("approval", approval_id),
            tool_idempotent=(
                _risk_is_idempotent(risk_level if risk_level is not None else "write")
                if tool_idempotent is None
                else bool(tool_idempotent)
            ),
            **extra,
        ).to_dict()
        try:
            self._insert(record, item_type="approval")
        except Exception as exc:
            message = str(exc).lower()
            if "unique" in message or "duplicate" in message:
                raise RepositoryConflict(
                    f"review_approval_idempotency_conflict:{record['idempotency_key']}"
                ) from exc
            raise
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
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        safe_metadata = _sanitize_payload(dict(metadata or {}))
        workspace = self._require_workspace(
            workspace_id or str(safe_metadata.get("workspace_id") or "")
        )
        safe_metadata["workspace_id"] = workspace
        created_at = _utc_now()
        review_id = _stable_id(category, title, source, target, approval_id, created_at)
        record = ReviewItem(
            schema=REVIEW_SCHEMA,
            review_id=review_id,
            created_at=created_at,
            category=category.strip().lower(),
            title=_sanitize_text(title),
            description=_sanitize_text(description),
            source=_sanitize_text(source),
            target=_sanitize_text(target),
            approval_id=approval_id,
            metadata=safe_metadata,
        ).to_dict()
        self._insert(record, item_type="review")
        return record

    def _insert(self, record: Mapping[str, Any], *, item_type: str) -> None:
        with self._transaction() as tx:
            self._insert_tx(tx, record, item_type=item_type)

    def _insert_tx(self, tx: Any, record: Mapping[str, Any], *, item_type: str) -> None:
        item_id = str(record.get("approval_id") or record.get("review_id"))
        workspace = str(record.get("workspace_id") or (record.get("metadata") or {}).get("workspace_id") or "")
        workspace = self._require_workspace(workspace)
        idem = str(record.get("idempotency_key") or "") or None
        approval_id = str(record.get("approval_id") or "") or None
        plan_id = str(record.get("plan_id") or "") or None
        tx.execute(
            """
            INSERT INTO review_approval_items
                (id, item_type, status, category, workspace_id, approval_id, plan_id,
                 version, idempotency_key, created_at, data)
            VALUES
                (:id, :item_type, :status, :category, :workspace_id, :approval_id, :plan_id,
                 :version, :idempotency_key, :created_at, :data)
            """,
            {
                "id": item_id,
                "item_type": item_type,
                "status": str(record.get("status") or "pending"),
                "category": str(record.get("category") or ""),
                "workspace_id": workspace,
                "approval_id": approval_id,
                "plan_id": plan_id,
                "version": int(record.get("version") or 0),
                "idempotency_key": idem,
                "created_at": str(record.get("created_at") or _utc_now()),
                "data": json.dumps(dict(record), ensure_ascii=False),
            },
        )

    # -- reads ------------------------------------------------------------

    def get_item(
        self, item_id: str, *, workspace_id: str | None = None
    ) -> dict[str, Any] | None:
        where = "id = :id"
        params: dict[str, Any] = {"id": item_id}
        if workspace_id is not None:
            where += " AND workspace_id = :workspace_id"
            params["workspace_id"] = workspace_id
        rows = self.executor.execute(
            f"SELECT data, status, version FROM review_approval_items WHERE {where}",
            params,
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
        workspace_id: str | None = None,
    ) -> dict[str, Any] | None:
        actor = actor.strip()
        if not actor:
            raise ValueError("approval_actor_required")
        new_status = new_status.strip().lower()
        lock = " FOR UPDATE" if self.dialect not in {"sqlite", ""} else ""
        with self._transaction() as tx:
            workspace_clause = ""
            select_params: dict[str, Any] = {"id": item_id}
            if workspace_id is not None:
                workspace_clause = " AND workspace_id = :workspace_id"
                select_params["workspace_id"] = workspace_id
            rows = tx.execute(
                f"SELECT data, status, version, item_type FROM review_approval_items "
                f"WHERE id = :id{workspace_clause}{lock}",
                select_params,
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
                "note": _sanitize_text(note),
                "timestamp": timestamp,
            }
            data.update(
                status=new_status,
                previous_status=old_status,
                updated_at=timestamp,
                decision_note=_sanitize_text(note),
                decided_by=actor,
                decided_at=timestamp,
                version=new_version,
                decision_audit=[*history, event],
            )
            if new_status == "deferred":
                data["deferred_until"] = deferred_until
            data["step_state"] = {
                "approved": "approved",
                "rejected": "rejected",
                "deferred": "deferred",
            }.get(new_status, str(data.get("step_state") or ""))
            tx.execute(
                "UPDATE review_approval_items SET status = :status, version = :version, data = :data "
                "WHERE id = :id AND version = :old_version",
                {"status": new_status, "version": new_version, "old_version": current_version,
                 "data": json.dumps(data, ensure_ascii=False), "id": item_id},
            )
            self._append_audit_tx(tx, item_id, event, timestamp)
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

    @staticmethod
    def _append_audit_tx(
        tx: Any, item_id: str, event: Mapping[str, Any], created_at: str
    ) -> None:
        seq_rows = tx.execute(
            "SELECT COALESCE(MAX(seq), 0) FROM review_approval_audit WHERE item_id = :id",
            {"id": item_id},
        )
        seq = int(seq_rows[0][0]) + 1 if seq_rows else 1
        tx.execute(
            """
            INSERT INTO review_approval_audit (id, item_id, seq, event, created_at)
            VALUES (:id, :item_id, :seq, :event, :created_at)
            """,
            {
                "id": uuid.uuid4().hex,
                "item_id": item_id,
                "seq": seq,
                "event": json.dumps(_sanitize_payload(dict(event)), ensure_ascii=False),
                "created_at": created_at,
            },
        )

    def append_audit_event(
        self,
        item_id: str,
        event: Mapping[str, Any],
        *,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        with self._transaction() as tx:
            workspace_clause = ""
            params: dict[str, Any] = {"id": item_id}
            if workspace_id is not None:
                workspace_clause = " AND workspace_id = :workspace_id"
                params["workspace_id"] = workspace_id
            lock = " FOR UPDATE" if self.dialect not in {"sqlite", ""} else ""
            rows = tx.execute(
                "SELECT id FROM review_approval_items "
                f"WHERE id = :id{workspace_clause}{lock}",
                params,
            )
            if not rows:
                raise KeyError(f"review_approval_item_not_found:{item_id}")
            self._append_audit_tx(tx, item_id, event, _utc_now())
        safe_event = _sanitize_payload(dict(event))
        return safe_event if isinstance(safe_event, dict) else {}

    def list_audit_events(
        self, item_id: str, *, workspace_id: str | None = None
    ) -> list[dict[str, Any]]:
        if self.get_item(item_id, workspace_id=workspace_id) is None:
            return []
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
        workspace_id: str | None = None,
        idempotency_key: str = "",
    ) -> dict[str, Any]:
        executor_id = executor_id.strip() or "executor"
        lock = " FOR UPDATE" if self.dialect not in {"sqlite", ""} else ""
        with self._transaction() as tx:
            workspace_clause = ""
            params: dict[str, Any] = {"id": item_id}
            if workspace_id is not None:
                workspace_clause = " AND workspace_id = :workspace_id"
                params["workspace_id"] = workspace_id
            rows = tx.execute(
                f"SELECT data, status, version FROM review_approval_items "
                f"WHERE id = :id{workspace_clause}{lock}",
                params,
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
            if data.get("consumed_at") or data.get("execution_result_hash"):
                raise RepositoryConflict(f"review_approval_already_consumed:{item_id}")
            stored_key = str(data.get("idempotency_key") or "")
            if idempotency_key and stored_key and idempotency_key != stored_key:
                raise RepositoryConflict(f"idempotency_key_mismatch:{item_id}")
            token = uuid.uuid4().hex
            timestamp = _utc_now()
            lease = (datetime.now(timezone.utc) + timedelta(seconds=max(1, int(lease_seconds)))).isoformat(timespec="seconds")
            new_version = current_version + 1
            data.update(
                status="executing",
                previous_status=old_status,
                updated_at=timestamp,
                lease_id=token,
                owner=executor_id,
                acquired_at=timestamp,
                expires_at=lease,
                heartbeat_at=timestamp,
                execution_token=token,
                executor_id=executor_id,
                lease_expires_at=lease,
                version=new_version,
            )
            tx.execute(
                "UPDATE review_approval_items SET status = :status, version = :version, data = :data "
                "WHERE id = :id AND version = :old_version",
                {"status": "executing", "version": new_version, "old_version": current_version,
                 "data": json.dumps(data, ensure_ascii=False), "id": item_id},
            )
            self._append_audit_tx(
                tx,
                item_id,
                {"approval_id": item_id, "old_status": old_status,
                 "new_status": "executing", "actor": executor_id,
                 "note": "execution_lease_acquired", "timestamp": timestamp},
                timestamp,
            )
            return data

    def renew_execution_lease(
        self,
        item_id: str,
        *,
        execution_token: str,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
        expected_version: int | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        lock = " FOR UPDATE" if self.dialect not in {"sqlite", ""} else ""
        with self._transaction() as tx:
            workspace_clause = ""
            params: dict[str, Any] = {"id": item_id}
            if workspace_id is not None:
                workspace_clause = " AND workspace_id = :workspace_id"
                params["workspace_id"] = workspace_id
            rows = tx.execute(
                f"SELECT data, status, version FROM review_approval_items "
                f"WHERE id = :id{workspace_clause}{lock}",
                params,
            )
            if not rows:
                raise KeyError(f"review_approval_item_not_found:{item_id}")
            data = json.loads(rows[0][0])
            current_version = int(rows[0][2])
            if expected_version is not None and int(expected_version) != current_version:
                raise RepositoryConflict(f"review_approval_version_conflict:{item_id}")
            if str(rows[0][1]) != "executing" or str(data.get("lease_id") or "") != execution_token:
                raise RepositoryConflict(f"execution_token_mismatch:{item_id}")
            timestamp = _utc_now()
            expires_at = (
                datetime.now(timezone.utc) + timedelta(seconds=max(1, int(lease_seconds)))
            ).isoformat(timespec="seconds")
            new_version = current_version + 1
            data.update(
                heartbeat_at=timestamp,
                expires_at=expires_at,
                lease_expires_at=expires_at,
                updated_at=timestamp,
                version=new_version,
            )
            tx.execute(
                "UPDATE review_approval_items SET version = :version, data = :data "
                "WHERE id = :id AND version = :old_version",
                {"version": new_version, "old_version": current_version,
                 "data": json.dumps(data, ensure_ascii=False), "id": item_id},
            )
            return data

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
        result_status = result_status if result_status in {"completed", "executed", "failed"} else "completed"
        lock = " FOR UPDATE" if self.dialect not in {"sqlite", ""} else ""
        with self._transaction() as tx:
            workspace_clause = ""
            params: dict[str, Any] = {"id": item_id}
            if workspace_id is not None:
                workspace_clause = " AND workspace_id = :workspace_id"
                params["workspace_id"] = workspace_id
            rows = tx.execute(
                f"SELECT data, status, version FROM review_approval_items "
                f"WHERE id = :id{workspace_clause}{lock}",
                params,
            )
            if not rows:
                raise KeyError(f"review_approval_item_not_found:{item_id}")
            data = json.loads(rows[0][0])
            if str(rows[0][1]) != "executing":
                raise RepositoryConflict(f"review_approval_not_executing:{item_id}")
            if str(data.get("execution_token") or "") != execution_token:
                raise RepositoryConflict(f"execution_token_mismatch:{item_id}")
            current_version = int(rows[0][2])
            if expected_version is not None and int(expected_version) != current_version:
                raise RepositoryConflict(f"review_approval_version_conflict:{item_id}")
            new_version = current_version + 1
            timestamp = _utc_now()
            data.update(
                status=result_status,
                previous_status="executing",
                updated_at=timestamp,
                consumed_at=timestamp,
                execution_result_hash=_result_hash({"status": result_status, "result": result}),
                lease_id="",
                owner="",
                expires_at="",
                heartbeat_at="",
                execution_token="",
                lease_expires_at="",
                version=new_version,
            )
            tx.execute(
                "UPDATE review_approval_items SET status = :status, version = :version, data = :data "
                "WHERE id = :id AND version = :old_version",
                {"status": result_status, "version": new_version, "old_version": current_version,
                 "data": json.dumps(data, ensure_ascii=False), "id": item_id},
            )
            self._append_audit_tx(
                tx,
                item_id,
                {"approval_id": item_id, "old_status": "executing",
                 "new_status": result_status,
                 "actor": str(data.get("executor_id") or "executor"),
                 "note": "execution_completed", "timestamp": timestamp},
                timestamp,
            )
            return data

    # -- migration target -------------------------------------------------

    def _import_item(self, item: Mapping[str, Any], events: list[Mapping[str, Any]]) -> dict[str, Any]:
        record = dict(item)
        workspace = str(
            record.get("workspace_id")
            or (record.get("metadata") or {}).get("workspace_id")
            or "legacy"
        )
        if record.get("approval_id"):
            record["workspace_id"] = workspace
        else:
            metadata = dict(record.get("metadata") or {})
            metadata["workspace_id"] = workspace
            record["metadata"] = metadata
        if events:
            record["decision_audit"] = [dict(event) for event in events]
        item_type = str(record.pop("item_type", "") or ("approval" if record.get("approval_id") else "review"))
        item_id = str(record.get("approval_id") or record.get("review_id"))
        with self._transaction() as tx:
            self._insert_tx(tx, record, item_type=item_type)
            for event in events:
                self._append_audit_tx(
                    tx,
                    item_id,
                    event,
                    str(event.get("timestamp") or _utc_now()),
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
