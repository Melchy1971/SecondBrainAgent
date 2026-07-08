"""v30.1 - Base repository contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepositoryResult:
    status: str
    affected: int = 0
    payload: dict | None = None


class BaseRepository:
    def __init__(self, database):
        self.database = database
