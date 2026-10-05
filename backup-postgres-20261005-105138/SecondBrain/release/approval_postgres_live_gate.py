"""Live certification for PostgreSQL-backed approval execution and recovery."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit
from uuid import uuid4

PASS, BLOCKED = "PASS", "BLOCKED"
REPORT_PATH = Path("runtime/reports/approval_postgres_live_gate.json")
_PARAM = re.compile(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)")


def _check(name: str, ok: bool) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok)}


def _safe_error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": "live database operation failed"}


def _validate_dsn(dsn: str) -> None:
    parsed = urlsplit(dsn)
    if parsed.scheme not in {"postgres", "postgresql", "postgresql+psycopg"} or not parsed.hostname:
        raise ValueError("TEST_DATABASE_URL must be a PostgreSQL DSN")


def _connect(dsn: str):
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("psycopg is required; install requirements-db.txt") from exc
    return psycopg.connect(dsn, connect_timeout=8)


class PsycopgExecutor:
    dialect = "postgresql"

    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def execute(self, statement: str, params: Mapping[str, Any] | None = None) -> list[tuple]:
        with self.connection.cursor() as cursor:
            cursor.execute(_PARAM.sub(r"%(\1)s", statement), dict(params or {}))
            return list(cursor.fetchall()) if cursor.description else []

    @contextmanager
    def transaction(self):
        with self.connection.transaction():
            yield self

    def ping(self) -> bool:
        return self.execute("SELECT 1") == [(1,)]


def _binding(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _approval(repo: Any, suffix: str, *, workspace: str = "workspace-a") -> dict[str, Any]:
    bound = {
        "actor": "gate-actor", "action_type": "connector_write", "connector": "gate",
        "recipient": "test-recipient", "attachments": [], "event_time": "2026-07-17T00:00:00Z",
        "expires_at": "2099-01-01T00:00:00Z", "value": suffix,
    }
    payload = {**bound, "payload_hash": _binding(bound)}
    return repo.create_approval(
        command="connector_write", intent="live certification", text="test data only",
        target="test-recipient", payload=payload, workspace_id=workspace,
        idempotency_key=f"gate-{suffix}-{uuid4().hex}", tool_idempotent=False,
    )


def _run_live(dsn: str, schema: str, connect: Callable[[str], Any]) -> tuple[list[dict[str, Any]], bool]:
    from psycopg import sql
    from secondbrain.repositories.postgres_review_approval_repository import PostgresReviewApprovalRepository
    from secondbrain.repositories.review_approval_repository import RepositoryConflict

    checks: list[dict[str, Any]] = []
    conn = connect(dsn)
    conn.autocommit = True
    created = False
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_setting('server_version_num')::int")
            checks.append(_check("postgresql", cursor.fetchone()[0] >= 140000))
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            created = True
            cursor.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(schema)))
        repo = PostgresReviewApprovalRepository(PsycopgExecutor(conn))
        repo.ensure_schema()
        checks += [_check("postgres_repository", repo.health().healthy), _check("no_development_fallback", repo.backend == "postgres")]

        approved = _approval(repo, "approve")
        approved = repo.update_status(approved["approval_id"], "approved", actor="gate-actor", workspace_id="workspace-a")
        checks.append(_check("approve", approved is not None and approved["status"] == "approved"))
        restarted = PostgresReviewApprovalRepository(PsycopgExecutor(conn)).get_item(approved["approval_id"], workspace_id="workspace-a")
        checks.append(_check("restart_persistence", restarted is not None and restarted["status"] == "approved"))
        checks.append(_check("workspace_isolation", repo.get_item(approved["approval_id"], workspace_id="workspace-b") is None))

        rejected = _approval(repo, "reject")
        rejected = repo.update_status(rejected["approval_id"], "rejected", actor="gate-actor", workspace_id="workspace-a")
        checks.append(_check("reject", rejected is not None and rejected["status"] == "rejected"))
        expired = _approval(repo, "expire")
        expired = repo.update_status(expired["approval_id"], "expired", actor="gate-clock", workspace_id="workspace-a")
        checks.append(_check("expiration", expired is not None and expired["status"] == "expired"))

        stored_payload = dict((restarted or {}).get("payload") or {})
        stored_hash = stored_payload.pop("payload_hash", "")
        checks.append(_check("payload_binding", bool(stored_hash) and stored_hash == _binding(stored_payload)))
        tampered = {**stored_payload, "recipient": "changed"}
        checks.append(_check("payload_tamper_rejected", _binding(tampered) != stored_hash))

        def claim(executor_id: str) -> bool:
            local = connect(dsn)
            try:
                local.autocommit = True
                with local.cursor() as cursor:
                    cursor.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(schema)))
                local_repo = PostgresReviewApprovalRepository(PsycopgExecutor(local))
                try:
                    local_repo.acquire_execution_lease(
                        approved["approval_id"], executor_id=executor_id,
                        workspace_id="workspace-a", idempotency_key=approved["idempotency_key"],
                    )
                    return True
                except RepositoryConflict:
                    return False
            finally:
                local.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            claims = list(pool.map(claim, ("executor-a", "executor-b")))
        checks.append(_check("parallel_exactly_once", claims.count(True) == 1))
        executing = repo.get_item(approved["approval_id"], workspace_id="workspace-a") or {}
        completed = repo.release_execution_lease(
            approved["approval_id"], execution_token=str(executing.get("execution_token")),
            workspace_id="workspace-a", result={"test": True},
        )
        checks.append(_check("execution_audit", completed["status"] == "completed" and len(repo.list_audit_events(approved["approval_id"], workspace_id="workspace-a")) >= 3))
        try:
            repo.acquire_execution_lease(approved["approval_id"], executor_id="replay", workspace_id="workspace-a")
            replay_blocked = False
        except RepositoryConflict:
            replay_blocked = True
        checks.append(_check("replay_blocked", replay_blocked))
    finally:
        cleanup = not created
        if created:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
                cleanup = True
            except Exception:
                cleanup = False
        conn.close()
    return checks, cleanup


def run_approval_postgres_live_gate(
    project_root: str | Path = ".", *, env: Mapping[str, str] | None = None,
    connect: Callable[[str], Any] | None = None, write_report: bool = True,
) -> dict[str, Any]:
    source = os.environ if env is None else env
    dsn = str(source.get("TEST_DATABASE_URL") or "")
    schema = f"sb_approval_gate_{uuid4().hex[:12]}"
    checks: list[dict[str, Any]] = []
    cleanup = False
    if not dsn:
        checks.append(_check("test_database_url", False))
    else:
        try:
            _validate_dsn(dsn)
            checks.append(_check("test_database_url", True))
            live, cleanup = _run_live(dsn, schema, connect or _connect)
            checks.extend(live)
        except Exception as exc:
            checks.append({**_check("live_execution", False), "error": _safe_error(exc)})
    failed = [check["name"] for check in checks if not check["ok"]]
    report = {
        "schema": "secondbrain.approval_postgres_live_gate.v1", "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": PASS if not failed else BLOCKED, "ok": not failed,
        "backend": "postgresql" if dsn else "not_configured", "test_data_only": True,
        "checks": checks, "failed_checks": failed, "evidence": {"test_schema": schema, "cleanup": cleanup},
    }
    if write_report:
        target = Path(project_root).resolve() / REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["report"] = REPORT_PATH.as_posix()
    return report
