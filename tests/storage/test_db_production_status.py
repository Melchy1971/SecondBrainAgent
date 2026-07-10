from __future__ import annotations

from secondbrain.storage.db_production_status import evaluate_db_pgvector_production_status


class FakePgExecutor:
    dialect = "postgresql"

    def __init__(self, ping_ok: bool = True, similarity_ok: bool = True) -> None:
        self._ping_ok = ping_ok
        self._similarity_ok = similarity_ok

    def ping(self) -> bool:
        return self._ping_ok

    def execute(self, sql: str, params=None):
        _ = params
        statement = sql.strip().lower()
        if "count(*) from schema_migrations" in statement:
            return [(3,)]
        if "::vector <=>" in statement:
            if not self._similarity_ok:
                raise RuntimeError("vector operator unavailable")
            return [(0.0,)]
        if statement == "select 1":
            return [(1,)]
        return []


def test_status_degraded_without_database_url(tmp_path):
    payload = evaluate_db_pgvector_production_status(tmp_path, env={})

    assert payload["status"] == "degraded_sqlite"
    assert payload["production_ready"] is False


def test_status_blocked_when_postgres_is_unreachable(tmp_path):
    payload = evaluate_db_pgvector_production_status(
        tmp_path,
        env={"DATABASE_URL": "postgresql://user:pw@db:5432/app"},
        pg_executor_factory=lambda _url: FakePgExecutor(ping_ok=False),
        pgvector_probe=lambda _cfg: {"ok": True, "status": "pass"},
    )

    assert payload["status"] == "blocked_missing_database"
    assert payload["production_ready"] is False


def test_status_blocked_when_pgvector_extension_missing(tmp_path):
    payload = evaluate_db_pgvector_production_status(
        tmp_path,
        env={"DATABASE_URL": "postgresql://user:pw@db:5432/app"},
        pg_executor_factory=lambda _url: FakePgExecutor(ping_ok=True),
        pgvector_probe=lambda _cfg: {"ok": False, "status": "blocked", "error": "pgvector_extension_missing"},
    )

    assert payload["status"] == "blocked_missing_pgvector"
    assert payload["production_ready"] is False


def test_status_ready_when_postgres_and_pgvector_are_valid(tmp_path):
    payload = evaluate_db_pgvector_production_status(
        tmp_path,
        env={"DATABASE_URL": "postgresql://user:pw@db:5432/app"},
        pg_executor_factory=lambda _url: FakePgExecutor(ping_ok=True, similarity_ok=True),
        pgvector_probe=lambda _cfg: {"ok": True, "status": "pass", "vector_extension_installed": True},
    )

    assert payload["status"] == "ready"
    assert payload["production_ready"] is True
