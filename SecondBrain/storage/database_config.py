"""v30.1 - PostgreSQL production database configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class DatabaseConfig:
    url: str
    pool_size: int = 20
    max_overflow: int = 40
    pool_recycle: int = 3600
    statement_timeout_ms: int = 30000

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "DatabaseConfig":
        source = env or os.environ
        url = source.get("SECOND_BRAIN_DATABASE_URL") or source.get("DATABASE_URL")
        if not url:
            raise ValueError("Missing SECOND_BRAIN_DATABASE_URL or DATABASE_URL")
        return cls(
            url=url,
            pool_size=int(source.get("SECOND_BRAIN_DB_POOL_SIZE", "20")),
            max_overflow=int(source.get("SECOND_BRAIN_DB_MAX_OVERFLOW", "40")),
            pool_recycle=int(source.get("SECOND_BRAIN_DB_POOL_RECYCLE", "3600")),
            statement_timeout_ms=int(source.get("SECOND_BRAIN_DB_STATEMENT_TIMEOUT_MS", "30000")),
        )
