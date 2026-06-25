from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol

from secondbrain.p1_embeddings import embedding_index_provider

VECTOR_PROVIDER_GUARD_SCHEMA = "secondbrain.p1_vector_provider_guard.v1"


class VectorRuntime(Protocol):
    db_path: Path
    reports_dir: Path
    embedding_provider: Any
    rag_store: Any


def _parse_tokens(raw: Any) -> list[Any]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, tuple):
        return list(raw)
    if isinstance(raw, str):
        try:
            value = json.loads(raw)
            return value if isinstance(value, list) else []
        except Exception:  # noqa: BLE001 - defensive stats parsing
            return []
    return []


def _audit_from_snapshot(runtime: VectorRuntime) -> dict[str, Any] | None:
    store = getattr(runtime, "rag_store", None)
    if store is None or not hasattr(store, "validation_snapshot"):
        return None

    provider_status = runtime.embedding_provider.status()
    current_provider = embedding_index_provider(runtime.embedding_provider)
    current_dimensions = int(provider_status.get("dimensions") or getattr(runtime.embedding_provider, "dimensions", 0) or 0)
    snapshot = store.validation_snapshot()
    backend = getattr(store, "backend", snapshot.get("backend", "unknown"))
    if not snapshot.get("ok"):
        return {
            "schema": VECTOR_PROVIDER_GUARD_SCHEMA,
            "ok": False,
            "status": "blocked",
            "store_backend": backend,
            "current_provider": current_provider,
            "provider_status": provider_status,
            "error": snapshot.get("error", "validation_snapshot_failed"),
            "store": snapshot,
            "reason": "rag store validation snapshot failed; vector provider audit cannot prove index consistency",
        }

    chunks = list(snapshot.get("chunks", []))
    embeddings = list(snapshot.get("embeddings", []))
    chunk_ids = {str(chunk.get("id") or chunk.get("chunk_id")) for chunk in chunks if chunk.get("id") or chunk.get("chunk_id")}
    embeddings_by_chunk: dict[str, list[dict[str, Any]]] = {}
    provider_counts: dict[tuple[str, int], int] = {}
    stale_vectors = 0
    dimension_mismatch_vectors = 0
    orphan_vectors = 0

    for embedding in embeddings:
        chunk_id = str(embedding.get("chunk_id") or "")
        provider = str(embedding.get("provider") or "")
        dimensions = int(embedding.get("dimensions") or 0)
        if chunk_id:
            embeddings_by_chunk.setdefault(chunk_id, []).append(embedding)
        provider_counts[(provider, dimensions)] = provider_counts.get((provider, dimensions), 0) + 1
        if provider != current_provider:
            stale_vectors += 1
        if current_dimensions and dimensions and dimensions != current_dimensions:
            dimension_mismatch_vectors += 1
        if chunk_id and chunk_id not in chunk_ids:
            orphan_vectors += 1

    missing_vectors = sum(1 for chunk_id in chunk_ids if chunk_id not in embeddings_by_chunk)
    malformed_token_rows = sum(1 for chunk in chunks if not _parse_tokens(chunk.get("token_json", [])))
    provider_inventory = [
        {"provider": provider, "dimensions": dimensions, "vectors": count}
        for (provider, dimensions), count in sorted(provider_counts.items(), key=lambda item: (item[0][0], item[0][1]))
    ]

    blockers: list[str] = []
    if stale_vectors:
        blockers.append("stale_vector_provider")
    if missing_vectors:
        blockers.append("missing_vectors")
    if dimension_mismatch_vectors:
        blockers.append("dimension_mismatch_vectors")
    if orphan_vectors:
        blockers.append("orphan_vectors")

    remediation = None
    if "stale_vector_provider" in blockers or "missing_vectors" in blockers or "dimension_mismatch_vectors" in blockers:
        remediation = "run python launcher.py p1-rag-reindex --write-report after changing embedding provider/model/dimensions"
    elif "orphan_vectors" in blockers:
        remediation = "run python launcher.py p1-rag-validate --write-report and repair orphan embeddings"

    return {
        "schema": VECTOR_PROVIDER_GUARD_SCHEMA,
        "ok": not blockers,
        "status": "pass" if not blockers else "blocked",
        "store_backend": backend,
        "current_provider": current_provider,
        "provider_status": provider_status,
        "chunks": len(chunks),
        "vectors": len(embeddings),
        "stale_vectors": stale_vectors,
        "dimension_mismatch_vectors": dimension_mismatch_vectors,
        "missing_vectors": missing_vectors,
        "orphan_vectors": orphan_vectors,
        "malformed_token_rows": malformed_token_rows,
        "providers": provider_inventory,
        "blockers": blockers,
        "remediation": remediation,
    }


def _audit_sqlite_legacy(runtime: VectorRuntime) -> dict[str, Any]:
    db_path = Path(runtime.db_path)
    provider_status = runtime.embedding_provider.status()
    current_provider = embedding_index_provider(runtime.embedding_provider)
    current_dimensions = int(provider_status.get("dimensions") or getattr(runtime.embedding_provider, "dimensions", 0) or 0)
    if not db_path.exists():
        return {
            "schema": VECTOR_PROVIDER_GUARD_SCHEMA,
            "ok": True,
            "status": "pass",
            "store_backend": "sqlite_legacy",
            "current_provider": current_provider,
            "provider_status": provider_status,
            "chunks": 0,
            "vectors": 0,
            "stale_vectors": 0,
            "dimension_mismatch_vectors": 0,
            "missing_vectors": 0,
            "orphan_vectors": 0,
            "providers": [],
            "message": "no vector database exists yet",
        }

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        try:
            chunks = int(conn.execute("select count(*) as n from chunks").fetchone()["n"])
            vectors = int(conn.execute("select count(*) as n from chunk_embeddings").fetchone()["n"])
            provider_rows = conn.execute("select provider, dimensions, count(*) as n from chunk_embeddings group by provider, dimensions order by provider, dimensions").fetchall()
            stale_vectors = int(conn.execute("select count(*) as n from chunk_embeddings where provider <> ?", (current_provider,)).fetchone()["n"])
            dimension_mismatch_vectors = 0
            if current_dimensions:
                dimension_mismatch_vectors = int(conn.execute("select count(*) as n from chunk_embeddings where dimensions <> ?", (current_dimensions,)).fetchone()["n"])
            missing_vectors = int(conn.execute("select count(*) as n from chunks c left join chunk_embeddings e on e.chunk_id = c.id where e.chunk_id is null").fetchone()["n"])
            orphan_vectors = int(conn.execute("select count(*) as n from chunk_embeddings e left join chunks c on c.id = e.chunk_id where c.id is null").fetchone()["n"])
        except sqlite3.OperationalError as exc:
            return {
                "schema": VECTOR_PROVIDER_GUARD_SCHEMA,
                "ok": False,
                "status": "blocked",
                "store_backend": "sqlite_legacy",
                "current_provider": current_provider,
                "provider_status": provider_status,
                "error": str(exc),
                "reason": "vector store schema is not initialized",
            }

    provider_inventory = [{"provider": row["provider"], "dimensions": int(row["dimensions"]), "vectors": int(row["n"])} for row in provider_rows]
    blockers = []
    if stale_vectors:
        blockers.append("stale_vector_provider")
    if missing_vectors:
        blockers.append("missing_vectors")
    if dimension_mismatch_vectors:
        blockers.append("dimension_mismatch_vectors")
    if orphan_vectors:
        blockers.append("orphan_vectors")
    return {
        "schema": VECTOR_PROVIDER_GUARD_SCHEMA,
        "ok": not blockers,
        "status": "pass" if not blockers else "blocked",
        "store_backend": "sqlite_legacy",
        "current_provider": current_provider,
        "provider_status": provider_status,
        "chunks": chunks,
        "vectors": vectors,
        "stale_vectors": stale_vectors,
        "dimension_mismatch_vectors": dimension_mismatch_vectors,
        "missing_vectors": missing_vectors,
        "orphan_vectors": orphan_vectors,
        "providers": provider_inventory,
        "blockers": blockers,
        "remediation": "run python launcher.py p1-rag-reindex --write-report after changing embedding provider/model/dimensions" if blockers else None,
    }


def audit_vector_provider(runtime: VectorRuntime, *, write_report: bool = False) -> dict[str, Any]:
    """Audit vector/provider consistency through the active RagStore.

    v30.9 removes the SQLite-only assumption from the provider guard. The audit now
    uses ``runtime.rag_store.validation_snapshot()`` for SQLite and pgvector and only
    falls back to direct SQLite reads for older runtimes without a RagStore bridge.
    """
    payload = _audit_from_snapshot(runtime) or _audit_sqlite_legacy(runtime)
    if write_report:
        reports_dir = Path(runtime.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        target = reports_dir / "p1_vector_provider_guard_latest.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        payload["report"] = {"path": str(target), "bytes": target.stat().st_size}
    return payload


def repair_vector_index(runtime: VectorRuntime, *, write_report: bool = False) -> dict[str, Any]:
    """Repair provider/model/dimension index drift by rebuilding current vectors.

    This command is intentionally narrow: it fixes stale-provider, missing-vector
    and dimension-drift states caused by embedding provider/model/dimension
    changes. It does not hide structural corruption such as orphan vectors.
    """
    before = audit_vector_provider(runtime, write_report=False)
    blockers = set(before.get("blockers", []))
    repairable = {"stale_vector_provider", "missing_vectors", "dimension_mismatch_vectors"}
    hard_blockers = sorted(blockers - repairable)
    if not blockers:
        payload = {
            "schema": "secondbrain.p1_vector_index_repair.v1",
            "ok": True,
            "status": "pass",
            "action": "noop",
            "reason": "vector index already matches current embedding provider identity",
            "before": before,
            "after": before,
        }
    elif hard_blockers:
        payload = {
            "schema": "secondbrain.p1_vector_index_repair.v1",
            "ok": False,
            "status": "blocked",
            "action": "blocked",
            "hard_blockers": hard_blockers,
            "before": before,
            "after": None,
            "remediation": "repair structural index errors first; this command only handles provider/model/dimension drift and missing vectors",
        }
    elif not hasattr(runtime, "reindex_vectors"):
        payload = {
            "schema": "secondbrain.p1_vector_index_repair.v1",
            "ok": False,
            "status": "blocked",
            "action": "blocked",
            "error": "runtime_reindex_vectors_missing",
            "before": before,
            "after": None,
        }
    else:
        reindex = runtime.reindex_vectors(write_report=write_report)
        after = audit_vector_provider(runtime, write_report=False)
        payload = {
            "schema": "secondbrain.p1_vector_index_repair.v1",
            "ok": bool(reindex.get("ok")) and bool(after.get("ok")),
            "status": "pass" if bool(reindex.get("ok")) and bool(after.get("ok")) else "blocked",
            "action": "reindex_current_provider",
            "before": before,
            "reindex": reindex,
            "after": after,
        }
    if write_report:
        reports_dir = Path(runtime.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        target = reports_dir / "p1_vector_index_repair_latest.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        payload["report"] = {"path": str(target), "bytes": target.stat().st_size}
    return payload
