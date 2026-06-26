"""v30.24 Memory Center runtime truth service.

Read-only aggregation layer for GUI/HUD. It separates real memory sources from
legacy demo counters and exposes governance gaps explicitly: vault memories,
runtime SQLite memories, semantic/episodic in-process stores, privacy/security
configuration and source lineage completeness.
"""
from __future__ import annotations

import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "secondbrain.gui.memory_center.v1"
MEMORY_DIRS = ("22_Memory", "48_AgentMemory", "100_MemoryEngine")
RUNTIME_DB_CANDIDATES = (
    "runtime/secondbrain.sqlite3",
    "runtime/secondbrain.db",
    "data/secondbrain.sqlite3",
    "data/runtime.sqlite3",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except Exception:
        return default


def _safe_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists() and path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}
    return {}


def _read_env(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        for raw in (root / ".env").read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return values


def _read_config(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        return _safe_json(path)
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    # minimal yaml-like reader for top-level booleans/strings used by existing config files
    result: dict[str, Any] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"').strip("'")
        if value.lower() in {"true", "false"}:
            result[key.strip()] = value.lower() == "true"
        elif value:
            result[key.strip()] = value
    return result


@dataclass(frozen=True)
class MemoryCenterRuntime:
    project_root: str | Path
    profile: str | None = None

    @property
    def root(self) -> Path:
        return Path(self.project_root).resolve()

    @property
    def vault(self) -> Path:
        # Compatible with the current HUD server convention.
        candidates = [self.root / "SecondBrain", self.root / "vault", self.root]
        for candidate in candidates:
            if any((candidate / d).exists() for d in MEMORY_DIRS):
                return candidate
        return self.root / "SecondBrain"

    @property
    def reports_dir(self) -> Path:
        return self.root / "runtime" / "reports"

    def _vault_memories(self) -> dict[str, Any]:
        groups: list[dict[str, Any]] = []
        total = 0
        bytes_total = 0
        recent: list[dict[str, Any]] = []
        by_dir: Counter[str] = Counter()
        for dirname in MEMORY_DIRS:
            folder = self.vault / dirname
            entries: list[dict[str, Any]] = []
            if not folder.exists() or not folder.is_dir():
                groups.append({"category": dirname, "exists": False, "count": 0, "entries": []})
                continue
            for path in folder.rglob("*.md"):
                rel_parts = path.relative_to(folder).parts
                if any(part.startswith(".") for part in rel_parts):
                    continue
                try:
                    st = path.stat()
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                item = {
                    "name": path.stem,
                    "file": path.name,
                    "path": str(path.relative_to(self.vault)).replace("\\", "/"),
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                    "preview": " ".join(text.strip().split())[:240],
                    "has_source": any(marker in text.lower() for marker in ("source:", "quelle:", "evidence:", "[[", "http")),
                    "has_tags": ("tags:" in text.lower()) or ("#" in text),
                }
                by_dir[dirname] += 1
                bytes_total += st.st_size
                entries.append(item)
                recent.append(item)
            entries.sort(key=lambda item: item["mtime"], reverse=True)
            total += len(entries)
            groups.append({"category": dirname, "exists": True, "count": len(entries), "entries": entries[:100]})
        recent.sort(key=lambda item: item["mtime"], reverse=True)
        no_source = sum(1 for item in recent if not item.get("has_source"))
        no_tags = sum(1 for item in recent if not item.get("has_tags"))
        return {
            "total": total,
            "bytes": bytes_total,
            "groups": groups,
            "by_directory": dict(by_dir),
            "recent": recent[:50],
            "lineage_gaps": no_source,
            "tag_gaps": no_tags,
        }

    def _runtime_sqlite_memories(self) -> dict[str, Any]:
        for rel in RUNTIME_DB_CANDIDATES:
            path = self.root / rel
            if not path.exists() or not path.is_file():
                continue
            try:
                con = sqlite3.connect(str(path))
                con.row_factory = sqlite3.Row
                tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'").fetchall()]
                if "memories" not in tables:
                    con.close()
                    continue
                rows = con.execute("select * from memories limit 200").fetchall()
                count = con.execute("select count(*) from memories").fetchone()[0]
                by_kind: Counter[str] = Counter()
                recent = []
                for row in rows:
                    d = dict(row)
                    by_kind[str(d.get("kind") or d.get("type") or "unknown")] += 1
                    recent.append({
                        "id": d.get("id") or d.get("memory_id"),
                        "kind": d.get("kind") or d.get("type") or "unknown",
                        "source": d.get("source") or "unknown",
                        "importance": d.get("importance"),
                        "preview": str(d.get("content") or d.get("text") or d.get("summary") or "")[:240],
                    })
                con.close()
                return {"exists": True, "path": str(path), "count": _safe_int(count), "by_kind": dict(by_kind), "recent": recent[:50]}
            except Exception as exc:  # noqa: BLE001
                return {"exists": True, "path": str(path), "count": 0, "error": str(exc), "by_kind": {}, "recent": []}
        return {"exists": False, "path": None, "count": 0, "by_kind": {}, "recent": []}

    def _agent_registry_status(self) -> dict[str, Any]:
        try:
            from secondbrain.memory.memory_registry import MemoryRegistry

            registry = MemoryRegistry()
            semantic = registry.semantic.list()
            episodic = registry.episodic.list()
            return {
                "ok": True,
                "semantic_items": len(semantic),
                "episodic_items": len(episodic),
                "persistence": "in_memory",
                "warning": "not_persistent" if not semantic and not episodic else "in_process_only",
            }
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "semantic_items": 0, "episodic_items": 0, "persistence": "unknown", "error": str(exc)}

    def _governance(self, vault: dict[str, Any], sqlite_mem: dict[str, Any]) -> dict[str, Any]:
        env = _read_env(self.root)
        security = _read_config(self.root / "config" / "security.yaml")
        privacy_mode = str(env.get("SECONDBRAIN_PRIVACY_MODE", security.get("privacy_mode", "false"))).lower() in {"1", "true", "yes", "on"}
        encryption = str(env.get("SECONDBRAIN_SECRET_ENCRYPTION", security.get("secret_encryption", "false"))).lower() in {"1", "true", "yes", "on"}
        classification = str(env.get("SECONDBRAIN_DATA_CLASSIFICATION", security.get("data_classification", "false"))).lower() in {"1", "true", "yes", "on"}
        blockers: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        if not encryption:
            blockers.append({"code": "secret_encryption_missing", "detail": "Secrets/OAuth tokens are not protected by a confirmed vault."})
        if not classification:
            warnings.append({"code": "data_classification_not_confirmed", "detail": "Memory writes may lack classification metadata."})
        if vault.get("lineage_gaps", 0) > 0:
            warnings.append({"code": "memory_lineage_gaps", "count": vault.get("lineage_gaps", 0)})
        if sqlite_mem.get("count", 0) and not encryption:
            blockers.append({"code": "sqlite_memory_without_encryption", "count": sqlite_mem.get("count", 0)})
        status = "blocked" if blockers else ("warning" if warnings else "pass")
        return {
            "status": status,
            "privacy_mode": privacy_mode,
            "secret_encryption": encryption,
            "data_classification": classification,
            "blockers": blockers,
            "warnings": warnings,
        }

    def _last_reports(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, pattern in {
            "last_memory": "*memory*.json",
            "last_privacy": "*privacy*.json",
            "last_backup": "*backup*.json",
        }.items():
            try:
                matches = sorted(self.reports_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
            except Exception:
                matches = []
            if matches:
                p = matches[0]
                out[key] = {"exists": True, "name": p.name, "path": str(p), "mtime": int(p.stat().st_mtime), "data": _safe_json(p)}
            else:
                out[key] = {"exists": False}
        return out

    def status(self) -> dict[str, Any]:
        vault = self._vault_memories()
        sqlite_mem = self._runtime_sqlite_memories()
        registry = self._agent_registry_status()
        governance = self._governance(vault, sqlite_mem)
        total = vault.get("total", 0) + sqlite_mem.get("count", 0) + registry.get("semantic_items", 0) + registry.get("episodic_items", 0)
        status = governance["status"]
        return {
            "schema": SCHEMA,
            "ok": status != "blocked",
            "status": status,
            "generated_at": _utc_now(),
            "summary": {
                "total_memories": total,
                "vault_memories": vault.get("total", 0),
                "sqlite_memories": sqlite_mem.get("count", 0),
                "semantic_items": registry.get("semantic_items", 0),
                "episodic_items": registry.get("episodic_items", 0),
                "lineage_gaps": vault.get("lineage_gaps", 0),
                "tag_gaps": vault.get("tag_gaps", 0),
                "governance_blockers": len(governance.get("blockers", [])),
                "governance_warnings": len(governance.get("warnings", [])),
            },
            "sources": {"vault": vault, "sqlite": sqlite_mem, "agent_registry": registry},
            "governance": governance,
            "reports": self._last_reports(),
        }


def memory_center_status(project_root: str | Path, profile: str | None = None) -> dict[str, Any]:
    return MemoryCenterRuntime(project_root, profile).status()
