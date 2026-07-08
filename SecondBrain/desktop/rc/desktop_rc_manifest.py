from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class DesktopRCManifest:
    rc_version: str
    build_id: str
    created_at: str
    desktop_modules: list[str]
    test_summary: dict[str, Any]
    gate_status: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rc_version": self.rc_version,
            "build_id": self.build_id,
            "created_at": self.created_at,
            "desktop_modules": list(self.desktop_modules),
            "test_summary": dict(self.test_summary),
            "gate_status": self.gate_status,
            "notes": list(self.notes),
        }


class DesktopRCManifestBuilder:
    REQUIRED_MODULES = [
        "desktop.state",
        "desktop.router",
        "desktop.events",
        "desktop.commands",
        "desktop.notifications",
        "desktop.status_service",
        "desktop.workspace_manager",
        "desktop.jobs",
    ]

    def build(
        self,
        rc_version: str,
        gate_status: str,
        test_summary: dict[str, Any],
        modules: list[str] | None = None,
        notes: list[str] | None = None,
    ) -> DesktopRCManifest:
        module_list = modules or self.REQUIRED_MODULES
        build_id = f"desktop-rc-{rc_version.replace('.', '-')}-{len(module_list)}"
        return DesktopRCManifest(
            rc_version=rc_version,
            build_id=build_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            desktop_modules=list(module_list),
            test_summary=dict(test_summary),
            gate_status=gate_status,
            notes=list(notes or []),
        )
