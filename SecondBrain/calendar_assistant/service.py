"""Calendar assistant service.

Read-only functions (list/get/free-slots/conflicts/focus/travel/summaries) never
require approval. Write functions never touch the calendar directly: they prepare
an approval bound to the event id, a payload hash, the workspace and an expiry.
``commit_change`` only executes when the approval is granted, unexpired, the
payload hash still matches, and it has not run before (exactly once). An offline
connector yields a controlled error, never data loss.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4
from typing import Any, Sequence

from secondbrain.calendar_assistant.models import (
    CalendarEvent,
    Conflict,
    ConflictType,
    FreeSlot,
    WorkingHours,
    parse_dt,
)

__all__ = ["CalendarService", "CalendarConnectorError", "WRITE_ACTIONS", "READ_ACTIONS"]

READ_ACTIONS = ["list_events", "get_event", "find_free_slots", "detect_conflicts",
                "calculate_focus_blocks", "calculate_travel_buffers", "summarize_day", "summarize_week"]
WRITE_ACTIONS = ["create_event", "update_event", "cancel_event", "invite_attendees",
                 "change_attendees", "move_event", "create_focus_time"]


class CalendarConnectorError(RuntimeError):
    pass


def _utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc)


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def _event_bounds(ev: CalendarEvent) -> tuple[datetime, datetime] | None:
    s, e = ev.start_dt(), ev.end_dt()
    if s is None or e is None or s.tzinfo is None or e.tzinfo is None:
        return None
    return (_utc(s), _utc(e))


class CalendarService:
    def __init__(self, connector: Any | None = None) -> None:
        self.connector = connector
        self._committed: set[str] = set()

    # -- read-only --------------------------------------------------------

    def list_events(self, events: Sequence[CalendarEvent], *, workspace_id: str,
                    period_start: str | None = None, period_end: str | None = None) -> list[CalendarEvent]:
        ps = parse_dt(period_start)
        pe = parse_dt(period_end)
        out = []
        for ev in events:
            if ev.workspace_id != workspace_id:
                continue
            b = _event_bounds(ev)
            if b and ps and pe and not _overlaps(b[0], b[1], _utc(ps), _utc(pe)):
                continue
            out.append(ev)
        return sorted(out, key=lambda e: e.start)

    def list_calendars(self, events: Sequence[CalendarEvent], *, workspace_id: str) -> list[str]:
        return sorted({event.calendar_id for event in events if event.workspace_id == workspace_id})

    def get_today(self, events: Sequence[CalendarEvent], *, workspace_id: str, now: datetime | None = None) -> list[CalendarEvent]:
        moment = now or datetime.now(timezone.utc)
        return [event for event in self.list_events(events, workspace_id=workspace_id)
                if (bounds := _event_bounds(event)) is not None and bounds[0].date() == _utc(moment).date()]

    def get_week(self, events: Sequence[CalendarEvent], *, workspace_id: str, week_start: str) -> list[CalendarEvent]:
        start = parse_dt(week_start)
        if start is None or start.tzinfo is None:
            return []
        start = _utc(start)
        return self.list_events(events, workspace_id=workspace_id, period_start=start.isoformat(),
                                period_end=(start + timedelta(days=7)).isoformat())

    def get_next_event(self, events: Sequence[CalendarEvent], *, workspace_id: str, now: datetime | None = None) -> CalendarEvent | None:
        moment = _utc(now or datetime.now(timezone.utc))
        return next((event for event in self.list_events(events, workspace_id=workspace_id)
                     if (start := event.start_dt()) is not None and start.tzinfo is not None and _utc(start) >= moment), None)

    def get_event_preparation(self, event: CalendarEvent) -> dict[str, Any]:
        return {"title": event.title, "start_at": event.start, "location": event.location,
                "attendees": list(event.attendees), "source_reference": event.external_id or event.event_id,
                "suggestion_only": True}

    def get_event(self, events: Sequence[CalendarEvent], event_id: str, *, workspace_id: str) -> CalendarEvent | None:
        for ev in events:
            if ev.event_id == event_id and ev.workspace_id == workspace_id:
                return ev
        return None

    def detect_conflicts(
        self, proposed: CalendarEvent, events: Sequence[CalendarEvent], *,
        working_hours: WorkingHours | None = None, travel_minutes: int = 0,
        buffer_minutes: int = 0, focus_blocks: Sequence[tuple[str, str]] | None = None,
    ) -> list[Conflict]:
        conflicts: list[Conflict] = []
        ps, pe = proposed.start_dt(), proposed.end_dt()
        if ps is None or pe is None or ps.tzinfo is None or pe.tzinfo is None:
            conflicts.append(Conflict(ConflictType.TIMEZONE.value, "Start/Ende ohne Zeitzone", proposed.title))
            return conflicts
        ps, pe = _utc(ps), _utc(pe)
        wh = working_hours
        if wh is not None:
            if not wh.is_workday(ps):
                conflicts.append(Conflict(ConflictType.WORKING_HOURS.value, "ausserhalb Arbeitstage", proposed.title))
            elif not (wh.start_hour <= ps.hour and pe.hour <= wh.end_hour and (pe.hour < wh.end_hour or pe.minute == 0)):
                conflicts.append(Conflict(ConflictType.WORKING_HOURS.value, "ausserhalb Arbeitszeit", proposed.title))
        for ev in events:
            if ev.workspace_id != proposed.workspace_id or ev.event_id == proposed.event_id:
                continue
            b = _event_bounds(ev)
            if b is None:
                continue
            es, ee = b
            if _overlaps(ps, pe, es, ee):
                same_people = bool(set(proposed.attendees) & set(ev.attendees)) or bool(proposed.organizer and proposed.organizer == ev.organizer)
                ctype = ConflictType.DOUBLE_BOOKING if (same_people or (ps == es and pe == ee)) else ConflictType.DIRECT_OVERLAP
                conflicts.append(Conflict(ctype.value, f"überschneidet '{ev.title}'", ev.title))
                continue
            gap = (es - pe).total_seconds() / 60 if es >= pe else (ps - ee).total_seconds() / 60
            if 0 <= gap < travel_minutes:
                conflicts.append(Conflict(ConflictType.SHORT_TRAVEL.value, f"nur {int(gap)}min Reisezeit zu '{ev.title}'", ev.title))
            elif travel_minutes <= gap < buffer_minutes:
                conflicts.append(Conflict(ConflictType.MISSING_BUFFER.value, f"nur {int(gap)}min Puffer zu '{ev.title}'", ev.title))
        for fb in focus_blocks or []:
            fs, fe = parse_dt(fb[0]), parse_dt(fb[1])
            if fs and fe and fs.tzinfo and fe.tzinfo and _overlaps(ps, pe, _utc(fs), _utc(fe)):
                conflicts.append(Conflict(ConflictType.FOCUS_TIME.value, "überschneidet Fokuszeit", proposed.title))
        return conflicts

    def find_free_slots(
        self, events: Sequence[CalendarEvent], *, period_start: str, period_end: str, duration_minutes: int,
        working_hours: WorkingHours | None = None, travel_minutes: int = 0, buffer_minutes: int = 0,
        max_candidates: int = 10, workspace_id: str | None = None,
    ) -> list[FreeSlot]:
        ps, pe = parse_dt(period_start), parse_dt(period_end)
        if ps is None or pe is None or ps.tzinfo is None or pe.tzinfo is None:
            return []
        ps, pe = _utc(ps), _utc(pe)
        wh = working_hours or WorkingHours()
        pad = timedelta(minutes=max(travel_minutes, buffer_minutes))
        busy: list[tuple[datetime, datetime]] = []
        for ev in events:
            if workspace_id and ev.workspace_id != workspace_id:
                continue
            b = _event_bounds(ev)
            if b:
                busy.append((b[0] - pad, b[1] + pad))
        busy.sort()

        slots: list[FreeSlot] = []
        day = ps.replace(hour=0, minute=0, second=0, microsecond=0)
        while day <= pe:
            if wh.is_workday(day):
                w_start, w_end = wh.day_window(day)
                # working window intersected with the requested period
                cur = max(w_start, ps)
                windows = [(cur, min(w_end, pe))]
                if wh.lunch_start_hour is not None:
                    windows = _subtract(windows, (day.replace(hour=wh.lunch_start_hour), day.replace(hour=wh.lunch_end_hour or wh.lunch_start_hour + 1)))
                for b0, b1 in busy:
                    windows = _subtract(windows, (b0, b1))
                for f0, f1 in windows:
                    length = (f1 - f0).total_seconds() / 60
                    if length >= duration_minutes:
                        end = f0 + timedelta(minutes=duration_minutes)
                        score = round(max(0.1, 1.0 - (f0.hour - wh.start_hour) / max(1, (wh.end_hour - wh.start_hour)) * 0.5), 3)
                        slots.append(FreeSlot(f0.isoformat(), end.isoformat(), duration_minutes, score,
                                              reason=f"freies Fenster {int(length)}min ab {f0.strftime('%H:%M')}"))
            day += timedelta(days=1)
        slots.sort(key=lambda s: (-s.score, s.start))
        return slots[:max_candidates]

    def calculate_focus_blocks(self, events, *, period_start, period_end, working_hours=None, min_minutes=60, workspace_id=None):
        return self.find_free_slots(events, period_start=period_start, period_end=period_end,
                                    duration_minutes=min_minutes, working_hours=working_hours, workspace_id=workspace_id)

    def calculate_travel_buffers(self, events: Sequence[CalendarEvent], *, workspace_id: str, default_travel_minutes: int = 30) -> list[dict[str, Any]]:
        ordered = self.list_events(events, workspace_id=workspace_id)
        out = []
        for prev, nxt in zip(ordered, ordered[1:]):
            bp, bn = _event_bounds(prev), _event_bounds(nxt)
            if not bp or not bn:
                continue
            gap = (bn[0] - bp[1]).total_seconds() / 60
            needs = bool(prev.location and nxt.location and prev.location != nxt.location)
            out.append({"from": prev.title, "to": nxt.title, "gap_minutes": int(gap),
                        "travel_needed": needs, "sufficient": (not needs) or gap >= default_travel_minutes})
        return out

    def summarize_day(self, events: Sequence[CalendarEvent], *, workspace_id: str, day: str) -> dict[str, Any]:
        d = parse_dt(day) or datetime.now(timezone.utc)
        target = _utc(d).date() if d.tzinfo else d.date()
        todays = [e for e in self.list_events(events, workspace_id=workspace_id)
                  if (_event_bounds(e) or (None,))[0] and _event_bounds(e)[0].date() == target]
        busy_min = sum(int((_event_bounds(e)[1] - _event_bounds(e)[0]).total_seconds() / 60) for e in todays)
        return {"date": target.isoformat(), "event_count": len(todays), "busy_minutes": busy_min,
                "titles": [e.title for e in todays],
                "first": todays[0].start if todays else None, "last": todays[-1].end if todays else None}

    def summarize_week(self, events: Sequence[CalendarEvent], *, workspace_id: str, week_start: str) -> dict[str, Any]:
        ws = parse_dt(week_start)
        if ws is None or ws.tzinfo is None:
            return {"error": "invalid_week_start"}
        ws = _utc(ws)
        days = [self.summarize_day(events, workspace_id=workspace_id, day=(ws + timedelta(days=i)).isoformat()) for i in range(7)]
        return {"week_start": ws.date().isoformat(), "total_events": sum(d["event_count"] for d in days),
                "total_busy_minutes": sum(d["busy_minutes"] for d in days), "days": days}

    # -- write with approval ----------------------------------------------

    @staticmethod
    def _payload_hash(payload: dict[str, Any]) -> str:
        return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    def prepare_change(self, action: str, payload: dict[str, Any], *, workspace_id: str,
                       connector_id: str = "", actor: str = "user",
                       ttl_minutes: int = 30, approval_queue: Any | None = None, now: datetime | None = None) -> dict[str, Any]:
        if action not in WRITE_ACTIONS:
            raise ValueError(f"unknown_write_action:{action}")
        moment = now or datetime.now(timezone.utc)
        payload_hash = self._payload_hash(payload)
        expires_at = (moment + timedelta(minutes=ttl_minutes)).isoformat(timespec="seconds")
        event_id = str(payload.get("event_id") or "")
        attendees = payload.get("attendees") or []
        attendee_hash = sha256(json.dumps(attendees, sort_keys=True).encode("utf-8")).hexdigest()
        idempotency_key = uuid4().hex
        bound = {"action": action, "action_type": action, "event_id": event_id,
                 "external_event_id": str(payload.get("external_id") or event_id),
                 "connector_id": connector_id, "workspace_id": workspace_id,
                 "payload_hash": payload_hash, "attendee_hash": attendee_hash,
                 "start_at": payload.get("start") or payload.get("start_at"),
                 "end_at": payload.get("end") or payload.get("end_at"),
                 "expires_at": expires_at, "actor": actor, "idempotency_key": idempotency_key}
        approval_id = ""
        if approval_queue is not None:
            try:
                approval = approval_queue.create(
                    command=f"calendar.{action}", intent=action,
                    text=f"Calendar {action}: {payload.get('title', event_id)}",
                    target=event_id, category="connector_permission_change", risk_level="high",
                    tool_name=f"calendar.{action}", workspace_id=workspace_id,
                    payload={k: v for k, v in bound.items()},
                    idempotency_key=idempotency_key,
                )
                approval_id = str(approval.get("approval_id") or "")
            except Exception:  # noqa: BLE001
                approval_id = ""
        return {"status": "approval_required", "approval_id": approval_id, **bound}

    def commit_change(self, prepared: dict[str, Any], payload: dict[str, Any], *, approval_queue: Any,
                      workspace_id: str, now: datetime | None = None) -> dict[str, Any]:
        moment = now or datetime.now(timezone.utc)
        approval_id = str(prepared.get("approval_id") or prepared.get("payload_hash"))
        if not approval_id or approval_queue is None:
            return {"status": "blocked", "reason": "approval_required"}
        if workspace_id != prepared.get("workspace_id"):
            return {"status": "blocked", "reason": "workspace_mismatch"}
        if self._payload_hash(payload) != prepared.get("payload_hash"):
            return {"status": "invalid", "reason": "payload_changed"}
        exp = parse_dt(prepared.get("expires_at"))
        if exp is not None and moment > exp:
            return {"status": "expired", "reason": "approval_expired"}
        if approval_id in self._committed:
            return {"status": "duplicate", "reason": "already_committed"}
        try:
            approval_queue.begin_execution(approval_id, executor_id="calendar-assistant",
                                           idempotency_key=str(prepared.get("idempotency_key") or ""))
        except Exception as exc:  # approval service is the authority; booleans are never accepted
            return {"status": "blocked", "reason": f"approval_not_executable:{type(exc).__name__}"}
        # Execute against the connector (offline -> controlled error, no data loss).
        if self.connector is None:
            return {"status": "no_connector", "reason": "connector_not_configured"}
        method = getattr(self.connector, prepared.get("action", ""), None)
        if method is None:
            return {"status": "unsupported", "reason": prepared.get("action")}
        try:
            result = method(payload)
        except CalendarConnectorError as exc:
            return {"status": "connector_offline", "reason": str(exc)}
        except Exception as exc:  # noqa: BLE001
            return {"status": "error", "reason": f"{type(exc).__name__}: {exc}"}
        self._committed.add(approval_id)
        return {"status": "committed", "result": result}

    def link_task(self, task_id: str, event: CalendarEvent, *, workspace_id: str) -> dict[str, Any]:
        if event.workspace_id != workspace_id:
            return {"status": "blocked", "reason": "workspace_mismatch"}
        return {"status": "proposed", "task_id": task_id, "event_reference": event.external_id or event.event_id,
                "workspace_id": workspace_id, "requires_user_decision": True}


def _subtract(windows: list[tuple[datetime, datetime]], busy: tuple[datetime, datetime]) -> list[tuple[datetime, datetime]]:
    b0, b1 = busy
    out: list[tuple[datetime, datetime]] = []
    for w0, w1 in windows:
        if b1 <= w0 or b0 >= w1:
            out.append((w0, w1))
            continue
        if b0 > w0:
            out.append((w0, min(b0, w1)))
        if b1 < w1:
            out.append((max(b1, w0), w1))
    return [(a, b) for a, b in out if b > a]
