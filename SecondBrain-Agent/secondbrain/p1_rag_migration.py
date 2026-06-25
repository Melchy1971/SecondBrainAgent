from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.p3_rag_store import RagChunkRecord, RagDocumentRecord, RagVectorRecord, create_rag_store
from secondbrain.p3_pgvector_foundation import pgvector_readiness

MIGRATION_SCHEMA = "secondbrain.p1_rag.sqlite_to_pgvector.v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MigrationPlan:
    source_db: str
    target_backend: str
    documents: int
    chunks: int
    vectors: int
    dry_run: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _connect_sqlite(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("select name from sqlite_master where type='table' and name = ?", (name,)).fetchone()
    return row is not None


def _load_sqlite_records(db_path: str | Path) -> tuple[list[RagDocumentRecord], list[RagChunkRecord], list[RagVectorRecord]]:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"sqlite_source_missing:{path}")
    with _connect_sqlite(path) as conn:
        required = {"documents", "chunks", "chunk_embeddings"}
        missing = sorted(t for t in required if not _table_exists(conn, t))
        if missing:
            raise RuntimeError("sqlite_source_schema_missing:" + ",".join(missing))
        documents = [
            RagDocumentRecord(
                id=str(row["id"]),
                source=str(row["source"]),
                title=str(row["title"]),
                content_hash=str(row["content_hash"]),
                created_at=str(row["created_at"]),
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
            for row in conn.execute("select id, source, title, content_hash, created_at, metadata_json from documents order by created_at, id").fetchall()
        ]
        chunks = [
            RagChunkRecord(
                id=str(row["id"]),
                document_id=str(row["document_id"]),
                ordinal=int(row["ordinal"]),
                text=str(row["text"]),
                char_start=int(row["char_start"]),
                char_end=int(row["char_end"]),
                tokens=json.loads(row["token_json"] or "[]"),
                token_count=int(row["token_count"]),
                created_at=str(row["created_at"]),
            )
            for row in conn.execute("select id, document_id, ordinal, text, char_start, char_end, token_json, token_count, created_at from chunks order by document_id, ordinal, id").fetchall()
        ]
        vectors = [
            RagVectorRecord(
                chunk_id=str(row["chunk_id"]),
                provider=str(row["provider"]),
                dimensions=int(row["dimensions"]),
                vector=[float(v) for v in json.loads(row["vector_json"] or "[]")],
                created_at=str(row["created_at"]),
            )
            for row in conn.execute("select chunk_id, provider, dimensions, vector_json, created_at from chunk_embeddings order by chunk_id").fetchall()
        ]
    return documents, chunks, vectors


def migrate_sqlite_to_selected_store(
    project_root: str | Path,
    *,
    sqlite_db_path: str | Path | None = None,
    dry_run: bool = True,
    write_report: bool = False,
    require_pgvector: bool = True,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    source = Path(sqlite_db_path or root / "runtime" / "p1_rag" / "rag.sqlite3")
    generated_at = _now()
    try:
        docs, chunks, vectors = _load_sqlite_records(source)
    except Exception as exc:  # noqa: BLE001 - migration boundary
        payload = {
            "schema": MIGRATION_SCHEMA,
            "generated_at": generated_at,
            "ok": False,
            "status": "blocked",
            "error": str(exc),
            "source_db": str(source),
        }
        return _maybe_write_report(root, payload, write_report)

    target = create_rag_store(root, sqlite_db_path=source)
    plan = MigrationPlan(str(source), target.backend, len(docs), len(chunks), len(vectors), dry_run)
    blockers: list[dict[str, Any]] = []
    if require_pgvector and target.backend != "pgvector":
        blockers.append({"code": "target_store_not_pgvector", "target_backend": target.backend})
    readiness = None
    if target.backend == "pgvector":
        readiness = pgvector_readiness(root, live=True, apply=False)
        if not readiness.get("ok"):
            blockers.append({"code": "pgvector_readiness_blocked", "detail": readiness})
    if blockers:
        payload = {
            "schema": MIGRATION_SCHEMA,
            "generated_at": generated_at,
            "ok": False,
            "status": "blocked",
            "plan": plan.to_dict(),
            "readiness": readiness,
            "blockers": blockers,
            "applied": False,
        }
        return _maybe_write_report(root, payload, write_report)
    if dry_run:
        payload = {
            "schema": MIGRATION_SCHEMA,
            "generated_at": generated_at,
            "ok": True,
            "status": "dry_run",
            "plan": plan.to_dict(),
            "readiness": readiness,
            "applied": False,
        }
        return _maybe_write_report(root, payload, write_report)

    doc_result = {"ok": True, "documents": 0}
    chunk_result = {"ok": True, "chunks": 0}
    vector_result = {"ok": True, "vectors": 0}
    for doc in docs:
        doc_result = target.upsert_document(doc)
        if not doc_result.get("ok"):
            break
    if doc_result.get("ok"):
        chunk_result = target.upsert_chunks(chunks)
    if doc_result.get("ok") and chunk_result.get("ok"):
        vector_result = target.upsert_vectors(vectors)
    ok = bool(doc_result.get("ok")) and bool(chunk_result.get("ok")) and bool(vector_result.get("ok"))
    payload = {
        "schema": MIGRATION_SCHEMA,
        "generated_at": generated_at,
        "ok": ok,
        "status": "pass" if ok else "blocked",
        "plan": plan.to_dict(),
        "readiness": readiness,
        "applied": ok,
        "results": {"last_document": doc_result, "chunks": chunk_result, "vectors": vector_result},
    }
    return _maybe_write_report(root, payload, write_report)


def _maybe_write_report(root: Path, payload: dict[str, Any], write_report: bool) -> dict[str, Any]:
    if write_report:
        reports_dir = root / "runtime" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        target = reports_dir / "p1_sqlite_to_pgvector_migration_latest.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        payload["report"] = {"path": str(target), "bytes": target.stat().st_size}
    return payload
