"""Task/project GUI view model + HTML render.

Main views (list, kanban, today, overdue, blocked, project overview) never
expose technical ids - items carry human fields only. The detail view may carry
the id for interaction. A self-contained HTML page renders the list + kanban.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any

from secondbrain.tasks.models import Priority, Status
from secondbrain.tasks.service import TaskProjectService

__all__ = ["TaskViewModel", "MODULES", "KANBAN_COLUMNS"]

MODULES = ["Aufgaben", "Projekte", "Heute", "Überfällig", "Blockiert"]
KANBAN_COLUMNS = [Status.INBOX.value, Status.PLANNED.value, Status.ACTIVE.value,
                  Status.BLOCKED.value, Status.WAITING.value, Status.COMPLETED.value]
_PRIO_RANK = {Priority.CRITICAL.value: 0, Priority.HIGH.value: 1, Priority.NORMAL.value: 2, Priority.LOW.value: 3}


def _parse(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        p = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return p.replace(tzinfo=timezone.utc) if p.tzinfo is None else p


class TaskViewModel:
    def __init__(self, service: TaskProjectService) -> None:
        self.service = service

    # -- main-view item (NO technical ids) --------------------------------

    def _item(self, task, *, project_title: str = "", overdue: bool = False) -> dict[str, Any]:
        return {
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date,
            "assignee": task.assignee,
            "source": task.source,
            "source_reference": task.source_reference,  # for "Quellenbezug öffnen"
            "project": project_title,
            "overdue": overdue,
        }

    def _project_titles(self, workspace_id: str) -> dict[str, str]:
        return {p.project_id: p.title for p in self.service.list_projects(workspace_id=workspace_id, include_archived=True)}

    def module_list(self, workspace_id: str, *, status: str | None = None,
                    query: str = "", sort: str = "priority") -> list[dict[str, Any]]:
        titles = self._project_titles(workspace_id)
        overdue_ids = {t.task_id for t in self.service.get_overdue(workspace_id=workspace_id)}
        items = []
        for t in self.service.list_tasks(workspace_id=workspace_id, status=status):
            if query and query.lower() not in t.title.lower():
                continue
            items.append((t, self._item(t, project_title=titles.get(t.project_id, ""), overdue=t.task_id in overdue_ids)))
        if sort == "priority":
            items.sort(key=lambda pair: (_PRIO_RANK.get(pair[0].priority, 2), _parse(pair[0].due_date) or datetime.max.replace(tzinfo=timezone.utc)))
        elif sort == "due_date":
            items.sort(key=lambda pair: _parse(pair[0].due_date) or datetime.max.replace(tzinfo=timezone.utc))
        return [view for _, view in items]

    def module_kanban(self, workspace_id: str) -> dict[str, list[dict[str, Any]]]:
        columns: dict[str, list[dict[str, Any]]] = {c: [] for c in KANBAN_COLUMNS}
        for item in self.module_list(workspace_id):
            columns.setdefault(item["status"], []).append(item)
        return columns

    def module_today(self, workspace_id: str, *, now: datetime | None = None) -> list[dict[str, Any]]:
        titles = self._project_titles(workspace_id)
        return [self._item(t, project_title=titles.get(t.project_id, "")) for t in self.service.get_today(workspace_id=workspace_id, now=now)]

    def module_overdue(self, workspace_id: str, *, now: datetime | None = None) -> list[dict[str, Any]]:
        titles = self._project_titles(workspace_id)
        return [self._item(t, project_title=titles.get(t.project_id, ""), overdue=True) for t in self.service.get_overdue(workspace_id=workspace_id, now=now)]

    def module_blocked(self, workspace_id: str) -> list[dict[str, Any]]:
        titles = self._project_titles(workspace_id)
        return [self._item(t, project_title=titles.get(t.project_id, "")) for t in self.service.get_blocked(workspace_id=workspace_id)]

    def project_overview(self, workspace_id: str) -> list[dict[str, Any]]:
        out = []
        for p in self.service.list_projects(workspace_id=workspace_id):
            tasks = self.service.list_tasks(workspace_id=workspace_id, project_id=p.project_id)
            out.append({
                "title": p.title, "status": p.status, "priority": p.priority, "progress": p.progress,
                "owner": p.owner, "due_date": p.due_date,
                "open": sum(1 for t in tasks if t.status not in {"completed", "cancelled", "archived"}),
                "total": len(tasks),
            })
        return out

    def calendar_view(self, workspace_id: str) -> dict[str, list[dict[str, Any]]]:
        titles = self._project_titles(workspace_id)
        by_day: dict[str, list[dict[str, Any]]] = {}
        for t in self.service.list_tasks(workspace_id=workspace_id):
            due = _parse(t.due_date)
            if due is not None:
                by_day.setdefault(due.date().isoformat(), []).append(self._item(t, project_title=titles.get(t.project_id, "")))
        return dict(sorted(by_day.items()))

    def dependency_view(self, workspace_id: str) -> list[dict[str, str]]:
        by_id = {t.task_id: t.title for t in self.service.list_tasks(workspace_id=workspace_id)}
        edges = []
        for d in self.service._read("dependencies"):  # noqa: SLF001
            if d.get("workspace_id") == workspace_id:
                edges.append({
                    "predecessor": by_id.get(str(d.get("predecessor_id")), "?"),
                    "successor": by_id.get(str(d.get("successor_id")), "?"),
                    "type": d.get("dependency_type", ""),
                })
        return edges

    def detail(self, task_id: str, *, workspace_id: str) -> dict[str, Any] | None:
        task = self.service.get_task(task_id, workspace_id=workspace_id)
        return task.to_dict() if task else None  # detail view may include the id

    def snapshot(self, workspace_id: str) -> dict[str, Any]:
        return {
            "modules": MODULES,
            "today": self.module_today(workspace_id),
            "overdue": self.module_overdue(workspace_id),
            "blocked": self.module_blocked(workspace_id),
            "projects": self.project_overview(workspace_id),
            "counts": {
                "open": len(self.service.list_tasks(workspace_id=workspace_id)),
                "overdue": len(self.service.get_overdue(workspace_id=workspace_id)),
                "blocked": len(self.service.get_blocked(workspace_id=workspace_id)),
            },
        }

    # -- HTML (no technical ids) ------------------------------------------

    def render_html(self, workspace_id: str) -> str:
        e = html.escape
        kanban = self.module_kanban(workspace_id)
        cols = []
        for col in KANBAN_COLUMNS:
            cards = "".join(
                f"<div class='card'><div class='t'>{e(i['title'])}</div>"
                f"<div class='m'>{e(i['priority'])}{' · ' + e(i['project']) if i['project'] else ''}"
                f"{' · ' + e(i['due_date']) if i['due_date'] else ''}</div></div>"
                for i in kanban.get(col, [])
            )
            cols.append(f"<div class='col'><div class='ch'>{e(col)} ({len(kanban.get(col, []))})</div>{cards}</div>")
        overdue = "".join(f"<li>{e(i['title'])} <span class='od'>überfällig</span></li>" for i in self.module_overdue(workspace_id))
        return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aufgaben & Projekte</title>
<style>
 body{{margin:0;background:#0a0e14;color:#d8ecf5;font:14px/1.5 system-ui,Segoe UI,sans-serif}}
 .wrap{{max-width:1200px;margin:0 auto;padding:24px}} h1{{font-size:19px;margin:0 0 14px}}
 .board{{display:flex;gap:12px;overflow-x:auto}} .col{{flex:1;min-width:180px;background:#0e141d;border:1px solid #1e2b3a;border-radius:10px;padding:10px}}
 .ch{{color:#8fb0c4;font-size:12px;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px}}
 .card{{background:#111823;border:1px solid #1e2b3a;border-radius:8px;padding:9px;margin-bottom:8px}}
 .card .t{{font-weight:600}} .card .m{{color:#6d8497;font-size:12px}}
 ul{{list-style:none;padding:0}} li{{padding:6px 0;border-bottom:1px solid #16202c}} .od{{color:#ff5c5c;font-size:12px}}
 h2{{font-size:14px;color:#8fb0c4;margin:22px 0 8px;text-transform:uppercase;letter-spacing:.06em}}
</style></head>
<body><div class="wrap">
 <h1>AUFGABEN & PROJEKTE</h1>
 <h2>Kanban</h2><div class="board">{''.join(cols)}</div>
 <h2>Überfällig</h2><ul>{overdue or '<li>keine</li>'}</ul>
</div></body></html>"""
