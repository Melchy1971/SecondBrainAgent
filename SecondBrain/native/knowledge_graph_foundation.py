"""Knowledge Graph Foundation (v30.77).

Builds entity and relationship suggestions from document content and metadata
without introducing a second search index. Designed for import-stage graph
projection and UI preview.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

ENTITY_TYPES: tuple[str, ...] = ("document", "person", "project", "topic", "action")
RELATIONSHIP_TYPES: tuple[str, ...] = (
    "mentions",
    "belongs_to",
    "created_by",
    "related_to",
    "supersedes",
    "depends_on",
    "assigned_to",
)

_ACTION_WORDS = {
    "create",
    "created",
    "delete",
    "deleted",
    "send",
    "sent",
    "import",
    "imported",
    "review",
    "reviewed",
    "approve",
    "approved",
    "reject",
    "rejected",
    "defer",
    "deferred",
    "assign",
    "assigned",
}

_TOPIC_WORD_RE = re.compile(r"\b[a-z][a-z0-9_-]{3,}\b")
_PERSON_RE = re.compile(r"\b[A-ZÄÖÜ][a-zäöüß]{2,}(?:\s+[A-ZÄÖÜ][a-zäöüß]{2,})?\b")
_DEPENDS_RE = re.compile(r"depends on\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9_-]{2,})", re.IGNORECASE)
_SUPERSEDES_RE = re.compile(r"supersedes\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9_-]{2,})", re.IGNORECASE)
_ASSIGNED_RE = re.compile(r"assigned to\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9_-]{2,}(?:\s+[A-ZÄÖÜ][A-Za-zÄÖÜäöüß0-9_-]{2,})?)", re.IGNORECASE)


def _hash(*parts: str) -> str:
    raw = "|".join(parts).encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()[:16]


def _clean(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _first_snippet(text: str, token: str, *, width: int = 160) -> str:
    needle = (token or "").strip()
    if not needle:
        return _clean(text)[:width]
    index = text.lower().find(needle.lower())
    if index < 0:
        return _clean(text)[:width]
    start = max(0, index - (width // 3))
    end = min(len(text), index + len(needle) + (width // 2))
    return _clean(text[start:end])[:width]


@dataclass(frozen=True)
class EvidenceLink:
    source: str
    snippet: str
    document_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphEntity:
    id: str
    type: str
    label: str
    confidence: float
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = round(float(self.confidence), 4)
        return payload


@dataclass(frozen=True)
class GraphRelationship:
    id: str
    source: str
    target: str
    type: str
    confidence: float
    evidence: dict[str, Any]
    source_ref: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["confidence"] = round(float(self.confidence), 4)
        return payload


@dataclass(frozen=True)
class GraphSuggestion:
    document_id: str
    entities: list[GraphEntity]
    relationships: list[GraphRelationship]

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "entities": [entity.to_dict() for entity in self.entities],
            "relationships": [relationship.to_dict() for relationship in self.relationships],
        }


class KnowledgeGraphFoundation:
    VERSION = "30.77"

    def suggest(self, *, document_id: str, title: str, text: str, metadata: dict[str, Any] | None = None, source: str = "import") -> GraphSuggestion:
        metadata = dict(metadata or {})
        cleaned_text = str(text or "")
        entities: dict[str, GraphEntity] = {}
        relationships: dict[str, GraphRelationship] = {}

        def add_entity(entity_type: str, label: str, confidence: float, **entity_meta: Any) -> GraphEntity:
            normalized = _clean(label)
            if not normalized:
                raise ValueError("empty_entity_label")
            node_id = f"{entity_type}:{_hash(entity_type, normalized.lower())}"
            current = entities.get(node_id)
            merged_meta = {**(current.metadata if current else {}), **entity_meta}
            candidate = GraphEntity(
                id=node_id,
                type=entity_type,
                label=normalized,
                confidence=max(float(confidence), float(current.confidence) if current else 0.0),
                source=source,
                metadata=merged_meta,
            )
            entities[node_id] = candidate
            return candidate

        def add_relationship(relation: str, left: GraphEntity, right: GraphEntity, confidence: float, token: str) -> None:
            if relation not in RELATIONSHIP_TYPES:
                return
            if left.id == right.id:
                return
            rel_id = f"rel:{_hash(relation, left.id, right.id, token)}"
            evidence = EvidenceLink(source=source, snippet=_first_snippet(cleaned_text, token), document_id=document_id).to_dict()
            relationships[rel_id] = GraphRelationship(
                id=rel_id,
                source=left.id,
                target=right.id,
                type=relation,
                confidence=max(0.0, min(1.0, float(confidence))),
                evidence=evidence,
                source_ref=source,
            )

        document = add_entity("document", title or document_id, 1.0, document_id=document_id)

        for person in _extract_people(metadata, cleaned_text):
            p = add_entity("person", person, 0.82)
            add_relationship("mentions", document, p, 0.78, person)

        for project in _extract_projects(metadata, cleaned_text):
            p = add_entity("project", project, 0.86)
            add_relationship("belongs_to", document, p, 0.81, project)

        created_by = _extract_created_by(metadata)
        for owner in created_by:
            p = add_entity("person", owner, 0.88)
            add_relationship("created_by", document, p, 0.84, owner)

        for topic in _extract_topics(metadata, cleaned_text):
            t = add_entity("topic", topic, 0.64)
            add_relationship("mentions", document, t, 0.61, topic)

        for action in _extract_actions(cleaned_text):
            a = add_entity("action", action, 0.67)
            add_relationship("mentions", document, a, 0.6, action)

        projects = [entity for entity in entities.values() if entity.type == "project"]
        topics = [entity for entity in entities.values() if entity.type == "topic"]
        actions = [entity for entity in entities.values() if entity.type == "action"]
        people = [entity for entity in entities.values() if entity.type == "person"]

        for topic in topics[:30]:
            for project in projects[:8]:
                add_relationship("related_to", topic, project, 0.58, f"{topic.label} {project.label}")

        for dep in _DEPENDS_RE.findall(cleaned_text):
            dep_topic = add_entity("topic", dep, 0.63)
            for action in actions[:10]:
                add_relationship("depends_on", action, dep_topic, 0.66, dep)

        for sup in _SUPERSEDES_RE.findall(cleaned_text):
            sup_topic = add_entity("topic", sup, 0.63)
            for action in actions[:10]:
                add_relationship("supersedes", action, sup_topic, 0.66, sup)

        for assignee in _ASSIGNED_RE.findall(cleaned_text):
            person = add_entity("person", assignee, 0.84)
            for action in actions[:10]:
                add_relationship("assigned_to", action, person, 0.79, assignee)

        for left in people:
            for right in people:
                if left.id < right.id:
                    add_relationship("related_to", left, right, 0.52, f"{left.label} {right.label}")

        return GraphSuggestion(
            document_id=document_id,
            entities=sorted(entities.values(), key=lambda item: (item.type, item.label.lower(), item.id)),
            relationships=sorted(relationships.values(), key=lambda item: (item.type, item.source, item.target, item.id)),
        )

    @staticmethod
    def export_json(suggestion: GraphSuggestion, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = suggestion.to_dict()
        payload["version"] = KnowledgeGraphFoundation.VERSION
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return target


class GraphQueryAPI:
    """In-memory read API with non-blocking query behavior."""

    VERSION = "30.77"

    def __init__(self) -> None:
        self._graph: dict[str, Any] = {"nodes": [], "edges": [], "version": self.VERSION}

    def is_ready(self) -> bool:
        return bool(self._graph.get("nodes")) or bool(self._graph.get("edges"))

    def update(self, *, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> None:
        self._graph = {
            "version": self.VERSION,
            "nodes": list(nodes),
            "edges": list(edges),
        }

    def query(self, term: str, *, node_types: Iterable[str] = (), relationship_types: Iterable[str] = (), limit: int = 100) -> dict[str, Any]:
        query = _clean(term).lower()
        if not query:
            return {"ok": False, "status": "query_required", "query": "", "nodes": [], "edges": []}

        allowed_nodes = {value for value in node_types if value}
        allowed_edges = {value for value in relationship_types if value}

        nodes = self._graph.get("nodes", [])
        edges = self._graph.get("edges", [])
        selected_nodes: list[dict[str, Any]] = []

        for node in nodes:
            node_type = str(node.get("type", ""))
            if allowed_nodes and node_type not in allowed_nodes:
                continue
            haystack = f"{node.get('label','')} {json.dumps(node.get('metadata', {}), ensure_ascii=False)} {node_type}".lower()
            if query in haystack:
                selected_nodes.append(node)

        selected_nodes = selected_nodes[: max(1, min(int(limit), 1000))]
        node_ids = {node.get("id") for node in selected_nodes}

        selected_edges: list[dict[str, Any]] = []
        for edge in edges:
            edge_type = str(edge.get("type", ""))
            if allowed_edges and edge_type not in allowed_edges:
                continue
            if edge.get("source") in node_ids or edge.get("target") in node_ids:
                selected_edges.append(edge)

        return {
            "ok": True,
            "version": self.VERSION,
            "query": query,
            "nodes": selected_nodes,
            "edges": selected_edges[: max(1, min(int(limit) * 4, 4000))],
            "result_count": len(selected_nodes),
            "non_blocking": True,
        }


def _extract_people(metadata: dict[str, Any], text: str) -> list[str]:
    values: list[str] = []
    for key in ("person", "people", "persons", "owner", "author", "participants", "created_by"):
        value = metadata.get(key)
        if isinstance(value, str):
            values.extend(part.strip() for part in value.replace(";", ",").split(",") if part.strip())
        elif isinstance(value, (list, tuple, set)):
            values.extend(str(part).strip() for part in value if str(part).strip())
    values.extend(match.strip() for match in _PERSON_RE.findall(text)[:25])
    return list(dict.fromkeys(values))[:30]


def _extract_projects(metadata: dict[str, Any], text: str) -> list[str]:
    values: list[str] = []
    for key in ("project", "projects", "workspace", "workspace_id"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())
        elif isinstance(value, (list, tuple, set)):
            values.extend(str(part).strip() for part in value if str(part).strip())
    for match in _PERSON_RE.findall(text):
        if "Project" in match or "Projekt" in match:
            values.append(match)
    return list(dict.fromkeys(values))[:20]


def _extract_topics(metadata: dict[str, Any], text: str) -> list[str]:
    tags = metadata.get("tags")
    values: list[str] = []
    if isinstance(tags, str):
        values.extend(part.strip("# ") for part in tags.replace(";", ",").split(",") if part.strip())
    elif isinstance(tags, (list, tuple, set)):
        values.extend(str(part).strip("# ") for part in tags if str(part).strip())
    for match in _TOPIC_WORD_RE.findall(text.lower()):
        if match in _ACTION_WORDS:
            continue
        values.append(match)
    return list(dict.fromkeys(values))[:40]


def _extract_actions(text: str) -> list[str]:
    values: list[str] = []
    lowered = text.lower()
    for action in _ACTION_WORDS:
        if action in lowered:
            values.append(action)
    return list(dict.fromkeys(values))[:20]


def _extract_created_by(metadata: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("created_by", "author", "owner"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            values.extend(part.strip() for part in value.replace(";", ",").split(",") if part.strip())
        elif isinstance(value, (list, tuple, set)):
            values.extend(str(part).strip() for part in value if str(part).strip())
    return list(dict.fromkeys(values))[:10]
