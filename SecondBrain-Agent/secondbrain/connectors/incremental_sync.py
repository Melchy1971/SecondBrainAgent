"""P4 v22.2 - Incremental Sync Engine."""

class IncrementalSyncEngine:
    def compute_changes(self, previous: list[str], current: list[str]):
        previous_set = set(previous)
        current_set = set(current)
        return {
            "added": sorted(current_set - previous_set),
            "removed": sorted(previous_set - current_set),
        }
