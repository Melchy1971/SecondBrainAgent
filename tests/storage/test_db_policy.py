import pytest
from secondbrain.storage.db_policy import resolve, parse_dialect, DatabaseStartupError


def test_dialect_parsing():
    assert parse_dialect("postgresql+psycopg://u:p@h/db") == "postgresql"
    assert parse_dialect("postgres://h/db") == "postgresql"
    assert parse_dialect("sqlite:///x.db") == "sqlite"
    assert parse_dialect(None) is None


def test_postgres_url_is_production_backend():
    r = resolve({"DATABASE_URL": "postgresql://u@h/db", "SECOND_BRAIN_ENV": "production"})
    assert r.backend == "postgresql" and r.is_fallback is False


def test_sqlite_in_production_blocks_without_flag():
    with pytest.raises(DatabaseStartupError):
        resolve({"DATABASE_URL": "sqlite:///x.db", "SECOND_BRAIN_ENV": "production"})


def test_sqlite_allowed_in_development():
    r = resolve({"DATABASE_URL": "sqlite:///x.db", "SECOND_BRAIN_ENV": "development"})
    assert r.backend == "sqlite"


def test_missing_url_blocks_without_fallback():
    with pytest.raises(DatabaseStartupError):
        resolve({"SECOND_BRAIN_ENV": "production"})


def test_missing_url_falls_back_only_when_enabled():
    r = resolve({"SECOND_BRAIN_ALLOW_SQLITE_FALLBACK": "1", "SECOND_BRAIN_ENV": "development"})
    assert r.backend == "sqlite" and r.is_fallback is True
    assert r.url.startswith("sqlite:")
