import pytest
from secondbrain.desktop.workspace_manager import WorkspaceManager


def test_workspace_manager_creates_workspace():
    manager = WorkspaceManager()
    workspace = manager.create(" Main ")

    assert workspace.name == "Main"
    assert manager.get(workspace.id) == workspace
    assert manager.list() == [workspace]


def test_workspace_manager_rejects_empty_name():
    manager = WorkspaceManager()
    with pytest.raises(ValueError):
        manager.create(" ")
