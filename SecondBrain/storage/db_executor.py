"""Backend-agnostic SQL executor.

- SqliteExecutor: stdlib sqlite3 (development + tests, no third-party deps).
- SqlAlchemyExecutor: wraps the existing Database.session() (production; lazy import).

Both expose the same minimal surface used by the migration runner and health checks.
Existing repository/Database/TransactionManager APIs are untouched.
"""

from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence


class DatabaseConfigurationError(RuntimeError):
    """Dauerhafter Fehler: fehlender Treiber, falscher Dialekt, abgelehntes TLS.

    Von :class:`ConnectionError` bewusst getrennt. Ein Wiederholungsversuch kann
    diese Bedingung nie aufloesen -- er verschleiert sie nur hinter Backoff.
    """


# Fehlertexte, die auf Konfiguration statt auf Erreichbarkeit hindeuten.
_PERMANENT_MARKERS = (
    "does not support ssl",
    "no pg_hba.conf entry",
    "password authentication failed",
    "role \"",
    "database \"",
    "does not exist",
    "invalid dsn",
    "unsupported dialect",
    "can't load plugin",
)


def classify_error(exc: BaseException) -> str:
    """'permanent' bei Konfigurationsfehlern, sonst 'transient'."""
    if isinstance(exc, (ModuleNotFoundError, ImportError)):
        return "permanent"
    if isinstance(exc, DatabaseConfigurationError):
        return "permanent"
    text = str(exc).lower()
    if any(marker in text for marker in _PERMANENT_MARKERS):
        return "permanent"
    return "transient"


class SqlExecutor:
    dialect: str

    def execute(self, sql: str, params: Sequence[Any] | dict | None = None) -> list[tuple]:
        raise NotImplementedError

    def executescript(self, script: str) -> None:
        raise NotImplementedError

    @contextmanager
    def transaction(self) -> Iterator["SqlExecutor"]:
        raise NotImplementedError

    def ping(self) -> bool:
        """True bei Erreichbarkeit, False bei transientem Fehler.

        Konfigurationsfehler werden als :class:`DatabaseConfigurationError`
        weitergereicht statt zu False zu kollabieren. Frueher wurde jeder
        Fehler zu 'database ping failed' -- ein fehlender Treiber sah damit aus
        wie eine nicht erreichbare Datenbank und lief in vier Retries.
        """
        try:
            self.execute("SELECT 1")
            return True
        except Exception as exc:
            if classify_error(exc) == "permanent":
                raise DatabaseConfigurationError(str(exc)) from exc
            return False


class SqliteExecutor(SqlExecutor):
    dialect = "sqlite"

    def __init__(self, url_or_path: str = ":memory:") -> None:
        path = url_or_path
        if url_or_path.startswith("sqlite:///"):
            path = url_or_path[len("sqlite:///"):] or ":memory:"   # sqlalchemy convention
        elif url_or_path.startswith("sqlite://"):
            path = url_or_path[len("sqlite://"):] or ":memory:"
        if path not in (":memory:", ""):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path or ":memory:"
        # isolation_level=None -> autocommit; we manage transactions explicitly so that
        # DDL inside a transaction is rolled back atomically (Python default auto-commits DDL).
        self._conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()

    def execute(self, sql: str, params=None) -> list[tuple]:
        with self._lock:
            cur = self._conn.execute(sql, params or [])
            rows = cur.fetchall() if cur.description else []
            return [tuple(r) for r in rows]

    def executescript(self, script: str) -> None:
        for statement in [s.strip() for s in script.split(";") if s.strip()]:
            self._conn.execute(statement)

    @contextmanager
    def transaction(self):
        with self._lock:
            self._conn.execute("BEGIN")
            try:
                yield self
                self._conn.execute("COMMIT")
            except Exception:
                self._conn.execute("ROLLBACK")
                raise

    def close(self) -> None:
        self._conn.close()


class SqlAlchemyExecutor(SqlExecutor):
    """Production executor over the existing Database (SQLAlchemy). Lazy import."""

    dialect = "postgresql"

    def __init__(self, database) -> None:
        self.database = database

    def _text(self, sql: str):
        from sqlalchemy import text
        return text(sql)

    def execute(self, sql: str, params=None) -> list[tuple]:  # pragma: no cover - needs sqlalchemy
        with self.database.session() as session:
            result = session.execute(self._text(sql), params or {})
            return [tuple(r) for r in result.fetchall()] if result.returns_rows else []

    def executescript(self, script: str) -> None:  # pragma: no cover - needs sqlalchemy
        from sqlalchemy import text
        with self.database.session() as session:
            for statement in [s.strip() for s in script.split(";") if s.strip()]:
                session.execute(text(statement))

    @contextmanager
    def transaction(self):  # pragma: no cover - needs sqlalchemy
        with self.database.session():
            yield self
