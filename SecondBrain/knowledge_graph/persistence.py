"""Atomic persistence for the evidence-based knowledge graph.

The legacy graph runtime remains untouched. This adapter persists the v31
``KnowledgeGraph`` service state as a workspace-scoped JSON snapshot. Writes use
``fsync`` plus ``os.replace`` so a crash cannot leave a partially written graph.
No document bodies are logged or duplicated outside the graph evidence model.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from secondbrain.knowledge_graph.models import Conflict, Entity, Relationship
from secondbrain.knowledge_graph.service import KnowledgeGraph

__all__ = ["KnowledgeGraphSnapshotRepository"]


class KnowledgeGraphSnapshotRepository:
    def __init__(self, project_root: str | Path = ".") -> None:
        self.root = Path(project_root).resolve()
        self.directory = self.root / "runtime" / "knowledge_graph"

    @staticmethod
    def _safe_workspace(workspace_id: str) -> str:
        value = "".join(ch for ch in str(workspace_id) if ch.isalnum() or ch in "-_")
        if not value or value != workspace_id:
            raise ValueError("invalid_workspace_id")
        return value

    def path_for(self, workspace_id: str) -> Path:
        return self.directory / f"{self._safe_workspace(workspace_id)}.json"

    def save(self, graph: KnowledgeGraph, *, workspace_id: str) -> dict[str, Any]:
        entities = {
            entity.id: entity.to_dict()
            for entity in graph._entities.values()
            if entity.workspace_id == workspace_id
        }
        entity_ids = set(entities)
        relationships = {
            relation.id: relation.to_dict()
            for relation in graph._relationships.values()
            if relation.workspace_id == workspace_id
            and relation.source_id in entity_ids
            and relation.target_id in entity_ids
        }
        conflicts = [
            conflict.to_dict()
            for conflict in graph._conflicts
            if conflict.entity_id in entity_ids
        ]
        payload = {
            "schema": "secondbrain.knowledge_graph.snapshot.v1",
            "workspace_id": workspace_id,
            "entities": entities,
            "relationships": relationships,
            "conflicts": conflicts,
            "merge_history": [
                item for item in graph._merge_history
                if item.get("keep_id") in entity_ids and item.get("drop_id") in entity_ids
            ],
        }
        path = self.path_for(workspace_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        return {"ok": True, "workspace_id": workspace_id, "path": str(path), "entities": len(entities), "relationships": len(relationships)}

    def load(self, *, workspace_id: str, graph: KnowledgeGraph | None = None) -> KnowledgeGraph:
        target = graph or KnowledgeGraph()
        path = self.path_for(workspace_id)
        if not path.exists():
            return target
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if payload.get("schema") != "secondbrain.knowledge_graph.snapshot.v1":
            raise ValueError("unsupported_graph_snapshot")
        if payload.get("workspace_id") != workspace_id:
            raise ValueError("workspace_mismatch")
        loaded_entities = {key: Entity.from_dict(value) for key, value in payload.get("entities", {}).items()}
        if any(entity.workspace_id != workspace_id for entity in loaded_entities.values()):
            raise ValueError("workspace_mismatch")
        loaded_relations = {key: Relationship.from_dict(value) for key, value in payload.get("relationships", {}).items()}
        if any(relation.workspace_id != workspace_id for relation in loaded_relations.values()):
            raise ValueError("workspace_mismatch")
        target._entities.update(loaded_entities)
        target._relationships.update(loaded_relations)
        target._conflicts.extend(
            Conflict(
                entity_id=row["entity_id"],
                attribute=row["attribute"],
                values=[__import__("secondbrain.knowledge_graph.models", fromlist=["AttributeValue"]).AttributeValue.from_dict(value) for value in row.get("values", [])],
                status=row.get("status", "open"),
                resolution=row.get("resolution", ""),
            )
            for row in payload.get("conflicts", [])
        )
        target._merge_history.extend(payload.get("merge_history", []))
        return target
