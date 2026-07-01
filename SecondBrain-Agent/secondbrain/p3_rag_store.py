from __future__ import annotations

import importlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from secondbrain.p1_embeddings import cosine_similarity
from secondbrain.p3_pgvector_foundation import PgVectorConfig, build_pgvector_schema_sql, load_pgvector_config, redact_dsn

RAG_STORE_SCHEMA = "secondbrain.p3_rag_store.v3"


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

    def delete_document_payload(self, document_id: str) -> dict[str, Any]:
        ...

    def all_chunks(self) -> dict[str, Any]:
        ...

    def embedding_summary(self) -> dict[str, Any]:
        ...

    def validation_snapshot(self) -> dict[str, Any]:
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
            providers = []
            for row in conn.execute("select provider, dimensions, count(*) as vectors from chunk_embeddings group by provider, dimensions order by provider, dimensions").fetchall():
                item = dict(row)
                identity = str(item["provider"])
                item["index_provider"] = identity
                item["provider"] = identity.split(":", 1)[0]
                providers.append(item)
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


    def delete_document_payload(self, document_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            chunk_ids = [row[0] for row in conn.execute("select id from chunks where document_id = ?", (document_id,)).fetchall()]
            if chunk_ids:
                conn.executemany("delete from chunk_embeddings where chunk_id = ?", [(chunk_id,) for chunk_id in chunk_ids])
            conn.execute("delete from chunks where document_id = ?", (document_id,))
            conn.commit()
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "document_id": document_id, "deleted_chunks": len(chunk_ids)}

    def all_chunks(self) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute("select c.id as chunk_id, c.document_id, c.ordinal, c.text, c.char_start, c.char_end, c.token_json, c.token_count, d.source, d.title, d.metadata_json from chunks c join documents d on d.id = c.document_id order by d.created_at desc, c.ordinal").fetchall()
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "chunks": [dict(row) for row in rows]}

    def embedding_summary(self) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute("select provider, dimensions, count(*) as n from chunk_embeddings group by provider, dimensions order by provider").fetchall()
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "providers": [{"provider": r["provider"], "dimensions": int(r["dimensions"]), "chunks": int(r["n"])} for r in rows]}

    def validation_snapshot(self) -> dict[str, Any]:
        with self._connect() as conn:
            docs = [dict(row) for row in conn.execute("select id, source, title, content_hash from documents").fetchall()]
            chunks = [dict(row) for row in conn.execute("select id, document_id, text, char_start, char_end, token_count, token_json from chunks").fetchall()]
            embeddings = [dict(row) for row in conn.execute("select chunk_id, provider, dimensions, vector_json from chunk_embeddings").fetchall()]
            orphan_chunks = [dict(row) for row in conn.execute("select c.id from chunks c left join documents d on d.id = c.document_id where d.id is null").fetchall()]
            orphan_embeddings = [dict(row) for row in conn.execute("select e.chunk_id from chunk_embeddings e left join chunks c on c.id = e.chunk_id where c.id is null").fetchall()]
            duplicate_hashes = [dict(row) for row in conn.execute("select content_hash, count(*) as n from documents group by content_hash having n > 1").fetchall()]
        return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "docs": docs, "chunks": chunks, "embeddings": embeddings, "orphan_chunks": orphan_chunks, "orphan_embeddings": orphan_embeddings, "duplicate_hashes": duplicate_hashes}

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

    def _psycopg(self) -> Any:
        try:
            return importlib.import_module("psycopg")
        except Exception as exc:  # noqa: BLE001 - optional dependency boundary
            raise RuntimeError("psycopg_missing") from exc

    def _connect(self) -> Any:
        if not self.config.enabled:
            raise RuntimeError("pgvector_disabled")
        if not self.config.dsn:
            raise RuntimeError("dsn_missing")
        return self._psycopg().connect(self.config.dsn, connect_timeout=5)

    def _run(self, operation: str, callback: Any) -> dict[str, Any]:
        try:
            with self._connect() as conn:
                result = callback(conn)
                if hasattr(conn, "commit"):
                    conn.commit()
            return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "operation": operation, "dsn": redact_dsn(self.config.dsn), **(result or {})}
        except Exception as exc:  # noqa: BLE001 - live store boundary
            return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": False, "status": "blocked", "operation": operation, "error": str(exc), "dsn": redact_dsn(self.config.dsn)}

    def status(self) -> dict[str, Any]:
        payload = {
            "schema": RAG_STORE_SCHEMA,
            "backend": self.backend,
            "ok": bool(self.config.enabled and self.config.dsn),
            "status": "ready" if self.config.enabled and self.config.dsn else "configured_offline",
            "config": self.config.to_dict(),
            "dsn": redact_dsn(self.config.dsn),
            "sql_preview": build_pgvector_schema_sql(self.config),
            "capabilities": ["schema_preview", "live_readiness", "live_sources", "live_upsert_document", "live_upsert_chunks", "live_upsert_vectors", "live_vector_search"],
        }
        if self.config.enabled and self.config.dsn:
            live = self._run("status", self._status_callback)
            payload["live"] = live
            if live.get("ok"):
                payload.update({"documents": live.get("documents", 0), "chunks": live.get("chunks", 0), "vectors": live.get("vectors", 0), "providers": live.get("providers", [])})
        return payload

    def _status_callback(self, conn: Any) -> dict[str, Any]:
        with conn.cursor() as cur:
            cur.execute(f"select count(*) from {self._table('documents')}")
            docs = int(cur.fetchone()[0])
            cur.execute(f"select count(*) from {self._table('chunks')}")
            chunks = int(cur.fetchone()[0])
            cur.execute(f"select count(*) from {self._table('chunk_embeddings')}")
            vectors = int(cur.fetchone()[0])
            cur.execute(f"select provider, dimensions, count(*) from {self._table('chunk_embeddings')} group by provider, dimensions order by provider, dimensions")
            providers = [{"provider": row[0], "dimensions": int(row[1]), "vectors": int(row[2])} for row in cur.fetchall()]
        return {"documents": docs, "chunks": chunks, "vectors": vectors, "providers": providers}

    def sources(self) -> dict[str, Any]:
        def callback(conn: Any) -> dict[str, Any]:
            with conn.cursor() as cur:
                cur.execute(
                    f"select d.id, d.source, d.title, d.content_hash, d.created_at, d.metadata_json, count(c.id) as chunks from {self._table('documents')} d left join {self._table('chunks')} c on c.document_id = d.id group by d.id, d.source, d.title, d.content_hash, d.created_at, d.metadata_json order by d.created_at desc, d.title"
                )
                sources = []
                for row in cur.fetchall():
                    metadata = _coerce_metadata(row[5])
                    metadata["chunks"] = int(row[6])
                    sources.append(RagDocumentRecord(str(row[0]), str(row[1]), str(row[2]), str(row[3]), str(row[4]), metadata).to_dict())
            return {"sources": sources, "documents": len(sources)}

        return self._run("sources", callback)

    def upsert_document(self, document: RagDocumentRecord) -> dict[str, Any]:
        def callback(conn: Any) -> dict[str, Any]:
            with conn.cursor() as cur:
                cur.execute(self.build_upsert_document_sql(), (document.id, document.source, document.title, document.content_hash, document.created_at, json.dumps(document.metadata, ensure_ascii=False, sort_keys=True)))
            return {"document_id": document.id}

        return self._run("upsert_document", callback)

    def upsert_chunks(self, chunks: list[RagChunkRecord]) -> dict[str, Any]:
        def callback(conn: Any) -> dict[str, Any]:
            with conn.cursor() as cur:
                sql = self.build_upsert_chunk_sql()
                for chunk in chunks:
                    cur.execute(sql, (chunk.id, chunk.document_id, chunk.ordinal, chunk.text, chunk.char_start, chunk.char_end, json.dumps(chunk.tokens, ensure_ascii=False), chunk.token_count, chunk.created_at))
            return {"chunks": len(chunks)}

        return self._run("upsert_chunks", callback)

    def upsert_vectors(self, vectors: list[RagVectorRecord]) -> dict[str, Any]:
        def callback(conn: Any) -> dict[str, Any]:
            with conn.cursor() as cur:
                sql = self.build_upsert_vector_sql()
                for vector in vectors:
                    cur.execute(sql, (vector.chunk_id, vector.provider, vector.dimensions, _vector_literal(vector.vector), vector.created_at))
            return {"vectors": len(vectors)}

        return self._run("upsert_vectors", callback)

    def vector_search(self, query_vector: list[float], *, limit: int = 5, provider: str | None = None) -> dict[str, Any]:
        if not query_vector:
            return {"schema": RAG_STORE_SCHEMA, "backend": self.backend, "ok": True, "status": "pass", "operation": "vector_search", "hit_count": 0, "hits": []}
        query_literal = _vector_literal(query_vector)
        dimensions = len(query_vector)
        sql = self.build_vector_search_sql(provider=provider)

        def callback(conn: Any) -> dict[str, Any]:
            params: list[Any] = [query_literal, dimensions]
            if provider:
                params.append(provider)
            params.extend([query_literal, max(1, int(limit))])
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                hits = [RagVectorHit(str(row[0]), str(row[1]), str(row[2]), str(row[3]), float(row[7]), str(row[4]), str(row[5]), int(row[6])).to_dict() for row in cur.fetchall()]
            return {"query_dimensions": dimensions, "hit_count": len(hits), "hits": hits}

        result = self._run("vector_search", callback)
        result["sql"] = sql
        result["params"] = {"limit": max(1, int(limit)), "provider": provider, "dimensions": dimensions}
        return result


    def delete_document_payload(self, document_id: str) -> dict[str, Any]:
        def callback(conn: Any) -> dict[str, Any]:
            with conn.cursor() as cur:
                cur.execute(f"select count(*) from {self._table('chunks')} where document_id = %s", (document_id,))
                deleted_chunks = int(cur.fetchone()[0])
                cur.execute(f"delete from {self._table('chunks')} where document_id = %s", (document_id,))
            return {"document_id": document_id, "deleted_chunks": deleted_chunks}
        return self._run("delete_document_payload", callback)

    def all_chunks(self) -> dict[str, Any]:
        def callback(conn: Any) -> dict[str, Any]:
            with conn.cursor() as cur:
                cur.execute(f"select c.id as chunk_id, c.document_id, c.ordinal, c.text, c.char_start, c.char_end, c.token_json, c.token_count, d.source, d.title, d.metadata_json from {self._table('chunks')} c join {self._table('documents')} d on d.id = c.document_id order by d.created_at desc, c.ordinal")
                chunks = []
                for row in cur.fetchall():
                    chunks.append({"chunk_id": str(row[0]), "document_id": str(row[1]), "ordinal": int(row[2]), "text": str(row[3]), "char_start": int(row[4]), "char_end": int(row[5]), "token_json": json.dumps(_coerce_metadata(row[6]) if isinstance(row[6], dict) else row[6], ensure_ascii=False) if not isinstance(row[6], str) else row[6], "token_count": int(row[7]), "source": str(row[8]), "title": str(row[9]), "metadata_json": json.dumps(_coerce_metadata(row[10]), ensure_ascii=False)})
            return {"chunks": chunks}
        return self._run("all_chunks", callback)

    def embedding_summary(self) -> dict[str, Any]:
        def callback(conn: Any) -> dict[str, Any]:
            with conn.cursor() as cur:
                cur.execute(f"select provider, dimensions, count(*) from {self._table('chunk_embeddings')} group by provider, dimensions order by provider")
                providers = [{"provider": str(row[0]), "dimensions": int(row[1]), "chunks": int(row[2])} for row in cur.fetchall()]
            return {"providers": providers}
        return self._run("embedding_summary", callback)

    def validation_snapshot(self) -> dict[str, Any]:
        def callback(conn: Any) -> dict[str, Any]:
            with conn.cursor() as cur:
                cur.execute(f"select id, source, title, content_hash from {self._table('documents')}")
                docs = [{"id": str(r[0]), "source": str(r[1]), "title": str(r[2]), "content_hash": str(r[3])} for r in cur.fetchall()]
                cur.execute(f"select id, document_id, text, char_start, char_end, token_count, token_json from {self._table('chunks')}")
                chunks = [{"id": str(r[0]), "document_id": str(r[1]), "text": str(r[2]), "char_start": int(r[3]), "char_end": int(r[4]), "token_count": int(r[5]), "token_json": json.dumps(r[6], ensure_ascii=False) if not isinstance(r[6], str) else r[6]} for r in cur.fetchall()]
                cur.execute(f"select chunk_id, provider, dimensions, embedding::text from {self._table('chunk_embeddings')}")
                embeddings = [{"chunk_id": str(r[0]), "provider": str(r[1]), "dimensions": int(r[2]), "vector_json": _pgvector_text_to_json(str(r[3]))} for r in cur.fetchall()]
                cur.execute(f"select c.id from {self._table('chunks')} c left join {self._table('documents')} d on d.id = c.document_id where d.id is null")
                orphan_chunks = [{"id": str(r[0])} for r in cur.fetchall()]
                cur.execute(f"select e.chunk_id from {self._table('chunk_embeddings')} e left join {self._table('chunks')} c on c.id = e.chunk_id where c.id is null")
                orphan_embeddings = [{"chunk_id": str(r[0])} for r in cur.fetchall()]
                cur.execute(f"select content_hash, count(*) from {self._table('documents')} group by content_hash having count(*) > 1")
                duplicate_hashes = [{"content_hash": str(r[0]), "n": int(r[1])} for r in cur.fetchall()]
            return {"docs": docs, "chunks": chunks, "embeddings": embeddings, "orphan_chunks": orphan_chunks, "orphan_embeddings": orphan_embeddings, "duplicate_hashes": duplicate_hashes}
        return self._run("validation_snapshot", callback)

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


def _vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(float(v)) for v in vector) + "]"


def _coerce_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if value is None:
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {"raw": str(value)}
    return parsed if isinstance(parsed, dict) else {"value": parsed}


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


def _pgvector_text_to_json(value: str) -> str:
    cleaned = (value or "").strip()
    if cleaned.startswith("[") and cleaned.endswith("]"):
        return cleaned
    return "[" + cleaned.strip("[]") + "]"
