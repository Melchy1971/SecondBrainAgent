from .metrics import SkillMetrics
from .patterns import PatternLearner
from .store import LearningStore


class ReflectionEngine:
    def __init__(self, store: LearningStore):
        self.store = store
        self.metrics = SkillMetrics(store)
        self.patterns = PatternLearner(store)

    def reflect(self) -> dict:
        metrics = self.metrics.compute()
        failures = self.patterns.failure_patterns()
        recommendations = []

        for metric in metrics:
            if metric["attempts"] >= 2 and metric["success_rate"] < 0.7:
                recommendations.append({
                    "type": "skill_improvement",
                    "capability": metric["capability"],
                    "reason": "low_success_rate",
                    "priority": "high" if metric["success_rate"] < 0.4 else "medium",
                })

        for pattern in failures[:5]:
            recommendations.append({
                "type": "failure_pattern",
                "capability": pattern["capability"],
                "error": pattern["error"],
                "count": pattern["count"],
                "priority": "high" if pattern["count"] >= 3 else "medium",
            })

        report = {
            "metrics": metrics,
            "failure_patterns": failures,
            "success_patterns": self.patterns.success_patterns(),
            "recommendations": recommendations,
        }
        self.store.save("latest_reflection", report)
        return report
