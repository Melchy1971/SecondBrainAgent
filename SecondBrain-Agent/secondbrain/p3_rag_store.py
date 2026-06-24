from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from secondbrain.p1_embeddings import cosine_similarity
from secondbrain.p3_pgvector_foundation import PgVectorConfig, build_pgvector_schema_sql, load_pgvector_config, redact_dsn

RAG_STORE_SCHEMA = "secondbrain.p3_rag_store.v1"


@dataclass(frozen=True)
class RagDocumentRecord:
    id: str
    source: str
    title: str
    content_hash: str
    created_at: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RagChunkRecord:
    id: str
    document_id: str
    ordinal: int
    text: str
    char_start: int
    char_end: int
    tokens: list[str]
    token_count: int
    provider: str | None = None
    dimensions: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RagVectorHit:
    chunk_id: str
    document_id: str
    source: str
    title: str
    score: float
    text: str
    provider: str
    dimensions: int

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["score"] = round(float(self.score), 6)
        return data


class RagStore(Protocol):
    backend: str

    def status(self) -> dict[str, Any]:
        ...

    def sources(self) -> dict[str, Any]:
        ...

    def vector_search(self, query_vector: list[float], *, limit: int = 5, provider: str | None = None) -> dict[str, Any]:
        ...


class SQLiteRagStore:
    backend = "sqlite"

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def status(self) -> dict[str, Any]:
        if not self.db_path.exists():
            return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "empty", "db_path": str(self.db_path), "documents": 0, "chunks": 0, "vectors": 0}
        with self._connect() as conn:
            docs = int(conn.execute("select count(*) as n from documents").fetchone()["n"])
            chunks = int(conn.execute("select count(*) as n from chunks").fetchone()["n"])
            vectors = int(conn.execute("select count(*) as n from chunk_embeddings").fetchone()["n"])
            providers = [dict(row) for row in conn.execute("select provider, dimensions, count(*) as vectors from chunk_embeddings group by provider, dimensions order by provider, dimensions").fetchall()]
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "db_path": str(self.db_path), "documents": docs, "chunks": chunks, "vectors": vectors, "providers": providers}

    def sources(self) -> dict[str, Any]:
        if not self.db_path.exists():
            return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "sources": []}
        with self._connect() as conn:
            rows = conn.execute("select d.id, d.source, d.title, d.content_hash, d.created_at, d.metadata_json, count(c.id) as chunks from documents d left join chunks c on c.document_id = d.id group by d.id order by d.created_at desc, d.title").fetchall()
        return {
            "schema": RAG_STORE_SCHEMA,
            "backend": self.backend,
            "ok": True,
            "status": "pass",
            "sources": [
                RagDocumentRecord(
                    id=row["id"],
                    source=row["source"],
                    title=row["title"],
                    content_hash=row["content_hash"],
                    created_at=row["created_at"],
                    metadata={**json.loads(row["metadata_json"] or "{}"), "chunks": int(row["chunks"])},
                ).to_dict()
                for row in rows
            ],
        }

    def vector_search(self, query_vector: list[float], *, limit: int = 5, provider: str | None = None) -> dict[str, Any]:
        if not self.db_path.exists() or not query_vector:
            return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "hits": [], "hit_count": 0}
        sql = "select c.id as chunk_id, c.document_id, c.text, d.source, d.title, e.vector_json, e.provider, e.dimensions from chunk_embeddings e join chunks c on c.id = e.chunk_id join documents d on d.id = c.document_id"
        params: tuple[Any, ...] = ()
        if provider:
            sql += " where e.provider = ?"
            params = (provider,)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        hits: list[RagVectorHit] = []
        for row in rows:
            try:
                vector = [float(v) for v in json.loads(row["vector_json"])]
            except Exception:
                continue
            score = cosine_similarity(query_vector, vector)
            if score <= 0:
                continue
            hits.append(RagVectorHit(row["chunk_id"], row["document_id"], row["source"], row["title"], score, row["text"], row["provider"], int(row["dimensions"])))
        hits.sort(key=lambda hit: (-hit.score, hit.title, hit.chunk_id))
        selected = hits[: max(1, int(limit))]
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "hit_count": len(selected), "hits": [hit.to_dict() for hit in selected]}


class PgVectorRagStore:
    backend = "pgvector"

    def __init__(self, config: PgVectorConfig):
        self.config = config

    def status(self) -> dict[str, Any]:
        return {
            "schema": RAG_STORE_SCHEMA,
            "backend": self.backend,
            "ok": bool(self.config.enabled and self.config.dsn),
            "status": "ready" if self.config.enabled and self.config.dsn else "configured_offline",
            "config": self.config.to_dict(),
            "dsn": redact_dsn(self.config.dsn),
            "sql_preview": build_pgvector_schema_sql(self.config),
            "capabilities": ["schema_preview", "live_readiness", "future_vector_search"],
        }

    def sources(self) -> dict[str, Any]:
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": False, "status": "not_implemented", "error": "pgvector_sources_not_implemented_yet"}

    def vector_search(self, query_vector: list[float], *, limit: int = 5, provider: str | None = None) -> dict[str, Any]:
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": False, "status": "not_implemented", "error": "pgvector_vector_search_not_implemented_yet", "limit": limit, "provider": provider}


def store_backend_from_config(project_root: str | Path) -> str:
    config = load_pgvector_config(project_root)
    if config.enabled:
        return "pgvector"
    return "sqlite"


def create_rag_store(project_root: str | Path, *, sqlite_db_path: str | Path | None = None) -> RagStore:
    root = Path(project_root).resolve()
    config = load_pgvector_config(root)
    if config.enabled:
        return PgVectorRagStore(config)
    return SQLiteRagStore(sqlite_db_path or root / "runtime" / "p1_rag" / "rag.sqlite3")
