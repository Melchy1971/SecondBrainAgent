"""Calendar assistant data model.

Times are ISO-8601 strings; helpers parse them into timezone-aware datetimes.
A naive (tz-less) time is treated as a timezone problem downstream.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, time, timezone
from enum import StrEnum
from typing import Any

__all__ = [
    "CalendarEvent", "CalendarAvailability", "FreeSlot", "Conflict", "ConflictType", "WorkingHours",
    "parse_dt", "to_utc",
]


class ConflictType(StrEnum):
    DIRECT_OVERLAP = "direct_overlap"
    SHORT_TRAVEL = "short_travel"
    MISSING_BUFFER = "missing_buffer"
    DOUBLE_BOOKING = "double_booking"
    WORKING_HOURS = "working_hours"
    FOCUS_TIME = "focus_time"
    TIMEZONE = "timezone"


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def to_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return None  # naive -> caller flags a timezone problem
    return dt.astimezone(timezone.utc)


@dataclass
class CalendarEvent:
    event_id: str
    calendar_id: str
    workspace_id: str
    title: str
    start: str
    end: str
    connector_id: str = ""
    description: str = ""
    timezone: str = "UTC"
    location: str = ""
    attendees: list[str] = field(default_factory=list)
    organizer: str = ""
    status: str = "confirmed"
    visibility: str = "default"
    recurrence: str = ""
    source: str = "connector"
    external_id: str = ""
    updated_at: str = ""
    source_updated_at: str = ""
    synced_at: str = ""
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CalendarEvent":
        return cls(**{k: data.get(k) for k in cls.__dataclass_fields__ if k in data})

    def start_dt(self) -> datetime | None:
        return parse_dt(self.start)

    def end_dt(self) -> datetime | None:
        return parse_dt(self.end)

    @property
    def start_at(self) -> str:
        return self.start

    @property
    def end_at(self) -> str:
        return self.end


@dataclass
class CalendarAvailability:
    date: str
    available_slots: list[dict[str, Any]] = field(default_factory=list)
    busy_slots: list[dict[str, Any]] = field(default_factory=list)
    focus_slots: list[dict[str, Any]] = field(default_factory=list)
    travel_blocks: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkingHours:
    start_hour: int = 9
    end_hour: int = 18
    workdays: tuple[int, ...] = (0, 1, 2, 3, 4)  # Mon..Fri
    lunch_start_hour: int | None = 12
    lunch_end_hour: int | None = 13

    def is_workday(self, dt: datetime) -> bool:
        return dt.weekday() in self.workdays

    def day_window(self, day_start_utc: datetime) -> tuple[datetime, datetime]:
        base = day_start_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        return (base.replace(hour=self.start_hour), base.replace(hour=self.end_hour))


@dataclass
class FreeSlot:
    start: str
    end: str
    duration_minutes: int
    score: float
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Conflict:
    type: str
    detail: str
    event_title: str = ""  # human reference, never an id

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
