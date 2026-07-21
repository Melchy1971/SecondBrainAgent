"""Kontrollfluss des PostgreSQL-Live-Gates ohne echte Datenbank.

Die Live-Zertifizierung selbst braucht einen erreichbaren Server. Was hier
geprueft wird, ist die Logik davor und danach: Statusermittlung, Blocker-
Erkennung, Aufraeumen im Fehlerfall und Redaktion des Reports.

Diese Trennung ist Absicht. Ein Gate, dessen Auswertung erst am Live-System
auffaellt, ist als Nachweisinstrument wertlos.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any

import pytest

from secondbrain.release import postgres_live_gate as gate


# --------------------------------------------------------------------------
# Fake-Verbindung im psycopg-Stil
# --------------------------------------------------------------------------


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection
        self.description = None
        self._result: list[tuple] = []

    def execute(self, sql: str, params: Any = None) -> None:
        self.connection.statements.append(sql)
        for pattern, outcome in self.connection.failures.items():
            if pattern in sql:
                if outcome == "raise":
                    raise RuntimeError(f"simulated failure: {pattern}")
        self._result = self.connection.answer(sql)
        self.description = [("col",)] if self._result else None

    def fetchone(self):
        return self._result[0] if self._result else None

    def fetchall(self):
        return list(self._result)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConnection:
    def __init__(self, *, answers: dict[str, list[tuple]] | None = None,
                 failures: dict[str, str] | None = None) -> None:
        self.answers = answers or {}
        self.failures = failures or {}
        self.statements: list[str] = []
        self.autocommit = False
        self.closed = False
        self.rolled_back = 0

    def answer(self, sql: str) -> list[tuple]:
        for pattern, rows in self.answers.items():
            if pattern.lower() in sql.lower():
                return rows
        return []

    def cursor(self):
        return FakeCursor(self)

    def rollback(self) -> None:
        self.rolled_back += 1

    def close(self) -> None:
        self.closed = True


def _healthy_answers() -> dict[str, list[tuple]]:
    return {
        "SHOW server_version": [("18.4",)],
        "SELECT current_user": [("gate_user",)],
        "SELECT current_database()": [("secondbrain_test",)],
        "SHOW TimeZone": [("UTC",)],
        "usesuper": [(False,)],
        "pg_stat_ssl": [(True,)],
        "extversion": [("0.8.4",)],
        "SELECT amname": [("btree",), ("hnsw",), ("ivfflat",)],
        "has_database_privilege": [(True,)],
        "schema_migrations": [("001_core",)],
        "count(*)": [(1,)],
    }


DSN = "postgresql://user:secret@db.example.com:5432/secondbrain_test"


# Echtes pgvector 0.8.4 lehnt einen direkten hnsw-Index auf vector(3072) ab und
# akzeptiert den halfvec-Cast. Der Fake muss das nachbilden, sonst prueft der
# Test eine Umgebung, die es nicht gibt.
REALISTIC_PGVECTOR = {"vector_cosine_ops": "raise"}


def _healthy_connection(**overrides: Any) -> FakeConnection:
    answers = _healthy_answers()
    answers.update(overrides.pop("answers", {}))
    failures = dict(REALISTIC_PGVECTOR)
    failures.update(overrides.pop("failures", {}))
    return FakeConnection(answers=answers, failures=failures)


def _run(connection: FakeConnection, *, dsn: str = DSN, **kw):
    return gate.run_postgres_live_gate(
        ".", env={"TEST_DATABASE_URL": dsn}, connect=lambda _: connection,
        write_report=False, **kw
    )


# --------------------------------------------------------------------------
# Vorbedingungen
# --------------------------------------------------------------------------


def test_missing_test_database_url_is_blocked() -> None:
    report = gate.run_postgres_live_gate(".", env={}, write_report=False)
    assert report["status"] == gate.BLOCKED
    assert "TEST_DATABASE_URL is not set" in report["blockers"]


def test_production_database_url_is_never_read() -> None:
    """Die produktive DSN darf das Gate nicht aktivieren."""
    report = gate.run_postgres_live_gate(
        ".", env={"DATABASE_URL": DSN}, write_report=False
    )
    assert report["status"] == gate.BLOCKED


@pytest.mark.parametrize("dsn", ["mysql://h/db", "postgresql:///nohost", "not-a-dsn"])
def test_invalid_dsn_is_blocked(dsn: str) -> None:
    report = gate.run_postgres_live_gate(
        ".", env={"TEST_DATABASE_URL": dsn}, write_report=False
    )
    assert report["status"] == gate.BLOCKED


# --------------------------------------------------------------------------
# Statusermittlung
# --------------------------------------------------------------------------


def test_healthy_environment_is_conditional_pass_not_pass() -> None:
    """Teilumfang darf niemals als vollstaendige Zertifizierung gelten."""
    report = _run(_healthy_connection())
    assert report["status"] == gate.CONDITIONAL_PASS
    assert report["blockers"] == []
    assert set(report["scope"]["not_implemented_phases"]) == set(gate.NOT_IMPLEMENTED_PHASES)


def test_missing_pgvector_blocks() -> None:
    report = _run(_healthy_connection(answers={"extversion": []}))
    assert report["status"] == gate.BLOCKED
    assert "pgvector_installed" in report["blockers"]


def test_refused_tls_blocks() -> None:
    report = _run(_healthy_connection(answers={"pg_stat_ssl": [(False,)]}))
    assert report["status"] == gate.BLOCKED
    assert "transport_encryption" in report["blockers"]


def test_missing_create_privilege_blocks() -> None:
    report = _run(_healthy_connection(answers={"has_database_privilege": [(False,)]}))
    assert report["status"] == gate.BLOCKED
    assert "isolated_schema" in report["blockers"]


def test_non_utc_timezone_warns_but_does_not_block() -> None:
    report = _run(_healthy_connection(answers={"SHOW TimeZone": [("Europe/Berlin",)]}))
    assert report["status"] != gate.BLOCKED
    assert "timezone_utc" in report["warnings"]


def test_unexpected_direct_vector_index_blocks() -> None:
    """Gelingt der direkte Index auf 3072 Dimensionen, stimmt unsere Annahme nicht."""
    connection = FakeConnection(answers=_healthy_answers())
    report = _run(connection)
    # Die Fake-Verbindung laesst jedes CREATE INDEX gelingen, auch den direkten.
    assert "vector_index_limit_as_documented" in report["blockers"]


# --------------------------------------------------------------------------
# Isolierte Testumgebung und Aufraeumen
# --------------------------------------------------------------------------


def test_schema_is_dropped_on_success() -> None:
    connection = _healthy_connection()
    _run(connection)
    created = [s for s in connection.statements if s.startswith("CREATE SCHEMA")]
    dropped = [s for s in connection.statements if s.startswith("DROP SCHEMA")]
    assert len(created) == 1 and len(dropped) == 1
    assert created[0].split()[-1] in dropped[0]


def test_schema_is_dropped_when_checks_fail() -> None:
    """Aufraeumen muss auch im Fehlerfall laufen -- Prompt 68 Phase 2."""
    connection = _healthy_connection(failures={"CREATE TABLE": "raise"})
    report = _run(connection)
    assert any(s.startswith("DROP SCHEMA") for s in connection.statements), (
        "Testschema blieb nach einem Fehler zurueck"
    )
    assert report["status"] == gate.BLOCKED


def test_schema_name_is_unique_per_run() -> None:
    names = set()
    for _ in range(3):
        connection = _healthy_connection()
        _run(connection)
        names.update(
            s.split()[-1] for s in connection.statements if s.startswith("CREATE SCHEMA")
        )
    assert len(names) == 3, "Schemanamen kollidieren zwischen Laeufen"


def test_connection_is_closed() -> None:
    connection = _healthy_connection()
    _run(connection)
    assert connection.closed


def test_no_destructive_statements() -> None:
    connection = _healthy_connection()
    _run(connection)
    joined = " ".join(connection.statements).upper()
    assert "DROP DATABASE" not in joined
    assert "TRUNCATE" not in joined
    for statement in connection.statements:
        if statement.startswith("DROP SCHEMA"):
            assert gate.SCHEMA_PREFIX in statement, "DROP SCHEMA ausserhalb des Testschemas"


# --------------------------------------------------------------------------
# Redaktion
# --------------------------------------------------------------------------


def test_report_contains_no_credentials() -> None:
    report = _run(_healthy_connection())
    serialized = json.dumps(report)
    for secret in ("secret", "db.example.com", "user:secret", DSN):
        assert secret not in serialized, f"{secret!r} steht im Report"


def test_report_identifies_target_without_exposing_it() -> None:
    report = _run(_healthy_connection())
    assert len(report["target"]["host_fingerprint"]) == 12
    assert report["target"]["database"] == "secondbrain_test"


def test_connection_error_is_redacted() -> None:
    def failing(_: str):
        raise RuntimeError(f"connection to {DSN} failed")

    report = gate.run_postgres_live_gate(
        ".", env={"TEST_DATABASE_URL": DSN}, connect=failing, write_report=False
    )
    assert report["status"] == gate.BLOCKED
    assert DSN not in json.dumps(report)
    assert report["error"]["message"] == "live database operation failed"
