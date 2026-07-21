"""Read-only Preflight-Sonde fuer das PostgreSQL-/pgvector-Live-Gate (Prompt 68).

Zweck: Fakten ueber die Testumgebung erheben, BEVOR das Gate implementiert wird.

Sicherheit:
  * Liest ausschliesslich TEST_DATABASE_URL aus der Umgebung.
  * Gibt niemals DSN, Passwort, Host oder Port aus.
  * Schreibt nichts dauerhaft. Der einzige Schreibtest laeuft in einer
    Transaktion, die immer zurueckgerollt wird.

Aufruf:
    $env:TEST_DATABASE_URL = "postgresql://..."
    python OUTPUTS\\v31.91-postgres-preflight\\preflight_probe.py

Die Ausgabe ist redigiertes JSON und kann unveraendert weitergegeben werden.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from typing import Any
from urllib.parse import urlparse

PROBE_SCHEMA = "sb_preflight_probe"
HNSW_DIMENSION_LIMIT = 2000  # pgvector: hnsw/ivfflat indizieren max. 2000 Dimensionen
PROJECT_EMBEDDING_DIMENSION = 3072  # aus storage/migrations/002_pgvector_embeddings.sql


def _clean(raw: str) -> str:
    """Entfernt Whitespace und versehentlich mituebernommene Anfuehrungszeichen."""
    value = raw.strip()
    for quote in ('"', "'"):
        if len(value) >= 2 and value.startswith(quote) and value.endswith(quote):
            value = value[1:-1].strip()
    return value


def placeholder_reason(dsn: str) -> str | None:
    """Erkennt nicht ersetzte Platzhalter, bevor sie als Netzwerkfehler erscheinen."""
    cleaned = _clean(dsn)
    lowered = cleaned.lower()

    if cleaned in {"postgresql://...", "postgres://...", "postgresql://", "postgres://"}:
        return "Die DSN ist der unveraenderte Beispiel-Platzhalter."

    try:
        host = urlparse(cleaned).hostname or ""
    except Exception:  # noqa: BLE001
        host = ""

    if host and set(host) <= {"."}:
        return f"Der Host besteht nur aus Punkten ({host!r}) - Platzhalter nicht ersetzt."
    if host in {"host", "hostname", "your-host", "dein-host", "example.com", "<host>"}:
        return f"Der Host ist ein Platzhalter ({host!r})."
    for token in ("<user>", "<password>", "<host>", "<db>", "username:password", "user:pass",
                  "benutzer:passwort"):
        if token in lowered:
            return f"Die DSN enthaelt den Platzhalter {token!r}."
    return None


def credential_shape_reason(dsn: str) -> str | None:
    """Erkennt vertauschte oder unvollstaendige Zugangsdaten vor dem Verbindungsversuch."""
    try:
        parsed = urlparse(_clean(dsn))
    except Exception:  # noqa: BLE001
        return None

    user = parsed.username
    password = parsed.password

    if user and password is None:
        return (
            "Die DSN enthaelt einen Benutzer, aber kein Passwort. "
            "Erwartet wird 'postgresql://BENUTZER:PASSWORT@host:5432/datenbank' - "
            "steht der Wert vor dem '@' ohne Doppelpunkt, liest libpq ihn als Benutzernamen."
        )
    if password and not user:
        return "Die DSN enthaelt ein Passwort, aber keinen Benutzer."
    if not user and not password:
        return "Die DSN enthaelt weder Benutzer noch Passwort."
    return None


def diagnose_dsn(raw: str) -> dict[str, Any]:
    """Zerlegt die DSN redigiert. Gibt niemals das Passwort aus."""
    cleaned = _clean(raw)
    placeholder = placeholder_reason(cleaned)
    if placeholder:
        return {
            "placeholder_detected": True,
            "reason": placeholder,
            "raw_length": len(raw),
            "starts_with": cleaned[:11],
            "hint": "TEST_DATABASE_URL mit der echten Verbindungszeichenkette setzen.",
        }
    info: dict[str, Any] = {
        "raw_length": len(raw),
        "cleaned_length": len(cleaned),
        "had_surrounding_quotes": cleaned != raw.strip(),
        "had_whitespace": raw != raw.strip(),
        "starts_with": cleaned[:11] if cleaned else "",
        "format": "uri" if "://" in cleaned else "keyvalue" if "=" in cleaned else "unknown",
    }

    if info["format"] != "uri":
        return info

    try:
        parsed = urlparse(cleaned)
    except Exception as exc:  # noqa: BLE001
        info["parse_error"] = f"{type(exc).__name__}: {exc}"
        return info

    host = parsed.hostname
    info["scheme"] = parsed.scheme
    info["host_parsed"] = host is not None
    info["host_length"] = len(host) if host else 0
    info["host_starts_with_dot"] = bool(host and host.startswith("."))
    info["host_ends_with_dot"] = bool(host and host.endswith("."))
    info["host_has_double_dot"] = bool(host and ".." in host)
    info["host_charclasses"] = sorted({_charclass(c) for c in (host or "")})
    info["database"] = (parsed.path or "/").lstrip("/")
    info["user_present"] = bool(parsed.username)

    try:
        info["port"] = parsed.port
    except ValueError as exc:
        info["port_error"] = str(exc)

    password = parsed.password or ""
    info["password_present"] = bool(password)
    info["password_length"] = len(password)
    # Zeichen, die in einer URI prozentkodiert werden muessen.
    needs_encoding = sorted({c for c in password if c in "@/:?#[]%& "})
    info["password_chars_needing_encoding"] = needs_encoding
    info["password_has_consecutive_dots"] = ".." in password

    return info


def _charclass(char: str) -> str:
    if char.isdigit():
        return "digit"
    if char.isalpha():
        return "alpha"
    return f"literal:{char!r}"


def _connect(dsn: str):
    dsn = _clean(dsn)
    errors: list[str] = []

    try:
        import psycopg  # psycopg 3
    except ModuleNotFoundError:
        psycopg = None  # type: ignore[assignment]

    if psycopg is not None:
        try:
            return psycopg.connect(dsn, connect_timeout=15), "psycopg3"
        except UnicodeError as exc:
            errors.append(f"psycopg3 URI-Parsing: {type(exc).__name__}: {exc}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"psycopg3: {type(exc).__name__}: {_redact(str(exc))}")

        # Fallback: URI in keyvalue-Conninfo umschreiben. Umgeht jede
        # URI-Escaping-Frage, weil libpq die Werte dann nicht mehr URL-dekodiert.
        keyvalue = _uri_to_keyvalue(dsn)
        if keyvalue:
            try:
                conn = psycopg.connect(keyvalue, connect_timeout=15)
                print("Hinweis: Verbindung ueber keyvalue-Conninfo statt URI.", file=sys.stderr)
                return conn, "psycopg3(keyvalue)"
            except Exception as exc:  # noqa: BLE001
                errors.append(f"psycopg3 keyvalue: {type(exc).__name__}: {_redact(str(exc))}")

    try:
        import psycopg2

        return psycopg2.connect(dsn, connect_timeout=15), "psycopg2"
    except ModuleNotFoundError:
        errors.append("psycopg2 nicht installiert")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"psycopg2: {type(exc).__name__}: {_redact(str(exc))}")

    print("Verbindung fehlgeschlagen. Versuche:", file=sys.stderr)
    for err in errors:
        print(f"  - {err}", file=sys.stderr)
    print("\nDSN-Diagnose (redigiert):", file=sys.stderr)
    print(json.dumps(diagnose_dsn(os.environ.get("TEST_DATABASE_URL", "")), indent=2,
                     ensure_ascii=False, default=str), file=sys.stderr)
    raise SystemExit(3)


def _uri_to_keyvalue(dsn: str) -> str | None:
    """postgresql://... -> 'host=... port=... dbname=... user=... password=...'"""
    try:
        p = urlparse(dsn)
        if not p.hostname:
            return None
        parts = [
            f"host={p.hostname}",
            f"port={p.port or 5432}",
            f"dbname={(p.path or '/').lstrip('/')}",
        ]
        if p.username:
            parts.append(f"user={p.username}")
        if p.password:
            escaped = p.password.replace("\\", "\\\\").replace("'", "\\'")
            parts.append(f"password='{escaped}'")
        return " ".join(parts)
    except Exception:  # noqa: BLE001
        return None


def _redact(text: str) -> str:
    """Entfernt eine eventuell in Fehlermeldungen enthaltene DSN."""
    dsn = _clean(os.environ.get("TEST_DATABASE_URL", ""))
    out = text
    if dsn:
        out = out.replace(dsn, "<DSN>")
        try:
            password = urlparse(dsn).password
            if password:
                out = out.replace(password, "<PASSWORD>")
        except Exception:  # noqa: BLE001
            pass
    return out[:300]


def _fingerprint(dsn: str) -> dict[str, Any]:
    """Identifiziert das Ziel, ohne es preiszugeben."""
    parsed = urlparse(dsn)
    host = (parsed.hostname or "").encode()
    return {
        "host_fingerprint": hashlib.sha256(host).hexdigest()[:12] if host else "unknown",
        "port_is_default": parsed.port in (None, 5432),
        "database": (parsed.path or "/").lstrip("/") or "unknown",
        "user_present": bool(parsed.username),
        "password_in_dsn": bool(parsed.password),
        "sslmode_in_dsn": "sslmode" in (parsed.query or ""),
    }


def _one(cur, sql: str, params: tuple = ()) -> Any:
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else None


def _rows(cur, sql: str, params: tuple = ()) -> list[tuple]:
    cur.execute(sql, params)
    return list(cur.fetchall())


def _safe(fn, *args, **kwargs) -> Any:
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - Sonde soll nie abbrechen
        return {"error": type(exc).__name__, "detail": str(exc)[:200]}


def probe() -> dict[str, Any]:
    dsn = _clean(os.environ.get("TEST_DATABASE_URL", ""))
    if not dsn:
        print("TEST_DATABASE_URL ist nicht gesetzt.", file=sys.stderr)
        raise SystemExit(2)

    placeholder = placeholder_reason(dsn)
    if placeholder:
        print(f"Abbruch: {placeholder}", file=sys.stderr)
        print("Setze TEST_DATABASE_URL auf die echte Verbindungszeichenkette.", file=sys.stderr)
        raise SystemExit(2)

    shape = credential_shape_reason(dsn)
    if shape:
        print(f"Abbruch: {shape}", file=sys.stderr)
        raise SystemExit(2)

    report: dict[str, Any] = {
        "probe_version": "1.0",
        "target": _fingerprint(dsn),
        "driver": None,
        "server": {},
        "privileges": {},
        "extensions": {},
        "pgvector": {},
        "schema_state": {},
        "findings": [],
    }

    conn, driver = _connect(dsn)
    report["driver"] = driver

    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            # ---------------- Server ----------------
            report["server"] = {
                "version": _safe(_one, cur, "SHOW server_version"),
                "version_num": _safe(_one, cur, "SHOW server_version_num"),
                "current_user": _safe(_one, cur, "SELECT current_user"),
                "session_user": _safe(_one, cur, "SELECT session_user"),
                "current_database": _safe(_one, cur, "SELECT current_database()"),
                "current_schema": _safe(_one, cur, "SELECT current_schema()"),
                "search_path": _safe(_one, cur, "SHOW search_path"),
                "timezone": _safe(_one, cur, "SHOW TimeZone"),
                "ssl_in_use": _safe(
                    _one, cur, "SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()"
                ),
                "max_connections": _safe(_one, cur, "SHOW max_connections"),
                "is_superuser": _safe(_one, cur, "SELECT usesuper FROM pg_user WHERE usename = current_user"),
            }

            # ---------------- Rechte ----------------
            report["privileges"] = {
                "database_create": _safe(
                    _one, cur, "SELECT has_database_privilege(current_user, current_database(), 'CREATE')"
                ),
                "database_connect": _safe(
                    _one, cur, "SELECT has_database_privilege(current_user, current_database(), 'CONNECT')"
                ),
                "public_schema_create": _safe(
                    _one, cur, "SELECT has_schema_privilege(current_user, 'public', 'CREATE')"
                ),
                "public_schema_usage": _safe(
                    _one, cur, "SELECT has_schema_privilege(current_user, 'public', 'USAGE')"
                ),
            }

            # ---------------- Extensions ----------------
            installed = _safe(
                _rows, cur, "SELECT extname, extversion FROM pg_extension ORDER BY extname"
            )
            report["extensions"]["installed"] = (
                {name: ver for name, ver in installed} if isinstance(installed, list) else installed
            )
            available_vector = _safe(
                _rows,
                cur,
                "SELECT name, default_version, installed_version "
                "FROM pg_available_extensions WHERE name = 'vector'",
            )
            report["extensions"]["vector_available"] = available_vector

            # ---------------- Indexzugriffsmethoden ----------------
            ams = _safe(_rows, cur, "SELECT amname FROM pg_am ORDER BY amname")
            am_names = [a[0] for a in ams] if isinstance(ams, list) else []
            report["pgvector"]["index_methods"] = am_names
            report["pgvector"]["hnsw_available"] = "hnsw" in am_names
            report["pgvector"]["ivfflat_available"] = "ivfflat" in am_names

            # ---------------- Schema-Bestand ----------------
            # Kein LIKE mit '%': psycopg3 deutet '%' als Platzhalter, sobald
            # execute() ein Parameter-Tupel bekommt.
            schemas = _safe(
                _rows,
                cur,
                "SELECT nspname FROM pg_namespace "
                "WHERE left(nspname, 3) <> 'pg_' AND nspname <> 'information_schema' "
                "ORDER BY nspname",
            )
            report["schema_state"]["schemas"] = [s[0] for s in schemas] if isinstance(schemas, list) else schemas

            tables = _safe(
                _rows,
                cur,
                "SELECT table_schema, table_name FROM information_schema.tables "
                "WHERE table_schema NOT IN ('pg_catalog','information_schema') "
                "ORDER BY table_schema, table_name LIMIT 100",
            )
            report["schema_state"]["tables"] = (
                [f"{s}.{t}" for s, t in tables] if isinstance(tables, list) else tables
            )

            report["schema_state"]["schema_migrations"] = _safe(
                _rows,
                cur,
                "SELECT version, applied_at FROM schema_migrations ORDER BY applied_at LIMIT 50",
            )

        # ---------------- Schreibprobe, immer zurueckgerollt ----------------
        report["privileges"]["create_schema_probe"] = _create_schema_probe(conn)

        # ---------------- pgvector-Verhalten ----------------
        report["pgvector"]["dimension_probe"] = _vector_dimension_probe(conn)

    finally:
        conn.close()

    report["findings"] = _derive_findings(report)
    return report


def _create_schema_probe(conn) -> dict[str, Any]:
    """Prueft CREATE SCHEMA -- Voraussetzung fuer Phase 2 des Gates. Rollt zurueck."""
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA {PROBE_SCHEMA}")
            cur.execute(f"CREATE TABLE {PROBE_SCHEMA}.t (id int primary key)")
            cur.execute(f"INSERT INTO {PROBE_SCHEMA}.t VALUES (1)")
            cur.execute(f"SELECT count(*) FROM {PROBE_SCHEMA}.t")
            count = cur.fetchone()[0]
        return {"ok": True, "rows_written": count, "rolled_back": True}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)[:200]}
    finally:
        conn.rollback()
        conn.autocommit = True


def _vector_dimension_probe(conn) -> dict[str, Any]:
    """Prueft, ob die im Projekt verwendete Dimension indizierbar ist. Rollt zurueck."""
    result: dict[str, Any] = {
        "project_dimension": PROJECT_EMBEDDING_DIMENSION,
        "hnsw_limit_assumed": HNSW_DIMENSION_LIMIT,
    }
    conn.autocommit = False
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"CREATE TABLE {PROBE_SCHEMA}_vec (id int, e vector({PROJECT_EMBEDDING_DIMENSION}))")
            result["table_with_project_dimension"] = "ok"
            result["variants"] = _index_variants(cur)
    except Exception as exc:  # noqa: BLE001
        result["error"] = type(exc).__name__
        result["detail"] = str(exc)[:250]
    finally:
        conn.rollback()
        conn.autocommit = True
    return result


def _index_variants(cur) -> dict[str, Any]:
    """Testet die realistischen Indexstrategien fuer Dimensionen ueber 2000.

    Jede Variante laeuft in einem SAVEPOINT, damit ein Fehlschlag die
    Transaktion nicht abbricht und die naechste Variante noch laufen kann.
    """
    dim = PROJECT_EMBEDDING_DIMENSION
    table = f"{PROBE_SCHEMA}_vec"

    variants: list[tuple[str, str, str]] = [
        (
            "hnsw_vector",
            f"CREATE INDEX ON {table} USING hnsw (e vector_cosine_ops)",
            "Status quo der Migration 002",
        ),
        (
            "ivfflat_vector",
            f"CREATE INDEX ON {table} USING ivfflat (e vector_cosine_ops) WITH (lists = 10)",
            "IVFFlat statt HNSW, gleiche Spalte",
        ),
        (
            "hnsw_halfvec_expression",
            f"CREATE INDEX ON {table} USING hnsw ((e::halfvec({dim})) halfvec_cosine_ops)",
            "Speicherung bleibt vector(3072), Index auf halbe Praezision",
        ),
        (
            "hnsw_halfvec_column",
            f"ALTER TABLE {table} ADD COLUMN h halfvec({dim}); "
            f"CREATE INDEX ON {table} USING hnsw (h halfvec_cosine_ops)",
            "Eigene halfvec-Spalte",
        ),
        (
            "hnsw_vector_1536",
            f"ALTER TABLE {table} ADD COLUMN s vector(1536); "
            f"CREATE INDEX ON {table} USING hnsw (s vector_cosine_ops)",
            "Reduzierte Dimension 1536",
        ),
    ]

    results: dict[str, Any] = {}
    for name, sql, note in variants:
        cur.execute(f"SAVEPOINT sp_{name}")
        try:
            for statement in sql.split("; "):
                cur.execute(statement)
            results[name] = {"ok": True, "note": note}
            cur.execute(f"RELEASE SAVEPOINT sp_{name}")
        except Exception as exc:  # noqa: BLE001
            results[name] = {"ok": False, "note": note, "error": str(exc)[:180]}
            cur.execute(f"ROLLBACK TO SAVEPOINT sp_{name}")
    return results


def _derive_findings(report: dict[str, Any]) -> list[str]:
    findings: list[str] = []

    ext = report["extensions"].get("installed")
    if isinstance(ext, dict) and "vector" not in ext:
        findings.append("BLOCKER: pgvector-Extension ist nicht installiert")

    if report["privileges"].get("create_schema_probe", {}).get("ok") is False:
        findings.append("BLOCKER: CREATE SCHEMA nicht moeglich - Phase 2 des Gates undurchfuehrbar")

    if report["server"].get("ssl_in_use") is False:
        findings.append("WARNUNG: Verbindung laeuft ohne SSL")

    if report["target"].get("password_in_dsn"):
        findings.append("WARNUNG: Passwort steht in der DSN - Vault-Aufloesung erwaegen")

    dim = report["pgvector"].get("dimension_probe", {})
    variants = dim.get("variants", {})
    if isinstance(variants, dict) and variants:
        if variants.get("hnsw_vector", {}).get("ok") is False:
            findings.append(
                f"BLOCKER: HNSW-Index auf vector({PROJECT_EMBEDDING_DIMENSION}) schlaegt fehl. "
                "storage/migrations/002_pgvector_embeddings.sql ist gegen echtes pgvector "
                "nicht lauffaehig."
            )
        workable = [name for name, res in variants.items() if res.get("ok")]
        if workable:
            findings.append("Tragfaehige Indexvarianten: " + ", ".join(sorted(workable)))
        else:
            findings.append(
                "BLOCKER: Keine der geprueften Indexvarianten funktioniert - "
                "Embedding-Dimension muss reduziert werden."
            )

    if not report["pgvector"].get("hnsw_available"):
        findings.append("HINWEIS: hnsw-Zugriffsmethode nicht verfuegbar - pgvector-Version pruefen")

    tz = report["server"].get("timezone")
    if tz and tz != "UTC":
        findings.append(f"HINWEIS: Server-Zeitzone ist {tz}, nicht UTC")

    if not findings:
        findings.append("Keine Blocker erkannt")
    return findings


if __name__ == "__main__":
    if "--diagnose" in sys.argv:
        raw = os.environ.get("TEST_DATABASE_URL", "")
        if not raw:
            print("TEST_DATABASE_URL ist nicht gesetzt.", file=sys.stderr)
            raise SystemExit(2)
        print(json.dumps(diagnose_dsn(raw), indent=2, ensure_ascii=False, default=str))
        raise SystemExit(0)

    print(json.dumps(probe(), indent=2, ensure_ascii=False, default=str))
