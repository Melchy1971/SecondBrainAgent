"""Host-enforced path and capability boundary exposed to trusted plugins."""
from __future__ import annotations

from pathlib import Path

from secondbrain.plugins.permissions import PluginPermission, PluginPermissionPolicy


class PluginSandbox:
    """Restricts API operations; Python activation still requires explicit host trust."""

    def __init__(self, project_root: str | Path, plugin_root: str | Path, plugin_id: str,
                 policy: PluginPermissionPolicy) -> None:
        self.project_root = Path(project_root).resolve()
        self.plugin_root = Path(plugin_root).resolve()
        self.plugin_id = plugin_id
        self.policy = policy
        self.data_root = self.project_root / "runtime" / "plugins" / "data" / plugin_id

    def resolve_entrypoint(self, relative_path: str) -> Path:
        path = (self.plugin_root / relative_path).resolve()
        if not path.is_relative_to(self.plugin_root) or not path.is_file():
            raise PermissionError(f"plugin_entrypoint_outside_root:{self.plugin_id}")
        return path

    def workspace_path(self, relative_path: str, *, write=False) -> Path:
        permission = PluginPermission.WORKSPACE_WRITE if write else PluginPermission.WORKSPACE_READ
        self.policy.require(permission, action=f"workspace:{relative_path}")
        candidate = (self.project_root / relative_path).resolve()
        if not candidate.is_relative_to(self.project_root):
            raise PermissionError(f"plugin_workspace_path_outside_root:{self.plugin_id}")
        relative = candidate.relative_to(self.project_root)
        lowered = [part.lower() for part in relative.parts]
        if lowered and lowered[0] in {".git", ".agents", ".codex"}:
            raise PermissionError(f"plugin_workspace_path_protected:{self.plugin_id}")
        settings_root = self.project_root / "runtime" / "plugins" / "settings"
        if candidate == settings_root or candidate.is_relative_to(settings_root):
            raise PermissionError(f"plugin_settings_api_required:{self.plugin_id}")
        name = candidate.name.lower()
        if name == ".env" or name.startswith(".env.") or name.endswith((".pem", ".key")) or name == "credentials.json":
            self.policy.require(PluginPermission.SECRETS, action=f"secret:{relative_path}")
        return candidate

    def read_text(self, relative_path: str, *, max_chars: int = 1_000_000) -> str:
        path = self.workspace_path(relative_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        limit = max(1, min(int(max_chars), 1_000_000))
        return path.read_text(encoding="utf-8", errors="replace")[:limit]

    def write_text(self, relative_path: str, content: str) -> Path:
        path = self.workspace_path(relative_path, write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding="utf-8")
        return path

    def data_path(self, relative_path: str = ".") -> Path:
        candidate = (self.data_root / relative_path).resolve()
        if not candidate.is_relative_to(self.data_root):
            raise PermissionError(f"plugin_data_path_outside_root:{self.plugin_id}")
        return candidate
