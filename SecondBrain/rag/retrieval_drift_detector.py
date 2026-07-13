"""P1 v19.3 - retrieval drift detection."""

from __future__ import annotations


class RetrievalDriftDetector:
    def __init__(self, min_recall_at_10: float = 0.80, min_mrr: float = 0.70, min_ndcg_at_10: float = 0.75) -> None:
        self.thresholds = {
            "recall_at_10": min_recall_at_10,
            "mrr": min_mrr,
            "ndcg_at_10": min_ndcg_at_10,
        }

    def evaluate(self, metrics: dict[str, float]) -> dict[str, object]:
        failed = {
            key: {"actual": float(metrics.get(key, 0.0)), "threshold": threshold}
            for key, threshold in self.thresholds.items()
            if float(metrics.get(key, 0.0)) < threshold
        }
        return {
            "status": "PASS" if not failed else "FAIL",
            "failed": failed,
            "thresholds": self.thresholds,
        }
