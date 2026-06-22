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

SCHEMA_VERSION = "secondbrain.p1_rag.v1"
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
            conn.execute("create index if not exists idx_chunks_document on chunks(document_id)")
            conn.execute("create index if not exists idx_documents_source on documents(source)")
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
        text = path.read_text(encoding="utf-8", errors="replace")
        return self.ingest_text(text, source or str(path), title or path.name, {"path": str(path)})

    def _all_chunks(self) -> list[sqlite3.Row]:
        with self._connect() as conn:
            return conn.execute(
                "select c.id as chunk_id, c.document_id, c.ordinal, c.text, c.char_start, c.char_end, c.token_json, c.token_count, d.source, d.title, d.metadata_json from chunks c join documents d on d.id = c.document_id"
            ).fetchall()

    def search(self, query: str, limit: int = 5) -> dict[str, Any]:
        query_tokens = tokenize(query)
        if not query_tokens:
            return {"schema": SCHEMA_VERSION, "ok": False, "status": "blocked", "error": "empty_query", "hits": []}
        q_counts = Counter(query_tokens)
        rows = self._all_chunks()
        doc_freq: Counter[str] = Counter()
        token_sets: dict[str, set[str]] = {}
        for row in rows:
            terms = set(json.loads(row["token_json"]))
            token_sets[row["chunk_id"]] = terms
            for term in terms:
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
        with self._connect() as conn:
            rows = conn.execute(
                "select d.id, d.source, d.title, d.content_hash, d.created_at, d.metadata_json, count(c.id) as chunks, coalesce(sum(c.token_count), 0) as tokens "
                "from documents d left join chunks c on c.document_id = d.id group by d.id order by d.created_at desc, d.title"
            ).fetchall()
        items = []
        for row in rows:
            items.append({
                "document_id": row["id"],
                "source": row["source"],
                "title": row["title"],
                "content_hash": row["content_hash"],
                "created_at": row["created_at"],
                "chunks": int(row["chunks"]),
                "tokens": int(row["tokens"]),
                "metadata": json.loads(row["metadata_json"] or "{}"),
            })
        return {"schema": SCHEMA_VERSION, "ok": True, "status": "pass", "documents": len(items), "sources": items}

    def explain(self, query: str, limit: int = 5) -> dict[str, Any]:
        result = self.search(query, limit)
        if not result.get("ok"):
            return result
        return {
            "schema": "secondbrain.p1_rag.explain.v1",
            "ok": True,
            "status": "pass",
            "query": query,
            "tokenized_query": tokenize(query),
            "ranking_model": "deterministic_tfidf_logtf_length_norm_v1",
            "hit_count": result["hit_count"],
            "hits": [
                {
                    "rank": idx,
                    "chunk_id": hit["chunk_id"],
                    "document_id": hit["document_id"],
                    "title": hit["title"],
                    "score": hit["score"],
                    "matched_terms": hit["terms"],
                    "char_range": [hit["char_start"], hit["char_end"]],
                    "snippet": hit["snippet"],
                }
                for idx, hit in enumerate(result["hits"], 1)
            ],
        }

    def status(self) -> dict[str, Any]:
        with self._connect() as conn:
            docs = conn.execute("select count(*) from documents").fetchone()[0]
            chunks = conn.execute("select count(*) from chunks").fetchone()[0]
            tokens = conn.execute("select coalesce(sum(token_count), 0) from chunks").fetchone()[0]
            avg_tokens = conn.execute("select coalesce(avg(token_count), 0) from chunks").fetchone()[0]
            schema_cols = [row[1] for row in conn.execute("pragma table_info(chunks)").fetchall()]
        return {
            "schema": SCHEMA_VERSION,
            "ok": True,
            "status": "pass",
            "profile": self.profile,
            "db_path": str(self.db_path),
            "documents": docs,
            "chunks": chunks,
            "tokens": tokens,
            "avg_tokens_per_chunk": round(float(avg_tokens), 2),
            "chunk_schema_columns": schema_cols,
            "capabilities": ["ingest_text", "ingest_file", "search", "answer", "sources", "explain", "validate_index", "quality_report", "gate"],
        }

    def validate_index(self, write_report: bool = False) -> dict[str, Any]:
        with self._connect() as conn:
            docs = conn.execute("select id, source, title, content_hash from documents").fetchall()
            chunks = conn.execute("select id, document_id, text, char_start, char_end, token_count, token_json from chunks").fetchall()
            orphan_chunks = conn.execute("select c.id from chunks c left join documents d on d.id = c.document_id where d.id is null").fetchall()
            duplicate_hashes = conn.execute("select content_hash, count(*) as n from documents group by content_hash having n > 1").fetchall()
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
        for row in orphan_chunks:
            findings.append({"severity": "blocker", "code": "orphan_chunk", "chunk_id": row["id"]})
        for row in duplicate_hashes:
            findings.append({"severity": "warning", "code": "duplicate_content_hash", "content_hash": row["content_hash"], "count": int(row["n"])})
        blockers = sum(1 for f in findings if f["severity"] == "blocker")
        warnings = sum(1 for f in findings if f["severity"] == "warning")
        payload = {
            "schema": "secondbrain.p1_rag.validation.v1",
            "generated_at": utc_now(),
            "ok": blockers == 0,
            "status": "pass" if blockers == 0 else "blocked",
            "documents": len(docs),
            "chunks": len(chunks),
            "blockers": blockers,
            "warnings": warnings,
            "findings": findings,
        }
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
            {"name": "answer_has_citations_when_evidence_exists", "ok": (not search_result.get("hits")) or bool(answer_result.get("citations")), "severity": "blocker", "detail": {"citations": len(answer_result.get("citations", [])), "confidence": answer_result.get("confidence", 0.0)}},
            {"name": "no_evidence_is_explicit", "ok": self.answer("zzzxxy_no_local_evidence_probe", 2).get("status") == "no_evidence", "severity": "blocker", "detail": {"policy": "answer_must_not_fabricate_without_hits"}},
        ]
        blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
        warnings = sum(1 for c in checks if not c["ok"] and c["severity"] == "warning")
        payload = {
            "schema": "secondbrain.p1_rag.quality.v1",
            "generated_at": utc_now(),
            "ok": blockers == 0,
            "status": "pass" if blockers == 0 else "blocked",
            "query": query,
            "blockers": blockers,
            "warnings": warnings,
            "checks": checks,
            "rag_status": status,
        }
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
        checks = [
            {"name": "rag_database_exists", "ok": self.db_path.exists(), "severity": "blocker", "detail": {"path": str(self.db_path)}},
            {"name": "rag_schema_ready", "ok": status["ok"] and required_columns.issubset(set(status["chunk_schema_columns"])), "severity": "blocker", "detail": {"columns": status["chunk_schema_columns"]}},
            {"name": "rag_has_indexed_content", "ok": status["chunks"] > 0, "severity": "warning", "detail": {"chunks": status["chunks"]}},
            {"name": "rag_source_inventory_available", "ok": self.sources()["ok"], "severity": "blocker", "detail": {"documents": status["documents"]}},
            {"name": "rag_explainability_available", "ok": callable(getattr(self, "explain", None)), "severity": "blocker", "detail": {"ranking_model": "deterministic_tfidf_logtf_length_norm_v1"}},
            {"name": "rag_index_validation", "ok": validation["ok"], "severity": "blocker", "detail": {"blockers": validation["blockers"], "warnings": validation["warnings"]}},
            {"name": "rag_quality_policy", "ok": quality["ok"], "severity": "blocker", "detail": {"blockers": quality["blockers"], "warnings": quality["warnings"]}},
        ]
        blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
        warnings = sum(1 for c in checks if not c["ok"] and c["severity"] == "warning")
        payload = {"schema": "secondbrain.p1_gate.v3", "generated_at": utc_now(), "ok": blockers == 0, "status": "pass" if blockers == 0 else "blocked", "blockers": blockers, "warnings": warnings, "checks": checks, "rag_status": status, "validation": validation, "quality": quality}
        if write_report:
            path = self.reports_dir / "p1_gate_latest.json"
            path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            payload["report"] = {"path": str(path), "bytes": path.stat().st_size}
        return payload
