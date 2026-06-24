from __future__ import annotations

import json

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p3_pgvector_foundation import build_pgvector_schema_sql, load_pgvector_config, pgvector_readiness, redact_dsn


def test_redact_dsn_hides_password():
    dsn = "postgresql://appuser:super-secret@localhost:5432/wissen2026"

    redacted = redact_dsn(dsn)

    assert redacted == "postgresql://appuser:***@localhost:5432/wissen2026"
    assert "super-secret" not in redacted


def test_pgvector_config_loads_from_env(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_SCHEMA", "SecondBrain")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_TABLE_PREFIX", "RAG")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DIMENSIONS", "3072")

    config = load_pgvector_config(tmp_path)

    assert config.enabled is True
    assert config.dsn == "postgresql://user:pw@db:5432/app"
    assert config.redacted_dsn() == "postgresql://user:***@db:5432/app"
    assert config.schema_name == "SecondBrain"
    assert config.table_prefix == "RAG"
    assert config.vector_dimensions == 3072


def test_pgvector_config_loads_from_yaml(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "pgvector.yaml").write_text(
        "enabled: true\n"
        "dsn: postgresql://app:pw@localhost:5432/secondbrain\n"
        "schema_name: secondbrain_custom\n"
        "table_prefix: rag\n"
        "vector_dimensions: 1536\n"
        "provider: openai\n",
        encoding="utf-8",
    )

    config = load_pgvector_config(tmp_path)

    assert config.enabled is True
    assert config.redacted_dsn() == "postgresql://app:***@localhost:5432/secondbrain"
    assert config.schema_name == "secondbrain_custom"
    assert config.table_prefix == "rag"
    assert config.vector_dimensions == 1536
    assert config.provider == "openai"


def test_pgvector_schema_sql_contains_required_objects(tmp_path):
    config = load_pgvector_config(tmp_path)
    sql = build_pgvector_schema_sql(config)

    assert "create extension if not exists vector" in sql
    assert "create schema if not exists secondbrain" in sql
    assert "p1_documents" in sql
    assert "p1_chunks" in sql
    assert "p1_chunk_embeddings" in sql
    assert "vector(1536)" in sql
    assert "ivfflat" in sql


def test_pgvector_readiness_warns_when_disabled_without_dsn(tmp_path):
    payload = pgvector_readiness(tmp_path, write_report=True)

    assert payload["schema"] == "secondbrain.p3_pgvector_foundation.v1"
    assert payload["ok"] is True
    assert payload["warnings"] >= 1
    assert payload["config"]["enabled"] is False
    assert (tmp_path / "runtime" / "reports" / "p3_pgvector_readiness_latest.json").exists()


def test_pgvector_readiness_blocks_when_enabled_without_dsn(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.delenv("SECONDBRAIN_PGVECTOR_DSN", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    payload = pgvector_readiness(tmp_path)

    assert payload["ok"] is False
    assert payload["status"] == "blocked"
    assert any(check["name"] == "pgvector_dsn_configured" and check["ok"] is False for check in payload["checks"])


def test_pgvector_readiness_launcher_command(tmp_path, capsys):
    rc = main(["--project-root", str(tmp_path), "p3-pgvector-readiness", "--write-report"])
    captured = capsys.readouterr().out

    assert rc == 0
    assert "secondbrain.p3_pgvector_foundation.v1" in captured
    assert "sql_preview" in captured
    assert (tmp_path / "runtime" / "reports" / "p3_pgvector_readiness_latest.json").exists()


def test_pgvector_command_index_registered():
    index = ModuleRegistry().command_index()

    assert index["p3-pgvector-readiness"] == "core"
    assert ModuleRegistry().resolve_command("p3-pgvector-readiness").key == "core"
