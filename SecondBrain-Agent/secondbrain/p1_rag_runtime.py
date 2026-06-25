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
from secondbrain.p3_rag_store import RagChunkRecord, RagDocumentRecord, RagVectorRecord, create_rag_store

SCHEMA_VERSION = "secondbrain.p1_rag.v2"
P1_PRODUCTION_SCHEMA = "secondbrain.p1_production.v1"
P1_PARSE_EVENT_SCHEMA = "secondbrain.p1_parse_event.v1"
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
    value = "manual" if source is None else source.strip()
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
        self.rag_store = create_rag_store(self.root, sqlite_db_path=self.db_path)
        if self.rag_store.backend == "sqlite":
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

    def _delete_document_payload(self, document_id: str) -> None:
        result = self.rag_store.delete_document_payload(document_id)
        if not result.get("ok"):
            raise RuntimeError(f"rag_store_delete_failed:{result.get('error', result.get('status'))}")

    def _embedding_provider_blocker(self, operation: str) -> dict[str, Any] | None:
        status = self.embedding_provider.status()
        is_network_provider = bool(status.get("network"))
        fallback_allowed = bool(status.get("fallback_allowed"))
        if is_network_provider and not bool(status.get("ok")) and not fallback_allowed:
            return {
                "schema": SCHEMA_VERSION,
                "ok": False,
                "status": "blocked",
                "error": "embedding_provider_unhealthy",
                "operation": operation,
                "provider": status,
                "remediation": "fix the configured embedding provider or set SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK=true for explicit offline fallback",
            }
        return None

    def _embedding_failure_payload(self, operation: str, exc: Exception) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "ok": False,
            "status": "blocked",
            "error": "embedding_generation_failed",
            "operation": operation,
            "provider": self.embedding_provider.status(),
            "detail": str(exc),
        }

    def ingest_text(self, text: str, source: str = "manual", title: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        provider_blocker = self._embedding_provider_blocker("ingest_text")
        if provider_blocker:
            return provider_blocker
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
        normalized_text = re.sub(r"\s+", " ", text or "").strip()
        spans: list[tuple[int, int]] = []
        cursor = 0
        for chunk in chunks:
            found = normalized_text.find(chunk, cursor)
            if found < 0:
                found = cursor
            spans.append((found, found + len(chunk)))
            cursor = max(found + 1, found + len(chunk) - DEFAULT_OVERLAP)

        document = RagDocumentRecord(document_id, source_check["source"], title_value, content_hash, now, metadata or {})
        chunk_records: list[RagChunkRecord] = []
        vector_records: list[RagVectorRecord] = []
        for idx, chunk in enumerate(chunks):
            tokens = tokenize(chunk)
            chunk_hash = fingerprint(f"{document_id}:{idx}:{chunk}")[:16]
            chunk_id = f"chk_{chunk_hash}"
            char_start, char_end = spans[idx]
            try:
                vector = self.embedding_provider.embed(chunk)
            except Exception as exc:  # noqa: BLE001 - provider boundary
                return self._embedding_failure_payload("ingest_text", exc)
            chunk_records.append(RagChunkRecord(chunk_id, document_id, idx, chunk, char_start, char_end, tokens, len(tokens), now))
            vector_records.append(RagVectorRecord(chunk_id, self.embedding_provider.name, len(vector), vector, now))

        self._delete_document_payload(document_id)
        doc_result = self.rag_store.upsert_document(document)
        chunk_result = self.rag_store.upsert_chunks(chunk_records)
        vector_result = self.rag_store.upsert_vectors(vector_records)
        ok = bool(doc_result.get("ok")) and bool(chunk_result.get("ok")) and bool(vector_result.get("ok"))
        return {"schema": SCHEMA_VERSION, "ok": ok, "status": "pass" if ok else "blocked", "document_id": document_id, "source": source_check["source"], "title": title_value, "chunks": len(chunks), "content_hash": content_hash, "metadata": metadata or {}, "store": {"backend": self.rag_store.backend, "write_path": "rag_store", "document": doc_result, "chunks": chunk_result, "vectors": vector_result}}

    def _parse_event(self, parsed: Any, path: Path, title: str | None = None) -> dict[str, Any]:
        payload = parsed.to_ingestion_payload()
        return {
            "schema": P1_PARSE_EVENT_SCHEMA,
            "status": parsed.status.value,
            "ok": parsed.status == ParseStatus.PARSED and bool(payload["text"].strip()),
            "path": str(path),
            "title": title or payload["title"],
            "source_path": payload["source_path"],
            "mime_type": parsed.mime_type,
            "pages": parsed.page_count,
            "chars": parsed.char_count,
            "requires_ocr": parsed.status == ParseStatus.OCR_REQUIRED or bool(payload["metadata"].get("ocr_required")),
            "metadata": payload["metadata"],
            "errors": payload["errors"],
        }

    def _parse_blocked_payload(self, *, path: Path, error: str, parsed: Any, title: str | None = None) -> dict[str, Any]:
        parse = self._parse_event(parsed, path, title)
        metadata = {"path": str(path), "ingest_mode": "parser_registry", "mime_type": parse["mime_type"], **parse["metadata"]}
        if parse["errors"]:
            metadata["parse_errors"] = parse["errors"]
        if parse["requires_ocr"]:
            metadata["ocr_required"] = True
        return {
            "schema": SCHEMA_VERSION,
            "ok": False,
            "status": "blocked",
            "error": error,
            "path": str(path),
            "title": parse["title"],
            "metadata": metadata,
            "errors": parse["errors"],
            "parse": parse,
        }

    def ingest_file(self, file_path: str | Path, source: str | None = None, title: str | None = None) -> dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": "file_not_found", "path": str(path)}
        if not path.is_file():
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": "not_a_file", "path": str(path)}
        parsed = self.parser_registry.parse(path)
        payload = parsed.to_ingestion_payload()
        parse = self._parse_event(parsed, path, title)
        metadata = {"path": str(path), "ingest_mode": "parser_registry", "mime_type": payload["mime_type"], **payload["metadata"]}
        if payload["errors"]:
            metadata["parse_errors"] = payload["errors"]
        if parse["requires_ocr"]:
            metadata["ocr_required"] = True
        if parsed.status == ParseStatus.OCR_REQUIRED:
            return self._parse_blocked_payload(path=path, error="ocr_required", parsed=parsed, title=title)
        if parsed.status == ParseStatus.UNSUPPORTED:
            return self._parse_blocked_payload(path=path, error="unsupported_file_type", parsed=parsed, title=title)
        if parsed.status == ParseStatus.FAILED:
            return self._parse_blocked_payload(path=path, error="parse_failed", parsed=parsed, title=title)
        if parsed.status == ParseStatus.EMPTY or not payload["text"].strip():
            return self._parse_blocked_payload(path=path, error="empty_text", parsed=parsed, title=title)
        result = self.ingest_text(payload["text"], source or payload["source_path"] or str(path), title or payload["title"], metadata)
        result["parse"] = parse
        return result

    def ingest_directory(self, directory_path: str | Path, recursive: bool = False, source_prefix: str | None = None) -> dict[str, Any]:
        directory = Path(directory_path)
        if not directory.exists():
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": "directory_not_found", "path": str(directory)}
        if not directory.is_dir():
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": "not_a_directory", "path": str(directory)}
        pattern = "**/*" if recursive else "*"
        files = sorted(path for path in directory.glob(pattern) if path.is_file())
        results = []
        counts = Counter()
        for file in files:
            source = f"{source_prefix.rstrip('/')}/{file.name}" if source_prefix else None
            item = self.ingest_file(file, source=source)
            results.append(item)
            counts[item.get("error") or item.get("status", "unknown")] += 1
        blocked = sum(1 for item in results if not item.get("ok"))
        return {
            "schema": "secondbrain.p1_rag.directory_ingest.v1",
            "ok": blocked == 0,
            "status": "pass" if blocked == 0 else "blocked",
            "path": str(directory),
            "recursive": recursive,
            "files": len(files),
            "ingested": len(files) - blocked,
            "blocked": blocked,
            "counts": dict(counts),
            "results": results,
        }

    def _all_chunks(self) -> list[dict[str, Any]]:
        result = self.rag_store.all_chunks()
        if not result.get("ok"):
            return []
        return list(result.get("chunks", []))

    def embedding_status(self) -> dict[str, Any]:
        summary = self.rag_store.embedding_summary()
        return {"schema": "secondbrain.p1_embeddings.status.v1", "ok": bool(summary.get("ok", True)), "status": "pass" if summary.get("ok", True) else "blocked", "provider": self.embedding_provider.status(), "indexed_vectors": list(summary.get("providers", [])), "store": {"backend": self.rag_store.backend, "summary": summary}}

    def reindex_vectors(self, write_report: bool = False) -> dict[str, Any]:
        provider_blocker = self._embedding_provider_blocker("reindex_vectors")
        if provider_blocker:
            return provider_blocker
        now = utc_now()
        vector_records: list[RagVectorRecord] = []
        chunks = self._all_chunks()
        for row in chunks:
            try:
                vector = self.embedding_provider.embed(row["text"])
            except Exception as exc:  # noqa: BLE001 - provider boundary
                return self._embedding_failure_payload("reindex_vectors", exc)
            vector_records.append(RagVectorRecord(row["chunk_id"], self.embedding_provider.name, len(vector), vector, now))
        result = self.rag_store.upsert_vectors(vector_records)
        payload = {"schema": "secondbrain.p1_vectors.reindex.v1", "generated_at": now, "ok": bool(result.get("ok")), "status": "pass" if result.get("ok") else "blocked", "chunks": len(chunks), "provider": self.embedding_provider.name, "store": {"backend": self.rag_store.backend, "write_path": "rag_store", "vectors": result}}
        if write_report:
            path = self.reports_dir / "p1_vector_reindex_latest.json"
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
        return payload

    def vector_search(self, query: str, limit: int = 5) -> dict[str, Any]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return {"schema": "secondbrain.p1_vectors.search.v1", "ok": False, "status": "blocked", "error": "empty_query", "hits": []}
        provider_blocker = self._embedding_provider_blocker("vector_search")
        if provider_blocker:
            return {**provider_blocker, "schema": "secondbrain.p1_vectors.search.v1", "query": query, "hits": []}
        try:
            q_vector = self.embedding_provider.embed(query)
        except Exception as exc:  # noqa: BLE001 - provider boundary
            return {**self._embedding_failure_payload("vector_search", exc), "schema": "secondbrain.p1_vectors.search.v1", "query": query, "hits": []}
        store_result = self.rag_store.vector_search(
            q_vector,
            limit=max(1, int(limit)),
            provider=self.embedding_provider.name,
        )
        if not store_result.get("ok"):
            return {
                "schema": "secondbrain.p1_vectors.search.v1",
                "ok": False,
                "status": "blocked",
                "query": query,
                "limit": limit,
                "hit_count": 0,
                "hits": [],
                "store": store_result,
            }
        hits = []
        for hit in store_result.get("hits", []):
            text = str(hit.get("text", ""))
            hits.append({
                "chunk_id": hit.get("chunk_id"),
                "document_id": hit.get("document_id"),
                "source": hit.get("source"),
                "title": hit.get("title"),
                "score": round(float(hit.get("score", 0.0)), 4),
                "text": text,
                "snippet": summarize_text(text, 260),
                "char_start": int(hit.get("char_start", 0) or 0),
                "char_end": int(hit.get("char_end", 0) or 0),
                "provider": hit.get("provider"),
                "dimensions": hit.get("dimensions"),
            })
        return {
            "schema": "secondbrain.p1_vectors.search.v1",
            "ok": True,
            "status": "pass",
            "query": query,
            "limit": limit,
            "hit_count": len(hits),
            "hits": hits,
            "store": {"backend": self.rag_store.backend, "result": store_result},
        }

    def hybrid_search(self, query: str, limit: int = 5) -> dict[str, Any]:
        keyword = self.search(query, limit=max(limit * 2, 5))
        vector = self.vector_search(query, limit=max(limit * 2, 5))
        keyword_hits = [dict(hit, retrieval_source="keyword") for hit in keyword.get("hits", [])]
        vector_hits = [dict(hit, retrieval_source="vector") for hit in vector.get("hits", [])]
        fused = reciprocal_rank_fusion([keyword_hits, vector_hits], weights=[1.15, 1.0])
        hits = fused[: max(1, int(limit))]
        for hit in hits:
            keyword_score = float(hit.get("raw_scores", {}).get("keyword", hit.get("keyword_score", 0.0)))
            vector_score = float(hit.get("raw_scores", {}).get("vector", hit.get("vector_score", 0.0)))
            hit["keyword_score"] = round(keyword_score, 4)
            hit["vector_score"] = round(vector_score, 4)
            hit["hybrid_score"] = round(float(hit.get("rrf_score", 0.0)), 6)
            hit["score"] = hit["hybrid_score"]
        return {"schema": "secondbrain.p1_hybrid.search.v1", "ok": bool(keyword.get("ok")) and bool(vector.get("ok")), "status": "pass" if vector.get("ok") else "blocked", "query": query, "limit": limit, "hit_count": len(hits), "hits": hits, "models": {"keyword": "tfidf_logtf_length_norm_v1", "vector": self.embedding_provider.name, "fusion": "rrf_v1"}, "vector_status": vector.get("status")}

    def retrieval_metrics(self, write_report: bool = False) -> dict[str, Any]:
        probes = [{"query": "Jarvis RAG Quellen", "expected_terms": ["jarvis", "rag", "quellen"]}, {"query": "Memory Evidenz", "expected_terms": ["memory", "evidenz"]}, {"query": "lokale Quellen", "expected_terms": ["lokale", "quellen"]}]
        rows = []
        for probe in probes:
            result = self.hybrid_search(probe["query"], 10)
            metrics = evaluate_ranked_hits(result.get("hits", []), probe["expected_terms"], k=10)
            answer = self.answer(probe["query"], 4)
            rows.append({"query": probe["query"], "hit_count": result.get("hit_count", 0), "confidence": answer.get("confidence", 0.0), **metrics})
        n = max(1, len(rows))
        payload = {"schema": "secondbrain.p1_retrieval.metrics.v1", "generated_at": utc_now(), "ok": True, "status": "pass", "probes": len(rows), "hit_rate": round(sum(1 for row in rows if row["hit_count"] > 0) / n, 4), "avg_recall_at_k": round(sum(float(row["recall_at_k"]) for row in rows) / n, 4), "avg_mrr": round(sum(float(row["mrr"]) for row in rows) / n, 4), "avg_ndcg": round(sum(float(row["ndcg"]) for row in rows) / n, 4), "avg_confidence": round(sum(float(row["confidence"]) for row in rows) / n, 4), "results": rows}
        if write_report:
            path = self.reports_dir / "p1_retrieval_metrics_latest.json"
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
        return payload

    def retrieval_benchmark(self, write_report: bool = False) -> dict[str, Any]:
        metrics = self.retrieval_metrics(write_report=False)
        payload = {"schema": "secondbrain.p1_retrieval.benchmark.v1", "generated_at": utc_now(), "ok": metrics["ok"], "status": metrics["status"], "probes": metrics["probes"], "hit_rate": metrics["hit_rate"], "avg_recall_at_k": metrics["avg_recall_at_k"], "avg_mrr": metrics["avg_mrr"], "avg_ndcg": metrics["avg_ndcg"], "results": [{"query": r["query"], "hit_count": r["hit_count"], "recall_at_k": r["recall_at_k"], "mrr": r["mrr"], "ndcg": r["ndcg"]} for r in metrics["results"]]}
        if write_report:
            path = self.reports_dir / "p1_retrieval_benchmark_latest.json"
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
        return payload

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": "empty_query", "hits": []}
        q_counts = Counter(query_tokens)
        rows = self._all_chunks()
        doc_freq: Counter[str] = Counter()
        for row in rows:
            for term in set(json.loads(row["token_json"])):
                doc_freq[term] += 1
        total_chunks = max(1, len(rows))
        hits: list[SearchHit] = []
        for row in rows:
            tokens = json.loads(row["token_json"])
            counts = Counter(tokens)
            score = 0.0
            matched: list[str] = []
            for term, q_weight in q_counts.items():
                tf = counts.get(term, 0)
                if not tf:
                    continue
                idf = math.log((1 + total_chunks) / (1 + doc_freq.get(term, 0))) + 1.0
                score += (1 + math.log(tf)) * idf * q_weight
                matched.append(term)
            if score <= 0:
                continue
            normalized = score / math.sqrt(max(1, row["token_count"]))
            hits.append(SearchHit(row["chunk_id"], row["document_id"], row["source"], row["title"], normalized, row["text"], sorted(set(matched)), int(row["char_start"]), int(row["char_end"])))
        hits.sort(key=lambda h: (-h.score, h.title, h.chunk_id))
        selected = hits[: max(1, int(limit))]
        return {"schema": SCHEMA_VERSION, "ok": True, "status": "pass", "query": query, "limit": limit, "hit_count": len(selected), "hits": [h.to_dict() for h in selected]}

    def answer(self, query: str, limit: int = 4) -> dict[str, Any]:
        search = self.search(query, limit)
        if not search.get("ok"):
            return search
        hits = search["hits"]
        if not hits:
            return {"schema": SCHEMA_VERSION, "ok": True, "status": "no_evidence", "query": query, "answer": "Keine belastbare Quelle im lokalen RAG-Index gefunden.", "citations": [], "confidence": 0.0}
        bullets = []
        citations = []
        for idx, hit in enumerate(hits, 1):
            snippet = hit["text"][:320].strip()
            bullets.append(f"[{idx}] {snippet}")
            citations.append({"ref": idx, "chunk_id": hit["chunk_id"], "document_id": hit["document_id"], "source": hit["source"], "title": hit["title"], "score": hit["score"]})
        confidence = min(0.95, max(0.15, sum(float(h["score"]) for h in hits) / max(1, len(hits))))
        return {"schema": SCHEMA_VERSION, "ok": True, "status": "pass", "query": query, "answer": "\n".join(bullets), "citations": citations, "confidence": round(confidence, 4)}

    def sources(self) -> dict[str, Any]:
        result = self.rag_store.sources()
        if not result.get("ok"):
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "documents": 0, "sources": [], "store": result}
        rows = self._all_chunks()
        tokens_by_doc: Counter[str] = Counter()
        for row in rows:
            tokens_by_doc[row["document_id"]] += int(row.get("token_count", 0))
        items = []
        for source in result.get("sources", []):
            document_id = source.get("id") or source.get("document_id")
            metadata = dict(source.get("metadata") or {})
            chunks = int(metadata.pop("chunks", source.get("chunks", 0) or 0))
            items.append({"document_id": document_id, "source": source.get("source"), "title": source.get("title"), "content_hash": source.get("content_hash"), "created_at": source.get("created_at"), "chunks": chunks, "tokens": int(tokens_by_doc.get(document_id, 0)), "metadata": metadata})
        return {"schema": SCHEMA_VERSION, "ok": True, "status": "pass", "documents": len(items), "sources": items, "store": {"backend": self.rag_store.backend}}

    def explain(self, query: str, limit: int = 5) -> dict[str, Any]:
        result = self.search(query, limit)
        if not result.get("ok"):
            return result
        return {"schema": "secondbrain.p1_rag.explain.v1", "ok": True, "status": "pass", "query": query, "tokenized_query": tokenize(query), "ranking_model": "deterministic_tfidf_logtf_length_norm_v1", "hit_count": result["hit_count"], "hits": [{"rank": idx, "chunk_id": hit["chunk_id"], "document_id": hit["document_id"], "title": hit["title"], "score": hit["score"], "matched_terms": hit["terms"], "char_range": [hit["char_start"], hit["char_end"]], "snippet": hit["snippet"]} for idx, hit in enumerate(result["hits"], 1)]}

    def status(self) -> dict[str, Any]:
        store_status = self.rag_store.status()
        rows = self._all_chunks()
        docs = int(store_status.get("documents", 0)) if "documents" in store_status else len({row["document_id"] for row in rows})
        chunks = int(store_status.get("chunks", len(rows)))
        tokens = sum(int(row.get("token_count", 0)) for row in rows)
        avg_tokens = tokens / max(1, chunks)
        schema_cols = ["id", "document_id", "ordinal", "text", "char_start", "char_end", "token_json", "token_count", "created_at"]
        return {"schema": SCHEMA_VERSION, "ok": bool(store_status.get("ok", True)), "status": "pass" if store_status.get("ok", True) else "blocked", "profile": self.profile, "db_path": str(self.db_path), "documents": docs, "chunks": chunks, "tokens": tokens, "avg_tokens_per_chunk": round(float(avg_tokens), 2), "chunk_schema_columns": schema_cols, "embedding_provider": self.embedding_provider.status(), "store": store_status, "capabilities": ["ingest_text", "ingest_file", "search", "vector_search", "hybrid_search", "answer", "sources", "explain", "validate_index", "quality_report", "retrieval_metrics", "retrieval_benchmark", "production_gate", "gate"]}

    def validate_index(self, write_report: bool = False) -> dict[str, Any]:
        snapshot = self.rag_store.validation_snapshot()
        if not snapshot.get("ok"):
            payload = {"schema": "secondbrain.p1_rag.validation.v1", "generated_at": utc_now(), "ok": False, "status": "blocked", "documents": 0, "chunks": 0, "embeddings": 0, "blockers": 1, "warnings": 0, "findings": [{"severity": "blocker", "code": "store_validation_snapshot_failed", "detail": snapshot}]}
            if write_report:
                path = self.reports_dir / "p1_rag_validation_latest.json"
                path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
                payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
            return payload
        docs = list(snapshot.get("docs", []))
        chunks = list(snapshot.get("chunks", []))
        embeddings = list(snapshot.get("embeddings", []))
        embedded_ids = {row["chunk_id"] for row in embeddings}
        orphan_chunks = list(snapshot.get("orphan_chunks", []))
        orphan_embeddings = list(snapshot.get("orphan_embeddings", []))
        duplicate_hashes = list(snapshot.get("duplicate_hashes", []))
        findings: list[dict[str, Any]] = []
        for row in docs:
            src = validate_source(row["source"])
            if not src["ok"]:
                findings.append({"severity": "blocker", "code": "invalid_source", "document_id": row["id"], "detail": src})
            if not row["title"].strip():
                findings.append({"severity": "warning", "code": "empty_title", "document_id": row["id"]})
        for row in chunks:
            if not (row["text"] or "").strip():
                findings.append({"severity": "blocker", "code": "empty_chunk", "chunk_id": row["id"]})
            if int(row["char_end"]) < int(row["char_start"]):
                findings.append({"severity": "blocker", "code": "invalid_char_range", "chunk_id": row["id"], "range": [row["char_start"], row["char_end"]]})
            try:
                parsed_tokens = json.loads(row["token_json"] or "[]")
            except json.JSONDecodeError:
                parsed_tokens = None
            if not isinstance(parsed_tokens, list):
                findings.append({"severity": "blocker", "code": "invalid_token_json", "chunk_id": row["id"]})
            elif len(parsed_tokens) != int(row["token_count"]):
                findings.append({"severity": "warning", "code": "token_count_mismatch", "chunk_id": row["id"], "actual": len(parsed_tokens), "stored": int(row["token_count"])})
        for row in chunks:
            if row["id"] not in embedded_ids:
                findings.append({"severity": "blocker", "code": "missing_embedding", "chunk_id": row["id"]})
        for row in embeddings:
            try:
                vector = json.loads(row["vector_json"] or "[]")
            except json.JSONDecodeError:
                vector = None
            if not isinstance(vector, list) or not vector:
                findings.append({"severity": "blocker", "code": "invalid_embedding", "chunk_id": row["chunk_id"]})
            elif len(vector) != int(row["dimensions"]):
                findings.append({"severity": "blocker", "code": "embedding_dimension_mismatch", "chunk_id": row["chunk_id"]})
        for row in orphan_chunks:
            findings.append({"severity": "blocker", "code": "orphan_chunk", "chunk_id": row["id"]})
        for row in orphan_embeddings:
            findings.append({"severity": "blocker", "code": "orphan_embedding", "chunk_id": row["chunk_id"]})
        for row in duplicate_hashes:
            findings.append({"severity": "warning", "code": "duplicate_content_hash", "content_hash": row["content_hash"], "count": int(row["n"])})
        blockers = sum(1 for f in findings if f["severity"] == "blocker")
        warnings = sum(1 for f in findings if f["severity"] == "warning")
        payload = {"schema": "secondbrain.p1_rag.validation.v1", "generated_at": utc_now(), "ok": blockers == 0, "status": "pass" if blockers == 0 else "blocked", "documents": len(docs), "chunks": len(chunks), "embeddings": len(embeddings), "blockers": blockers, "warnings": warnings, "findings": findings}
        if write_report:
            path = self.reports_dir / "p1_rag_validation_latest.json"
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
        return payload

    def quality_report(self, query: str = "Jarvis RAG Quellen", limit: int = 5, write_report: bool = False) -> dict[str, Any]:
        status = self.status()
        validation = self.validate_index(False)
        search_result = self.search(query, limit) if query.strip() else {"ok": False, "hit_count": 0, "hits": []}
        answer_result = self.answer(query, min(limit, 4)) if query.strip() else {"ok": False, "citations": [], "confidence": 0.0}
        checks = [
            {"name": "index_valid", "ok": validation["ok"], "severity": "blocker", "detail": {"blockers": validation["blockers"], "warnings": validation["warnings"]}},
            {"name": "content_available", "ok": status["chunks"] > 0, "severity": "warning", "detail": {"chunks": status["chunks"], "documents": status["documents"]}},
            {"name": "search_executes", "ok": bool(search_result.get("ok")), "severity": "blocker", "detail": {"hit_count": search_result.get("hit_count", 0)}},
            {"name": "hybrid_search_executes", "ok": bool(self.hybrid_search(query, limit).get("ok")), "severity": "blocker", "detail": {"model": "hybrid_keyword_vector_rrf_v1"}},
            {"name": "answer_has_citations_when_evidence_exists", "ok": (not search_result.get("hits")) or bool(answer_result.get("citations")), "severity": "blocker", "detail": {"citations": len(answer_result.get("citations", [])), "confidence": answer_result.get("confidence", 0.0)}},
            {"name": "no_evidence_is_explicit", "ok": self.answer("zzzxxy_no_local_evidence_probe", 2).get("status") == "no_evidence", "severity": "blocker", "detail": {"policy": "answer_must_not_fabricate_without_hits"}},
        ]
        blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
        warnings = sum(1 for c in checks if not c["ok"] and c["severity"] == "warning")
        payload = {"schema": "secondbrain.p1_rag.quality.v1", "generated_at": utc_now(), "ok": blockers == 0, "status": "pass" if blockers == 0 else "blocked", "query": query, "blockers": blockers, "warnings": warnings, "checks": checks, "rag_status": status}
        if write_report:
            path = self.reports_dir / "p1_rag_quality_latest.json"
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
        return payload

    def gate(self, write_report: bool = False) -> dict[str, Any]:
        status = self.status()
        required_columns = {"id", "document_id", "ordinal", "text", "char_start", "char_end", "token_json", "token_count", "created_at"}
        validation = self.validate_index(False)
        quality = self.quality_report("Jarvis RAG Quellen", 5, False)
        embedding = self.embedding_status()
        checks = [
            {"name": "rag_store_available", "ok": bool(status.get("store", {}).get("ok", status.get("ok"))), "severity": "blocker", "detail": {"backend": self.rag_store.backend, "store_status": status.get("store", {}).get("status")}},
            {"name": "rag_database_exists", "ok": self.rag_store.backend != "sqlite" or self.db_path.exists(), "severity": "blocker", "detail": {"path": str(self.db_path), "backend": self.rag_store.backend}},
            {"name": "rag_schema_ready", "ok": status["ok"] and required_columns.issubset(set(status["chunk_schema_columns"])), "severity": "blocker", "detail": {"columns": status["chunk_schema_columns"], "backend": self.rag_store.backend}},
            {"name": "rag_has_indexed_content", "ok": status["chunks"] > 0, "severity": "warning", "detail": {"chunks": status["chunks"]}},
            {"name": "rag_source_inventory_available", "ok": self.sources()["ok"], "severity": "blocker", "detail": {"documents": status["documents"]}},
            {"name": "rag_explainability_available", "ok": callable(getattr(self, "explain", None)), "severity": "blocker", "detail": {"ranking_model": "deterministic_tfidf_logtf_length_norm_v1"}},
            {"name": "rag_index_validation", "ok": validation["ok"], "severity": "blocker", "detail": {"blockers": validation["blockers"], "warnings": validation["warnings"]}},
            {"name": "rag_quality_policy", "ok": quality["ok"], "severity": "blocker", "detail": {"blockers": quality["blockers"], "warnings": quality["warnings"]}},
            {"name": "embedding_provider_ready", "ok": embedding["provider"].get("ok", False), "severity": "blocker", "detail": embedding["provider"]},
            {"name": "retrieval_benchmark_available", "ok": self.retrieval_benchmark()["ok"], "severity": "warning", "detail": {"schema": "secondbrain.p1_retrieval.benchmark.v1"}},
        ]
        blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
        warnings = sum(1 for c in checks if not c["ok"] and c["severity"] == "warning")
        payload = {"schema": "secondbrain.p1_gate.v4", "generated_at": utc_now(), "ok": blockers == 0, "status": "pass" if blockers == 0 else "blocked", "blockers": blockers, "warnings": warnings, "checks": checks, "rag_status": status, "validation": validation, "quality": quality, "retrieval_metrics": self.retrieval_metrics(False)}
        if write_report:
            path = self.reports_dir / "p1_gate_latest.json"
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
        return payload

    def production_gate(self, write_report: bool = False) -> dict[str, Any]:
        gate = self.gate(False)
        metrics = self.retrieval_metrics(False)
        embedding = self.embedding_status()["provider"]
        decision = production_decision(metrics)
        checks = [
            {"name": "p1_gate_passes", "ok": bool(gate.get("ok")), "severity": "blocker", "detail": {"schema": gate.get("schema"), "blockers": gate.get("blockers"), "warnings": gate.get("warnings")}},
            {"name": "embedding_provider_production_ready", "ok": bool(embedding.get("production_ready")) and not bool(embedding.get("fallback_used")), "severity": "blocker", "detail": embedding},
            {"name": "retrieval_thresholds_pass", "ok": decision["ok"], "severity": "blocker", "detail": decision},
            {"name": "answer_policy_enforced", "ok": self.answer("zzzxxy_no_local_evidence_probe", 2).get("status") == "no_evidence", "severity": "blocker", "detail": {"policy": "no_evidence_must_be_explicit"}},
            {"name": "source_lineage_available", "ok": self.sources().get("ok") and self.status().get("documents", 0) >= 0, "severity": "blocker", "detail": {"documents": self.status().get("documents", 0)}},
        ]
        blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
        payload = {"schema": P1_PRODUCTION_SCHEMA, "generated_at": utc_now(), "ok": blockers == 0, "status": "pass" if blockers == 0 else "blocked", "blockers": blockers, "checks": checks, "gate": gate, "metrics": metrics}
        if write_report:
            path = self.reports_dir / "p1_production_latest.json"
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
        return payload
