from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .models import WorkspaceModuleState, WorkspaceSnapshot, normalize_project_root


class AIWorkspaceService:
    """Native AI workspace composition layer.

    The service is intentionally offline-safe. It does not execute tools during status
    collection; it checks module availability and builds one consistent surface model
    for the native desktop shell.
    """

    VERSION = "v30.46"

    MODULES = (
        ("dashboard", "Dashboard", "dashboard-center-status", ("secondbrain/native/dashboard_center",)),
        ("layout", "Layout", "layout-status", ("secondbrain/native/layout_center",)),
        ("themes", "Themes", "theme-status", ("secondbrain/native/theme_center",)),
        ("notifications", "Benachrichtigungen", "notification-center-status", ("secondbrain/native/notification_center",)),
        ("jobs", "Jobs", "job-queue-status", ("secondbrain/native/job_queue_center",)),
        ("health", "Desktop Health", "native-desktop-health", ("secondbrain/native/desktop_health",)),
        ("chat", "Chat", "native-chat-status", ("secondbrain/native/chat.py",)),
        ("documents", "Dokumente", "document-explorer-status", ("secondbrain/native/document_explorer.py",)),
        ("memory", "Memory", "memory-explorer-status", ("secondbrain/native/memory_explorer.py",)),
        ("agents", "Agenten", "agent-control-status", ("secondbrain/native/agent_control_center.py",)),
        ("voice", "Sprache", "voice-control-status", ("secondbrain/native/voice_control_center.py",)),
        ("commands", "Kommandos", "command-center-status", ("secondbrain/native/command_center.py",)),
        ("settings", "Einstellungen", "settings-center-status", ("secondbrain/native/settings_center",)),
        ("updates", "Updates", "update-status", ("secondbrain/native/update_center",)),
        ("installer", "Installer", "native-installer-status", ("secondbrain/native/installer_center.py",)),
    )

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = normalize_project_root(project_root)
        self.runtime_dir = self.project_root / "runtime" / "native" / "ai_workspace"
        self.activity_path = self.runtime_dir / "workspace_activity.jsonl"

    def ensure_dirs(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def current_version(self) -> str:
        status_file = self.project_root / "docs" / "09_MASTERPLAN_STATUS.json"
        if status_file.exists():
            try:
                data = json.loads(status_file.read_text(encoding="utf-8"))
                documented = str(data.get("current_version") or data.get("version") or self.VERSION)
                return max((documented, self.VERSION), key=self._version_key)
            except Exception:
                return self.VERSION
        return self.VERSION

    @staticmethod
    def _version_key(value: str) -> tuple[int, ...]:
        raw = value.lower().removeprefix("v")
        try:
            return tuple(int(part) for part in raw.split("."))
        except ValueError:
            return (0,)

    def _module_exists(self, candidates: tuple[str, ...]) -> bool:
        return any((self.project_root / candidate).exists() for candidate in candidates)

    def _module_state(self, module_id: str, title: str, command: str, candidates: tuple[str, ...]) -> WorkspaceModuleState:
        exists = self._module_exists(candidates)
        if exists:
            return WorkspaceModuleState(
                id=module_id,
                title=title,
                status="ready",
                command=command,
                summary=f"{title} ist im nativen Workspace verfügbar.",
            )
        return WorkspaceModuleState(
            id=module_id,
            title=title,
            status="missing",
            command=command,
            summary=f"{title} ist noch nicht im Repository vorhanden.",
            blockers=[f"missing_module:{module_id}"],
        )

    def activity(self, limit: int = 30) -> dict[str, Any]:
        self.ensure_dirs()
        if not self.activity_path.exists():
            return {"ok": True, "items": [], "count": 0}
        rows: list[dict[str, Any]] = []
        for line in self.activity_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                rows.append({"event": "invalid_activity_line", "raw": line[:200]})
        rows = rows[-limit:]
        rows.reverse()
        return {"ok": True, "items": rows, "count": len(rows)}

    def record_activity(self, event: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_dirs()
        row = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event,
            "payload": payload or {},
        }
        with self.activity_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return {"ok": True, "recorded": row}

    def snapshot(self) -> WorkspaceSnapshot:
        modules = [self._module_state(*spec) for spec in self.MODULES]
        blockers = [blocker for module in modules for blocker in module.blockers]
        activity_count = int(self.activity(limit=100000).get("count", 0))
        return WorkspaceSnapshot(
            ok=not blockers,
            version=self.current_version(),
            project_root=str(self.project_root),
            primary_surface="native_ai_workspace",
            modules=modules,
            activity_count=activity_count,
            blockers=blockers,
        )

    def status(self) -> dict[str, Any]:
        snapshot = self.snapshot().to_dict()
        ready = [m for m in snapshot["modules"] if m["status"] == "ready"]
        missing = [m for m in snapshot["modules"] if m["status"] != "ready"]
        snapshot.update({
            "ok": True,
            "workspace_ready": len(missing) == 0,
            "ready_modules": len(ready),
            "missing_modules": len(missing),
        })
        return snapshot

    def navigation(self) -> dict[str, Any]:
        modules = [module.to_dict() for module in self.snapshot().modules]
        return {
            "ok": True,
            "navigation": [
                {"id": module["id"], "title": module["title"], "command": module["command"], "enabled": module["status"] == "ready"}
                for module in modules
            ],
        }
