"""Framework-neutral view model for the native update center GUI."""
from __future__ import annotations

from typing import Any, Mapping

from .runtime import InstallerUpdateRuntime


class UpdateCenterViewModel:
    def __init__(self, updater: InstallerUpdateRuntime) -> None:
        self.updater = updater
        self.available_version: str | None = None
        self.release_notes = ""
        self.download_progress = 0
        self.installation_status = "idle"
        self.error_details = ""

    def refresh(self, manifest: Mapping[str, Any] | None = None) -> dict[str, Any]:
        result = self.updater.check_for_updates(manifest)
        data = result.get("manifest", {})
        self.available_version = data.get("application_version")
        self.release_notes = data.get("release_notes", "")
        self.installation_status = result["status"]
        self.error_details = result.get("detail", "")
        return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "current_version": self.updater.current_version,
            "available_version": self.available_version,
            "release_notes": self.release_notes,
            "download_progress": self.download_progress,
            "installation_status": self.installation_status,
            "update_history": self.updater.update_history(),
            "rollback_available": bool(self.updater.store.load("update_backups", [])),
            "channel": self.updater.channel(),
            "channels": list(("stable", "beta", "development")),
            "error_details": self.error_details,
        }
