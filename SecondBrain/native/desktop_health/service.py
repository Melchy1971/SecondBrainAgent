from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from secondbrain.native.ai_workspace.service import AIWorkspaceService
from secondbrain.native.layout_center.service import NativeLayoutService
from secondbrain.native.theme_center.service import ThemeCenterService


@dataclass(frozen=True)
class HealthCheck:
    id: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class NativeDesktopHealthService:
    """Read-only integration checks with explicit report persistence."""

    VERSION = "v30.46"

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root).resolve()

    def checks(self) -> list[HealthCheck]:
        workspace = AIWorkspaceService(self.project_root).status()
        layout = NativeLayoutService(self.project_root).status()
        theme = ThemeCenterService(self.project_root).status()
        missing = [item["id"] for item in workspace["modules"] if item["status"] != "ready" and item["id"] not in {"settings", "updates"}]
        return [
            HealthCheck("python", "pass" if sys.version_info >= (3, 11) else "fail", sys.version.split()[0]),
            HealthCheck("launcher", "pass" if (self.project_root / "launcher.py").is_file() else "fail", str(self.project_root / "launcher.py")),
            HealthCheck("workspace", "pass" if not missing else "fail", "ready" if not missing else f"missing: {', '.join(missing)}"),
            HealthCheck("layout", "pass" if layout.get("ok") else "fail", str(layout.get("active", "unknown"))),
            HealthCheck("theme", "pass" if theme.get("ok") else "fail", str(theme.get("active_theme", "unknown"))),
            HealthCheck("runtime", "pass" if self._runtime_writable() else "fail", str(self.project_root / "runtime" / "native")),
        ]

    def _runtime_writable(self) -> bool:
        runtime = self.project_root / "runtime" / "native"
        existing = next((parent for parent in (runtime, runtime.parent, self.project_root) if parent.exists()), None)
        return existing is not None and os.access(existing, os.W_OK)

    def status(self) -> dict[str, Any]:
        checks = self.checks()
        failed = [check.id for check in checks if check.status == "fail"]
        return {
            "ok": not failed,
            "version": self.VERSION,
            "status": "pass" if not failed else "blocked",
            "project_root": str(self.project_root),
            "checks": [check.to_dict() for check in checks],
            "failed_checks": failed,
        }

    def write_report(self, target: str | Path | None = None) -> dict[str, Any]:
        payload = self.status()
        path = Path(target) if target else self.project_root / "runtime" / "reports" / "native_desktop_health_v30_46.json"
        if not path.is_absolute():
            path = self.project_root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        report = {**payload, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return {**payload, "report_path": str(path)}
