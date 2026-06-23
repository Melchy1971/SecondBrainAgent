"""v30.1 - PostgreSQL health checks."""

from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class DatabaseHealth:
    status: str
    dialect: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class DatabaseHealthcheck:
    def __init__(self, database):
        self.database = database

    def run(self) -> DatabaseHealth:
        try:
            from sqlalchemy import text
            with self.database.engine().connect() as connection:
                dialect = connection.engine.dialect.name
                connection.execute(text("SELECT 1"))
            return DatabaseHealth(status="PASS", dialect=dialect)
        except Exception as exc:
            return DatabaseHealth(status="FAIL", error=str(exc))
