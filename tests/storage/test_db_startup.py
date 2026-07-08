import pytest
from secondbrain.storage.db_startup import validate_and_connect
from secondbrain.storage.db_policy import DatabaseStartupError
from secondbrain.storage.db_retry import RetryPolicy


class FakePg:
    dialect = "postgresql"
    def __init__(self, ok: bool):
        self._ok = ok
    def ping(self):
        return self._ok


_FAST = dict(retry=RetryPolicy(max_attempts=2, base_delay=0), sleeper=lambda _s: None)


def test_postgres_connected():
    rt = validate_and_connect({"DATABASE_URL": "postgresql://h/db", "SECOND_BRAIN_ENV": "production"},
                              pg_executor_factory=lambda url: FakePg(True), **_FAST)
    assert rt.backend == "postgresql" and rt.connected is True and rt.is_fallback is False


def test_postgres_unreachable_blocks_cleanly():
    with pytest.raises(DatabaseStartupError):
        validate_and_connect({"DATABASE_URL": "postgresql://h/db", "SECOND_BRAIN_ENV": "production"},
                             pg_executor_factory=lambda url: FakePg(False), **_FAST)


def test_postgres_unreachable_falls_back_only_with_flag():
    rt = validate_and_connect(
        {"DATABASE_URL": "postgresql://h/db", "SECOND_BRAIN_ENV": "production",
         "SECOND_BRAIN_ALLOW_SQLITE_FALLBACK": "1", "SECOND_BRAIN_SQLITE_DEV_PATH": ":memory:"},
        pg_executor_factory=lambda url: FakePg(False), **_FAST)
    assert rt.backend == "sqlite" and rt.is_fallback is True


def test_missing_url_blocks():
    with pytest.raises(DatabaseStartupError):
        validate_and_connect({"SECOND_BRAIN_ENV": "production"}, **_FAST)


def test_dev_sqlite_connects():
    rt = validate_and_connect({"SECOND_BRAIN_ENV": "development", "DATABASE_URL": "sqlite:///:memory:"}, **_FAST)
    assert rt.backend == "sqlite" and rt.connected is True
