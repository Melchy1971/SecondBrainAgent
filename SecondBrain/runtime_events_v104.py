from __future__ import annotations

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
import json
import uuid


@dataclass(frozen=True)
class RuntimeEvent:
    """Canonical append-only event used by connectors, AI runtime and agents."""

    event_type: str
    source: str
    payload: dict[str, Any]
    actor: str = "system"
    risk_level: int = 1
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str = "v10.4"

    def validate(self) -> None:
        if not self.event_type or not isinstance(self.event_type, str):
            raise ValueError("event_type is required")
        if not self.source or not isinstance(self.source, str):
            raise ValueError("source is required")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")
        if self.risk_level < 1 or self.risk_level > 4:
            raise ValueError("risk_level must be between 1 and 4")

    def to_json(self) -> str:
        self.validate()
        return json.dumps(asdict(self), ensure_ascii=False, sort_keys=True)

    @staticmethod
    def from_json(line: str) -> "RuntimeEvent":
        data = json.loads(line)
        return RuntimeEvent(**data)


class JsonlEventStore:
    """Small local event store. No database dependency. Durable enough for v10.4."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, event: RuntimeEvent) -> Path:
        day = event.created_at[:10]
        return self.root / f"{day}.jsonl"

    def append(self, event: RuntimeEvent) -> Path:
        event.validate()
        path = self._path_for(event)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(event.to_json() + "\n")
        return path

    def read_all(self) -> list[RuntimeEvent]:
        events: list[RuntimeEvent] = []
        for path in sorted(self.root.glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    events.append(RuntimeEvent.from_json(line))
        return events

    def filter(self, event_type: str | None = None, source: str | None = None) -> list[RuntimeEvent]:
        result = self.read_all()
        if event_type:
            result = [event for event in result if event.event_type == event_type]
        if source:
            result = [event for event in result if event.source == source]
        return result

    def summarize(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_source: dict[str, int] = {}
        max_risk = 1
        for event in self.read_all():
            by_type[event.event_type] = by_type.get(event.event_type, 0) + 1
            by_source[event.source] = by_source.get(event.source, 0) + 1
            max_risk = max(max_risk, event.risk_level)
        return {"event_count": sum(by_type.values()), "by_type": by_type, "by_source": by_source, "max_risk": max_risk}


def emit_many(store: JsonlEventStore, events: Iterable[RuntimeEvent]) -> list[Path]:
    return [store.append(event) for event in events]
