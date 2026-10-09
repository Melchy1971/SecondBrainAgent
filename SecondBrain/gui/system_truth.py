"""Echtdaten fuer Header, System-Info und Alerts des Web-HUD.

Ersetzt die frueheren Anzeige-Settings (``postgres_status``, ``release_blocking``,
``system_health`` ...), die frei editierbar waren und keinen Bezug zum
tatsaechlichen Systemzustand hatten. Jeder Wert hier stammt aus einer
Runtime-Quelle; was nicht ermittelbar ist, wird als ``None`` geliefert und von
der GUI als "—" angezeigt -- nie geschaetzt.

Alle Quellen sind injizierbar, damit die Aggregation ohne Datenbank, ohne
Ollama und ohne Reports testbar ist.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from secondbrain.version import get_version

SYSTEM_TRUTH_SCHEMA = "secondbrain.gui.system_truth.v1"

HEALTH_OK = "OK"
HEALTH_DEGRADED = "EINGESCHRÄNKT"
HEALTH_BLOCKED = "BLOCKIERT"

_BACKEND_LABELS = {"sqlite": "SQLite", "postgresql": "PostgreSQL", "postgres": "PostgreSQL"}


def _norm_version(value: str) -> str:
    return str(value or "").strip().lstrip("vV")


def _environment(env: Mapping[str, str]) -> str:
    from secondbrain.storage.db_policy import read_env
    return read_env(dict(env))["environment"]


def _database(db: Mapping[str, Any]) -> dict[str, Any]:
    backend = str(db.get("backend") or "unknown")
    pgvector = db.get("pgvector") if isinstance(db.get("pgvector"), Mapping) else {}
    return {
        "backend": backend,
        "label": _BACKEND_LABELS.get(backend, backend),
        "status": str(db.get("status") or "unknown"),
        "reason": str(db.get("reason") or ""),
        "production_ready": bool(db.get("production_ready")),
        "postgres_version": pgvector.get("postgres_version"),
        "pgvector_version": pgvector.get("vector_extension_version"),
    }


def _embedding(provider: Mapping[str, Any]) -> dict[str, Any]:
    status = provider.get("provider_status") if isinstance(provider.get("provider_status"), Mapping) else {}
    config_health = provider.get("config_health") if isinstance(provider.get("config_health"), Mapping) else {}
    config = config_health.get("config") if isinstance(config_health.get("config"), Mapping) else {}
    return {
        "provider": str(provider.get("provider") or config.get("provider") or "unknown"),
        "model": str(config.get("model") or ""),
        "dimensions": status.get("dimensions") or config.get("dimensions"),
        "status": str(provider.get("status") or "unknown"),
        "production_ready": bool(status.get("production_ready")),
        "blockers": list(provider.get("blockers") or []),
    }


def _vector_index(store: Mapping[str, Any]) -> dict[str, Any]:
    vectors = int(store.get("vectors") or 0)
    ok = bool(store.get("ok"))
    return {
        "backend": str(store.get("backend") or "unknown"),
        "documents": int(store.get("documents") or 0),
        "chunks": int(store.get("chunks") or 0),
        "vectors": vectors,
        "status": "error" if not ok else ("empty" if vectors == 0 else "ok"),
    }


def _release_gate(report: Mapping[str, Any]) -> dict[str, Any]:
    status = str(report.get("status") or "unknown")
    report_version = str(report.get("version") or "")
    return {
        "status": status,
        "blockers": list(report.get("blockers") or []),
        "timestamp": str(report.get("timestamp") or ""),
        "report_version": report_version,
        # Ein Bericht aus einer anderen Version beschreibt nicht den aktuellen Code.
        "stale": bool(report_version) and _norm_version(report_version) != _norm_version(get_version()),
    }


def _backup(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    center = snapshot.get("backup_center") if isinstance(snapshot.get("backup_center"), Mapping) else {}
    scheduler = snapshot.get("scheduler") if isinstance(snapshot.get("scheduler"), Mapping) else {}
    latest = center.get("latest_backup") if isinstance(center.get("latest_backup"), Mapping) else {}
    return {
        "status": str(center.get("status") or "unknown"),
        "count": int(center.get("backup_count") or 0),
        "last_at": latest.get("created_at") or scheduler.get("last_success_at") or None,
        "schedule_enabled": bool(scheduler.get("enabled")),
        "interval": scheduler.get("interval") if scheduler.get("enabled") else None,
    }


def _memory(status: Mapping[str, Any]) -> dict[str, Any]:
    summary = status.get("summary") if isinstance(status.get("summary"), Mapping) else {}
    return {
        "status": str(status.get("status") or "unknown"),
        "total": int(summary.get("total_memories") or 0),
        "vault": int(summary.get("vault_memories") or 0),
        "sqlite": int(summary.get("sqlite_memories") or 0),
    }


def _job_queue(database: Mapping[str, Any], job_runtime: Mapping[str, Any]) -> dict[str, Any]:
    # Die Job-Queue existiert nur mit PostgreSQL-Repository; ohne gibt es keine
    # Warteschlange und damit keine Pending-Zahl.
    active = database.get("backend") == "postgresql" and database.get("production_ready")
    return {
        "backend": "postgresql" if active else None,
        "state": str(job_runtime.get("state") or "unknown") if active else "inactive",
        "pending": None,
    }


def _health(parts: Mapping[str, Mapping[str, Any]], environment: str) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    gate = parts["release_gate"]
    if gate["status"].upper() == "BLOCKED":
        blockers.extend([f"release_gate:{b}" for b in gate["blockers"]] or ["release_gate"])
    if gate["stale"] or gate["status"] in ("not_run", "unknown", "error"):
        warnings.append("release_gate_report_outdated")

    db = parts["database"]
    if db["status"].startswith("blocked"):
        blockers.append(f"database:{db['status']}")
    elif not db["production_ready"]:
        (blockers if environment == "production" else warnings).append(f"database:{db['status']}")

    emb = parts["embedding"]
    if emb["status"] == "blocked":
        blockers.append("embedding:blocked")

    if parts["vector_index"]["status"] != "ok":
        warnings.append(f"vector_index:{parts['vector_index']['status']}")
    if parts["backup"]["count"] == 0:
        warnings.append("backup:none")
    if parts["memory"]["status"] == "blocked":
        warnings.append("memory:governance_blocked")
    if not parts["ollama"]["models"]:
        warnings.append("ollama:unreachable")

    if blockers:
        level, text = HEALTH_BLOCKED, f"{len(blockers)} Blocker, {len(warnings)} Warnungen"
    elif warnings:
        level, text = HEALTH_DEGRADED, f"{len(warnings)} Warnungen"
    else:
        level, text = HEALTH_OK, "Alle Prüfungen bestanden"
    return {"level": level, "text": text, "blockers": blockers, "warnings": warnings}


def build_system_truth(
    project_root: str | Path,
    *,
    release_gate: Callable[[], Mapping[str, Any]],
    ollama_models: Callable[[], list[str]],
    ollama_url: str,
    view_model: Callable[[Path], Mapping[str, Any]] | None = None,
    db_status: Callable[[Path], Mapping[str, Any]] | None = None,
    backup_snapshot: Callable[[Path], Mapping[str, Any]] | None = None,
    memory_status: Callable[[Path], Mapping[str, Any]] | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    if view_model is None:
        from secondbrain.native.runtime_snapshot import (
            build_native_view_model as view_model,
        )
    if db_status is None:
        from secondbrain.storage.db_production_status import (
            evaluate_db_pgvector_production_status as db_status,
        )
    if memory_status is None:
        from secondbrain.gui.memory_center_runtime import (
            memory_center_status as memory_status,
        )
    if backup_snapshot is None:
        def backup_snapshot(path: Path) -> Mapping[str, Any]:
            from secondbrain.gui.backup_center import BackupCenterViewModel
            return BackupCenterViewModel(path).snapshot()

    model = view_model(root)
    environment = _environment(os.environ if env is None else env)
    database = _database(db_status(root))
    models = list(ollama_models())
    parts: dict[str, Any] = {
        "database": database,
        "embedding": _embedding(model.get("provider") or {}),
        "vector_index": _vector_index((model.get("rag") or {}).get("store") or {}),
        "release_gate": _release_gate(release_gate()),
        "backup": _backup(backup_snapshot(root)),
        "memory": _memory(memory_status(root)),
        "ollama": {"url": ollama_url, "models": len(models)},
        "job_queue": _job_queue(database, model.get("job_runtime") or {}),
    }
    return {
        "ok": True,
        "schema": SYSTEM_TRUTH_SCHEMA,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "version": f"v{get_version()}",
        "environment": environment,
        "health": _health(parts, environment),
        **parts,
    }


class CachedSystemTruth:
    """Kurzzeit-Cache: die GUI pollt, die Quellen kosten ~0,5 s (+ Ollama-Timeout)."""

    def __init__(self, builder: Callable[[], dict[str, Any]], ttl_seconds: float = 30.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._builder = builder
        self._ttl = ttl_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._value: dict[str, Any] | None = None
        self._at = 0.0

    def get(self) -> dict[str, Any]:
        with self._lock:  # serialisiert auch parallele Erstaufrufe -> ein Build
            if self._value is None or self._clock() - self._at >= self._ttl:
                self._value = self._builder()
                self._at = self._clock()
            return self._value
