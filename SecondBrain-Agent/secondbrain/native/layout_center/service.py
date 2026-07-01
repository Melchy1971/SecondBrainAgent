from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

from .models import LayoutSpec, PanelSpec, normalize_project_root


class NativeLayoutService:
    """Persisted native docking layout service.

    The service keeps layout state in runtime/native/layouts and only writes files
    when explicitly asked. It is intentionally toolkit-neutral so the same layout
    contract can be used by Tkinter now and by a richer desktop shell later.
    """

    VERSION = "v30.41"
    DEFAULT_LAYOUT = "default"

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = normalize_project_root(project_root)
        self.runtime_dir = self.project_root / "runtime" / "native" / "layouts"
        self.history_path = self.runtime_dir / "layout_history.jsonl"
        self.active_path = self.runtime_dir / "active_layout.json"

    def ensure_dirs(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def templates(self) -> dict[str, LayoutSpec]:
        return {
            "default": LayoutSpec(
                name="default",
                title="Standard",
                description="Ausgewogenes Jarvis-Layout mit Navigation, Arbeitsbereich und Statusleiste.",
                panels=[
                    PanelSpec("navigation", "Navigation", "ai_workspace", "left", True, 1, "ai-workspace-navigation"),
                    PanelSpec("dashboard", "Dashboard", "dashboard_center", "center", True, 2, "dashboard-center-snapshot"),
                    PanelSpec("inspector", "Status / Inspector", "dashboard_center", "right", True, 1, "dashboard-center-status"),
                    PanelSpec("activity", "Aktivitäten", "ai_workspace", "bottom", True, 1, "ai-workspace-activity"),
                ],
            ),
            "developer": LayoutSpec(
                name="developer",
                title="Entwicklung",
                description="Layout für Diagnose, Logs, Kommandos und Systemzustand.",
                right_width=420,
                bottom_height=240,
                panels=[
                    PanelSpec("navigation", "Navigation", "ai_workspace", "left", True, 1, "ai-workspace-navigation"),
                    PanelSpec("commands", "Command Center", "command_center", "center", True, 2, "command-center-status"),
                    PanelSpec("settings", "Einstellungen", "settings_center", "right", True, 1, "settings-center-status"),
                    PanelSpec("logs", "Aktivitäten", "dashboard_center", "bottom", True, 1, "dashboard-center-activity"),
                ],
            ),
            "documents": LayoutSpec(
                name="documents",
                title="Dokumente",
                description="Layout für Import, Vorschau und Dokumentenstatus.",
                left_width=300,
                right_width=420,
                panels=[
                    PanelSpec("documents", "Dokumentenbaum", "document_explorer", "left", True, 2, "document-explorer-list"),
                    PanelSpec("preview", "Vorschau", "document_explorer", "center", True, 3, "document-explorer-preview"),
                    PanelSpec("metadata", "Metadaten / OCR", "document_explorer", "right", True, 1, "document-explorer-status"),
                    PanelSpec("search", "Suche", "document_explorer", "bottom", True, 1, "document-explorer-search"),
                ],
            ),
            "chat": LayoutSpec(
                name="chat",
                title="Chat",
                description="Layout für Dialog, Quellen und Sprachinteraktion.",
                right_width=360,
                panels=[
                    PanelSpec("navigation", "Navigation", "ai_workspace", "left", True, 1, "ai-workspace-navigation"),
                    PanelSpec("chat", "Chat", "chat_center", "center", True, 3, "native-chat-status"),
                    PanelSpec("voice", "Sprache", "voice_control_center", "right", True, 1, "voice-control-status"),
                    PanelSpec("activity", "Chat-Verlauf", "chat_center", "bottom", True, 1, "native-chat-search"),
                ],
            ),
            "analysis": LayoutSpec(
                name="analysis",
                title="Analyse",
                description="Layout für RAG, Memory, Agenten und Qualitätssignale.",
                right_width=420,
                panels=[
                    PanelSpec("memory", "Memory", "memory_explorer", "left", True, 1, "memory-explorer-status"),
                    PanelSpec("dashboard", "Qualität / Gates", "dashboard_center", "center", True, 2, "dashboard-center-snapshot"),
                    PanelSpec("agents", "Agenten", "agent_control_center", "right", True, 1, "agent-control-status"),
                    PanelSpec("activity", "Audit", "dashboard_center", "bottom", True, 1, "dashboard-center-activity"),
                ],
            ),
            "fullscreen": LayoutSpec(
                name="fullscreen",
                title="Vollbild",
                description="Maximaler Arbeitsbereich ohne Seitenleisten.",
                left_width=0,
                right_width=0,
                bottom_height=0,
                panels=[
                    PanelSpec("workspace", "Arbeitsbereich", "ai_workspace", "center", True, 1, "ai-workspace-snapshot"),
                ],
            ),
        }

    def _path_for(self, name: str) -> Path:
        safe = "".join(ch for ch in name.lower().strip() if ch.isalnum() or ch in {"-", "_"}) or self.DEFAULT_LAYOUT
        return self.runtime_dir / f"{safe}.json"

    def _record(self, event: str, payload: dict[str, Any] | None = None) -> None:
        self.ensure_dirs()
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "event": event, "payload": payload or {}}
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def ensure_defaults(self) -> dict[str, Any]:
        self.ensure_dirs()
        created: list[str] = []
        for name, spec in self.templates().items():
            path = self._path_for(name)
            if not path.exists():
                path.write_text(json.dumps(spec.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
                created.append(name)
        if not self.active_path.exists():
            self.active_path.write_text(json.dumps({"active": self.DEFAULT_LAYOUT}, indent=2), encoding="utf-8")
            created.append("active_layout")
        if created:
            self._record("layout_defaults_created", {"created": created})
        return {"ok": True, "created": created, "layout_dir": str(self.runtime_dir)}

    def list_layouts(self) -> dict[str, Any]:
        self.ensure_defaults()
        layouts: list[dict[str, Any]] = []
        for path in sorted(self.runtime_dir.glob("*.json")):
            if path.name == "active_layout.json":
                continue
            try:
                spec = LayoutSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))
                layouts.append(spec.to_dict())
            except Exception as exc:
                layouts.append({"name": path.stem, "title": path.stem, "ok": False, "error": str(exc)})
        return {"ok": True, "layouts": layouts, "count": len(layouts), "active": self.active_name()}

    def active_name(self) -> str:
        self.ensure_defaults()
        try:
            data = json.loads(self.active_path.read_text(encoding="utf-8"))
            return str(data.get("active") or self.DEFAULT_LAYOUT)
        except Exception:
            return self.DEFAULT_LAYOUT

    def load(self, name: str | None = None) -> dict[str, Any]:
        self.ensure_defaults()
        layout_name = name or self.active_name()
        path = self._path_for(layout_name)
        if not path.exists():
            return {"ok": False, "error": "layout_not_found", "name": layout_name}
        try:
            spec = LayoutSpec.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            return {"ok": False, "error": "layout_invalid", "name": layout_name, "detail": str(exc)}
        return {"ok": True, "layout": spec.to_dict(), "path": str(path), "active": self.active_name() == spec.name}

    def save(self, layout: LayoutSpec | dict[str, Any]) -> dict[str, Any]:
        self.ensure_dirs()
        spec = layout if isinstance(layout, LayoutSpec) else LayoutSpec.from_dict(layout)
        path = self._path_for(spec.name)
        path.write_text(json.dumps(spec.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        self._record("layout_saved", {"name": spec.name})
        return {"ok": True, "saved": spec.name, "path": str(path)}

    def activate(self, name: str) -> dict[str, Any]:
        loaded = self.load(name)
        if not loaded.get("ok"):
            return loaded
        self.active_path.write_text(json.dumps({"active": name}, indent=2, ensure_ascii=False), encoding="utf-8")
        self._record("layout_activated", {"name": name})
        return {"ok": True, "active": name, "layout": loaded["layout"]}

    def reset(self, name: str | None = None) -> dict[str, Any]:
        self.ensure_dirs()
        names = [name] if name else list(self.templates().keys())
        reset: list[str] = []
        templates = self.templates()
        for item in names:
            if item not in templates:
                continue
            self._path_for(item).write_text(json.dumps(templates[item].to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
            reset.append(item)
        if not name:
            self.active_path.write_text(json.dumps({"active": self.DEFAULT_LAYOUT}, indent=2), encoding="utf-8")
        self._record("layout_reset", {"layouts": reset})
        return {"ok": True, "reset": reset, "active": self.active_name()}

    def export(self, name: str, target: str | Path | None = None) -> dict[str, Any]:
        loaded = self.load(name)
        if not loaded.get("ok"):
            return loaded
        target_path = Path(target).resolve() if target else self.project_root / f"{name}_layout_export.json"
        target_path.write_text(json.dumps(loaded["layout"], indent=2, ensure_ascii=False), encoding="utf-8")
        self._record("layout_exported", {"name": name, "target": str(target_path)})
        return {"ok": True, "exported": name, "target": str(target_path)}

    def import_layout(self, source: str | Path, activate: bool = False) -> dict[str, Any]:
        self.ensure_dirs()
        source_path = Path(source).resolve()
        if not source_path.exists():
            return {"ok": False, "error": "source_not_found", "source": str(source_path)}
        try:
            spec = LayoutSpec.from_dict(json.loads(source_path.read_text(encoding="utf-8")))
        except Exception as exc:
            return {"ok": False, "error": "source_invalid", "source": str(source_path), "detail": str(exc)}
        saved = self.save(spec)
        if activate and saved.get("ok"):
            return self.activate(spec.name)
        self._record("layout_imported", {"name": spec.name, "source": str(source_path)})
        return {"ok": True, "imported": spec.name, "path": saved.get("path")}

    def history(self, limit: int = 50) -> dict[str, Any]:
        self.ensure_dirs()
        if not self.history_path.exists():
            return {"ok": True, "items": [], "count": 0}
        rows: list[dict[str, Any]] = []
        for line in self.history_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                rows.append({"event": "invalid_history_line", "raw": line[:200]})
        rows = rows[-limit:]
        rows.reverse()
        return {"ok": True, "items": rows, "count": len(rows)}

    def status(self) -> dict[str, Any]:
        listed = self.list_layouts()
        active = self.load(listed.get("active"))
        blockers: list[str] = []
        if not active.get("ok"):
            blockers.append("active_layout_invalid")
        return {
            "ok": not blockers,
            "version": self.VERSION,
            "layout_dir": str(self.runtime_dir),
            "active": listed.get("active"),
            "layout_count": listed.get("count", 0),
            "layouts": [{"name": row.get("name"), "title": row.get("title"), "panels": len(row.get("panels", []))} for row in listed.get("layouts", [])],
            "blockers": blockers,
        }
