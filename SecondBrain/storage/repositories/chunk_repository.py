"""v30.1 - Chunk repository."""

from __future__ import annotations

from secondbrain.storage.repositories.base_repository import BaseRepository, RepositoryResult


class ChunkRepository(BaseRepository):
    def create_minimal(self, chunk_id: str, document_id: str, text_value: str) -> RepositoryResult:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(
                text("INSERT INTO chunks (id, document_id, text) VALUES (:id, :document_id, :text)"),
                {"id": chunk_id, "document_id": document_id, "text": text_value},
            )
        return RepositoryResult(status="PASS", affected=1)
