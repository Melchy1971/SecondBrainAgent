"""v30.65 Agent Goal Tracking - GoalTracker.

The application service. It reuses:
* Agent Planner   - decompose a goal into an executable plan (and milestones).
* Workflow Engine - read linked workflow state for progress (optional).
* Memory          - optional sink fed with goal lifecycle facts.
* Notification Center - risk / completion / review notices.
* Dashboard       - a cross-goal snapshot for the native dashboard.

Progress is a deterministic blend of milestone completion, metric attainment and
linked-plan step completion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .models import (
    Goal,
    GoalEvidence,
    GoalMetric,
    GoalMilestone,
    GoalReview,
    GoalStatus,
    new_id,
    utc_now,
    _parse_ts,
)
from .store import GoalStore


@dataclass
class GoalProgress:
    overall: float
    milestone: float | None = None
    metric: float | None = None
    plan: float | None = None
    components: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall": round(self.overall, 4),
            "milestone": None if self.milestone is None else round(self.milestone, 4),
            "metric": None if self.metric is None else round(self.metric, 4),
            "plan": None if self.plan is None else round(self.plan, 4),
            "components": self.components,
        }


class GoalTracker:
    def __init__(
        self,
        project_root: str | Path,
        *,
        notifications: Any | None = None,
        memory_sink: Callable[[dict], None] | None = None,
        planner: Any | None = None,
        workflow_store: Any | None = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.store = GoalStore(self.project_root)
        self.notifications = notifications
        self.memory_sink = memory_sink
        self.planner = planner
        self.workflow_store = workflow_store

    @classmethod
    def for_project(cls, project_root: str | Path, **overrides: Any) -> "GoalTracker":
        root = Path(project_root).resolve()
        defaults: dict[str, Any] = {}
        try:
            from secondbrain.native.notification_center.service import NotificationCenterService
            defaults["notifications"] = NotificationCenterService(root)
        except Exception:
            pass
        try:
            from secondbrain.agent.planner import AgentPlanService
            defaults["planner"] = AgentPlanService(root)
        except Exception:
            pass
        try:
            from secondbrain.agent.workflow.store import WorkflowStore
            defaults["workflow_store"] = WorkflowStore(root)
        except Exception:
            pass
        defaults.update(overrides)
        return cls(root, **defaults)

    # -- creation ----------------------------------------------------------
    def create_goal(self, title: str, *, description: str = "", metrics: list[dict] | None = None,
                    milestones: list[dict] | None = None, target_date: str | None = None,
                    owner: str = "", workspace_id: str | None = None, activate: bool = True) -> Goal:
        goal = Goal(
            id=new_id("goal"),
            title=title,
            description=description,
            status=GoalStatus.ACTIVE if activate else GoalStatus.DRAFT,
            workspace_id=workspace_id,
            owner=owner,
            target_date=target_date,
            metrics=[GoalMetric.from_dict(m) for m in (metrics or [])],
            milestones=[GoalMilestone.from_dict({**m, "id": m.get("id") or new_id("ms")})
                        for m in (milestones or [])],
        )
        self.store.upsert(goal)
        self._remember({"kind": "goal_created", "goal_id": goal.id, "title": title})
        return goal

    def decompose(self, goal_id: str, *, workspace_id: str | None = None) -> dict[str, Any]:
        goal = self._require(goal_id)
        if self.planner is None:
            raise RuntimeError("planner_unavailable")
        plan = self.planner.create(goal.title, workspace_id=workspace_id or goal.workspace_id)
        plan_dict = plan.to_dict() if hasattr(plan, "to_dict") else dict(plan)
        plan_id = plan_dict["id"]
        if plan_id not in goal.plan_ids:
            goal.plan_ids.append(plan_id)
        # one milestone per plan step (idempotent by plan_id+step id)
        existing = {(m.plan_id, m.id) for m in goal.milestones}
        for step in plan_dict.get("steps", []):
            ms_id = f"{plan_id}:{step['id']}"
            if (plan_id, ms_id) in existing:
                continue
            goal.milestones.append(GoalMilestone(
                id=ms_id, title=step.get("title", step["id"]), plan_id=plan_id))
        goal.updated_at = utc_now()
        self.store.upsert(goal)
        self.add_evidence(goal_id, source="planner", note="goal decomposed into plan",
                          ref=f"plan:{plan_id}")
        self._remember({"kind": "goal_decomposed", "goal_id": goal.id, "plan_id": plan_id})
        return {"goal": goal.to_dict(), "plan_id": plan_id, "steps": len(plan_dict.get("steps", []))}

    # -- progress ----------------------------------------------------------
    def measure_progress(self, goal_id: str) -> GoalProgress:
        goal = self._require(goal_id)
        components: list[str] = []
        parts: list[float] = []

        ms = goal.milestone_progress()
        if ms is not None:
            components.append("milestone")
            parts.append(ms)
        met = goal.metric_progress()
        if met is not None:
            components.append("metric")
            parts.append(met)
        plan = self._plan_progress(goal)
        if plan is not None:
            components.append("plan")
            parts.append(plan)

        overall = sum(parts) / len(parts) if parts else 0.0
        return GoalProgress(overall=overall, milestone=ms, metric=met, plan=plan, components=components)

    def _plan_progress(self, goal: Goal) -> float | None:
        if not goal.plan_ids or self.planner is None:
            return None
        ratios: list[float] = []
        for plan_id in goal.plan_ids:
            try:
                plan = self.planner.load(plan_id)
            except Exception:
                continue
            steps = getattr(plan, "steps", [])
            if not steps:
                continue
            done = sum(1 for s in steps if str(getattr(s.status, "value", s.status)) == "completed")
            ratios.append(done / len(steps))
        if not ratios:
            return None
        return sum(ratios) / len(ratios)

    # -- risks -------------------------------------------------------------
    def risks(self, goal_id: str, *, now: datetime | None = None) -> list[str]:
        goal = self._require(goal_id)
        current = now or datetime.now(timezone.utc)
        found: list[str] = []
        for m in goal.milestones:
            if m.is_overdue(current):
                found.append(f"milestone_overdue:{m.id}")
        target = _parse_ts(goal.target_date)
        overall = self.measure_progress(goal_id).overall
        if target is not None and current > target and overall < 1.0 and not goal.status.is_terminal:
            found.append("goal_overdue")
            for metric in goal.metrics:
                if not metric.reached:
                    found.append(f"metric_behind:{metric.name}")
        if goal.status == GoalStatus.PAUSED:
            found.append("goal_paused")
        return found

    # -- updates -----------------------------------------------------------
    def update_metric(self, goal_id: str, name: str, current: float) -> Goal:
        goal = self._require(goal_id)
        metric = goal.metric(name)
        if metric is None:
            raise KeyError(f"unknown_metric:{name}")
        metric.current = float(current)
        goal.updated_at = utc_now()
        return self.store.upsert(goal)

    def add_metric(self, goal_id: str, metric: dict) -> Goal:
        goal = self._require(goal_id)
        goal.metrics.append(GoalMetric.from_dict(metric))
        goal.updated_at = utc_now()
        return self.store.upsert(goal)

    def complete_milestone(self, goal_id: str, milestone_id: str, done: bool = True) -> Goal:
        goal = self._require(goal_id)
        ms = goal.milestone(milestone_id)
        if ms is None:
            raise KeyError(f"unknown_milestone:{milestone_id}")
        ms.done = bool(done)
        goal.updated_at = utc_now()
        self._remember({"kind": "milestone_completed", "goal_id": goal.id, "milestone_id": milestone_id})
        return self.store.upsert(goal)

    def add_milestone(self, goal_id: str, title: str, *, weight: float = 1.0,
                      due: str | None = None) -> Goal:
        goal = self._require(goal_id)
        goal.milestones.append(GoalMilestone(id=new_id("ms"), title=title, weight=weight, due=due))
        goal.updated_at = utc_now()
        return self.store.upsert(goal)

    def add_evidence(self, goal_id: str, *, source: str, note: str = "", ref: str = "") -> Goal:
        goal = self._require(goal_id)
        goal.evidence.append(GoalEvidence(id=new_id("ev"), ts=utc_now(), source=source,
                                          note=note, ref=ref))
        goal.updated_at = utc_now()
        return self.store.upsert(goal)

    # -- lifecycle ---------------------------------------------------------
    def pause(self, goal_id: str) -> Goal:
        return self._set_status(goal_id, GoalStatus.PAUSED, terminal_ok=False)

    def resume(self, goal_id: str) -> Goal:
        return self._set_status(goal_id, GoalStatus.ACTIVE, terminal_ok=False)

    def close(self, goal_id: str, *, force: bool = False) -> Goal:
        goal = self._require(goal_id)
        if goal.status.is_terminal:
            return goal
        progress = self.measure_progress(goal_id).overall
        if progress < 1.0 and not force:
            raise ValueError(f"goal_incomplete:{round(progress, 2)}")
        goal.status = GoalStatus.COMPLETED
        goal.updated_at = utc_now()
        self.store.upsert(goal)
        self._notify(f"Ziel abgeschlossen: {goal.title}", f"Fortschritt {round(progress * 100)}%",
                     level="success")
        self._remember({"kind": "goal_completed", "goal_id": goal.id})
        return goal

    def cancel(self, goal_id: str) -> Goal:
        goal = self._require(goal_id)
        if goal.status.is_terminal:
            return goal
        goal.status = GoalStatus.CANCELLED
        goal.updated_at = utc_now()
        return self.store.upsert(goal)

    def _set_status(self, goal_id: str, status: GoalStatus, *, terminal_ok: bool) -> Goal:
        goal = self._require(goal_id)
        if goal.status.is_terminal and not terminal_ok:
            raise ValueError(f"goal_terminal:{goal.status.value}")
        goal.status = status
        goal.updated_at = utc_now()
        return self.store.upsert(goal)

    # -- reporting ---------------------------------------------------------
    def report(self, goal_id: str, *, now: datetime | None = None) -> dict[str, Any]:
        goal = self._require(goal_id)
        progress = self.measure_progress(goal_id)
        risks = self.risks(goal_id, now=now)

        # auto status: keep terminal / paused; else AT_RISK if risks else ACTIVE
        if not goal.status.is_terminal and goal.status != GoalStatus.PAUSED:
            goal.status = GoalStatus.AT_RISK if risks else GoalStatus.ACTIVE
            self.store.upsert(goal)

        done_ms = sum(1 for m in goal.milestones if m.done)
        summary = (f"{goal.title}: {round(progress.overall * 100)}% "
                   f"({done_ms}/{len(goal.milestones)} Meilensteine), "
                   f"{len(risks)} Risiken")
        review = GoalReview(
            id=new_id("review"), goal_id=goal.id, ts=utc_now(),
            progress=round(progress.overall, 4), status=goal.status.value,
            risks=risks, summary=summary,
            metrics=[m.to_dict() for m in goal.metrics],
            milestones=[m.to_dict() for m in goal.milestones],
        )
        self.store.append_review(review)
        self._notify(f"Zielbericht: {goal.title}", summary,
                     level="warning" if risks else "info")
        self._remember({"kind": "goal_review", "goal_id": goal.id,
                        "progress": review.progress, "risks": len(risks)})
        return {"review": review.to_dict(), "progress": progress.to_dict()}

    # -- read --------------------------------------------------------------
    def status(self, goal_id: str) -> dict[str, Any]:
        goal = self._require(goal_id)
        reviews = self.store.reviews(goal_id, limit=1)
        return {
            "goal": goal.to_dict(),
            "progress": self.measure_progress(goal_id).to_dict(),
            "risks": self.risks(goal_id),
            "last_review": reviews[-1].to_dict() if reviews else None,
        }

    def list(self) -> list[dict[str, Any]]:
        result = []
        for goal in self.store.load_goals().values():
            result.append({
                "id": goal.id,
                "title": goal.title,
                "status": goal.status.value,
                "progress": round(self.measure_progress(goal.id).overall, 4),
                "milestones": len(goal.milestones),
                "plans": len(goal.plan_ids),
                "target_date": goal.target_date,
            })
        return result

    def dashboard_snapshot(self) -> dict[str, Any]:
        goals = list(self.store.load_goals().values())
        by_status: dict[str, int] = {}
        progresses: list[float] = []
        at_risk: list[str] = []
        for goal in goals:
            by_status[goal.status.value] = by_status.get(goal.status.value, 0) + 1
            p = self.measure_progress(goal.id).overall
            progresses.append(p)
            if goal.status == GoalStatus.AT_RISK or self.risks(goal.id):
                at_risk.append(goal.id)
        return {
            "schema": "secondbrain.agent.goals.dashboard.v30_65",
            "total": len(goals),
            "by_status": by_status,
            "avg_progress": round(sum(progresses) / len(progresses), 4) if progresses else 0.0,
            "at_risk": at_risk,
        }

    # -- helpers -----------------------------------------------------------
    def _require(self, goal_id: str) -> Goal:
        goal = self.store.get(goal_id)
        if goal is None:
            raise KeyError(f"unknown_goal:{goal_id}")
        return goal

    def _notify(self, title: str, message: str, *, level: str = "info") -> None:
        if self.notifications is None:
            return
        try:
            self.notifications.notify(title, message, level=level, category="agent",
                                      source="goal_tracker")
        except Exception:
            pass

    def _remember(self, fact: dict[str, Any]) -> None:
        if self.memory_sink is None:
            return
        try:
            self.memory_sink(fact)
        except Exception:
            pass
