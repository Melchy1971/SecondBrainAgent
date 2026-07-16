from __future__ import annotations

import json

import pytest

from secondbrain.knowledge_graph.models import EntityType, RelationType
from secondbrain.knowledge_graph.persistence import KnowledgeGraphSnapshotRepository
from secondbrain.knowledge_graph.service import KnowledgeGraph
from secondbrain.release.personal_jarvis_gate import PASS, run_personal_jarvis_gate


def test_graph_roundtrip_preserves_evidence_conflicts_and_relations(tmp_path):
    graph = KnowledgeGraph()
    person = graph.add_entity(
        workspace_id="ws-1",
        canonical_name="Markus",
        type=EntityType.PERSON.value,
        source_ids=["doc-1"],
        evidence=[{"source_id": "doc-1", "snippet": "Markus arbeitet am Projekt"}],
    )
    project = graph.add_entity(
        workspace_id="ws-1",
        canonical_name="SecondBrain",
        type=EntityType.PROJECT.value,
        source_ids=["doc-1"],
    )
    relation = graph.add_relationship(
        workspace_id="ws-1",
        source_entity=person.id,
        target_entity=project.id,
        type=RelationType.RESPONSIBLE_FOR.value,
        evidence=[{"source_id": "doc-1"}],
    )
    graph.set_attribute(project.id, "status", "active", source_id="doc-1")
    graph.set_attribute(project.id, "status", "paused", source_id="doc-2")

    repository = KnowledgeGraphSnapshotRepository(tmp_path)
    result = repository.save(graph, workspace_id="ws-1")
    restored = repository.load(workspace_id="ws-1")

    assert result["ok"] is True
    assert restored.get(person.id).evidence[0]["source_id"] == "doc-1"
    assert restored._relationships[relation.id].type == RelationType.RESPONSIBLE_FOR.value
    assert restored.conflicts(workspace_id="ws-1")[0].attribute == "status"


def test_workspace_snapshots_are_isolated(tmp_path):
    graph = KnowledgeGraph()
    first = graph.add_entity(workspace_id="ws-1", canonical_name="A", type=EntityType.TOPIC.value)
    graph.add_entity(workspace_id="ws-2", canonical_name="B", type=EntityType.TOPIC.value)
    repository = KnowledgeGraphSnapshotRepository(tmp_path)
    repository.save(graph, workspace_id="ws-1")
    restored = repository.load(workspace_id="ws-1")

    assert restored.get(first.id) is not None
    assert [entity.canonical_name for entity in restored.entities(workspace_id="ws-1")] == ["A"]
    assert restored.entities(workspace_id="ws-2") == []


def test_invalid_workspace_id_is_rejected(tmp_path):
    repository = KnowledgeGraphSnapshotRepository(tmp_path)
    with pytest.raises(ValueError, match="invalid_workspace_id"):
        repository.path_for("../escape")


def test_tampered_workspace_snapshot_is_rejected(tmp_path):
    repository = KnowledgeGraphSnapshotRepository(tmp_path)
    path = repository.path_for("ws-1")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema": "secondbrain.knowledge_graph.snapshot.v1",
        "workspace_id": "ws-2",
        "entities": {},
        "relationships": {},
        "conflicts": [],
    }), encoding="utf-8")

    with pytest.raises(ValueError, match="workspace_mismatch"):
        repository.load(workspace_id="ws-1")


def test_personal_jarvis_gate_certifies_graph_persistence(tmp_path):
    report = run_personal_jarvis_gate(tmp_path, write_report=False)
    checks = {row["check_id"]: row for row in report["checks"]}

    assert checks["knowledge_graph_available"]["status"] == PASS
    assert checks["knowledge_graph_persistence"]["status"] == PASS
