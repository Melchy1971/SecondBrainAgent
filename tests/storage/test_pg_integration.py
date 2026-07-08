"""Real PostgreSQL integration - runs only when TEST_DATABASE_URL + SQLAlchemy are present."""
import os
import pytest

TEST_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_URL, reason="set TEST_DATABASE_URL to run PostgreSQL integration")


def test_postgres_validate_migrate_health():
    pytest.importorskip("sqlalchemy")
    from secondbrain.storage.db_provider import DatabaseProvider
    provider = DatabaseProvider.start({"DATABASE_URL": TEST_URL, "SECOND_BRAIN_ENV": "production"})
    assert provider.runtime.backend == "postgresql"
    provider.migrate()
    assert provider.health()["migrations"]["up_to_date"] is True
