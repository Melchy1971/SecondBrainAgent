from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .models import NativeTheme, ThemeSnapshot, normalize_project_root


class ThemeCenterService:
    """Native theme engine for the desktop surface.

    Scope v30.42:
    - deterministic built-in theme catalog
    - persisted active theme
    - import/export of JSON theme definitions
    - audit history for theme changes
    - offline-safe status for AI Workspace integration
    """

    VERSION = "v30.42"

    BUILTIN_THEMES: tuple[NativeTheme, ...] = (
        NativeTheme(
            id="jarvis_dark",
            name="Jarvis Dark",
            mode="dark",
            description="Dunkles Standardtheme für die native Jarvis-Oberfläche.",
            tokens={
                "background": "#0b1220",
                "surface": "#111827",
                "surface_raised": "#172033",
                "text": "#e5e7eb",
                "text_muted": "#9ca3af",
                "accent": "#38bdf8",
                "accent_2": "#22c55e",
                "warning": "#f59e0b",
                "danger": "#ef4444",
                "border": "#263244",
            },
            typography={"font_family": "Segoe UI", "font_size": "10", "title_size": "16"},
        ),
        NativeTheme(
            id="cyber_blue",
            name="Cyber Blue",
            mode="dark",
            description="Kontrastreiches Tech-Theme mit blauen Akzenten.",
            tokens={
                "background": "#050816",
                "surface": "#0f172a",
                "surface_raised": "#172554",
                "text": "#dbeafe",
                "text_muted": "#93c5fd",
                "accent": "#06b6d4",
                "accent_2": "#8b5cf6",
                "warning": "#facc15",
                "danger": "#fb7185",
                "border": "#1e40af",
            },
            typography={"font_family": "Segoe UI", "font_size": "10", "title_size": "16"},
        ),
        NativeTheme(
            id="minimal_light",
            name="Minimal Light",
            mode="light",
            description="Helles reduziertes Theme für längere Arbeitsphasen.",
            tokens={
                "background": "#f8fafc",
                "surface": "#ffffff",
                "surface_raised": "#f1f5f9",
                "text": "#0f172a",
                "text_muted": "#475569",
                "accent": "#2563eb",
                "accent_2": "#16a34a",
                "warning": "#d97706",
                "danger": "#dc2626",
                "border": "#cbd5e1",
            },
            typography={"font_family": "Segoe UI", "font_size": "10", "title_size": "16"},
        ),
        NativeTheme(
            id="operator_gray",
            name="Operator Gray",
            mode="dark",
            description="Ruhiges dunkles Theme für Monitoring und Analyse.",
            tokens={
                "background": "#111111",
                "surface": "#1f1f1f",
                "surface_raised": "#2a2a2a",
                "text": "#f3f4f6",
                "text_muted": "#a3a3a3",
                "accent": "#a78bfa",
                "accent_2": "#34d399",
                "warning": "#fbbf24",
                "danger": "#f87171",
                "border": "#3f3f46",
            },
            typography={"font_family": "Segoe UI", "font_size": "10", "title_size": "16"},
            density="compact",
        ),
    )

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = normalize_project_root(project_root)
        self.runtime_dir = self.project_root / "runtime" / "native" / "theme_center"
        self.active_path = self.runtime_dir / "active_theme.json"
        self.history_path = self.runtime_dir / "theme_history.jsonl"
        self.custom_dir = self.runtime_dir / "custom_themes"

    def ensure_dirs(self) -> None:
        self.custom_dir.mkdir(parents=True, exist_ok=True)

    def _builtin_map(self) -> dict[str, NativeTheme]:
        return {theme.id: theme for theme in self.BUILTIN_THEMES}

    def _theme_from_dict(self, data: dict[str, Any]) -> NativeTheme:
        required = {"id", "name", "mode", "description", "tokens"}
        missing = sorted(required - set(data))
        if missing:
            raise ValueError(f"missing theme fields: {', '.join(missing)}")
        tokens = data.get("tokens")
        if not isinstance(tokens, dict) or not tokens:
            raise ValueError("theme tokens must be a non-empty object")
        return NativeTheme(
            id=str(data["id"]),
            name=str(data["name"]),
            mode=str(data["mode"]),
            description=str(data["description"]),
            tokens={str(k): str(v) for k, v in tokens.items()},
            typography={str(k): str(v) for k, v in dict(data.get("typography") or {}).items()},
            density=str(data.get("density") or "comfortable"),
        )

    def custom_themes(self) -> list[NativeTheme]:
        self.ensure_dirs()
        themes: list[NativeTheme] = []
        for path in sorted(self.custom_dir.glob("*.json")):
            try:
                themes.append(self._theme_from_dict(json.loads(path.read_text(encoding="utf-8"))))
            except Exception:
                continue
        return themes

    def themes(self) -> list[NativeTheme]:
        custom_ids = {theme.id for theme in self.custom_themes()}
        builtins = [theme for theme in self.BUILTIN_THEMES if theme.id not in custom_ids]
        return [*builtins, *self.custom_themes()]

    def theme_map(self) -> dict[str, NativeTheme]:
        return {theme.id: theme for theme in self.themes()}

    def current_theme_id(self) -> str:
        self.ensure_dirs()
        if self.active_path.exists():
            try:
                data = json.loads(self.active_path.read_text(encoding="utf-8"))
                theme_id = str(data.get("active_theme") or "")
                if theme_id in self.theme_map():
                    return theme_id
            except Exception:
                pass
        return "jarvis_dark"

    def current_theme(self) -> NativeTheme:
        return self.theme_map().get(self.current_theme_id()) or self._builtin_map()["jarvis_dark"]

    def record(self, event: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_dirs()
        row = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event,
            "payload": payload or {},
        }
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def activate(self, theme_id: str) -> dict[str, Any]:
        self.ensure_dirs()
        themes = self.theme_map()
        if theme_id not in themes:
            return {"ok": False, "error": "unknown_theme", "theme_id": theme_id, "available": sorted(themes)}
        payload = {"active_theme": theme_id, "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        self.active_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.record("theme_activated", {"theme_id": theme_id})
        return {"ok": True, "active_theme": theme_id, "theme": themes[theme_id].to_dict()}

    def reset(self) -> dict[str, Any]:
        self.ensure_dirs()
        if self.active_path.exists():
            self.active_path.unlink()
        self.record("theme_reset", {"active_theme": "jarvis_dark"})
        return {"ok": True, "active_theme": "jarvis_dark", "theme": self.current_theme().to_dict()}

    def snapshot(self) -> ThemeSnapshot:
        blockers: list[str] = []
        active = self.current_theme_id()
        if active not in self.theme_map():
            blockers.append("active_theme_missing")
        return ThemeSnapshot(
            ok=not blockers,
            version=self.VERSION,
            active_theme=active,
            available_themes=self.themes(),
            project_root=str(self.project_root),
            blockers=blockers,
        )

    def status(self) -> dict[str, Any]:
        data = self.snapshot().to_dict()
        data["current"] = self.current_theme().to_dict()
        data["runtime_dir"] = str(self.runtime_dir)
        return data

    def list_themes(self) -> dict[str, Any]:
        return {"ok": True, "active_theme": self.current_theme_id(), "themes": [theme.to_dict() for theme in self.themes()]}

    def preview(self, theme_id: str) -> dict[str, Any]:
        theme = self.theme_map().get(theme_id)
        if not theme:
            return {"ok": False, "error": "unknown_theme", "theme_id": theme_id}
        tokens = theme.tokens
        return {
            "ok": True,
            "theme": theme.to_dict(),
            "sample": {
                "window": tokens.get("background"),
                "panel": tokens.get("surface"),
                "button": tokens.get("accent"),
                "text": tokens.get("text"),
                "muted": tokens.get("text_muted"),
            },
        }

    def export_theme(self, theme_id: str, output_path: str | Path | None = None) -> dict[str, Any]:
        self.ensure_dirs()
        theme = self.theme_map().get(theme_id)
        if not theme:
            return {"ok": False, "error": "unknown_theme", "theme_id": theme_id}
        out_path = Path(output_path) if output_path else self.runtime_dir / f"{theme_id}.theme.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(theme.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        self.record("theme_exported", {"theme_id": theme_id, "path": str(out_path)})
        return {"ok": True, "path": str(out_path), "theme_id": theme_id}

    def import_theme(self, input_path: str | Path) -> dict[str, Any]:
        self.ensure_dirs()
        path = Path(input_path)
        if not path.exists():
            return {"ok": False, "error": "file_not_found", "path": str(path)}
        try:
            theme = self._theme_from_dict(json.loads(path.read_text(encoding="utf-8")))
        except Exception as exc:
            return {"ok": False, "error": "invalid_theme", "detail": str(exc), "path": str(path)}
        target = self.custom_dir / f"{theme.id}.json"
        target.write_text(json.dumps(theme.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        self.record("theme_imported", {"theme_id": theme.id, "path": str(path)})
        return {"ok": True, "theme": theme.to_dict(), "stored_at": str(target)}

    def history(self, limit: int = 30) -> dict[str, Any]:
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
