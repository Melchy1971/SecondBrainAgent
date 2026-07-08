from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class Experience:
    task: str
    outcome: str
    success: bool
    capability: str
    duration_seconds: float = 0.0
    error: str | None = None
    id: str = ""
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["id"] = data["id"] or str(uuid4())
        data["created_at"] = data["created_at"] or datetime.now(timezone.utc).isoformat()
        return data


@dataclass
class SkillMetric:
    capability: str
    attempts: int
    successes: int
    failures: int
    success_rate: float
    avg_duration_seconds: float
