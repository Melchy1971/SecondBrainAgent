from secondbrain.storage.database_config import DatabaseConfig
from secondbrain.storage.repositories.base_repository import RepositoryResult


def test_database_config_from_env():
    cfg = DatabaseConfig.from_env({
        "DATABASE_URL": "postgresql+psycopg://user:pass@localhost/db",
        "SECOND_BRAIN_DB_POOL_SIZE": "5",
        "SECOND_BRAIN_DB_MAX_OVERFLOW": "7",
    })
    assert cfg.pool_size == 5
    assert cfg.max_overflow == 7


def test_database_config_requires_url():
    try:
        DatabaseConfig.from_env({})
    except ValueError as exc:
        assert "DATABASE_URL" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_repository_result_defaults():
    result = RepositoryResult(status="PASS")
    assert result.affected == 0
    assert result.payload is None
