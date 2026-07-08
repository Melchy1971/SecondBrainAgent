from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any
import json
import time
import uuid

from .digital_twin_v113 import DigitalTwin, ScenarioChange, ScenarioResult


@dataclass
class DecisionOption:
    name: str
    weekly_hours: float = 0.0
    expected_value: int = 3
    risk_level: int = 2
    reversibility: int = 3
    strategic_fit: int = 3
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionResult:
    decision_id: str
    question: str
    ranking: list[dict[str, Any]]
    recommended_option: str
    rationale: list[str]
    risks: list[str]
    created_at: float = field(default_factory=time.time)


class DecisionStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def append(self, result: DecisionResult) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8") or "[]")
        except json.JSONDecodeError:
            data = []
        data.append(asdict(result))
        tmp = self.path.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.path)

    def list(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8") or "[]")
        except json.JSONDecodeError:
            return []


class DecisionEngine:
    """v11.3 deterministic decision support.

    Score model: value + fit + reversibility - risk - capacity penalty.
    It optimizes transparency over pseudo-intelligence.
    """
    def __init__(self, runtime_dir: str | Path, twin: DigitalTwin):
        self.runtime_dir = Path(runtime_dir)
        self.twin = twin
        self.store = DecisionStore(self.runtime_dir / "decisions_v113.json")

    def evaluate(self, question: str, options: list[DecisionOption]) -> DecisionResult:
        if not options:
            raise ValueError("at_least_one_option_required")
        ranking: list[dict[str, Any]] = []
        risks: list[str] = []
        for option in options:
            scenario: ScenarioResult = self.twin.simulate(
                name=f"decision:{option.name}",
                changes=[ScenarioChange(kind="project", name=option.name, weekly_hours=option.weekly_hours, risk_level=option.risk_level)]
            )
            capacity_penalty = 4 if scenario.overload_hours > 0 else (2 if scenario.free_hours < 3 else 0)
            score = (
                int(option.expected_value) * 2
                + int(option.strategic_fit) * 2
                + int(option.reversibility)
                - int(option.risk_level) * 2
                - capacity_penalty
            )
            ranking.append({
                "option": option.name,
                "score": score,
                "expected_value": option.expected_value,
                "strategic_fit": option.strategic_fit,
                "risk_level": option.risk_level,
                "weekly_hours": option.weekly_hours,
                "capacity_impact": scenario.impact,
                "free_hours_after": scenario.free_hours,
                "overload_hours": scenario.overload_hours,
            })
            if scenario.overload_hours > 0:
                risks.append(f"{option.name}: Überlast {scenario.overload_hours:.1f} h/Woche")
            if option.risk_level >= 4:
                risks.append(f"{option.name}: hohes Umsetzungsrisiko")
        ranking.sort(key=lambda x: (x["score"], x["free_hours_after"]), reverse=True)
        best = ranking[0]["option"]
        rationale = [
            f"Beste Option nach Score: {best}",
            "Score = Nutzen + strategischer Fit + Reversibilität - Risiko - Kapazitätsstrafe",
            "Kapazitätsstrafe greift bei <3 freien Stunden oder Überlast",
        ]
        result = DecisionResult(uuid.uuid4().hex, question, ranking, best, rationale, risks)
        self.store.append(result)
        return result

    def history(self) -> list[dict[str, Any]]:
        return self.store.list()


def parse_option(text: str) -> DecisionOption:
    """Parse 'Name:hours:value:risk:fit:reversible'."""
    parts = [p.strip() for p in text.split(":")]
    return DecisionOption(
        name=parts[0] if parts and parts[0] else "Unnamed Option",
        weekly_hours=float(parts[1]) if len(parts) > 1 and parts[1] else 0.0,
        expected_value=int(parts[2]) if len(parts) > 2 and parts[2] else 3,
        risk_level=int(parts[3]) if len(parts) > 3 and parts[3] else 2,
        strategic_fit=int(parts[4]) if len(parts) > 4 and parts[4] else 3,
        reversibility=int(parts[5]) if len(parts) > 5 and parts[5] else 3,
    )
