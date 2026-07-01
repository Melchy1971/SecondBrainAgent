from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from .models import DashboardCard, DashboardSnapshot, normalize_project_root


class NativeDashboardService:
    """Offline-safe native dashboard aggregation layer.

    The dashboard must not execute expensive imports, sync jobs or write actions.
    It reads status files, environment flags and native runtime logs to build one
    truthful cockpit for the Jarvis desktop shell.
    """

    VERSION = "v30.40"

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = normalize_project_root(project_root)
        self.runtime_dir = self.project_root / "runtime" / "native" / "dashboard_center"
        self.activity_path = self.runtime_dir / "dashboard_activity.jsonl"

    def ensure_dirs(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def current_version(self) -> str:
        status_file = self.project_root / "docs" / "09_MASTERPLAN_STATUS.json"
        if status_file.exists():
            try:
                data = json.loads(status_file.read_text(encoding="utf-8"))
                return str(data.get("current_version") or data.get("version") or self.VERSION)
            except Exception:
                return self.VERSION
        return self.VERSION

    def _exists(self, *parts: str) -> bool:
        return (self.project_root.joinpath(*parts)).exists()

    def _json_file(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"ok": False, "error": "invalid_json", "path": str(path), "detail": str(exc)}

    def _activity_count(self, path: Path) -> int:
        if not path.exists():
            return 0
        try:
            return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())
        except Exception:
            return 0

    def _status_from_bool(self, condition: bool, warning: bool = False) -> str:
        if condition:
            return "ready"
        return "warning" if warning else "blocked"

    def _card(self, card_id: str, title: str, status: str, value: Any, description: str, command: str | None = None, blockers: list[str] | None = None, warnings: list[str] | None = None) -> DashboardCard:
        return DashboardCard(card_id, title, status, value, description, command, blockers or [], warnings or [])

    def _desktop_card(self) -> DashboardCard:
        native_exists = self._exists("secondbrain", "native")
        surface = os.environ.get("SECONDBRAIN_SURFACE", "native")
        warnings = [] if surface == "native" else ["surface_not_native"]
        return self._card(
            "desktop",
            "Native Desktop",
            "ready" if native_exists and surface == "native" else "warning",
            surface,
            "Primäre Jarvis-Oberfläche.",
            "ai-workspace-gui",
            warnings=warnings,
        )

    def _database_card(self) -> DashboardCard:
        database_url = os.environ.get("DATABASE_URL", "")
        if database_url.startswith(("postgresql://", "postgres://")):
            return self._card("database", "PostgreSQL / pgvector", "ready", "configured", "DATABASE_URL ist auf PostgreSQL gesetzt.", "p3-pgvector-readiness")
        return self._card("database", "PostgreSQL / pgvector", "warning", "not_configured", "Keine produktive PostgreSQL-Verbindung in ENV sichtbar.", "settings-center-gui", warnings=["database_url_missing"])

    def _embedding_card(self) -> DashboardCard:
        provider = os.environ.get("SECONDBRAIN_EMBEDDING_PROVIDER", "local")
        if provider in {"openai", "ollama"}:
            return self._card("embeddings", "Embeddings", "ready", provider, "Produktiver Embedding-Provider ist konfiguriert.", "p1-provider-health")
        return self._card("embeddings", "Embeddings", "warning", provider, "Lokale Embeddings sind für Entwicklung ok, nicht für Produktion.", "settings-center-gui", warnings=["local_embeddings_not_production_ready"])

    def _module_card(self, card_id: str, title: str, path: str, command: str) -> DashboardCard:
        exists = self._exists(*path.split("/"))
        return self._card(card_id, title, "ready" if exists else "blocked", "available" if exists else "missing", f"Native Oberfläche: {title}.", command, blockers=[] if exists else [f"missing_module:{card_id}"])

    def _runtime_card(self) -> DashboardCard:
        runtime = self.project_root / "runtime" / "native"
        count = 0
        if runtime.exists():
            try:
                count = sum(1 for _ in runtime.rglob("*.jsonl"))
            except Exception:
                count = 0
        return self._card("runtime", "Runtime Logs", "ready", count, "Anzahl nativer JSONL-Runtime-Protokolle.", "dashboard-center-activity")

    def _security_card(self) -> DashboardCard:
        approval = os.environ.get("SECONDBRAIN_APPROVAL_REQUIRED", "true").lower() in {"1", "true", "yes", "on"}
        vault = os.environ.get("SECONDBRAIN_SECRET_VAULT", "false").lower() in {"1", "true", "yes", "on"}
        warnings = [] if vault else ["secret_vault_not_enabled"]
        blockers = [] if approval else ["approval_required_disabled"]
        status = "blocked" if blockers else "warning" if warnings else "ready"
        return self._card("security", "Security", status, {"approval_required": approval, "secret_vault": vault}, "Freigaben, Privacy Mode und Secret Vault.", "settings-center-gui", blockers, warnings)

    def snapshot(self) -> DashboardSnapshot:
        cards = [
            self._desktop_card(),
            self._database_card(),
            self._embedding_card(),
            self._module_card("chat", "Chat Center", "secondbrain/native/chat_center", "native-chat-status"),
            self._module_card("documents", "Document Explorer", "secondbrain/native/document_explorer", "document-explorer-status"),
            self._module_card("memory", "Memory Explorer", "secondbrain/native/memory_explorer", "memory-explorer-status"),
            self._module_card("agents", "Agent Control", "secondbrain/native/agent_control_center", "agent-control-status"),
            self._module_card("voice", "Voice Control", "secondbrain/native/voice_control_center", "voice-control-status"),
            self._module_card("commands", "Command Center", "secondbrain/native/command_center", "command-center-status"),
            self._module_card("settings", "Settings Center", "secondbrain/native/settings_center", "settings-center-status"),
            self._module_card("updates", "Update Center", "secondbrain/native/update_center", "update-status"),
            self._runtime_card(),
            self._security_card(),
        ]
        blockers = [item for card in cards for item in card.blockers]
        warnings = [item for card in cards for item in card.warnings]
        activity_count = self._activity_count(self.activity_path)
        return DashboardSnapshot(
            ok=not blockers,
            version=self.current_version(),
            project_root=str(self.project_root),
            surface="native_dashboard_center",
            cards=cards,
            blockers=blockers,
            warnings=warnings,
            activity_count=activity_count,
        )

    def status(self) -> dict[str, Any]:
        snap = self.snapshot().to_dict()
        snap["ready_cards"] = sum(1 for c in snap["cards"] if c["status"] == "ready")
        snap["warning_cards"] = sum(1 for c in snap["cards"] if c["status"] == "warning")
        snap["blocked_cards"] = sum(1 for c in snap["cards"] if c["status"] == "blocked")
        snap["ok"] = True
        return snap

    def activity(self, limit: int = 50) -> dict[str, Any]:
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
                rows.append({"event": "invalid_dashboard_activity_line", "raw": line[:200]})
        rows = rows[-limit:]
        rows.reverse()
        return {"ok": True, "items": rows, "count": len(rows)}

    def record_activity(self, event: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_dirs()
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, "payload": payload or {}}
        with self.activity_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return {"ok": True, "recorded": row}
