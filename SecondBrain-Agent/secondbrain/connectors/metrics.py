"""P4 v22.1 - Connector Metrics."""

class ConnectorMetrics:
    def summarize(self, sync_runs: int, synced_items: int, failures: int):
        success_rate = 0.0 if sync_runs == 0 else ((sync_runs - failures) / sync_runs)
        return {
            "sync_runs": sync_runs,
            "synced_items": synced_items,
            "failures": failures,
            "success_rate": round(success_rate, 3),
        }
