"""P0.2 - deterministic incremental sync diff engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any


@dataclass(frozen=True)
class SyncChangeSet:
    added: list[str]
    removed: list[str]
    updated: list[str]
    unchanged: list[str]

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "added": self.added,
            "removed": self.removed,
            "updated": self.updated,
            "unchanged": self.unchanged,
        }


class IncrementalSyncEngine:
    def compute_changes(
        self,
        previous: Iterable[str] | Mapping[str, Any],
        current: Iterable[str] | Mapping[str, Any],
    ) -> dict[str, list[str]]:
        previous_map = self._to_revision_map(previous)
        current_map = self._to_revision_map(current)

        previous_ids = set(previous_map)
        current_ids = set(current_map)
        common_ids = previous_ids & current_ids

        changes = SyncChangeSet(
            added=sorted(current_ids - previous_ids),
            removed=sorted(previous_ids - current_ids),
            updated=sorted(item_id for item_id in common_ids if previous_map[item_id] != current_map[item_id]),
            unchanged=sorted(item_id for item_id in common_ids if previous_map[item_id] == current_map[item_id]),
        )
        return changes.as_dict()

    def has_changes(self, previous: Iterable[str] | Mapping[str, Any], current: Iterable[str] | Mapping[str, Any]) -> bool:
        changes = self.compute_changes(previous, current)
        return bool(changes["added"] or changes["removed"] or changes["updated"])

    @staticmethod
    def _to_revision_map(items: Iterable[str] | Mapping[str, Any]) -> dict[str, Any]:
        if isinstance(items, Mapping):
            return {str(key): value for key, value in items.items()}
        return {str(item): None for item in items}
