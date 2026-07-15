"""Calendar GUI view model + HTML (day/week/conflicts/free-slots/preparation).

Main views never expose technical ids; each event item shows its source and
status. Proposed changes link to their approval id (that link is the only place
an id appears, for the approval hand-off).
"""

from __future__ import annotations

import html
from typing import Any, Sequence

from secondbrain.calendar_assistant.models import CalendarEvent, WorkingHours
from secondbrain.calendar_assistant.service import CalendarService

__all__ = ["CalendarViewModel", "MODULES"]

MODULES = ["Tagesansicht", "Wochenansicht", "Konflikte", "freie Zeitfenster", "Vorbereitung", "vorgeschlagene Änderungen"]


def _ev_item(ev: CalendarEvent) -> dict[str, Any]:
    return {
        "title": ev.title, "start": ev.start, "end": ev.end,
        "location": ev.location, "status": ev.status, "source": ev.source,
        "organizer": ev.organizer, "attendees_count": len(ev.attendees),
    }


class CalendarViewModel:
    def __init__(self, service: CalendarService | None = None) -> None:
        self.service = service or CalendarService()

    def day_view(self, events: Sequence[CalendarEvent], *, workspace_id: str, day: str) -> dict[str, Any]:
        summary = self.service.summarize_day(events, workspace_id=workspace_id, day=day)
        items = [_ev_item(e) for e in self.service.list_events(events, workspace_id=workspace_id)
                 if (e.start_dt() and e.start_dt().tzinfo and e.start_dt().date().isoformat() == summary["date"])]
        return {"date": summary["date"], "events": items, "summary": summary}

    def week_view(self, events: Sequence[CalendarEvent], *, workspace_id: str, week_start: str) -> dict[str, Any]:
        week = self.service.summarize_week(events, workspace_id=workspace_id, week_start=week_start)
        return {"week_start": week.get("week_start"), "total_events": week.get("total_events"), "days": week.get("days", [])}

    def conflicts_view(self, proposed: CalendarEvent, events: Sequence[CalendarEvent], **kwargs: Any) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.service.detect_conflicts(proposed, events, **kwargs)]

    def free_slots_view(self, events: Sequence[CalendarEvent], **kwargs: Any) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.service.find_free_slots(events, **kwargs)]

    def proposed_changes_view(self, prepared: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{"action": p.get("action"), "status": p.get("status"),
                 "approval_id": p.get("approval_id", ""), "expires_at": p.get("expires_at", "")}
                for p in prepared]

    def render_html(self, events: Sequence[CalendarEvent], *, workspace_id: str, day: str) -> str:
        e = html.escape
        dv = self.day_view(events, workspace_id=workspace_id, day=day)
        rows = "".join(
            f"<tr><td>{e(i['start'][11:16])}–{e(i['end'][11:16])}</td><td><b>{e(i['title'])}</b></td>"
            f"<td>{e(i['location'] or '—')}</td><td>{e(i['status'])}</td><td>{e(i['source'])}</td></tr>"
            for i in dv["events"]
        )
        return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Kalender - {e(dv['date'])}</title>
<style>
 body{{margin:0;background:#0a0e14;color:#d8ecf5;font:14px/1.5 system-ui,Segoe UI,sans-serif}}
 .wrap{{max-width:960px;margin:0 auto;padding:24px}} h1{{font-size:19px;margin:0 0 12px}}
 table{{width:100%;border-collapse:collapse;background:#0e141d;border:1px solid #1e2b3a;border-radius:10px;overflow:hidden}}
 th,td{{padding:9px 12px;text-align:left;border-bottom:1px solid #16202c}}
 th{{color:#8fb0c4;font-size:12px;text-transform:uppercase;background:#0c1621}}
</style></head><body><div class="wrap">
 <h1>KALENDER · {e(dv['date'])} · {dv['summary']['event_count']} Termine</h1>
 <table><thead><tr><th>Zeit</th><th>Titel</th><th>Ort</th><th>Status</th><th>Quelle</th></tr></thead>
 <tbody>{rows or '<tr><td colspan=5>keine Termine</td></tr>'}</tbody></table>
</div></body></html>"""
