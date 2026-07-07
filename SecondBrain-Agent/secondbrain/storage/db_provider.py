"""Facade tying startup validation, migrations, health and repositories together.

Keeps all existing storage APIs intact; this is an additive orchestration layer.
"""

from __future__ import annotations

from pathlib import Path

from secondbrain.storage.db_startup import validate_and_connect, DatabaseRuntime, DEFAULT_MIGRATIONS_DIR
from secondbrain.storage.migration_runner import MigrationRunner


class DatabaseProvider:
    def __init__(self, runtime: DatabaseRuntime, *, migrations_dir=DEFAULT_MIGRATIONS_DIR) -> None:
        self.runtime = runtime
        self.migrations_dir = Path(migrations_dir)

    @classmethod
    def start(cls, env=None, **kw) -> "DatabaseProvider":
        return cls(validate_and_connect(env, **kw))

    @property
    def executor(self):
        return self.runtime.executor

    def migration_runner(self) -> MigrationRunner:
        return MigrationRunner(self.runtime.executor, self.migrations_dir)

    def migrate(self) -> dict:
        return self.migration_runner().apply()

    def repositories(self):
        """Bind the existing SQLAlchemy repositories to the production Database.

        Only available on the SQLAlchemy/PostgreSQL path. Kept API-compatible with
        the existing repository classes.
        """
        from secondbrain.storage.db_executor import SqlAlchemyExecutor
        if not isinstance(self.runtime.executor, SqlAlchemyExecutor):  # pragma: no cover
            raise RuntimeError("repositories() requires the SQLAlchemy/PostgreSQL backend")
        database = self.runtime.executor.database  # pragma: no cover - needs sqlalchemy
        from secondbrain.storage.repositories.document_repository import DocumentRepository
        from secondbrain.storage.repositories.chunk_repository import ChunkRepository
        from secondbrain.storage.repositories.connector_repository import ConnectorRepository
        from secondbrain.storage.repositories.memory_repository import MemoryRepository
        from secondbrain.storage.repositories.workflow_repository import WorkflowRepository
        return {
            "document": DocumentRepository(database),
            "chunk": ChunkRepository(database),
            "connector": ConnectorRepository(database),
            "memory": MemoryRepository(database),
            "workflow": WorkflowRepository(database),
        }

    def health(self) -> dict:
        report = dict(self.runtime.health())
        try:
            report["migrations"] = self.migration_runner().status()
        except Exception as exc:  # noqa: BLE001
            report["migrations"] = {"error": str(exc)}
        return report
