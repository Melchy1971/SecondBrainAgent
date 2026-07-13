"""Prompt 15 - persistent repository abstraction for review/approval.

Acceptance coverage:
  1. Services work over the repository interface.
  2. JSONL behaviour stays compatible.
  3. The PostgreSQL repository runs against a test database.
  4. Compare-and-set prevents parallel conflicts.
  5. Workspace isolation works.
  6. Migration preserves ids and decisions.
  7. Production health marks JSONL as degraded.
"""

from __future__ import annotations

from contextlib import contextmanager

import pytest

from secondbrain.agent.approval_service import AgentApprovalService
from secondbrain.repositories.jsonl_review_approval_repository import JsonlReviewApprovalRepository
from secondbrain.repositories.postgres_review_approval_repository import PostgresReviewApprovalRepository
from secondbrain.repositories.review_approval_repository import (
    RepositoryConflict,
    RepositoryUnavailable,
    create_review_approval_repository,
    migrate_repository,
    resolve_backend,
)
from secondbrain.storage.db_executor import SqliteExecutor


def _pg_repo() -> PostgresReviewApprovalRepository:
    repo = PostgresReviewApprovalRepository(SqliteExecutor(":memory:"))
    repo.ensure_schema()
    return repo


def _delete(repo, **extra):
    return repo.create_approval(
        command="records.delete",
        intent="delete_record",
        text="Delete 1",
        category="delete_request",
        risk_level="high",
        **extra,
    )


# -- 1 ---------------------------------------------------------------------

def test_service_operates_over_repository(tmp_path):
    repo = JsonlReviewApprovalRepository(tmp_path)
    service = AgentApprovalService(repository=repo)
    approval = _delete(repo, workspace_id="w1")

    result = service.approve(approval["approval_id"], "markus")

    assert result["status"] == "approved"
    assert service.health()["backend"] == "jsonl"
    assert repo.get_item(approval["approval_id"])["status"] == "approved"


# -- 2 ---------------------------------------------------------------------

def test_jsonl_repository_stays_compatible(tmp_path):
    repo = JsonlReviewApprovalRepository(tmp_path)
    approval = _delete(repo, workspace_id="w1")
    approval_id = approval["approval_id"]

    assert approval["version"] == 0
    updated = repo.update_status(approval_id, "approved", actor="markus")
    assert updated["version"] == 1
    assert updated["decision_audit"]
    assert repo.list_items(item_type="approval", status="approved")[0]["approval_id"] == approval_id


# -- 3 ---------------------------------------------------------------------

def test_postgres_repository_runs_on_test_db():
    repo = _pg_repo()
    approval = _delete(repo, workspace_id="w1")
    approval_id = approval["approval_id"]

    assert repo.get_item(approval_id)["status"] == "pending"
    repo.compare_and_set_status(approval_id, 0, "approved", actor="markus")
    assert repo.get_item(approval_id)["status"] == "approved"
    lease = repo.acquire_execution_lease(approval_id, executor_id="w", lease_seconds=60)
    done = repo.release_execution_lease(approval_id, execution_token=lease["execution_token"])
    assert done["status"] == "completed"


# -- 4 ---------------------------------------------------------------------

@pytest.mark.parametrize("factory", ["jsonl", "postgres"])
def test_compare_and_set_prevents_conflict(tmp_path, factory):
    repo = JsonlReviewApprovalRepository(tmp_path) if factory == "jsonl" else _pg_repo()
    approval_id = _delete(repo, workspace_id="w1")["approval_id"]
    repo.compare_and_set_status(approval_id, 0, "approved", actor="markus")

    with pytest.raises(RepositoryConflict):
        repo.compare_and_set_status(approval_id, 0, "executing", actor="markus")


# -- 5 ---------------------------------------------------------------------

def test_workspace_isolation():
    repo = _pg_repo()

    def mk(text, ws):
        return repo.create_approval(command="records.delete", intent="delete", text=text, category="delete_request", risk_level="high", workspace_id=ws)

    mk("Del A", "w1")
    mk("Del B", "w2")
    mk("Del C", "w2")

    assert len(repo.list_items(workspace_id="w1")) == 1
    assert len(repo.list_items(workspace_id="w2")) == 2
    assert all(item["workspace_id"] == "w2" for item in repo.list_items(workspace_id="w2"))


# -- 6 ---------------------------------------------------------------------

def test_migration_preserves_ids_and_decisions(tmp_path):
    source = JsonlReviewApprovalRepository(tmp_path)
    a1 = _delete(source, workspace_id="w1")
    review = source.create_review(category="sensitive_document", title="S", source="c")
    source.update_status(a1["approval_id"], "approved", actor="markus", note="ok")

    target = _pg_repo()
    dry = migrate_repository(source, target, dry_run=True)
    assert dry["imported_count"] == 2
    assert target.get_item(a1["approval_id"]) is None  # dry run wrote nothing

    report = migrate_repository(source, target)
    assert set(report["imported"]) == {a1["approval_id"], review["review_id"]}
    migrated = target.get_item(a1["approval_id"])
    assert migrated["status"] == "approved"
    assert migrated["version"] == 1
    assert target.list_audit_events(a1["approval_id"])  # decision history preserved

    # Re-running is idempotent (duplicates skipped).
    again = migrate_repository(source, target)
    assert again["imported_count"] == 0
    assert again["skipped_count"] == 2


# -- 7 ---------------------------------------------------------------------

def test_production_health_marks_jsonl_degraded(tmp_path):
    dev = JsonlReviewApprovalRepository(tmp_path, production=False)
    prod = JsonlReviewApprovalRepository(tmp_path, production=True)

    assert dev.health().degraded is False
    assert prod.health().degraded is True
    assert prod.health().healthy is True  # still usable, just not production-grade


def test_postgres_backend_has_no_silent_fallback(tmp_path):
    with pytest.raises(RepositoryUnavailable):
        create_review_approval_repository(tmp_path, env={"REVIEW_APPROVAL_BACKEND": "postgres"})

    repo = create_review_approval_repository(
        tmp_path,
        env={"REVIEW_APPROVAL_BACKEND": "postgres"},
        executor=SqliteExecutor(":memory:"),
    )
    assert repo.backend == "postgres"

    jsonl = create_review_approval_repository(tmp_path, env={"REVIEW_APPROVAL_BACKEND": "jsonl"})
    assert jsonl.backend == "jsonl"


def test_resolve_backend_rejects_unknown():
    assert resolve_backend({"REVIEW_APPROVAL_BACKEND": "jsonl"}) == "jsonl"
    with pytest.raises(RepositoryUnavailable):
        resolve_backend({"REVIEW_APPROVAL_BACKEND": "mysql"})


# -- parametrized SQL only -------------------------------------------------

class _CapturingExecutor:
    dialect = "postgresql"

    def __init__(self):
        self.calls: list[tuple[str, object]] = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        return []

    @contextmanager
    def transaction(self):
        yield self

    def ping(self):
        return True


def test_postgres_repository_uses_parametrized_sql():
    executor = _CapturingExecutor()
    repo = PostgresReviewApprovalRepository(executor)
    repo.ensure_schema()
    repo.create_approval(
        command="records.delete",
        intent="delete",
        text="Del",
        category="delete_request",
        risk_level="high",
        workspace_id="w-secret",
    )

    insert_calls = [(sql, params) for sql, params in executor.calls if "INSERT INTO review_approval_items" in sql]
    assert insert_calls
    sql, params = insert_calls[0]
    assert isinstance(params, dict)
    assert ":id" in sql and ":data" in sql
    # Values are bound, never interpolated into the SQL text.
    assert "w-secret" not in sql
