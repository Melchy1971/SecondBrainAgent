"""v30.2 - pgvector repository.

Uses raw SQL to avoid binding the project to a specific ORM model layer.
"""

from __future__ import annotations

import json

from secondbrain.storage.vector_models import VectorRecord, VectorSearchResult


def to_pgvector_literal(values: list[float]) -> str:
    if not values:
        raise ValueError("embedding vector must not be empty")
    return "[" + ",".join(str(float(v)) for v in values) + "]"


class PgVectorRepository:
    def __init__(self, database):
        self.database = database

    def upsert(self, record: VectorRecord) -> None:
        from sqlalchemy import text
        vector_literal = to_pgvector_literal(record.embedding)
        with self.database.session() as session:
            session.execute(
                text("""
                INSERT INTO embeddings (
                    id, owner_type, owner_id, provider, model, dimension, embedding, metadata
                )
                VALUES (
                    :id, :owner_type, :owner_id, :provider, :model, :dimension,
                    CAST(:embedding AS vector), CAST(:metadata AS jsonb)
                )
                ON CONFLICT (id) DO UPDATE SET
                    owner_type = EXCLUDED.owner_type,
                    owner_id = EXCLUDED.owner_id,
                    provider = EXCLUDED.provider,
                    model = EXCLUDED.model,
                    dimension = EXCLUDED.dimension,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
                """),
                {
                    "id": record.id,
                    "owner_type": record.owner_type,
                    "owner_id": record.owner_id,
                    "provider": record.provider,
                    "model": record.model,
                    "dimension": record.dimension,
                    "embedding": vector_literal,
                    "metadata": json.dumps(record.metadata),
                },
            )

    def search(
        self,
        query_embedding: list[float],
        *,
        provider: str | None = None,
        model: str | None = None,
        limit: int = 10,
    ) -> list[VectorSearchResult]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        from sqlalchemy import text

        filters = []
        params = {
            "query_embedding": to_pgvector_literal(query_embedding),
            "limit": limit,
        }
        if provider:
            filters.append("provider = :provider")
            params["provider"] = provider
        if model:
            filters.append("model = :model")
            params["model"] = model
        where_clause = "WHERE " + " AND ".join(filters) if filters else ""

        sql = f"""
            SELECT
                id,
                owner_type,
                owner_id,
                metadata,
                embedding <=> CAST(:query_embedding AS vector) AS distance
            FROM embeddings
            {where_clause}
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :limit
        """
        with self.database.session() as session:
            rows = session.execute(text(sql), params).mappings().all()

        results = []
        for row in rows:
            distance = float(row["distance"])
            results.append(VectorSearchResult(
                id=row["id"],
                owner_type=row["owner_type"],
                owner_id=row["owner_id"],
                distance=distance,
                score=1.0 - distance,
                metadata=dict(row["metadata"] or {}),
            ))
        return results
