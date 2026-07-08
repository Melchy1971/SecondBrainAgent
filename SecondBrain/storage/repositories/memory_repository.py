"""v30.1 - Memory repository."""

from __future__ import annotations

from secondbrain.storage.repositories.base_repository import BaseRepository, RepositoryResult


class MemoryRepository(BaseRepository):
    def create_minimal(self, memory_id: str, text_value: str, kind: str = "semantic") -> RepositoryResult:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(
                text("INSERT INTO memories (id, kind, text) VALUES (:id, :kind, :text)"),
                {"id": memory_id, "kind": kind, "text": text_value},
            )
        return RepositoryResult(status="PASS", affected=1)
