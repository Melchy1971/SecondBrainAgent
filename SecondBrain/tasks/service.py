"""Task & project service - the single source of truth for tasks/projects.

Persists to JSONL under ``runtime/tasks/`` so state survives restarts. Enforces
status transitions, prevents dependency cycles, marks (but never auto-escalates)
overdue tasks, isolates workspaces and routes deletes through an approval.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from secondbrain.tasks.repository import TaskRepository, TaskRepositoryConflict, create_task_repository

from secondbrain.tasks.models import (
    VALID_TASK_TRANSITIONS,
    DependencyType,
    Priority,
    Project,
    Status,
    Task,
    TaskDependency,
    TaskEvent,
    TaskEventType,
    new_id,
    utc_now,
)

__all__ = ["TaskProjectService", "TaskServiceError", "StatusTransitionError", "DependencyCycleError", "ApprovalRequired", "VersionConflict"]

_TERMINAL = {Status.COMPLETED.value, Status.CANCELLED.value, Status.ARCHIVED.value}


class TaskServiceError(RuntimeError):
    pass


class StatusTransitionError(TaskServiceError):
    pass


class DependencyCycleError(TaskServiceError):
    pass


class ApprovalRequired(TaskServiceError):
    pass


class VersionConflict(TaskServiceError):
    pass


def _parse(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


class TaskProjectService:
    def __init__(self, project_root: str | Path = ".", *, approval_queue: Any | None = None,
                 repository: TaskRepository | None = None, env: dict[str, str] | None = None,
                 executor: Any | None = None) -> None:
        self.root = Path(project_root).resolve()
        self.dir = self.root / "runtime" / "tasks"
        self._approval_queue = approval_queue
        self._repository = repository if repository is not None else create_task_repository(env=env, executor=executor)

    # -- persistence ------------------------------------------------------

    def _path(self, name: str) -> Path:
        return self.dir / f"{name}.jsonl"

    def _read(self, name: str) -> list[dict[str, Any]]:
        if self._repository is not None:
            return self._repository.read(name)
        p = self._path(name)
        if not p.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

    def _write(self, name: str, rows: Iterable[dict[str, Any]]) -> None:
        if self._repository is not None:
            try:
                self._repository.write(name, rows)
            except TaskRepositoryConflict as exc:
                raise VersionConflict(str(exc)) from exc
            return
        self.dir.mkdir(parents=True, exist_ok=True)
        p = self._path(name)
        tmp = p.with_name(f"{p.name}.{new_id('tmp')}.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        tmp.replace(p)

    def _append(self, name: str, row: dict[str, Any]) -> None:
        if self._repository is not None:
            self._repository.append(name, row)
            return
        self.dir.mkdir(parents=True, exist_ok=True)
        with self._path(name).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _emit(self, task: Task, event_type: TaskEventType, *, actor: str, detail: str = "", metadata: dict[str, Any] | None = None) -> None:
        event = TaskEvent(
            event_id=new_id("evt"), task_id=task.task_id, workspace_id=task.workspace_id,
            event_type=event_type.value, actor=actor, detail=detail, metadata=metadata or {},
        )
        self._append("events", event.to_dict())

    # -- projects ---------------------------------------------------------

    def create_project(self, *, workspace_id: str, title: str, actor: str = "user", **fields: Any) -> Project:
        project = Project(project_id=new_id("prj"), workspace_id=workspace_id, title=title,
                          source=fields.pop("source", "user"), **{k: v for k, v in fields.items() if k in Project.__dataclass_fields__})
        rows = self._read("projects")
        rows.append(project.to_dict())
        self._write("projects", rows)
        return project

    def update_project(self, project_id: str, *, workspace_id: str, **changes: Any) -> Project:
        rows = self._read("projects")
        updated: Project | None = None
        for i, row in enumerate(rows):
            if row.get("project_id") == project_id and row.get("workspace_id") == workspace_id:
                expected_version = changes.pop("expected_version", None)
                if expected_version is not None and int(expected_version) != int(row.get("version", 1)):
                    raise VersionConflict(f"project_version_conflict:{project_id}")
                for k, v in changes.items():
                    if k in Project.__dataclass_fields__ and k not in {"project_id", "workspace_id", "created_at"}:
                        row[k] = v
                row["updated_at"] = utc_now()
                row["version"] = int(row.get("version", 1)) + 1
                rows[i] = row
                updated = Project.from_dict(row)
                break
        if updated is None:
            raise TaskServiceError(f"project_not_found:{project_id}")
        self._write("projects", rows)
        return updated

    def get_project(self, project_id: str, *, workspace_id: str) -> Project | None:
        return next((p for p in self.list_projects(workspace_id=workspace_id, include_archived=True)
                     if p.project_id == project_id), None)

    def archive_project(self, project_id: str, *, workspace_id: str) -> Project:
        return self.update_project(project_id, workspace_id=workspace_id, status=Status.ARCHIVED.value, archived_at=utc_now())

    def list_projects(self, *, workspace_id: str, include_archived: bool = False) -> list[Project]:
        out = [Project.from_dict(r) for r in self._read("projects") if r.get("workspace_id") == workspace_id]
        if not include_archived:
            out = [p for p in out if p.status != Status.ARCHIVED.value]
        return out

    # -- tasks ------------------------------------------------------------

    def create_task(self, *, workspace_id: str, title: str, project_id: str | None = None, actor: str = "user", **fields: Any) -> Task:
        allowed = {k: v for k, v in fields.items() if k in Task.__dataclass_fields__}
        task = Task(task_id=new_id("tsk"), project_id=project_id, workspace_id=workspace_id, title=title, **allowed)
        rows = self._read("tasks")
        rows.append(task.to_dict())
        self._write("tasks", rows)
        self._emit(task, TaskEventType.CREATED, actor=actor, detail=task.source,
                   metadata={"source": task.source, "source_reference": task.source_reference, "confidence": task.confidence})
        if project_id:
            self._recompute_progress(project_id, workspace_id)
        return task

    def get_task(self, task_id: str, *, workspace_id: str) -> Task | None:
        for r in self._read("tasks"):
            if r.get("task_id") == task_id and r.get("workspace_id") == workspace_id:
                return Task.from_dict(r)
        return None

    def update_task(self, task_id: str, *, workspace_id: str, actor: str = "user", **changes: Any) -> Task:
        rows = self._read("tasks")
        updated: Task | None = None
        for i, row in enumerate(rows):
            if row.get("task_id") == task_id and row.get("workspace_id") == workspace_id:
                expected_version = changes.pop("expected_version", None)
                if expected_version is not None and int(expected_version) != int(row.get("version", 1)):
                    raise VersionConflict(f"task_version_conflict:{task_id}")
                new_status = changes.get("status")
                if new_status is not None and new_status != row.get("status"):
                    self._validate_transition(str(row.get("status")), str(new_status))
                for k, v in changes.items():
                    if k in Task.__dataclass_fields__ and k not in {"task_id", "workspace_id", "created_at"}:
                        row[k] = v
                row["updated_at"] = utc_now()
                row["version"] = int(row.get("version", 1)) + 1
                rows[i] = row
                updated = Task.from_dict(row)
                break
        if updated is None:
            raise TaskServiceError(f"task_not_found:{task_id}")
        self._write("tasks", rows)
        self._emit(updated, TaskEventType.UPDATED, actor=actor, detail=",".join(changes))
        if updated.project_id:
            self._recompute_progress(updated.project_id, workspace_id)
        return updated

    @staticmethod
    def _validate_transition(old: str, new: str) -> None:
        try:
            allowed = VALID_TASK_TRANSITIONS.get(Status(old), frozenset())
        except ValueError:
            raise StatusTransitionError(f"invalid_status:{old}")
        if new == old:
            return
        try:
            target = Status(new)
        except ValueError:
            raise StatusTransitionError(f"invalid_status:{new}")
        if target not in allowed:
            raise StatusTransitionError(f"invalid_transition:{old}->{new}")

    def complete_task(self, task_id: str, *, workspace_id: str, actor: str = "user") -> Task:
        task = self.update_task(task_id, workspace_id=workspace_id, actor=actor, status=Status.COMPLETED.value, completed_at=utc_now())
        self._emit(task, TaskEventType.COMPLETED, actor=actor)
        return task

    def reopen_task(self, task_id: str, *, workspace_id: str, actor: str = "user") -> Task:
        task = self.update_task(task_id, workspace_id=workspace_id, actor=actor, status=Status.ACTIVE.value, completed_at=None)
        self._emit(task, TaskEventType.REOPENED, actor=actor)
        return task

    def defer_task(self, task_id: str, *, workspace_id: str, due_date: str | None = None, actor: str = "user") -> Task:
        changes: dict[str, Any] = {"status": Status.WAITING.value}
        if due_date is not None:
            changes["due_date"] = due_date
        task = self.update_task(task_id, workspace_id=workspace_id, actor=actor, **changes)
        self._emit(task, TaskEventType.DEFERRED, actor=actor, detail=str(due_date or ""))
        return task

    def delete_task(self, task_id: str, *, workspace_id: str, actor: str = "user", approved: bool = False) -> dict[str, Any]:
        task = self.get_task(task_id, workspace_id=workspace_id)
        if task is None:
            raise TaskServiceError(f"task_not_found:{task_id}")
        if not approved:
            approval = self._create_delete_approval(task, actor)
            return {"status": "approval_required", "approval": approval, "task_id": task_id}
        rows = [r for r in self._read("tasks") if not (r.get("task_id") == task_id and r.get("workspace_id") == workspace_id)]
        self._write("tasks", rows)
        deps = [d for d in self._read("dependencies")
                if d.get("predecessor_id") != task_id and d.get("successor_id") != task_id]
        self._write("dependencies", deps)
        self._emit(task, TaskEventType.DELETED, actor=actor)
        return {"status": "deleted", "task_id": task_id}

    def _create_delete_approval(self, task: Task, actor: str) -> dict[str, Any]:
        try:
            from secondbrain.native.approval import NativeApprovalQueue

            queue = self._approval_queue or NativeApprovalQueue(self.root)
            return queue.create(
                command="tasks.delete", intent="delete_task", text=f"Delete task: {task.title}",
                target=task.task_id, category="delete_request", risk_level="high",
                tool_name="tasks.delete", workspace_id=task.workspace_id,
            )
        except Exception as exc:  # noqa: BLE001 - approval backend optional in bare checkout
            return {"status": "approval_backend_unavailable", "error": f"{type(exc).__name__}", "task_id": task.task_id}

    # -- dependencies -----------------------------------------------------

    def add_dependency(self, predecessor_id: str, successor_id: str, *, workspace_id: str,
                       dependency_type: str = DependencyType.FINISH_TO_START.value, lag_minutes: int = 0) -> TaskDependency:
        if predecessor_id == successor_id:
            raise DependencyCycleError("self_dependency")
        for tid in (predecessor_id, successor_id):
            if self.get_task(tid, workspace_id=workspace_id) is None:
                raise TaskServiceError(f"task_not_found:{tid}")
        edges = self._dependency_edges(workspace_id)
        edges.setdefault(predecessor_id, set()).add(successor_id)
        if self._creates_cycle(edges, successor_id, predecessor_id):
            raise DependencyCycleError(f"cycle:{predecessor_id}->{successor_id}")
        dep = TaskDependency(predecessor_id=predecessor_id, successor_id=successor_id,
                             dependency_type=dependency_type, lag_minutes=int(lag_minutes))
        rows = self._read("dependencies")
        rows.append({**dep.to_dict(), "workspace_id": workspace_id})
        self._write("dependencies", rows)
        return dep

    def remove_dependency(self, predecessor_id: str, successor_id: str, *, workspace_id: str) -> None:
        rows = [d for d in self._read("dependencies")
                if not (d.get("predecessor_id") == predecessor_id and d.get("successor_id") == successor_id and d.get("workspace_id") == workspace_id)]
        self._write("dependencies", rows)

    def _dependency_edges(self, workspace_id: str) -> dict[str, set[str]]:
        edges: dict[str, set[str]] = {}
        for d in self._read("dependencies"):
            if d.get("workspace_id") == workspace_id:
                edges.setdefault(str(d.get("predecessor_id")), set()).add(str(d.get("successor_id")))
        return edges

    @staticmethod
    def _creates_cycle(edges: dict[str, set[str]], start: str, target: str) -> bool:
        stack = [start]
        seen: set[str] = set()
        while stack:
            node = stack.pop()
            if node == target:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(edges.get(node, set()))
        return False

    # -- queries ----------------------------------------------------------

    def list_tasks(self, *, workspace_id: str, status: str | None = None, project_id: str | None = None) -> list[Task]:
        out = [Task.from_dict(r) for r in self._read("tasks") if r.get("workspace_id") == workspace_id]
        if status is not None:
            out = [t for t in out if t.status == status]
        if project_id is not None:
            out = [t for t in out if t.project_id == project_id]
        return out

    def get_overdue(self, *, workspace_id: str, now: datetime | None = None) -> list[Task]:
        moment = now or datetime.now(timezone.utc)
        result = []
        for t in self.list_tasks(workspace_id=workspace_id):
            if t.status in _TERMINAL:
                continue
            due = _parse(t.due_date)
            if due is not None and due < moment:
                result.append(t)
        return result

    def get_today(self, *, workspace_id: str, now: datetime | None = None) -> list[Task]:
        moment = now or datetime.now(timezone.utc)
        today = moment.date()
        out = []
        for t in self.list_tasks(workspace_id=workspace_id):
            if t.status in _TERMINAL:
                continue
            due = _parse(t.due_date)
            if (due is not None and due.date() <= today) or t.status == Status.ACTIVE.value:
                out.append(t)
        return out

    def get_upcoming(self, *, workspace_id: str, now: datetime | None = None) -> list[Task]:
        moment = now or datetime.now(timezone.utc)
        return sorted(
            (t for t in self.list_tasks(workspace_id=workspace_id)
             if t.status not in _TERMINAL and (due := _parse(t.due_date)) is not None and due >= moment),
            key=lambda task: _parse(task.due_date) or moment,
        )

    def get_waiting(self, *, workspace_id: str) -> list[Task]:
        return self.list_tasks(workspace_id=workspace_id, status=Status.WAITING.value)

    def get_blocked(self, *, workspace_id: str) -> list[Task]:
        completed = {t.task_id for t in self.list_tasks(workspace_id=workspace_id) if t.status == Status.COMPLETED.value}
        blockers: dict[str, list[str]] = {}
        for d in self._read("dependencies"):
            if d.get("workspace_id") != workspace_id:
                continue
            pred = str(d.get("predecessor_id"))
            if pred not in completed:  # completed predecessors do not block
                blockers.setdefault(str(d.get("successor_id")), []).append(pred)
        out = []
        for t in self.list_tasks(workspace_id=workspace_id):
            if t.status in _TERMINAL:
                continue
            if t.status == Status.BLOCKED.value or t.task_id in blockers:
                out.append(t)
        return out

    def get_next_actions(self, *, workspace_id: str, limit: int = 10) -> list[Task]:
        blocked_ids = {t.task_id for t in self.get_blocked(workspace_id=workspace_id)}
        rank = {Priority.CRITICAL.value: 0, Priority.HIGH.value: 1, Priority.NORMAL.value: 2, Priority.LOW.value: 3}
        candidates = [t for t in self.list_tasks(workspace_id=workspace_id)
                      if t.status in {Status.INBOX.value, Status.PLANNED.value, Status.ACTIVE.value} and t.task_id not in blocked_ids]
        candidates.sort(key=lambda t: (rank.get(t.priority, 2), _parse(t.due_date) or datetime.max.replace(tzinfo=timezone.utc)))
        return candidates[:limit]

    def _recompute_progress(self, project_id: str, workspace_id: str) -> None:
        tasks = self.list_tasks(workspace_id=workspace_id, project_id=project_id)
        if not tasks:
            return
        done = sum(1 for t in tasks if t.status == Status.COMPLETED.value)
        progress = round(done / len(tasks) * 100.0, 1)
        try:
            self.update_project(project_id, workspace_id=workspace_id, progress=progress)
        except TaskServiceError:
            pass
