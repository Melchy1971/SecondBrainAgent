"""v30.48 integration facade for the existing ProjectCenter."""
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from secondbrain.desktop.workspace_manager import WorkspaceManager
from secondbrain.desktop_pro.projects import ProjectCenter
from secondbrain.desktop_pro.store import DesktopStore
from secondbrain.security.rbac import RBAC


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _tags(values: Iterable[str]) -> list[str]:
    return sorted({str(value).strip().lower() for value in values if str(value).strip()})


class ProjectWorkspaceService:
    """Adds workspace presentation and lifecycle actions to ProjectCenter.

    It deliberately uses ``data/desktop_pro/projects.json`` and does not create
    a second project catalog.
    """

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root).resolve()
        self.store = DesktopStore(self.project_root)
        self.projects_service = ProjectCenter(self.store)
        self.workspaces_service = WorkspaceManager(self.project_root / ".config" / "secondbrain")
        self.rbac = RBAC(self.store)

    @staticmethod
    def normalize(row: dict[str, Any]) -> dict[str, Any]:
        state = row.get("state") or ("archived" if row.get("archived") else "active")
        now = _now()
        return {**row, "id": str(row.get("id") or ""), "name": str(row.get("name") or "").strip(),
                "status": str(row.get("status") or "active"), "risk": str(row.get("risk") or "medium"),
                "workspace_id": str(row.get("workspace_id") or "default"), "tags": _tags(row.get("tags") or []),
                "favorite": bool(row.get("favorite")), "state": state if state in {"active", "archived", "trash"} else "active",
                "created_at": row.get("created_at") or now, "updated_at": row.get("updated_at") or now,
                "archived_at": row.get("archived_at"), "deleted_at": row.get("deleted_at")}

    def projects(self, *, view="active", query="", tags=(), workspace_id=None) -> list[dict[str, Any]]:
        if view not in {"all", "active", "favorites", "archive", "trash"}:
            raise ValueError(f"unknown project view: {view}")
        wanted, query = set(_tags(tags)), query.strip().lower()
        rows = [self.normalize(row) for row in self.projects_service.projects()]
        def visible(row):
            if view == "active" and row["state"] != "active": return False
            if view == "favorites" and (row["state"] == "trash" or not row["favorite"]): return False
            if view == "archive" and row["state"] != "archived": return False
            if view == "trash" and row["state"] != "trash": return False
            if workspace_id and row["workspace_id"] != workspace_id: return False
            if wanted and not wanted.issubset(row["tags"]): return False
            text = " ".join((row["name"], row["status"], row["risk"], row["workspace_id"], *row["tags"])).lower()
            return not query or query in text
        return sorted(filter(visible, rows), key=lambda row: (not row["favorite"], row["name"].lower()))

    def add_project(self, name, *, status="active", risk="medium", workspace_id="default", tags=()) -> dict:
        name = name.strip()
        if not name: raise ValueError("project name must not be empty")
        self.workspaces_service.registry.get(workspace_id)
        now = _now()
        return self.store.append("projects", {"id": f"proj_{uuid4().hex[:12]}", "name": name, "status": status,
            "risk": risk, "workspace_id": workspace_id, "tags": _tags(tags), "favorite": False,
            "state": "active", "created_at": now, "updated_at": now, "archived_at": None, "deleted_at": None})

    def update(self, project_id: str, **changes) -> dict:
        rows = self.projects(view="all")
        for index, row in enumerate(rows):
            if row["id"] != project_id: continue
            if "tags" in changes: changes["tags"] = _tags(changes["tags"])
            rows[index] = {**row, **changes, "updated_at": _now()}
            self.store.save("projects", rows)
            return rows[index]
        raise KeyError(project_id)

    def set_favorite(self, project_id, value=True): return self.update(project_id, favorite=bool(value))
    def set_tags(self, project_id, tags): return self.update(project_id, tags=tags)
    def archive(self, project_id): return self.update(project_id, state="archived", archived_at=_now(), deleted_at=None)
    def trash(self, project_id): return self.update(project_id, state="trash", deleted_at=_now())
    def restore(self, project_id): return self.update(project_id, state="active", archived_at=None, deleted_at=None)

    def workspaces(self) -> list[dict[str, Any]]:
        active = self.workspaces_service.current_workspace().workspace_id
        return [{**row.to_dict(), "active": row.workspace_id == active} for row in self.workspaces_service.list_workspaces()]

    def create_workspace(self, workspace_id, name, root_path):
        return self.workspaces_service.create_workspace(workspace_id.strip(), name.strip(), root_path).to_dict()

    def switch_workspace(self, workspace_id): return self.workspaces_service.switch_workspace(workspace_id).to_dict()
    def add_user(self, user_id, display_name=None, role="viewer"): return self.rbac.add_user(user_id, display_name=display_name, role=role)
    def add_role(self, name, permissions): return self.rbac.add_role(name, permissions)

    def export_data(self, target=None) -> dict[str, Any]:
        payload = {"schema": "secondbrain.projects.v30.48", "projects": self.projects(view="all"),
                   "workspaces": self.workspaces(), "access": self.rbac.snapshot()}
        if target:
            path = Path(target); path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def import_data(self, source) -> dict[str, Any]:
        data = json.loads(Path(source).read_text(encoding="utf-8")) if isinstance(source, (str, Path)) else source
        incoming = data.get("projects", []) if isinstance(data, dict) else data
        if not isinstance(incoming, list): raise ValueError("projects list required")
        rows, imported = self.projects(view="all"), 0
        ids = {row["id"] for row in rows}
        for raw in incoming:
            if not isinstance(raw, dict) or not str(raw.get("name", "")).strip(): continue
            row = self.normalize(raw)
            if not row["id"] or row["id"] in ids: row["id"] = f"proj_{uuid4().hex[:12]}"
            rows.append(row); ids.add(row["id"]); imported += 1
        self.store.save("projects", rows)
        return {"ok": True, "imported": imported, "total": len(rows)}

    def snapshot(self, **filters) -> dict[str, Any]:
        all_rows = self.projects(view="all")
        summary = {"projects": len(all_rows), "active": sum(row["state"] == "active" for row in all_rows),
                   "favorites": sum(row["favorite"] for row in all_rows), "archived": sum(row["state"] == "archived" for row in all_rows),
                   "trash": sum(row["state"] == "trash" for row in all_rows), "workspaces": len(self.workspaces()),
                   "users": len(self.rbac.users()), "roles": len(self.rbac.roles())}
        return {"ok": True, "version": "30.48", "mode": "existing_project_center",
                "projects": self.projects(**filters), "workspaces": self.workspaces(),
                "tags": sorted({tag for row in all_rows for tag in row["tags"]}),
                "access": self.rbac.snapshot(), "summary": summary, "filters": filters}
