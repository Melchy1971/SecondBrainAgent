"""Production-focused PostgreSQL/pgvector readiness evaluation.

Status taxonomy is intentionally strict and finite:
- ready
- degraded_sqlite
- blocked_missing_database
- blocked_missing_pgvector
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from secondbrain.p3_pgvector_foundation import PgVectorConfig, load_pgvector_config, pgvector_live_check, redact_dsn
from secondbrain.storage.db_policy import DatabaseStartupError, parse_dialect, read_env
from secondbrain.storage.db_startup import validate_and_connect


DB_PRODUCTION_STATUS_SCHEMA = "secondbrain.storage.db_production_status.v1"


def _check(name: str, ok: bool, severity: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "severity": severity, "detail": detail or {}}


def _strict_env(env: dict[str, str] | None = None) -> dict[str, str]:
    merged = dict(read_env(env))
    raw = dict(env or {})
    url = (raw.get("SECOND_BRAIN_DATABASE_URL") or raw.get("DATABASE_URL") or merged.get("url") or "").strip()
    if url:
        merged["url"] = url
    merged["environment"] = "production"
    merged["allow_fallback"] = ""
    return {
        "SECOND_BRAIN_DATABASE_URL": merged.get("url", ""),
        "DATABASE_URL": merged.get("url", ""),
        "SECOND_BRAIN_ENV": "production",
        "SECOND_BRAIN_ALLOW_SQLITE_FALLBACK": "0",
        "SECOND_BRAIN_SQLITE_DEV_PATH": merged.get("sqlite_dev_path", "runtime/dev.sqlite3"),
    }


def _with_runtime_dsn(root: Path, dsn: str) -> PgVectorConfig:
    cfg = load_pgvector_config(root)
    return replace(cfg, enabled=True, dsn=dsn)


def evaluate_db_pgvector_production_status(
    project_root: str | Path,
    env: dict[str, str] | None = None,
    *,
    pg_executor_factory: Callable[[str], Any] | None = None,
    pgvector_probe: Callable[[PgVectorConfig], dict[str, Any]] = pgvector_live_check,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    strict_env = _strict_env(env)
    url = strict_env.get("DATABASE_URL", "")
    dialect = parse_dialect(url)
    checks: list[dict[str, Any]] = []

    if not url:
        checks.append(_check("database_url_present", False, "warning", {"expected": "DATABASE_URL postgres://..."}))
        return {
            "schema": DB_PRODUCTION_STATUS_SCHEMA,
            "ok": False,
            "status": "degraded_sqlite",
            "reason": "database_url_missing",
            "backend": "sqlite",
            "url": None,
            "production_ready": False,
            "checks": checks,
        }

    checks.append(_check("database_url_present", True, "blocker", {"url": redact_dsn(url)}))

    if dialect == "sqlite":
        checks.append(_check("postgresql_required_for_production", False, "blocker", {"dialect": "sqlite"}))
        return {
            "schema": DB_PRODUCTION_STATUS_SCHEMA,
            "ok": False,
            "status": "degraded_sqlite",
            "reason": "sqlite_configured",
            "backend": "sqlite",
            "url": redact_dsn(url),
            "production_ready": False,
            "checks": checks,
        }

    if dialect != "postgresql":
        checks.append(_check("postgresql_required_for_production", False, "blocker", {"dialect": dialect or "unknown"}))
        return {
            "schema": DB_PRODUCTION_STATUS_SCHEMA,
            "ok": False,
            "status": "blocked_missing_database",
            "reason": "unsupported_database_scheme",
            "backend": dialect or "unknown",
            "url": redact_dsn(url),
            "production_ready": False,
            "checks": checks,
        }

    checks.append(_check("postgresql_required_for_production", True, "blocker", {"dialect": "postgresql"}))

    try:
        runtime = validate_and_connect(strict_env, pg_executor_factory=pg_executor_factory)
    except DatabaseStartupError as exc:
        checks.append(_check("postgresql_connection", False, "blocker", {"error": str(exc)}))
        return {
            "schema": DB_PRODUCTION_STATUS_SCHEMA,
            "ok": False,
            "status": "blocked_missing_database",
            "reason": "postgresql_unreachable",
            "backend": "postgresql",
            "url": redact_dsn(url),
            "production_ready": False,
            "checks": checks,
        }

    checks.append(_check("postgresql_connection", bool(runtime.connected), "blocker", {"backend": runtime.backend, "reason": runtime.reason}))

    if runtime.backend != "postgresql" or runtime.is_fallback:
        checks.append(_check("sqlite_fallback_not_allowed", False, "blocker", {"backend": runtime.backend, "is_fallback": runtime.is_fallback}))
        return {
            "schema": DB_PRODUCTION_STATUS_SCHEMA,
            "ok": False,
            "status": "degraded_sqlite",
            "reason": "sqlite_fallback_active",
            "backend": runtime.backend,
            "url": redact_dsn(url),
            "production_ready": False,
            "checks": checks,
        }

    migration_ok = True
    migration_detail: dict[str, Any] = {}
    try:
        migration_rows = runtime.executor.execute("SELECT COUNT(*) FROM schema_migrations")
        migration_detail = {"rows": int(migration_rows[0][0]) if migration_rows else 0}
    except Exception as exc:  # noqa: BLE001 - prod DB may not have migration table yet
        migration_ok = False
        migration_detail = {"error": str(exc)}
    checks.append(_check("migration_health_probe", migration_ok, "warning", migration_detail))

    pg_cfg = _with_runtime_dsn(root, url)
    live = pgvector_probe(pg_cfg)
    live_ok = bool(live.get("ok"))
    checks.append(_check("pgvector_live_check", live_ok, "blocker", live))
    if not live_ok:
        return {
            "schema": DB_PRODUCTION_STATUS_SCHEMA,
            "ok": False,
            "status": "blocked_missing_pgvector",
            "reason": str(live.get("error") or "pgvector_validation_failed"),
            "backend": "postgresql",
            "url": redact_dsn(url),
            "production_ready": False,
            "checks": checks,
            "pgvector": live,
        }

    similarity_ok = True
    similarity_detail: dict[str, Any] = {}
    try:
        similarity_rows = runtime.executor.execute("SELECT ('[1,0,0]'::vector <=> '[1,0,0]'::vector) AS distance")
        distance = float(similarity_rows[0][0]) if similarity_rows else 1.0
        similarity_ok = abs(distance) < 1e-9
        similarity_detail = {"distance": distance}
    except Exception as exc:  # noqa: BLE001 - extension/runtime boundary
        similarity_ok = False
        similarity_detail = {"error": str(exc)}
    checks.append(_check("pgvector_similarity_smoke", similarity_ok, "blocker", similarity_detail))
    if not similarity_ok:
        return {
            "schema": DB_PRODUCTION_STATUS_SCHEMA,
            "ok": False,
            "status": "blocked_missing_pgvector",
            "reason": "pgvector_similarity_smoke_failed",
            "backend": "postgresql",
            "url": redact_dsn(url),
            "production_ready": False,
            "checks": checks,
            "pgvector": live,
        }

    return {
        "schema": DB_PRODUCTION_STATUS_SCHEMA,
        "ok": True,
        "status": "ready",
        "reason": "postgresql_pgvector_validated",
        "backend": "postgresql",
        "url": redact_dsn(url),
        "production_ready": True,
        "checks": checks,
        "pgvector": live,
    }
