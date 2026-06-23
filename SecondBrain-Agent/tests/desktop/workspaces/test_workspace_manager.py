from secondbrain.desktop.workspace_manager import WorkspaceManager


def test_manager_creates_switches_and_resolves_workspace_paths(tmp_path):
    manager = WorkspaceManager(tmp_path / "config")

    manager.create_workspace("project-a", "Project A", tmp_path / "project-a")
    assert manager.current_workspace().workspace_id == "project-a"
    assert manager.workspace_path("docs", "inbox").as_posix().endswith("project-a/docs/inbox")

    manager.switch_workspace("default")
    assert manager.current_workspace().workspace_id == "default"
    assert len(manager.list_workspaces()) == 2


def test_manager_persists_workspace_registry(tmp_path):
    config = tmp_path / "config"
    manager = WorkspaceManager(config)
    manager.create_workspace("project-a", "Project A", tmp_path / "project-a")

    reloaded = WorkspaceManager(config)

    assert reloaded.current_workspace().workspace_id == "project-a"
    assert {workspace.workspace_id for workspace in reloaded.list_workspaces()} == {"default", "project-a"}
