"""Kontrollfluss des PostgreSQL-Live-Gates ohne echte Datenbank.

Die Live-Zertifizierung selbst braucht einen erreichbaren Server. Was hier
geprueft wird, ist die Logik davor und danach: Statusermittlung, Blocker-
Erkennung, Aufraeumen im Fehlerfall und Redaktion des Reports.

Diese Trennung ist Absicht. Ein Gate, dessen Auswertung erst am Live-System
auffaellt, ist als Nachweisinstrument wertlos.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Any

import pytest

from secondbrain.release import postgres_live_gate as gate

_TEST_DB = os.environ.get("TEST_DATABASE_URL")


# --------------------------------------------------------------------------
# Fake-Verbindung im psycopg-Stil
# --------------------------------------------------------------------------


class FakeCursor:
    def __init__(self, connection: "FakeConnection") -> None:
        self.connection = connection
        self.description = None
        self.rowcount = 1
        self._result: list[tuple] = []

    def execute(self, sql: str, params: Any = None) -> None:
        self.connection.statements.append(sql)
        for pattern, outcome in self.connection.failures.items():
            if pattern in sql:
                if outcome == "raise":
                    raise RuntimeError(f"simulated failure: {pattern}")
        self._result = self.connection.answer(sql)
        self.description = [("col",)] if self._result else None
        # rowcount ist ein schlichtes Attribut, kein Property: ein Getter mit
        # Seiteneffekt wird schon von hasattr() ausgeloest.
        if sql.strip().upper().startswith("UPDATE"):
            if ".records" in sql:
                # Phase-4-Hijack: RLS laesst kein Update ueber die Grenze zu.
                self.rowcount = 0
            elif self.connection.rowcounts:
                self.rowcount = self.connection.rowcounts.pop(0)

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
                 failures: dict[str, str] | None = None,
                 sequences: dict[str, list[list[tuple]]] | None = None) -> None:
        self.answers = answers or {}
        self.failures = failures or {}
        self.sequences = sequences or {}
        self.statements: list[str] = []
        self.autocommit = False
        self.closed = False
        self.rolled_back = 0
        self.committed = 0
        # Optimistische Versionierung: erste Aktualisierung greift, zweite nicht.
        self.rowcounts: list[int] = [1, 0]

    def commit(self) -> None:
        self.committed += 1

    def answer(self, sql: str) -> list[tuple]:
        lowered = sql.lower()
        # Phase-4-spezifisch, nach Tabellen-Suffix, damit sich die Phasen nicht
        # ueberschneiden (records = Isolation, golden = Suche, queue = Concurrency).
        if "select id from" in lowered and ".records" in lowered:
            return [(1,)]                       # ws-a sieht nur die eigene Zeile
        if "count(*)" in lowered and ".records" in lowered:
            return [(0,)]                       # fail-closed ohne Kontext
        # Sequenzen: aufeinanderfolgende gleiche Abfragen, unterschiedliche
        # Ergebnisse -- noetig fuer SKIP LOCKED.
        for pattern, queue in self.sequences.items():
            if pattern.lower() in lowered and queue:
                return queue.pop(0)
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
        # EXPLAIN zuerst: die Zeichenkette enthaelt auch "SELECT id FROM".
        "EXPLAIN": [("Limit  (cost=..)",), ("  ->  Index Scan using golden_hnsw on golden",)],
        "SELECT id FROM": [(0,), (1,), (2,), (3,), (4,)],
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
REALISTIC_PGVECTOR = {
    "vector_cosine_ops": "raise",   # direkter Index auf 3072 Dimensionen
    "9001": "raise",                # Dimension Guard weist 3-dim Vektor ab
    "(99,": "raise",                # doppelter Idempotency Key
    "'x')": "raise",                # WITH CHECK weist Cross-Workspace-Insert ab
}


def _skip_locked_sequence() -> dict[str, list[list[tuple]]]:
    """Zwei Worker, zwei verschiedene Zeilen -- so verhaelt sich SKIP LOCKED."""
    return {"FOR UPDATE SKIP LOCKED": [[(1,)], [(2,)]]}


def _healthy_connection(**overrides: Any) -> FakeConnection:
    answers = _healthy_answers()
    answers.update(overrides.pop("answers", {}))
    failures = dict(REALISTIC_PGVECTOR)
    failures.update(overrides.pop("failures", {}))
    sequences = _skip_locked_sequence()
    sequences.update(overrides.pop("sequences", {}))
    return FakeConnection(answers=answers, failures=failures, sequences=sequences)


def _passing_repository_contracts(connector, dsn, schema):
    """Kontrollfluss-Stub: die produktiven Contracts brauchen ein echtes
    PostgreSQL. Hier wird nur die Aggregation geprueft, daher passieren alle."""
    names = [
        "repo_crud", "repo_optimistic_version", "repo_idempotent_repeat",
        "repo_version_conflict", "repo_workspace_isolation",
        "repo_cross_workspace_prevented", "repo_transaction_rollback",
        "repo_jsonl_migration", "repo_utc_serialization",
    ]
    return [{"name": n, "ok": True, "contract_status": "PASS", "detail": "ok",
             "duration_ms": 0.1, "blocking": True} for n in names]


def _run(connection: FakeConnection, *, dsn: str = DSN, **kw):
    kw.setdefault("repository_contracts_impl", _passing_repository_contracts)
    return gate.run_postgres_live_gate(
        ".", env={"TEST_DATABASE_URL": dsn}, connect=lambda _: connection,
        write_report=False, **kw
    )


# --------------------------------------------------------------------------
# Phase 3 -- Repository-Vertraege (Kontrollfluss, ohne Datenbank)
# --------------------------------------------------------------------------


def test_not_implemented_phases_is_empty() -> None:
    assert gate.NOT_IMPLEMENTED_PHASES == ()


def test_repository_contracts_appears_in_report() -> None:
    report = _run(_healthy_connection())
    names = {c["name"] for c in report["checks"]}
    assert "repo_crud" in names
    assert "repository_contracts" in report["facts"]
    assert "repository_contracts" in report["scope"]["implemented_phases"]


def test_healthy_environment_reaches_pass() -> None:
    """Mit erreichbarer DB und bestandenen Contracts ist PASS moeglich."""
    report = _run(_healthy_connection())
    assert report["status"] == gate.PASS, report.get("blockers")
    assert report["scope"]["not_implemented_phases"] == []


def test_repository_contracts_schema_is_dropped() -> None:
    connection = _healthy_connection()
    _run(connection)
    dropped = [s for s in connection.statements if s.startswith("DROP SCHEMA")]
    assert any("_repo_" in s for s in dropped), "Contract-Testschema blieb zurueck"


def test_repository_contract_failure_blocks() -> None:
    def failing_impl(connector, dsn, schema):
        return [{"name": "repo_crud", "ok": False, "contract_status": "FAIL",
                 "detail": "AssertionError", "duration_ms": 1.0, "blocking": True}]

    report = _run(_healthy_connection(), repository_contracts_impl=failing_impl)
    assert report["status"] == gate.BLOCKED
    assert "repo_crud" in report["blockers"]


def test_repository_contracts_schema_dropped_even_on_error() -> None:
    def exploding_impl(connector, dsn, schema):
        raise RuntimeError("contract crashed")

    connection = _healthy_connection()
    report = _run(connection, repository_contracts_impl=exploding_impl)
    assert any("_repo_" in s for s in connection.statements if s.startswith("DROP SCHEMA")), (
        "Contract-Schema muss auch bei Absturz entfernt werden"
    )
    assert report["status"] == gate.BLOCKED


def test_repository_contract_error_is_redacted() -> None:
    """Ein Contract-Fehler darf keine DSN oder rohe Meldung durchreichen."""
    def leaky_impl(connector, dsn, schema):
        raise RuntimeError(f"boom against {dsn}")

    report = _run(_healthy_connection(), repository_contracts_impl=leaky_impl)
    assert DSN not in json.dumps(report)
    assert "secret" not in json.dumps(report)


def test_contract_helper_records_status_and_duration() -> None:
    ok = gate._contract("x", lambda: (True, "fine"))
    assert ok["contract_status"] == "PASS" and ok["ok"] is True
    assert isinstance(ok["duration_ms"], float)

    bad = gate._contract("y", lambda: (False, "nope"))
    assert bad["contract_status"] == "FAIL" and bad["blocking"] is True

    def _raise():
        raise ValueError("with dsn postgresql://u:p@h/db inside")
    red = gate._contract("z", _raise)
    assert red["contract_status"] == "FAIL"
    assert red["detail"] == "ValueError"  # nur Klasse, keine Meldung
    assert "postgresql://" not in json.dumps(red)


def test_contract_skip_is_non_blocking() -> None:
    def _skip():
        raise gate._ContractSkip("not applicable to production class")
    result = gate._contract("s", _skip)
    assert result["contract_status"] == "SKIPPED"
    assert result["blocking"] is False and result["ok"] is True


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


def test_conditional_pass_when_a_phase_is_still_missing(monkeypatch) -> None:
    """Solange eine Phase als not_implemented gilt, ist PASS unzulaessig.

    Historie: Frueher galt das dauerhaft (repository_contracts fehlte). Seit die
    Phase implementiert ist, wird die Regel hier durch einen simulierten
    Rueckfall geprueft -- der Deckel gegen falsches PASS muss bleiben.
    """
    monkeypatch.setattr(gate, "NOT_IMPLEMENTED_PHASES", ("simulated_pending",))
    report = _run(_healthy_connection())
    assert report["status"] == gate.CONDITIONAL_PASS
    assert report["blockers"] == []


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
    """Jedes erzeugte Schema wird wieder entfernt -- Phase 2 und Phase 5."""
    connection = _healthy_connection()
    _run(connection)
    created = [s.split()[-1] for s in connection.statements if s.startswith("CREATE SCHEMA")]
    dropped = " ".join(s for s in connection.statements if s.startswith("DROP SCHEMA"))
    assert created, "kein Testschema angelegt"
    for schema in created:
        assert schema in dropped, f"{schema} wurde nicht entfernt"


def test_schema_is_dropped_when_checks_fail() -> None:
    """Aufraeumen muss auch im Fehlerfall laufen -- Prompt 68 Phase 2."""
    connection = _healthy_connection(failures={"CREATE TABLE": "raise"})
    report = _run(connection)
    assert any(s.startswith("DROP SCHEMA") for s in connection.statements), (
        "Testschema blieb nach einem Fehler zurueck"
    )
    assert report["status"] == gate.BLOCKED


def test_schema_name_is_unique_per_run() -> None:
    """Parallele Gate-Laeufe duerfen sich nicht gegenseitig das Schema wegziehen."""
    runs = 3
    names: list[str] = []
    for _ in range(runs):
        connection = _healthy_connection()
        _run(connection)
        names.extend(
            s.split()[-1] for s in connection.statements if s.startswith("CREATE SCHEMA")
        )
    assert len(names) == len(set(names)), f"Schemanamen kollidieren: {names}"
    # Je Lauf: Phase 2 (isolated), Phase 3 (repository_contracts), Phase 4 (RLS),
    # Phase 5 (concurrency).
    assert len(names) == runs * 4, "erwartet je vier Schemata pro Lauf"


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
# Phase 6 -- Vektorsuche
# --------------------------------------------------------------------------


def _named(report, name: str) -> dict:
    for check in report["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Pruefung {name!r} fehlt im Report")


def test_golden_vector_is_deterministic() -> None:
    """Eine Recall-Erwartung, die sich zwischen Laeufen aendert, ist kein Nachweis."""
    assert gate.golden_vector(3) == gate.golden_vector(3)
    assert gate.golden_vector(3) != gate.golden_vector(4)
    vector = gate.golden_vector(7)
    assert len(vector) == gate.PROJECT_DIMENSIONS
    assert sum(vector) == 1.0 and vector[7] == 1.0


def test_vector_search_checks_run_in_healthy_environment() -> None:
    report = _run(_healthy_connection())
    for name in (
        "vector_search_returns_results",
        "vector_search_exact_match_first",
        "vector_search_min_recall",
        "vector_index_used_by_query",
        "dimension_guard_rejects_mismatch",
        "reindex",
        "search_after_reindex",
    ):
        assert _named(report, name)["ok"], f"{name} fehlgeschlagen"
    assert report["facts"]["recall"] >= gate.MIN_RECALL


def test_sequential_scan_despite_index_is_blocked() -> None:
    """Die stille Fehlerklasse: Index vorhanden, Abfrage trifft ihn nicht."""
    report = _run(_healthy_connection(answers={"EXPLAIN": [("Seq Scan on golden",)]}))
    assert report["status"] == gate.BLOCKED
    assert "vector_index_used_by_query" in report["blockers"]


def test_wrong_search_result_order_is_blocked() -> None:
    report = _run(_healthy_connection(answers={"SELECT id FROM": [(42,), (1,), (2,), (3,), (4,)]}))
    assert report["status"] == gate.BLOCKED
    assert "vector_search_exact_match_first" in report["blockers"]
    assert "vector_search_min_recall" in report["blockers"]


def test_accepted_dimension_mismatch_is_blocked() -> None:
    """Nimmt die Datenbank einen 3-dim Vektor in vector(3072) an, ist der Guard defekt."""
    # "allow" ueberschreibt das "raise" aus REALISTIC_PGVECTOR: die Datenbank
    # nimmt den zu kurzen Vektor entgegen, statt ihn abzuweisen.
    report = _run(_healthy_connection(failures={"9001": "allow"}))
    assert report["status"] == gate.BLOCKED
    assert "dimension_guard_rejects_mismatch" in report["blockers"]


def test_vector_search_skipped_when_index_unavailable() -> None:
    report = _run(_healthy_connection(failures={"halfvec_cosine_ops": "raise"}))
    assert report["status"] == gate.BLOCKED
    assert "halfvec_index_creatable" in report["blockers"]
    assert _named(report, "vector_search")["ok"] is False


def test_golden_dataset_stays_inside_test_schema() -> None:
    connection = _healthy_connection()
    _run(connection)
    for statement in connection.statements:
        if statement.startswith(("CREATE TABLE", "INSERT INTO", "CREATE INDEX", "ANALYZE")):
            assert gate.SCHEMA_PREFIX in statement or "golden_hnsw" in statement, (
                f"Statement ausserhalb des Testschemas: {statement[:80]}"
            )


# --------------------------------------------------------------------------
# Phase 4 -- Workspace-Isolation
# --------------------------------------------------------------------------


def test_workspace_isolation_checks_run_in_healthy_environment() -> None:
    report = _run(_healthy_connection())
    for name in (
        "rls_read_isolation",
        "rls_fail_closed_without_context",
        "rls_write_check_blocks_cross_workspace",
        "rls_update_cannot_reach_other_workspace",
    ):
        assert _named(report, name)["ok"], f"{name} fehlgeschlagen"
    assert "workspace_isolation" not in report["scope"]["not_implemented_phases"]


def test_rls_leak_is_blocked() -> None:
    """Sieht ws-a mehr als die eigene Zeile, ist die Isolation gebrochen."""
    connection = _healthy_connection()

    original = connection.answer

    def leaky(sql: str):
        if "select id from" in sql.lower() and ".records" in sql.lower():
            return [(1,), (2,)]           # ws-a sieht auch die Zeile von ws-b
        return original(sql)

    connection.answer = leaky  # type: ignore[method-assign]
    report = _run(connection)
    assert report["status"] == gate.BLOCKED
    assert "rls_read_isolation" in report["blockers"]


def test_rls_not_fail_closed_is_blocked() -> None:
    connection = _healthy_connection()
    original = connection.answer

    def visible(sql: str):
        if "count(*)" in sql.lower() and ".records" in sql.lower():
            return [(2,)]                 # ohne Kontext trotzdem Zeilen sichtbar
        return original(sql)

    connection.answer = visible  # type: ignore[method-assign]
    report = _run(connection)
    assert report["status"] == gate.BLOCKED
    assert "rls_fail_closed_without_context" in report["blockers"]


def test_accepted_cross_workspace_write_is_blocked() -> None:
    """Laesst WITH CHECK einen fremden Insert durch, fehlt der Schutz."""
    failures = dict(REALISTIC_PGVECTOR)
    failures["'x')"] = "allow"
    report = _run(_healthy_connection(failures=failures))
    assert report["status"] == gate.BLOCKED
    assert "rls_write_check_blocks_cross_workspace" in report["blockers"]


def test_workspace_isolation_schema_is_dropped() -> None:
    connection = _healthy_connection()
    _run(connection)
    dropped = [s for s in connection.statements if s.startswith("DROP SCHEMA")]
    assert any("_rls_" in s for s in dropped), "RLS-Testschema blieb zurueck"


# --------------------------------------------------------------------------
# Phase 5 -- Concurrency
# --------------------------------------------------------------------------


def test_concurrency_checks_run_in_healthy_environment() -> None:
    report = _run(_healthy_connection())
    for name in (
        "idempotency_key_unique",
        "skip_locked_both_workers_get_work",
        "skip_locked_no_double_claim",
        "optimistic_versioning_blocks_stale_write",
    ):
        assert _named(report, name)["ok"], f"{name} fehlgeschlagen"
    assert report["facts"]["claimed"] == [1, 2]


def test_double_claim_is_blocked() -> None:
    """Zwei Worker duerfen niemals dieselbe Zeile beanspruchen."""
    report = _run(_healthy_connection(
        sequences={"FOR UPDATE SKIP LOCKED": [[(1,)], [(1,)]]}
    ))
    assert report["status"] == gate.BLOCKED
    assert "skip_locked_no_double_claim" in report["blockers"]


def test_accepted_duplicate_idempotency_key_is_blocked() -> None:
    report = _run(_healthy_connection(failures={"(99,": "allow"}))
    assert report["status"] == gate.BLOCKED
    assert "idempotency_key_unique" in report["blockers"]


def test_stale_write_that_succeeds_is_blocked() -> None:
    """Greift die zweite Aktualisierung mit veralteter Version, fehlt der Schutz."""
    connection = _healthy_connection()
    connection.rowcounts = [1, 1]
    report = _run(connection)
    assert report["status"] == gate.BLOCKED
    assert "optimistic_versioning_blocks_stale_write" in report["blockers"]


def test_concurrency_schema_is_dropped() -> None:
    connection = _healthy_connection()
    report = _run(connection)
    dropped = [s for s in connection.statements if s.startswith("DROP SCHEMA")]
    assert any("_conc_" in s for s in dropped), "Concurrency-Schema blieb zurueck"
    assert report["facts"]["cleanup_schema_dropped"] is True


def test_concurrency_connections_are_closed() -> None:
    """Drei Verbindungen werden geoeffnet -- keine darf offen bleiben."""
    connection = _healthy_connection()
    _run(connection)
    assert connection.closed


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


# --------------------------------------------------------------------------
# Optionaler Integrationstest -- nur mit gesetzter TEST_DATABASE_URL
# --------------------------------------------------------------------------


@pytest.mark.skipif(not _TEST_DB, reason="set TEST_DATABASE_URL for the live repository-contract run")
def test_repository_contracts_live() -> None:
    """Faehrt die produktiven Repository-Contracts gegen echtes PostgreSQL.

    Ohne TEST_DATABASE_URL wird der Test uebersprungen -- niemals faelschlich
    als PASS gewertet. Das Testschema wird im finally-Pfad entfernt.
    """
    pytest.importorskip("psycopg")
    from secondbrain.release.postgres_live_gate import (
        _default_connect,
        _repository_contracts_checks,
    )

    checks, facts = _repository_contracts_checks(_default_connect, _TEST_DB)
    by_name = {c["name"]: c for c in checks}
    for contract in (
        "repo_crud", "repo_optimistic_version", "repo_idempotent_repeat",
        "repo_version_conflict", "repo_workspace_isolation",
        "repo_cross_workspace_prevented", "repo_transaction_rollback",
        "repo_jsonl_migration", "repo_utc_serialization",
    ):
        assert contract in by_name, f"{contract} fehlt im Report"
        assert by_name[contract]["ok"], f"{contract}: {by_name[contract]['detail']}"
    assert facts["cleanup_schema_dropped"] is True


@pytest.mark.skipif(not _TEST_DB, reason="set TEST_DATABASE_URL for the full live gate run")
def test_full_gate_live_reaches_pass_or_conditional() -> None:
    pytest.importorskip("psycopg")
    report = gate.run_postgres_live_gate(".", env={"TEST_DATABASE_URL": _TEST_DB}, write_report=False)
    assert report["status"] in {gate.PASS, gate.CONDITIONAL_PASS}, report.get("blockers")
    assert _TEST_DB not in json.dumps(report)
