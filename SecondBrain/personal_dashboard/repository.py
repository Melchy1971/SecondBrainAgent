"""PostgreSQL-first persistence for personal dashboard configuration."""

from __future__ import annotations

import json
import os
from typing import Any, Mapping

from secondbrain.personal_dashboard.models import DashboardConfig


class DashboardRepositoryError(RuntimeError):
    pass


class PostgresDashboardRepository:
    backend = "postgres"

    def __init__(self, executor: Any) -> None:
        self.executor = executor

    def ensure_schema(self) -> None:
        self.executor.execute("""CREATE TABLE IF NOT EXISTS dashboard_preferences (
            profile_id TEXT NOT NULL, workspace_id TEXT NOT NULL, version INTEGER NOT NULL,
            data TEXT NOT NULL, PRIMARY KEY(profile_id, workspace_id)
        )""")

    def save(self, config: DashboardConfig, *, profile_id: str = "default",
             expected_version: int | None = None) -> int:
        if not config.workspace_id or not profile_id:
            raise DashboardRepositoryError("profile_and_workspace_required")
        rows = self.executor.execute(
            "SELECT version FROM dashboard_preferences WHERE profile_id=:profile_id "
            "AND workspace_id=:workspace_id",
            {"profile_id": profile_id, "workspace_id": config.workspace_id})
        current = int(rows[0][0]) if rows else 0
        if expected_version is not None and expected_version != current:
            raise DashboardRepositoryError("stale_dashboard_config")
        version = current + 1
        params = {"profile_id": profile_id, "workspace_id": config.workspace_id,
                  "version": version,
                  "data": json.dumps(config.to_dict(), ensure_ascii=False, sort_keys=True)}
        self.executor.execute(
            "INSERT INTO dashboard_preferences(profile_id,workspace_id,version,data) "
            "VALUES(:profile_id,:workspace_id,:version,:data) "
            "ON CONFLICT(profile_id,workspace_id) DO UPDATE SET version=:version,data=:data",
            params)
        return version

    def load(self, *, workspace_id: str, profile_id: str = "default") -> tuple[DashboardConfig, int] | None:
        rows = self.executor.execute(
            "SELECT data,version FROM dashboard_preferences WHERE profile_id=:profile_id "
            "AND workspace_id=:workspace_id",
            {"profile_id": profile_id, "workspace_id": workspace_id})
        if not rows:
            return None
        return DashboardConfig(**json.loads(rows[0][0])), int(rows[0][1])


def create_dashboard_repository(*, env: Mapping[str, str] | None = None,
                                executor: Any | None = None) -> PostgresDashboardRepository | None:
    values = env if env is not None else os.environ
    profile = str(values.get("SECONDBRAIN_ENV") or "development").lower()
    backend = str(values.get("DASHBOARD_REPOSITORY_BACKEND") or
                  ("postgres" if profile.startswith("prod") else "memory")).lower()
    if backend == "memory":
        if profile.startswith("prod"):
            raise DashboardRepositoryError("memory_not_allowed_in_production")
        return None
    if backend != "postgres":
        raise DashboardRepositoryError(f"unknown_dashboard_repository_backend:{backend}")
    if executor is None:
        url = str(values.get("SECOND_BRAIN_DATABASE_URL") or values.get("DATABASE_URL") or "").strip()
        if not url:
            raise DashboardRepositoryError("postgres_dashboard_repository_requires_database_url")
        from secondbrain.storage.database import Database
        from secondbrain.storage.database_config import DatabaseConfig
        from secondbrain.storage.db_executor import SqlAlchemyExecutor
        executor = SqlAlchemyExecutor(Database(DatabaseConfig(url=url)))
    repository = PostgresDashboardRepository(executor)
    repository.ensure_schema()
    return repository
