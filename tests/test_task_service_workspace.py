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
from threading import Barrier
import tempfile
from pathlib import Path

import pytest

from secondbrain.storage.db_executor import SqliteExecutor
from secondbrain.tasks.repository import PostgresTaskRepository
from secondbrain.tasks.service import TaskProjectService, TaskServiceError, DependencyCycleError, VersionConflict

WS_A = "ws-a"
WS_B = "ws-b"


def test_parallel_project_creation_preserves_both_projects(tmp_path):
    services = [_sqlite_service(tmp_path), _sqlite_service(tmp_path)]
    barrier = Barrier(2)
    def create(service, title):
        barrier.wait(timeout=5)
        return service.create_project(workspace_id=WS_A, title=title)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(create, service, str(i)) for i, service in enumerate(services)]
        projects = [future.result(timeout=10) for future in futures]
    assert {p.project_id for p in services[0].list_projects(workspace_id=WS_A)} == {
        p.project_id for p in projects}


def test_parallel_project_update_and_task_progress_preserve_fields(tmp_path):
    services = [_sqlite_service(tmp_path), _sqlite_service(tmp_path)]
    project = services[0].create_project(workspace_id=WS_A, title="Original")
    barrier = Barrier(2)
    def rename():
        barrier.wait(timeout=5)
        return services[0].update_project(project.project_id, workspace_id=WS_A, title="Renamed")
    def create_task():
        barrier.wait(timeout=5)
        return services[1].create_task(workspace_id=WS_A, title="Done", project_id=project.project_id,
                                        status="completed")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(rename), pool.submit(create_task)]
        for future in futures:
            future.result(timeout=10)
    final = services[0].get_project(project.project_id, workspace_id=WS_A)
    assert final.title == "Renamed"
    assert final.progress == 100
    assert final.version == project.version + 2


def test_parallel_task_creation_preserves_tasks_and_events(tmp_path):
    services = [_sqlite_service(tmp_path), _sqlite_service(tmp_path)]
    barrier = Barrier(2)
    def create(service, title):
        barrier.wait(timeout=5)
        return service.create_task(workspace_id=WS_A, title=title)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(create, service, str(i)) for i, service in enumerate(services)]
        tasks = [future.result(timeout=10) for future in futures]
    assert {t.task_id for t in services[0].list_tasks(workspace_id=WS_A)} == {t.task_id for t in tasks}
    assert len(services[0]._read("events", workspace_id=WS_A)) == 2


def test_parallel_expected_version_updates_allow_one_writer(tmp_path):
    services = [_sqlite_service(tmp_path), _sqlite_service(tmp_path)]
    task = services[0].create_task(workspace_id=WS_A, title="Original")
    barrier = Barrier(2)
    def update(service, title):
        barrier.wait(timeout=5)
        try:
            return service.update_task(task.task_id, workspace_id=WS_A, title=title, expected_version=task.version)
        except VersionConflict:
            return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(update, service, str(i)) for i, service in enumerate(services)]
        results = [future.result(timeout=10) for future in futures]
    winners = [result for result in results if result is not None]
    assert len(winners) == 1
    assert services[0].get_task(task.task_id, workspace_id=WS_A).to_dict() == winners[0].to_dict()
    assert len(services[0]._read("events", workspace_id=WS_A)) == 2


@pytest.mark.parametrize("operation", ["create", "update"])
def test_task_mutation_rolls_back_on_event_failure(tmp_path, monkeypatch, operation):
    svc = _sqlite_service(tmp_path)
    task = svc.create_task(workspace_id=WS_A, title="Original")
    before = {name: svc._read(name, workspace_id=WS_A) for name in ("tasks", "events")}
    def fail(*args, **kwargs):
        raise TaskServiceError("event_failure")
    monkeypatch.setattr(svc, "_emit", fail)
    with pytest.raises(TaskServiceError, match="event_failure"):
        if operation == "create":
            svc.create_task(workspace_id=WS_A, title="Rejected")
        else:
            svc.update_task(task.task_id, workspace_id=WS_A, title="Rejected")
    assert {name: svc._read(name, workspace_id=WS_A) for name in before} == before


@pytest.mark.parametrize("failure", ["event", "progress"])
def test_approved_delete_rolls_back_all_changes(tmp_path, monkeypatch, failure):
    svc = _sqlite_service(tmp_path)
    project = svc.create_project(workspace_id=WS_A, title="Project")
    first = svc.create_task(workspace_id=WS_A, title="First", project_id=project.project_id)
    second = svc.create_task(workspace_id=WS_A, title="Second", project_id=project.project_id)
    svc.add_dependency(first.task_id, second.task_id, workspace_id=WS_A)
    before = {name: svc._read(name, workspace_id=WS_A)
              for name in ("tasks", "dependencies", "events", "projects")}
    def fail(*args, **kwargs):
        raise TaskServiceError("injected_failure")
    monkeypatch.setattr(svc, "_emit" if failure == "event" else "update_project", fail)
    with pytest.raises(TaskServiceError, match="injected_failure"):
        svc.delete_task(first.task_id, workspace_id=WS_A, approved=True)
    assert {name: svc._read(name, workspace_id=WS_A) for name in before} == before


def test_parallel_dependency_creation_and_task_deletion(tmp_path):
    services = [_sqlite_service(tmp_path), _sqlite_service(tmp_path)]
    first = services[0].create_task(workspace_id=WS_A, title="First")
    second = services[0].create_task(workspace_id=WS_A, title="Second")
    barrier = Barrier(2)
    def add():
        barrier.wait(timeout=5)
        try:
            services[0].add_dependency(first.task_id, second.task_id, workspace_id=WS_A)
            return "added"
        except TaskServiceError as exc:
            assert str(exc).startswith("task_not_found:")
            return "missing"
    def delete():
        barrier.wait(timeout=5)
        return services[1].delete_task(first.task_id, workspace_id=WS_A, approved=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        addition, deletion = pool.submit(add), pool.submit(delete)
        assert addition.result(timeout=10) in {"added", "missing"}
        assert deletion.result(timeout=10)["status"] == "deleted"
    assert services[0].get_task(first.task_id, workspace_id=WS_A) is None
    assert services[0]._read("dependencies", workspace_id=WS_A) == []


@pytest.mark.parametrize("scenario", ["identical", "opposite", "distinct"])
def test_parallel_dependency_edits_across_connections(tmp_path, scenario):
    services = [_sqlite_service(tmp_path), _sqlite_service(tmp_path)]
    tasks = [services[0].create_task(workspace_id=WS_A, title=str(i)) for i in range(3)]
    first = (tasks[0].task_id, tasks[1].task_id)
    second = {"identical": first, "opposite": first[::-1],
              "distinct": (tasks[0].task_id, tasks[2].task_id)}[scenario]
    barrier = Barrier(2)

    def add(service, pair):
        barrier.wait(timeout=5)
        try:
            return service.add_dependency(*pair, workspace_id=WS_A)
        except DependencyCycleError:
            return "cycle"

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(add, service, pair) for service, pair in zip(services, [first, second])]
        results = [future.result(timeout=10) for future in futures]
    rows = services[0]._read("dependencies", workspace_id=WS_A)
    if scenario == "identical":
        assert results[0].dependency_id == results[1].dependency_id
        assert len(rows) == 1
    elif scenario == "opposite":
        assert results.count("cycle") == 1
        assert len(rows) == 1
    else:
        assert {(r["predecessor_id"], r["successor_id"]) for r in rows} == {first, second}


@pytest.mark.parametrize("backend", ["sqlite", "jsonl"])
def test_dependency_retries_are_idempotent_and_conflicts_preserve_data(tmp_path, backend):
    svc = _sqlite_service(tmp_path) if backend == "sqlite" else _jsonl_service(tmp_path)
    first = svc.create_task(workspace_id=WS_A, title="First")
    second = svc.create_task(workspace_id=WS_A, title="Second")
    original = svc.add_dependency(first.task_id, second.task_id, workspace_id=WS_A, lag_minutes=5)
    repeated = svc.add_dependency(first.task_id, second.task_id, workspace_id=WS_A, lag_minutes=5)
    assert repeated.to_dict() == original.to_dict()
    before = svc._read("dependencies", workspace_id=WS_A)
    assert len(before) == 1
    for changes in ({"lag_minutes": 6}, {"dependency_type": "start_to_start", "lag_minutes": 5}):
        with pytest.raises(TaskServiceError, match="^dependency_conflict$"):
            svc.add_dependency(first.task_id, second.task_id, workspace_id=WS_A, **changes)
    assert svc._read("dependencies", workspace_id=WS_A) == before


@pytest.mark.parametrize("backend", ["sqlite", "jsonl"])
@pytest.mark.parametrize("changes,error", [({"dependency_type": "unknown"}, "invalid_dependency_type"),
                                         ({"dependency_type": []}, "invalid_dependency_type"),
                                         ({"lag_minutes": "invalid"}, "invalid_dependency_lag"),
                                         ({"lag_minutes": True}, "invalid_dependency_lag"),
                                         ({"lag_minutes": False}, "invalid_dependency_lag"),
                                         ({"lag_minutes": 1.9}, "invalid_dependency_lag"),
                                         ({"lag_minutes": 1.0}, "invalid_dependency_lag"),
                                         ({"lag_minutes": "1.5"}, "invalid_dependency_lag"),
                                         ({"lag_minutes": float("inf")}, "invalid_dependency_lag"),
                                         ({"lag_minutes": None}, "invalid_dependency_lag")])
def test_invalid_dependency_parameters_do_not_write(tmp_path, backend, changes, error):
    svc = _sqlite_service(tmp_path) if backend == "sqlite" else _jsonl_service(tmp_path)
    first = svc.create_task(workspace_id=WS_A, title="First")
    second = svc.create_task(workspace_id=WS_A, title="Second")
    with pytest.raises(TaskServiceError, match=f"^{error}$"):
        svc.add_dependency(first.task_id, second.task_id, workspace_id=WS_A, **changes)
    assert svc._read("dependencies", workspace_id=WS_A) == []


@pytest.mark.parametrize("backend", ["sqlite", "jsonl"])
@pytest.mark.parametrize("kind", ["finish_to_start", "start_to_start", "finish_to_finish", "start_to_finish"])
@pytest.mark.parametrize("lag,expected", [(0, 0), (-5, -5), (" +12 ", 12)])
def test_dependency_types_and_integer_lags_round_trip(tmp_path, backend, kind, lag, expected):
    svc = _sqlite_service(tmp_path) if backend == "sqlite" else _jsonl_service(tmp_path)
    first = svc.create_task(workspace_id=WS_A, title="First")
    second = svc.create_task(workspace_id=WS_A, title="Second")
    dependency = svc.add_dependency(first.task_id, second.task_id, workspace_id=WS_A,
                                    dependency_type=kind, lag_minutes=lag)
    assert dependency.lag_minutes == expected
    assert dependency.dependency_type == kind
    repeated = svc.add_dependency(first.task_id, second.task_id, workspace_id=WS_A,
                                  dependency_type=kind, lag_minutes=expected)
    assert repeated.to_dict() == dependency.to_dict()
    assert len(svc._read("dependencies", workspace_id=WS_A)) == 1


@pytest.mark.parametrize("backend", ["sqlite", "jsonl"])
@pytest.mark.parametrize("deleted_status,expected", [("planned", 100), ("completed", 0)])
def test_approved_delete_refreshes_project_progress(tmp_path, backend, deleted_status, expected):
    svc = _sqlite_service(tmp_path) if backend == "sqlite" else _jsonl_service(tmp_path)
    project = svc.create_project(workspace_id=WS_A, title="Project")
    deleted = svc.create_task(workspace_id=WS_A, title="Delete", project_id=project.project_id,
                              status=deleted_status)
    retained = svc.create_task(workspace_id=WS_A, title="Keep", project_id=project.project_id,
                               status="completed" if deleted_status == "planned" else "planned")
    svc.add_dependency(deleted.task_id, retained.task_id, workspace_id=WS_A)
    foreign_project = svc.create_project(workspace_id=WS_B, title="Foreign")
    svc.create_task(workspace_id=WS_B, title="Foreign done", project_id=foreign_project.project_id,
                    status="completed")
    foreign_before = svc.get_project(foreign_project.project_id, workspace_id=WS_B).to_dict()
    assert svc.get_project(project.project_id, workspace_id=WS_A).progress == 50
    assert svc.delete_task(deleted.task_id, workspace_id=WS_A)["status"] == "approval_required"
    assert svc.get_project(project.project_id, workspace_id=WS_A).progress == 50
    svc.delete_task(deleted.task_id, workspace_id=WS_A, approved=True)
    assert svc.get_project(project.project_id, workspace_id=WS_A).progress == expected
    assert svc._read("dependencies", workspace_id=WS_A) == []
    assert svc.get_project(foreign_project.project_id, workspace_id=WS_B).to_dict() == foreign_before
    svc.delete_task(retained.task_id, workspace_id=WS_A, approved=True)
    assert svc.get_project(project.project_id, workspace_id=WS_A).progress == 0


@pytest.mark.parametrize("backend", ["sqlite", "jsonl"])
@pytest.mark.parametrize("foreign", [False, True])
def test_task_project_reference_rejected_without_mutation(tmp_path, backend, foreign):
    svc = _sqlite_service(tmp_path) if backend == "sqlite" else _jsonl_service(tmp_path)
    project_id = (svc.create_project(workspace_id=WS_B, title="B").project_id
                  if foreign else "missing")
    with pytest.raises(TaskServiceError, match="^project_not_found$"):
        svc.create_task(workspace_id=WS_A, title="Rejected", project_id=project_id)
    assert svc.list_tasks(workspace_id=WS_A) == []
    task = svc.create_task(workspace_id=WS_A, title="Original")
    events = svc._read("events", workspace_id=WS_A)
    with pytest.raises(TaskServiceError, match="^project_not_found$"):
        svc.update_task(task.task_id, workspace_id=WS_A, project_id=project_id, title="Changed")
    assert svc.get_task(task.task_id, workspace_id=WS_A).to_dict() == task.to_dict()
    assert svc._read("events", workspace_id=WS_A) == events


@pytest.mark.parametrize("backend", ["sqlite", "jsonl"])
def test_project_reassignment_recomputes_both_projects(tmp_path, backend):
    svc = _sqlite_service(tmp_path) if backend == "sqlite" else _jsonl_service(tmp_path)
    first = svc.create_project(workspace_id=WS_A, title="First")
    second = svc.create_project(workspace_id=WS_A, title="Second")
    task = svc.create_task(workspace_id=WS_A, title="Done", project_id=first.project_id, status="completed")
    svc.update_task(task.task_id, workspace_id=WS_A, project_id=second.project_id)
    assert svc.get_project(first.project_id, workspace_id=WS_A).progress == 0
    assert svc.get_project(second.project_id, workspace_id=WS_A).progress == 100
    svc.update_task(task.task_id, workspace_id=WS_A, project_id=None)
    assert svc.get_project(second.project_id, workspace_id=WS_A).progress == 0


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
