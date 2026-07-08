from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from secondbrain.p3_rag_store import RagChunkRecord, RagDocumentRecord, RagVectorRecord, RagStore, SQLiteRagStore, create_rag_store

P1_STORE_BRIDGE_SCHEMA = "secondbrain.p3_p1_store_bridge.v1"


def _connect(db_path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def export_p1_sqlite_records(db_path: str | Path) -> dict[str, Any]:
    """Export existing P1 SQLite RAG rows into store contract records."""
    path = Path(db_path)
    if not path.exists():
        return {
            "schema": P1_STORE_BRIDGE_SCHEMA,
            "ok": True,
            "status": "empty",
            "db_path": str(path),
            "documents": [],
            "chunks": [],
            "vectors": [],
        }
    with _connect(path) as conn:
        docs = conn.execute("select id, source, title, content_hash, created_at, metadata_json from documents order by created_at, id").fetchall()
        chunks = conn.execute("select id, document_id, ordinal, text, char_start, char_end, token_json, token_count, created_at from chunks order by document_id, ordinal").fetchall()
        vectors = conn.execute("select chunk_id, provider, dimensions, vector_json, created_at from chunk_embeddings order by chunk_id").fetchall()
    return {
        "schema": P1_STORE_BRIDGE_SCHEMA,
        "ok": True,
        "status": "pass",
        "db_path": str(path),
        "documents": [
            RagDocumentRecord(
                id=row["id"],
                source=row["source"],
                title=row["title"],
                content_hash=row["content_hash"],
                created_at=row["created_at"],
                metadata=json.loads(row["metadata_json"] or "{}"),
            )
            for row in docs
        ],
        "chunks": [
            RagChunkRecord(
                id=row["id"],
                document_id=row["document_id"],
                ordinal=int(row["ordinal"]),
                text=row["text"],
                char_start=int(row["char_start"]),
                char_end=int(row["char_end"]),
                tokens=json.loads(row["token_json"] or "[]"),
                token_count=int(row["token_count"]),
                created_at=row["created_at"],
            )
            for row in chunks
        ],
        "vectors": [
            RagVectorRecord(
                chunk_id=row["chunk_id"],
                provider=row["provider"],
                dimensions=int(row["dimensions"]),
                vector=[float(v) for v in json.loads(row["vector_json"] or "[]")],
                created_at=row["created_at"],
            )
            for row in vectors
        ],
    }


def mirror_p1_sqlite_to_store(source_db_path: str | Path, target_store: RagStore) -> dict[str, Any]:
    export = export_p1_sqlite_records(source_db_path)
    if not export.get("ok"):
        return export
    documents: list[RagDocumentRecord] = export["documents"]
    chunks: list[RagChunkRecord] = export["chunks"]
    vectors: list[RagVectorRecord] = export["vectors"]

    doc_results = [target_store.upsert_document(document) for document in documents]
    chunk_result = target_store.upsert_chunks(chunks) if chunks else {"ok": True, "chunks": 0}
    vector_result = target_store.upsert_vectors(vectors) if vectors else {"ok": True, "vectors": 0}
    ok = all(result.get("ok") for result in doc_results) and bool(chunk_result.get("ok")) and bool(vector_result.get("ok"))
    return {
        "schema": P1_STORE_BRIDGE_SCHEMA,
        "ok": ok,
        "status": "pass" if ok else "blocked",
        "source_db_path": str(source_db_path),
        "target_backend": target_store.backend,
        "documents": len(documents),
        "chunks": len(chunks),
        "vectors": len(vectors),
        "document_results": doc_results,
        "chunk_result": chunk_result,
        "vector_result": vector_result,
    }


def mirror_project_p1_to_selected_store(project_root: str | Path, *, write_report: bool = False) -> dict[str, Any]:
    root = Path(project_root).resolve()
    source_db = root / "runtime" / "p1_rag" / "rag.sqlite3"
    target_store = create_rag_store(root)
    if isinstance(target_store, SQLiteRagStore) and Path(target_store.db_path) == source_db:
        payload = {
            "schema": P1_STORE_BRIDGE_SCHEMA,
            "ok": True,
            "status": "noop",
            "reason": "selected store is the existing P1 SQLite database",
            "source_db_path": str(source_db),
            "target_backend": target_store.backend,
            "store_status": target_store.status(),
        }
    else:
        payload = mirror_p1_sqlite_to_store(source_db, target_store)
    if write_report:
        reports_dir = root / "runtime" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        target = reports_dir / "p3_p1_store_bridge_latest.json"
        serializable = _to_jsonable(payload)
        target.write_text(json.dumps(serializable, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        payload["report"] = {"path": str(target), "bytes": target.stat().st_size}
    return payload


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    return value
