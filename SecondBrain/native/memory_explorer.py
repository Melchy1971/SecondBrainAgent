from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

MEMORY_TYPES: tuple[str, ...] = ("episodic", "semantic", "preference", "project", "task")

SENSITIVE_BLOCK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"password\s*[:=]", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[:=]", re.IGNORECASE),
    re.compile(r"token\s*[:=]", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9]{10,}\b"),
)

SENSITIVE_REVIEW_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\biban\b", re.IGNORECASE),
    re.compile(r"\bssn\b", re.IGNORECASE),
    re.compile(r"\bprivate\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
)


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
    evidence: tuple[str, ...] = ()
    expires_at: float | None = None
    archived: bool = False
    favorite: bool = False
    lineage: str = "runtime"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["tags"] = list(self.tags)
        payload["evidence"] = list(self.evidence)
        return payload


@dataclass(frozen=True)
class MemoryReviewItem:
    review_id: str
    memory_id: str
    status: str
    reason: str
    content: str
    source: str
    kind: str
    confidence: float
    created_at: float
    pending_entry: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MemoryExplorerService:
    def __init__(self, project_root: Path | str = ".") -> None:
        self.project_root = Path(project_root).resolve()
        self.runtime_root = self.project_root / "runtime"
        self.runtime_dir = self.runtime_root / "native"
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.legacy_runtime_dir = self.runtime_root
        self.meta_path = self.runtime_dir / "memory_meta.json"
        self.memory_path = self.runtime_dir / "memory_entries.jsonl"
        self.review_path = self.runtime_dir / "memory_review_queue.jsonl"
        self.forget_audit_path = self.runtime_dir / "memory_forget_audit.jsonl"
        self.voice_notes_path = self.runtime_dir / "voice_notes.jsonl"
        self.chat_history_path = self.runtime_dir / "chat_history.jsonl"
        self.legacy_voice_notes_path = self.legacy_runtime_dir / "voice_notes.jsonl"
        self.legacy_chat_history_path = self.legacy_runtime_dir / "chat_history.jsonl"
        self.chat_root = self.project_root / "runtime" / "chat"

    def overview(self) -> dict[str, Any]:
        entries = self._load_entries()
        by_kind: dict[str, int] = {}
        archived = 0
        favorites = 0
        tag_gaps = 0
        lineage_gaps = 0
        for entry in entries:
            if entry.metadata.get("deleted", False):
                continue
            by_kind[entry.kind] = by_kind.get(entry.kind, 0) + 1
            if entry.archived:
                archived += 1
            if entry.favorite:
                favorites += 1
            if not entry.tags:
                tag_gaps += 1
            if not entry.lineage:
                lineage_gaps += 1
        return {
            "total_memories": len([entry for entry in entries if not entry.metadata.get("deleted", False)]),
            "active_memories": len([entry for entry in entries if not entry.archived and not entry.metadata.get("deleted", False)]),
            "archived_memories": archived,
            "favorites": favorites,
            "reviews_pending": len(self.list_reviews(status="pending")["items"]),
            "privacy_mode": self.privacy_mode_enabled(),
            "by_kind": by_kind,
            "tag_gaps": tag_gaps,
            "lineage_gaps": lineage_gaps,
            "sources": self.sources(),
        }

    def entries(
        self,
        *,
        query: str = "",
        kind: str = "",
        include_archived: bool = False,
        include_expired: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        query_norm = query.strip().lower()
        kind_norm = kind.strip().lower()
        rows = [entry.to_dict() for entry in self._load_entries()]
        now = time.time()
        rows = [row for row in rows if not bool((row.get("metadata") or {}).get("deleted", False))]
        if not include_archived:
            rows = [row for row in rows if not row.get("archived")]
        if not include_expired:
            rows = [row for row in rows if not row.get("expires_at") or float(row.get("expires_at") or 0) > now]
        if kind_norm:
            rows = [row for row in rows if row.get("kind", "").lower() == kind_norm]
        if query_norm:
            rows = [
                row
                for row in rows
                if query_norm in row.get("content", "").lower()
                or query_norm in row.get("source", "").lower()
                or any(query_norm in str(tag).lower() for tag in row.get("tags", []))
            ]
        rows.sort(key=lambda row: float(row.get("created_at", 0.0)), reverse=True)
        total = len(rows)
        page = rows[offset : offset + max(1, limit)]
        return {
            "ok": True,
            "total": total,
            "count": total,
            "offset": max(0, offset),
            "limit": max(1, limit),
            "items": page,
            "memories": page,
        }

    def search(self, query: str, *, limit: int = 25) -> dict[str, Any]:
        return self.entries(query=query, limit=limit)

    def add(
        self,
        content: str,
        *,
        kind: str = "semantic",
        source: str = "manual",
        tags: Iterable[str] = (),
        importance: float = 0.5,
        confidence: float = 0.8,
        evidence: Iterable[str] = (),
        expires_in_seconds: int | None = None,
        privacy_mode: bool | None = None,
    ) -> dict[str, Any]:
        content = content.strip()
        if not content:
            return {"ok": False, "status": "empty_content"}

        if privacy_mode is None:
            privacy_mode = self.privacy_mode_enabled()
        if privacy_mode:
            return {"ok": False, "status": "privacy_mode_blocks_writes"}

        normalized_kind = self._normalize_kind(kind, allow_legacy=False)
        normalized_source = source.strip() or "manual"
        normalized_evidence = tuple(_normalize_strings(evidence))

        duplicate = self._find_duplicate(content, normalized_kind)
        if duplicate is not None:
            return {"ok": True, "status": "deduplicated", "memory": duplicate.to_dict()}

        blocked_reason = self._sensitive_match(content, SENSITIVE_BLOCK_PATTERNS)
        if blocked_reason:
            return {
                "ok": False,
                "status": "sensitive_blocked",
                "reason": blocked_reason,
            }

        expires_at = time.time() + int(expires_in_seconds) if expires_in_seconds else None
        entry = MemoryEntry(
            memory_id=f"mem_{uuid.uuid4().hex[:12]}",
            kind=normalized_kind,
            content=content,
            source=normalized_source,
            created_at=time.time(),
            tags=tuple(_normalize_tags(tags)),
            importance=float(importance),
            confidence=max(0.0, min(1.0, float(confidence))),
            evidence=normalized_evidence,
            expires_at=expires_at,
            lineage="manual:native_memory_explorer",
            metadata={"evidence_bound": bool(normalized_evidence)},
        )

        review_reason = self._sensitive_match(content, SENSITIVE_REVIEW_PATTERNS)
        if review_reason:
            review = MemoryReviewItem(
                review_id=f"memrev_{uuid.uuid4().hex[:10]}",
                memory_id=entry.memory_id,
                status="pending",
                reason=review_reason,
                content=entry.content,
                source=entry.source,
                kind=entry.kind,
                confidence=entry.confidence,
                created_at=time.time(),
                pending_entry=entry.to_dict(),
            )
            _append_jsonl(self.review_path, review.to_dict())
            return {"ok": False, "status": "review_required", "review": review.to_dict()}

        _append_jsonl(self.memory_path, entry.to_dict())
        return {"ok": True, "status": "created", "memory": entry.to_dict()}

    def privacy_mode_enabled(self) -> bool:
        env = _read_env(self.project_root)
        security = _read_simple_yaml(self.project_root / "config" / "security.yaml")
        raw = str(env.get("SECONDBRAIN_PRIVACY_MODE", security.get("privacy_mode", "false"))).strip().lower()
        return raw in {"1", "true", "yes", "on"}

    def archive(self, memory_ref: str) -> dict[str, Any]:
        return self._set_meta_flag(memory_ref, "archived", True)

    def favorite(self, memory_ref: str, enabled: bool = True) -> dict[str, Any]:
        return self._set_meta_flag(memory_ref, "favorite", bool(enabled))

    def restore(self, memory_ref: str) -> dict[str, Any]:
        return self._set_meta_flag(memory_ref, "archived", False)

    def delete(self, memory_ref: str) -> dict[str, Any]:
        return self._set_meta_flag(memory_ref, "deleted", True)

    def export_json(self) -> dict[str, Any]:
        payload = {
            "generated_at": time.time(),
            "overview": self.overview(),
            "entries": self.entries(include_archived=True, include_expired=True, limit=10000)["items"],
            "reviews": self.list_reviews(limit=10000)["items"],
        }
        target = self.runtime_dir / "memory_export.json"
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "status": "exported", "path": str(target), "items": len(payload["entries"])}

    def export_md(self) -> dict[str, Any]:
        rows = self.entries(include_archived=True, include_expired=True, limit=10000)["items"]
        lines = ["# Memory Export", ""]
        for row in rows:
            lines.append(f"- [{row.get('kind', 'unknown')}] {row.get('content', '')}")
        target = self.runtime_dir / "memory_export.md"
        target.write_text("\n".join(lines), encoding="utf-8")
        return {"ok": True, "status": "exported", "path": str(target), "items": len(rows)}

    def list_reviews(self, *, status: str | None = None, limit: int = 100) -> dict[str, Any]:
        rows = [row for row in _read_jsonl(self.review_path)]
        if status:
            rows = [row for row in rows if str(row.get("status", "")).lower() == status.lower()]
        rows.sort(key=lambda row: float(row.get("created_at") or 0), reverse=True)
        return {"ok": True, "count": len(rows), "items": rows[: max(1, int(limit))]}

    def review_decide(self, review_id: str, *, approved: bool) -> dict[str, Any]:
        rows = [dict(row) for row in _read_jsonl(self.review_path)]
        chosen: dict[str, Any] | None = None
        for row in rows:
            if row.get("review_id") == review_id:
                row["status"] = "approved" if approved else "rejected"
                row["decided_at"] = time.time()
                chosen = row
                break
        if chosen is None:
            return {"ok": False, "status": "review_not_found", "review_id": review_id}
        _write_jsonl(self.review_path, rows)
        if approved:
            pending = chosen.get("pending_entry")
            if isinstance(pending, dict):
                _append_jsonl(self.memory_path, pending)
        return {"ok": True, "status": chosen["status"], "review": chosen}

    def apply_forget_policy(self, *, max_age_days: int = 365, min_confidence: float = 0.15) -> dict[str, Any]:
        now = time.time()
        max_age_seconds = max(1, int(max_age_days)) * 86400
        changed = 0
        expired = 0
        low_confidence = 0
        for entry in self._load_entries():
            remove = False
            if entry.expires_at and float(entry.expires_at) <= now:
                remove = True
                expired += 1
            elif (now - float(entry.created_at)) > max_age_seconds and float(entry.confidence) < float(min_confidence):
                remove = True
                low_confidence += 1
            if remove:
                self._set_meta_flag(entry.memory_id, "archived", True)
                changed += 1
        audit = {
            "ts": now,
            "policy": {"max_age_days": max_age_days, "min_confidence": min_confidence},
            "archived": changed,
            "expired": expired,
            "low_confidence": low_confidence,
        }
        _append_jsonl(self.forget_audit_path, audit)
        return {"ok": True, **audit}

    def sources(self) -> dict[str, int]:
        sources: dict[str, int] = {}
        for entry in self._load_entries():
            if entry.metadata.get("deleted", False):
                continue
            sources[entry.source] = sources.get(entry.source, 0) + 1
        return dict(sorted(sources.items(), key=lambda item: (-item[1], item[0])))

    def timeline(self, *, limit: int = 200) -> dict[str, Any]:
        rows = [entry.to_dict() for entry in self._load_entries() if not entry.metadata.get("deleted", False)]
        rows.sort(key=lambda row: float(row.get("created_at", 0.0)), reverse=True)
        days: dict[str, int] = {}
        for row in rows[: max(1, limit)]:
            day = time.strftime("%Y-%m-%d", time.gmtime(float(row.get("created_at", 0.0))))
            days[day] = days.get(day, 0) + 1
        return {"ok": True, "days": days, "items": rows[: max(1, limit)]}

    def _load_entries(self) -> list[MemoryEntry]:
        rows: list[MemoryEntry] = []

        for raw in _read_jsonl(self.memory_path):
            rows.append(self._from_raw(raw, default_kind="semantic", default_source="memory_entries"))

        for raw in _read_jsonl(self.voice_notes_path):
            rows.append(self._from_raw(raw, default_kind="episodic", default_source="voice_notes"))

        for raw in _read_jsonl(self.legacy_voice_notes_path):
            rows.append(self._from_raw(raw, default_kind="episodic", default_source="voice_notes"))

        for raw in _read_jsonl(self.chat_history_path):
            rows.append(self._from_raw(raw, default_kind="episodic", default_source="chat_history"))

        for raw in _read_jsonl(self.legacy_chat_history_path):
            rows.append(self._from_raw(raw, default_kind="episodic", default_source="chat_history"))

        for conversation in self._iter_chat_conversations():
            memory = conversation.get("memory")
            if isinstance(memory, list):
                for item in memory:
                    rows.append(self._from_raw(item, default_kind="episodic", default_source="chat_memory"))

        meta = self._load_meta()
        merged: dict[str, MemoryEntry] = {}
        for entry in rows:
            if not entry.memory_id:
                continue
            existing = merged.get(entry.memory_id)
            if existing is not None and existing.created_at >= entry.created_at:
                continue
            flags = meta.get(entry.memory_id, {})
            payload = {
                **entry.to_dict(),
                "tags": tuple(entry.tags),
                "evidence": tuple(entry.evidence),
                "archived": bool(flags.get("archived", entry.archived)),
                "favorite": bool(flags.get("favorite", entry.favorite)),
                "metadata": {**entry.metadata, "deleted": bool(flags.get("deleted", False))},
            }
            merged[entry.memory_id] = MemoryEntry(**payload)
        return list(merged.values())

    def _from_raw(self, raw: dict[str, Any], *, default_kind: str, default_source: str) -> MemoryEntry:
        content = str(raw.get("content") or raw.get("text") or raw.get("message") or "").strip()
        if not content:
            content = "(leer)"
        memory_id = str(raw.get("memory_id") or raw.get("id") or f"mem_{uuid.uuid4().hex[:12]}")
        created = raw.get("created_at") or raw.get("ts") or raw.get("timestamp") or time.time()
        try:
            created_at = float(created)
        except (TypeError, ValueError):
            created_at = time.time()
        expires_raw = raw.get("expires_at")
        expires_at: float | None = None
        if expires_raw is not None:
            try:
                expires_at = float(expires_raw)
            except (TypeError, ValueError):
                expires_at = None
        return MemoryEntry(
            memory_id=memory_id,
            kind=self._normalize_kind(str(raw.get("kind") or default_kind), allow_legacy=True),
            content=content,
            source=str(raw.get("source") or default_source),
            created_at=created_at,
            tags=tuple(_normalize_tags(raw.get("tags") or [])),
            importance=float(raw.get("importance") or 0.5),
            confidence=max(0.0, min(1.0, float(raw.get("confidence") or 0.5))),
            evidence=tuple(_normalize_strings(raw.get("evidence") or [])),
            expires_at=expires_at,
            archived=bool(raw.get("archived") or False),
            favorite=bool(raw.get("favorite") or False),
            lineage=str(raw.get("lineage") or default_source),
            metadata=dict(raw.get("metadata") or {}),
        )

    def _iter_chat_conversations(self) -> Iterable[dict[str, Any]]:
        if not self.chat_root.exists():
            return []
        conversations: list[dict[str, Any]] = []
        for file in self.chat_root.glob("*.json"):
            try:
                payload = json.loads(file.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(payload, dict):
                conversations.append(payload)
        return conversations

    def _resolve(self, memory_ref: str) -> MemoryEntry | None:
        ref = memory_ref.strip().lower()
        for entry in self._load_entries():
            if entry.memory_id.lower() == ref:
                return entry
        return None

    def _set_meta_flag(self, memory_ref: str, key: str, value: bool) -> dict[str, Any]:
        match = self._resolve(memory_ref)
        if match is None:
            return {"ok": False, "status": "not_found", "memory_ref": memory_ref}
        meta = self._load_meta()
        row = dict(meta.get(match.memory_id, {}))
        row[key] = bool(value)
        row.setdefault("updated_at", time.time())
        row["updated_at"] = time.time()
        meta[match.memory_id] = row
        self._save_meta(meta)
        return {"ok": True, "status": "updated", "memory_id": match.memory_id, key: bool(value)}

    def _normalize_kind(self, kind: str, *, allow_legacy: bool = False) -> str:
        normalized = (kind or "").strip().lower()
        if normalized in MEMORY_TYPES:
            return normalized
        if allow_legacy and normalized in {"conversation"}:
            return normalized
        if normalized in {"working", "conversation", "imported"}:
            return "episodic"
        return "semantic"

    def _find_duplicate(self, content: str, kind: str) -> MemoryEntry | None:
        needle = _canonical_text(content)
        for entry in self._load_entries():
            if entry.kind != kind:
                continue
            if _canonical_text(entry.content) == needle and not entry.metadata.get("deleted", False):
                return entry
        return None

    @staticmethod
    def _sensitive_match(content: str, patterns: Iterable[re.Pattern[str]]) -> str:
        for pattern in patterns:
            if pattern.search(content):
                return pattern.pattern
        return ""

    def _load_meta(self) -> dict[str, dict[str, Any]]:
        if not self.meta_path.exists():
            return {}
        try:
            payload = json.loads(self.meta_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(payload, dict):
            return {}
        normalized: dict[str, dict[str, Any]] = {}
        for key, value in payload.items():
            if isinstance(value, dict):
                normalized[str(key)] = dict(value)
        return normalized

    def _save_meta(self, payload: dict[str, dict[str, Any]]) -> None:
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


class MemoryExplorer(MemoryExplorerService):
    VERSION = "30.33"

    def __init__(self, project_root: Path | str = ".", ensure_dirs: bool = True) -> None:
        super().__init__(project_root)
        if ensure_dirs:
            self.runtime_dir.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict[str, Any]:
        return {"ok": True, "version": self.VERSION, **self.overview()}

    def export(self, fmt: str = "json") -> dict[str, Any]:
        if str(fmt).lower() == "md":
            return self.export_md()
        return self.export_json()


def _normalize_tags(tags: Iterable[Any]) -> list[str]:
    if isinstance(tags, str):
        raw = tags.replace(";", ",").split(",")
    else:
        raw = list(tags)
    return sorted({str(item).strip().lower() for item in raw if str(item).strip()})


def _normalize_strings(values: Iterable[Any]) -> list[str]:
    if isinstance(values, str):
        values = values.replace(";", ",").split(",")
    return [str(value).strip() for value in values if str(value).strip()]


def _canonical_text(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _read_env(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    env = root / ".env"
    if not env.exists():
        return out
    try:
        for raw in env.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            out[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        return {}
    return out


def _read_simple_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    out: dict[str, Any] = {}
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            out[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        return {}
    return out
