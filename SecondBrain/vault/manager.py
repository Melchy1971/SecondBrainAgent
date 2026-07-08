"""SecretManager - service/view-model the GUI binds to.

Exposes only what a UI needs: list rows (no values), add, reveal-on-demand,
delete, rotate, health, migrate, import/export. Every reveal is audited and the
revealed value is registered with the redactor so it cannot leak into logs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from secondbrain.vault import health as vault_health
from secondbrain.vault import migration as vault_migration
from secondbrain.vault.store import SecretVault


class SecretManager:
    def __init__(
        self,
        vault_dir: str | Path,
        *,
        env: Mapping[str, str] | None = None,
        allow_generate: bool = True,
        actor: str = "gui",
    ) -> None:
        self.vault = SecretVault(vault_dir, env=env, allow_generate=allow_generate, actor=actor)

    def rows(self, *, workspace: str | None = None) -> list[dict[str, Any]]:
        """Table rows for the GUI. Values are masked; never included."""
        rows = []
        for record in self.vault.list_secrets(workspace=workspace):
            rows.append({
                "workspace": record["workspace"],
                "name": record["name"],
                "reference": record["reference"],
                "value_masked": "********",
                "dek_version": record["dek_version"],
                "updated_at": record["updated_at"],
                "origin": record["meta"].get("origin", "manual"),
            })
        return rows

    def workspaces(self) -> list[str]:
        return self.vault.workspaces()

    def add_secret(self, name: str, value: str, *, workspace: str = "default") -> str:
        return self.vault.put_secret(name, value, workspace=workspace)

    def reveal_secret(self, name: str, *, workspace: str = "default") -> str:
        return self.vault.get_secret(name, workspace=workspace)

    def delete_secret(self, name: str, *, workspace: str = "default") -> bool:
        return self.vault.delete_secret(name, workspace=workspace)

    def rotate_key(self) -> int:
        return self.vault.rotate_data_key()

    def health(self, *, scan_paths: list[str | Path] | None = None) -> dict[str, Any]:
        return vault_health.health_check(self.vault, scan_paths=scan_paths)

    def migrate(self, project_root: str | Path, *, workspace: str = "default", rewrite_env: bool = False) -> dict[str, Any]:
        return vault_migration.migrate_all(self.vault, project_root, workspace=workspace, rewrite_env=rewrite_env)

    def export_bundle(self, path: str | Path, passphrase: str, *, workspace: str | None = None) -> Path:
        return self.vault.export_encrypted(path, passphrase, workspace=workspace)

    def import_bundle(self, path: str | Path, passphrase: str, *, overwrite: bool = False) -> int:
        return self.vault.import_encrypted(path, passphrase, overwrite=overwrite)

    def audit_entries(self) -> list[dict[str, Any]]:
        return self.vault.audit.entries()
