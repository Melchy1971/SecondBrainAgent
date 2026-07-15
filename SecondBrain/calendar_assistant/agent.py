"""Agent-facing calendar functions (natural-language intents).

Read intents return data directly; anything that would change the calendar
returns an approval-required proposal via the service (never executed here).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence

from secondbrain.calendar_assistant.models import CalendarEvent, WorkingHours
from secondbrain.calendar_assistant.service import CalendarService

__all__ = ["CalendarAgent"]


class CalendarAgent:
    def __init__(self, service: CalendarService | None = None) -> None:
        self.service = service or CalendarService()

    def whats_today(self, events: Sequence[CalendarEvent], *, workspace_id: str, now: datetime | None = None) -> dict[str, Any]:
        moment = now or datetime.now(timezone.utc)
        return {"intent": "today", **self.service.summarize_day(events, workspace_id=workspace_id, day=moment.isoformat())}

    def when_free(self, events: Sequence[CalendarEvent], *, workspace_id: str, duration_minutes: int,
                  period_start: str, period_end: str, working_hours: WorkingHours | None = None) -> dict[str, Any]:
        slots = self.service.find_free_slots(events, period_start=period_start, period_end=period_end,
                                             duration_minutes=duration_minutes, working_hours=working_hours, workspace_id=workspace_id)
        return {"intent": "free_slots", "duration_minutes": duration_minutes,
                "candidates": [s.to_dict() for s in slots], "best": slots[0].to_dict() if slots else None}

    def prepare_next_meeting(self, events: Sequence[CalendarEvent], *, workspace_id: str, now: datetime | None = None) -> dict[str, Any]:
        moment = now or datetime.now(timezone.utc)
        upcoming = [e for e in self.service.list_events(events, workspace_id=workspace_id)
                    if (e.start_dt() and e.start_dt().tzinfo and e.start_dt() > moment)]
        if not upcoming:
            return {"intent": "prepare", "status": "no_upcoming"}
        nxt = upcoming[0]
        return {"intent": "prepare", "status": "ok", "title": nxt.title, "start": nxt.start,
                "location": nxt.location, "attendees": nxt.attendees, "organizer": nxt.organizer,
                "preparation": [
                    f"Teilnehmer: {', '.join(nxt.attendees) or 'keine'}",
                    f"Ort: {nxt.location or 'nicht angegeben'}",
                    "Agenda und offene Punkte prüfen",
                ], "source_reference": nxt.external_id or nxt.event_id}

    def move_event(self, event_id: str, *, workspace_id: str, new_start: str, new_end: str,
                   approval_queue: Any | None = None) -> dict[str, Any]:
        return {"intent": "move_event", **self.service.prepare_change(
            "move_event", {"event_id": event_id, "start": new_start, "end": new_end},
            workspace_id=workspace_id, approval_queue=approval_queue)}

    def plan_focus_time(self, events: Sequence[CalendarEvent], *, workspace_id: str, minutes: int,
                        period_start: str, period_end: str, working_hours: WorkingHours | None = None,
                        approval_queue: Any | None = None) -> dict[str, Any]:
        blocks = self.service.calculate_focus_blocks(events, period_start=period_start, period_end=period_end,
                                                     working_hours=working_hours, min_minutes=minutes, workspace_id=workspace_id)
        if not blocks:
            return {"intent": "focus_time", "status": "no_block"}
        best = blocks[0]
        prepared = self.service.prepare_change(
            "create_focus_time", {"event_id": "", "title": "Fokuszeit", "start": best.start, "end": best.end},
            workspace_id=workspace_id, approval_queue=approval_queue)
        return {"intent": "focus_time", "status": "proposed", "slot": best.to_dict(), "approval": prepared}
