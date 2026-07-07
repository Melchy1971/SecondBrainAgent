"""v30.65 Agent Goal Tracking - service facade for the launcher CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .tracker import GoalTracker


class GoalService:
    def __init__(self, project_root: str | Path, *, tracker: GoalTracker | None = None, **overrides: Any):
        self.project_root = Path(project_root).resolve()
        self.tracker = tracker or GoalTracker.for_project(self.project_root, **overrides)

    def create(self, title: str, *, description: str = "", target_date: str | None = None,
               owner: str = "", metrics: list[dict] | None = None,
               milestones: list[dict] | None = None, decompose: bool = False) -> dict[str, Any]:
        goal = self.tracker.create_goal(title, description=description, target_date=target_date,
                                        owner=owner, metrics=metrics, milestones=milestones)
        result: dict[str, Any] = {"ok": True, "goal": goal.to_dict()}
        if decompose:
            try:
                result["decomposition"] = self.tracker.decompose(goal.id)
            except Exception as exc:
                result["decomposition_error"] = str(exc)
        return result

    def list(self) -> dict[str, Any]:
        goals = self.tracker.list()
        return {"ok": True, "count": len(goals), "goals": goals}

    def show(self, goal_id: str) -> dict[str, Any]:
        return {"ok": True, **self.tracker.status(goal_id)}

    def report(self, goal_id: str) -> dict[str, Any]:
        return {"ok": True, **self.tracker.report(goal_id)}

    def close(self, goal_id: str, *, force: bool = False) -> dict[str, Any]:
        goal = self.tracker.close(goal_id, force=force)
        return {"ok": True, "goal": goal.to_dict()}

    def dashboard(self) -> dict[str, Any]:
        return {"ok": True, **self.tracker.dashboard_snapshot()}

    def update(self, goal_id: str, *, metric: str | None = None, complete_milestone: str | None = None,
               add_milestone: str | None = None, status: str | None = None,
               decompose: bool = False, evidence: str | None = None) -> dict[str, Any]:
        actions: list[str] = []
        if decompose:
            self.tracker.decompose(goal_id)
            actions.append("decomposed")
        if metric:
            name, _, value = metric.partition("=")
            self.tracker.update_metric(goal_id, name.strip(), float(value))
            actions.append(f"metric:{name.strip()}")
        if complete_milestone:
            self.tracker.complete_milestone(goal_id, complete_milestone)
            actions.append(f"milestone_done:{complete_milestone}")
        if add_milestone:
            self.tracker.add_milestone(goal_id, add_milestone)
            actions.append("milestone_added")
        if evidence:
            self.tracker.add_evidence(goal_id, source="user", note=evidence)
            actions.append("evidence_added")
        if status == "pause":
            self.tracker.pause(goal_id)
            actions.append("paused")
        elif status == "resume":
            self.tracker.resume(goal_id)
            actions.append("resumed")
        elif status == "cancel":
            self.tracker.cancel(goal_id)
            actions.append("cancelled")
        return {"ok": True, "actions": actions, **self.tracker.status(goal_id)}
