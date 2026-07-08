from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


class LayoutValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class WidgetPosition:
    widget_id: str
    x: int
    y: int
    width: int = 1
    height: int = 1

    def cells(self) -> set[tuple[int, int]]:
        return {
            (cx, cy)
            for cx in range(self.x, self.x + self.width)
            for cy in range(self.y, self.y + self.height)
        }

    def validate(self, columns: int) -> list[str]:
        errors: list[str] = []
        if not self.widget_id:
            errors.append("widget_id_required")
        if self.x < 0 or self.y < 0:
            errors.append("position_must_be_non_negative")
        if self.width <= 0 or self.height <= 0:
            errors.append("size_must_be_positive")
        if self.x + self.width > columns:
            errors.append("position_exceeds_columns")
        return errors


@dataclass(slots=True)
class DashboardLayout:
    layout_id: str = "default"
    columns: int = 12
    positions: list[WidgetPosition] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def by_widget_id(self) -> dict[str, WidgetPosition]:
        return {position.widget_id: position for position in self.positions}

    def add_or_replace(self, position: WidgetPosition) -> None:
        self.positions = [item for item in self.positions if item.widget_id != position.widget_id]
        self.positions.append(position)
        self.positions.sort(key=lambda item: (item.y, item.x, item.widget_id))

    def remove(self, widget_id: str) -> bool:
        before = len(self.positions)
        self.positions = [item for item in self.positions if item.widget_id != widget_id]
        return len(self.positions) != before

    def to_dict(self) -> dict[str, Any]:
        return {
            "layout_id": self.layout_id,
            "columns": self.columns,
            "positions": [asdict(position) for position in self.positions],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "DashboardLayout":
        return cls(
            layout_id=str(payload.get("layout_id", "default")),
            columns=int(payload.get("columns", 12)),
            positions=[WidgetPosition(**dict(item)) for item in payload.get("positions", [])],
            metadata=dict(payload.get("metadata", {})),
        )


@dataclass(frozen=True, slots=True)
class LayoutValidationResult:
    status: LayoutValidationStatus
    errors: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return self.status == LayoutValidationStatus.VALID


class DashboardLayoutValidator:
    def validate(self, layout: DashboardLayout, enabled_widgets: Iterable[str] | None = None) -> LayoutValidationResult:
        errors: list[str] = []
        if not layout.layout_id:
            errors.append("layout_id_required")
        if layout.columns <= 0:
            errors.append("columns_must_be_positive")

        seen_widgets: set[str] = set()
        occupied: dict[tuple[int, int], str] = {}
        enabled = set(enabled_widgets or [])

        for position in layout.positions:
            errors.extend(f"{position.widget_id}:{error}" for error in position.validate(layout.columns))
            if position.widget_id in seen_widgets:
                errors.append(f"{position.widget_id}:duplicate_widget")
            seen_widgets.add(position.widget_id)
            if enabled and position.widget_id not in enabled:
                errors.append(f"{position.widget_id}:unknown_widget")
            for cell in position.cells():
                if cell in occupied:
                    errors.append(f"{position.widget_id}:overlaps:{occupied[cell]}")
                occupied[cell] = position.widget_id

        status = LayoutValidationStatus.VALID if not errors else LayoutValidationStatus.INVALID
        return LayoutValidationResult(status=status, errors=tuple(errors))


class DashboardLayoutPersistence:
    def __init__(self, config_dir: str | Path):
        self.config_dir = Path(config_dir)
        self.path = self.config_dir / "dashboard" / "layout.json"

    def save(self, layout: DashboardLayout) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(layout.to_dict(), indent=2, sort_keys=True), encoding="utf-8")

    def load(self) -> DashboardLayout:
        if not self.path.exists():
            return DashboardLayout()
        return DashboardLayout.from_dict(json.loads(self.path.read_text(encoding="utf-8")))


class DashboardLayoutService:
    def __init__(self, persistence: DashboardLayoutPersistence, validator: DashboardLayoutValidator | None = None):
        self.persistence = persistence
        self.validator = validator or DashboardLayoutValidator()
        self.layout = self.persistence.load()

    def place_widget(self, position: WidgetPosition, enabled_widgets: Iterable[str] | None = None) -> LayoutValidationResult:
        candidate = DashboardLayout(
            layout_id=self.layout.layout_id,
            columns=self.layout.columns,
            positions=list(self.layout.positions),
            metadata=dict(self.layout.metadata),
        )
        candidate.add_or_replace(position)
        result = self.validator.validate(candidate, enabled_widgets=enabled_widgets)
        if result.is_valid:
            self.layout = candidate
            self.persistence.save(self.layout)
        return result

    def remove_widget(self, widget_id: str) -> bool:
        removed = self.layout.remove(widget_id)
        if removed:
            self.persistence.save(self.layout)
        return removed

    def load_layout(self) -> DashboardLayout:
        self.layout = self.persistence.load()
        return self.layout
