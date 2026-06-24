from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from secondbrain.p1_embeddings import cosine_similarity
from secondbrain.p3_pgvector_foundation import PgVectorConfig, build_pgvector_schema_sql, load_pgvector_config, redact_dsn

RAG_STORE_SCHEMA = "secondbrain.p3_rag_store.v2"


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
    created_at: str = ""
    provider: str | None = None
    dimensions: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RagVectorRecord:
    chunk_id: str
    provider: str
    dimensions: int
    vector: list[float]
    created_at: str

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

    def upsert_document(self, document: RagDocumentRecord) -> dict[str, Any]:
        ...

    def upsert_chunks(self, chunks: list[RagChunkRecord]) -> dict[str, Any]:
        ...

    def upsert_vectors(self, vectors: list[RagVectorRecord]) -> dict[str, Any]:
        ...

    def vector_search(self, query_vector: list[float], *, limit: int = 5, provider: str | None = None) -> dict[str, Any]:
        ...


class SQLiteRagStore:
    backend = "sqlite"

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                create table if not exists documents(
                    id text primary key,
                    source text not null,
                    title text not null,
                    content_hash text not null,
                    created_at text not null,
                    metadata_json text not null
                )
            """)
            conn.execute("""
                create table if not exists chunks(
                    id text primary key,
                    document_id text not null,
                    ordinal integer not null,
                    text text not null,
                    char_start integer not null default 0,
                    char_end integer not null default 0,
                    token_json text not null,
                    token_count integer not null,
                    created_at text not null,
                    foreign key(document_id) references documents(id)
                )
            """)
            conn.execute("""
                create table if not exists chunk_embeddings(
                    chunk_id text primary key,
                    provider text not null,
                    dimensions integer not null,
                    vector_json text not null,
                    created_at text not null,
                    foreign key(chunk_id) references chunks(id)
                )
            """)
            conn.execute("create index if not exists idx_chunks_document on chunks(document_id)")
            conn.execute("create index if not exists idx_documents_source on documents(source)")
            conn.execute("create index if not exists idx_chunk_embeddings_provider on chunk_embeddings(provider)")
            conn.commit()

    def status(self) -> dict[str, Any]:
        with self._connect() as conn:
            docs = int(conn.execute("select count(*) as n from documents").fetchone()["n"])
            chunks = int(conn.execute("select count(*) as n from chunks").fetchone()["n"])
            vectors = int(conn.execute("select count(*) as n from chunk_embeddings").fetchone()["n"])
            providers = [dict(row) for row in conn.execute("select provider, dimensions, count(*) as vectors from chunk_embeddings group by provider, dimensions order by provider, dimensions").fetchall()]
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "db_path": str(self.db_path), "documents": docs, "chunks": chunks, "vectors": vectors, "providers": providers, "capabilities": ["status", "sources", "upsert_document", "upsert_chunks", "upsert_vectors", "vector_search"]}

    def sources(self) -> dict[str, Any]:
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

    def upsert_document(self, document: RagDocumentRecord) -> dict[str, Any]:
        with self._connect() as conn:
            conn.execute(
                "insert or replace into documents(id, source, title, content_hash, created_at, metadata_json) values (?, ?, ?, ?, ?, ?)",
                (document.id, document.source, document.title, document.content_hash, document.created_at, json.dumps(document.metadata, ensure_ascii=False, sort_keys=True)),
            )
            conn.commit()
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "document_id": document.id}

    def upsert_chunks(self, chunks: list[RagChunkRecord]) -> dict[str, Any]:
        with self._connect() as conn:
            for chunk in chunks:
                conn.execute(
                    "insert or replace into chunks(id, document_id, ordinal, text, char_start, char_end, token_json, token_count, created_at) values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (chunk.id, chunk.document_id, chunk.ordinal, chunk.text, chunk.char_start, chunk.char_end, json.dumps(chunk.tokens, ensure_ascii=False), chunk.token_count, chunk.created_at),
                )
            conn.commit()
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "chunks": len(chunks)}

    def upsert_vectors(self, vectors: list[RagVectorRecord]) -> dict[str, Any]:
        with self._connect() as conn:
            for vector in vectors:
                conn.execute(
                    "insert or replace into chunk_embeddings(chunk_id, provider, dimensions, vector_json, created_at) values (?, ?, ?, ?, ?)",
                    (vector.chunk_id, vector.provider, vector.dimensions, json.dumps(vector.vector), vector.created_at),
                )
            conn.commit()
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "vectors": len(vectors)}

    def vector_search(self, query_vector: list[float], *, limit: int = 5, provider: str | None = None) -> dict[str, Any]:
        if not query_vector:
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

    def _table(self, suffix: str) -> str:
        schema = _safe_identifier(self.config.schema_name, "secondbrain")
        prefix = _safe_identifier(self.config.table_prefix, "p1")
        return f"{schema}.{prefix}_{suffix}"

    def status(self) -> dict[str, Any]:
        return {
            "schema": RAG_STORE_SCHEMA,
            "backend": self.backend,
            "ok": bool(self.config.enabled and self.config.dsn),
            "status": "ready" if self.config.enabled and self.config.dsn else "configured_offline",
            "config": self.config.to_dict(),
            "dsn": redact_dsn(self.config.dsn),
            "sql_preview": build_pgvector_schema_sql(self.config),
            "capabilities": ["schema_preview", "live_readiness", "sql_upsert_document", "sql_upsert_chunks", "sql_upsert_vectors", "sql_vector_search"],
        }

    def sources(self) -> dict[str, Any]:
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": False, "status": "not_implemented", "error": "pgvector_sources_live_execution_not_implemented_yet"}

    def upsert_document(self, document: RagDocumentRecord) -> dict[str, Any]:
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "sql_preview", "sql": self.build_upsert_document_sql(), "params": (document.id, document.source, document.title, document.content_hash, document.created_at, json.dumps(document.metadata, ensure_ascii=False, sort_keys=True))}

    def upsert_chunks(self, chunks: list[RagChunkRecord]) -> dict[str, Any]:
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "sql_preview", "sql": self.build_upsert_chunk_sql(), "chunks": len(chunks)}

    def upsert_vectors(self, vectors: list[RagVectorRecord]) -> dict[str, Any]:
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "sql_preview", "sql": self.build_upsert_vector_sql(), "vectors": len(vectors)}

    def vector_search(self, query_vector: list[float], *, limit: int = 5, provider: str | None = None) -> dict[str, Any]:
        sql = self.build_vector_search_sql(provider=provider)
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": bool(self.config.enabled and self.config.dsn), "status": "sql_preview", "sql": sql, "params": {"query_vector": query_vector, "limit": max(1, int(limit)), "provider": provider}, "hit_count": 0, "hits": []}

    def build_upsert_document_sql(self) -> str:
        return f"""
insert into {self._table('documents')}(id, source, title, content_hash, created_at, metadata_json)
values (%s, %s, %s, %s, %s, %s::jsonb)
on conflict (id) do update set
    source = excluded.source,
    title = excluded.title,
    content_hash = excluded.content_hash,
    created_at = excluded.created_at,
    metadata_json = excluded.metadata_json;
""".strip()

    def build_upsert_chunk_sql(self) -> str:
        return f"""
insert into {self._table('chunks')}(id, document_id, ordinal, text, char_start, char_end, token_json, token_count, created_at)
values (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
on conflict (id) do update set
    document_id = excluded.document_id,
    ordinal = excluded.ordinal,
    text = excluded.text,
    char_start = excluded.char_start,
    char_end = excluded.char_end,
    token_json = excluded.token_json,
    token_count = excluded.token_count,
    created_at = excluded.created_at;
""".strip()

    def build_upsert_vector_sql(self) -> str:
        return f"""
insert into {self._table('chunk_embeddings')}(chunk_id, provider, dimensions, embedding, created_at)
values (%s, %s, %s, %s::vector, %s)
on conflict (chunk_id) do update set
    provider = excluded.provider,
    dimensions = excluded.dimensions,
    embedding = excluded.embedding,
    created_at = excluded.created_at;
""".strip()

    def build_vector_search_sql(self, *, provider: str | None = None) -> str:
        provider_filter = "and e.provider = %s" if provider else ""
        return f"""
select
    c.id as chunk_id,
    c.document_id,
    d.source,
    d.title,
    c.text,
    e.provider,
    e.dimensions,
    1 - (e.embedding <=> %s::vector) as score
from {self._table('chunk_embeddings')} e
join {self._table('chunks')} c on c.id = e.chunk_id
join {self._table('documents')} d on d.id = c.document_id
where e.dimensions = %s
{provider_filter}
order by e.embedding <=> %s::vector
limit %s;
""".strip()


def _safe_identifier(value: str, fallback: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in (value or "")).lower()
    if not cleaned or cleaned[0].isdigit():
        return fallback
    return cleaned


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
