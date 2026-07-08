from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
import json
import time
import uuid


@dataclass
class Goal:
    goal_id: str
    name: str
    target_value: float | None = None
    current_value: float | None = None
    unit: str = ""
    priority: int = 3
    deadline: str = ""
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Project:
    project_id: str
    name: str
    weekly_hours: float = 0.0
    priority: int = 3
    status: str = "active"
    risk_level: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TimeBudget:
    weekly_capacity_hours: float = 40.0
    fixed_commitments_hours: float = 0.0
    recovery_buffer_hours: float = 5.0

    @property
    def usable_hours(self) -> float:
        return max(0.0, self.weekly_capacity_hours - self.fixed_commitments_hours - self.recovery_buffer_hours)


@dataclass
class TwinProfile:
    profile_id: str = "default"
    goals: list[Goal] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    time_budget: TimeBudget = field(default_factory=TimeBudget)
    preferences: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


@dataclass
class ScenarioChange:
    kind: str
    name: str
    weekly_hours: float = 0.0
    priority: int = 3
    risk_level: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScenarioResult:
    scenario_id: str
    name: str
    capacity_hours: float
    used_hours: float
    free_hours: float
    overload_hours: float
    risk_score: int
    impact: str
    bottlenecks: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class DigitalTwinStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.save(TwinProfile())

    def load(self) -> TwinProfile:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            backup = self.path.with_suffix('.json.corrupt')
            self.path.replace(backup)
            profile = TwinProfile()
            self.save(profile)
            return profile
        goals = [Goal(**g) for g in raw.get("goals", [])]
        projects = [Project(**p) for p in raw.get("projects", [])]
        budget_raw = raw.get("time_budget", {}) or {}
        budget = TimeBudget(**budget_raw)
        return TwinProfile(
            profile_id=raw.get("profile_id", "default"),
            goals=goals,
            projects=projects,
            time_budget=budget,
            preferences=dict(raw.get("preferences", {})),
            updated_at=float(raw.get("updated_at", time.time())),
        )

    def save(self, profile: TwinProfile) -> None:
        profile.updated_at = time.time()
        tmp = self.path.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(asdict(profile), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)


class DigitalTwin:
    """v11.3 deterministic personal model.

    Scope:
    - no medical, legal or financial advice
    - capacity and trade-off model only
    - persistent local JSON state
    """
    def __init__(self, runtime_dir: str | Path):
        self.runtime_dir = Path(runtime_dir)
        self.store = DigitalTwinStore(self.runtime_dir / "digital_twin_v113.json")

    def snapshot(self) -> dict[str, Any]:
        profile = self.store.load()
        active_projects = [p for p in profile.projects if p.status == "active"]
        used = sum(max(0.0, p.weekly_hours) for p in active_projects)
        free = profile.time_budget.usable_hours - used
        return {
            "profile_id": profile.profile_id,
            "goals": len(profile.goals),
            "active_projects": len(active_projects),
            "capacity_hours": profile.time_budget.usable_hours,
            "used_hours": round(used, 2),
            "free_hours": round(free, 2),
            "overload_hours": round(abs(min(0.0, free)), 2),
            "risk_state": self._risk_state(free, active_projects),
            "store": str(self.store.path),
        }

    def add_goal(self, name: str, target_value: float | None = None, current_value: float | None = None, unit: str = "", priority: int = 3, deadline: str = "") -> Goal:
        profile = self.store.load()
        goal = Goal(uuid.uuid4().hex, name, target_value, current_value, unit, int(priority), deadline)
        profile.goals.append(goal)
        self.store.save(profile)
        return goal

    def add_project(self, name: str, weekly_hours: float, priority: int = 3, risk_level: int = 1) -> Project:
        profile = self.store.load()
        project = Project(uuid.uuid4().hex, name, float(weekly_hours), int(priority), "active", int(risk_level))
        profile.projects.append(project)
        self.store.save(profile)
        return project

    def set_capacity(self, weekly_capacity_hours: float, fixed_commitments_hours: float = 0.0, recovery_buffer_hours: float = 5.0) -> TimeBudget:
        profile = self.store.load()
        profile.time_budget = TimeBudget(float(weekly_capacity_hours), float(fixed_commitments_hours), float(recovery_buffer_hours))
        self.store.save(profile)
        return profile.time_budget

    def simulate(self, name: str, changes: list[ScenarioChange] | None = None) -> ScenarioResult:
        profile = self.store.load()
        changes = changes or []
        active_projects = [p for p in profile.projects if p.status == "active"]
        base_used = sum(max(0.0, p.weekly_hours) for p in active_projects)
        delta_hours = sum(max(0.0, c.weekly_hours) for c in changes if c.kind in {"project", "habit", "commitment"})
        used = base_used + delta_hours
        capacity = profile.time_budget.usable_hours
        free = capacity - used
        overload = abs(min(0.0, free))
        risk_score = self._risk_score(free, active_projects, changes)
        bottlenecks: list[str] = []
        recommendations: list[str] = []
        if overload > 0:
            bottlenecks.append(f"Zeitbudget überlastet um {overload:.1f} h/Woche")
            recommendations.append("Scope reduzieren, Projekt pausieren oder Recovery-Puffer explizit senken")
        if len(active_projects) + len([c for c in changes if c.kind == "project"]) > 5:
            bottlenecks.append("Zu viele parallele aktive Projekte")
            recommendations.append("WIP-Limit auf maximal 3 priorisierte Projekte setzen")
        if any(c.risk_level >= 4 for c in changes):
            bottlenecks.append("Mindestens eine Änderung hat hohes Einzelrisiko")
            recommendations.append("Vor Umsetzung Approval und Rollback-Kriterium definieren")
        if not bottlenecks:
            recommendations.append("Szenario ist kapazitiv tragfähig; nächste Prüfung über konkrete Meilensteine")
        return ScenarioResult(
            scenario_id=uuid.uuid4().hex,
            name=name,
            capacity_hours=round(capacity, 2),
            used_hours=round(used, 2),
            free_hours=round(free, 2),
            overload_hours=round(overload, 2),
            risk_score=risk_score,
            impact=self._impact_label(risk_score, overload),
            bottlenecks=bottlenecks,
            recommendations=recommendations,
        )

    @staticmethod
    def _risk_state(free_hours: float, projects: list[Project]) -> str:
        if free_hours < 0:
            return "overloaded"
        if free_hours < 3 or any(p.risk_level >= 4 for p in projects):
            return "tight"
        return "stable"

    @staticmethod
    def _risk_score(free_hours: float, projects: list[Project], changes: list[ScenarioChange]) -> int:
        score = 1
        if free_hours < 0: score += 4
        elif free_hours < 3: score += 2
        score += min(3, max(0, len(projects) + len([c for c in changes if c.kind == "project"]) - 3))
        score += max([0] + [c.risk_level - 2 for c in changes])
        return max(1, min(10, score))

    @staticmethod
    def _impact_label(risk_score: int, overload_hours: float) -> str:
        if overload_hours > 0 or risk_score >= 7:
            return "high_risk"
        if risk_score >= 4:
            return "medium_risk"
        return "low_risk"


def parse_scenario_change(text: str) -> ScenarioChange:
    """Parse 'Projektname:5:4' -> 5h/w risk 4. Conservative fallback."""
    parts = [p.strip() for p in text.split(":")]
    name = parts[0] if parts and parts[0] else "Unnamed Change"
    weekly_hours = float(parts[1]) if len(parts) > 1 and parts[1] else 1.0
    risk = int(parts[2]) if len(parts) > 2 and parts[2] else 2
    return ScenarioChange(kind="project", name=name, weekly_hours=weekly_hours, risk_level=risk)
