"""Shared fakes for v30.69 coordination tests."""

from __future__ import annotations

from typing import Any


class FakePlan:
    def __init__(self, plan_id: str, goal: str, steps: list[dict]):
        self._d = {"id": plan_id, "goal": goal, "status": "validated", "steps": steps}

    def to_dict(self) -> dict[str, Any]:
        return dict(self._d)


class FakePlanner:
    """Stand-in for AgentPlanService with controllable plan content."""

    def __init__(self, steps: list[dict] | None = None):
        self.steps = steps if steps is not None else [
            {"id": "s1", "title": "Analyse", "risk_level": "low",
             "requires_approval": False, "expected_output": "Analyse fertig"},
        ]
        self._n = 0

    def create(self, goal: str, *, workspace_id: str | None = None) -> FakePlan:
        self._n += 1
        return FakePlan(f"plan_{self._n}", goal, [dict(s) for s in self.steps])


RISKY_STEPS = [
    {"id": "s1", "title": "Loeschen", "risk_level": "high",
     "requires_approval": True, "expected_output": "geloescht"},
]
