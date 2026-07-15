"""Persistence backends and migration tooling for task/project records."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol


class TaskRepositoryError(RuntimeError):
    pass


class TaskRepositoryConflict(TaskRepositoryError):
    pass


class TaskRepository(Protocol):
    backend: str
    def read(self, collection: str) -> list[dict[str, Any]]: ...
    def write(self, collection: str, rows: Iterable[dict[str, Any]]) -> None: ...
    def append(self, collection: str, row: dict[str, Any]) -> None: ...


_ID_FIELDS = {
    "projects": "project_id", "tasks": "task_id", "dependencies": "dependency_id", "events": "event_id",
}

_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS task_project_records (
        collection TEXT NOT NULL, record_id TEXT NOT NULL, workspace_id TEXT NOT NULL,
        version INTEGER NOT NULL DEFAULT 1, data TEXT NOT NULL,
        PRIMARY KEY (collection, record_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_task_records_workspace ON task_project_records(workspace_id, collection)",
)


class PostgresTaskRepository:
    backend = "postgres"

    def __init__(self, executor: Any) -> None:
        self.executor = executor
        self.dialect = getattr(executor, "dialect", "postgresql")

    def ensure_schema(self) -> None:
        with self._transaction() as tx:
            for statement in _SCHEMA:
                tx.execute(statement)

    def read(self, collection: str) -> list[dict[str, Any]]:
        self._validate_collection(collection)
        rows = self.executor.execute(
            "SELECT data FROM task_project_records WHERE collection = :collection ORDER BY record_id",
            {"collection": collection},
        )
        return [json.loads(row[0]) for row in rows]

    def write(self, collection: str, rows: Iterable[dict[str, Any]]) -> None:
        self._validate_collection(collection)
        desired = [dict(row) for row in rows]
        id_field = _ID_FIELDS[collection]
        for row in desired:
            if not row.get(id_field) or not row.get("workspace_id"):
                raise TaskRepositoryError(f"invalid_{collection}_record")
        with self._transaction() as tx:
            lock = " FOR UPDATE" if self.dialect not in {"sqlite", ""} else ""
            current_rows = tx.execute(
                f"SELECT record_id, version, data FROM task_project_records WHERE collection = :collection{lock}",
                {"collection": collection},
            )
            current = {str(record_id): (int(version), str(data)) for record_id, version, data in current_rows}
            desired_ids = {str(row[id_field]) for row in desired}
            for row in desired:
                record_id = str(row[id_field])
                version = int(row.get("version", 1))
                encoded = json.dumps(row, ensure_ascii=False, sort_keys=True)
                if record_id in current:
                    current_version, current_data = current[record_id]
                    if version == current_version and encoded != current_data:
                        raise TaskRepositoryConflict(f"stale_write:{collection}:{record_id}")
                    if version not in {current_version, current_version + 1}:
                        raise TaskRepositoryConflict(f"version_conflict:{collection}:{record_id}")
                params = {"collection": collection, "record_id": record_id,
                          "workspace_id": str(row["workspace_id"]), "version": version,
                          "data": encoded}
                if record_id in current:
                    changed = tx.execute(
                        "UPDATE task_project_records SET workspace_id=:workspace_id, version=:version, data=:data "
                        "WHERE collection=:collection AND record_id=:record_id AND version IN (:old_version, :version)",
                        {**params, "old_version": current[record_id][0]},
                    )
                else:
                    tx.execute(
                        "INSERT INTO task_project_records(collection,record_id,workspace_id,version,data) "
                        "VALUES(:collection,:record_id,:workspace_id,:version,:data)", params)
            for record_id in set(current) - desired_ids:
                tx.execute("DELETE FROM task_project_records WHERE collection=:collection AND record_id=:record_id",
                           {"collection": collection, "record_id": record_id})

    @contextmanager
    def _transaction(self):
        database = getattr(self.executor, "database", None)
        if database is None:
            with self.executor.transaction() as tx:
                yield tx
            return
        from sqlalchemy import text
        class SessionExecutor:
            def __init__(self, session: Any) -> None: self.session = session
            def execute(self, sql: str, params: Mapping[str, Any] | None = None):
                result = self.session.execute(text(sql), dict(params or {}))
                return [tuple(row) for row in result.fetchall()] if result.returns_rows else []
        with database.session() as session:
            yield SessionExecutor(session)

    def append(self, collection: str, row: dict[str, Any]) -> None:
        existing = self.read(collection)
        existing.append(dict(row))
        self.write(collection, existing)

    @staticmethod
    def _validate_collection(collection: str) -> None:
        if collection not in _ID_FIELDS:
            raise TaskRepositoryError(f"unknown_collection:{collection}")


def create_task_repository(*, env: Mapping[str, str] | None = None, executor: Any | None = None) -> TaskRepository | None:
    values = env if env is not None else os.environ
    profile = str(values.get("SECONDBRAIN_ENV") or values.get("SECONDBRAIN_PROFILE") or "development").lower()
    backend = str(values.get("TASK_REPOSITORY_BACKEND") or ("postgres" if profile.startswith("prod") else "jsonl")).lower()
    if backend == "jsonl":
        if profile.startswith("prod"):
            raise TaskRepositoryError("jsonl_not_allowed_in_production")
        return None
    if backend != "postgres":
        raise TaskRepositoryError(f"unknown_task_repository_backend:{backend}")
    if executor is None:
        database_url = str(values.get("SECOND_BRAIN_DATABASE_URL") or values.get("DATABASE_URL") or "").strip()
        if not database_url:
            raise TaskRepositoryError("postgres_task_repository_requires_database_url")
        from secondbrain.storage.database import Database
        from secondbrain.storage.database_config import DatabaseConfig
        from secondbrain.storage.db_executor import SqlAlchemyExecutor
        executor = SqlAlchemyExecutor(Database(DatabaseConfig(url=database_url)))
    repository = PostgresTaskRepository(executor)
    repository.ensure_schema()
    return repository


def migrate_jsonl_to_repository(project_root: str | Path, target: TaskRepository, *, dry_run: bool = True) -> dict[str, Any]:
    root = Path(project_root).resolve() / "runtime" / "tasks"
    report: dict[str, Any] = {"dry_run": dry_run, "collections": {}, "invalid": [], "duplicates": []}
    validated: dict[str, list[dict[str, Any]]] = {}
    for collection, id_field in _ID_FIELDS.items():
        source = root / f"{collection}.jsonl"
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        if source.exists():
            for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    report["invalid"].append({"collection": collection, "line": number, "reason": "invalid_json"})
                    continue
                record_id = str(row.get(id_field) or "")
                if not record_id or not row.get("workspace_id"):
                    report["invalid"].append({"collection": collection, "line": number, "reason": "missing_identity"})
                    continue
                if record_id in seen:
                    report["duplicates"].append({"collection": collection, "record_id": record_id})
                    continue
                seen.add(record_id)
                rows.append(row)
        report["collections"][collection] = {"valid": len(rows), "source": str(source)}
        validated[collection] = rows
    report["status"] = "ready" if not report["invalid"] and not report["duplicates"] else "blocked"
    if not dry_run and report["status"] == "ready":
        for collection, rows in validated.items():
            target.write(collection, rows)
    return report
