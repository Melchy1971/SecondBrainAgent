from __future__ import annotations

import json

from secondbrain.native.ai_workspace.service import AIWorkspaceService
from secondbrain.native.project_workspace import ProjectWorkspaceService


def test_project_lifecycle_search_filter_and_tags(tmp_path):
    service = ProjectWorkspaceService(tmp_path)
    project = service.add_project("Migration", risk="high", tags=["SAP", "2026"])
    assert service.projects(query="sap")[0]["id"] == project["id"]
    service.set_favorite(project["id"])
    assert service.projects(view="favorites")[0]["favorite"] is True
    service.archive(project["id"])
    assert service.projects(view="archive")[0]["state"] == "archived"
    service.trash(project["id"])
    assert service.projects(view="trash")[0]["state"] == "trash"
    service.restore(project["id"])
    assert service.projects(view="active")[0]["state"] == "active"


def test_workspaces_users_roles_and_permissions_share_existing_services(tmp_path):
    service = ProjectWorkspaceService(tmp_path)
    workspace = service.create_workspace("kunde-a", "Kunde A", tmp_path / "kunde-a")
    service.switch_workspace(workspace["workspace_id"])
    user = service.add_user("anna", "Anna", "editor")
    assert service.workspaces()[1]["active"] is True
    assert user["role"] == "editor"
    assert "project.write" in user["permissions"]


def test_import_export_roundtrip_and_duplicate_ids(tmp_path):
    source = ProjectWorkspaceService(tmp_path / "source")
    project = source.add_project("Exportprojekt", tags=["export"])
    export_path = tmp_path / "projects.json"
    source.export_data(export_path)
    payload = json.loads(export_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "secondbrain.projects.v30.48"
    result = source.import_data(payload)
    assert result["imported"] == 1
    assert len({row["id"] for row in source.projects(view="all")}) == 2
    assert project["id"] in {row["id"] for row in source.projects(view="all")}


def test_ai_workspace_registers_existing_project_center(tmp_path):
    workspace = AIWorkspaceService(tmp_path)
    modules = {module.id: module for module in workspace.snapshot().modules}
    assert modules["projects"].status == "missing"

    repository_workspace = AIWorkspaceService(__file__)
    assert repository_workspace.VERSION == "v30.48"
