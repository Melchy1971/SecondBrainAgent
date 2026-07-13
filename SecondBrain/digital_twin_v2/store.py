import json
from pathlib import Path
from .models import Goal, Project, Habit, TwinState


class TwinStore:
    def __init__(self, root: str | Path = "."):
        self.root = Path(root)
        self.path = self.root / "data" / "digital_twin_v2" / "state.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> TwinState:
        if not self.path.exists():
            return TwinState(
                weekly_capacity_hours=20.0,
                energy_level=0.7,
                goals=[],
                projects=[],
                habits=[],
            )
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return TwinState(
            weekly_capacity_hours=float(data.get("weekly_capacity_hours", 20.0)),
            energy_level=float(data.get("energy_level", 0.7)),
            goals=[Goal(**g) for g in data.get("goals", [])],
            projects=[Project(**p) for p in data.get("projects", [])],
            habits=[Habit(**h) for h in data.get("habits", [])],
        )

    def save(self, state: TwinState) -> None:
        self.path.write_text(json.dumps(state.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
