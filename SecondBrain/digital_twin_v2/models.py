from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class Goal:
    id: str
    name: str
    target_value: float
    current_value: float
    unit: str
    deadline_days: int
    priority: int = 3


@dataclass
class Project:
    id: str
    name: str
    weekly_hours: float
    impact: float
    risk: float
    deadline_days: int
    strategic_score: float = 0.5


@dataclass
class Habit:
    id: str
    name: str
    weekly_hours: float
    energy_effect: float
    consistency: float


@dataclass
class TwinState:
    weekly_capacity_hours: float
    energy_level: float
    goals: List[Goal]
    projects: List[Project]
    habits: List[Habit]

    def to_dict(self) -> Dict:
        return asdict(self)
