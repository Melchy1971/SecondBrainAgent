from __future__ import annotations

from typing import Any

from secondbrain.desktop_app import DesktopAppRuntime

TASK_FILTERS = frozenset({"all", "open", "completed", "archived"})
_FILTER_LABELS = {
    "all": "ALLE",
    "open": "OFFEN",
    "completed": "ERLEDIGT",
    "archived": "ARCHIVIERT",
}


def _safe_text(value: Any, *, limit: int) -> str:
    printable = "".join(character if character.isprintable() else " " for character in str(value or ""))
    return " ".join(printable.split())[:limit]


class TaskSurface:
    """Root-local, bounded task projection for the native desktop view."""

    def __init__(self, runtime: DesktopAppRuntime, *, limit: int = 50) -> None:
        self.runtime = runtime
        self.limit = max(1, min(int(limit), 200))

    def snapshot(self, task_filter: str = "all") -> dict[str, Any]:
        selected_filter = str(task_filter or "all").strip().casefold()
        if selected_filter not in TASK_FILTERS:
            raise ValueError(f"unsupported task filter: {selected_filter}")
        try:
            raw_tasks = self.runtime.tasks()
        except Exception:
            return self._unavailable(selected_filter)
        if not isinstance(raw_tasks, list):
            return self._unavailable(selected_filter)
        tasks = [self._safe_item(task) for task in raw_tasks if isinstance(task, dict)]
        completed_count = sum(task["completed"] for task in tasks)
        archived_count = sum(task["archived"] for task in tasks)
        filtered_tasks = [task for task in tasks if self._matches_filter(task, selected_filter)]
        items = list(reversed(filtered_tasks[-self.limit :]))
        return {
            "status": "ready",
            "task_filter": selected_filter,
            "total": len(tasks),
            "open_count": len(tasks) - completed_count - archived_count,
            "completed_count": completed_count,
            "archived_count": archived_count,
            "filtered_count": len(filtered_tasks),
            "visible_count": len(items),
            "invalid_count": len(raw_tasks) - len(tasks),
            "items": items,
            "workspace_local": True,
        }

    @staticmethod
    def _matches_filter(task: dict[str, Any], task_filter: str) -> bool:
        if task_filter == "open":
            return not task["completed"] and not task["archived"]
        if task_filter == "completed":
            return task["completed"]
        if task_filter == "archived":
            return task["archived"]
        return True

    @staticmethod
    def _safe_item(task: dict[str, Any]) -> dict[str, Any]:
        column = _safe_text(task.get("column"), limit=32) or "backlog"
        return {
            "task_id": _safe_text(task.get("id"), limit=80),
            "title": _safe_text(task.get("title"), limit=200) or "Ohne Titel",
            "column": column,
            "priority": _safe_text(task.get("priority"), limit=16) or "medium",
            "created_at": _safe_text(task.get("created_at"), limit=48),
            "completed_at": _safe_text(task.get("completed_at"), limit=48),
            "completed": column.casefold() == "done",
            "archived": column.casefold() == "archived",
        }

    @staticmethod
    def _unavailable(task_filter: str = "all") -> dict[str, Any]:
        return {
            "status": "unavailable",
            "task_filter": task_filter,
            "total": 0,
            "open_count": 0,
            "completed_count": 0,
            "archived_count": 0,
            "filtered_count": 0,
            "visible_count": 0,
            "invalid_count": 0,
            "items": [],
            "workspace_local": True,
        }


def task_view_text(snapshot: dict[str, Any]) -> str:
    if snapshot.get("status") != "ready":
        return "TASKS · Daten derzeit nicht verfügbar"
    task_filter = str(snapshot.get("task_filter") or "all")
    lines = [
        (
            f"TASKS · {snapshot.get('open_count', 0)} offen · "
            f"{snapshot.get('completed_count', 0)} erledigt · "
            f"{snapshot.get('archived_count', 0)} archiviert · {snapshot.get('total', 0)} gesamt"
        ),
        f"FILTER: {_FILTER_LABELS.get(task_filter, 'ALLE')} · {snapshot.get('filtered_count', 0)} Treffer",
        "",
    ]
    items = snapshot.get("items") if isinstance(snapshot.get("items"), list) else []
    if not items:
        lines.append("Keine Aufgaben in diesem Filter vorhanden.")
    for task in items:
        if not isinstance(task, dict):
            continue
        marker = "-" if task.get("archived") else "x" if task.get("completed") else " "
        lines.append(f"- [{marker}] {task.get('title', 'Ohne Titel')} · {task.get('priority', 'medium')}")
        if task.get("task_id"):
            lines.append(f"  ID: {task['task_id']}")
    lines.extend([
        "",
        "Befehle:",
        "- Neue Aufgabe",
        "- Liste Aufgaben",
        "- Aufgabe abschließen",
        "- Aufgabe umbenennen",
        "- Aufgabe archivieren",
        "- Aufgabe wiederherstellen",
        "- Zeige alle Aufgaben",
        "- Zeige offene Aufgaben",
        "- Zeige erledigte Aufgaben",
        "- Zeige archivierte Aufgaben",
    ])
    return "\n".join(lines)
