from __future__ import annotations

import json
import sys
import types

from launcher import main
from secondbrain.module_registry import ModuleRegistry
from secondbrain.p3_pgvector_foundation import apply_pgvector_schema, build_pgvector_schema_sql, load_pgvector_config, pgvector_live_check, pgvector_readiness, redact_dsn


class _FakeCursor:
    def __init__(self):
        self.queries: list[str] = []
        self._last_query = ""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql):
        self._last_query = str(sql)
        self.queries.append(self._last_query)

    def fetchone(self):
        if "select version" in self._last_query:
            return ["PostgreSQL 16 fake"]
        if "pg_extension" in self._last_query:
            return ["0.7.4"]
        return [1]


class _FakeConnection:
    def __init__(self):
        self.cursor_obj = _FakeCursor()
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True


class _FakePsycopg:
    def __init__(self):
        self.connections: list[_FakeConnection] = []

    def connect(self, dsn, connect_timeout=5):
        assert dsn.startswith("postgresql://")
        assert connect_timeout == 5
        conn = _FakeConnection()
        self.connections.append(conn)
        return conn


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

    assert payload["schema"] == "secondbrain.p3_pgvector_foundation.v2"
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


def test_pgvector_live_check_uses_psycopg_when_enabled(tmp_path, monkeypatch):
    fake = _FakePsycopg()
    monkeypatch.setitem(sys.modules, "psycopg", fake)
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")
    config = load_pgvector_config(tmp_path)

    live = pgvector_live_check(config)

    assert live["ok"] is True
    assert live["postgres_version"] == "PostgreSQL 16 fake"
    assert live["vector_extension_installed"] is True
    assert live["vector_extension_version"] == "0.7.4"
    assert live["dsn"] == "postgresql://user:***@db:5432/app"


def test_pgvector_live_check_blocks_when_psycopg_missing(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "psycopg", None)
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")
    config = load_pgvector_config(tmp_path)

    live = pgvector_live_check(config)

    assert live["ok"] is False
    assert live["status"] == "blocked"
    assert live["error"] == "psycopg_missing"


def test_pgvector_apply_schema_dry_run_does_not_need_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")
    config = load_pgvector_config(tmp_path)

    result = apply_pgvector_schema(config, dry_run=True)

    assert result["ok"] is True
    assert result["status"] == "dry_run"
    assert result["applied"] is False
    assert "create extension if not exists vector" in result["sql"]


def test_pgvector_apply_schema_executes_with_fake_psycopg(tmp_path, monkeypatch):
    fake = _FakePsycopg()
    monkeypatch.setitem(sys.modules, "psycopg", fake)
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")
    config = load_pgvector_config(tmp_path)

    result = apply_pgvector_schema(config, dry_run=False)

    assert result["ok"] is True
    assert result["applied"] is True
    assert fake.connections[0].committed is True
    assert any("create extension if not exists vector" in q for q in fake.connections[0].cursor_obj.queries)


def test_pgvector_readiness_launcher_command(tmp_path, capsys):
    rc = main(["--project-root", str(tmp_path), "p3-pgvector-readiness", "--write-report"])
    captured = capsys.readouterr().out

    assert rc == 0
    assert "secondbrain.p3_pgvector_foundation.v2" in captured
    assert "sql_preview" in captured
    assert (tmp_path / "runtime" / "reports" / "p3_pgvector_readiness_latest.json").exists()


def test_pgvector_readiness_launcher_live_with_fake_psycopg(tmp_path, capsys, monkeypatch):
    fake = _FakePsycopg()
    monkeypatch.setitem(sys.modules, "psycopg", fake)
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_ENABLED", "true")
    monkeypatch.setenv("SECONDBRAIN_PGVECTOR_DSN", "postgresql://user:pw@db:5432/app")

    rc = main(["--project-root", str(tmp_path), "p3-pgvector-readiness", "--live", "--write-report"])
    captured = capsys.readouterr().out

    assert rc == 0
    assert "pgvector_live_connection" in captured
    assert "PostgreSQL 16 fake" in captured


def test_pgvector_command_index_registered():
    index = ModuleRegistry().command_index()

    assert index["p3-pgvector-readiness"] == "core"
    assert ModuleRegistry().resolve_command("p3-pgvector-readiness").key == "core"
