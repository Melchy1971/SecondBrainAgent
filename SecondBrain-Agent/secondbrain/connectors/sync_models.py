"""v30.4 - connector sync domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass(frozen=True)
class SyncItem:
    external_id: str
    source: str
    kind: str
    payload: dict[str, Any]
    updated_at: float = field(default_factory=time)


@dataclass(frozen=True)
class SyncResult:
    connector: str
    status: str
    items: int
    cursor: str | None = None
    errors: list[str] = field(default_factory=list)
