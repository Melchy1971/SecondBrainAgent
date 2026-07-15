"""Persistence and concurrency contract for the integrated task repository."""

from __future__ import annotations

import json
import pytest

from secondbrain.tasks.service import TaskProjectService, VersionConflict
from secondbrain.tasks.repository import (
    PostgresTaskRepository, TaskRepositoryError, create_task_repository, migrate_jsonl_to_repository,
)
from secondbrain.storage.db_executor import SqliteExecutor


def test_repository_persists_and_isolates_workspaces(tmp_path):
    service = TaskProjectService(tmp_path)
    task = service.create_task(workspace_id="alpha", title="Persisted")
    service.create_task(workspace_id="beta", title="Private")

    restarted = TaskProjectService(tmp_path)
    assert restarted.get_task(task.task_id, workspace_id="alpha") is not None
    assert restarted.get_task(task.task_id, workspace_id="beta") is None
    assert [item.title for item in restarted.list_tasks(workspace_id="beta")] == ["Private"]


def test_task_optimistic_version_prevents_lost_update(tmp_path):
    service = TaskProjectService(tmp_path)
    task = service.create_task(workspace_id="alpha", title="Initial")
    updated = service.update_task(task.task_id, workspace_id="alpha", title="First", expected_version=1)
    assert updated.version == 2

    with pytest.raises(VersionConflict):
        service.update_task(task.task_id, workspace_id="alpha", title="Stale", expected_version=1)


def test_project_optimistic_version_prevents_lost_update(tmp_path):
    service = TaskProjectService(tmp_path)
    project = service.create_project(workspace_id="alpha", title="Project")
    updated = service.update_project(project.project_id, workspace_id="alpha", title="Current", expected_version=1)
    assert updated.version == 2

    with pytest.raises(VersionConflict):
        service.update_project(project.project_id, workspace_id="alpha", title="Stale", expected_version=1)


def test_postgres_repository_persists_and_isolates_workspaces(tmp_path):
    executor = SqliteExecutor(":memory:")
    repository = PostgresTaskRepository(executor)
    repository.ensure_schema()
    service = TaskProjectService(tmp_path, repository=repository)
    mine = service.create_task(workspace_id="alpha", title="Mine")
    service.create_task(workspace_id="beta", title="Other")
    restarted = TaskProjectService(tmp_path, repository=repository)
    assert restarted.get_task(mine.task_id, workspace_id="alpha").title == "Mine"
    assert restarted.get_task(mine.task_id, workspace_id="beta") is None


def test_postgres_repository_rejects_stale_concurrent_write():
    repository = PostgresTaskRepository(SqliteExecutor(":memory:"))
    repository.ensure_schema()
    service_a = TaskProjectService(repository=repository)
    service_b = TaskProjectService(repository=repository)
    task = service_a.create_task(workspace_id="alpha", title="Initial")
    stale = service_b.get_task(task.task_id, workspace_id="alpha")
    service_a.update_task(task.task_id, workspace_id="alpha", title="Winner", expected_version=1)
    with pytest.raises(VersionConflict):
        service_b.update_task(stale.task_id, workspace_id="alpha", title="Loser", expected_version=1)


def test_production_refuses_jsonl_and_missing_database_url(tmp_path):
    with pytest.raises(TaskRepositoryError, match="jsonl_not_allowed"):
        create_task_repository(env={"SECONDBRAIN_ENV": "production", "TASK_REPOSITORY_BACKEND": "jsonl"})
    with pytest.raises(TaskRepositoryError, match="requires_database_url"):
        create_task_repository(env={"SECONDBRAIN_ENV": "production"})


def test_migration_dry_run_detects_duplicates_without_writing(tmp_path):
    service = TaskProjectService(tmp_path, env={"SECONDBRAIN_ENV": "development"})
    task = service.create_task(workspace_id="alpha", title="One")
    path = tmp_path / "runtime" / "tasks" / "tasks.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + json.dumps(task.to_dict()) + "\n", encoding="utf-8")
    repository = PostgresTaskRepository(SqliteExecutor(":memory:"))
    repository.ensure_schema()
    report = migrate_jsonl_to_repository(tmp_path, repository, dry_run=True)
    assert report["status"] == "blocked" and report["duplicates"]
    assert repository.read("tasks") == []


def test_migration_apply_preserves_ids_and_events(tmp_path):
    source = TaskProjectService(tmp_path, env={"SECONDBRAIN_ENV": "development"})
    task = source.create_task(workspace_id="alpha", title="Migrated", actor="tester")
    repository = PostgresTaskRepository(SqliteExecutor(":memory:"))
    repository.ensure_schema()
    report = migrate_jsonl_to_repository(tmp_path, repository, dry_run=False)
    assert report["status"] == "ready"
    migrated = TaskProjectService(tmp_path, repository=repository)
    assert migrated.get_task(task.task_id, workspace_id="alpha").title == "Migrated"
    assert repository.read("events")[0]["task_id"] == task.task_id
