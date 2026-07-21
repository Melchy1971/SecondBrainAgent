from __future__ import annotations

from typing import Any

from secondbrain.desktop_app import DesktopAppRuntime


def _safe_text(value: Any, *, limit: int) -> str:
    printable = "".join(character if character.isprintable() else " " for character in str(value or ""))
    return " ".join(printable.split())[:limit]


class TaskSurface:
    """Root-local, bounded task projection for the native desktop view."""

    def __init__(self, runtime: DesktopAppRuntime, *, limit: int = 50) -> None:
        self.runtime = runtime
        self.limit = max(1, min(int(limit), 200))

    def snapshot(self) -> dict[str, Any]:
        try:
            raw_tasks = self.runtime.tasks()
        except Exception:
            return self._unavailable()
        if not isinstance(raw_tasks, list):
            return self._unavailable()
        tasks = [self._safe_item(task) for task in raw_tasks if isinstance(task, dict)]
        completed_count = sum(task["completed"] for task in tasks)
        archived_count = sum(task["archived"] for task in tasks)
        items = list(reversed(tasks[-self.limit :]))
        return {
            "status": "ready",
            "total": len(tasks),
            "open_count": len(tasks) - completed_count - archived_count,
            "completed_count": completed_count,
            "archived_count": archived_count,
            "visible_count": len(items),
            "invalid_count": len(raw_tasks) - len(tasks),
            "items": items,
            "workspace_local": True,
        }

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
    def _unavailable() -> dict[str, Any]:
        return {
            "status": "unavailable",
            "total": 0,
            "open_count": 0,
            "completed_count": 0,
            "archived_count": 0,
            "visible_count": 0,
            "invalid_count": 0,
            "items": [],
            "workspace_local": True,
        }


def task_view_text(snapshot: dict[str, Any]) -> str:
    if snapshot.get("status") != "ready":
        return "TASKS · Daten derzeit nicht verfügbar"
    lines = [
        (
            f"TASKS · {snapshot.get('open_count', 0)} offen · "
            f"{snapshot.get('completed_count', 0)} erledigt · "
            f"{snapshot.get('archived_count', 0)} archiviert · {snapshot.get('total', 0)} gesamt"
        ),
        "",
    ]
    items = snapshot.get("items") if isinstance(snapshot.get("items"), list) else []
    if not items:
        lines.append("Keine Aufgaben vorhanden.")
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
    ])
    return "\n".join(lines)
