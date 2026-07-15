"""Data model for an evidence-based knowledge graph.

Entities and relationships are never bare assertions: each carries the source
ids it was derived from, structured ``evidence`` snippets, a confidence and a
validity window. Conflicting attribute values are retained side by side
(``superseded`` instead of deletion) so the history stays auditable. Technical
identifiers live on the objects for detail views and drill-down; overview
representations use ``canonical_name`` only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

__all__ = [
    "EntityType", "RelationType", "AttributeValue", "Entity", "Relationship",
    "Conflict", "MergeProposal",
]


class EntityType(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    PROJECT = "project"
    DOCUMENT = "document"
    TASK = "task"
    EVENT = "event"
    TOPIC = "topic"
    LOCATION = "location"
    SYSTEM = "system"
    PRODUCT = "product"


class RelationType(StrEnum):
    MENTIONS = "mentions"
    BELONGS_TO = "belongs_to"
    WORKS_FOR = "works_for"
    ASSIGNED_TO = "assigned_to"
    CREATED_BY = "created_by"
    RELATED_TO = "related_to"
    DEPENDS_ON = "depends_on"
    SUPERSEDES = "supersedes"
    CONTRADICTS = "contradicts"
    PARTICIPATED_IN = "participated_in"
    SCHEDULED_FOR = "scheduled_for"
    RESPONSIBLE_FOR = "responsible_for"


@dataclass
class AttributeValue:
    """One value for an entity attribute, bound to its source and validity.

    Multiple values for the same key coexist when sources disagree; a value is
    retired via ``superseded_by`` rather than removed.
    """

    value: str
    source_id: str = ""
    confidence: float = 1.0
    valid_from: str = ""
    valid_to: str = ""
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "source_id": self.source_id,
            "confidence": round(float(self.confidence), 3),
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "superseded_by": self.superseded_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttributeValue":
        return cls(**{k: data.get(k, cls.__dataclass_fields__[k].default) for k in cls.__dataclass_fields__})


@dataclass
class Entity:
    id: str
    workspace_id: str
    canonical_name: str
    type: str
    aliases: list[str] = field(default_factory=list)
    confidence: float = 1.0
    source_ids: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    attributes: dict[str, list[AttributeValue]] = field(default_factory=dict)
    valid_from: str = ""
    valid_to: str = ""
    created_at: str = ""
    updated_at: str = ""
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "canonical_name": self.canonical_name,
            "type": self.type,
            "aliases": list(self.aliases),
            "confidence": round(float(self.confidence), 3),
            "source_ids": list(self.source_ids),
            "evidence": [dict(e) for e in self.evidence],
            "attributes": {k: [v.to_dict() for v in vals] for k, vals in self.attributes.items()},
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "superseded_by": self.superseded_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Entity":
        return cls(
            id=data["id"], workspace_id=data.get("workspace_id", ""),
            canonical_name=data.get("canonical_name", ""), type=data.get("type", EntityType.TOPIC.value),
            aliases=list(data.get("aliases", [])), confidence=float(data.get("confidence", 1.0)),
            source_ids=list(data.get("source_ids", [])), evidence=[dict(e) for e in data.get("evidence", [])],
            attributes={k: [AttributeValue.from_dict(v) for v in vals] for k, vals in data.get("attributes", {}).items()},
            valid_from=data.get("valid_from", ""), valid_to=data.get("valid_to", ""),
            created_at=data.get("created_at", ""), updated_at=data.get("updated_at", ""),
            superseded_by=data.get("superseded_by", ""),
        )


@dataclass
class Relationship:
    id: str
    workspace_id: str
    source_id: str          # source entity id
    target_id: str          # target entity id
    type: str
    confidence: float = 1.0
    origin_source_ids: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    valid_from: str = ""
    valid_to: str = ""
    created_at: str = ""
    updated_at: str = ""
    superseded_by: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "workspace_id": self.workspace_id, "source_id": self.source_id,
            "target_id": self.target_id, "type": self.type, "confidence": round(float(self.confidence), 3),
            "origin_source_ids": list(self.origin_source_ids), "evidence": [dict(e) for e in self.evidence],
            "valid_from": self.valid_from, "valid_to": self.valid_to,
            "created_at": self.created_at, "updated_at": self.updated_at, "superseded_by": self.superseded_by,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Relationship":
        return cls(
            id=data["id"], workspace_id=data.get("workspace_id", ""), source_id=data["source_id"],
            target_id=data["target_id"], type=data.get("type", RelationType.RELATED_TO.value),
            confidence=float(data.get("confidence", 1.0)),
            origin_source_ids=list(data.get("origin_source_ids", [])),
            evidence=[dict(e) for e in data.get("evidence", [])],
            valid_from=data.get("valid_from", ""), valid_to=data.get("valid_to", ""),
            created_at=data.get("created_at", ""), updated_at=data.get("updated_at", ""),
            superseded_by=data.get("superseded_by", ""),
        )


@dataclass
class Conflict:
    entity_id: str
    attribute: str
    values: list[AttributeValue]
    status: str = "open"        # open | resolved
    resolution: str = ""        # keep_both | supersede | merge

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id, "attribute": self.attribute,
            "values": [v.to_dict() for v in self.values],
            "status": self.status, "resolution": self.resolution,
        }


@dataclass
class MergeProposal:
    entity_a: str
    entity_b: str
    score: float
    signals: dict[str, Any]
    auto_mergeable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_a": self.entity_a, "entity_b": self.entity_b,
            "score": round(float(self.score), 3), "signals": dict(self.signals),
            "auto_mergeable": bool(self.auto_mergeable),
        }
