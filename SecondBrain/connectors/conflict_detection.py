"""Conflict detection for bidirectional sync (extends the existing resolver)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ConflictType(str, Enum):
    NONE = "none"
    LOCAL_ONLY = "local_only"
    REMOTE_ONLY = "remote_only"
    IDENTICAL = "identical"
    LOCAL_AHEAD = "local_ahead"
    REMOTE_AHEAD = "remote_ahead"
    BOTH_CHANGED = "both_changed"      # true conflict


@dataclass(frozen=True)
class ConflictReport:
    type: ConflictType
    external_id: str
    resolution: str      # "local" | "remote" | "manual" | "noop"


def _fingerprint(version: dict | None, key: str) -> Any:
    if not version:
        return None
    return version.get("content_hash") or version.get(key)


def detect(local: dict | None, remote: dict | None, *, external_id: str = "",
           base: dict | None = None, timestamp_key: str = "updated_at") -> ConflictReport:
    """Classify local vs remote versions relative to an optional common base."""
    if local is None and remote is None:
        return ConflictReport(ConflictType.NONE, external_id, "noop")
    if local is None:
        return ConflictReport(ConflictType.REMOTE_ONLY, external_id, "remote")
    if remote is None:
        return ConflictReport(ConflictType.LOCAL_ONLY, external_id, "local")

    lf, rf = _fingerprint(local, timestamp_key), _fingerprint(remote, timestamp_key)
    if lf == rf:
        return ConflictReport(ConflictType.IDENTICAL, external_id, "noop")

    if base is not None:
        bf = _fingerprint(base, timestamp_key)
        local_changed = lf != bf
        remote_changed = rf != bf
        if local_changed and remote_changed:
            return ConflictReport(ConflictType.BOTH_CHANGED, external_id, "manual")
        if local_changed:
            return ConflictReport(ConflictType.LOCAL_AHEAD, external_id, "local")
        return ConflictReport(ConflictType.REMOTE_AHEAD, external_id, "remote")

    # no base: fall back to timestamp comparison (last-write-wins hint)
    lt, rt = local.get(timestamp_key, 0), remote.get(timestamp_key, 0)
    if rt > lt:
        return ConflictReport(ConflictType.REMOTE_AHEAD, external_id, "remote")
    if lt > rt:
        return ConflictReport(ConflictType.LOCAL_AHEAD, external_id, "local")
    return ConflictReport(ConflictType.BOTH_CHANGED, external_id, "manual")
