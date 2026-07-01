from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkspaceActivity:
    kind: str
    title: str
    detail: str = ""
    section: str = "dashboard"
    ts: float = 0.0
    ok: bool | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if not data.get("ts"):
            data["ts"] = time.time()
        data["metadata"] = data.get("metadata") or {}
        return data


class WorkspaceActivityLog:
    """Local JSONL activity stream for the native workspace shell.

    Runtime file:
        runtime/native/activity_log.jsonl

    Design constraints:
    - no web server dependency
    - deterministic local writes
    - corrupt JSONL lines stay visible instead of being dropped silently
    """

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.path = self.project_root / "runtime" / "native" / "activity_log.jsonl"

    def append(self, activity: WorkspaceActivity | dict[str, Any]) -> dict[str, Any]:
        record = activity.to_dict() if isinstance(activity, WorkspaceActivity) else dict(activity)
        record.setdefault("ts", time.time())
        record.setdefault("kind", "event")
        record.setdefault("section", "dashboard")
        record.setdefault("metadata", {})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
        return record

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({
                    "kind": "invalid_record",
                    "title": "INVALID_ACTIVITY_RECORD",
                    "detail": line,
                    "section": "developer",
                    "ts": 0,
                    "ok": False,
                })
        return rows[-max(1, int(limit)):]

    def status(self, limit: int = 20) -> dict[str, Any]:
        items = self.list(limit=limit)
        total = 0
        if self.path.exists():
            total = sum(1 for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip())
        return {
            "ok": True,
            "schema": "secondbrain.native.workspace.activity.v30_30",
            "status": "ready",
            "path": str(self.path),
            "total_activities": total,
            "visible_activities": len(items),
            "activities": items,
        }


class NativeWorkspaceCenter:
    """Central native workspace aggregation layer.

    This module is deliberately a view-model bridge. It does not replace RAG,
    Memory, Chat or Command execution. It exposes one consistent desktop surface
    for the existing native modules.
    """

    SECTIONS = [
        {"id": "dashboard", "title": "Dashboard", "description": "Systemstatus und Runtime Truth"},
        {"id": "chat", "title": "Chat", "description": "Fragen, Antworten, Suchverlauf"},
        {"id": "documents", "title": "Dokumente", "description": "Importe, Parser, OCR, Index"},
        {"id": "search", "title": "Suche", "description": "Hybrid Search, Quellen, Golden Quality"},
        {"id": "memory", "title": "Memory", "description": "Notizen, Governance, Privacy"},
        {"id": "tasks", "title": "Aufgaben", "description": "Freigaben und offene Aktionen"},
        {"id": "agents", "title": "Agenten", "description": "Agent-Status und Tool-Ausführung"},
        {"id": "activity", "title": "Aktivitäten", "description": "Lokaler Workspace-Verlauf"},
        {"id": "settings", "title": "Einstellungen", "description": "Provider, Datenbank, Security"},
        {"id": "developer", "title": "Developer", "description": "Diagnose und JSON-Details"},
    ]

    def __init__(self, project_root: str | Path | None = None):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.activity = WorkspaceActivityLog(self.project_root)

    def status(self, limit: int = 12) -> dict[str, Any]:
        model = self._view_model()
        chat = self._chat_status(limit=limit)
        approvals = self._approval_status(limit=limit)
        activity = self.activity.status(limit=limit)
        sections = self.sections()
        return {
            "ok": True,
            "schema": "secondbrain.native.workspace.v30_30",
            "status": "ready",
            "version": "30.30",
            "project_root": str(self.project_root),
            "primary_surface": "native_workspace_center",
            "web_hud": "secondary_only",
            "sections": sections,
            "section_count": len(sections),
            "chat": chat,
            "documents": self._documents_summary(model),
            "search": self._search_summary(model),
            "memory": self._memory_summary(model),
            "tasks": approvals,
            "agents": self._agent_summary(model),
            "activity": activity,
            "runtime": self._runtime_summary(model),
        }

    def sections(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self.SECTIONS]

    def open_section(self, section_id: str) -> dict[str, Any]:
        wanted = (section_id or "").strip().lower()
        known = {item["id"]: item for item in self.SECTIONS}
        if wanted not in known:
            return {"ok": False, "status": "unknown_section", "section": wanted, "known_sections": sorted(known)}
        record = self.activity.append(WorkspaceActivity(
            kind="open_section",
            title=f"Bereich geöffnet: {known[wanted]['title']}",
            section=wanted,
            ok=True,
        ))
        return {"ok": True, "status": "opened", "section": known[wanted], "activity": record}

    def record_activity(self, title: str, *, kind: str = "event", section: str = "dashboard", detail: str = "", ok: bool | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if not (title or "").strip():
            return {"ok": False, "status": "empty_title", "error": "Aktivitätstitel fehlt"}
        record = self.activity.append(WorkspaceActivity(kind=kind, title=title.strip(), detail=detail, section=section, ok=ok, metadata=metadata or {}))
        return {"ok": True, "status": "recorded", "activity": record}

    def _view_model(self) -> dict[str, Any]:
        try:
            from secondbrain.native.runtime_snapshot import build_native_view_model
            value = build_native_view_model(self.project_root)
            return value if isinstance(value, dict) else {"ok": True, "value": value}
        except Exception as exc:
            return {"ok": False, "status": "runtime_model_unavailable", "error": f"{type(exc).__name__}: {exc}"}

    def _chat_status(self, limit: int = 12) -> dict[str, Any]:
        try:
            from secondbrain.native.chat import native_chat_status
            return native_chat_status(self.project_root, limit=limit)
        except Exception as exc:
            return {"ok": False, "status": "chat_unavailable", "error": f"{type(exc).__name__}: {exc}"}

    def _approval_status(self, limit: int = 12) -> dict[str, Any]:
        try:
            from secondbrain.native.approval import native_audit_status
            return native_audit_status(self.project_root, limit=limit)
        except Exception as exc:
            return {"ok": False, "status": "approval_unavailable", "error": f"{type(exc).__name__}: {exc}"}

    def _runtime_summary(self, model: dict[str, Any]) -> dict[str, Any]:
        bootstrap = model.get("bootstrap", {}) if isinstance(model, dict) else {}
        provider = model.get("provider", {}) if isinstance(model, dict) else {}
        rag = model.get("rag", {}) if isinstance(model, dict) else {}
        return {
            "ok": bool(model.get("ok", False)) if isinstance(model, dict) else False,
            "bootstrap_status": bootstrap.get("status", "unknown"),
            "rag_status": rag.get("status", "unknown"),
            "embedding_provider": provider.get("provider", "unknown"),
            "mode": model.get("mode", "native_workspace_primary") if isinstance(model, dict) else "native_workspace_primary",
        }

    def _documents_summary(self, model: dict[str, Any]) -> dict[str, Any]:
        rag = model.get("rag", {}) if isinstance(model, dict) else {}
        return {
            "ok": bool(rag.get("ok", False)),
            "status": rag.get("status", "unknown"),
            "source": "rag_status",
            "documents": rag.get("documents") or rag.get("document_count") or rag.get("total_documents") or 0,
            "chunks": rag.get("chunks") or rag.get("chunk_count") or rag.get("total_chunks") or 0,
            "vectors": rag.get("vectors") or rag.get("vector_count") or rag.get("total_vectors") or 0,
            "blockers": rag.get("blockers", []),
        }

    def _search_summary(self, model: dict[str, Any]) -> dict[str, Any]:
        production = model.get("production", {}) if isinstance(model, dict) else {}
        provider = model.get("provider", {}) if isinstance(model, dict) else {}
        return {
            "ok": bool(production.get("ok", provider.get("ok", False))),
            "production_status": production.get("status", "unknown"),
            "provider": provider.get("provider", "unknown"),
            "quality_gate_visible": True,
            "golden_eval_visible": True,
            "vector_audit_visible": True,
        }

    def _memory_summary(self, model: dict[str, Any]) -> dict[str, Any]:
        memory = model.get("memory", {}) if isinstance(model, dict) else {}
        return {
            "ok": bool(memory.get("ok", False)),
            "status": memory.get("status", "unknown"),
            "privacy_mode_visible": True,
            "secret_encryption_visible": True,
            "lineage_visible": True,
            "blockers": memory.get("blockers", []),
        }

    def _agent_summary(self, model: dict[str, Any]) -> dict[str, Any]:
        actions = model.get("actions", {}) if isinstance(model, dict) else {}
        return {
            "ok": True,
            "status": "surface_ready_runtime_pending",
            "voice_action_dispatcher": bool(actions.get("mode")),
            "approval_required_for_writes": actions.get("confirmation_required_for", []),
            "known_gap": "full_agent_planner_not_yet_productive",
        }


def workspace_status(project_root: str | Path | None = None, limit: int = 12) -> dict[str, Any]:
    return NativeWorkspaceCenter(project_root).status(limit=limit)


def workspace_activity(project_root: str | Path | None = None, limit: int = 20) -> dict[str, Any]:
    return NativeWorkspaceCenter(project_root).activity.status(limit=limit)
