"""Workspace-Bindung von PostgresTaskRepository, gegen SQLite geprueft.

SQLite kennt keine RLS -- dort traegt allein die Methodenbindung (WHERE-Filter
und Cross-Workspace-Guard). Der RLS-Backstop wird im PostgreSQL-Live-Gate
gegen echtes Postgres nachgewiesen.

Bewusst ohne Import von ``secondbrain.tasks.service`` gehalten: dessen
Modulkette verlangt Python 3.11 (``enum.StrEnum``). ``repository.py`` selbst
ist versionsneutral.
"""

from __future__ import annotations

import pytest

from secondbrain.storage.db_executor import SqliteExecutor
from secondbrain.tasks.repository import PostgresTaskRepository, TaskRepositoryError


def _repo(tmp_path, *, require_workspace: bool = False) -> PostgresTaskRepository:
    executor = SqliteExecutor(str(tmp_path / "tasks.sqlite"))
    repo = PostgresTaskRepository(executor, require_workspace=require_workspace)
    repo.ensure_schema()
    return repo


def _project(pid: str, workspace: str) -> dict:
    return {"project_id": pid, "workspace_id": workspace, "title": pid, "version": 1}


# --------------------------------------------------------------------------
# Rueckwaertskompatibilitaet: der ungebundene Pfad bleibt unveraendert
# --------------------------------------------------------------------------


def test_unscoped_read_returns_all_workspaces(tmp_path) -> None:
    repo = _repo(tmp_path)
    repo.write("projects", [_project("p1", "ws-a"), _project("p2", "ws-b")])
    rows = repo.read("projects")
    assert {r["project_id"] for r in rows} == {"p1", "p2"}


def test_unscoped_write_still_replaces_full_collection(tmp_path) -> None:
    repo = _repo(tmp_path)
    repo.write("projects", [_project("p1", "ws-a"), _project("p2", "ws-b")])
    repo.write("projects", [_project("p1", "ws-a")])  # p2 faellt weg
    assert {r["project_id"] for r in repo.read("projects")} == {"p1"}


# --------------------------------------------------------------------------
# Gebundener Pfad: Isolation auf Methodenebene
# --------------------------------------------------------------------------


def test_scoped_read_only_returns_own_workspace(tmp_path) -> None:
    repo = _repo(tmp_path)
    repo.write("projects", [_project("p1", "ws-a"), _project("p2", "ws-b")])
    rows = repo.read("projects", workspace_id="ws-a")
    assert [r["project_id"] for r in rows] == ["p1"]


def test_scoped_write_does_not_touch_other_workspace(tmp_path) -> None:
    """Der gefaehrliche Loeschpfad darf fremde Workspaces nicht erreichen."""
    repo = _repo(tmp_path)
    repo.write("projects", [_project("p1", "ws-a")], workspace_id="ws-a")
    repo.write("projects", [_project("p2", "ws-b")], workspace_id="ws-b")

    # ws-b schreibt seine (vollstaendige) Teilmenge neu -- ws-a bleibt unberuehrt.
    repo.write("projects", [_project("p2b", "ws-b")], workspace_id="ws-b")

    assert {r["project_id"] for r in repo.read("projects", workspace_id="ws-a")} == {"p1"}
    assert {r["project_id"] for r in repo.read("projects", workspace_id="ws-b")} == {"p2b"}


def test_scoped_write_rejects_foreign_rows(tmp_path) -> None:
    repo = _repo(tmp_path)
    with pytest.raises(TaskRepositoryError, match="write_crosses_workspace"):
        repo.write("projects", [_project("p1", "ws-b")], workspace_id="ws-a")


def test_scoped_append_stays_in_workspace(tmp_path) -> None:
    repo = _repo(tmp_path)
    repo.write("projects", [_project("p1", "ws-a")], workspace_id="ws-a")
    repo.append("projects", _project("p2", "ws-a"), workspace_id="ws-a")
    assert {r["project_id"] for r in repo.read("projects", workspace_id="ws-a")} == {"p1", "p2"}


def test_invalid_workspace_id_is_rejected(tmp_path) -> None:
    from secondbrain.storage.workspace_context import WorkspaceContextError

    repo = _repo(tmp_path)
    with pytest.raises(WorkspaceContextError):
        repo.read("projects", workspace_id="ws'; DROP TABLE task_project_records; --")


# --------------------------------------------------------------------------
# Require-Flag
# --------------------------------------------------------------------------


def test_require_flag_blocks_unscoped_read(tmp_path) -> None:
    repo = _repo(tmp_path, require_workspace=True)
    with pytest.raises(TaskRepositoryError, match="workspace_id_required"):
        repo.read("projects")


def test_require_flag_blocks_unscoped_write(tmp_path) -> None:
    repo = _repo(tmp_path, require_workspace=True)
    with pytest.raises(TaskRepositoryError, match="workspace_id_required"):
        repo.write("projects", [_project("p1", "ws-a")])


def test_require_flag_allows_scoped_access(tmp_path) -> None:
    repo = _repo(tmp_path, require_workspace=True)
    repo.write("projects", [_project("p1", "ws-a")], workspace_id="ws-a")
    assert len(repo.read("projects", workspace_id="ws-a")) == 1


def test_require_flag_reads_env(tmp_path) -> None:
    executor = SqliteExecutor(str(tmp_path / "e.sqlite"))
    repo = PostgresTaskRepository(executor, env={"TASK_REPOSITORY_REQUIRE_WORKSPACE": "1"})
    assert repo.require_workspace is True


# --------------------------------------------------------------------------
# SQLite bekommt kein SET LOCAL
# --------------------------------------------------------------------------


def test_sqlite_schema_has_no_rls_statements(tmp_path) -> None:
    """ensure_schema darf auf SQLite kein RLS-DDL absetzen."""
    class Recording(SqliteExecutor):
        def __init__(self, path):
            super().__init__(path)
            self.seen: list[str] = []

        def execute(self, sql, params=None):
            self.seen.append(sql)
            return super().execute(sql, params)

    executor = Recording(str(tmp_path / "r.sqlite"))
    repo = PostgresTaskRepository(executor)
    repo.ensure_schema()
    joined = " ".join(executor.seen).upper()
    assert "ROW LEVEL SECURITY" not in joined
    assert "SET LOCAL" not in joined
