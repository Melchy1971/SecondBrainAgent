"""Migrate vectors between stores (SQLite dev -> PostgreSQL/pgvector production)."""

from __future__ import annotations

from typing import Any


def migrate_vectors(source, target, *, batch_size: int = 500) -> dict:
    """Copy every VectorRecord from source into target using batch upserts.

    Both source and target implement the VectorStore surface (iter_records + batch_upsert).
    Backend-agnostic: SQLite->SQLite (tests), SQLite->pgvector (production).
    """
    if batch_size < 1:
        raise ValueError("batch_size must be >= 1")
    migrated = 0
    batches = 0
    buffer: list = []
    for record in source.iter_records():
        buffer.append(record)
        if len(buffer) >= batch_size:
            migrated += target.batch_upsert(buffer)
            batches += 1
            buffer = []
    if buffer:
        migrated += target.batch_upsert(buffer)
        batches += 1
    return {"migrated": migrated, "batches": batches, "target_count": target.count()}
