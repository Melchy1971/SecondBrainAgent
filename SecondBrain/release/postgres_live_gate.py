"""PostgreSQL- und pgvector-Live-Gate (Prompt 68, Phase 1, 2 und 8).

Umfang dieser Stufe
-------------------
Phase 1  Preflight: Treiber, Verbindung, Version, SSL, Rechte, Zeitzone,
         Migrationsstand, pgvector-Extension und Indexfaehigkeit.
Phase 2  Isolierte Testumgebung: eigenes Schema je Lauf, Aufraeumen im
         ``finally``-Block, niemals Zugriff auf produktive Tabellen.
Phase 8  Redigierter Report.

Die Phasen 3 bis 7 (Repository-, Isolations-, Concurrency- und
Vektor-Suchtests) folgen als eigene Pakete. Der Report weist sie als
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

NOT_IMPLEMENTED_PHASES = (
    "repository_contracts",
    "workspace_isolation",
    "concurrency",
    "vector_search_recall",
)


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
    write_report: bool = True,
) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    dsn = (values.get("TEST_DATABASE_URL") or "").strip()

    report: dict[str, Any] = {
        "gate": "postgres_live_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "implemented_phases": ["preflight", "isolated_schema", "report"],
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
                report["cleanup"]["schema_dropped"] = True
            except Exception as exc:  # noqa: BLE001
                report["checks"].append(
                    _check("isolated_schema", False, detail=type(exc).__name__)
                )
                report["cleanup"]["schema_dropped"] = schema_name is None
            finally:
                connection.rollback()
                connection.autocommit = True
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
