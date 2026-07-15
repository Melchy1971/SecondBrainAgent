"""Long-term memory consolidation service.

Groups semantic duplicates, merges their evidence, recomputes confidence, ages
memories by a type-specific half-life and resolves conflicts by explicit
decision. Invariants:

* consolidation is idempotent - running it again changes nothing;
* a user correction always wins and supersedes conflicting memories;
* conflicts are never silently overwritten - both sides are retained;
* important or protected (sensitive) memories are never auto-deleted;
* ``no_memory`` is absolute and privacy mode blocks all writes;
* deletion is approval-gated and export carries full provenance.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from hashlib import sha256
from typing import Any, Iterable, Mapping, Sequence
from uuid import uuid4

from secondbrain.memory_consolidation.models import (
    Decision, DuplicateGroup, Memory, MemoryConflict, MemoryStatus, MemoryType,
    ConflictType, TYPE_HALFLIFE_DAYS,
)

__all__ = ["MemoryConsolidator", "SIMILARITY_THRESHOLD", "IMPORTANT_THRESHOLD"]

SIMILARITY_THRESHOLD = 0.72
IMPORTANT_THRESHOLD = 0.8
_TOKEN_RE = re.compile(r"[a-z0-9äöüß]+")
_SECRET_RE = re.compile(r"(?i)(api[_-]?key|password|secret|token|-----BEGIN)")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def _parse(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def _stem(token: str) -> str:
    # light German inflection trim: drop a single trailing "s" (plural/genitive) on longer tokens
    if len(token) > 4 and token[-1] == "s":
        return token[:-1]
    return token


def _tokens(text: str) -> set[str]:
    return {_stem(t) for t in _TOKEN_RE.findall((text or "").lower())}


class MemoryConsolidator:
    def __init__(self, *, privacy_mode: bool = False) -> None:
        self.privacy_mode = privacy_mode
        self._memories: dict[str, Memory] = {}
        self._conflicts: list[MemoryConflict] = []
        self._committed: set[str] = set()
        self._merge_history: list[dict[str, Any]] = []

    # -- writes -----------------------------------------------------------

    def add_memory(self, *, workspace_id: str, type: str, content: str,
                   source_ids: Sequence[str] | None = None, evidence: Sequence[Mapping[str, Any]] | None = None,
                   confidence: float = 0.75, importance: float = 0.5, no_memory: bool = False,
                   sensitive: bool | None = None, now: datetime | None = None) -> Memory:
        if self.privacy_mode:
            raise PermissionError("privacy_mode_active")
        moment = now or _now()
        is_sensitive = bool(_SECRET_RE.search(content)) if sensitive is None else bool(sensitive)
        blocked = bool(no_memory) or bool(_SECRET_RE.search(content))
        mem = Memory(
            memory_id=str(uuid4()), workspace_id=workspace_id, type=type, content=content,
            normalized_content=" ".join(sorted(_tokens(content))),
            evidence=[dict(e) for e in (evidence or [])], source_ids=list(source_ids or []),
            confidence=float(confidence), importance=float(importance), created_at=_iso(moment),
            last_confirmed_at=_iso(moment), updated_at=_iso(moment), sensitive=is_sensitive, no_memory=bool(no_memory),
            status=MemoryStatus.BLOCKED.value if blocked else MemoryStatus.ACTIVE.value,
        )
        self._memories[mem.memory_id] = mem
        return mem

    def confirm(self, memory_id: str, *, now: datetime | None = None) -> Memory:
        """User confirmation: resets age (last_confirmed_at) and marks confirmed."""
        if self.privacy_mode:
            raise PermissionError("privacy_mode_active")
        mem = self._memories[memory_id]
        mem.last_confirmed_at = _iso(now or _now())
        mem.user_confirmed = True
        if mem.status == MemoryStatus.EXPIRED.value:
            mem.status = MemoryStatus.ACTIVE.value
        return mem

    def apply_correction(self, *, workspace_id: str, type: str, content: str,
                         supersedes: Iterable[str], source_ids: Sequence[str] | None = None,
                         now: datetime | None = None) -> Memory:
        """User correction wins: create authoritative memory, supersede the rest."""
        if self.privacy_mode:
            raise PermissionError("privacy_mode_active")
        correction = self.add_memory(workspace_id=workspace_id, type=type, content=content,
                                     source_ids=source_ids, confidence=1.0, now=now)
        correction.user_confirmed = True
        for mid in supersedes:
            old = self._memories.get(mid)
            if old is not None:
                old.status = MemoryStatus.SUPERSEDED.value
                old.superseded_by = correction.memory_id  # retained, not deleted
        return correction

    # -- duplicate detection & consolidation -----------------------------

    def _active(self, workspace_id: str) -> list[Memory]:
        return [m for m in self._memories.values()
                if m.workspace_id == workspace_id and m.status == MemoryStatus.ACTIVE.value]

    def similarity(self, a: Memory, b: Memory) -> float:
        if a.type != b.type:
            return 0.0
        ta, tb = _tokens(a.content), _tokens(b.content)
        jaccard = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
        seq = SequenceMatcher(None, a.content.lower(), b.content.lower()).ratio()
        return max(jaccard, seq)

    def find_duplicates(self, *, workspace_id: str) -> list[DuplicateGroup]:
        mems = sorted(self._active(workspace_id), key=lambda m: m.created_at)
        groups: list[DuplicateGroup] = []
        used: set[str] = set()
        for i, base in enumerate(mems):
            if base.memory_id in used:
                continue
            members = [base.memory_id]
            best = 1.0
            for other in mems[i + 1:]:
                if other.memory_id in used or other.sensitive or base.sensitive:
                    continue
                sim = self.similarity(base, other)
                if sim >= SIMILARITY_THRESHOLD:
                    members.append(other.memory_id)
                    used.add(other.memory_id)
                    best = min(best, sim)
            if len(members) > 1:
                used.add(base.memory_id)
                groups.append(DuplicateGroup(key=base.memory_id, memory_ids=members, similarity=best))
        return groups

    def consolidate(self, *, workspace_id: str, now: datetime | None = None) -> dict[str, Any]:
        """Idempotent: merge each duplicate group into its newest-confirmed
        member, fold evidence, recompute confidence, supersede the rest."""
        merged = 0
        # Never auto-merge across a contradiction: surface similarity cannot
        # tell a reworded statement from its opposite, so any group entangled
        # with a contradictory conflict stays active for a human decision.
        contradictory: set[str] = set()
        for c in self.detect_conflicts(workspace_id=workspace_id, now=now):
            if c.conflict_type == ConflictType.CONTRADICTORY.value:
                contradictory.update(c.memory_ids)
        for group in self.find_duplicates(workspace_id=workspace_id):
            members = [self._memories[mid] for mid in group.memory_ids]
            # winner = most recently confirmed, user_confirmed preferred
            winner = max(members, key=lambda m: (m.user_confirmed, _parse(m.last_confirmed_at) or datetime.min.replace(tzinfo=timezone.utc)))
            if winner.memory_id in contradictory:
                continue
            others = [m for m in members
                      if m.memory_id != winner.memory_id and m.memory_id not in contradictory]
            if not others:
                continue
            self._merge_history.append({
                "winner": winner.memory_id,
                "winner_evidence": list(winner.evidence),
                "winner_sources": list(winner.source_ids),
                "winner_confidence": winner.confidence,
                "winner_importance": winner.importance,
                "others": [(m.memory_id, m.status, m.superseded_by) for m in others],
            })
            for other in others:
                for e in other.evidence:
                    if e not in winner.evidence:
                        winner.evidence.append(e)
                for s in other.source_ids:
                    if s not in winner.source_ids:
                        winner.source_ids.append(s)
                other.status = MemoryStatus.SUPERSEDED.value
                other.superseded_by = winner.memory_id  # retained
                merged += 1
            winner.confidence = round(min(1.0, max(m.confidence for m in members) + 0.02 * len(others)), 3)
            winner.importance = max(m.importance for m in members)
        return {"merged": merged, "active": len(self._active(workspace_id))}

    def undo_merge(self, winner_id: str) -> int:
        snapshot = next((item for item in reversed(self._merge_history) if item["winner"] == winner_id), None)
        if snapshot is None:
            raise KeyError("merge_not_found")
        winner = self._memories[winner_id]
        winner.evidence = snapshot["winner_evidence"]
        winner.source_ids = snapshot["winner_sources"]
        winner.confidence = snapshot["winner_confidence"]
        winner.importance = snapshot["winner_importance"]
        for memory_id, status, superseded_by in snapshot["others"]:
            memory = self._memories[memory_id]
            memory.status, memory.superseded_by = status, superseded_by
        self._merge_history.remove(snapshot)
        return len(snapshot["others"])

    # -- conflicts --------------------------------------------------------

    def detect_conflicts(self, *, workspace_id: str, known_subjects: Mapping[str, str] | None = None,
                         now: datetime | None = None) -> list[MemoryConflict]:
        moment = now or _now()
        found: list[MemoryConflict] = []
        active = self._active(workspace_id)
        # contradictory: same subject fingerprint, different content
        by_subject: dict[str, list[Memory]] = {}
        for m in active:
            by_subject.setdefault(self._subject(m.content), []).append(m)
        for subject, mems in by_subject.items():
            contents = {m.content for m in mems}
            if len(contents) > 1 and subject:
                found.append(MemoryConflict(ConflictType.CONTRADICTORY.value,
                                            [m.memory_id for m in mems], detail=subject))
        for m in active:
            # outdated: episodic well past half-life
            if self._effective_confidence(m, moment) < 0.1 and m.type == MemoryType.EPISODIC.value:
                found.append(MemoryConflict(ConflictType.OUTDATED.value, [m.memory_id], detail="decayed"))
            # unsupported: preference without evidence/source
            if m.type == MemoryType.PREFERENCE.value and not m.evidence and not m.source_ids:
                found.append(MemoryConflict(ConflictType.UNSUPPORTED.value, [m.memory_id], detail="no_evidence"))
        self._conflicts = found
        return found

    def resolve(self, conflict: MemoryConflict, *, decision: str, keep: str | None = None) -> None:
        if decision not in {d.value for d in Decision}:
            raise ValueError("invalid_decision")
        conflict.decision = decision
        conflict.status = "resolved" if decision != Decision.DEFER.value else "deferred"
        if decision == Decision.SUPERSEDE.value and keep is not None:
            for mid in conflict.memory_ids:
                if mid != keep and mid in self._memories:
                    self._memories[mid].status = MemoryStatus.SUPERSEDED.value
                    self._memories[mid].superseded_by = keep  # retained
        elif decision == Decision.REJECT.value:
            for mid in conflict.memory_ids:
                m = self._memories.get(mid)
                if m and not (m.importance >= IMPORTANT_THRESHOLD or m.sensitive):
                    m.status = MemoryStatus.BLOCKED.value

    # -- decay ------------------------------------------------------------

    def _effective_confidence(self, mem: Memory, moment: datetime) -> float:
        half = TYPE_HALFLIFE_DAYS.get(mem.type)
        if half is None:
            return mem.confidence
        anchor = _parse(mem.last_confirmed_at) or _parse(mem.created_at) or moment
        age_days = max(0.0, (moment - anchor).total_seconds() / 86400.0)
        factor = 0.5 ** (age_days / half)
        if mem.user_confirmed:
            factor = min(1.0, factor * 1.5)  # confirmed ages slower
        return round(mem.confidence * factor, 3)

    def apply_decay(self, *, workspace_id: str, now: datetime | None = None) -> dict[str, int]:
        moment = now or _now()
        expired = 0
        for m in self._active(workspace_id):
            eff = self._effective_confidence(m, moment)
            hard_expired = m.expires_at is not None and (_parse(m.expires_at) or moment) <= moment
            faded = eff < 0.1
            if (hard_expired or (faded and m.type == MemoryType.EPISODIC.value)):
                if m.importance >= IMPORTANT_THRESHOLD or m.sensitive or m.user_confirmed:
                    continue  # important/protected memories are never auto-expired
                m.status = MemoryStatus.EXPIRED.value  # marked, not deleted
                expired += 1
        return {"expired": expired}

    def effective_confidence(self, memory_id: str, *, now: datetime | None = None) -> float:
        return self._effective_confidence(self._memories[memory_id], now or _now())

    # -- deletion (approval) & export ------------------------------------

    @staticmethod
    def _payload_hash(payload: Mapping[str, Any]) -> str:
        return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    def prepare_delete(self, memory_id: str, *, workspace_id: str, approval_queue: Any | None = None) -> dict[str, Any]:
        if memory_id not in self._memories:
            raise KeyError("unknown_memory")
        if self._memories[memory_id].workspace_id != workspace_id:
            raise ValueError("workspace_mismatch")
        payload = {"action": "delete_memory", "memory_id": memory_id, "workspace_id": workspace_id}
        payload_hash = self._payload_hash(payload)
        approval_id = ""
        if approval_queue is not None:
            approval = approval_queue.create(command="memory.delete", intent="delete_memory", text="Memory archivieren",
                                             target=memory_id, category="delete_request", risk_level="high",
                                             tool_name="memory.delete", workspace_id=workspace_id,
                                             payload={**payload, "payload_hash": payload_hash}, tool_idempotent=False)
            approval_id = str(approval.get("approval_id") or "")
        return {"status": "approval_required", "approval_id": approval_id, "payload_hash": payload_hash, **payload}

    def commit_delete(self, prepared: Mapping[str, Any], *, approval_queue: Any, workspace_id: str) -> dict[str, Any]:
        approval_id = str(prepared.get("approval_id") or "")
        if approval_queue is None or not approval_id:
            return {"status": "blocked", "reason": "approval_required"}
        if workspace_id != prepared.get("workspace_id"):
            return {"status": "blocked", "reason": "workspace_mismatch"}
        payload = {k: prepared[k] for k in ("action", "memory_id", "workspace_id")}
        if self._payload_hash(payload) != prepared.get("payload_hash"):
            return {"status": "invalid", "reason": "payload_changed"}
        key = str(prepared.get("payload_hash"))
        if key in self._committed:
            return {"status": "duplicate", "reason": "already_committed"}
        try:
            approval_queue.begin_execution(approval_id, executor_id="memory-consolidation")
        except Exception as exc:
            return {"status": "blocked", "reason": f"approval_not_executable:{type(exc).__name__}"}
        mid = prepared["memory_id"]
        if mid not in self._memories:
            return {"status": "error", "reason": "unknown_memory"}
        self._memories[mid].status = MemoryStatus.BLOCKED.value
        self._memories[mid].updated_at = _iso(_now())
        self._committed.add(key)
        return {"status": "committed", "memory_id": mid}

    def produce_report(self, *, workspace_id: str, now: datetime | None = None) -> dict[str, Any]:
        memories = self.memories(workspace_id=workspace_id)
        return {"workspace_id": workspace_id, "generated_at": _iso(now or _now()),
                "counts": {status.value: sum(m.status == status.value for m in memories) for status in MemoryStatus},
                "duplicate_groups": len(self.find_duplicates(workspace_id=workspace_id)),
                "conflicts": len(self.detect_conflicts(workspace_id=workspace_id, now=now))}

    def export(self, *, workspace_id: str, include_blocked: bool = False) -> list[dict[str, Any]]:
        """Full-provenance export: content, evidence, sources, supersede chain."""
        out = []
        for m in self._memories.values():
            if m.workspace_id != workspace_id:
                continue
            if m.no_memory:
                continue  # no_memory is absolute - never exported
            if m.status == MemoryStatus.BLOCKED.value and not include_blocked:
                continue
            record = m.to_dict()
            record["provenance"] = {"source_ids": list(m.source_ids), "evidence": [dict(e) for e in m.evidence],
                                    "superseded_by": m.superseded_by, "created_at": m.created_at,
                                    "last_confirmed_at": m.last_confirmed_at}
            out.append(record)
        return out

    # -- helpers ----------------------------------------------------------

    def memories(self, *, workspace_id: str, status: str | None = None) -> list[Memory]:
        out = [m for m in self._memories.values() if m.workspace_id == workspace_id]
        return [m for m in out if status is None or m.status == status]

    def get(self, memory_id: str) -> Memory | None:
        return self._memories.get(memory_id)

    @staticmethod
    def _subject(text: str) -> str:
        tokens = _TOKEN_RE.findall((text or "").lower())
        stop = {"ist", "war", "der", "die", "das", "the", "a", "und", "and", "of", "is", "mag", "hat"}
        sig = [t for t in tokens if t not in stop]
        return " ".join(sig[:2])
