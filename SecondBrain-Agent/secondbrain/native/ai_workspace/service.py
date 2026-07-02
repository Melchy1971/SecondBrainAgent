from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .models import ApplicationState, WorkspaceModuleState, WorkspaceSnapshot, normalize_project_root


class AIWorkspaceService:
    """Native AI workspace composition layer.

    The service is intentionally offline-safe. It does not execute tools during status
    collection; it checks module availability and builds one consistent surface model
    for the native desktop shell.
    """

    VERSION = "v30.45"

    MODULES = (
        ("dashboard", "Dashboard", "dashboard-center-gui", ("secondbrain/native/dashboard_center",)),
        ("layout", "Layout", "layout-status", ("secondbrain/native/layout_center",)),
        ("workspace", "Workspace", "workspace-center-gui", ("secondbrain/native/workspace_center.py",)),
        ("chat", "Chat", "native-chat-status", ("secondbrain/native/chat.py",)),
        ("documents", "Document Explorer", "document-explorer-gui", ("secondbrain/native/document_explorer.py",)),
        ("memory", "Memory Explorer", "memory-explorer", ("secondbrain/native/memory_explorer.py",)),
        ("agents", "Agent Control", "agent-control-gui", ("secondbrain/native/agent_control_center.py",)),
        ("voice", "Voice Control", "voice-control-status", ("secondbrain/native/voice_control_center.py",)),
        ("commands", "Command Center", "command-center-gui", ("secondbrain/native/command_center.py",)),
        ("jobs", "Job Queue", "job-queue-center-gui", ("secondbrain/native/job_queue_center",)),
        ("notifications", "Notification Center", "notification-center-gui", ("secondbrain/native/notification_center",)),
        ("settings", "Settings Center", "gui-status", ("secondbrain/gui/settings_center.py",)),
        ("themes", "Theme Center", "theme-status", ("secondbrain/native/theme_center",)),
        ("updates", "Update Center", "status", ("secondbrain/update_system.py",)),
        ("health", "Desktop Health", "native-desktop-health", ("secondbrain/native/desktop_health",)),
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

    def application_state(self) -> ApplicationState:
        snapshot = self.snapshot()
        state = ApplicationState(
            project_root=snapshot.project_root,
            version=snapshot.version,
            modules=list(snapshot.modules),
        )
        state.replace_modules(list(snapshot.modules))
        return state

    def module_payload(self, module_id: str) -> dict[str, Any]:
        """Load one module's existing service model without coupling it to Tk."""
        providers = {
            "dashboard": self._dashboard_payload,
            "layout": self._layout_payload,
            "workspace": self._workspace_payload,
            "chat": self._chat_payload,
            "documents": self._documents_payload,
            "memory": self._memory_payload,
            "agents": self._agents_payload,
            "voice": self._voice_payload,
            "commands": self._commands_payload,
            "jobs": self._jobs_payload,
            "notifications": self._notifications_payload,
            "settings": self._settings_payload,
            "themes": self._themes_payload,
            "updates": self._updates_payload,
            "health": self._health_payload,
            "installer": self._installer_payload,
        }
        provider = providers.get(module_id)
        if provider is None:
            return {"ok": False, "status": "unknown_module", "module": module_id}
        try:
            return provider()
        except Exception as exc:
            return {"ok": False, "status": "module_error", "module": module_id, "error": type(exc).__name__, "detail": str(exc)}

    def _dashboard_payload(self) -> dict[str, Any]:
        from secondbrain.native.dashboard_center.service import NativeDashboardService
        return NativeDashboardService(self.project_root).snapshot().to_dict()

    def _workspace_payload(self) -> dict[str, Any]:
        from secondbrain.native.workspace_center import workspace_status
        return workspace_status(self.project_root)

    def _layout_payload(self) -> dict[str, Any]:
        from secondbrain.native.layout_center.service import NativeLayoutService
        return NativeLayoutService(self.project_root).status()

    def _chat_payload(self) -> dict[str, Any]:
        from secondbrain.native.chat import native_chat_status
        return native_chat_status(self.project_root)

    def _documents_payload(self) -> dict[str, Any]:
        from secondbrain.native.document_explorer import DocumentExplorer
        return DocumentExplorer(self.project_root).status()

    def _memory_payload(self) -> dict[str, Any]:
        from secondbrain.native.memory_explorer import MemoryExplorer
        return MemoryExplorer(self.project_root).status()

    def _agents_payload(self) -> dict[str, Any]:
        from secondbrain.native.agent_control_center import AgentControlCenter
        return AgentControlCenter(self.project_root).status()

    def _voice_payload(self) -> dict[str, Any]:
        from secondbrain.native.voice_control_center import voice_center_status
        return voice_center_status()

    def _commands_payload(self) -> dict[str, Any]:
        from secondbrain.native.command_center import CommandCenter
        return CommandCenter(self.project_root).status()

    def _jobs_payload(self) -> dict[str, Any]:
        from secondbrain.native.job_queue_center.service import JobQueueService
        return JobQueueService(self.project_root).snapshot()

    def _notifications_payload(self) -> dict[str, Any]:
        from secondbrain.native.notification_center.service import NotificationCenterService
        return NotificationCenterService(self.project_root).status()

    def _settings_payload(self) -> dict[str, Any]:
        from secondbrain.gui.settings_center import SettingsCenter
        return {"ok": True, **SettingsCenter().render_embedding_settings()}

    def _themes_payload(self) -> dict[str, Any]:
        from secondbrain.native.theme_center.service import ThemeCenterService
        return ThemeCenterService(self.project_root).status()

    def _updates_payload(self) -> dict[str, Any]:
        release_notes = self.project_root / "RELEASE_NOTES.md"
        return {
            "ok": release_notes.exists(),
            "mode": "manual",
            "current_version": self.current_version(),
            "release_notes": str(release_notes),
            "rules": ["backup_before_update", "production_gate_after_update", "preserve_local_secrets"],
        }

    def _health_payload(self) -> dict[str, Any]:
        from secondbrain.native.desktop_health.service import NativeDesktopHealthService
        return NativeDesktopHealthService(self.project_root).status()

    def _installer_payload(self) -> dict[str, Any]:
        return {
            "ok": (self.project_root / "secondbrain" / "native" / "installer_center.py").exists(),
            "mode": "native_installer",
            "module": "secondbrain.native.installer_center",
        }

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
