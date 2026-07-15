"""Evidence-based knowledge graph service.

Adds entities and relationships, resolves probable duplicates without ever
auto-merging on weak evidence, records attribute conflicts instead of
overwriting them, answers graph queries with their supporting sources, and
gates deletion behind an approval. Nothing here calls an external system; the
only guarded operation is delete, which follows the prepare/commit approval
pattern used across the agent.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from hashlib import sha256
from typing import Any, Iterable, Mapping, Sequence
from uuid import uuid4

from secondbrain.knowledge_graph.models import (
    AttributeValue, Conflict, Entity, EntityType, MergeProposal, Relationship, RelationType,
)

__all__ = ["KnowledgeGraph", "AUTO_MERGE_THRESHOLD", "normalize_name"]

AUTO_MERGE_THRESHOLD = 0.9
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_TOKEN_RE = re.compile(r"[a-z0-9äöüß]+")


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (name or "").lower())).strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class KnowledgeGraph:
    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._relationships: dict[str, Relationship] = {}
        self._conflicts: list[Conflict] = []
        self._committed: set[str] = set()
        self._merge_history: list[dict[str, Any]] = []

    # -- ingestion --------------------------------------------------------

    def add_entity(self, *, workspace_id: str, canonical_name: str, type: str,
                   aliases: Sequence[str] | None = None, source_ids: Sequence[str] | None = None,
                   evidence: Sequence[Mapping[str, Any]] | None = None, confidence: float = 1.0,
                   valid_from: str = "") -> Entity:
        ent = Entity(
            id=str(uuid4()), workspace_id=workspace_id, canonical_name=canonical_name.strip(),
            type=type, aliases=[a.strip() for a in (aliases or []) if a.strip()],
            source_ids=list(source_ids or []), evidence=[dict(e) for e in (evidence or [])],
            confidence=float(confidence), valid_from=valid_from, created_at=_now(), updated_at=_now(),
        )
        self._entities[ent.id] = ent
        return ent

    def add_relationship(self, *, workspace_id: str, source_entity: str, target_entity: str, type: str,
                         evidence: Sequence[Mapping[str, Any]] | None = None,
                         origin_source_ids: Sequence[str] | None = None, confidence: float = 1.0,
                         valid_from: str = "") -> Relationship:
        if source_entity not in self._entities or target_entity not in self._entities:
            raise KeyError("unknown_entity")
        if any(self._entities[entity_id].workspace_id != workspace_id
               for entity_id in (source_entity, target_entity)):
            raise ValueError("workspace_mismatch")
        ev = [dict(e) for e in (evidence or [])]
        if not ev and not origin_source_ids:
            raise ValueError("relationship_requires_evidence")
        rel = Relationship(
            id=str(uuid4()), workspace_id=workspace_id, source_id=source_entity, target_id=target_entity,
            type=type, evidence=ev, origin_source_ids=list(origin_source_ids or []),
            confidence=float(confidence), valid_from=valid_from, created_at=_now(), updated_at=_now(),
        )
        self._relationships[rel.id] = rel
        return rel

    def extract_candidates(self, document: Mapping[str, Any], *, workspace_id: str) -> list[Entity]:
        """Turn a document into entity candidates. Every candidate keeps the
        document id as source and a short evidence snippet."""
        doc_id = str(document.get("id") or document.get("source_reference") or "")
        text = str(document.get("text", ""))
        created: list[Entity] = []
        for person in document.get("people", []) or []:
            created.append(self.add_entity(
                workspace_id=workspace_id, canonical_name=str(person), type=EntityType.PERSON.value,
                source_ids=[doc_id], confidence=0.7,
                evidence=[{"source_id": doc_id, "snippet": self._snippet(text, str(person))}]))
        for org in document.get("organizations", []) or []:
            created.append(self.add_entity(
                workspace_id=workspace_id, canonical_name=str(org), type=EntityType.ORGANIZATION.value,
                source_ids=[doc_id], confidence=0.7,
                evidence=[{"source_id": doc_id, "snippet": self._snippet(text, str(org))}]))
        for proj in document.get("projects", []) or []:
            created.append(self.add_entity(
                workspace_id=workspace_id, canonical_name=str(proj), type=EntityType.PROJECT.value,
                source_ids=[doc_id], confidence=0.7,
                evidence=[{"source_id": doc_id, "snippet": self._snippet(text, str(proj))}]))
        return created

    # -- attributes & conflicts ------------------------------------------

    def set_attribute(self, entity_id: str, key: str, value: str, *, source_id: str = "",
                      confidence: float = 1.0, valid_from: str = "") -> Conflict | None:
        ent = self._entities[entity_id]
        current = ent.attributes.setdefault(key, [])
        active = [v for v in current if not v.superseded_by]
        new_val = AttributeValue(value=value, source_id=source_id, confidence=confidence, valid_from=valid_from)
        if any(v.value == value for v in active):
            return None
        current.append(new_val)
        ent.updated_at = _now()
        distinct = {v.value for v in current if not v.superseded_by}
        if len(distinct) > 1:
            conflict = Conflict(entity_id=entity_id, attribute=key,
                                values=[v for v in current if not v.superseded_by])
            self._conflicts.append(conflict)
            return conflict
        return None

    def conflicts(self, *, workspace_id: str | None = None, status: str = "open") -> list[Conflict]:
        out = []
        for c in self._conflicts:
            if c.status != status:
                continue
            if workspace_id is not None and self._entities.get(c.entity_id, Entity("", "", "", "")).workspace_id != workspace_id:
                continue
            out.append(c)
        return out

    def resolve_conflict(self, conflict: Conflict, *, resolution: str, keep_value: str | None = None) -> None:
        if resolution not in ("keep_both", "supersede", "merge"):
            raise ValueError("invalid_resolution")
        conflict.status = "resolved"
        conflict.resolution = resolution
        if resolution == "supersede" and keep_value is not None:
            ent = self._entities[conflict.entity_id]
            for v in ent.attributes.get(conflict.attribute, []):
                if v.value != keep_value and not v.superseded_by:
                    v.superseded_by = keep_value  # retained, not deleted

    # -- entity resolution ------------------------------------------------

    def match_score(self, a: Entity, b: Entity) -> tuple[float, dict[str, Any]]:
        signals: dict[str, Any] = {}
        if a.type != b.type:
            return 0.0, {"type_mismatch": True}
        na, nb = normalize_name(a.canonical_name), normalize_name(b.canonical_name)
        name_sim = SequenceMatcher(None, na, nb).ratio()
        signals["name_similarity"] = round(name_sim, 3)
        alias_hit = bool({normalize_name(x) for x in a.aliases + [a.canonical_name]} &
                         {normalize_name(x) for x in b.aliases + [b.canonical_name]})
        signals["alias_match"] = alias_hit
        emails_a = {m.lower() for x in a.aliases + a.source_ids for m in _EMAIL_RE.findall(x)}
        emails_b = {m.lower() for x in b.aliases + b.source_ids for m in _EMAIL_RE.findall(x)}
        email_hit = bool(emails_a & emails_b)
        signals["email_match"] = email_hit
        source_overlap = bool(set(a.source_ids) & set(b.source_ids))
        signals["source_overlap"] = source_overlap
        score = max(name_sim, 1.0 if alias_hit else 0.0, 1.0 if email_hit else 0.0)
        if source_overlap:
            score = min(1.0, score + 0.05)
        return score, signals

    def detect_duplicates(self, *, workspace_id: str, threshold: float = 0.6) -> list[MergeProposal]:
        ents = [e for e in self._entities.values() if e.workspace_id == workspace_id and not e.superseded_by]
        proposals: list[MergeProposal] = []
        for i in range(len(ents)):
            for j in range(i + 1, len(ents)):
                score, signals = self.match_score(ents[i], ents[j])
                if score >= threshold:
                    proposals.append(MergeProposal(
                        entity_a=ents[i].id, entity_b=ents[j].id, score=score, signals=signals,
                        auto_mergeable=(score >= AUTO_MERGE_THRESHOLD and
                                        (ents[i].type != EntityType.PERSON.value or bool(signals.get("email_match"))))))
        proposals.sort(key=lambda p: -p.score)
        return proposals

    def resolve_duplicates(self, *, workspace_id: str, auto_only: bool = True) -> list[str]:
        """Merge only auto-mergeable proposals. Low-confidence pairs are left
        for manual decision - never merged here."""
        merged: list[str] = []
        for prop in self.detect_duplicates(workspace_id=workspace_id):
            if auto_only and not prop.auto_mergeable:
                continue
            if prop.entity_a in self._entities and prop.entity_b in self._entities:
                self.merge(prop.entity_a, prop.entity_b)
                merged.append(prop.entity_b)
        return merged

    def merge(self, keep_id: str, drop_id: str) -> Entity:
        """Manual/explicit merge: fold drop into keep, retain drop as superseded."""
        keep, drop = self._entities[keep_id], self._entities[drop_id]
        if keep.workspace_id != drop.workspace_id:
            raise ValueError("workspace_mismatch")
        snapshot = {"keep_id": keep_id, "drop_id": drop_id, "keep_aliases": list(keep.aliases),
                    "keep_sources": list(keep.source_ids), "keep_evidence": list(keep.evidence),
                    "relationships": {rid: (rel.source_id, rel.target_id) for rid, rel in self._relationships.items()}}
        self._merge_history.append(snapshot)
        keep.aliases = sorted(set(keep.aliases) | set(drop.aliases) | {drop.canonical_name})
        keep.source_ids = sorted(set(keep.source_ids) | set(drop.source_ids))
        keep.evidence = keep.evidence + drop.evidence
        keep.updated_at = _now()
        drop.superseded_by = keep_id
        drop.valid_to = _now()
        for rel in self._relationships.values():
            if rel.source_id == drop_id:
                rel.source_id = keep_id
            if rel.target_id == drop_id:
                rel.target_id = keep_id
        return keep

    def undo_merge(self, keep_id: str, drop_id: str) -> Entity:
        snapshot = next((item for item in reversed(self._merge_history)
                         if item["keep_id"] == keep_id and item["drop_id"] == drop_id), None)
        if snapshot is None:
            raise KeyError("merge_not_found")
        keep, drop = self._entities[keep_id], self._entities[drop_id]
        keep.aliases = snapshot["keep_aliases"]
        keep.source_ids = snapshot["keep_sources"]
        keep.evidence = snapshot["keep_evidence"]
        drop.superseded_by = ""
        drop.valid_to = ""
        for rid, endpoints in snapshot["relationships"].items():
            if rid in self._relationships:
                self._relationships[rid].source_id, self._relationships[rid].target_id = endpoints
        self._merge_history.remove(snapshot)
        return drop

    # -- queries (always return sources) ---------------------------------

    def relations_of(self, entity_id: str) -> list[dict[str, Any]]:
        out = []
        for rel in self._relationships.values():
            if rel.superseded_by:
                continue
            if rel.source_id == entity_id or rel.target_id == entity_id:
                other = rel.target_id if rel.source_id == entity_id else rel.source_id
                out.append({"relationship": rel.type, "other": self._name(other),
                            "other_id": other, "sources": rel.origin_source_ids or [e.get("source_id", "") for e in rel.evidence],
                            "evidence": rel.evidence})
        return out

    def path_between(self, a: str, b: str, *, max_depth: int = 5) -> list[str]:
        if a not in self._entities or b not in self._entities:
            return []
        adj: dict[str, set[str]] = {}
        for rel in self._relationships.values():
            if rel.superseded_by:
                continue
            adj.setdefault(rel.source_id, set()).add(rel.target_id)
            adj.setdefault(rel.target_id, set()).add(rel.source_id)
        queue: list[list[str]] = [[a]]
        seen = {a}
        while queue:
            path = queue.pop(0)
            if len(path) > max_depth + 1:
                continue
            if path[-1] == b:
                return path
            for nxt in sorted(adj.get(path[-1], ())):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(path + [nxt])
        return []

    def context(self, entity_id: str, *, want_types: Iterable[str] | None = None) -> dict[str, Any]:
        """Project/person context, relevant documents, open tasks, upcoming
        events - each with the entities' source ids."""
        wants = set(want_types) if want_types else None
        related: dict[str, list[dict[str, Any]]] = {}
        for r in self.relations_of(entity_id):
            ent = self._entities.get(r["other_id"])
            if ent is None or ent.superseded_by:
                continue
            if wants and ent.type not in wants:
                continue
            related.setdefault(ent.type, []).append(
                {"name": ent.canonical_name, "id": ent.id, "sources": ent.source_ids})
        return {"entity": self._name(entity_id), "entity_id": entity_id, "related": related}

    def context_for_rag(self, entity_id: str) -> dict[str, Any]:
        """Compact, evidence-bearing context block usable as RAG grounding."""
        ent = self._entities[entity_id]
        return {
            "canonical_name": ent.canonical_name,
            "type": ent.type,
            "aliases": ent.aliases,
            "sources": ent.source_ids,
            "evidence": ent.evidence,
            "relations": self.relations_of(entity_id),
        }

    # -- deletion (approval-gated) ---------------------------------------

    @staticmethod
    def _payload_hash(payload: Mapping[str, Any]) -> str:
        return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    def prepare_delete(self, entity_id: str, *, workspace_id: str, approval_queue: Any | None = None) -> dict[str, Any]:
        if entity_id not in self._entities:
            raise KeyError("unknown_entity")
        if self._entities[entity_id].workspace_id != workspace_id:
            raise ValueError("workspace_mismatch")
        payload = {"action": "delete_entity", "entity_id": entity_id, "workspace_id": workspace_id}
        payload_hash = self._payload_hash(payload)
        approval_id = ""
        if approval_queue is not None:
            approval = approval_queue.create(command="graph.delete_entity", intent="delete_entity",
                                             text="Knowledge graph entity archivieren", target=entity_id,
                                             category="delete_request", risk_level="high",
                                             tool_name="graph.delete_entity", workspace_id=workspace_id,
                                             payload={**payload, "payload_hash": payload_hash}, tool_idempotent=False)
            approval_id = str(approval.get("approval_id") or "")
        return {"status": "approval_required", "approval_id": approval_id, "payload_hash": payload_hash, **payload}

    def commit_delete(self, prepared: Mapping[str, Any], *, approval_queue: Any, workspace_id: str) -> dict[str, Any]:
        approval_id = str(prepared.get("approval_id") or "")
        if approval_queue is None or not approval_id:
            return {"status": "blocked", "reason": "approval_required"}
        if workspace_id != prepared.get("workspace_id"):
            return {"status": "blocked", "reason": "workspace_mismatch"}
        payload = {k: prepared[k] for k in ("action", "entity_id", "workspace_id")}
        if self._payload_hash(payload) != prepared.get("payload_hash"):
            return {"status": "invalid", "reason": "payload_changed"}
        key = str(prepared.get("payload_hash"))
        if key in self._committed:
            return {"status": "duplicate", "reason": "already_committed"}
        try:
            approval_queue.begin_execution(approval_id, executor_id="knowledge-graph")
        except Exception as exc:
            return {"status": "blocked", "reason": f"approval_not_executable:{type(exc).__name__}"}
        eid = prepared["entity_id"]
        if eid not in self._entities:
            return {"status": "error", "reason": "unknown_entity"}
        self._entities[eid].status = "archived"
        self._entities[eid].valid_to = _now()
        for relationship in self._relationships.values():
            if relationship.source_id == eid or relationship.target_id == eid:
                relationship.status = "archived"
        self._committed.add(key)
        return {"status": "committed", "entity_id": eid}

    # -- helpers ----------------------------------------------------------

    def entities(self, *, workspace_id: str, include_superseded: bool = False) -> list[Entity]:
        return [e for e in self._entities.values() if e.workspace_id == workspace_id and e.status == "active"
                and (include_superseded or not e.superseded_by)]

    def get(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def _name(self, entity_id: str) -> str:
        ent = self._entities.get(entity_id)
        return ent.canonical_name if ent else ""

    @staticmethod
    def _snippet(text: str, term: str, width: int = 60) -> str:
        idx = text.lower().find(term.lower())
        if idx < 0:
            return term
        start = max(0, idx - width // 2)
        return text[start:start + width].strip()
