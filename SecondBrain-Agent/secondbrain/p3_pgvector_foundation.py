from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PGVECTOR_SCHEMA = "secondbrain.p3_pgvector_foundation.v1"
DEFAULT_VECTOR_DIMENSIONS = 1536


@dataclass(frozen=True)
class PgVectorConfig:
    enabled: bool
    dsn: str | None
    schema_name: str = "secondbrain"
    table_prefix: str = "p1"
    vector_dimensions: int = DEFAULT_VECTOR_DIMENSIONS
    provider: str = "unknown"

    def redacted_dsn(self) -> str | None:
        return redact_dsn(self.dsn)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["dsn"] = self.redacted_dsn()
        return data


def redact_dsn(dsn: str | None) -> str | None:
    if not dsn:
        return None
    # postgresql://user:password@host:5432/db -> postgresql://user:***@host:5432/db
    return re.sub(r"(postgres(?:ql)?://[^:/@]+:)([^@]+)(@)", r"\1***\3", dsn)


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value.strip())
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _yaml_value(text: str, key: str) -> str | None:
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith(key.lower() + ":"):
            return line.split(":", 1)[1].strip().strip('"\'')
    return None


def load_pgvector_config(project_root: str | Path) -> PgVectorConfig:
    root = Path(project_root).resolve()
    config_path = root / "config" / "pgvector.yaml"
    values: dict[str, str] = {}
    if config_path.exists():
        text = config_path.read_text(encoding="utf-8", errors="ignore")
        for key in ("enabled", "dsn", "schema_name", "table_prefix", "vector_dimensions", "provider"):
            value = _yaml_value(text, key)
            if value is not None:
                values[key] = value

    env_dsn = os.getenv("SECONDBRAIN_PGVECTOR_DSN") or os.getenv("DATABASE_URL")
    enabled = _parse_bool(os.getenv("SECONDBRAIN_PGVECTOR_ENABLED"), _parse_bool(values.get("enabled"), bool(env_dsn or values.get("dsn"))))
    return PgVectorConfig(
        enabled=enabled,
        dsn=env_dsn or values.get("dsn"),
        schema_name=os.getenv("SECONDBRAIN_PGVECTOR_SCHEMA") or values.get("schema_name") or "secondbrain",
        table_prefix=os.getenv("SECONDBRAIN_PGVECTOR_TABLE_PREFIX") or values.get("table_prefix") or "p1",
        vector_dimensions=_parse_int(os.getenv("SECONDBRAIN_PGVECTOR_DIMENSIONS") or values.get("vector_dimensions"), DEFAULT_VECTOR_DIMENSIONS),
        provider=os.getenv("SECONDBRAIN_EMBEDDING_PROVIDER") or values.get("provider") or "unknown",
    )


def build_pgvector_schema_sql(config: PgVectorConfig) -> str:
    schema = _safe_identifier(config.schema_name, fallback="secondbrain")
    prefix = _safe_identifier(config.table_prefix, fallback="p1")
    dimensions = max(1, int(config.vector_dimensions))
    return f"""-- SecondBrain pgvector foundation schema
create extension if not exists vector;
create schema if not exists {schema};

create table if not exists {schema}.{prefix}_documents (
    id text primary key,
    source text not null,
    title text not null,
    content_hash text not null,
    created_at timestamptz not null,
    metadata_json jsonb not null default '{{}}'::jsonb
);

create table if not exists {schema}.{prefix}_chunks (
    id text primary key,
    document_id text not null references {schema}.{prefix}_documents(id) on delete cascade,
    ordinal integer not null,
    text text not null,
    char_start integer not null default 0,
    char_end integer not null default 0,
    token_json jsonb not null default '[]'::jsonb,
    token_count integer not null default 0,
    created_at timestamptz not null
);

create table if not exists {schema}.{prefix}_chunk_embeddings (
    chunk_id text primary key references {schema}.{prefix}_chunks(id) on delete cascade,
    provider text not null,
    dimensions integer not null,
    embedding vector({dimensions}) not null,
    created_at timestamptz not null
);

create index if not exists idx_{prefix}_documents_source on {schema}.{prefix}_documents(source);
create index if not exists idx_{prefix}_chunks_document on {schema}.{prefix}_chunks(document_id);
create index if not exists idx_{prefix}_embeddings_provider on {schema}.{prefix}_chunk_embeddings(provider);
create index if not exists idx_{prefix}_embeddings_vector on {schema}.{prefix}_chunk_embeddings using ivfflat (embedding vector_cosine_ops);
"""


def _safe_identifier(value: str, *, fallback: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", value or "")
    if not cleaned or cleaned[0].isdigit():
        cleaned = fallback
    return cleaned.lower()


def pgvector_readiness(project_root: str | Path, *, write_report: bool = False) -> dict[str, Any]:
    root = Path(project_root).resolve()
    config = load_pgvector_config(root)
    checks: list[dict[str, Any]] = []
    checks.append({"name": "pgvector_config_loaded", "ok": True, "severity": "info", "detail": config.to_dict()})
    checks.append({"name": "pgvector_enabled", "ok": bool(config.enabled), "severity": "warning", "detail": {"enabled": config.enabled}})
    checks.append({"name": "pgvector_dsn_configured", "ok": bool(config.dsn), "severity": "blocker" if config.enabled else "warning", "detail": {"dsn": config.redacted_dsn()}})
    checks.append({"name": "pgvector_dimensions_valid", "ok": config.vector_dimensions > 0, "severity": "blocker", "detail": {"dimensions": config.vector_dimensions}})
    checks.append({"name": "pgvector_schema_sql_builds", "ok": bool(build_pgvector_schema_sql(config).strip()), "severity": "blocker", "detail": {"schema_name": config.schema_name, "table_prefix": config.table_prefix}})

    blockers = sum(1 for check in checks if not check["ok"] and check["severity"] == "blocker")
    warnings = sum(1 for check in checks if not check["ok"] and check["severity"] == "warning")
    payload = {
        "schema": PGVECTOR_SCHEMA,
        "ok": blockers == 0,
        "status": "pass" if blockers == 0 else "blocked",
        "blockers": blockers,
        "warnings": warnings,
        "config": config.to_dict(),
        "sql_preview": build_pgvector_schema_sql(config),
        "checks": checks,
    }
    if write_report:
        reports_dir = root / "runtime" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        target = reports_dir / "p3_pgvector_readiness_latest.json"
        target.write_text(__import__("json").dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        payload["report"] = {"path": str(target), "bytes": target.stat().st_size}
    return payload
