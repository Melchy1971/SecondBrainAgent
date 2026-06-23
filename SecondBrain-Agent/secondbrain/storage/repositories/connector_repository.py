"""v30.1 - Connector repository."""

from __future__ import annotations

from secondbrain.storage.repositories.base_repository import BaseRepository, RepositoryResult


class ConnectorRepository(BaseRepository):
    def save_checkpoint(self, connector: str, cursor: str | None) -> RepositoryResult:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(
                text("""
                INSERT INTO connector_checkpoints (connector, cursor)
                VALUES (:connector, :cursor)
                ON CONFLICT (connector) DO UPDATE SET cursor = EXCLUDED.cursor
                """),
                {"connector": connector, "cursor": cursor},
            )
        return RepositoryResult(status="PASS", affected=1)
