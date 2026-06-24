from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol

VECTOR_PROVIDER_GUARD_SCHEMA = "secondbrain.p1_vector_provider_guard.v1"


class VectorRuntime(Protocol):
    db_path: Path
    reports_dir: Path
    embedding_provider: Any


def audit_vector_provider(runtime: VectorRuntime, *, write_report: bool = False) -> dict[str, Any]:
    """Detect stale vectors after embedding provider changes.

    The current SQLite vector store keeps one embedding row per chunk. If the
    active provider changes from local to OpenAI/Ollama, all existing vectors
    must be recreated before production can be considered safe.
    """
    db_path = Path(runtime.db_path)
    current_provider = getattr(runtime.embedding_provider, "name", "unknown")
    provider_status = runtime.embedding_provider.status()
    if not db_path.exists():
        payload = {
            "schema": VECTOR_PROVIDER_GUARD_SCHEMA,
            "ok": True,
            "status": "pass",
            "current_provider": current_provider,
            "provider_status": provider_status,
            "chunks": 0,
            "vectors": 0,
            "stale_vectors": 0,
            "missing_vectors": 0,
            "providers": [],
            "message": "no vector database exists yet",
        }
    else:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            try:
                chunks = int(conn.execute("select count(*) as n from chunks").fetchone()["n"])
                vectors = int(conn.execute("select count(*) as n from chunk_embeddings").fetchone()["n"])
                provider_rows = conn.execute("select provider, dimensions, count(*) as n from chunk_embeddings group by provider, dimensions order by provider, dimensions").fetchall()
                stale_vectors = int(conn.execute("select count(*) as n from chunk_embeddings where provider <> ?", (current_provider,)).fetchone()["n"])
                missing_vectors = int(conn.execute("select count(*) as n from chunks c left join chunk_embeddings e on e.chunk_id = c.id where e.chunk_id is null").fetchone()["n"])
            except sqlite3.OperationalError as exc:
                payload = {
                    "schema": VECTOR_PROVIDER_GUARD_SCHEMA,
                    "ok": False,
                    "status": "blocked",
                    "current_provider": current_provider,
                    "provider_status": provider_status,
                    "error": str(exc),
                    "reason": "vector store schema is not initialized",
                }
            else:
                provider_inventory = [{"provider": row["provider"], "dimensions": int(row["dimensions"]), "vectors": int(row["n"])} for row in provider_rows]
                blockers = []
                if stale_vectors:
                    blockers.append("stale_vector_provider")
                if missing_vectors:
                    blockers.append("missing_vectors")
                payload = {
                    "schema": VECTOR_PROVIDER_GUARD_SCHEMA,
                    "ok": not blockers,
                    "status": "pass" if not blockers else "blocked",
                    "current_provider": current_provider,
                    "provider_status": provider_status,
                    "chunks": chunks,
                    "vectors": vectors,
                    "stale_vectors": stale_vectors,
                    "missing_vectors": missing_vectors,
                    "providers": provider_inventory,
                    "blockers": blockers,
                    "remediation": "run python launcher.py p1-rag-reindex --write-report after changing embedding provider" if blockers else None,
                }
    if write_report:
        reports_dir = Path(runtime.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        target = reports_dir / "p1_vector_provider_guard_latest.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        payload["report"] = {"path": str(target), "bytes": target.stat().st_size}
    return payload
