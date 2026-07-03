"""v30.49 task integration over existing agent, queue and approval stores."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from secondbrain.native.agent_control_center import AgentControlCenter
from secondbrain.native.approval import NativeApprovalQueue
from secondbrain.native.job_queue_center.service import JobQueueService


class TaskWorkspaceService:
    """One view over existing task, job, approval and history components."""

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root).resolve()
        self.tasks_service = AgentControlCenter(self.project_root)
        self.jobs_service = JobQueueService(self.project_root)
        self.approvals_service = NativeApprovalQueue(self.project_root)

    @staticmethod
    def _iso(value: str | None, field: str) -> str | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"invalid {field}: {value}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC).isoformat()

    def add_task(self, title: str, *, priority=50, dependencies=(), due_at=None, reminder_at=None, source="task_workspace") -> dict[str, Any]:
        result = self.tasks_service.add_task(title, source, priority=priority, dependencies=list(dependencies),
            due_at=self._iso(due_at, "due_at"), reminder_at=self._iso(reminder_at, "reminder_at"))
        if not result.get("ok"):
            return result
        task = result["task"]
        if task.get("requires_approval"):
            approval = self.approvals_service.create(command="agent.task", intent=task["intent"], text=task["title"], target=task["id"])
            task = self.tasks_service.update_task(task["id"], approval_id=approval["approval_id"], approval_status="pending")["task"]
        return {**result, "task": task}

    def add_reminder(self, title: str, reminder_at: str, *, priority=50, due_at=None) -> dict[str, Any]:
        return self.add_task(title, priority=priority, due_at=due_at, reminder_at=reminder_at, source="reminder")

    def add_calendar_task(self, title: str, due_at: str, *, priority=50, reminder_at=None) -> dict[str, Any]:
        result = self.add_task(title, priority=priority, due_at=due_at, reminder_at=reminder_at, source="calendar")
        if result.get("ok"):
            event_id = f"task:{result['task']['id']}"
            result["task"] = self.tasks_service.update_task(result["task"]["id"], calendar_event_id=event_id)["task"]
        return result

    def enqueue_agent_job(self, title: str, *, priority=50, dependencies=(), approval_required=False) -> dict[str, Any]:
        task_result = self.add_task(title, priority=priority, dependencies=dependencies, source="agent_job")
        if not task_result.get("ok"):
            return task_result
        task = task_result["task"]
        gated = bool(approval_required or task.get("requires_approval"))
        job = self.jobs_service.add_job("agent", title, priority=int(task["priority"]), approval_required=gated, payload={"task_id": task["id"]})
        task = self.tasks_service.update_task(task["id"], queue_job_id=job.id)["task"]
        if gated and not task.get("approval_id"):
            approval = self.approvals_service.create(command="agent.job", intent=task["intent"], text=title, target=task["id"])
            task = self.tasks_service.update_task(task["id"], approval_id=approval["approval_id"], approval_status="pending")["task"]
        return {"ok": True, "task": task, "job": job.to_dict()}

    def tasks(self, *, status=None, priority=None, query="") -> list[dict[str, Any]]:
        rows = self.tasks_service.tasks(limit=100_000)
        query = query.strip().lower()
        if status: rows = [row for row in rows if row.get("status") == status]
        if priority is not None: rows = [row for row in rows if int(row.get("priority", 50)) == int(priority)]
        if query: rows = [row for row in rows if query in str(row.get("title", "")).lower()]
        return rows

    def reminders(self) -> list[dict[str, Any]]:
        return sorted((row for row in self.tasks() if row.get("reminder_at")), key=lambda row: row["reminder_at"])

    def calendar(self) -> list[dict[str, Any]]:
        return sorted((row for row in self.tasks() if row.get("due_at")), key=lambda row: row["due_at"])

    def run_task(self, task_id: str, *, dry_run=False) -> dict[str, Any]:
        task = next((row for row in self.tasks() if row.get("id") == task_id), None)
        confirmed = bool(task and task.get("approval_status") == "approved")
        result = self.tasks_service.run_task(task_id, confirmed=confirmed, dry_run=dry_run)
        if result.get("ok") and task and task.get("queue_job_id") and not dry_run:
            self.jobs_service.update_status(task["queue_job_id"], "success")
        return result

    def decide_approval(self, approval_id: str, approved: bool) -> dict[str, Any]:
        status = "approved" if approved else "rejected"
        approval = self.approvals_service.mark(approval_id, status)
        if approval is None:
            raise KeyError(approval_id)
        task = next((row for row in self.tasks() if row.get("approval_id") == approval_id or row.get("id") == approval.get("target")), None)
        if task:
            task = self.tasks_service.update_task(task["id"], approval_status=status)["task"]
            job_id = task.get("queue_job_id")
            if job_id:
                self.jobs_service.approve(job_id) if approved else self.jobs_service.cancel(job_id)
            if not approved:
                self.tasks_service.cancel_task(task["id"])
        return {"ok": True, "approval": approval, "task": task}

    def history(self, limit=100) -> list[dict[str, Any]]:
        rows = [{**row, "source": "agent"} for row in self.tasks_service.logs(limit=limit)]
        path = self.jobs_service.history_path
        if path.exists():
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                try: rows.append({"source": "queue", **json.loads(line)})
                except (json.JSONDecodeError, TypeError): continue
        return rows[-max(0, int(limit)):]

    def snapshot(self) -> dict[str, Any]:
        tasks = self.tasks()
        jobs = self.jobs_service.snapshot()
        approvals = self.approvals_service.list(status="pending")
        completed_ids = {str(row.get("id")) for row in tasks if row.get("status") == "done"}
        summary = {"tasks": len(tasks), "open": sum(row.get("status") == "pending" for row in tasks),
            "reminders": len(self.reminders()), "calendar": len(self.calendar()), "agent_jobs": jobs["total"],
            "pending_approvals": len(approvals),
            "blocked_dependencies": sum(bool(set(row.get("dependencies") or ()) - completed_ids) for row in tasks if row.get("status") == "pending")}
        return {"ok": True, "version": "30.49", "mode": "existing_agent_task_queue",
            "tasks": tasks, "reminders": self.reminders(), "calendar": self.calendar(), "jobs": jobs,
            "approvals": approvals, "history": self.history(), "summary": summary}
