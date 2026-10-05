"""Workspace-Bindung des TaskProjectService gegen SQLite und JSONL.

Der Service reicht workspace_id jetzt durchgaengig an das Repository weiter.
Getestet werden Isolation zweier Workspaces, Strict Mode
(TASK_REPOSITORY_REQUIRE_WORKSPACE=1), Cross-Workspace-Abwehr und parallele
Aufrufe ohne Kontextleck.

Sandbox-Hinweis: ``secondbrain.tasks.models`` nutzt ``enum.StrEnum`` (Python
3.11). In reinen 3.10-Umgebungen wird ein deckungsgleicher Shim gesetzt, bevor
der Task-Stack importiert wird -- reine Testumgebung, kein Produktionscode.
"""

from __future__ import annotations

import enum

if not hasattr(enum, "StrEnum"):  # pragma: no cover - nur unter Python < 3.11
    class _StrEnum(str, enum.Enum):
        def __str__(self) -> str:
            return str(self.value)
    enum.StrEnum = _StrEnum  # type: ignore[attr-defined]

import concurrent.futures
import tempfile
from pathlib import Path

import pytest

from secondbrain.storage.db_executor import SqliteExecutor
from secondbrain.tasks.repository import PostgresTaskRepository
from secondbrain.tasks.service import TaskProjectService, TaskServiceError

WS_A = "ws-a"
WS_B = "ws-b"


def _sqlite_service(tmp_path: Path, *, require_workspace: bool = False) -> TaskProjectService:
    repo = PostgresTaskRepository(SqliteExecutor(str(tmp_path / "t.sqlite")),
                                  require_workspace=require_workspace)
    repo.ensure_schema()
    return TaskProjectService(tmp_path, repository=repo)


def _jsonl_service(tmp_path: Path) -> TaskProjectService:
    # repository=None -> JSONL-Entwicklungspfad
    return TaskProjectService(tmp_path, repository=None)


# --------------------------------------------------------------------------
# Isolation zweier Workspaces
# --------------------------------------------------------------------------


@pytest.mark.parametrize("backend", ["sqlite", "jsonl"])
def test_two_workspaces_are_isolated(tmp_path, backend) -> None:
    svc = _sqlite_service(tmp_path) if backend == "sqlite" else _jsonl_service(tmp_path)
    a = svc.create_project(workspace_id=WS_A, title="A-Projekt")
    b = svc.create_project(workspace_id=WS_B, title="B-Projekt")

    a_ids = {p.project_id for p in svc.list_projects(workspace_id=WS_A)}
    b_ids = {p.project_id for p in svc.list_projects(workspace_id=WS_B)}
    assert a_ids == {a.project_id}
    assert b_ids == {b.project_id}
    assert a.project_id not in b_ids and b.project_id not in a_ids


@pytest.mark.parametrize("backend", ["sqlite", "jsonl"])
def test_workspace_a_cannot_read_b(tmp_path, backend) -> None:
    svc = _sqlite_service(tmp_path) if backend == "sqlite" else _jsonl_service(tmp_path)
    b = svc.create_project(workspace_id=WS_B, title="Nur B")
    # ws-a fragt B's Projekt-ID ab -> nicht sichtbar.
    assert svc.get_project(b.project_id, workspace_id=WS_A) is None
    assert svc.get_project(b.project_id, workspace_id=WS_B) is not None


@pytest.mark.parametrize("backend", ["sqlite", "jsonl"])
def test_workspace_a_cannot_update_b(tmp_path, backend) -> None:
    svc = _sqlite_service(tmp_path) if backend == "sqlite" else _jsonl_service(tmp_path)
    b = svc.create_project(workspace_id=WS_B, title="Nur B")
    with pytest.raises(TaskServiceError, match="project_not_found"):
        svc.update_project(b.project_id, workspace_id=WS_A, title="gehijackt")
    # B bleibt unveraendert.
    assert svc.get_project(b.project_id, workspace_id=WS_B).title == "Nur B"


def test_jsonl_write_preserves_other_workspace(tmp_path) -> None:
    """Der JSONL-Pfad darf beim Schreiben fremde Workspaces nicht verlieren."""
    svc = _jsonl_service(tmp_path)
    a = svc.create_project(workspace_id=WS_A, title="A")
    svc.create_project(workspace_id=WS_B, title="B")
    # Weitere Schreiboperation in ws-a
    svc.update_project(a.project_id, workspace_id=WS_A, title="A2")
    assert {p.title for p in svc.list_projects(workspace_id=WS_A)} == {"A2"}
    assert {p.title for p in svc.list_projects(workspace_id=WS_B)} == {"B"}


# --------------------------------------------------------------------------
# Tasks quer durch den Lebenszyklus, isoliert
# --------------------------------------------------------------------------


def test_task_lifecycle_isolated(tmp_path) -> None:
    svc = _sqlite_service(tmp_path)
    ta = svc.create_task(workspace_id=WS_A, title="Task A")
    svc.create_task(workspace_id=WS_B, title="Task B")

    assert {t.title for t in svc.list_tasks(workspace_id=WS_A)} == {"Task A"}
    assert {t.title for t in svc.list_tasks(workspace_id=WS_B)} == {"Task B"}

    # ws-b darf ws-a's Task nicht abschliessen.
    with pytest.raises(TaskServiceError, match="task_not_found"):
        svc.complete_task(ta.task_id, workspace_id=WS_B)
    done = svc.complete_task(ta.task_id, workspace_id=WS_A)
    assert done.status == "completed"


# --------------------------------------------------------------------------
# Strict Mode
# --------------------------------------------------------------------------


def test_strict_mode_can_be_enabled(tmp_path) -> None:
    svc = _sqlite_service(tmp_path, require_workspace=True)
    p = svc.create_project(workspace_id=WS_A, title="Strict")
    assert svc.list_projects(workspace_id=WS_A)[0].project_id == p.project_id


def test_empty_workspace_fails_closed(tmp_path) -> None:
    svc = _sqlite_service(tmp_path, require_workspace=True)
    with pytest.raises(TaskServiceError, match="invalid_workspace_id"):
        svc.create_project(workspace_id="", title="X")


def test_invalid_workspace_is_rejected(tmp_path) -> None:
    svc = _sqlite_service(tmp_path)
    with pytest.raises(TaskServiceError, match="invalid_workspace_id"):
        svc.list_projects(workspace_id="ws a; DROP TABLE task_project_records; --")


def test_strict_repository_rejects_unbound_direct_call(tmp_path) -> None:
    """Der Repository-Layer selbst weist einen ungebundenen Aufruf ab."""
    from secondbrain.tasks.repository import TaskRepositoryError

    repo = PostgresTaskRepository(SqliteExecutor(str(tmp_path / "t.sqlite")), require_workspace=True)
    repo.ensure_schema()
    with pytest.raises(TaskRepositoryError, match="workspace_id_required"):
        repo.read("projects")  # ohne workspace_id


# --------------------------------------------------------------------------
# Fehlermeldungen tragen keine Daten
# --------------------------------------------------------------------------


def test_error_does_not_leak_payload(tmp_path) -> None:
    svc = _sqlite_service(tmp_path)
    secret_title = "streng-geheimer-projekttitel-4711"
    try:
        svc.create_project(workspace_id="", title=secret_title)
    except TaskServiceError as exc:
        assert secret_title not in str(exc)
        assert str(exc) == "invalid_workspace_id"
    else:
        pytest.fail("erwarteter Fehler blieb aus")


# --------------------------------------------------------------------------
# Parallele Aufrufe ohne Kontextleck
# --------------------------------------------------------------------------


def test_parallel_service_calls_do_not_leak_context(tmp_path) -> None:
    """Zwei Threads, zwei Workspaces, eigene Services auf derselben DB-Datei.

    workspace_id wird als Parameter durchgereicht -- kein Thread-lokaler
    Zustand, der lecken koennte. Nach dem Lauf ist jede Zeile im richtigen
    Workspace und keine im fremden.
    """
    db = tmp_path / "shared.sqlite"

    def worker(ws: str, n: int) -> list[str]:
        repo = PostgresTaskRepository(SqliteExecutor(str(db)))
        repo.ensure_schema()
        svc = TaskProjectService(tmp_path, repository=repo)
        titles = []
        for i in range(n):
            t = svc.create_task(workspace_id=ws, title=f"{ws}-task-{i}")
            titles.append(t.title)
        return titles

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fut_a = pool.submit(worker, WS_A, 5)
        fut_b = pool.submit(worker, WS_B, 5)
        titles_a = set(fut_a.result())
        titles_b = set(fut_b.result())

    # Verifikation ueber einen frischen Service.
    repo = PostgresTaskRepository(SqliteExecutor(str(db)))
    repo.ensure_schema()
    check = TaskProjectService(tmp_path, repository=repo)
    seen_a = {t.title for t in check.list_tasks(workspace_id=WS_A)}
    seen_b = {t.title for t in check.list_tasks(workspace_id=WS_B)}

    assert seen_a == titles_a
    assert seen_b == titles_b
    assert seen_a.isdisjoint(seen_b)
    assert all(t.startswith("ws-a") for t in seen_a)
    assert all(t.startswith("ws-b") for t in seen_b)
