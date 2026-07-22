"""PostgreSQL- und pgvector-Live-Gate (Prompt 68, Phase 1, 2 und 8).

Umfang dieser Stufe
-------------------
Phase 1  Preflight: Treiber, Verbindung, Version, SSL, Rechte, Zeitzone,
         Migrationsstand, pgvector-Extension und Indexfaehigkeit.
Phase 2  Isolierte Testumgebung: eigenes Schema je Lauf, Aufraeumen im
         ``finally``-Block, niemals Zugriff auf produktive Tabellen.
Phase 4  Workspace-Isolation per Row Level Security: Lese-Isolation,
         fail-closed ohne Kontext, WITH-CHECK gegen Cross-Workspace-Schreiben,
         kein Update ueber die Grenze.
Phase 5  Concurrency: ``FOR UPDATE SKIP LOCKED`` ohne Doppelvergabe,
         optimistische Versionierung, doppelter Idempotency Key.
Phase 6  Vektorsuche: Golden Dataset, Trefferqualitaet, Mindest-Recall,
         nachgewiesene Indexnutzung, Dimension Guard, Reindex.
Phase 8  Redigierter Report.

Offen bleibt allein Phase 3 (Repository-Vertraege). Der Report weist sie als
``not_implemented`` aus, damit ein Teilumfang nicht als vollstaendige
Zertifizierung missverstanden wird.

Sicherheit
----------
* Liest ausschliesslich ``TEST_DATABASE_URL``. ``DATABASE_URL`` wird nie
  gelesen und nie veraendert.
* Kein Report-Feld enthaelt DSN, Passwort, Host oder Port.
* Jedes erzeugte Objekt liegt im Testschema und wird im ``finally`` entfernt.
* Kein ``DROP DATABASE``, kein globales ``TRUNCATE``.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit
from uuid import uuid4

PASS, CONDITIONAL_PASS, BLOCKED = "PASS", "CONDITIONAL_PASS", "BLOCKED"
REPORT_PATH = Path("runtime/reports/postgres_live_gate.json")

SCHEMA_PREFIX = "sb_gate"

# pgvector indiziert vector mit hnsw/ivfflat bis 2000, halfvec bis 4000.
# Belegt gegen PostgreSQL 18.4 / pgvector 0.8.4 am 2026-07-21.
MAX_VECTOR_INDEX_DIMENSIONS = 2000
PROJECT_DIMENSIONS = 3072

NOT_IMPLEMENTED_PHASES: tuple[str, ...] = ()

# Workspace-Bezeichner fuer die Repository-Contract-Phase.
_RC_WS_A = "gate-ws-a"
_RC_WS_B = "gate-ws-b"

# Golden Dataset: klein, deterministisch, ohne Zufall. Ein Recall-Nachweis,
# dessen Erwartung sich zwischen Laeufen aendert, ist kein Nachweis.
GOLDEN_ROWS = 64
GOLDEN_TOP_K = 5
MIN_RECALL = 0.8


# --------------------------------------------------------------------------
# Hilfen
# --------------------------------------------------------------------------


def _check(name: str, ok: bool, *, detail: str = "", blocking: bool = True) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail, "blocking": bool(blocking)}


def _safe_error(exc: BaseException) -> dict[str, str]:
    """Fehlertyp ohne Inhalt -- Meldungen koennen DSN-Fragmente enthalten."""
    return {"type": type(exc).__name__, "message": "live database operation failed"}


def _fingerprint(dsn: str) -> dict[str, Any]:
    parsed = urlsplit(dsn)
    host = (parsed.hostname or "").encode()
    return {
        "host_fingerprint": hashlib.sha256(host).hexdigest()[:12] if host else "unknown",
        "database": (parsed.path or "/").lstrip("/") or "unknown",
        "sslmode_requested": "sslmode=require" in (parsed.query or ""),
    }


def _validate_dsn(dsn: str) -> None:
    parsed = urlsplit(dsn)
    if parsed.scheme not in {"postgres", "postgresql", "postgresql+psycopg", "postgresql+psycopg2"}:
        raise ValueError("TEST_DATABASE_URL must be a PostgreSQL DSN")
    if not parsed.hostname:
        raise ValueError("TEST_DATABASE_URL has no host")


def _default_connect(dsn: str):  # pragma: no cover - benoetigt psycopg + Server
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("psycopg is required; install requirements-db.txt") from exc
    # SQLAlchemy-Dialektpraefix ist fuer psycopg direkt unzulaessig.
    for prefix in ("postgresql+psycopg2://", "postgresql+psycopg://"):
        if dsn.startswith(prefix):
            dsn = "postgresql://" + dsn[len(prefix):]
            break
    return psycopg.connect(dsn, connect_timeout=10)


def _scalar(connection, sql: str) -> Any:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        row = cursor.fetchone()
    return row[0] if row else None


def _rows(connection, sql: str) -> list[tuple]:
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return list(cursor.fetchall()) if cursor.description else []


# --------------------------------------------------------------------------
# Phase 1 -- Preflight
# --------------------------------------------------------------------------


def _preflight(connection) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    facts: dict[str, Any] = {}

    facts["server_version"] = _scalar(connection, "SHOW server_version")
    facts["current_user"] = _scalar(connection, "SELECT current_user")
    facts["current_database"] = _scalar(connection, "SELECT current_database()")
    facts["timezone"] = _scalar(connection, "SHOW TimeZone")
    facts["is_superuser"] = _scalar(
        connection, "SELECT usesuper FROM pg_user WHERE usename = current_user"
    )
    facts["ssl_in_use"] = _scalar(
        connection, "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()"
    )
    checks.append(_check("connection", True, detail="reachable"))

    # SSL ist Projektvorgabe fuer oeffentlich erreichbare Instanzen.
    checks.append(
        _check(
            "transport_encryption",
            bool(facts["ssl_in_use"]),
            detail="server refuses TLS" if not facts["ssl_in_use"] else "TLS active",
        )
    )

    checks.append(
        _check("timezone_utc", facts["timezone"] == "UTC",
               detail=str(facts["timezone"]), blocking=False)
    )

    # pgvector
    version = _scalar(connection, "SELECT extversion FROM pg_extension WHERE extname = 'vector'")
    facts["pgvector_version"] = version
    checks.append(_check("pgvector_installed", version is not None, detail=str(version)))

    methods = [row[0] for row in _rows(connection, "SELECT amname FROM pg_am")]
    facts["index_methods"] = sorted(methods)
    checks.append(_check("hnsw_available", "hnsw" in methods))

    # Rechte -- ohne CREATE SCHEMA ist Phase 2 nicht durchfuehrbar.
    can_create = _scalar(
        connection,
        "SELECT has_database_privilege(current_user, current_database(), 'CREATE')",
    )
    facts["can_create_schema"] = bool(can_create)
    checks.append(_check("privilege_create_schema", bool(can_create)))

    # Migrationsstand -- fehlende Tabelle ist kein Fehler, nur ein Zustand.
    try:
        applied = _rows(connection, "SELECT version FROM schema_migrations ORDER BY applied_at")
        facts["applied_migrations"] = [row[0] for row in applied]
    except Exception:
        facts["applied_migrations"] = None
    checks.append(
        _check("migration_state_readable", True,
               detail="fresh database" if facts["applied_migrations"] is None else "present",
               blocking=False)
    )

    return checks, facts


# --------------------------------------------------------------------------
# Phase 2 -- isolierte Testumgebung
# --------------------------------------------------------------------------


@contextmanager
def isolated_schema(connection, *, name: str | None = None):
    """Eigenes Schema je Lauf. Wird immer entfernt, auch bei Fehlern."""
    schema = name or f"{SCHEMA_PREFIX}_{uuid4().hex[:12]}"
    created = False
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA {schema}")
        created = True
        yield schema
    finally:
        if created:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")


def _schema_checks(connection, schema: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    facts: dict[str, Any] = {}

    with connection.cursor() as cursor:
        cursor.execute(f"CREATE TABLE {schema}.probe (id int primary key, note text)")
        cursor.execute(f"INSERT INTO {schema}.probe VALUES (1, 'gate')")
        cursor.execute(f"SELECT count(*) FROM {schema}.probe")
        written = cursor.fetchone()[0]
    checks.append(_check("isolated_write", written == 1))

    # pgvector in der Projektdimension: Speicherung und Indizierbarkeit.
    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cursor.execute(
            f"CREATE TABLE {schema}.vec (id int, e vector({PROJECT_DIMENSIONS}))"
        )
    checks.append(_check("vector_column_project_dimension", True))

    direct_ok = _try(
        connection,
        f"CREATE INDEX ON {schema}.vec USING hnsw (e vector_cosine_ops)",
    )
    facts["direct_vector_index_supported"] = direct_ok
    # Ueber 2000 Dimensionen MUSS der direkte Index scheitern. Gelingt er
    # trotzdem, stimmt unsere Annahme ueber die pgvector-Version nicht.
    expected_direct = PROJECT_DIMENSIONS <= MAX_VECTOR_INDEX_DIMENSIONS
    checks.append(
        _check("vector_index_limit_as_documented", direct_ok is expected_direct,
               detail=f"direct index supported={direct_ok}, expected={expected_direct}")
    )

    halfvec_ok = _try(
        connection,
        f"CREATE INDEX ON {schema}.vec "
        f"USING hnsw ((e::halfvec({PROJECT_DIMENSIONS})) halfvec_cosine_ops)",
    )
    facts["halfvec_index_supported"] = halfvec_ok
    checks.append(_check("halfvec_index_creatable", halfvec_ok))

    return checks, facts


# --------------------------------------------------------------------------
# Phase 6 -- Vektorsuche
# --------------------------------------------------------------------------


def golden_vector(index: int, dimensions: int = PROJECT_DIMENSIONS) -> list[float]:
    """Deterministischer Einheitsvektor: Achse ``index`` traegt 1.0.

    Damit ist die erwartete Rangfolge einer Cosine-Suche analytisch bekannt und
    muss nicht aus einem Referenzlauf abgeleitet werden.
    """
    vector = [0.0] * dimensions
    vector[index % dimensions] = 1.0
    return vector


def _literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in vector) + "]"


def _vector_search_checks(connection, schema: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    facts: dict[str, Any] = {}
    table = f"{schema}.golden"
    cast = f"halfvec({PROJECT_DIMENSIONS})"

    with connection.cursor() as cursor:
        cursor.execute(
            f"CREATE TABLE {table} (id int primary key, e vector({PROJECT_DIMENSIONS}))"
        )
        for i in range(GOLDEN_ROWS):
            cursor.execute(
                f"INSERT INTO {table} (id, e) VALUES (%s, %s::vector)",
                (i, _literal(golden_vector(i))),
            )
        cursor.execute(
            f"CREATE INDEX golden_hnsw ON {table} "
            f"USING hnsw ((e::{cast}) halfvec_cosine_ops)"
        )
        cursor.execute(f"ANALYZE {table}")

    # -- Trefferqualitaet -------------------------------------------------
    probe = 0
    query = _literal(golden_vector(probe))
    order_by = f"e::{cast} <=> %s::{cast}"
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT id FROM {table} ORDER BY {order_by} LIMIT %s",
            (query, GOLDEN_TOP_K),
        )
        hits = [row[0] for row in cursor.fetchall()]

    facts["search_top_k"] = hits
    checks.append(
        _check("vector_search_returns_results", len(hits) == GOLDEN_TOP_K,
               detail=f"{len(hits)} of {GOLDEN_TOP_K}")
    )
    checks.append(
        _check("vector_search_exact_match_first", bool(hits) and hits[0] == probe,
               detail=f"expected {probe}, got {hits[0] if hits else None}")
    )

    # Recall gegen die analytisch bekannte Erwartung: der Anfragevektor ist
    # orthogonal zu allen anderen, also ist nur der Treffer selbst relevant.
    relevant = {probe}
    recall = len(relevant & set(hits)) / len(relevant)
    facts["recall"] = recall
    checks.append(
        _check("vector_search_min_recall", recall >= MIN_RECALL,
               detail=f"{recall:.2f} >= {MIN_RECALL}")
    )

    # -- Indexnutzung -----------------------------------------------------
    # Kernpruefung. Ein Ausdrucksindex wird nur genutzt, wenn die Abfrage
    # denselben Ausdruck traegt. Weicht sie ab, existiert der Index und jede
    # Suche degradiert still zum Sequential Scan.
    usable, plan = _index_usable(connection, table, order_by, query)
    facts["index_scan_plan"] = plan
    checks.append(
        _check("vector_index_used_by_query", usable,
               detail="query expression cannot use the halfvec index" if not usable else plan)
    )

    # -- Dimension Guard --------------------------------------------------
    wrong = _try(
        connection,
        f"INSERT INTO {table} (id, e) VALUES (9001, '{_literal([0.1, 0.2, 0.3])}'::vector)",
    )
    checks.append(
        _check("dimension_guard_rejects_mismatch", wrong is False,
               detail="a 3-dimensional vector was accepted" if wrong else "rejected")
    )

    # -- Reindex ----------------------------------------------------------
    reindexed = _try(connection, f"REINDEX INDEX {schema}.golden_hnsw")
    checks.append(_check("reindex", reindexed))
    if reindexed:
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT id FROM {table} ORDER BY {order_by} LIMIT 1", (query,)
            )
            row = cursor.fetchone()
        checks.append(
            _check("search_after_reindex", bool(row) and row[0] == probe)
        )

    return checks, facts


# --------------------------------------------------------------------------
# Phase 4 -- Workspace-Isolation per Row Level Security
# --------------------------------------------------------------------------


def _workspace_isolation_checks(connector: Callable[[str], Any], dsn: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Weist nach, dass RLS Workspaces auch gegen direkten SQL-Zugriff trennt.

    Committet, mit eigener Verbindung und eigenem Schema. Genau das ist die
    Anforderung aus Prompt 68 Phase 4: ein Raw-SQL-Bypass darf Workspaces nicht
    ueberschreiten.
    """
    from secondbrain.storage.workspace_context import (
        rls_setup_statements,
        set_workspace_sql,
    )

    checks: list[dict[str, Any]] = []
    facts: dict[str, Any] = {}

    schema = f"{SCHEMA_PREFIX}_rls_{uuid4().hex[:10]}"
    table = f"{schema}.records"
    setup = connector(dsn)
    setup.autocommit = True

    try:
        with setup.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA {schema}")
            cursor.execute(
                f"CREATE TABLE {table} (id int primary key, workspace_id text NOT NULL, data text)"
            )
            for statement in rls_setup_statements(table):
                cursor.execute(statement)

        # -- Schreiben unter ws-a, dann ws-b -------------------------------
        with setup.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(set_workspace_sql("ws-a"))
            cursor.execute(f"INSERT INTO {table} (id, workspace_id, data) VALUES (1, 'ws-a', 'a')")
            cursor.execute("COMMIT")
        with setup.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(set_workspace_sql("ws-b"))
            cursor.execute(f"INSERT INTO {table} (id, workspace_id, data) VALUES (2, 'ws-b', 'b')")
            cursor.execute("COMMIT")

        # -- ws-a sieht nur die eigene Zeile -------------------------------
        with setup.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(set_workspace_sql("ws-a"))
            cursor.execute(f"SELECT id FROM {table}")
            visible_a = sorted(row[0] for row in cursor.fetchall())
            cursor.execute("COMMIT")
        facts["visible_to_ws_a"] = visible_a
        checks.append(
            _check("rls_read_isolation", visible_a == [1],
                   detail=f"ws-a sees {visible_a}, expected [1]")
        )

        # -- Ohne gesetzten Workspace: nichts sichtbar (fail-closed) -------
        with setup.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(f"SELECT count(*) FROM {table}")
            without_context = cursor.fetchone()[0]
            cursor.execute("COMMIT")
        checks.append(
            _check("rls_fail_closed_without_context", without_context == 0,
                   detail=f"{without_context} rows visible without workspace context")
        )

        # -- Cross-Workspace-Schreibversuch muss scheitern -----------------
        blocked = _write_rejected_under_context(setup, table, workspace="ws-b", foreign_id=3, foreign_ws="ws-a")
        checks.append(
            _check("rls_write_check_blocks_cross_workspace", blocked,
                   detail="WITH CHECK did not reject a foreign-workspace insert" if not blocked else "rejected")
        )

        # -- ws-a kann die Zeile von ws-b nicht aktualisieren --------------
        with setup.cursor() as cursor:
            cursor.execute("BEGIN")
            cursor.execute(set_workspace_sql("ws-a"))
            cursor.execute(f"UPDATE {table} SET data = 'hijack' WHERE id = 2")
            affected = cursor.rowcount
            cursor.execute("COMMIT")
        checks.append(
            _check("rls_update_cannot_reach_other_workspace", affected == 0,
                   detail=f"update affected {affected} foreign rows, expected 0")
        )

    except Exception as exc:  # noqa: BLE001
        checks.append(_check("workspace_isolation", False, detail=type(exc).__name__))
    finally:
        try:
            setup.autocommit = True
            with setup.cursor() as cursor:
                cursor.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
            facts["cleanup_schema_dropped"] = True
        except Exception:  # noqa: BLE001
            facts["cleanup_schema_dropped"] = False
        finally:
            try:
                setup.close()
            except Exception:  # noqa: BLE001
                pass

    return checks, facts


def _write_rejected_under_context(connection, table: str, *, workspace: str, foreign_id: int, foreign_ws: str) -> bool:
    """True, wenn ein Insert mit fremdem workspace_id von WITH CHECK abgewiesen wird."""
    from secondbrain.storage.workspace_context import set_workspace_sql

    with connection.cursor() as cursor:
        cursor.execute("BEGIN")
        cursor.execute(set_workspace_sql(workspace))
        try:
            cursor.execute(
                f"INSERT INTO {table} (id, workspace_id, data) VALUES (%s, %s, 'x')",
                (foreign_id, foreign_ws),
            )
            cursor.execute("COMMIT")
            return False
        except Exception:
            cursor.execute("ROLLBACK")
            return True


# --------------------------------------------------------------------------
# Phase 3 -- Repository-Vertraege gegen die produktiven Repository-Klassen
# --------------------------------------------------------------------------


def _contract(name: str, fn: Callable[[], tuple[bool, str]]) -> dict[str, Any]:
    """Fuehrt einen Contract aus und misst die Dauer.

    Ergebnis: PASS/FAIL/SKIPPED, Dauer in ms und -- im Fehlerfall -- nur die
    Fehlerklasse. Niemals str(exc): dort koennten DSN-Fragmente stehen.
    """
    start = time.perf_counter()
    try:
        ok, detail = fn()
        status = "PASS" if ok else "FAIL"
    except _ContractSkip as skip:
        ok, status, detail = True, "SKIPPED", str(skip)
        return {"name": name, "ok": True, "contract_status": status, "detail": detail,
                "duration_ms": round((time.perf_counter() - start) * 1000, 1), "blocking": False}
    except Exception as exc:  # noqa: BLE001 - Fehlerklasse redigiert
        ok, status, detail = False, "FAIL", type(exc).__name__
    return {"name": name, "ok": ok, "contract_status": status, "detail": detail,
            "duration_ms": round((time.perf_counter() - start) * 1000, 1), "blocking": True}


class _ContractSkip(RuntimeError):
    """Ein Contract ist gegen die produktive Klasse nicht anwendbar."""


def _repository_contracts_checks(
    connector: Callable[[str], Any],
    dsn: str,
    *,
    contracts_impl: Callable[[Callable[[str], Any], str, str], list[dict[str, Any]]] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Isoliertes Schema anlegen, produktive Repository-Contracts fahren, aufraeumen.

    ``contracts_impl`` ist injizierbar, damit der Kontrollfluss (Anlegen,
    Aufraeumen im Fehlerfall, Aggregation) ohne Datenbank pruefbar ist. Die
    Standardimplementierung nutzt ``PostgresTaskRepository`` -- keine parallele
    Testimplementierung.
    """
    checks: list[dict[str, Any]] = []
    facts: dict[str, Any] = {}

    schema = f"{SCHEMA_PREFIX}_repo_{uuid4().hex[:10]}"
    setup = connector(dsn)
    setup.autocommit = True

    try:
        with setup.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA {schema}")
        impl = contracts_impl or _default_repository_contracts
        checks.extend(impl(connector, dsn, schema))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("repository_contracts", False, detail=type(exc).__name__))
    finally:
        try:
            setup.autocommit = True
            with setup.cursor() as cursor:
                cursor.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
            facts["cleanup_schema_dropped"] = True
        except Exception:  # noqa: BLE001
            facts["cleanup_schema_dropped"] = False
        finally:
            try:
                setup.close()
            except Exception:  # noqa: BLE001
                pass

    return checks, facts


def _default_repository_contracts(connector: Callable[[str], Any], dsn: str, schema: str) -> list[dict[str, Any]]:  # pragma: no cover - benoetigt PostgreSQL
    """Fuehrt die Contracts gegen das echte PostgresTaskRepository im Testschema."""
    from secondbrain.release.approval_postgres_live_gate import PsycopgExecutor
    from secondbrain.tasks.repository import (
        PostgresTaskRepository,
        TaskRepositoryConflict,
        TaskRepositoryError,
        migrate_jsonl_to_repository,
    )

    work = connector(dsn)
    checks: list[dict[str, Any]] = []
    try:
        # search_path committen, damit task_project_records im Testschema landet.
        work.autocommit = True
        with work.cursor() as cursor:
            cursor.execute(f"SET search_path TO {schema}, public")
        work.autocommit = False

        executor = PsycopgExecutor(work)
        repo = PostgresTaskRepository(executor, require_workspace=True)
        repo.ensure_schema()

        def _project(pid: str, ws: str, *, title: str = "P", version: int = 1) -> dict[str, Any]:
            return {"project_id": pid, "workspace_id": ws, "title": title, "version": version}

        def _task(tid: str, ws: str, *, title: str = "T", version: int = 1) -> dict[str, Any]:
            return {"task_id": tid, "workspace_id": ws, "title": title, "version": version}

        # 1 -- CRUD
        def crud() -> tuple[bool, str]:
            repo.write("projects", [_project("p1", _RC_WS_A)], workspace_id=_RC_WS_A)
            repo.write("tasks", [_task("t1", _RC_WS_A)], workspace_id=_RC_WS_A)
            got = {r["project_id"] for r in repo.read("projects", workspace_id=_RC_WS_A)}
            repo.write("projects", [_project("p1", _RC_WS_A, title="P2", version=2)], workspace_id=_RC_WS_A)
            updated = repo.read("projects", workspace_id=_RC_WS_A)[0]["title"]
            repo.write("tasks", [], workspace_id=_RC_WS_A)
            tasks_after = repo.read("tasks", workspace_id=_RC_WS_A)
            return (got == {"p1"} and updated == "P2" and tasks_after == []), "crud"
        checks.append(_contract("repo_crud", crud))

        # 2 -- optimistische Versionspruefung
        def optimistic() -> tuple[bool, str]:
            repo.write("projects", [_project("p2", _RC_WS_A)], workspace_id=_RC_WS_A)
            try:
                repo.write("projects", [_project("p2", _RC_WS_A, title="stale", version=1)], workspace_id=_RC_WS_A)
            except TaskRepositoryConflict:
                return True, "stale write rejected"
            return False, "stale write was accepted"
        checks.append(_contract("repo_optimistic_version", optimistic))

        # 3 -- idempotente Wiederholung
        def idempotent() -> tuple[bool, str]:
            repo.write("projects", [_project("p3", _RC_WS_A)], workspace_id=_RC_WS_A)
            repo.write("projects", [_project("p3", _RC_WS_A)], workspace_id=_RC_WS_A)
            hits = [r for r in repo.read("projects", workspace_id=_RC_WS_A) if r["project_id"] == "p3"]
            return len(hits) == 1, "identical rewrite is a no-op"
        checks.append(_contract("repo_idempotent_repeat", idempotent))

        # 4 -- Konflikt bei nicht-fortlaufender Version
        def version_conflict() -> tuple[bool, str]:
            repo.write("projects", [_project("p4", _RC_WS_A)], workspace_id=_RC_WS_A)
            try:
                repo.write("projects", [_project("p4", _RC_WS_A, title="jump", version=5)], workspace_id=_RC_WS_A)
            except TaskRepositoryConflict:
                return True, "non-sequential version rejected"
            return False, "version jump accepted"
        checks.append(_contract("repo_version_conflict", version_conflict))

        # 5 -- Workspace-Isolation ueber Repository-Methoden
        def isolation() -> tuple[bool, str]:
            repo.write("projects", [_project("pa", _RC_WS_A)], workspace_id=_RC_WS_A)
            repo.write("projects", [_project("pb", _RC_WS_B)], workspace_id=_RC_WS_B)
            a = {r["project_id"] for r in repo.read("projects", workspace_id=_RC_WS_A)}
            b = {r["project_id"] for r in repo.read("projects", workspace_id=_RC_WS_B)}
            return ("pb" not in a and "pa" not in b and "pa" in a and "pb" in b), "scoped reads isolated"
        checks.append(_contract("repo_workspace_isolation", isolation))

        # 6 -- Cross-Workspace Read/Update/Delete verhindert
        def cross_workspace() -> tuple[bool, str]:
            # Fremde Zeile im Schreibsatz -> abgewiesen.
            try:
                repo.write("projects", [_project("pc", _RC_WS_B)], workspace_id=_RC_WS_A)
                return False, "cross-workspace write accepted"
            except TaskRepositoryError:
                pass
            # Scoped Delete von ws-a laesst pb (ws-b) unberuehrt.
            repo.write("projects", [], workspace_id=_RC_WS_A)
            b = {r["project_id"] for r in repo.read("projects", workspace_id=_RC_WS_B)}
            return "pb" in b, "foreign rows untouched by scoped delete"
        checks.append(_contract("repo_cross_workspace_prevented", cross_workspace))

        # 7 -- Transaktions-Rollback nach absichtlichem Fehler
        def rollback() -> tuple[bool, str]:
            repo.write("projects", [_project("p7", _RC_WS_A)], workspace_id=_RC_WS_A)
            # Batch: neue Zeile zuerst, dann veraltete Version -> Konflikt mitten drin.
            batch = [_project("p7new", _RC_WS_A), _project("p7", _RC_WS_A, title="x", version=1)]
            try:
                repo.write("projects", batch, workspace_id=_RC_WS_A)
            except TaskRepositoryConflict:
                pass
            present = {r["project_id"] for r in repo.read("projects", workspace_id=_RC_WS_A)}
            return "p7new" not in present, "partial batch rolled back"
        checks.append(_contract("repo_transaction_rollback", rollback))

        # 8 -- JSONL-Migration in das isolierte Schema mit Mengen-/Feldvergleich
        def migration() -> tuple[bool, str]:
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                tdir = Path(tmp) / "runtime" / "tasks"
                tdir.mkdir(parents=True)
                rows = [
                    {"project_id": "m1", "workspace_id": _RC_WS_A, "title": "M1", "version": 1},
                    {"project_id": "m2", "workspace_id": _RC_WS_B, "title": "M2", "version": 1},
                ]
                (tdir / "projects.jsonl").write_text(
                    "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
                report = migrate_jsonl_to_repository(tmp, repo, dry_run=False)
                migrated_a = repo.read("projects", workspace_id=_RC_WS_A)
                migrated_b = repo.read("projects", workspace_id=_RC_WS_B)
                count_ok = report["collections"]["projects"]["valid"] == 2
                m1 = next((r for r in migrated_a if r["project_id"] == "m1"), None)
                field_ok = m1 is not None and m1["title"] == "M1"
                set_ok = any(r["project_id"] == "m2" for r in migrated_b)
            return (count_ok and field_ok and set_ok), "counts and fields match"
        checks.append(_contract("repo_jsonl_migration", migration))

        # 9 -- UTC-Zeitstempel und Serialisierungs-Roundtrip
        def serialization() -> tuple[bool, str]:
            payload = {
                "project_id": "p9", "workspace_id": _RC_WS_A, "title": "ünïcode ✓",
                "version": 1, "created_at": "2026-07-22T00:00:00Z",
                "nested": {"k": [1, 2, 3], "flag": True},
            }
            repo.write("projects", [payload], workspace_id=_RC_WS_A)
            back = next(r for r in repo.read("projects", workspace_id=_RC_WS_A) if r["project_id"] == "p9")
            utc_ok = back.get("created_at", "").endswith("Z")
            roundtrip_ok = back["title"] == payload["title"] and back["nested"] == payload["nested"]
            return (utc_ok and roundtrip_ok), "utc timestamp and nested payload preserved"
        checks.append(_contract("repo_utc_serialization", serialization))

        return checks
    finally:
        try:
            work.rollback()
        except Exception:  # noqa: BLE001
            pass
        try:
            work.close()
        except Exception:  # noqa: BLE001
            pass


# --------------------------------------------------------------------------
# Phase 5 -- Concurrency
# --------------------------------------------------------------------------


def _concurrency_checks(connector: Callable[[str], Any], dsn: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Zwei echte Sessions gegen dieselbe Tabelle.

    Anders als die uebrigen Phasen laeuft das committet: ``FOR UPDATE SKIP
    LOCKED`` ist ohne eine zweite, die Zeilen sehende Session nicht pruefbar.
    Das Schema wird deshalb eigenstaendig verwaltet und im ``finally`` entfernt.
    """
    checks: list[dict[str, Any]] = []
    facts: dict[str, Any] = {}

    schema = f"{SCHEMA_PREFIX}_conc_{uuid4().hex[:10]}"
    table = f"{schema}.queue"
    setup = connector(dsn)
    setup.autocommit = True
    worker_a = None
    worker_b = None

    try:
        with setup.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA {schema}")
            cursor.execute(
                f"CREATE TABLE {table} ("
                "  id int primary key,"
                "  idempotency_key text UNIQUE,"
                "  version int NOT NULL DEFAULT 1,"
                "  claimed_by text"
                ")"
            )
            for i in (1, 2):
                cursor.execute(
                    f"INSERT INTO {table} (id, idempotency_key) VALUES (%s, %s)",
                    (i, f"key-{i}"),
                )

        # -- Idempotenz: doppelter Schluessel muss abgewiesen werden -------
        duplicate = _try(
            setup,
            f"INSERT INTO {table} (id, idempotency_key) VALUES (99, 'key-1')",
        )
        checks.append(
            _check("idempotency_key_unique", duplicate is False,
                   detail="duplicate key accepted" if duplicate else "rejected")
        )

        # -- Claiming ohne Doppelvergabe -----------------------------------
        worker_a = connector(dsn)
        worker_b = connector(dsn)
        worker_a.autocommit = False
        worker_b.autocommit = False

        claim = (
            f"SELECT id FROM {table} WHERE claimed_by IS NULL "
            "ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1"
        )
        with worker_a.cursor() as cursor:
            cursor.execute(claim)
            row_a = cursor.fetchone()
        with worker_b.cursor() as cursor:
            cursor.execute(claim)
            row_b = cursor.fetchone()

        claimed_a = row_a[0] if row_a else None
        claimed_b = row_b[0] if row_b else None
        facts["claimed"] = [claimed_a, claimed_b]

        checks.append(_check("skip_locked_both_workers_get_work",
                             claimed_a is not None and claimed_b is not None))
        checks.append(
            _check("skip_locked_no_double_claim", claimed_a != claimed_b,
                   detail=f"worker_a={claimed_a}, worker_b={claimed_b}")
        )

        worker_a.rollback()
        worker_b.rollback()

        # -- Optimistische Versionierung ------------------------------------
        # Beide Sessions aktualisieren dieselbe Zeile mit derselben erwarteten
        # Version. Genau eine darf zum Zug kommen.
        update = f"UPDATE {table} SET version = version + 1 WHERE id = 1 AND version = %s"
        with worker_a.cursor() as cursor:
            cursor.execute(update, (1,))
            first = int(cursor.rowcount)
        worker_a.commit()
        with worker_b.cursor() as cursor:
            cursor.execute(update, (1,))
            second = int(cursor.rowcount)
        worker_b.commit()

        facts["optimistic_update_rowcounts"] = [first, second]
        checks.append(
            _check("optimistic_versioning_blocks_stale_write", second == 0,
                   detail=f"second update affected {second} rows, expected 0")
        )

    except Exception as exc:  # noqa: BLE001
        checks.append(_check("concurrency", False, detail=type(exc).__name__))
    finally:
        for connection in (worker_a, worker_b):
            if connection is not None:
                try:
                    connection.rollback()
                    connection.close()
                except Exception:  # noqa: BLE001
                    pass
        try:
            setup.autocommit = True
            with setup.cursor() as cursor:
                cursor.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
            facts["cleanup_schema_dropped"] = True
        except Exception:  # noqa: BLE001
            facts["cleanup_schema_dropped"] = False
        finally:
            try:
                setup.close()
            except Exception:  # noqa: BLE001
                pass

    return checks, facts


def _index_usable(connection, table: str, order_by: str, query: str) -> tuple[bool, str]:
    """Kann die Abfrage den Vektorindex nutzen?

    Bei kleinen Tabellen waehlt der Planner legitim einen Sequential Scan. Die
    kritische Eigenschaft ist nicht seine Wahl, sondern ob der Index ueberhaupt
    in Frage kommt. Deshalb wird der Seq Scan testweise abgeschaltet: bleibt es
    dann immer noch beim Seq Scan, passt der Abfrageausdruck nicht zum Index.
    """
    statement = f"EXPLAIN SELECT id FROM {table} ORDER BY {order_by} LIMIT 5"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL enable_seqscan = off")
            cursor.execute(statement, (query,))
            plan = " ".join(str(row[0]) for row in cursor.fetchall())
    except Exception:  # noqa: BLE001
        return False, "explain failed"
    return ("Index Scan" in plan or "Index Only Scan" in plan), plan[:200]


def _try(connection, statement: str) -> bool:
    """Fuehrt ``statement`` in einem SAVEPOINT aus und meldet nur Erfolg."""
    savepoint = f"sp_{uuid4().hex[:8]}"
    with connection.cursor() as cursor:
        cursor.execute(f"SAVEPOINT {savepoint}")
        try:
            cursor.execute(statement)
        except Exception:
            cursor.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            return False
        cursor.execute(f"RELEASE SAVEPOINT {savepoint}")
        return True


# --------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------


def run_postgres_live_gate(
    project_root: str | Path = ".",
    *,
    env: dict[str, str] | None = None,
    connect: Callable[[str], Any] | None = None,
    repository_contracts_impl: Callable[[Callable[[str], Any], str, str], list[dict[str, Any]]] | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    dsn = (values.get("TEST_DATABASE_URL") or "").strip()

    report: dict[str, Any] = {
        "gate": "postgres_live_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "implemented_phases": [
                "preflight", "isolated_schema", "repository_contracts",
                "workspace_isolation", "concurrency", "vector_search_recall", "report",
            ],
            "not_implemented_phases": list(NOT_IMPLEMENTED_PHASES),
        },
        "checks": [],
        "facts": {},
        "cleanup": {"schema_dropped": None},
    }

    if not dsn:
        report["status"] = BLOCKED
        report["ok"] = False
        report["blockers"] = ["TEST_DATABASE_URL is not set"]
        return _finalize(report, project_root, write_report)

    try:
        _validate_dsn(dsn)
    except ValueError as exc:
        report["status"] = BLOCKED
        report["ok"] = False
        report["blockers"] = [str(exc)]
        return _finalize(report, project_root, write_report)

    report["target"] = _fingerprint(dsn)
    connector = connect or _default_connect

    connection = None
    try:
        connection = connector(dsn)
        connection.autocommit = True

        checks, facts = _preflight(connection)
        report["checks"].extend(checks)
        report["facts"].update(facts)

        if facts.get("can_create_schema"):
            connection.autocommit = False
            schema_name = None
            try:
                with isolated_schema(connection) as schema:
                    schema_name = schema
                    schema_checks, schema_facts = _schema_checks(connection, schema)
                    report["checks"].extend(schema_checks)
                    report["facts"].update(schema_facts)

                    # Phase 6 setzt einen anlegbaren halfvec-Index voraus.
                    if schema_facts.get("halfvec_index_supported"):
                        search_checks, search_facts = _vector_search_checks(connection, schema)
                        report["checks"].extend(search_checks)
                        report["facts"].update(search_facts)
                    else:
                        report["checks"].append(
                            _check("vector_search", False,
                                   detail="skipped: no usable vector index")
                        )
                report["cleanup"]["schema_dropped"] = True
            except Exception as exc:  # noqa: BLE001
                report["checks"].append(
                    _check("isolated_schema", False, detail=type(exc).__name__)
                )
                report["cleanup"]["schema_dropped"] = schema_name is None
            finally:
                connection.rollback()
                connection.autocommit = True
            # Phase 3, 4 und 5 laufen committet und benoetigen eigene Verbindungen.
            repo_checks, repo_facts = _repository_contracts_checks(
                connector, dsn, contracts_impl=repository_contracts_impl)
            report["checks"].extend(repo_checks)
            report["facts"]["repository_contracts"] = repo_facts
            if repo_facts.get("cleanup_schema_dropped") is False:
                report["cleanup"]["repository_contracts_schema_dropped"] = False

            iso_checks, iso_facts = _workspace_isolation_checks(connector, dsn)
            report["checks"].extend(iso_checks)
            report["facts"]["workspace_isolation"] = iso_facts
            if iso_facts.get("cleanup_schema_dropped") is False:
                report["cleanup"]["workspace_isolation_schema_dropped"] = False

            conc_checks, conc_facts = _concurrency_checks(connector, dsn)
            report["checks"].extend(conc_checks)
            report["facts"].update(conc_facts)
            if conc_facts.get("cleanup_schema_dropped") is False:
                report["cleanup"]["concurrency_schema_dropped"] = False
        else:
            report["checks"].append(
                _check("isolated_schema", False, detail="CREATE privilege missing")
            )

    except Exception as exc:  # noqa: BLE001
        report["checks"].append(_check("connection", False, detail=type(exc).__name__))
        report["error"] = _safe_error(exc)
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:  # noqa: BLE001
                pass

    blocking_failures = [c["name"] for c in report["checks"] if c["blocking"] and not c["ok"]]
    warnings = [c["name"] for c in report["checks"] if not c["blocking"] and not c["ok"]]

    report["blockers"] = blocking_failures
    report["warnings"] = warnings
    if blocking_failures:
        report["status"] = BLOCKED
    elif warnings or NOT_IMPLEMENTED_PHASES:
        # Teilumfang kann nie PASS bedeuten.
        report["status"] = CONDITIONAL_PASS
    else:
        report["status"] = PASS
    report["ok"] = report["status"] != BLOCKED

    return _finalize(report, project_root, write_report)


def _finalize(report: dict[str, Any], project_root: str | Path, write_report: bool) -> dict[str, Any]:
    report.setdefault("warnings", [])
    report.setdefault("blockers", [])
    if write_report:
        target = Path(project_root) / REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["report"] = REPORT_PATH.as_posix()
    return report
