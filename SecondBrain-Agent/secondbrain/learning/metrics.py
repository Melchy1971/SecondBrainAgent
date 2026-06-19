from collections import defaultdict
from .store import LearningStore


class SkillMetrics:
    def __init__(self, store: LearningStore):
        self.store = store

    def compute(self) -> list[dict]:
        experiences = self.store.load("experiences", [])
        grouped = defaultdict(list)
        for exp in experiences:
            grouped[exp.get("capability", "unknown")].append(exp)

        result = []
        for capability, items in grouped.items():
            attempts = len(items)
            successes = sum(1 for x in items if x.get("success"))
            failures = attempts - successes
            avg_duration = sum(float(x.get("duration_seconds", 0)) for x in items) / max(attempts, 1)
            result.append({
                "capability": capability,
                "attempts": attempts,
                "successes": successes,
                "failures": failures,
                "success_rate": round(successes / max(attempts, 1), 3),
                "avg_duration_seconds": round(avg_duration, 2),
            })
        result.sort(key=lambda x: (x["success_rate"], -x["attempts"]))
        return result
