from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class MemoryEntry:
    memory_id: str
    kind: str
    content: str
    source: str
    created_at: float
    tags: tuple[str, ...] = ()
    importance: float = 0.5
    confidence: float = 0.5
    archived: bool = False
    favorite: bool = False
    lineage: str = "runtime"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tags"] = list(self.tags)
        return payload


class MemoryExplorer:
    """File-backed native memory explorer.

    This module deliberately works without a database. It aggregates runtime
    memories, chat questions, voice notes and imported JSONL memory files into a
    stable desktop-readable view. Write actions are limited to local metadata so
    the explorer can be enabled before the productive memory backend is final.
    """

    def __init__(self, project_root: str | Path = ".") -> None:
        self.project_root = Path(project_root).resolve()
        self.runtime_dir = self.project_root / "runtime" / "native"
        self.memory_dir = self.project_root / "runtime" / "memory"
        self.export_dir = self.project_root / "exports" / "memory"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.meta_path = self.runtime_dir / "memory_meta.json"
        self.memory_path = self.runtime_dir / "memory_entries.jsonl"
        self.voice_notes_path = self.runtime_dir / "voice_notes.jsonl"
        self.chat_history_path = self.runtime_dir / "chat_history.jsonl"

    def status(self) -> dict[str, Any]:
        entries = self.entries(limit=100000)["memories"]
        by_kind: dict[str, int] = {}
        archived = 0
        favorites = 0
        tag_gaps = 0
        lineage_gaps = 0
        for row in entries:
            by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1
            archived += 1 if row.get("archived") else 0
            favorites += 1 if row.get("favorite") else 0
            tag_gaps += 1 if not row.get("tags") else 0
            lineage_gaps += 1 if not row.get("lineage") else 0
        return {
            "ok": True,
            "version": "30.33",
            "mode": "native_memory_explorer",
            "project_root": str(self.project_root),
            "total_memories": len(entries),
            "active_memories": len(entries) - archived,
            "archived_memories": archived,
            "favorites": favorites,
            "by_kind": by_kind,
            "tag_gaps": tag_gaps,
            "lineage_gaps": lineage_gaps,
            "sources": self.sources(),
        }

    def entries(self, *, query: str = "", kind: str = "", include_archived: bool = False, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        query_norm = query.strip().lower()
        kind_norm = kind.strip().lower()
        rows = [entry.to_dict() for entry in self._load_entries()]
        if not include_archived:
            rows = [row for row in rows if not row.get("archived")]
        if kind_norm:
            rows = [row for row in rows if row.get("kind", "").lower() == kind_norm]
        if query_norm:
            def matches(row: dict[str, Any]) -> bool:
                haystack = " ".join([
                    str(row.get("memory_id", "")),
                    str(row.get("kind", "")),
                    str(row.get("content", "")),
                    str(row.get("source", "")),
                    " ".join(row.get("tags") or []),
                ]).lower()
                return query_norm in haystack
            rows = [row for row in rows if matches(row)]
        rows.sort(key=lambda row: float(row.get("created_at") or 0), reverse=True)
        return {"ok": True, "count": len(rows), "limit": limit, "offset": offset, "memories": rows[offset: offset + limit]}

    def search(self, query: str, *, limit: int = 25) -> dict[str, Any]:
        return self.entries(query=query, limit=limit)

    def timeline(self, *, limit: int = 100) -> dict[str, Any]:
        rows = self.entries(include_archived=True, limit=limit)["memories"]
        buckets: dict[str, int] = {}
        for row in rows:
            day = time.strftime("%Y-%m-%d", time.localtime(float(row.get("created_at") or 0)))
            buckets[day] = buckets.get(day, 0) + 1
        return {"ok": True, "days": buckets, "memories": rows[:limit]}

    def add(self, content: str, *, kind: str = "working", source: str = "manual", tags: Iterable[str] = (), importance: float = 0.5) -> dict[str, Any]:
        content = content.strip()
        if not content:
            return {"ok": False, "status": "empty_content"}
        entry = MemoryEntry(
            memory_id=f"mem_{uuid.uuid4().hex[:12]}",
            kind=kind.strip() or "working",
            content=content,
            source=source.strip() or "manual",
            created_at=time.time(),
            tags=tuple(_normalize_tags(tags)),
            importance=float(importance),
            confidence=0.8,
            lineage="manual:native_memory_explorer",
        )
        _append_jsonl(self.memory_path, entry.to_dict())
        return {"ok": True, "status": "created", "memory": entry.to_dict()}

    def favorite(self, memory_ref: str, favorite: bool = True) -> dict[str, Any]:
        return self._set_meta_flag(memory_ref, "favorite", favorite)

    def archive(self, memory_ref: str) -> dict[str, Any]:
        return self._set_meta_flag(memory_ref, "archived", True)

    def restore(self, memory_ref: str) -> dict[str, Any]:
        return self._set_meta_flag(memory_ref, "archived", False)

    def export(self, fmt: str = "json", *, include_archived: bool = True) -> dict[str, Any]:
        fmt = fmt.lower().strip() or "json"
        rows = self.entries(include_archived=include_archived, limit=100000)["memories"]
        stamp = time.strftime("%Y%m%d_%H%M%S")
        if fmt == "md":
            path = self.export_dir / f"memory_export_{stamp}.md"
            lines = ["# Jarvis Memory Export", ""]
            for row in rows:
                lines.append(f"## {row['memory_id']} · {row['kind']}")
                lines.append(f"- Quelle: {row.get('source','')}")
                lines.append(f"- Tags: {', '.join(row.get('tags') or [])}")
                lines.append("")
                lines.append(str(row.get("content") or ""))
                lines.append("")
            path.write_text("\n".join(lines), encoding="utf-8")
        else:
            path = self.export_dir / f"memory_export_{stamp}.json"
            path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"ok": True, "format": fmt, "count": len(rows), "path": str(path)}

    def sources(self) -> list[dict[str, Any]]:
        candidates = [self.memory_path, self.voice_notes_path, self.chat_history_path, *sorted(self.memory_dir.glob("*.jsonl"))]
        rows = []
        for path in candidates:
            rows.append({"path": str(path), "exists": path.exists(), "entries": sum(1 for _ in _read_jsonl(path)) if path.exists() else 0})
        return rows

    def _load_entries(self) -> list[MemoryEntry]:
        meta = self._load_meta()
        rows: list[MemoryEntry] = []
        for raw in _read_jsonl(self.memory_path):
            rows.append(self._from_raw(raw, default_kind="working", default_source="memory_entries"))
        for raw in _read_jsonl(self.voice_notes_path):
            content = str(raw.get("text") or raw.get("content") or raw.get("note") or "").strip()
            if content:
                rows.append(self._from_raw({**raw, "content": content}, default_kind="episodic", default_source="voice"))
        for raw in _read_jsonl(self.chat_history_path):
            content = str(raw.get("question") or raw.get("prompt") or raw.get("content") or "").strip()
            if content:
                rows.append(self._from_raw({**raw, "content": content}, default_kind="conversation", default_source="chat"))
        for path in sorted(self.memory_dir.glob("*.jsonl")):
            for raw in _read_jsonl(path):
                rows.append(self._from_raw(raw, default_kind=str(raw.get("kind") or "imported"), default_source=path.name))
        merged: dict[str, MemoryEntry] = {}
        for entry in rows:
            flags = meta.get(entry.memory_id, {}) if isinstance(meta.get(entry.memory_id), dict) else {}
            merged[entry.memory_id] = MemoryEntry(
                **{**entry.to_dict(), "tags": tuple(entry.tags), "archived": bool(flags.get("archived", entry.archived)), "favorite": bool(flags.get("favorite", entry.favorite))}
            )
        return list(merged.values())

    def _from_raw(self, raw: dict[str, Any], *, default_kind: str, default_source: str) -> MemoryEntry:
        content = str(raw.get("content") or raw.get("text") or raw.get("body") or "").strip()
        created = raw.get("created_at") or raw.get("timestamp") or raw.get("ts") or time.time()
        try:
            created_at = float(created)
        except Exception:
            created_at = time.time()
        memory_id = str(raw.get("memory_id") or raw.get("id") or _stable_memory_id(default_kind, default_source, content, created_at))
        return MemoryEntry(
            memory_id=memory_id,
            kind=str(raw.get("kind") or default_kind),
            content=content,
            source=str(raw.get("source") or default_source),
            created_at=created_at,
            tags=tuple(_normalize_tags(raw.get("tags") or [])),
            importance=float(raw.get("importance") or 0.5),
            confidence=float(raw.get("confidence") or 0.5),
            archived=bool(raw.get("archived") or False),
            favorite=bool(raw.get("favorite") or False),
            lineage=str(raw.get("lineage") or default_source),
        )

    def _set_meta_flag(self, memory_ref: str, key: str, value: bool) -> dict[str, Any]:
        match = self._resolve(memory_ref)
        if match is None:
            return {"ok": False, "status": "not_found", "memory_ref": memory_ref}
        meta = self._load_meta()
        row = meta.get(match.memory_id, {}) if isinstance(meta.get(match.memory_id), dict) else {}
        row[key] = bool(value)
        meta[match.memory_id] = row
        self._save_meta(meta)
        return {"ok": True, "status": "updated", "memory_id": match.memory_id, key: bool(value)}

    def _resolve(self, memory_ref: str) -> MemoryEntry | None:
        ref = memory_ref.strip().lower()
        if not ref:
            return None
        for entry in self._load_entries():
            if ref in {entry.memory_id.lower(), entry.content.lower()} or ref in entry.content.lower():
                return entry
        return None

    def _load_meta(self) -> dict[str, Any]:
        if not self.meta_path.exists():
            return {}
        try:
            data = json.loads(self.meta_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return data if isinstance(data, dict) else {}

    def _save_meta(self, data: dict[str, Any]) -> None:
        self.meta_path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def _normalize_tags(tags: Iterable[Any]) -> list[str]:
    if isinstance(tags, str):
        raw = tags.replace(";", ",").split(",")
    else:
        raw = list(tags)
    return sorted({str(item).strip().lower() for item in raw if str(item).strip()})


def _stable_memory_id(kind: str, source: str, content: str, created_at: float) -> str:
    seed = f"{kind}|{source}|{content}|{int(created_at)}"
    return "mem_" + uuid.uuid5(uuid.NAMESPACE_URL, seed).hex[:12]


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except Exception:
            continue
        if isinstance(data, dict):
            rows.append(data)
    return rows


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
