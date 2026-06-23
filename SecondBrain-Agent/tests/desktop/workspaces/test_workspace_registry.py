from secondbrain.desktop.workspaces import DuplicateWorkspaceError, WorkspaceRef, WorkspaceRegistry, WorkspaceStore


def registry(tmp_path):
    return WorkspaceRegistry(WorkspaceStore(tmp_path / "workspaces.json"), default_root=tmp_path / "default")


def test_registry_creates_default_workspace(tmp_path):
    reg = registry(tmp_path)

    assert reg.active().workspace_id == "default"
    assert reg.default_workspace().is_default is True
    assert len(reg.list_workspaces()) == 1


def test_add_and_switch_workspace_persists_active_workspace(tmp_path):
    store = WorkspaceStore(tmp_path / "workspaces.json")
    reg = WorkspaceRegistry(store, default_root=tmp_path / "default")
    reg.add_workspace(WorkspaceRef("w1", "Work", str(tmp_path / "w1")), activate=False)

    switched = reg.switch("w1")

    assert switched.workspace_id == "w1"
    assert switched.last_opened_at is not None
    reloaded = WorkspaceRegistry(store, default_root=tmp_path / "default")
    assert reloaded.active().workspace_id == "w1"


def test_duplicate_workspace_is_rejected(tmp_path):
    reg = registry(tmp_path)
    reg.add_workspace(WorkspaceRef("w1", "Work", str(tmp_path / "w1")))

    try:
        reg.add_workspace(WorkspaceRef("w1", "Other", str(tmp_path / "w2")))
    except DuplicateWorkspaceError:
        pass
    else:
        raise AssertionError("duplicate workspace was accepted")


def test_default_workspace_cannot_be_removed(tmp_path):
    reg = registry(tmp_path)

    try:
        reg.remove("default")
    except ValueError as exc:
        assert "default workspace" in str(exc)
    else:
        raise AssertionError("default workspace was removed")
