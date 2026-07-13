"""Shared fakes for v30.65 goal-tracking tests."""

from __future__ import annotations

from typing import Any


class FakeNotifications:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    def notify(self, title: str, message: str, *, level: str = "info", category: str = "system",
               source: str = "native", action_required: bool = False, actions=None, metadata=None):
        self.sent.append({"title": title, "message": message, "level": level,
                          "category": category, "source": source})
        return {"ok": True}


class FakeStep:
    def __init__(self, sid: str, title: str, status: str = "pending"):
        self.id = sid
        self.title = title
        self.status = status  # plain string; tracker reads getattr(status,'value',status)


class FakePlan:
    def __init__(self, plan_id: str, steps: list[FakeStep]):
        self.id = plan_id
        self.steps = steps

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id,
                "steps": [{"id": s.id, "title": s.title, "status": s.status} for s in self.steps]}


class FakePlanner:
    """Stand-in for AgentPlanService: create() decomposes, load() reads back."""

    def __init__(self, n_steps: int = 3):
        self.n_steps = n_steps
        self._plans: dict[str, FakePlan] = {}
        self._n = 0

    def create(self, goal: str, *, workspace_id: str | None = None) -> FakePlan:
        self._n += 1
        pid = f"plan_{self._n}"
        steps = [FakeStep(f"s{i}", f"Schritt {i} fuer {goal}") for i in range(1, self.n_steps + 1)]
        plan = FakePlan(pid, steps)
        self._plans[pid] = plan
        return plan

    def load(self, plan_id: str) -> FakePlan:
        if plan_id not in self._plans:
            raise KeyError(plan_id)
        return self._plans[plan_id]

    def complete_all(self, plan_id: str) -> None:
        for s in self._plans[plan_id].steps:
            s.status = "completed"


class MemorySink:
    def __init__(self) -> None:
        self.facts: list[dict] = []

    def __call__(self, fact: dict) -> None:
        self.facts.append(fact)


def make_tracker(tmp_path, *, planner=None, notifications=None, memory_sink=None):
    from secondbrain.agent.goals import GoalTracker

    notifications = notifications or FakeNotifications()
    tracker = GoalTracker(tmp_path, notifications=notifications, planner=planner,
                          memory_sink=memory_sink)
    return tracker, notifications
