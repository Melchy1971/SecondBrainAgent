"""v30.2 - vector index management."""

from __future__ import annotations


class VectorIndexManager:
    def __init__(self, database):
        self.database = database

    def ensure_hnsw_index(self) -> None:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw_cosine
            ON embeddings
            USING hnsw (embedding vector_cosine_ops)
            """))

    def analyze(self) -> None:
        from sqlalchemy import text
        with self.database.session() as session:
            session.execute(text("ANALYZE embeddings"))
