"""Persistence and concurrency contract for the integrated task repository."""

from __future__ import annotations

import pytest

from secondbrain.tasks.service import TaskProjectService, VersionConflict


def test_repository_persists_and_isolates_workspaces(tmp_path):
    service = TaskProjectService(tmp_path)
    task = service.create_task(workspace_id="alpha", title="Persisted")
    service.create_task(workspace_id="beta", title="Private")

    restarted = TaskProjectService(tmp_path)
    assert restarted.get_task(task.task_id, workspace_id="alpha") is not None
    assert restarted.get_task(task.task_id, workspace_id="beta") is None
    assert [item.title for item in restarted.list_tasks(workspace_id="beta")] == ["Private"]


def test_task_optimistic_version_prevents_lost_update(tmp_path):
    service = TaskProjectService(tmp_path)
    task = service.create_task(workspace_id="alpha", title="Initial")
    updated = service.update_task(task.task_id, workspace_id="alpha", title="First", expected_version=1)
    assert updated.version == 2

    with pytest.raises(VersionConflict):
        service.update_task(task.task_id, workspace_id="alpha", title="Stale", expected_version=1)


def test_project_optimistic_version_prevents_lost_update(tmp_path):
    service = TaskProjectService(tmp_path)
    project = service.create_project(workspace_id="alpha", title="Project")
    updated = service.update_project(project.project_id, workspace_id="alpha", title="Current", expected_version=1)
    assert updated.version == 2

    with pytest.raises(VersionConflict):
        service.update_project(project.project_id, workspace_id="alpha", title="Stale", expected_version=1)
