"""Konfigurationsfehler duerfen nicht als Verbindungsfehler auftreten.

Hintergrund (2026-07-21, Live-Lauf gegen PostgreSQL 18.4)
--------------------------------------------------------
``SqlExecutor.ping()`` fing jede Exception ab und lieferte ``False``. Zwei
reale Folgen:

1. ``No module named 'psycopg2'`` erschien als ``database ping failed``.
2. ``server does not support SSL, but SSL was required`` ebenfalls.

In beiden Faellen lief ``run_with_retry`` vier Versuche mit exponentiellem
Backoff gegen eine Bedingung, die sich durch Wiederholung nie aendert -- und
bei aktiviertem Fallback waere still auf SQLite umgeschaltet worden, obwohl
die Datenbank erreichbar war.
"""

from __future__ import annotations

import pytest

from secondbrain.storage.db_executor import (
    DatabaseConfigurationError,
    SqlExecutor,
    classify_error,
)
from secondbrain.storage.db_policy import DatabaseStartupError
from secondbrain.storage.db_startup import normalize_postgres_url, validate_and_connect


class _FailingExecutor(SqlExecutor):
    dialect = "postgresql"

    def __init__(self, exc: BaseException) -> None:
        self.exc = exc
        self.calls = 0

    def execute(self, sql, params=None):  # noqa: ANN001, ANN201
        self.calls += 1
        raise self.exc


# --------------------------------------------------------------------------
# Klassifizierung
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "exc",
    [
        ModuleNotFoundError("No module named 'psycopg2'"),
        ImportError("cannot import name 'psycopg2'"),
        RuntimeError("connection failed: server does not support SSL, but SSL was required"),
        RuntimeError('FATAL: password authentication failed for user "x"'),
        RuntimeError('FATAL: database "nope" does not exist'),
        RuntimeError("no pg_hba.conf entry for host"),
    ],
)
def test_configuration_errors_are_permanent(exc: BaseException) -> None:
    assert classify_error(exc) == "permanent"


@pytest.mark.parametrize(
    "exc",
    [
        OSError("connection refused"),
        TimeoutError("timeout expired"),
        RuntimeError("server closed the connection unexpectedly"),
    ],
)
def test_reachability_errors_are_transient(exc: BaseException) -> None:
    assert classify_error(exc) == "transient"


# --------------------------------------------------------------------------
# ping() kollabiert Konfigurationsfehler nicht mehr auf False
# --------------------------------------------------------------------------


def test_ping_raises_on_missing_driver() -> None:
    executor = _FailingExecutor(ModuleNotFoundError("No module named 'psycopg2'"))
    with pytest.raises(DatabaseConfigurationError, match="psycopg2"):
        executor.ping()


def test_ping_raises_on_rejected_tls() -> None:
    executor = _FailingExecutor(
        RuntimeError("connection failed: server does not support SSL, but SSL was required")
    )
    with pytest.raises(DatabaseConfigurationError, match="does not support SSL"):
        executor.ping()


def test_ping_returns_false_on_transient_error() -> None:
    executor = _FailingExecutor(OSError("connection refused"))
    assert executor.ping() is False


# --------------------------------------------------------------------------
# Kein Retry und kein stiller Fallback bei permanenten Fehlern
# --------------------------------------------------------------------------


def _env(**overrides: str) -> dict[str, str]:
    env = {
        "DATABASE_URL": "postgresql://u:p@example.invalid:5432/db",
        "SECOND_BRAIN_ENV": "production",
    }
    env.update(overrides)
    return env


def test_configuration_error_is_not_retried() -> None:
    executor = _FailingExecutor(ModuleNotFoundError("No module named 'psycopg2'"))

    with pytest.raises(DatabaseStartupError, match="configuration error"):
        validate_and_connect(_env(), pg_executor_factory=lambda url: executor, sleeper=lambda _: None)

    assert executor.calls == 1, (
        f"Konfigurationsfehler wurde {executor.calls}x versucht - Retry kann ihn nie aufloesen"
    )


def test_configuration_error_does_not_fall_back_to_sqlite() -> None:
    """Ein Treiber- oder TLS-Problem darf nicht als 'Postgres unerreichbar' gelten."""
    executor = _FailingExecutor(
        RuntimeError("connection failed: server does not support SSL, but SSL was required")
    )
    env = _env(SECOND_BRAIN_ENV="development", SECOND_BRAIN_ALLOW_SQLITE_FALLBACK="1")

    with pytest.raises(DatabaseStartupError, match="configuration error"):
        validate_and_connect(env, pg_executor_factory=lambda url: executor, sleeper=lambda _: None)


# --------------------------------------------------------------------------
# Dialekt-Normalisierung
# --------------------------------------------------------------------------


def _only(*installed: str):
    return lambda name: name in installed


def test_bare_postgresql_url_prefers_psycopg3() -> None:
    normalized = normalize_postgres_url(
        "postgresql://u:p@host:5432/db", is_installed=_only("psycopg")
    )
    assert normalized == "postgresql+psycopg://u:p@host:5432/db"


def test_bare_postgresql_url_falls_back_to_psycopg2() -> None:
    normalized = normalize_postgres_url(
        "postgresql://u:p@host:5432/db", is_installed=_only("psycopg2")
    )
    assert normalized == "postgresql+psycopg2://u:p@host:5432/db"


def test_missing_driver_is_a_configuration_error() -> None:
    with pytest.raises(DatabaseConfigurationError, match="requirements-db.txt"):
        normalize_postgres_url("postgresql://u:p@host/db", is_installed=_only())


def test_explicit_dialect_is_left_untouched() -> None:
    for url in (
        "postgresql+psycopg://u:p@host/db",
        "postgresql+psycopg2://u:p@host/db",
        "sqlite:///local.db",
    ):
        assert normalize_postgres_url(url, is_installed=_only("psycopg")) == url


def test_query_parameters_survive_normalization() -> None:
    normalized = normalize_postgres_url(
        "postgresql://u:p@host:5432/db?sslmode=require", is_installed=_only("psycopg")
    )
    assert normalized.endswith("?sslmode=require")
