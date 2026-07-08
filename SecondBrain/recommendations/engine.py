from datetime import datetime, timezone
from uuid import uuid4


class RecommendationEngine:
    def __init__(self, store, goal_engine=None, supervisor=None):
        self.store = store
        self.goal_engine = goal_engine
        self.supervisor = supervisor

    def generate(self) -> list[dict]:
        recs = []
        if self.supervisor:
            health = self.supervisor.health()
            if health["status"] != "healthy":
                recs.append(self._rec("runtime_recovery", "Runtime reparieren", "critical", health))

        if self.goal_engine:
            for forecast in self.goal_engine.forecast():
                if not forecast["on_track"]:
                    recs.append(self._rec("goal_risk", f"Ziel gefährdet: {forecast['name']}", "high", forecast))
                elif forecast["success_probability"] < 0.7:
                    recs.append(self._rec("goal_attention", f"Ziel beobachten: {forecast['name']}", "medium", forecast))

        if not recs:
            recs.append(self._rec("system_ok", "Keine kritischen Empfehlungen", "low", {}))

        self.store.save("latest_recommendations", recs)
        return recs

    def _rec(self, kind: str, title: str, priority: str, data: dict) -> dict:
        return {
            "id": str(uuid4()),
            "type": kind,
            "title": title,
            "priority": priority,
            "data": data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
