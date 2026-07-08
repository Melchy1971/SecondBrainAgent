"""SQL migration runner. Applies migrations/NNN_*.sql in order, tracked + idempotent.

Backend-agnostic (works over any SqlExecutor). The bundled migrations are PostgreSQL
SQL; tests exercise the runner mechanics against SQLite with dialect-neutral fixtures.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from secondbrain.storage.db_executor import SqlExecutor

_NAME = re.compile(r"^(\d+)_.*\.sql$")


@dataclass(frozen=True)
class Migration:
    version: str
    path: Path
    order: int


class MigrationRunner:
    def __init__(self, executor: SqlExecutor, migrations_dir: str | Path) -> None:
        self.executor = executor
        self.dir = Path(migrations_dir)

    def _ensure_table(self) -> None:
        self.executor.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations "
            "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )

    def discover(self) -> list[Migration]:
        out: list[Migration] = []
        if not self.dir.exists():
            return out
        for p in sorted(self.dir.iterdir()):
            m = _NAME.match(p.name)
            if m:
                out.append(Migration(version=p.stem, path=p, order=int(m.group(1))))
        out.sort(key=lambda x: x.order)
        return out

    def applied(self) -> set[str]:
        self._ensure_table()
        rows = self.executor.execute("SELECT version FROM schema_migrations")
        return {r[0] for r in rows}

    def pending(self) -> list[Migration]:
        done = self.applied()
        return [m for m in self.discover() if m.version not in done]

    def apply(self) -> dict:
        self._ensure_table()
        applied_now: list[str] = []
        for migration in self.pending():
            sql = migration.path.read_text(encoding="utf-8")
            with self.executor.transaction():
                self.executor.executescript(sql)
                self.executor.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)"
                    if self.executor.dialect == "sqlite"
                    else "INSERT INTO schema_migrations (version, applied_at) VALUES (:version, :applied_at)",
                    [migration.version, datetime.now(timezone.utc).isoformat()]
                    if self.executor.dialect == "sqlite"
                    else {"version": migration.version, "applied_at": datetime.now(timezone.utc).isoformat()},
                )
            applied_now.append(migration.version)
        return {"applied": applied_now, "total_applied": len(self.applied()),
                "pending": [m.version for m in self.pending()]}

    def status(self) -> dict:
        discovered = [m.version for m in self.discover()]
        done = self.applied()
        return {"discovered": discovered, "applied": sorted(done),
                "pending": [v for v in discovered if v not in done],
                "up_to_date": all(v in done for v in discovered)}
