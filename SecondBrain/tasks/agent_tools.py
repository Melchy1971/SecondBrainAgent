"""Agent-facing task tools.

The agent may propose, extract, and create tasks and query projects. Actions
with external side effects (delete, modifying external tasks, creating calendar
events, sending messages) never execute here - they return an
``approval_required`` result so the human decides. Every agent-created task is
tagged ``source=agent`` with a confidence and leaves an audit event.
"""

from __future__ import annotations

import re
from typing import Any

from secondbrain.tasks.models import Priority, Status
from secondbrain.tasks.service import TaskProjectService

__all__ = ["TaskAgentTools"]

_ACTION_LINE = re.compile(r"^\s*(?:[-*]\s*)?(?:TODO|TASK|AUFGABE|ACTION|[-*])\s*[:\-]?\s*(.+)$", re.IGNORECASE)


def _task_view(task) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "source": task.source,
        "source_reference": task.source_reference,
        "confidence": task.confidence,
    }


class TaskAgentTools:
    def __init__(self, service: TaskProjectService, *, actor: str = "agent") -> None:
        self.service = service
        self.actor = actor

    # -- allowed create/update -------------------------------------------

    def task_create(self, *, workspace_id: str, title: str, project_id: str | None = None,
                    priority: str = Priority.NORMAL.value, due_date: str | None = None,
                    source_reference: str = "", confidence: float = 0.7) -> dict[str, Any]:
        task = self.service.create_task(
            workspace_id=workspace_id, title=title, project_id=project_id, actor=self.actor,
            status=Status.INBOX.value, priority=priority, due_date=due_date,
            source="agent", source_reference=source_reference, confidence=float(confidence),
        )
        return {"ok": True, **_task_view(task)}

    def task_update(self, task_id: str, *, workspace_id: str, **changes: Any) -> dict[str, Any]:
        task = self.service.update_task(task_id, workspace_id=workspace_id, actor=self.actor, **changes)
        return {"ok": True, **_task_view(task)}

    def task_complete(self, task_id: str, *, workspace_id: str) -> dict[str, Any]:
        return {"ok": True, **_task_view(self.service.complete_task(task_id, workspace_id=workspace_id, actor=self.actor))}

    def task_defer(self, task_id: str, *, workspace_id: str, due_date: str | None = None) -> dict[str, Any]:
        return {"ok": True, **_task_view(self.service.defer_task(task_id, workspace_id=workspace_id, due_date=due_date, actor=self.actor))}

    # -- approval-gated ---------------------------------------------------

    def task_delete(self, task_id: str, *, workspace_id: str) -> dict[str, Any]:
        # Agent can never pass approved=True; delete always routes to approval.
        result = self.service.delete_task(task_id, workspace_id=workspace_id, actor=self.actor)
        return {"ok": False, "requires_approval": True, **result}

    def modify_external_task(self, task_id: str, *, workspace_id: str, **_changes: Any) -> dict[str, Any]:
        return {"ok": False, "requires_approval": True, "reason": "external_task_change_needs_approval", "task_id": task_id}

    def create_calendar_event_from_task(self, task_id: str, *, workspace_id: str) -> dict[str, Any]:
        return {"ok": False, "requires_approval": True, "reason": "calendar_event_needs_approval", "task_id": task_id}

    def send_message(self, *, workspace_id: str, **_payload: Any) -> dict[str, Any]:
        return {"ok": False, "requires_approval": True, "reason": "sending_needs_approval"}

    # -- projects ---------------------------------------------------------

    def project_create(self, *, workspace_id: str, title: str, **fields: Any) -> dict[str, Any]:
        project = self.service.create_project(workspace_id=workspace_id, title=title, actor=self.actor, source="agent", **fields)
        return {"ok": True, "project_id": project.project_id, "title": project.title, "status": project.status}

    def project_status(self, project_id: str, *, workspace_id: str) -> dict[str, Any]:
        projects = {p.project_id: p for p in self.service.list_projects(workspace_id=workspace_id, include_archived=True)}
        p = projects.get(project_id)
        if p is None:
            return {"ok": False, "error": "project_not_found"}
        tasks = self.service.list_tasks(workspace_id=workspace_id, project_id=project_id)
        return {"ok": True, "title": p.title, "status": p.status, "progress": p.progress,
                "open": sum(1 for t in tasks if t.status not in {"completed", "cancelled", "archived"}),
                "total": len(tasks)}

    def project_summary(self, project_id: str, *, workspace_id: str) -> dict[str, Any]:
        status = self.project_status(project_id, workspace_id=workspace_id)
        if not status.get("ok"):
            return status
        blocked = [t.title for t in self.service.get_blocked(workspace_id=workspace_id) if t.project_id == project_id]
        overdue = [t.title for t in self.service.get_overdue(workspace_id=workspace_id) if t.project_id == project_id]
        return {**status, "blocked": blocked, "overdue": overdue}

    # -- suggestions / extraction (proposals only) ------------------------

    def suggest_task(self, *, workspace_id: str, title: str, source_reference: str = "",
                     confidence: float = 0.6, priority: str | None = None, due_date: str | None = None) -> dict[str, Any]:
        """Store a proposal as an inbox task tagged as an agent suggestion (auditable)."""

        return self.task_create(
            workspace_id=workspace_id, title=title, source_reference=source_reference,
            confidence=confidence, priority=priority or Priority.NORMAL.value, due_date=due_date,
        )

    def extract_tasks(self, text: str, *, workspace_id: str, source_reference: str, confidence: float = 0.6) -> list[dict[str, Any]]:
        proposals: list[dict[str, Any]] = []
        for line in (text or "").splitlines():
            m = _ACTION_LINE.match(line)
            if m and m.group(1).strip():
                proposals.append(self.suggest_task(
                    workspace_id=workspace_id, title=m.group(1).strip()[:200],
                    source_reference=source_reference, confidence=confidence,
                ))
        return proposals
