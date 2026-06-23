"""v30.1 - Document repository."""

from __future__ import annotations

from secondbrain.storage.repositories.base_repository import BaseRepository, RepositoryResult


class DocumentRepository(BaseRepository):
    def count(self) -> int:
        from sqlalchemy import text
        with self.database.session() as session:
            return int(session.execute(text("SELECT COUNT(*) FROM documents")).scalar_one())

    def create_minimal(self, document_id: str, title: str) -> RepositoryResult:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(
                text("INSERT INTO documents (id, title) VALUES (:id, :title)"),
                {"id": document_id, "title": title},
            )
        return RepositoryResult(status="PASS", affected=1)
