from collections import Counter
from .store import LearningStore


class PatternLearner:
    def __init__(self, store: LearningStore):
        self.store = store

    def failure_patterns(self) -> list[dict]:
        experiences = self.store.load("experiences", [])
        failures = [x for x in experiences if not x.get("success")]
        counter = Counter((x.get("capability", "unknown"), x.get("error") or "unknown_error") for x in failures)
        return [
            {"capability": cap, "error": err, "count": count}
            for (cap, err), count in counter.most_common()
        ]

    def success_patterns(self) -> list[dict]:
        experiences = self.store.load("experiences", [])
        successes = [x for x in experiences if x.get("success")]
        counter = Counter(x.get("capability", "unknown") for x in successes)
        return [{"capability": cap, "success_count": count} for cap, count in counter.most_common()]
