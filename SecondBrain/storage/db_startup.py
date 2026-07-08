"""Startup validation: resolve DATABASE_URL, connect (with retry), block cleanly.

Fallback to SQLite only when explicitly enabled (policy). Dependency-injectable so
the control flow is testable without a live PostgreSQL / SQLAlchemy.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from secondbrain.storage.db_policy import resolve, DbResolution, DatabaseStartupError, read_env
from secondbrain.storage.db_retry import RetryPolicy, run_with_retry
from secondbrain.storage.db_executor import SqlExecutor, SqliteExecutor

DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


@dataclass
class DatabaseRuntime:
    backend: str
    url: str
    environment: str
    is_fallback: bool
    executor: SqlExecutor
    connected: bool
    reason: str

    def health(self) -> dict:
        return {"backend": self.backend, "environment": self.environment,
                "is_fallback": self.is_fallback, "connected": self.connected,
                "dialect": self.executor.dialect, "reason": self.reason}


def _require_ping(executor: SqlExecutor) -> bool:
    if not executor.ping():
        raise ConnectionError("database ping failed")
    return True


def _default_pg_executor_factory(url: str) -> SqlExecutor:  # pragma: no cover - needs sqlalchemy
    from secondbrain.storage.database import Database
    from secondbrain.storage.database_config import DatabaseConfig
    from secondbrain.storage.db_executor import SqlAlchemyExecutor
    return SqlAlchemyExecutor(Database(DatabaseConfig(url=url)))


def validate_and_connect(
    env: dict[str, str] | None = None,
    *,
    retry: RetryPolicy | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    pg_executor_factory: Callable[[str], SqlExecutor] | None = None,
    sqlite_executor_factory: Callable[[str], SqlExecutor] = SqliteExecutor,
) -> DatabaseRuntime:
    """Resolve + validate the database. Raises DatabaseStartupError to block cleanly."""
    resolution: DbResolution = resolve(env)                     # may raise DatabaseStartupError
    allow_fallback = bool(read_env(env)["allow_fallback"])
    retry = retry or RetryPolicy()

    if resolution.backend == "sqlite":
        executor = sqlite_executor_factory(resolution.url)
        connected = executor.ping()
        if not connected and not allow_fallback:
            raise DatabaseStartupError(f"SQLite database not usable: {resolution.url}")
        return DatabaseRuntime("sqlite", resolution.url, resolution.environment,
                               resolution.is_fallback, executor, connected, resolution.reason)

    # postgresql
    factory = pg_executor_factory or _default_pg_executor_factory
    try:
        executor = factory(resolution.url)
        run_with_retry(lambda: _require_ping(executor), retry, sleeper=sleeper)
        return DatabaseRuntime("postgresql", resolution.url, resolution.environment,
                               False, executor, True, "postgresql connected")
    except DatabaseStartupError:
        raise
    except BaseException as exc:  # noqa: BLE001 - connection failure handling
        if allow_fallback:
            sqlite_url = "sqlite:///" + read_env(env)["sqlite_dev_path"]
            executor = sqlite_executor_factory(sqlite_url)
            return DatabaseRuntime("sqlite", sqlite_url, resolution.environment,
                                   True, executor, executor.ping(),
                                   f"postgres unreachable, sqlite fallback engaged: {exc}")
        raise DatabaseStartupError(
            f"PostgreSQL unreachable and SQLite fallback not enabled: {exc}"
        ) from exc
