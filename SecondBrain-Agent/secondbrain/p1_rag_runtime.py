from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.document_understanding.parser_contract import ParseStatus
from secondbrain.document_understanding.parsers import default_parser_registry
from secondbrain.p1_embeddings import cosine_similarity, provider_from_profile
from secondbrain.p1_retrieval import evaluate_ranked_hits, production_decision, reciprocal_rank_fusion

SCHEMA_VERSION = "secondbrain.p1_rag.v2"
P1_PRODUCTION_SCHEMA = "secondbrain.p1_production.v1"
TOKEN_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9_\-]{2,}")
DEFAULT_CHUNK_SIZE = 900
DEFAULT_OVERLAP = 120


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text or "")]


def fingerprint(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        if end < len(cleaned):
            boundary = cleaned.rfind(". ", start + int(chunk_size * 0.55), end)
            if boundary != -1:
                end = boundary + 1
        part = cleaned[start:end].strip()
        if part:
            chunks.append(part)
        if end >= len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks


def summarize_text(text: str, max_chars: int = 420) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if len(cleaned) <= max_chars:
        return cleaned
    cut = cleaned.rfind(". ", 0, max_chars)
    if cut < int(max_chars * 0.45):
        cut = max_chars
    return cleaned[:cut].strip() + "…"


def validate_source(source: str | None) -> dict[str, Any]:
    if source is None:
        value = "manual"
    else:
        value = source.strip()
    if not value:
        return {"ok": False, "error": "empty_source"}
    if len(value) > 500:
        return {"ok": False, "error": "source_too_long"}
    return {"ok": True, "source": value}


@dataclass(frozen=True)
class SearchHit:
    chunk_id: str
    document_id: str
    source: str
    title: str
    score: float
    text: str
    terms: list[str]
    char_start: int = 0
    char_end: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "source": self.source,
            "title": self.title,
            "score": round(self.score, 4),
            "text": self.text,
            "terms": self.terms,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "snippet": summarize_text(self.text, 260),
        }


class P1RagRuntime:
    def __init__(self, project_root: str | Path, profile: str | None = None):
        self.root = Path(project_root).resolve()
        self.profile = profile or "default"
        self.runtime_dir = self.root / "runtime" / "p1_rag"
        self.db_path = self.runtime_dir / "rag.sqlite3"
        self.reports_dir = self.root / "runtime" / "reports"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_provider = provider_from_profile(self.root, self.profile)
        self.parser_registry = default_parser_registry()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
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
            columns = {row[1] for row in conn.execute("pragma table_info(chunks)").fetchall()}
            if "char_start" not in columns:
                conn.execute("alter table chunks add column char_start integer not null default 0")
            if "char_end" not in columns:
                conn.execute("alter table chunks add column char_end integer not null default 0")
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

    def ingest_text(self, text: str, source: str = "manual", title: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        source_check = validate_source(source)
        if not source_check["ok"]:
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": source_check["error"]}
        chunks = chunk_text(text)
        if not chunks:
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": "empty_text", "chunks": 0}
        content_hash = fingerprint(text)
        document_id = "doc_" + content_hash[:16]
        title_value = title or source_check["source"] or document_id
        now = utc_now()
        spans: list[tuple[int, int]] = []
        cursor = 0
        normalized_text = re.sub(r"\s+", " ", text or "").strip()
        for chunk in chunks:
            found = normalized_text.find(chunk, cursor)
            if found < 0:
                found = cursor
            spans.append((found, found + len(chunk)))
            cursor = max(found + 1, found + len(chunk) - DEFAULT_OVERLAP)
        with self._connect() as conn:
            conn.execute(
                "insert or replace into documents(id, source, title, content_hash, created_at, metadata_json) values (?, ?, ?, ?, ?, ?)",
                (document_id, source_check["source"], title_value, content_hash, now, json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)),
            )
            conn.execute("delete from chunks where document_id = ?", (document_id,))
            for idx, chunk in enumerate(chunks):
                tokens = tokenize(chunk)
                chunk_hash = fingerprint(f"{document_id}:{idx}:{chunk}")[:16]
                chunk_id = f"chk_{chunk_hash}"
                char_start, char_end = spans[idx]
                conn.execute(
                    "insert into chunks(id, document_id, ordinal, text, char_start, char_end, token_json, token_count, created_at) values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (chunk_id, document_id, idx, chunk, char_start, char_end, json.dumps(tokens, ensure_ascii=False), len(tokens), now),
                )
                vector = self.embedding_provider.embed(chunk)
                conn.execute(
                    "insert or replace into chunk_embeddings(chunk_id, provider, dimensions, vector_json, created_at) values (?, ?, ?, ?, ?)",
                    (chunk_id, self.embedding_provider.name, len(vector), json.dumps(vector), now),
                )
            conn.commit()
        return {
            "schema": SCHEMA_VERSION,
            "ok": True,
            "status": "pass",
            "document_id": document_id,
            "source": source_check["source"],
            "title": title_value,
            "chunks": len(chunks),
            "content_hash": content_hash,
            "metadata": metadata or {},
        }

    def ingest_file(self, file_path: str | Path, source: str | None = None, title: str | None = None) -> dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": "file_not_found", "path": str(path)}
        if not path.is_file():
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": "not_a_file", "path": str(path)}

        parsed = self.parser_registry.parse(path)
        payload = parsed.to_ingestion_payload()
        metadata = {
            "path": str(path),
            "ingest_mode": "parser_registry",
            "mime_type": payload["mime_type"],
            **payload["metadata"],
        }
        if payload["errors"]:
            metadata["parse_errors"] = payload["errors"]

        if parsed.status == ParseStatus.OCR_REQUIRED:
            return {
                "schema": SCHEMA_VERSION,
                "ok": False,
                "status": "blocked",
                "error": "ocr_required",
                "path": str(path),
                "title": title or payload["title"],
                "metadata": metadata,
                "errors": payload["errors"],
            }
        if parsed.status == ParseStatus.UNSUPPORTED:
            return {
                "schema": SCHEMA_VERSION,
                "ok": False,
                "status": "blocked",
                "error": "unsupported_file_type",
                "path": str(path),
                "title": title or payload["title"],
                "metadata": metadata,
                "errors": payload["errors"],
            }
        if parsed.status == ParseStatus.FAILED:
            return {
                "schema": SCHEMA_VERSION,
                "ok": False,
                "status": "blocked",
                "error": "parse_failed",
                "path": str(path),
                "title": title or payload["title"],
                "metadata": metadata,
                "errors": payload["errors"],
            }
        if parsed.status == ParseStatus.EMPTY or not payload["text"].strip():
            return {
                "schema": SCHEMA_VERSION,
                "ok": False,
                "status": "blocked",
                "error": "empty_text",
                "path": str(path),
                "title": title or payload["title"],
                "metadata": metadata,
                "errors": payload["errors"],
            }

        result = self.ingest_text(payload["text"], source or payload["source_path"] or str(path), title or payload["title"], metadata)
        result["parse"] = {
            "status": parsed.status.value,
            "mime_type": parsed.mime_type,
            "pages": parsed.page_count,
            "chars": parsed.char_count,
            "errors": payload["errors"],
        }
        return result

    def _all_chunks(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "select c.id as chunk_id, c.document_id, c.ordinal, c.text, c.char_start, c.char_end, c.token_json, c.token_count, d.source, d.title, d.metadata_json from chunks c join documents d on d.id = c.document_id"
            ).fetchall()


    def embedding_status(self) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute("select provider, dimensions, count(*) as n from chunk_embeddings group by provider, dimensions order by provider").fetchall()
        return {
            "schema": "secondbrain.p1_embeddings.status.v1",
            "ok": True,
            "status": "pass",
            "provider": self.embedding_provider.status(),
            "indexed_vectors": [{"provider": r["provider"], "dimensions": int(r["dimensions"]), "chunks": int(r["n"])} for r in rows],
        }

    def reindex_vectors(self, write_report: bool = False) -> dict[str, Any]:
        now = utc_now()
        with self._connect() as conn:
            chunks = conn.execute("select id, text from chunks order by document_id, ordinal").fetchall()
            for row in chunks:
                vector = self.embedding_provider.embed(row["text"])
                conn.execute(
                    "insert or replace into chunk_embeddings(chunk_id, provider, dimensions, vector_json, created_at) values (?, ?, ?, ?, ?)",
                    (row["id"], self.embedding_provider.name, len(vector), json.dumps(vector), now),
                )
            conn.commit()
        payload = {"schema": "secondbrain.p1_vectors.reindex.v1", "generated_at": now, "ok": True, "status": "pass", "chunks": len(chunks), "provider": self.embedding_provider.name}
        if write_report:
            path = self.reports_dir / "p1_vector_reindex_latest.json"
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
        return payload

    def vector_search(self, query: str, limit: int = 5) -> dict[str, Any]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return {"schema": "secondbrain.p1_vectors.search.v1", "ok": False, "status": "blocked", "error": "empty_query", "hits": []}
        q_vector = self.embedding_provider.embed(query)
        with self._connect() as conn:
            rows = conn.execute(
                "select c.id as chunk_id, c.document_id, c.text, c.char_start, c.char_end, d.source, d.title, e.vector_json, e.provider "
                "from chunk_embeddings e join chunks c on c.id = e.chunk_id join documents d on d.id = c.document_id"
            ).fetchall()
        hits = []
        for row in rows:
            try:
                vector = [float(v) for v in json.loads(row["vector_json"])]
            except Exception:
                continue
            score = cosine_similarity(q_vector, vector)
            if score <= 0:
                continue
            hits.append({
                "chunk_id": row["chunk_id"],
                "document_id": row["document_id"],
                "source": row["source"],
                "title": row["title"],
                "score": round(float(score), 4),
                "text": row["text"],
                "snippet": summarize_text(row["text"], 260),
                "char_start": int(row["char_start"]),
                "char_end": int(row["char_end"]),
                "provider": row["provider"],
            })
        hits.sort(key=lambda h: (-h["score"], h["title"], h["chunk_id"]))
        return {"schema": "secondbrain.p1_vectors.search.v1", "ok": True, "status": "pass", "query": query, "limit": limit, "hit_count": len(hits[: max(1, int(limit))]), "hits": hits[: max(1, int(limit))]}

    def hybrid_search(self, query: str, limit: int = 5) -> dict[str, Any]:
        keyword = self.search(query, limit=max(limit * 2, 5))
        vector = self.vector_search(query, limit=max(limit * 2, 5))
        keyword_hits = [dict(hit, retrieval_source="keyword") for hit in keyword.get("hits", [])]
        vector_hits = [dict(hit, retrieval_source="vector") for hit in vector.get("hits", [])]
        fused = reciprocal_rank_fusion(keyword_hits, vector_hits, key="chunk_id", limit=limit)
        return {
            "schema": "secondbrain.p1_hybrid.search.v1",
            "ok": bool(keyword.get("ok") and vector.get("ok")),
            "status": "pass" if keyword.get("ok") and vector.get("ok") else "blocked",
            "query": query,
            "limit": limit,
            "keyword_hits": keyword.get("hit_count", 0),
            "vector_hits": vector.get("hit_count", 0),
            "hit_count": len(fused),
            "hits": fused,
        }

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": "empty_query", "hits": []}
        chunks = self._all_chunks()
        total_docs = max(1, len({row["document_id"] for row in chunks}))
        df = Counter()
        parsed_rows = []
        for row in chunks:
            tokens = json.loads(row["token_json"])
            unique = set(tokens)
            for token in unique:
                df[token] += 1
            parsed_rows.append((row, tokens))
        hits: list[SearchHit] = []
        for row, tokens in parsed_rows:
            counts = Counter(tokens)
            matched = [token for token in query_tokens if token in counts]
            if not matched:
                continue
            score = 0.0
            for token in matched:
                tf = counts[token]
                idf = math.log((1 + total_docs) / (1 + df[token])) + 1.0
                score += tf * idf
            hits.append(SearchHit(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                source=row["source"],
                title=row["title"],
                score=score,
                text=row["text"],
                terms=matched,
                char_start=int(row["char_start"]),
                char_end=int(row["char_end"]),
            ))
        hits.sort(key=lambda h: (-h.score, h.title, h.chunk_id))
        limited = hits[: max(1, int(limit))]
        return {"schema": SCHEMA_VERSION, "ok": True, "status": "pass", "query": query, "hit_count": len(limited), "hits": [hit.to_dict() for hit in limited]}

    def answer(self, query: str, limit: int = 4) -> dict[str, Any]:
        search = self.hybrid_search(query, limit=limit)
        hits = search.get("hits", [])
        if not hits:
            return {"schema": "secondbrain.p1_answer.v1", "ok": True, "status": "no_answer", "query": query, "answer": "Keine belastbare Quelle im lokalen Index gefunden.", "citations": [], "used_chunks": 0}

    def sources(self) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                "select d.id, d.source, d.title, d.content_hash, d.created_at, d.metadata_json, count(c.id) as chunks "
                "from documents d left join chunks c on c.document_id = d.id group by d.id order by d.created_at desc"
            ).fetchall()
        return {
            "schema": "secondbrain.p1_sources.v1",
            "ok": True,
            "status": "pass",
            "sources": [
                {"document_id": r["id"], "source": r["source"], "title": r["title"], "content_hash": r["content_hash"], "created_at": r["created_at"], "chunks": int(r["chunks"]), "metadata": json.loads(r["metadata_json"])} for r in rows
            ],
        }

    def validate_index(self) -> dict[str, Any]:
        with self._connect() as conn:
            docs = conn.execute("select count(*) as n from documents").fetchone()["n"]
            chunks = conn.execute("select count(*) as n from chunks").fetchone()["n"]
            vectors = conn.execute("select count(*) as n from chunk_embeddings").fetchone()["n"]
            orphan_chunks = conn.execute("select count(*) as n from chunks c left join documents d on d.id=c.document_id where d.id is null").fetchone()["n"]
            missing_vectors = conn.execute("select count(*) as n from chunks c left join chunk_embeddings e on e.chunk_id=c.id where e.chunk_id is null").fetchone()["n"]
        issues = []
        if chunks == 0:
            issues.append("no_chunks")
        if missing_vectors:
            issues.append("missing_vectors")
        if orphan_chunks:
            issues.append("orphan_chunks")
        return {"schema": "secondbrain.p1_index.validation.v1", "ok": not issues, "status": "pass" if not issues else "blocked", "documents": docs, "chunks": chunks, "vectors": vectors, "issues": issues}

    def quality_report(self, query: str | None = None) -> dict[str, Any]:
        probes = [
            {"query": query or "second brain runtime health", "expected_terms": ["second", "brain"]},
            {"query": "local memory retrieval", "expected_terms": ["memory"]},
            {"query": "rag search citations", "expected_terms": ["rag", "search"]},
        ]
        evaluations = []
        for probe in probes:
            result = self.hybrid_search(probe["query"], limit=5)
            evaluations.append(evaluate_ranked_hits(probe["query"], result.get("hits", []), expected_terms=probe["expected_terms"]))
        avg_precision = sum(e.precision_at_k for e in evaluations) / len(evaluations)
        avg_coverage = sum(e.expected_term_coverage for e in evaluations) / len(evaluations)
        return {
            "schema": "secondbrain.p1_quality.v1",
            "ok": True,
            "status": "pass" if avg_precision >= 0.1 or avg_coverage >= 0.1 else "warning",
            "provider": self.embedding_provider.status(),
            "evaluations": [e.to_dict() for e in evaluations],
            "average_precision_at_k": round(avg_precision, 4),
            "average_expected_term_coverage": round(avg_coverage, 4),
        }

    def production_gate(self, write_report: bool = True) -> dict[str, Any]:
        validation = self.validate_index()
        quality = self.quality_report()
        embedding = self.embedding_status()
        decision = production_decision({"validation": validation, "quality": quality, "embedding": embedding})
        payload = {
            "schema": P1_PRODUCTION_SCHEMA,
            "generated_at": utc_now(),
            "ok": decision.ok,
            "status": decision.status,
            "summary": decision.summary,
            "checks": decision.checks,
            "validation": validation,
            "quality": quality,
            "embedding": embedding,
        }
        if write_report:
            path = self.reports_dir / "p1_production_latest.json"
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
        return payload

    def gate(self) -> dict[str, Any]:
        production = self.production_gate(write_report=True)
        return {"schema": "secondbrain.p1_gate.v1", "ok": production["ok"], "status": production["status"], "production": production}
