"""Database backend policy: DATABASE_URL classification + dev/prod + fallback gating.

Rules (v30.62):
- PostgreSQL is the only production backend.
- SQLite is development-only.
- Falling back to SQLite is NEVER automatic unless explicitly enabled via
  SECOND_BRAIN_ALLOW_SQLITE_FALLBACK.
- A missing/invalid production database must block cleanly (DatabaseStartupError).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

PROD = "production"
DEV = "development"


class DatabaseStartupError(RuntimeError):
    """Raised when the database cannot be resolved/validated and no fallback is allowed."""


def parse_dialect(url: str | None) -> str | None:
    if not url:
        return None
    scheme = urlparse(url).scheme.lower()
    head = scheme.split("+", 1)[0]
    if head.startswith("postgres"):
        return "postgresql"
    if head.startswith("sqlite"):
        return "sqlite"
    return head or None


def _bool(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class DbResolution:
    backend: str          # "postgresql" | "sqlite"
    url: str
    environment: str
    is_fallback: bool
    reason: str


def read_env(env: dict[str, str] | None = None) -> dict[str, str]:
    src = os.environ if env is None else env
    return {
        "url": (src.get("SECOND_BRAIN_DATABASE_URL") or src.get("DATABASE_URL") or "").strip(),
        "environment": (src.get("SECOND_BRAIN_ENV") or PROD).strip().lower(),
        "allow_fallback": "1" if _bool(src.get("SECOND_BRAIN_ALLOW_SQLITE_FALLBACK")) else "",
        "sqlite_dev_path": (src.get("SECOND_BRAIN_SQLITE_DEV_PATH") or "runtime/dev.sqlite3").strip(),
    }


def resolve(env: dict[str, str] | None = None) -> DbResolution:
    e = read_env(env)
    environment = DEV if e["environment"].startswith("dev") else PROD
    allow_fallback = bool(e["allow_fallback"])
    url = e["url"]
    dialect = parse_dialect(url)

    if dialect == "postgresql":
        return DbResolution("postgresql", url, environment, False, "postgresql url")

    if dialect == "sqlite":
        if environment == PROD and not allow_fallback:
            raise DatabaseStartupError(
                "SQLite is development-only. Set a PostgreSQL DATABASE_URL for production, "
                "or set SECOND_BRAIN_ENV=development (with SECOND_BRAIN_ALLOW_SQLITE_FALLBACK=1)."
            )
        return DbResolution("sqlite", url, environment, False, "explicit sqlite url (dev)")

    # no/unknown url
    if url:
        raise DatabaseStartupError(f"Unsupported database URL scheme: {url!r}")
    if allow_fallback:
        sqlite_url = f"sqlite:///{e['sqlite_dev_path']}"
        return DbResolution("sqlite", sqlite_url, environment, True,
                            "no DATABASE_URL; explicit SQLite fallback enabled")
    raise DatabaseStartupError(
        "Missing DATABASE_URL and SQLite fallback is not enabled "
        "(set SECOND_BRAIN_ALLOW_SQLITE_FALLBACK=1 to allow a development SQLite database)."
    )
