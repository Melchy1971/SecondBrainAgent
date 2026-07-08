"""Backend-agnostic vector store.

- SqliteVectorStore: stdlib sqlite3 + Python similarity (development + tests; no pgvector).
- PgVectorStore: production, wraps the EXISTING PgVectorRepository/VectorIndexManager unchanged
  and adds batch insert, reindex, alternative metrics and EXPLAIN.

Search returns the existing VectorSearchResult, so all prior vector searches keep working.
"""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Protocol, runtime_checkable

from secondbrain.storage.vector_models import VectorRecord, VectorSearchResult
from secondbrain.storage.vector_index import hnsw_index_sql, ivfflat_index_sql, drop_index_sql, index_name, OPERATOR

METRICS = ("cosine", "l2", "ip")


# ---- similarity helpers (pure python, for the sqlite dev backend) ----------
def _dot(a, b): return sum(x * y for x, y in zip(a, b))
def _norm(a): return math.sqrt(sum(x * x for x in a)) or 1e-12


def distance(metric: str, a: list[float], b: list[float]) -> float:
    if metric == "cosine":
        return 1.0 - _dot(a, b) / (_norm(a) * _norm(b))
    if metric == "l2":
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    if metric == "ip":
        return -_dot(a, b)                      # pgvector <#> returns negative inner product
    raise ValueError(f"unsupported metric: {metric}")


def _score(metric: str, dist: float) -> float:
    if metric == "cosine":
        return 1.0 - dist                       # identical to existing PgVectorRepository semantics
    if metric == "l2":
        return 1.0 / (1.0 + dist)
    return -dist                                 # ip: higher inner product -> higher score


@runtime_checkable
class VectorStore(Protocol):
    def upsert(self, record: VectorRecord) -> None: ...
    def batch_upsert(self, records: Iterable[VectorRecord]) -> int: ...
    def search(self, query_embedding: list[float], *, provider: str | None = None,
               model: str | None = None, limit: int = 10, metric: str = "cosine") -> list[VectorSearchResult]: ...
    def count(self) -> int: ...


class SqliteVectorStore:
    """Development/test vector store. Cosine/L2/IP computed in Python."""

    def __init__(self, url_or_path: str = ":memory:") -> None:
        path = url_or_path
        if url_or_path.startswith("sqlite:///"):
            path = url_or_path[len("sqlite:///"):] or ":memory:"
        if path not in (":memory:", ""):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path or ":memory:", isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY, owner_type TEXT, owner_id TEXT,
                provider TEXT, model TEXT, dimension INTEGER,
                embedding TEXT NOT NULL, metadata TEXT
            )
        """)

    def upsert(self, record: VectorRecord) -> None:
        self.batch_upsert([record])

    def batch_upsert(self, records: Iterable[VectorRecord]) -> int:
        rows = [(r.id, r.owner_type, r.owner_id, r.provider, r.model, r.dimension,
                 json.dumps(list(r.embedding)), json.dumps(r.metadata)) for r in records]
        if not rows:
            return 0
        self._conn.executemany("""
            INSERT INTO embeddings (id, owner_type, owner_id, provider, model, dimension, embedding, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                owner_type=excluded.owner_type, owner_id=excluded.owner_id,
                provider=excluded.provider, model=excluded.model, dimension=excluded.dimension,
                embedding=excluded.embedding, metadata=excluded.metadata
        """, rows)
        return len(rows)

    def search(self, query_embedding, *, provider=None, model=None, limit=10, metric="cosine"):
        if limit < 1:
            raise ValueError("limit must be >= 1")
        sql = "SELECT id, owner_type, owner_id, embedding, metadata FROM embeddings"
        filters, params = [], []
        if provider:
            filters.append("provider = ?"); params.append(provider)
        if model:
            filters.append("model = ?"); params.append(model)
        if filters:
            sql += " WHERE " + " AND ".join(filters)
        scored = []
        for row in self._conn.execute(sql, params):
            emb = json.loads(row["embedding"])
            dist = distance(metric, query_embedding, emb)
            scored.append((dist, row))
        scored.sort(key=lambda t: t[0])
        out = []
        for dist, row in scored[:limit]:
            out.append(VectorSearchResult(
                id=row["id"], owner_type=row["owner_type"], owner_id=row["owner_id"],
                distance=float(dist), score=float(_score(metric, dist)),
                metadata=json.loads(row["metadata"] or "{}")))
        return out

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0])

    def reindex(self, *, method="hnsw", metric="cosine", **opts) -> dict:
        # sqlite has no ANN index; this is a no-op recorded for parity with pgvector
        return {"backend": "sqlite", "method": method, "metric": metric, "status": "noop"}

    def explain(self, query_embedding, *, limit=10, metric="cosine") -> dict:
        plan = self._conn.execute(
            "EXPLAIN QUERY PLAN SELECT id FROM embeddings LIMIT ?", [limit]).fetchall()
        return {"backend": "sqlite", "metric": metric,
                "plan": [dict(r) for r in plan],
                "note": "sqlite scans all rows; ANN index only on PostgreSQL/pgvector"}

    def iter_records(self):
        for row in self._conn.execute("SELECT id, owner_type, owner_id, provider, model, embedding, metadata FROM embeddings"):
            yield VectorRecord(id=row["id"], owner_type=row["owner_type"], owner_id=row["owner_id"],
                               provider=row["provider"], model=row["model"],
                               embedding=json.loads(row["embedding"]),
                               metadata=json.loads(row["metadata"] or "{}"))

    def close(self) -> None:
        self._conn.close()


class PgVectorStore:
    """Production store. Delegates single upsert/search to the EXISTING PgVectorRepository."""

    def __init__(self, database) -> None:
        self.database = database
        from secondbrain.storage.pgvector_repository import PgVectorRepository
        from secondbrain.storage.vector_index_manager import VectorIndexManager
        self.repo = PgVectorRepository(database)
        self.index = VectorIndexManager(database)

    def upsert(self, record: VectorRecord) -> None:  # pragma: no cover - needs pg
        self.repo.upsert(record)

    def search(self, query_embedding, *, provider=None, model=None, limit=10, metric="cosine"):  # pragma: no cover
        if metric == "cosine":
            return self.repo.search(query_embedding, provider=provider, model=model, limit=limit)
        return self._search_metric(query_embedding, provider=provider, model=model, limit=limit, metric=metric)

    def _search_metric(self, query_embedding, *, provider, model, limit, metric):  # pragma: no cover
        from sqlalchemy import text
        from secondbrain.storage.pgvector_repository import to_pgvector_literal
        op = OPERATOR[metric]
        filters, params = [], {"q": to_pgvector_literal(query_embedding), "limit": limit}
        if provider:
            filters.append("provider = :provider"); params["provider"] = provider
        if model:
            filters.append("model = :model"); params["model"] = model
        where = "WHERE " + " AND ".join(filters) if filters else ""
        sql = (f"SELECT id, owner_type, owner_id, metadata, embedding {op} CAST(:q AS vector) AS distance "
               f"FROM embeddings {where} ORDER BY embedding {op} CAST(:q AS vector) LIMIT :limit")
        with self.database.session() as session:
            rows = session.execute(text(sql), params).mappings().all()
        return [VectorSearchResult(id=r["id"], owner_type=r["owner_type"], owner_id=r["owner_id"],
                                   distance=float(r["distance"]), score=float(_score(metric, float(r["distance"]))),
                                   metadata=dict(r["metadata"] or {})) for r in rows]

    def batch_upsert(self, records: Iterable[VectorRecord]) -> int:  # pragma: no cover - needs pg
        from sqlalchemy import text
        from secondbrain.storage.pgvector_repository import to_pgvector_literal
        rows = list(records)
        if not rows:
            return 0
        with self.database.session() as session:
            for r in rows:
                session.execute(text("""
                    INSERT INTO embeddings (id, owner_type, owner_id, provider, model, dimension, embedding, metadata)
                    VALUES (:id,:ot,:oi,:p,:m,:d, CAST(:e AS vector), CAST(:md AS jsonb))
                    ON CONFLICT (id) DO UPDATE SET embedding=EXCLUDED.embedding, metadata=EXCLUDED.metadata
                """), {"id": r.id, "ot": r.owner_type, "oi": r.owner_id, "p": r.provider, "m": r.model,
                       "d": r.dimension, "e": to_pgvector_literal(r.embedding), "md": json.dumps(r.metadata)})
        return len(rows)

    def count(self) -> int:  # pragma: no cover - needs pg
        from sqlalchemy import text
        with self.database.session() as session:
            return int(session.execute(text("SELECT COUNT(*) FROM embeddings")).scalar_one())

    def reindex(self, *, method="hnsw", metric="cosine", m=16, ef_construction=64, lists=100) -> dict:  # pragma: no cover
        from sqlalchemy import text
        name = index_name(method, metric)
        ddl = (hnsw_index_sql(metric=metric, m=m, ef_construction=ef_construction) if method == "hnsw"
               else ivfflat_index_sql(metric=metric, lists=lists))
        with self.database.session() as session:
            session.execute(text(drop_index_sql(name)))
            session.execute(text(ddl))
            session.execute(text("ANALYZE embeddings"))
        return {"backend": "postgresql", "method": method, "metric": metric, "index": name, "status": "rebuilt"}

    def iter_records(self):  # pragma: no cover - needs pg
        from sqlalchemy import text
        with self.database.session() as session:
            rows = session.execute(text(
                "SELECT id, owner_type, owner_id, provider, model, embedding, metadata FROM embeddings")).mappings().all()
        for r in rows:
            emb = r["embedding"]
            if isinstance(emb, str):
                emb = [float(x) for x in emb.strip("[]").split(",") if x]
            yield VectorRecord(id=r["id"], owner_type=r["owner_type"], owner_id=r["owner_id"],
                               provider=r["provider"], model=r["model"], embedding=list(emb),
                               metadata=dict(r["metadata"] or {}))
