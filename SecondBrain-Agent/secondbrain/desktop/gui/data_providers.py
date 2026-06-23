"""Live-Datenprovider fuer die Desktop-GUI.

Bindet die GUI-Shell an reale Daten aus Vault, Inbox, Config und Runtime.
Jede Methode ist gekapselt und wirft nie -- fehlende Quellen ergeben ein
leeres, aber valides View-Model. Keine Loeschungen, nur Lesezugriffe.

Root-Aufloesung funktioniert ohne harte Pfade: aus der Paketstruktur
abgeleitet (SecondBrain-Agent), Vault/Inbox als Geschwisterordner. Dadurch
laeuft der Provider auf der Zielmaschine und in Tests gleichermassen.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

# secondbrain/desktop/gui/data_providers.py -> parents[3] == SecondBrain-Agent
_DEFAULT_ROOT = Path(__file__).resolve().parents[3]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _load_simple_yaml(path: Path) -> dict:
    """Minimaler YAML-Leser fuer flache 'name:'/'  enabled: true' Strukturen."""
    data: dict[str, dict] = {}
    text = _read_text(path)
    if not text:
        return data
    current: str | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if indent == 0 and line.endswith(":"):
            current = line[:-1]
            data[current] = {}
        elif indent >= 2 and current and ":" in line:
            key, _, val = line.partition(":")
            v = val.strip()
            if v.lower() in ("true", "false"):
                data[current][key.strip()] = (v.lower() == "true")
            else:
                data[current][key.strip()] = v.strip('"')
    return data


def _tokenize(text: str) -> list[str]:
    out, word = [], []
    for ch in text.lower():
        if ch.isalnum() or ch in "äöüß":
            word.append(ch)
        elif word:
            out.append("".join(word))
            word = []
    if word:
        out.append("".join(word))
    return out


@dataclass
class LiveDataService:
    """Liest reale SecondBrain-Daten und liefert View-Models pro GUI-Modul."""

    root: Path = _DEFAULT_ROOT

    # --- Pfade -------------------------------------------------------------
    @property
    def vault(self) -> Path:
        return self.root.parent / "SecondBrain"

    @property
    def inbox(self) -> Path:
        return self.root.parent / "SecondBrain-Inbox"

    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def runtime_dir(self) -> Path:
        return self.root / "runtime"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    # --- Bausteine ---------------------------------------------------------
    def _vault_markdown(self) -> list[Path]:
        if not self.vault.exists():
            return []
        return [p for p in self.vault.rglob("*.md") if "99_System" not in p.parts]

    def _connector_list(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        yaml_cfg = _load_simple_yaml(self.config_dir / "connectors.yaml")
        for name, cfg in yaml_cfg.items():
            items.append({
                "name": name,
                "source": "connectors.yaml",
                "enabled": bool(cfg.get("enabled", False)),
            })
        v104 = _read_json(self.config_dir / "connectors_v104.json", {})
        for c in v104.get("connectors", []) if isinstance(v104, dict) else []:
            items.append({
                "name": c.get("name", "?"),
                "source": "connectors_v104.json",
                "kind": c.get("kind", ""),
                "enabled": bool(c.get("enabled", False)),
            })
        return items

    def _recent_jobs(self) -> list[dict[str, Any]]:
        jobs: list[dict[str, Any]] = []
        jsonl = self.runtime_dir / "jobs.jsonl"
        if jsonl.exists():
            for line in _read_text(jsonl).splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    jobs.append(json.loads(line))
                except Exception:
                    continue
        for fname in ("agent_runs_v110.json", "workflow_runs_v112.json"):
            blob = _read_json(self.runtime_dir / fname, {})
            if isinstance(blob, dict):
                for key, val in blob.items():
                    jobs.append({"id": key, "source": fname, "detail": val})
            elif isinstance(blob, list):
                for val in blob:
                    jobs.append({"source": fname, "detail": val})
        return jobs

    # --- View-Models pro Modul --------------------------------------------
    def dashboard(self) -> dict[str, Any]:
        md = self._vault_markdown()
        connectors = self._connector_list()
        inbox_files = list(self.inbox.rglob("*")) if self.inbox.exists() else []
        inbox_count = sum(1 for p in inbox_files if p.is_file())
        return {
            "module": "dashboard",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "vault_exists": self.vault.exists(),
            "markdown_files": len(md),
            "inbox_files": inbox_count,
            "connectors_total": len(connectors),
            "connectors_enabled": sum(1 for c in connectors if c["enabled"]),
            "jobs_recent": len(self._recent_jobs()),
            "status": "ready" if self.vault.exists() else "degraded",
        }

    def documents(self, limit: int = 25) -> dict[str, Any]:
        md = self._vault_markdown()
        md.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        items = []
        for p in md[:limit]:
            try:
                st = p.stat()
                rel = p.relative_to(self.vault)
                items.append({
                    "name": p.name,
                    "folder": rel.parts[0] if len(rel.parts) > 1 else ".",
                    "size": st.st_size,
                    "modified": datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds"),
                })
            except Exception:
                continue
        folders = sorted({p.relative_to(self.vault).parts[0]
                          for p in md if len(p.relative_to(self.vault).parts) > 1})
        return {
            "module": "documents",
            "total": len(md),
            "folders": len(folders),
            "items": items,
        }

    def search(self, query: str = "", limit: int = 10) -> dict[str, Any]:
        query = (query or "").strip()
        terms = set(t for t in _tokenize(query) if len(t) > 1)
        hits: list[dict[str, Any]] = []
        if terms and self.vault.exists():
            scored: list[tuple[int, Path, str]] = []
            for note in self._vault_markdown():
                text = _read_text(note)
                low = text.lower()
                score = sum(low.count(t) for t in terms)
                score += sum(3 for t in terms if t in note.stem.lower())
                if score > 0:
                    idx = min((low.find(t) for t in terms if t in low), default=0)
                    start = max(0, idx - 80)
                    preview = text[start:start + 240].replace("\n", " ").strip()
                    scored.append((score, note, preview))
            scored.sort(key=lambda x: x[0], reverse=True)
            for score, note, preview in scored[:limit]:
                hits.append({
                    "note": str(note.relative_to(self.vault)),
                    "score": score,
                    "preview": preview,
                })
        return {"module": "search", "query": query, "result_count": len(hits), "hits": hits}

    def connectors(self) -> dict[str, Any]:
        items = self._connector_list()
        return {
            "module": "connectors",
            "total": len(items),
            "enabled": sum(1 for c in items if c["enabled"]),
            "items": items,
        }

    def settings(self) -> dict[str, Any]:
        desktop = _read_json(self.data_dir / "desktop_app" / "settings.json", {})
        return {
            "module": "settings",
            "desktop": desktop if isinstance(desktop, dict) else {},
            "config_files": sorted(p.name for p in self.config_dir.glob("*.y*ml")) if self.config_dir.exists() else [],
            "vault_path": str(self.vault),
        }

    def jobs(self, limit: int = 25) -> dict[str, Any]:
        jobs = self._recent_jobs()
        return {
            "module": "jobs",
            "total": len(jobs),
            "items": jobs[:limit],
        }

    def status(self) -> dict[str, Any]:
        checks = {
            "vault": self.vault.exists(),
            "inbox": self.inbox.exists(),
            "config": self.config_dir.exists(),
            "runtime": self.runtime_dir.exists(),
        }
        connectors = self._connector_list()
        color = "GREEN"
        if not checks["vault"] or not checks["config"]:
            color = "RED"
        elif not any(c["enabled"] for c in connectors):
            color = "YELLOW"
        return {
            "module": "status",
            "checks": checks,
            "connectors_enabled": sum(1 for c in connectors if c["enabled"]),
            "overall": color,
        }

    def notifications(self) -> dict[str, Any]:
        notes: list[dict[str, str]] = []
        if not self.vault.exists():
            notes.append({"level": "error", "message": f"Vault fehlt: {self.vault}"})
        if not any(c["enabled"] for c in self._connector_list()):
            notes.append({"level": "warning", "message": "Kein Connector aktiviert."})
        inbox_files = [p for p in self.inbox.rglob("*") if p.is_file()] if self.inbox.exists() else []
        if inbox_files:
            notes.append({"level": "info", "message": f"{len(inbox_files)} Datei(en) in der Inbox."})
        return {"module": "notifications", "count": len(notes), "items": notes}

    def desktop_foundation(self) -> dict[str, Any]:
        return {
            "module": "desktop_foundation",
            "root": str(self.root),
            "root_exists": self.root.exists(),
            "vault_exists": self.vault.exists(),
            "ready": self.root.exists(),
        }

    # --- Mapping module_id -> Provider ------------------------------------
    def provider_for(self, module_id: str) -> Callable[[], dict[str, Any]]:
        mapping: dict[str, Callable[[], dict[str, Any]]] = {
            "desktop_foundation": self.desktop_foundation,
            "dashboard": self.dashboard,
            "documents": self.documents,
            "search": lambda: self.search(""),
            "connectors": self.connectors,
            "settings": self.settings,
            "jobs": self.jobs,
            "status": self.status,
            "notifications": self.notifications,
        }
        return mapping.get(module_id, lambda: {"module": module_id, "live": False})
