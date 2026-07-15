"""Sprint 44 - project service acceptance tests."""
from __future__ import annotations

import pytest

from secondbrain.tasks.models import Status
from secondbrain.tasks.service import TaskProjectService, TaskServiceError


def _svc(tmp_path):
    return TaskProjectService(tmp_path)


def test_create_update_archive_project(tmp_path):
    s = _svc(tmp_path)
    p = s.create_project(workspace_id="w1", title="P", priority="high")
    assert p.priority == "high" and p.status == Status.PLANNED.value
    up = s.update_project(p.project_id, workspace_id="w1", status="active", description="desc")
    assert up.status == "active" and up.description == "desc"
    arch = s.archive_project(p.project_id, workspace_id="w1")
    assert arch.status == Status.ARCHIVED.value and arch.archived_at


def test_project_contains_tasks_and_progress(tmp_path):
    s = _svc(tmp_path)
    p = s.create_project(workspace_id="w1", title="P")
    a = s.create_task(workspace_id="w1", title="a", project_id=p.project_id, status="active")
    s.create_task(workspace_id="w1", title="b", project_id=p.project_id)
    assert len(s.list_tasks(workspace_id="w1", project_id=p.project_id)) == 2
    s.complete_task(a.task_id, workspace_id="w1")
    assert s.list_projects(workspace_id="w1")[0].progress == 50.0


def test_list_projects_excludes_archived_by_default(tmp_path):
    s = _svc(tmp_path)
    p = s.create_project(workspace_id="w1", title="P")
    s.archive_project(p.project_id, workspace_id="w1")
    assert s.list_projects(workspace_id="w1") == []
    assert len(s.list_projects(workspace_id="w1", include_archived=True)) == 1


def test_project_workspace_isolation(tmp_path):
    s = _svc(tmp_path)
    s.create_project(workspace_id="w1", title="A")
    s.create_project(workspace_id="w2", title="B")
    assert len(s.list_projects(workspace_id="w1")) == 1
    assert len(s.list_projects(workspace_id="w2")) == 1


def test_update_missing_project_raises(tmp_path):
    s = _svc(tmp_path)
    with pytest.raises(TaskServiceError):
        s.update_project("prj_missing", workspace_id="w1", status="active")
